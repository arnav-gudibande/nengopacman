import random
from random import randint
import numpy as np
import nengo
import cellular
import continuous
import body
from threading import Timer

# These variables keep track of the row and column count while generating the maze
global counter
counter = 0
global row
row = 0
global col
col = 0

# The cell class encapsulates every "object" in the game (walls, food, enemies, pacman, etc.)
class Cell(cellular.Cell):

    # These are the inital states of the food, pacman start and enemy start booleans
    food = False
    pacman_start = False
    none = False
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

        global counter
        counter += 1
        global row
        row+=1

        # Conditionals to place food in only increments of 5
        if(row%100==0):
            global col
            col+=1
            global counter
            counter = 0
        if char == '#':
            global hashct
            self.wall = True
        elif char == 'S':
            self.pacman_start = True
        elif char == 'E':
            self.enemy_start = True
        elif char == ' ' and counter%5==0 and col%5==0:
            self.food = True
        else:
            self.space = True

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
        listFood = list()
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
                if color=="white" and i!=1 and j!=1:
                    cell.state = "food"
                    cells.append('<circle cx=%d cy=%d r=0.4 style="fill:%s"/>' %
                        (i, j, color))

                # If the cell is super food, then set its appearance to a larger white circle
                if color=="white" and i!=1 and j!=1 and ((i==84 and j==25) or (i==64 and j==10) or (i==34 and j==15)):
                    cell.state = "super"
                    cells.append('<circle cx=%d cy=%d r=0.55 style="fill:%s"/>' %
                        (i, j, "orange"))

        # Runs through every agent in the world (ghost & pacman)
        agents = []
        for agent in world.agents:

            # sets variables like agent direction, color and size
            direction = agent.dir * 360.0 / world.directions
            color = getattr(agent, 'color', "yellow")
            if callable(color):
                color = color()
            s = agent.size

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

