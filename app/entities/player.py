import numpy as np
import math
import pyglet
from pyglet.window import key
from pyglet.graphics import GL_POINTS

import config
from app import world
from app.entities.base import Entity
from app.system.utils import calc_1D_intersect

SPRINT_MOD = 2

class Player(Entity):
    defaults = {
        'collidable': True,
        'mobile': True,
        'width': 50,
        'height': 50
    }

    attributes = {
        'dead': False,
        'speed': 5,
        'sprinting': False,
        'image_file': 'app/assets/player.png',
        'moving_to': None,
        'chunk': None
    }

    def init(self, **kwargs):
        self.image = pyglet.image.load(self.image_file)
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y)
        self.key_handler = key.KeyStateHandler()


    def check_bounds(self):
        if (self.x + self.width) > config.window_width:
            self.move_to_chunk(self.chunk.e)
            self.x = 0
        
        elif self.x < 0:
            self.move_to_chunk(self.chunk.w)
            self.x = config.window_width - self.width

        elif (self.y + self.height) > config.window_height:
            self.move_to_chunk(self.chunk.n)
            self.y = 0

        elif self.y < 0:
            self.move_to_chunk(self.chunk.s)
            self.y = config.window_height - self.height


    def move_to_chunk(self, chunk):
        if self.chunk:
            self.chunk.players.remove(self)
        
        self.chunk = chunk
        chunk.players.append(self)
        self.sprite.batch = chunk.draw_batch
        self.sprite.group = chunk.foreground


    def on_collision(self, obj):
        x_intersect = calc_1D_intersect(*self.x_1D, *obj.x_1D)
        y_intersect = calc_1D_intersect(*self.y_1D, *obj.y_1D)

        if x_intersect < y_intersect:
            if self.center.x < obj.center.x:
                self.x = obj.x - self.width
            else:
                self.x = obj.x + obj.width
        else:
            if self.center.y < obj.center.y:
                self.y = obj.y - self.height
            else:
                self.y = obj.y + obj.height


    def update(self):
        if self.sprinting:
            speed = self.speed*SPRINT_MOD
        else:
            speed = self.speed

        if self.moving_to:
            dist_from_target = np.sqrt((self.x-self.moving_to.x)**2 + 
                                       (self.y-self.moving_to.y)**2)
            
            if dist_from_target <= speed:
                self.x = self.moving_to.x
                self.y = self.moving_to.y
            else:
                dist_ratio = speed/dist_from_target
                self.x = (1.0 - dist_ratio)*self.x + dist_ratio*self.moving_to.x
                self.y = (1.0 - dist_ratio)*self.y + dist_ratio*self.moving_to.y
        else:
            if self.key_handler[key.UP]:
                self.y += speed
            if self.key_handler[key.RIGHT]:
                self.x += speed
            if self.key_handler[key.DOWN]:
                self.y -= speed
            if self.key_handler[key.LEFT]:
                self.x -= speed

        self.check_bounds()
        self.sprite.update(x=self.x, y=self.y)


    def draw(self):
        self.sprite.draw()
