import random
from random import randint
import numpy as np
import nengo
import cellular
import continuous
import body
from threading import Timer

# Global variables that contain information about the pacman and ghost
# The pacman and ghost classes extend the continuous body class
# Additonally, their parameters can be edited to change their state, color, size, etc.

global pacman
pacman = body.Player("pacman", "eating", 2, "yellow", 70, 20)

global ghost
ghost = body.Player("ghost", "seeking", 0.35, "red", 40, 15)

# The cell class encapsulates every "object" in the game (walls, food, enemies, pacman, etc.)
class Cell(cellular.Cell):

    # These are the inital states of the food, pacman start and enemy start booleans
    food = False
    pacman_start = False
    enemy_start = False
    state = "regular"

    # The Color function sets the color of both the wall and food
    def color(self):
        if self.wall:
            return 'blue'
        if self.food:
            return 'white'
        return None

    # The load function runs through the mymap string passed in and initalizes starting positions for the pacman, enemy and food
    def load(self, char):
        if char == '#':
            self.wall = True
        elif char == 'S':
            self.pacman_start = True
        elif char == 'E':
            self.enemy_start = True
        else:
            self.food = True

# GridNode sets up the pacman world for visualization
class GridNode(nengo.Node):
    def __init__(self, world, dt=0.001):
        # The initalizer sets up the html layout for display
        def svg(t):
            last_t = getattr(svg, '_nengo_html_t_', None)
            if t <= last_t:
                last_t = None
            if last_t is None or t >= last_t + dt:
                svg._nengo_html_ = self.generate_svg(world)
                svg._nengo_html_t_ = t
        super(GridNode, self).__init__(svg)

    # This function sets up an SVG (used to embed html code in the environment)
    def generate_svg(self, world):
        cells = []

        # Runs through every cell in the world (walls & food)
        for i in range(world.width):
            for j in range(world.height):
                cell = world.get_cell(i, j)
                color = cell.color
                if callable(color):
                    color = color()
                # If the cell is a wall, then set its appearance to a blue rectangle
                if color=="blue":
                    cells.append('<rect x=%d y=%d width=1 height=1 style="fill:%s"/>' %
                         (i, j, color))
                # If the cell is normal food, then set its appearance to a white circle
                if color=="white" and i!=1 and j!=1 and i%5==0 and j%5==0:
                    cells.append('<circle cx=%d cy=%d r=0.4 style="fill:%s"/>' %
                        (i, j, color))
                # If the cell is super food, then set its appearance to a larger white circle
                if color=="white" and i!=1 and j!=1 and i%5==0 and j%5==0 and i==20 and j==5:
                    cell.state = "super"
                    cells.append('<circle cx=%d cy=%d r=0.65 style="fill:%s"/>' %
                        (i, j, "white"))

        # Runs through every agent in the world (ghost & pacman)
        agents = []
        for agent in world.agents:
            # sets variables like agent direction, color and size
            direction = agent.dir * 360.0 / world.directions
            color = getattr(agent, 'color', pacman.color)
            if callable(color):
                color = color()
            s = pacman.size
            # Uses HTML rendering to setup the agents
            agent_poly = ('<circle r="%f"'
                     ' style="fill:%s" transform="translate(%f,%f) rotate(%f)"/>'
                     % (s, color, agent.x+0.5, agent.y+0.5, direction))

            agents.append(agent_poly)

        # Sets up the environment as a HTML SVG

        svg = '''<svg style="background: black" width="100%%" height="100%%" viewbox="0 0 %d %d">
            %s
            %s
            </svg>''' % (world.width, world.height,
                         ''.join(cells), ''.join(agents))
        return svg


