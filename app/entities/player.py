import numpy as np
import math
from random import randint
from pyglet import clock
from pyglet.image import load as load_image
from pyglet.sprite import Sprite
from pyglet.window import key
from pyglet.text import Label

import config
from app import world
from app.entities.base import Stats
from app.entities.base_mobile import MobileEntity
from app.entities.misc import TemporaryEntity
from app.entities.projectile import Projectile
from app.system.dice import d6, d20
from app.system.utils import calc_1D_intersect, Coord, distance, RGB


class Player(MobileEntity):
    overwrite = {
        'image_file': 'app/assets/player.png',
        'damage_text_color': (200,0,0,255),
        'chunk_container': 'players'
    }


    def post_init(self, **kwargs):
        self.key_handler = key.KeyStateHandler()
         

    def out_of_bounds(self, direction):
        self.move_to_chunk(getattr(self.chunk, direction))
        if direction == 'e':
            self.x = 0
        elif direction == 'w':
            self.x = config.window_width - self.width
        elif direction == 'n':
            self.y = 0
        elif direction == 's':
            self.y = config.window_height - self.height


    def move_to_chunk(self, chunk):
        if self.chunk and self in self.chunk.players:
            self.chunk.players.remove(self)
        
        self.chunk = chunk
        chunk.players.append(self)
        self.set_sprite_render(chunk.foreground)
        self.moving_to = None


    def parse_keys(self):
        x, y = self.x, self.y

        if self.key_handler[key.UP]:
            y += self.speed
        if self.key_handler[key.RIGHT]:
            x += self.speed
        if self.key_handler[key.DOWN]:
            y -= self.speed
        if self.key_handler[key.LEFT]:
            x -= self.speed

        move_to = Coord(x, y)
        if move_to != self.coord:
            self.moving_to = move_to

        if self.key_handler[key.A]:
            self.attack()

        if self.key_handler[key.S]:
            self.fire_proj()

        if self.key_handler[key.D]:
            self.in_combat_with.clear()


    def after_death(self):
        corpse = TemporaryEntity(x=self.x, 
                                 y=self.y,
                                 chunk=self.chunk,
                                 batch=self.chunk.draw_batch,
                                 group=self.chunk.midground)


    def update(self):
        self.check_state()
        if not self.dead:
            self.update_cooldowns()
            self.parse_keys()
            self.move()
            self.check_bounds()
            self.update_sprites()
        else:
            self.after_death()

