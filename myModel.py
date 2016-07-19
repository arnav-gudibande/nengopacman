# Refer to pacman.py for model framework

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

    # Create Instances of pacman, add it to a pacmen list

    pacmen = []

    # Create Instances of ghosts and add it to the ghostList

    ghostList = []

    world = pacman_world.PacmanWorld(mymap, pacmen, myGhost, ghostList)

    for (i, pac) in enumerate(pacmen):
        player = nengo.Network("Pacman " + str(i+1))
        with player:

            # pacnets contain "pacman" networks
            pacnet = world.pacnets[i]

            # create the movement control
            # - dimensions are speed (forward|backward) and rotation (left|right)


            # create the food ensemble
            # - angle is the direction to the food
            # - radius is the strength (1.0/distance)


            # turn towards food

            # move towards food



            # create the obstacles ensemble
            # - distance to obstacles on left, front-left, front, front-right, and right
            # - maximum distance is 4


            # turn away from walls
            # Define an avoid function, apply it to the obstacles connection (1st index)


            # avoid crashing into walls
            # Define an ahead function, apply it to the obstacles connection (0th index)



            # detect enemies
            # Create an enemy ensemble


            # Define a run away function to run from enemies, connect to move ensemble
            # - angle is the direction to the enemies
            # - radius is the strength (1.0/distance)
