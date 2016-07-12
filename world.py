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
mymap = maze.generateMaze()
world = nengo.Network()

# Initliazing the nengo model, network and game map

myPacman = body.Player("pacman", "eating", 2, "yellow", 70, 20)
myGhost = body.Player("ghost", "seeking", 2, "red", 5, 5)
myGhost2 = body.Player("ghost", "seeking", 2, "green", 5, 5)
myGhost3 = body.Player("ghost", "seeking", 2, "blue", 5, 5)
ghostList = []



with model:

    pacPlayer = pacman_world.PacmanWorld(mymap, myPacman, myGhost, ghostList)
    pacPlayer2 = pacman_world.PacmanWorld(mymap, myPacman, myGhost, ghostList)
    environment = pacman_world.GridNode(pacPlayer.world)
    gamePacmen = [pacPlayer, pacPlayer2]

    sensor = nengo.Ensemble(n_neurons = 100, dimensions = 2*len(gamePacmen), radius = 3)

    for i, pacPlayer in enumerate(gamePacmen):
        start = 2*i
        end = ((2*(i+1))-1)+1

        # Connected the world's move sensor to pacman's move sensor
        nengo.Connection(sensor[start:end], pacPlayer.move)

        # Created Food ensemble
        food = nengo.Ensemble(n_neurons = 100, dimensions = 2)
        nengo.Connection(pacPlayer.detect_food, food, synapse = 0.)

        # Connected pacman's food node to the world's ensemble
        nengo.Connection(food[0], sensor[end-1], transform = 2, synapse = 0.)
        nengo.Connection(food[1], sensor[start], transform = 3, synapse = 0.)

        # Created obstacles ensemble
        obstacles = nengo.Ensemble(n_neurons = 50, dimensions = 3, radius = 4)
        nengo.Connection(pacPlayer.obstacles[[1,2,3]], obstacles, transform = 0.5, synapse = 0.)

        # turn away from walls
        def avoid(x):
            return 1*(x[2] - x[0])
        # Connected the obstacles node to the world's ensemble
        nengo.Connection(obstacles, sensor[end-1], function=avoid, synapse = 0.)

        # avoid crashing into walls
        def ahead(x):
            return 1*(x[1] - 0.5)
        # Connected the obstacles node to the world's ensemble
        nengo.Connection(obstacles, sensor[start], function=ahead, synapse = 0.)

        enemy = nengo.Ensemble(n_neurons = 50, dimensions = 2)
        nengo.Connection(pacPlayer.detect_enemy, enemy, synapse = 0.)

        # run away from enemies
        # - angle is the direction to the enemies
        # - radius is the strength (1.0/distance)
        def run_away(x):
            return -1*x[1], -1*x[0]
        nengo.Connection(enemy, sensor[start:end], function=run_away, synapse = 0.)
