import random
import numpy as np
import nengo
import cellular
import continuous

class Pacman(continuous.Body):
    color = "pink"
    def __init__(self):
        self.score = 0

# Pacman Extensibility
