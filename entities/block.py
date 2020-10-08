import statistics
from random import randint
from numpy.random import normal
from PIL import Image, ImageDraw

import config
from database import session, models
from system.utils import (compass_points, compass_opposite, compass_coord_mod, RGB,
    env_bound, color_bound)
from system.exceptions import NoDatabaseModel, DirectionMismatch

BLOCK_ENV_PARAMS = {
    'z': (-100, 100),
    'foliage': (0, 100)
}

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
        #elif not getattr(other, '_'+compass_opposite[self.direction]) == obj:
        #    raise DirectionMismatch(f'Direction mismatch between '
        #                            f'{obj}->{self.direction}->{other}, {other}->{compass_opposite[self.direction]}->{getattr(other, compass_opposite[self.direction])}')


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
        #self._mod_foliage()

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
        if self.z < config.sea_level:
            r = min(50 + self.z*10, 255)
            g = min(150 + self.z*10, 255)
            b = 255
            
        elif self.z < config.grass_level:
            r = min(0 + self.z, 255)
            g = min(100 + self.z, 255)
            b = min(0 + self.z, 255)
        else:
            r = min(25 + self.z, 255)
            g = min(100 + self.z, 255)
            b = min(25 + self.z, 255)
        self.color = RGB(r, g, b)

    def _set_collidable(self):
        self.collidable = True if self.z > NOOB_WALL else False

    @property
    def _foliage(self):
        return int(round(max(0, (self.foliage+100)/2 - (self.z/3)**2)))

    @staticmethod
    def load(id):
        loaded_block = session.query(models.Block).get(id)
        if loaded_block is None:
            return
        return Block.load_from_db_obj(loaded_block)

    @staticmethod
    def load_from_db_obj(db_obj):
        block = Block(**db_obj.__dict__)
        block.db_obj = db_obj
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
        for direction in ['w', 's']:
            block = getattr(self, direction)
            if block:
                lower_adjs.append(block)
        
        if lower_adjs:
            height_diff = self.z - statistics.mean([b.z for b in lower_adjs])//1
        else:
            height_diff = 0

        if height_diff <= 0:
            color_mod = 0
        else:
            color_mod = -5 * height_diff

        border_color = RGB(color_bound(self.color.r + color_mod),
                           color_bound(self.color.g + color_mod),
                           color_bound(self.color.b + color_mod))

        if self.collidable:
            draw.rectangle(self.pil_coords, 
                           fill=self.color, 
                           outline=(200,0,0))
        else:
            draw.rectangle(self.pil_coords, 
                           fill=self.color, 
                           outline=border_color)
        grass_image = Image.open('assets/foliage/grass.png')
        for i in range(self._foliage//10):
            img.paste(grass_image,
                      (randint(self.pil_coords[0], self.pil_coords[2]),
                       randint(self.pil_coords[3], self.pil_coords[1])),
                      grass_image)

    def __eq__(self, other):
        return self.db_obj.id == other.db_obj.id

    def __repr__(self):
        return f'<Block({self.x}, {self.y})>'