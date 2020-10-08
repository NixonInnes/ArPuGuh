import numpy as np
import pyglet
from random import randint

import config
from app.entities.base import Entity
from app.system.utils import calc_1D_intersect


class Mob(Entity):

    def __init__(self, *args, **kwargs):
        """
        Creates a sprite using a ball image.
        """
        super(Mob, self).__init__(*args, **kwargs)
        self.collidable = False
        self.mobile = True
        self.dead = False
        self.death_timer = 300
        self.speed = kwargs.get('speed', 5)
        self.image = pyglet.image.load('app/assets/mob.png')
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y, 
                                           batch=self.batch,
                                           group=self.group)

        self.steps = 0
        self.last_dx = 0
        self.last_dy = 0
        self.rest_time = 0

    def on_collision(self, obj):
        self.steps = 0
        x_intersect = calc_1D_intersect(*self.x_1D, *obj.x_1D)
        y_intersect = calc_1D_intersect(*self.y_1D, *obj.y_1D)

        if x_intersect < y_intersect:
            if self.x < obj.x:
                self.x = obj.x - self.width
            else:
                self.x = obj.x + obj.width
        else:
            if self.y < obj.y:
                self.y = obj.y - self.height
            else:
                self.y = obj.y + obj.height

    def move(self):
        self.wander()
        self.check_bounds()

    def wander(self):
        if self.rest_time:
            self.rest_time -= 1
        else:
            if self.steps < 1:
                self.rest_time = randint(0, self.speed**3)
                dx = randint(-1, 1)
                dy = randint(-1, 1)
                self.steps = randint(3, self.speed**2)
            else:
                dx = self.last_dx
                dy = self.last_dy

            self.x += self.speed * dx
            self.y += self.speed * dy

            self.steps -= 1
            self.last_dx = dx
            self.last_dy = dy

    def check_bounds(self):
        if (self.x + self.width) > config.window_width:
            self.x = config.window_width - self.width
            self.steps = 0
        elif self.x < 0:
            self.x = 0
            self.steps = 0

        if (self.y + self.height) > config.window_height:
            self.y = config.window_height - self.height
            self.steps = 0
        elif self.y < 0:
            self.y = 0
            self.steps = 0

    def update(self):
        self.move()
        self.sprite.update(x=self.x, y=self.y)

    def draw(self):
        self.sprite.draw()