import numpy as np
import nengo
import cellular
import continuous
import body

class NetPlayer(nengo.Network):

    def __init__(self, **kwargs):

        super(self, NetPlayer).__init__(**kwargs)

        self.move = nengo.Node(move, size_in = 2, size_out = 2)
        self.food = nengo.Node(food, size_in = 2, size_out = 2)
        self.obstacles = nengo.Node(obstacles, size_in = 2, size_out = 2)
        
