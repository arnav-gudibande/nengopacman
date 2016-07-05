import random
from random import randint
import numpy as np
import nengo
import cellular
import continuous
import body
from threading import Timer
import math

global agents
agents = []

class world(self):

    def addToWorld(self, Player):
        agents.append(Player)

    pacman1 = body.Player("pacman", "eating", 2, "yellow", 70, 20)

    addToWorld(pacman1)
