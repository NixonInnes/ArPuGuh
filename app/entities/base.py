import abc
from pyglet.shapes import Rectangle
from collections import namedtuple

from app.system.utils import Coord, Rect


class Entity(metaclass=abc.ABCMeta):
    __defaults = {
        'active': True,
        'render': True,
        'debug': False,
        'dead': False,

        'batch': None,
        'group': None,

        'x': 0.0,
        'y': 0.0,
        'width': 1.0,
        'height': 1.0,

        'mobile': False,
        'collidable': False,

        'name': 'Unnamed'
    }

    # Overwrite to update base default values
    defaults = {
    }

    # Overwrite to add additional attributes
    attributes = {
    }


    def __init__(self, **kwargs):
        defaults = {**self.__defaults, **self.defaults}
        for attr, default in defaults.items():
            setattr(self, attr, kwargs.get(attr, default))
    
        self.prev_coord = Coord(self.x, self.y)    

        for attr, default in self.attributes.items():
            setattr(self, attr, kwargs.get(attr, default))

        self.init(**kwargs)


    @abc.abstractmethod
    def init(self, **kwargs):
        pass
    
    @abc.abstractmethod
    def update(self):
        pass


    @abc.abstractmethod
    def draw(self):
        pass

    @property
    def coord(self):
        return Coord(self.x, self.y)
    

    @property
    def center(self):
        return Coord(self.x+self.width/2, self.y+self.height/2)


    @property
    def rect(self):
        return Rect(self.x, self.y, self.x+self.width, self.y+self.height)


    @property
    def x_1D(self):
        return (self.x, self.x+self.width)
    

    @property
    def y_1D(self):
        return (self.y, self.y+self.height)


    def collides_with(self, entity):
        r1 = self.rect
        r2 = entity.rect

        if (r1.x1 >= r2.x2) or (r1.x2 <= r2.x1) or (r1.y1 >= r2.y2) or (r1.y2 <= r2.y1):
            return False
        return True


    def on_collision(self, entity):
        pass
        
        
class Stats:
    __base = 16
    __stats = [
        'str',
        'dex',
        'wis',
        'int',
        'con',
        'lck'
    ]

    def __init__(self, modifiers={}):
        for stat in self.__stats:
            setattr(self, stat, self.__base+modifiers.get(stat, 0))

        self.hp = self.base_hp
        self.mn = self.base_mn

    @property
    def base_hp(self):
        return self.con*20

    @property
    def base_mn(self):
        return self.wis*40
    
    

    






