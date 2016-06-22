import random
import numpy as np
import nengo
import cellular
import continuous

class Ghost(continuous.Body):

    # Ghost attributes
    color = "red"
    speed = 10
    rotate = 5
