import nengo
import pacman_world
reload(pacman_world)
from random import randint
import numpy as np
import random
import re
import body
import maze

# Nengo Network
model = nengo.Network()
mymap = maze.generateMaze(4, 10)

# Initliazing the nengo model, network and game map

with model:

    pacman1 = body.Player("pacman", 1, 2, "yellow", 70, 20)
    pacman2 = body.Player("pacman", 2, 2, "yellow", 70, 20)
    pacman3 = body.Player("pacman", 3, 2, "yellow", 70, 20)

    pacmen = [pacman1, pacman2, pacman3]
    myGhost = body.Player("ghost", "seeking", 2, "red", 5, 5)
    myGhost2 = body.Player("ghost", "seeking", 2, "green", 5, 5)
    myGhost3 = body.Player("ghost", "seeking", 2, "blue", 5, 5)
    ghostList = []
    ghostList.append(myGhost2)
    ghostList.append(myGhost3)

    world = pacman_world.PacmanWorld(mymap, pacmen, myGhost, ghostList)

    for (i, pac) in enumerate(pacmen):
        player = nengo.Network("Pacman " + str(i+1))
        with player:

            # pacnets contain "pacman" networks
            pacnet = world.pacnets[i]

            # create the movement control
            # - dimensions are speed (forward|backward) and rotation (left|right)
            move = nengo.Ensemble(n_neurons=100, dimensions=2, radius=3)
            nengo.Connection(move, pacnet.move, synapse = 0.)

            # sense food
            # - angle is the direction to the food
            # - radius is the strength (1.0/distance)
            food = nengo.Ensemble(n_neurons=100, dimensions=2)
            nengo.Connection(pacnet.detect_food, food, synapse = 0.)

            # turn towards food
            nengo.Connection(food[0], move[1], transform=2)
            # move towards food
            nengo.Connection(food[1], move[0], transform=3)

            # sense obstacles
            # - distance to obstacles on left, front-left, front, front-right, and right
            # - maximum distance is 4
            obstacles = nengo.Ensemble(n_neurons=50, dimensions=3, radius=4)
            nengo.Connection(pacnet.obstacles[[1,2,3]], obstacles, transform=0.5, synapse = 0.)

            # turn away from walls
            def avoid(x):
                return 1*(x[2] - x[0])
            nengo.Connection(obstacles, move[1], function=avoid)

            # avoid crashing into walls
            def ahead(x):
                return 1*(x[1] - 0.5)
            nengo.Connection(obstacles, move[0], function=ahead)

            # detect enemies
            enemy = nengo.Ensemble(n_neurons=50, dimensions=2)
            nengo.Connection(pacnet.detect_enemy, enemy, synapse = 0.)

            # run away from enemies
            # - angle is the direction to the enemies
            # - radius is the strength (1.0/distance)
            def run_away(x):
                return -1*x[1], -1*x[0]
            nengo.Connection(enemy, move, function=run_away)
