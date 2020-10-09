import numpy as np
import pyglet
from random import randint

import config
from app.entities.base import Entity, Stats
from app.system.utils import calc_1D_intersect, Coord


class Mob(Entity):
    defaults = {
        'collidable': True,
        'mobile': True,
        'width': 50,
        'height': 50,
        'stat_modifiers': {'str': 0,
                           'dex': 0,
                           'wis': 0,
                           'int': 0,
                           'con': 0,
                           'lck': 0}
    }

    attributes = {
        'chunk': None,
        'dead': False,
        'sprinting': False,
        'image_file': 'app/assets/mob.png',        
        'in_combat': False,
        'in_combat_with': [],
        'aggro_time': 600,
        'aggro_cooldown': 600,
        'moving_to': None,
        'rest_time': 0
    }
        
    def init(self, **kwargs):
        self.image = pyglet.image.load('app/assets/zombie.png')
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y, 
                                           batch=kwargs.get('batch', None),
                                           group=kwargs.get('group', None))
        self.stats = Stats(modifiers=self.stat_modifiers)


    @property
    def speed(self):
        walk_speed = self.stats.dex//2
        return walk_speed


    def on_collision(self, obj):
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
        self.rest()

    def take_damage(self, source, dmg):
        if source is not None:
            self.in_combat = True
            self.in_combat_with.append(source)
        self.stats.hp -= dmg
        if self.stats.hp < 1:
            self.dead = True
        print(f'{self.name} ({self.stats.hp}/{self.stats.base_hp}) took {dmg} damage from {source.name}!')


    def check_state(self):
        if self.dead:
            print(f'{self.name} died!')
            if self.in_combat:
                for entity in self.in_combat_with:
                    if self in entity.in_combat_with:
                        entity.in_combat_with.remove(self)
            self.chunk.mobs.remove(self)
            self.sprite.delete()

        elif self.in_combat:
            if len(self.in_combat_with) < 1:
                self.in_combat = False
            else:
                found_entity = False
                for entity in self.in_combat_with:
                    if entity.chunk == self.chunk:
                        found_entity = True
                        self.moving_to = entity.coord
                        self.aggro_cooldown = self.aggro_time
                        break
                if not found_entity:
                    self.aggro_cooldown -= 1
            if self.aggro_cooldown < 1:
                self.in_combat = False
                self.in_combat_with.clear()
        else:
            if self.moving_to is None:
                self.wander()
            elif self.coord == self.moving_to:
                self.rest()


    def move(self):
        if self.moving_to:
            dist_from_target = np.sqrt((self.x-self.moving_to.x)**2 + 
                                       (self.y-self.moving_to.y)**2)
            
            if dist_from_target <= self.speed:
                self.x = self.moving_to.x
                self.y = self.moving_to.y
            else:
                dist_ratio = self.speed/dist_from_target
                self.x = (1.0 - dist_ratio)*self.x + dist_ratio*self.moving_to.x
                self.y = (1.0 - dist_ratio)*self.y + dist_ratio*self.moving_to.y


    def wander(self):
        if self.rest_time:
            self.rest_time -= 1
        else:
            self.moving_to = Coord(self.x+randint(-(self.speed**3)/2, (self.speed**3)/2),
                                   self.y+randint(-(self.speed**3)/2, (self.speed**3)/2))


    def rest(self):
        self.moving_to = None
        self.rest_time = randint(1, (3600/self.speed)//1)


    def check_bounds(self):
        if (self.x + self.width) > config.window_width:
            self.x = config.window_width - self.width
            self.rest()
        elif self.x < 0:
            self.x = 0
            self.rest()

        if (self.y + self.height) > config.window_height:
            self.y = config.window_height - self.height
            self.rest()
        elif self.y < 0:
            self.y = 0
            self.rest()


    def update(self):
        self.check_state()
        if not self.dead:
            self.move()
            self.check_bounds()
            self.sprite.update(x=self.x, y=self.y)


    def draw(self):
        self.sprite.draw()