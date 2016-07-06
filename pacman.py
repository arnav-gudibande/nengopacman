import nengo
import pacman_world
reload(pacman_world)
from random import randint
import numpy as np
import random
import re
import body

def generateMaze():
    num_rows = 3 # number of rows
    num_cols = 10 # number of columns

    M = np.zeros((num_rows,num_cols,5), dtype=np.uint8)
    # The array M is going to hold the array information for each cell.
    # The first four coordinates tell if walls exist on those sides
    # and the fifth indicates if the cell has been visited in the search.
    # M(LEFT, UP, RIGHT, DOWN, CHECK_IF_VISITED)
    image = np.zeros((num_rows*10,num_cols*10), dtype=np.uint8)
    # The array image is going to be the output image to display

    # Set starting row and column
    r = 0
    c = 0
    history = [(r,c)] # The history is the

    # Trace a path though the cells of the maze and open walls along the path.
    # We do this with a while loop, repeating the loop until there is no history,
    # which would mean we backtracked to the initial start.
    while history:
        M[r,c,4] = 1 # designate this location as visited
        # check if the adjacent cells are valid for moving to
        check = []
        if c > 0 and M[r,c-1,4] == 0:
            check.append('L')
        if r > 0 and M[r-1,c,4] == 0:
            check.append('U')
        if c < num_cols-1 and M[r,c+1,4] == 0:
            check.append('R')
        if r < num_rows-1 and M[r+1,c,4] == 0:
            check.append('D')

        if len(check): # If there is a valid cell to move to.
            # Mark the walls between cells as open if we move
            history.append([r,c])
            move_direction = random.choice(check)
            if move_direction == 'L':
                M[r,c,0] = 1
                c = c-1
                M[r,c,2] = 1
            if move_direction == 'U':
                M[r,c,1] = 1
                r = r-1
                M[r,c,3] = 1
            if move_direction == 'R':
                M[r,c,2] = 1
                c = c+1
                M[r,c,0] = 1
            if move_direction == 'D':
                M[r,c,3] = 1
                r = r+1
                M[r,c,1] = 1
        else: # If there are no valid cells to move to.
    	# retrace one step back in history if no move is possible
            r,c = history.pop()

    hashes = ""
    # Generate the image for display
    for row in range(0,num_rows):
        for col in range(0,num_cols):

            cell_data = M[row,col]
            for i in range(10*row+1,10*row+9):
                image[i,range(10*col+1,10*col+9)] = 255
                if cell_data[0] == 1:
                    image[range(10*row+1,10*row+9),10*col] = 255
                    hashes += " "
                if cell_data[1] == 1:
                    image[10*row,range(10*col+1,10*col+9)] = 255
                    hashes += " "
                if cell_data[2] == 1:
                    image[range(10*row+1,10*row+9),10*col+9] = 255
                    hashes += " "
                if cell_data[3] == 1:
                    image[10*row+9,range(10*col+1,10*col+9)] = 255
                    hashes += " "
                else:
                    hashes += "#"

    new = ""
    eC=0
    for x in range(len(image)):
        for y in range(len(image[0])):
            if(randint(0,500) == randint(0,500)):
                eC+=1
                new = new[:-1]
                if(eC<=3): new += "E"
                elif(eC>3): new += " "
            if (image[x][y] == 255): new += " "
            if (image[x][y] == 0): new += "#"
        new += "\n"

    return new

# Nengo Network
model = nengo.Network()
mymap = generateMaze()

# Initliazing the nengo model, network and game map

with model:

    myPacman = body.Player("pacman", "eating", 2, "yellow", 70, 20)
    pacman = pacman_world.PacmanWorld(mymap, myPacman)

    # create the movement control
    # - dimensions are speed (forward|backward) and rotation (left|right)
    moveSensor = nengo.Node(size_in = 2)
    move = nengo.Ensemble(n_neurons=100, dimensions=2, radius=3)

    nengo.Connection(move, moveSensor, synapse = 0.)
    nengo.Connection(moveSensor, pacman.move, synapse = 0.)

    # sense food
    # - angle is the direction to the food
    # - radius is the strength (1.0/distance)
    foodSensor = nengo.Node(size_in = 2)
    nengo.Connection(pacman.detect_food, foodSensor, synapse = 0.)

    food = nengo.Ensemble(n_neurons=100, dimensions=2)
    nengo.Connection(foodSensor, food, synapse = 0.)

    # turn towards food
    nengo.Connection(food[0], move[1], transform=2)
    # move towards food
    nengo.Connection(food[1], move[0], transform=3)

    # sense obstacles
    # - distance to obstacles on left, front-left, front, front-right, and right
    # - maximum distance is 4
    obstacleSensor = nengo.Node(size_in = 3)
    obstacles = nengo.Ensemble(n_neurons=50, dimensions=3, radius=4)
    nengo.Connection(pacman.obstacles[[1,2,3]], obstacleSensor, transform=0.5, synapse = 0.)
    nengo.Connection(obstacleSensor, obstacles, synapse = 0.)

    # turn away from walls
    def avoid(x):
        return 1*(x[2] - x[0])
    nengo.Connection(obstacles, move[1], function=avoid)

    # avoid crashing into walls
    def ahead(x):
        return 1*(x[1] - 0.5)
    nengo.Connection(obstacles, move[0], function=ahead)

    # detect enemies
    enemySensor = nengo.Node(size_in = 2)
    nengo.Connection(pacman.detect_enemy, enemySensor, synapse = 0.)

    enemy = nengo.Ensemble(n_neurons=50, dimensions=2)
    nengo.Connection(enemySensor, enemy, synapse = 0.)

    # run away from enemies
    # - angle is the direction to the enemies
    # - radius is the strength (1.0/distance)
    def run_away(x):
        return -1*x[1], -1*x[0]
    nengo.Connection(enemy, move, function=run_away)