# Main Pacman World class
class PacmanWorld(nengo.Network):

    def __init__(self, worldmap, pacmen, ghost, ghostList, **kwargs):

        # Initializes Pacman World using parameters from the global pacman and ghost variables
        super(PacmanWorld, self).__init__(**kwargs)
        self.world = cellular.World(Cell, map=worldmap, directions=4)
        self.pacmen = pacmen
        self.ghost = ghost
        self.ghost_rotate = self.ghost.rotate
        self.ghost_speed = self.ghost.speed

        # Init for starting positions of the pacman and for food, etc.
        starting = list(self.world.find_cells(lambda cell: cell.pacman_start))
        if len(starting) == 0:
            starting = list(self.world.find_cells(lambda cell: cell.food))
        cell = random.choice(starting)
        total = len(list(self.world.find_cells(lambda cell: cell.food)))

        # Adds a random amount of ghost enemies to the world
        self.enemies = []

        for cell in self.world.find_cells(lambda cell: cell.enemy_start):
            new = body.Player("ghost", "seeking", 2, "red", 10, 5)
            self.world.add(new, cell=cell, dir=1)
            self.enemies.append(new)
            for gG in ghostList:
                self.world.add(gG, cell = cell, dir = 1)
                self.enemies.append(gG)
        self.completion_time = None


        # Sets up environment for the GridNode (this includes the nodes for obstacles and food)
        with self:
            self.environment = GridNode(self.world)

            self.pacnets = []
            for i, pacman in enumerate(self.pacmen):
                self.world.add(pacman, cell=cell, dir=3)

                pacnet = nengo.Network(label='pacman[%d]' % i)
                self.pacnets.append(pacnet)

                #Pacman's move function -- called every 0.001 second (set using dt)
                def move(t, x, pacman=pacman):

                    def revertColor():

                        self.ghost.color = "red"
                        self.ghost.state = "seeking"

                        i=0
                        for g in self.enemies:
                            g.color = ghostC[i]
                            i+=1

                    speed, rotation = x
                    dt = 0.001

                    # Pacman turns and moves forward based on obstacles and food availability
                    pacman.turn(rotation * dt * pacman.rotate)
                    pacman.go_forward(speed * dt * pacman.speed)

                    # If pacman moves into a cell containing food...
                    if pacman.cell.food:
                        ghostC = []
                        for g in self.enemies:
                            ghostC.append(g.color)
                        if(pacman.cell.state=="super"):
                            self.ghost.color = "white"
                            self.ghost.state = "running"
                            for g in self.enemies:
                                g.color = "white"
                                g.state = "running"
                            tx = Timer(5.0, revertColor)
                            tx.start()
                        pacman.score += 1
                        pacman.cell.food = False

                # Sets up the node for the obstacles (this factors in angles and distances towards respective obstacles)
                def obstacles(t, pacman=pacman):
                    angles = np.linspace(-1, 1, 5) + pacman.dir
                    angles = angles % self.world.directions
                    pacman.obstacle_distances = [pacman.detect(d, max_distance=4*2)[0] for d in angles]
                    return pacman.obstacle_distances

                # Sets up the node for the food (factors in amount of food in an area and its relative strength, distance, etc)
                def detect_food(t, pacman=pacman):
                    x = 0
                    y = 0

                    # Runs through the total number of cells in the world and calculates strength and relative distance for each one
                    for cell in self.world.find_cells(lambda cell:cell.food):
                        dir = pacman.get_direction_to(cell)
                        dist = pacman.get_distance_to(cell)
                        rel_dir = dir - pacman.dir
                        if dist > 5: continue
                        if dist>=0.05:
                            strength = 1.0 / dist
                        else: strength = 20

                        dx = np.sin(rel_dir * np.pi / 2) * strength
                        dy = np.cos(rel_dir * np.pi / 2) * strength

                        x += dx
                        y += dy
                    return x, y

                # Sets up the node for the enemies (factors in number of enemies in an area and their relative strength, distance, etc.)
                def detect_enemy(t, pacman=pacman):
                    x = 0
                    y = 0

                    # Runs through the total number of ghosts in the world and calculates strength and relative distance for each one
                    for ghost in self.enemies:
                        dir = pacman.get_direction_to(ghost)
                        dist = pacman.get_distance_to(ghost)
                        rel_dir = dir - pacman.dir
                        if dist < 0.001:
                            dist = 0.001
                        strength = 1.0 / dist

                        dx = np.sin(rel_dir * np.pi / 2) * strength
                        dy = np.cos(rel_dir * np.pi / 2) * strength

                        x += dx
                        y += dy
                    return x, y

                with pacnet:
                    pacnet.move = nengo.Node(move, size_in=2)
                    pacnet.obstacles = nengo.Node(obstacles)
                    pacnet.detect_food = nengo.Node(detect_food)
                    pacnet.detect_enemy = nengo.Node(detect_enemy)

            # The score is kept track of using an html rendering
            def score(t):
                for ghost in self.enemies:
                    self.update_ghost(ghost)
                total_score = sum([pacman.score for pacman in self.pacmen])
                if self.completion_time is None and total_score == total:
                    self.completion_time = t
                scores = ':'.join(['%d' % pacman.score for pacman in self.pacmen])

                html = '<h1>%s / %d</h1>' % (scores, total)
                if self.completion_time is not None:
                    html += 'Completed in<br/>%1.3f seconds' % self.completion_time
                else:
                    html += '%1.3f seconds' % t
                html = '<center>%s</center>' % html
                score._nengo_html_ = html
            self.score = nengo.Node(score)

    # Updates the ghost's position every 0.001 second
    def update_ghost(self, ghost):
        dt = 0.001

        # Updates the ghost's position based on angles and distance towards the obstacles, etc.
        angles = np.linspace(-1, 1, 5) + ghost.dir
        angles = angles % self.world.directions
        obstacle_distances = [ghost.detect(d, max_distance=4*2)[0] for d in angles]

        ghost.turn((obstacle_distances[1]-obstacle_distances[3])*-2 * dt * self.ghost_rotate)
        ghost.go_forward((obstacle_distances[2]-0.5)*2*self.ghost_speed * dt)

        dirs = [ghost.get_direction_to(pacman) for pacman in self.pacmen]
        dists = [ghost.get_distance_to(pacman) for pacman in self.pacmen]
        closest = dists.index(min(dists))

        target_dir = dirs[closest]

        # If the ghost is in a seeking condition, then it is turning towards the pacman and going forward
        if(ghost.state == "seeking"):
            theta = ghost.dir - target_dir
            while theta > 2: theta -= 4
            while theta < -2: theta += 4
            ghost.turn(-theta * dt * self.ghost_rotate)
            ghost.go_forward(self.ghost_speed * dt)
            if dists[closest] < 1:
                self.reset()

        # If the ghost is in a running condition, then it is turning away from the pacman and going forward
        if(ghost.state == "running"):
            if dists[closest] < 1:
                self.reset()
            theta = ghost.dir - target_dir
            while theta > 2: theta -= 4
            while theta < -2: theta += 4
            ghost.turn(360-( -theta * dt * self.ghost_rotate))
            ghost.go_forward(self.ghost_speed * dt)

    # Resets the pacman's position after it loses
    def reset(self):
        for pacman in self.pacmen:
            pacman.score = 0

        # Runs through the rows in the world and reinializes cells
        for row in self.world.grid:
            for cell in row:
                if not (cell.wall or cell.pacman_start or cell.enemy_start) and (cell.state == "food" or cell.state == "super"):
                    cell.food = True

        # reinializes the starting position of the pacman
        for pacman in self.pacmen:
            starting = list(self.world.find_cells(lambda cell: cell.pacman_start))
            if len(starting) == 0:
                starting = list(self.world.find_cells(lambda cell: cell.food))
            pacman.cell = random.choice(starting)
            pacman.x = pacman.cell.x
            pacman.y = pacman.cell.y
            pacman.dir = 3

        for i, cell in enumerate(self.world.find_cells(lambda cell: cell.enemy_start)):
            self.enemies[i].cell = cell
            self.enemies[i].dir = 1
            self.enemies[i].x = cell.x
            self.enemies[i].y = cell.y
