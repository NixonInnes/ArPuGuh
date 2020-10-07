import math
from uuid import uuid4
from collections import namedtuple

import config


RGB = namedtuple('RGB', ('r', 'g', 'b'))
Coord = namedtuple('Coord', ('x', 'y'))


def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def calc_1D_intersect(a0, a1, b0, b1):
    if a0 >= b0 and a1 <= b1: # Contained
        return a1 - a0
    elif a0 < b0 and a1 > b1: # Contains
        return b1 - b0
    elif a0 < b0 and a1 > b0: # Intersects right
        return a1 - b0
    elif a1 > b1 and a0 < b1: # Intersects left
        return b1 - a0
    else: # No intersection (either side)
        return 0.0


def get_unique_name():
    return str(uuid4())


compass_points = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']


compass_opposite = {
    'n': 's',
    'ne': 'sw',
    'e': 'w',
    'se': 'nw',
    's': 'n',
    'sw': 'ne',
    'w': 'e',
    'nw': 'se'
}


compass_coord_mod = {
    'n': Coord(0, 1),
    'ne': Coord(1, 1),
    'e': Coord(1, 0),
    'se': Coord(1, -1),
    's': Coord(0, -1),
    'sw': Coord(-1, -1),
    'w': Coord(-1, 0),
    'nw': Coord(-1, 1)
}


def env_bound(value):
    value = int(round(value))
    return max(config.env_param_low_bound, 
               min(config.env_param_high_bound, value))


def color_bound(value):
    return int(max(0, min(value, 255)))
