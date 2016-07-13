import numpy as np

def generateMaze(num_rows, num_cols, num_ghosts=3, seed=None, num_passage=2):

    rng = np.random.RandomState(seed=seed)

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
            move_direction = rng.choice(check)
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


    walls = np.where(M[1:-1,1:-1,:2] == 0)
    chosen = rng.choice(np.arange(len(walls[0])),
                              size=num_passage, replace=False)
    for i in chosen:
        M[walls[0][i]+1, walls[1][i]+1, walls[2][i]] = 1
        if walls[2][i] == 0:
            M[walls[0][i]+1, walls[1][i]+1-1, 2] = 1
        elif walls[2][i] == 2:
            M[walls[0][i]+1, walls[1][i]+1+1, 0] = 1
        elif walls[2][i] == 1:
            M[walls[0][i]+1-1, walls[1][i]+1, 3] = 1
        elif walls[2][i] == 3:
            M[walls[0][i]+1+1, walls[1][i]+1, 1] = 1


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

    spaces = np.where(image == 255)
    chosen = rng.choice(np.arange(len(spaces[0])),
                              size=num_ghosts, replace=False)

    for i in chosen:
        image[spaces[0][i], spaces[1][i]] = 2

    new = ""

    for x in range(len(image)):
        for y in range(len(image[0])):
            if (image[x][y] == 2): new += "E"
            if (image[x][y] == 255): new += " "
            if (image[x][y] == 0): new += "#"
        new += "\n"

    return new

if __name__ == '__main__':
    print generateMaze(4, 4, num_ghosts=3, seed=None)
