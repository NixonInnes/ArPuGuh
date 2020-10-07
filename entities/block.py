import statistics
from random import randint
from numpy.random import normal
from PIL import Image, ImageDraw

import config
from database import session, models
from system.utils import (compass_points, compass_opposite, compass_coord_mod, RGB,
    env_bound, color_bound)
from system.exceptions import NoDatabaseModel, DirectionMismatch

BLOCK_ENV_PARAMS = [
    'z',
    'foliage'
]

NOOB_WALL = 25

class CompassPoint:
    def __init__(self, direction):
        self.direction = direction
        self.block = None
    
    def __get__(self, obj, objtype):
        return getattr(obj, '_'+self.direction)
    
    def __set__(self, obj, other):
        setattr(obj, '_'+self.direction, other)
        if getattr(other, '_'+compass_opposite[self.direction]) is None:
            setattr(other, '_'+compass_opposite[self.direction], obj)
        elif getattr(other, '_'+compass_opposite[self.direction]) is not obj:
            raise DirectionMismatch(f'Direction mismatch between '
                                    f'{obj}->{self.direction}->{other}, {other}->{compass_opposite[self.direction]}->{getattr(other, compass_opposite[self.direction])}')


class Block:
    n = CompassPoint('n')
    ne = CompassPoint('ne')
    e = CompassPoint('e')
    se = CompassPoint('se')
    s = CompassPoint('s')
    sw = CompassPoint('sw')
    w = CompassPoint('w')
    nw = CompassPoint('nw')

    def __init__(self, x, y,
                 **kwargs):
        self.db_obj = None
        self.x = x
        self.y = y
        
        self.__init_env_params(**kwargs)
        self._set_color()
        self._set_collidable()


        self.width = config.block_width
        self.height = config.block_height

        self._n = None
        self._ne = None
        self._e = None
        self._se = None
        self._s = None
        self._sw = None
        self._w = None
        self._nw = None


    def __init_env_params(self, **kwargs):
        for param in BLOCK_ENV_PARAMS:
            setattr(self, param, kwargs.get(param, randint(-10, 10)))
            setattr(self, param+'_dist_scale', kwargs.get(param+'_dist_scale', 3))

    def _set_color(self):
        r = min(100 + self.z, 255)
        g = min(100 + self.z, 255)
        b = min(100 + self.z, 255)
        self.color = RGB(r, g, b)

    def _set_collidable(self):
        self.collidable = True if self.z > NOOB_WALL else False

    @staticmethod
    def load(id):
        loaded_block = session.query(models.Block).get(id)
        if loaded_block is None:
            return
        return Block.load_from_db_obj(loaded_block)

    @staticmethod
    def load_from_db_obj(db_obj):
        block = Block(**db_obj.__dict__)
        return block

    def save(self, commit=True):
        if self.db_obj is None:
            self.db_obj = models.Block()
        self.db_obj.x = self.x
        self.db_obj.y = self.y
        for param in BLOCK_ENV_PARAMS:
            setattr(self.db_obj, param, getattr(self, param))
        session.add(self.db_obj)
        if commit:
            session.commit()

    def get_env_params(self):
        return {param:getattr(self, param) for param in BLOCK_ENV_PARAMS}

    @property
    def pil_coords(self):
        return (self.x, config.window_height-self.y, 
                self.x+config.block_width, config.window_height-self.y-config.block_height)

    @property
    def adj_blocks(self):
        return [getattr(self, direction) for direction in compass_points 
                if getattr(self, direction) is not None]
    
    def get_local(self, property_):
        properties = [getattr(self, property_)]
        properties += [getattr(block, property_) for block in self.adj_blocks]
        return statistics.mean(properties)
       
    def create_direction(self, direction):
        if direction not in compass_points:
            raise Exception('Invalid compass direction')
        coord_mod = compass_coord_mod[direction]
        env_params = {param: env_bound(self.get_local(param) + \
                                       normal(scale=getattr(self, param+'_dist_scale'))/2)
                      for param in BLOCK_ENV_PARAMS}
        new_block = Block(
            x=self.x+coord_mod.x*config.block_width,
            y=self.y+coord_mod.y*config.block_height,
            **env_params
        )
        setattr(self, direction, new_block)
        return new_block

    def img_draw(self, img):
        draw = ImageDraw.Draw(img)
        lower_adjs = []
        for direction in ['w', 'sw', 's']:
            block = getattr(self, direction)
            if block:
                lower_adjs.append(block)
        
        if lower_adjs:
            height_diff = self.z - statistics.mean([b.z for b in lower_adjs])
        else:
            height_diff = 0

        border_color = RGB(*[color_bound(200-height_diff**2)]*3)

        if self.collidable:
            draw.rectangle(self.pil_coords, 
                           fill=self.color, 
                           outline=(200,0,0))
        else:
            draw.rectangle(self.pil_coords, 
                           fill=self.color, 
                           outline=border_color)
        grass_image = Image.open('assets/foliage/grass.png', mode='alpha')
        for i in range(max(20, (self.foliage+100)//5)):
            img.paste(grass_image,
                      (randint(self.pil_coords[0], self.pil_coords[2]),
                       randint(self.pil_coords[3], self.pil_coords[1])))
        
    def __repr__(self):
        return f'<Block({self.x}, {self.y})>'