import itertools
import numpy as np
from collections import namedtuple
from random import randint
from PIL import Image, ImageDraw

import config
from database import session, models
from entities.block import Block
from system.exceptions import NoDatabaseModel, DirectionMismatch
from system.utils import RGB


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
        print(f'loading chunk {dir_map[self.direction]}')
        return Chunk.load(*dir_map[self.direction], create=True)


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

        if name is None:
            self.name = f'{self.__class__.__name__}({self.x}, {self.y})'
        else:
            self.name = name      

        self.grid = []
        self.blocks = []

    def load_blocks(self):
        if self.db_obj is None:
            raise NoDatabaseObject
        self.blocks = [Block.load_from_db_obj(block)
                       for block in self.db_obj.blocks]
        self.grid = np.array(sorted(self.blocks, 
                                    key=lambda block:(block.y, block.x))).reshape(self.n_rows,
                                                                                  self.n_cols)
        self.link_blocks()

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

    def update(self):
        if self.db_obj is None:
            raise NoDatabaseObject
        self.x = self.db_obj.x
        self.y = self.db_obj.y
        self.width = self.db_obj.width
        self.height = self.db_obj.height
        self.name = self.db_obj.name
        self.load_blocks()


    @staticmethod
    def load(x, y, create=False):
        loaded_chunk = session.query(models.Chunk).filter_by(x=x, y=y).first()

        if loaded_chunk is None:
            if create:
                chunk = Chunk(x, y)
                chunk.build_blocks()
                chunk.save()
                return chunk
            return None

        chunk = Chunk.load_from_db_obj(loaded_chunk)
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
        return f'assets/chunks/{self.name}.png'
    
    def build_blocks(self):
        chunk_w = Chunk.load(self.x-1, self.y)
        chunk_s = Chunk.load(self.x, self.y-1)
        self.grid = []
        n_rows = self.height//config.block_height
        n_cols = self.width//config.block_width

        for r_i in range(n_rows):
            row = []
            for c_i in range(n_cols):

                # FIRST COLUMN
                if c_i == 0:

                    # FIRST ROW, FIRST COLUMN
                    if r_i == 0: # First row
                        if chunk_s and chunk_w:
                            chunk_w.grid[0][-1].se = chunk_s.grid[-1][0]
                            new_block = chunk_w.grid[0][-1].create_direction('e')
                            new_block.x, new_block.y = 0, 0
                        elif chunk_w:
                            new_block = chunk_w.grid[0][-1].create_direction('e')
                            new_block.x, new_block.y = 0, 0
                        elif chunk_s:
                            new_block = chunk_s.grid[-1][0].create_direction('n')
                            new_block.x, new_block.y = 0, 0
                        else:
                            new_block = Block(0, 0)
                    
                    # OTHER ROWS. FIRST COLUMN
                    else:
                        if chunk_w:
                            self.grid[r_i-1][0].nw = chunk_w.grid[r_i][-1]
                            self.grid[r_i-1][0].w = chunk_w.grid[r_i-1][-1]
                            self.grid[r_i-1][0].sw = chunk_w.grid[r_i-2][-1]
                        new_block = self.grid[r_i-1][0].create_direction('n')
                        new_block.se = self.grid[r_i-1][c_i+1]

                        if chunk_w:
                            new_block.w = chunk_w.grid[r_i][-1]
                
                # LAST COLUMN
                elif c_i == n_cols-1: # Last column
                    new_block = row[-1].create_direction('e')

                    # FIRST ROW, LAST COLUMN
                    if r_i == 0:
                        pass

                    # OTHER ROWS, LAST COLUMN
                    else:
                        new_block.s = self.grid[r_i-1][c_i]
                        new_block.sw = self.grid[r_i-1][c_i-1]
                
                # OTHER COLUMNS
                else:
                    new_block = row[-1].create_direction('e')
                    
                    # FIRST ROW, OTHER COLUMNS
                    if r_i == 0:
                        if chunk_s:
                            new_block.sw = chunk_s.grid[-1][c_i-1]
                            new_block.s = chunk_s.grid[-1][c_i]
                            new_block.se = chunk_s.grid[-1][c_i+1]

                    # OTHER ROWS, OTHER COLUMNS
                    else:
                        new_block.sw = self.grid[r_i-1][c_i-1]
                        new_block.s = self.grid[r_i-1][c_i]
                        new_block.se = self.grid[r_i-1][c_i+1]
                
                row.append(new_block)
            self.grid.append(row)
            row = []
        self.save()
        self.blocks = list(itertools.chain.from_iterable(self.grid))

    def build_img(self):
        img = Image.new(mode='RGB', size=(self.width, self.height), color=(255,255,255))
        for block in self.blocks:
            block.img_draw(img)
        img.save(self.img_file)
