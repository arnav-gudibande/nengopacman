# Nengo Pacman

![pacman](https://cloud.githubusercontent.com/assets/15108659/16967655/ecd43682-4dbe-11e6-9c5c-04300d215cc0.gif)

## Installation

This project is compatible with Python 2.7.x and has dependencies on Nengo and Nengo GUI. Ensure you have installed both before running the project.

* Install [nengo](https://github.com/nengo/nengo)
* Use pip to install the nengo gui
  * `pip install nengo_gui`

Next, clone/fork this project from Github and run it from a terminal.

 `nengo pacman.py`
 

## Neural Network Architecture

<img width="1358" alt="screen shot 2016-07-19 at 1 55 27 pm" src="https://cloud.githubusercontent.com/assets/15108659/16966338/fad4e19c-4db8-11e6-9fc4-72757f9dcb98.png">

The game is organized into the pacman world and each individual instance of pacman.

The world owns the game environment, score and sensor data for each pacman. Additionally, the world collects information on distance from wall to pacman, food availability, enemy distance, etc. Using its respective nodes, it sends this information to the pacman's ensembles.

The pacman ensembles, consisting of the food, enemy and obstacles, apply functions on the incoming data and pass it on to the move ensemble. Finally, the move ensemble aggregates the sensory input and determines the speed and direction for the pacman to move in, thereby continuing the game.

The control algorithm for the movement of the pacman lies in the functions that are applied by the food, obstacles and enemy ensembles. Their sensitivity, strength and functionality can be edited by changing the transform, nuerons, and synapse parameters.

## Examples

The following examples demonstrate features of the API

### Add a pacman to the game

First, create a new instance of pacman in `pacman.py`:

`myPacman = body.Player("pacman", 4, 2, "yellow", 70, 20)`

The paramaters passed into the pacman signify (respectively):
* Type of player in the world
* ID of player (n number)
* Size of player
* Color of player
* Linear speed of player
* Rotational speed of player

Now, add the pacman to the game:

`pacmen.append(myPacman)`

### Add a ghost to the game

Create a new instance of a ghost:

`myGhost4 = body.Player("ghost", "seeking", 2, "orange", 5, 5)`

The paramaters passed into the ghost signify (respectively):
* Type of player in the world
* State of player (either seeking or running away)
* Size of player
* Color of player
* Linear speed of player
* Rotational speed of player

### Edit sensory input

In `pacman.py`, simply edit transform parameters to adjust pacman's sensory input

`nengo.Connection(food[0], move[1], transform = 3)`

This adjusts the way pacman turns toward the food


`nengo.Connection(pacnet.obstacles[[1,2,3]], obstacles, transform = 1, synapse = 0.`

This makes pacman more sensitive to enemies

### Change maze dimensions

`mymap = maze.generateMaze(8,20)`

Note: Rows must be in multiples of 2 and columns in 10

## Usage

When creating your own neural control network & algorithm to run the game, apply changes on the `myModel.py` using the framework provided. To run your version of pacman after completing `myModel.py`, simply run `nengo myModel.py` to execute the game.

## Acknowlegments

[@arnav-gudibande](https://github.com/arnav-gudibande), [@tcstewar](https://github.com/tcstewar)