class PacmanWorld(nengo.Network):

    def __init__(self, worldmap, pacman_speed = pacman.speed, pacman_rotate = pacman.rotate,
                 ghost_speed = ghost.speed, ghost_rotate=ghost.rotate,
                 **kwargs):
        # Initializes PacmanWorld using parameters from the global pacman and ghost variables
        super(PacmanWorld, self).__init__(**kwargs)
        self.world = cellular.World(Cell, map=worldmap, directions=4)

        self.pacman = pacman

        self.ghost_rotate = ghost_rotate
        self.ghost_speed = ghost_speed

        starting = list(self.world.find_cells(lambda cell: cell.pacman_start))
        if len(starting) == 0:
            starting = list(self.world.find_cells(lambda cell: cell.food))
        cell = random.choice(starting)

        total = len(list(self.world.find_cells(lambda cell: cell.food)))

        self.world.add(self.pacman, cell=cell, dir=3)

        # Adds a random amount of ghost enemies to the world
        self.enemies = []
        for cell in self.world.find_cells(lambda cell: cell.enemy_start):
            new = body.Player("ghost", "seeking", 0.37, "red", 10, 5)
            self.world.add(new, cell=cell, dir=1)
            self.enemies.append(new)

        self.completion_time = None

        with self:
            self.environment = GridNode(self.world)

            # Pacman's move function -- called every 0.001 second (set using dt)
            def move(t, x):

                speed, rotation = x
                dt = 0.001

                # Pacman turns and moves forward based on obstacles and food availability
                self.pacman.turn(rotation * dt * pacman_rotate)
                self.pacman.go_forward(speed * dt * pacman_speed)

                # If pacman moves into a cell containing food...
                if self.pacman.cell.food:
                    # If pacman eats a super food...
                    if(self.pacman.cell.state=="super"):

                        def revertColor():
                            # Turns ghosts to their orginal state
                            global ghost
                            ghost.color = "red"
                            # Sets the pacman's state to "eating"
                            global pacman
                            pacman.state = "eating"
                            for g in self.enemies:
                                g.color = "red"

                        # Ghosts turn white when pacman eats a super food
                        global ghost
                        ghost.color = "white"
                        # Pacman's state becomes "seeking"
                        global pacman
                        pacman.state = "seeking"

                        for g in self.enemies:
                            g.color = "white"

                        # After 5 seconds, the revertColor method is called
                        tx = Timer(5.0, revertColor)
                        tx.start()

                    def saveCoor():
                        x = self.pacman.x
                        y = self.pacman.y

                    def respawnFood():
                        for i in range(self.world.width):
                            for j in range(self.world.height):
                                if(self.world.get_cell(i, j).state == "eaten"):
                                    self.world.get_cell(i, j).food = True
                                    self.world.get_cell(i, j).state = "regular"

                    self.pacman.score += 1

                    self.pacman.cell.food = False
                    self.pacman.cell.state = "eaten"

                    #tF = Timer(5.0, respawnFood)
                    #tF.start()

                    #Sif(self.pacman.cell.state == "eaten"):


                    if self.completion_time is None and self.pacman.score == total:
                        self.completion_time = t

                for ghost in self.enemies:
                    self.update_ghost(ghost)

            self.move = nengo.Node(move, size_in=2)

            # The score is kept track of using an html rendering

            def score(t):
                html = '<h1>%d / %d</h1>' % (self.pacman.score, total)
                if self.completion_time is not None:
                    html += 'Completed in<br/>%1.3f seconds' % self.completion_time
                else:
                    html += '%1.3f seconds' % t
                html = '<center>%s</center>' % html
                score._nengo_html_ = html
            self.score = nengo.Node(score)



            def obstacles(t):
                angles = np.linspace(-1, 1, 5) + self.pacman.dir
                angles = angles % self.world.directions
                self.pacman.obstacle_distances = [self.pacman.detect(d, max_distance=4)[0] for d in angles]
                return self.pacman.obstacle_distances
            self.obstacles = nengo.Node(obstacles)

            def detect_food(t):
                x = 0
                y = 0
                for cell in self.world.find_cells(lambda cell:cell.food):
                    dir = self.pacman.get_direction_to(cell)
                    dist = self.pacman.get_distance_to(cell)
                    rel_dir = dir - self.pacman.dir
                    strength = 1.0 / dist

                    dx = np.sin(rel_dir * np.pi / 2) * strength
                    dy = np.cos(rel_dir * np.pi / 2) * strength

                    x += dx
                    y += dy
                return x, y
            self.detect_food = nengo.Node(detect_food)

            def detect_enemy(t):
                x = 0
                y = 0
                for ghost in self.enemies:
                    dir = self.pacman.get_direction_to(ghost)
                    dist = self.pacman.get_distance_to(ghost)
                    rel_dir = dir - self.pacman.dir
                    strength = 1.0 / dist

                    dx = np.sin(rel_dir * np.pi / 2) * strength
                    dy = np.cos(rel_dir * np.pi / 2) * strength

                    x += dx
                    y += dy
                return x, y
            self.detect_enemy = nengo.Node(detect_enemy)

    def update_ghost(self, ghost):
        dt = 0.001

        target_dir = ghost.get_direction_to(self.pacman)

        theta = ghost.dir - target_dir
        while theta > 2: theta -= 4
        while theta < -2: theta += 4

        ghost.turn(-theta * dt * self.ghost_rotate)
        ghost.go_forward(self.ghost_speed * dt)

        if ghost.get_distance_to(self.pacman) < 0.5:
            self.reset()

    def reset(self):
        self.pacman.score = 0

        for row in self.world.grid:
            for cell in row:
                if not (cell.wall or cell.pacman_start or cell.enemy_start):
                    cell.food = True

        starting = list(self.world.find_cells(lambda cell: cell.pacman_start))
        if len(starting) == 0:
            starting = list(self.world.find_cells(lambda cell: cell.food))
        self.pacman.cell = random.choice(starting)
        self.pacman.x = self.pacman.cell.x
        self.pacman.y = self.pacman.cell.y
        self.pacman.dir = 3

        for i, cell in enumerate(self.world.find_cells(lambda cell: cell.enemy_start)):
            self.enemies[i].cell = cell
            self.enemies[i].dir = 1
            self.enemies[i].x = cell.x
            self.enemies[i].y = cell.y
