import numpy as np
import math
import pyglet
from pyglet.window import key

import config
from system.component import PhysicalComponent
from system.utils import calc_1D_intersect

SPRINT_MOD = 2

class Player(PhysicalComponent):

    def __init__(self, *args, **kwargs):
        """
        Creates a sprite using a player image.
        """
        super(Player, self).__init__(*args, **kwargs)
        self.collidable = False
        self.mobile = True
        self.dead = False
        self.speed = kwargs.get('speed', 5)
        self.image = pyglet.image.load('assets/player.png')
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y, 
                                           batch=self.batch,
                                           group=self.group)
        self.key_handler = key.KeyStateHandler()
        self.move_target = None
        self.sprint = False


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
        if self.sprint:
            speed = self.speed*SPRINT_MOD
        else:
            speed = self.speed

        if self.move_target:
            dist_from_target = np.sqrt((self.x-self.move_target.x)**2 + 
                                         (self.y-self.move_target.y)**2)
            
            if dist_from_target <= speed:
                self.x = self.move_target.x
                self.y = self.move_target.y
            else:
                dist_ratio = speed/dist_from_target
                self.x = (1.0 - dist_ratio)*self.x + dist_ratio*self.move_target.x
                self.y = (1.0 - dist_ratio)*self.y + dist_ratio*self.move_target.y
        else:
            if self.key_handler[key.UP]:
                self.y += speed
            if self.key_handler[key.RIGHT]:
                self.x += speed
            if self.key_handler[key.DOWN]:
                self.y -= speed
            if self.key_handler[key.LEFT]:
                self.x -= speed

        self.sprite.update(x=self.x, y=self.y)

    def draw(self):
        self.sprite.draw()
