import random
import numpy as np
import nengo
import cellular
import continuous

class Body(continuous.Body):

    def __init__(self, typeBody, state, size, color, speed, rotate):
        setattr(self, 'typeBody', typeBody)
        setattr(self, 'size', size)
        setattr(self, 'color', color)
        setattr(self, 'speed', speed)
        setattr(self, 'rotate', rotate)

        if(typeBody=="pacman"):
            self.score = 0
