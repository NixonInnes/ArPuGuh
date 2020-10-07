import abc
from pyglet.shapes import Rectangle
from collections import namedtuple

from . import utils

Coord = namedtuple('Coord', ('x', 'y'))
Rect = namedtuple('Rect', ('x1', 'y1', 'x2', 'y2'))


class Component(metaclass=abc.ABCMeta):

    def __init__(self, **kwargs):
        self.active = kwargs.get('active', True)
        self.render = kwargs.get('render', True)
        self.debug = kwargs.get('debug', False)
        self.batch = kwargs.get('batch', None)
        self.group = kwargs.get('group', None)
        self.x = kwargs.get('x', 0.0)
        self.y = kwargs.get('y', 0.0)
        self.last_pos = Coord(self.x, self.y)
        self.name = kwargs.get('name', 
                               f'{self.__class__.__name__}_{utils.get_unique_name()}')

    @property
    def center(self):
        return Coord(self.x+self.width/2, self.y+self.height/2)

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def draw(self):
        pass


class PhysicalComponent(Component):
    def __init__(self, **kwargs):
        super(PhysicalComponent, self).__init__(**kwargs)
        self.height = kwargs.get('height', 1.0)
        self.width = kwargs.get('width', 1.0)
        self.collidable = kwargs.get('collidable', True)
        self.mobile = kwargs.get('mobile', False)

    @property
    def rect(self):
        return Rect(self.x, self.y, self.x+self.width, self.y+self.height)

    @property
    def x_1D(self):
        return (self.x, self.x+self.width)
    
    @property
    def y_1D(self):
        return (self.y, self.y+self.height)


    def collides_with(self, comp):
        r1 = self.rect
        r2 = comp.rect

        if (r1.x1 >= r2.x2) or (r1.x2 <= r2.x1) or (r1.y1 >= r2.y2) or (r1.y2 <= r2.y1):
            return False
        return True

    @abc.abstractmethod
    def on_collision(self, comp):
        pass






