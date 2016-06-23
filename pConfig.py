import random
import numpy as np
import nengo
import cellular
import continuous

class Pacman(continuous.Body):
    # Initalizer attributes
    def __init__(self):
        self.score = 0

    # Pacman attributes
    size = 0.37
    color = "yellow"
    speed = 20
    rotate = 10
