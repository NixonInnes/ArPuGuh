import os
import itertools
import noise
import numpy as np
from collections import namedtuple
from random import randint
from PIL import Image, ImageDraw

from pyglet.graphics import Batch, OrderedGroup
from pyglet.image import load as load_image
from pyglet.sprite import Sprite

import config
from app import world
from app.database import session, models
from app.entities.block import Block
from app.entities.npc import NPC
from app.entities.wall import Wall
from app.system.exceptions import NoDatabaseModel, DirectionMismatch
from app.system.utils import RGB, Coord, env_bound


class LazyChunkLoader:

    def __init__(self, direction):
        self.direction = direction

    def __get__(self, obj, objtype=None):
        dir_map = {
            'n':  (obj.x, obj.y+1),
            'ne': (obj.x+1, obj.y+1),
            'e':  (obj.x+1, obj.y),
            'se': (obj.x+1, obj.y-1),
            's':  (obj.x, obj.y-1),
            'sw': (obj.x-1, obj.y-1),
            'w':  (obj.x-1, obj.y),
            'nw': (obj.x-1, obj.y+1)
        }
        print(f'Loading chunk {dir_map[self.direction]}')
        return world.load_chunk(*dir_map[self.direction], create=True)


class Chunk:
    n = LazyChunkLoader('n')
    ne = LazyChunkLoader('ne')
    e = LazyChunkLoader('e')
    se = LazyChunkLoader('se')
    s = LazyChunkLoader('s')
    sw = LazyChunkLoader('sw')
    w = LazyChunkLoader('w')
    nw = LazyChunkLoader('nw')


    def __init__(self, x, y, name=None):
        self.db_obj = None
        self.x = x
        self.y = y
        self.width = config.window_width
        self.height = config.window_height

        self.n_rows = config.window_height//config.block_height
        self.n_cols = config.window_width//config.block_width

        self.players = []
        self.npcs = []
        self.walls = []
        self.objects = []
        
        self.sprite = None

        self.name = name if name else \
                    f'{self.__class__.__name__}({self.x}, {self.y})'
     
        self.grid = []
        self.blocks = []

        self.draw_batch = Batch()
        self.background = OrderedGroup(0)
        self.midground = OrderedGroup(1)
        self.foreground = OrderedGroup(2)


    @property
    def game_objects(self):
        return self.players + self.npcs + self.walls + self.objects


    @property
    def attackable_objects(self):
        return self.players + self.npcs
    

    @property
    def coord(self):
        return Coord(self.x, self.y)
    

    # TODO: num of loops over the blocks is too damn high!
    def load_blocks(self):
        if self.db_obj is None:
            raise NoDatabaseObject
        self.blocks = [Block.load_from_db_obj(block)
                       for block in self.db_obj.blocks]
        self.grid = np.array(sorted(self.blocks, 
                                    key=lambda block:(block.y, block.x))).reshape(self.n_rows,
                                                                                  self.n_cols)
        self.link_blocks()

    def set_walls(self):
        self.walls.clear()
        for block in self.blocks:
            if block.collidable:
                wall = Wall(x=block.x,
                            y=block.y,
                            width=block.width,
                            height=block.height,
                            color=block.color,
                            # Note: don't really need to draw these
                            #color=(255,0,0),
                            #batch=self.draw_batch
                            )
                self.objects.append(wall)


    def link_blocks(self):
        for r_i, row in enumerate(self.grid):
            for b_i, block in enumerate(row):
                if r_i != 0:
                    block.s = self.grid[r_i-1][b_i]
                    block.sw = self.grid[r_i-1][b_i-1]
                    if b_i+1 != self.n_cols:
                        block.se = self.grid[r_i-1][b_i+1]
                if b_i != 0:
                    block.w = self.grid[r_i][b_i-1]


    @staticmethod
    def load(x, y, create=False):
        loaded_chunk = session.query(models.Chunk).filter_by(x=x, y=y).first()

        if loaded_chunk is None:
            if create:
                chunk = Chunk(x, y)
                chunk.build_blocks()
                chunk.save()
            else:
                return None
        else:
            chunk = Chunk.load_from_db_obj(loaded_chunk)

        if not os.path.isfile(chunk.img_file):
            chunk.build_img()
        
        bg_img = load_image(chunk.img_file)
        chunk.sprite = Sprite(bg_img, 0, 0, 
                              batch=chunk.draw_batch, 
                              group=chunk.background)

        chunk.set_walls()
        chunk.add_npcs(5)
        
        return chunk


    @staticmethod
    def load_from_db_obj(db_obj):
        chunk = Chunk(x=db_obj.x,
                      y=db_obj.y,
                      name=db_obj.name)
        
        chunk.db_obj = db_obj
        chunk.load_blocks()
        return chunk


    def save(self):
        if self.db_obj is None:
            self.db_obj = models.Chunk()
        self.db_obj.x = self.x
        self.db_obj.y = self.y
        self.db_obj.name = self.name

        for block in self.blocks:
            block.save(commit=False)
            block.db_obj.chunk_id = self.db_obj.id
            
        session.add(self.db_obj)
        session.commit()


    @property
    def img_file(self):
        return f'app/assets/chunks/{self.name}.png'


    def gen_z_map(self):
        shape = (config.window_width, config.window_height)
        scale = 5000
        octaves = 6
        persistence = 0.4
        lacunarity = 2.0
        seed = config.map_seed

        z_map = np.zeros(shape)

        x_i = np.linspace(self.x*config.window_width,
                          self.x*config.window_width + config.window_width - config.block_width,
                          config.window_width//config.block_width).astype(int)
        y_i = np.linspace(self.y*config.window_height,
                          self.y*config.window_height + config.window_height - config.block_height,
                          config.window_height//config.block_height).astype(int)

        z_map_x, z_map_y = np.meshgrid(x_i, y_i)

        z_map = np.vectorize(noise.pnoise2)(z_map_x/scale,
                                            z_map_y/scale,
                                            octaves=octaves,
                                            persistence=persistence,
                                            lacunarity=lacunarity,
                                            repeatx=config.window_width,
                                            repeaty=config.window_height,
                                            base=config.map_seed)
        return z_map*300


    def gen_foliage_map(self):
        shape = (config.window_width, config.window_height)
        scale = 10000
        octaves = 6
        persistence = 0.4
        lacunarity = 2.0
        seed = config.map_seed//2

        z_map = np.zeros(shape)

        x_i = np.linspace(self.x*config.window_width,
                          self.x*config.window_width + config.window_width - config.block_width,
                          config.window_width//config.block_width).astype(int)
        y_i = np.linspace(self.y*config.window_height,
                          self.y*config.window_height + config.window_height - config.block_height,
                          config.window_height//config.block_height).astype(int)

        z_map_x, z_map_y = np.meshgrid(x_i, y_i)

        z_map = np.vectorize(noise.pnoise2)(z_map_x/scale,
                                            z_map_y/scale,
                                            octaves=octaves,
                                            persistence=persistence,
                                            lacunarity=lacunarity,
                                            repeatx=config.window_width,
                                            repeaty=config.window_height,
                                            base=config.map_seed)
        return z_map*300
    

    def build_blocks(self):
        self.grid = []
        n_rows = self.height//config.block_height
        n_cols = self.width//config.block_width

        z_map = self.gen_z_map()
        foliage_map = self.gen_foliage_map()
        for y_i in range(self.n_rows):
            row = []
            for x_i in range(self.n_cols):
                new_block = Block(x=x_i*config.block_width, 
                                  y=y_i*config.block_height,
                                  z=env_bound(z_map[y_i][x_i]),
                                  foliage=env_bound(foliage_map[y_i][x_i]))
                row.append(new_block)
            self.grid.append(row)
        self.link_blocks()
        self.save()
        self.blocks = list(itertools.chain.from_iterable(self.grid))


    def build_img(self):
        img = Image.new(mode='RGB', 
                        size=(self.width, self.height), 
                        color=(255,255,255))
        for block in self.blocks:
            block.img_draw(img)
        img.save(self.img_file)


    def add_npcs(self, n):
        for i in range(n):
            npc = NPC(chunk=self,
                      x=randint(0, config.window_width),
                      y=randint(0, config.window_height),
                      width=50,
                      height=50,
                      group=self.midground)


    def update(self):
        collision_checked = []
        for obj in self.game_objects:
            obj.update()
            if obj.mobile:
                for other_obj in self.game_objects:
                    if other_obj is obj:
                        pass
                    elif other_obj.collidable:
                        if obj.collides_with(other_obj):
                            obj.on_collision(other_obj)
                            other_obj.on_collision(obj)
            collision_checked.append(obj)
