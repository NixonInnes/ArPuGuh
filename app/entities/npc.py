import numpy as np
from random import randint
from pyglet import clock
from pyglet.image import load as load_image
from pyglet.sprite import Sprite
from pyglet.text import Label

import config
from app.entities.base import Stats
from app.entities.base_mobile import MobileEntity
from app.entities.misc import TemporaryEntity
from app.system.dice import d6
from app.system.utils import calc_1D_intersect, Coord, distance


class NPC(MobileEntity):
    overwrite = {
        'rest_time': 0,
        'aggro_time': 600,
        'aggro_cooldown': 600
    }

    def after_collision(self, obj):
        self.rest()


    def rest(self):
        self.moving_to = None
        self.rest_time = randint(1, (3600/self.speed)//1)


    def wander(self):
        if self.rest_time:
            self.rest_time -= 1
        else:
            self.moving_to = Coord(self.x+randint(-((self.speed**3)/2)//1, 
                                                  ((self.speed**3)/2)//1),
                                   self.y+randint(-((self.speed**3)/2)//1, 
                                                  ((self.speed**3)/2)//1))


    def do_idle(self):
        if self.moving_to is None:
            self.wander()
        elif self.coord == self.moving_to:
            self.rest()


    def do_combat(self):
        found_entity = False
        remove_from_combat = []
        for entity in self.in_combat_with:
            if entity.dead:
                remove_from_combat.append(entity)
            elif entity.chunk == self.chunk:
                found_entity = True
                self.moving_to = entity.coord
                self.aggro_cooldown = self.aggro_time
                self.attack()
                break
        [self.in_combat_with.remove(entity) for entity in remove_from_combat]
        
        if not found_entity:
            self.aggro_cooldown -= 1
    
        if self.aggro_cooldown < 1:
            self.in_combat = False
            self.in_combat_with.clear()


    def out_of_bounds(self, direction):
        if direction == 'e':
            self.x = config.window_width - self.width
        elif direction == 'w':
            self.x = 0
        elif direction == 'n':
            self.y = config.window_height - self.height
        elif direction == 's':
            self.y = 0
        self.rest()


    def after_death(self):
        corpse = TemporaryEntity(x=self.x, 
                                 y=self.y,
                                 chunk=self.chunk,
                                 batch=self.chunk.draw_batch,
                                 group=self.chunk.midground)
