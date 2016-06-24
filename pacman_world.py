import random
from random import randint
import numpy as np
import nengo
import cellular
import continuous
import body
from threading import Timer

global pacman
pacman = body.Body("pacman", "eating", 2, "yellow", 20, 10)

global ghost
ghost = body.Body("ghost", "seeking", 1, "red", 10, 5)

class Cell(cellular.Cell):
    food = False
    pacman_start = False
    enemy_start = False
    state = "regular"

    def color(self):
        if self.wall:
            return 'blue'
        if self.food:
            return 'white'
        return None
    def load(self, char):
        if char == '#':
            self.wall = True
        elif char == 'S':
            self.pacman_start = True
        elif char == 'E':
            self.enemy_start = True
        else:
            self.food = True

class GridNode(nengo.Node):
    def __init__(self, world, dt=0.001):
        def svg(t):
            last_t = getattr(svg, '_nengo_html_t_', None)
            if t <= last_t:
                last_t = None
            if last_t is None or t >= last_t + dt:
                svg._nengo_html_ = self.generate_svg(world)
                svg._nengo_html_t_ = t
        super(GridNode, self).__init__(svg)

    def generate_svg(self, world):
        cells = []

        for i in range(world.width):
            for j in range(world.height):
                cell = world.get_cell(i, j)
                color = cell.color
                if callable(color):
                    color = color()
                if color=="blue":
                    cells.append('<rect x=%d y=%d width=1 height=1 style="fill:%s"/>' %
                         (i, j, color))
                if color=="white" and i!=1 and j!=1 and i%5==0 and j%5==0:
                    cells.append('<circle cx=%d cy=%d r=0.5 style="fill:%s"/>' %
                        (i, j, color))
                if color=="white" and i!=1 and j!=1 and i%5==0 and j%5==0 and i==20 and j==5:
                    cell.state = "super"
                    cells.append('<circle cx=%d cy=%d r=0.85 style="fill:%s"/>' %
                        (i, j, color))

        agents = []
        for agent in world.agents:
            direction = agent.dir * 360.0 / world.directions
            color = getattr(agent, 'color', pacman.color)
            if callable(color):
                color = color()
            s = pacman.size
            agent_poly = ('<circle r="%f"'
                     ' style="fill:%s" transform="translate(%f,%f) rotate(%f)"/>'
                     % (s, color, agent.x+0.5, agent.y+0.5, direction))

            agents.append(agent_poly)

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

        self.enemies = []
        for cell in self.world.find_cells(lambda cell: cell.enemy_start):
            new = body.Body("ghost", "seeking", 0.37, "red", 10, 5)
            self.world.add(new, cell=cell, dir=1)
            self.enemies.append(new)

        self.completion_time = None

        with self:
            self.environment = GridNode(self.world)

            def move(t, x):
                speed, rotation = x
                dt = 0.009
                self.pacman.turn(rotation * dt * pacman_rotate)
                self.pacman.go_forward(speed * dt * pacman_speed)

                if self.pacman.cell.food:
                    if(self.pacman.cell.state=="super"):

                        def revertColor():
                            global ghost
                            ghost.color = "red"
                            for g in self.enemies:
                                g.color = "red"

                        global ghost
                        ghost.color = "white"
                        for g in self.enemies:
                            g.color = "white"

                    self.pacman.score += 1
                    self.pacman.cell.food = False
                    if self.completion_time is None and self.pacman.score == total:
                        self.completion_time = t

                for ghost in self.enemies:
                    self.update_ghost(ghost)

            self.move = nengo.Node(move, size_in=2)

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
        dt = 0.009

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
