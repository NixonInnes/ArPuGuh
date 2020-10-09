import numpy as np
import math
import pyglet
from pyglet.window import key
from pyglet.graphics import GL_POINTS

import config
from app import world
from app.entities.base import Entity, Stats
from app.entities.projectile import Projectile
from app.system.dice import d6, d20
from app.system.utils import calc_1D_intersect, Coord, distance

SPRINT_MOD = 1.5

class Player(Entity):
    defaults = {
        'collidable': True,
        'mobile': True,
        'width': 50,
        'height': 50,
    }

    attributes = {
        'cursor_coord': Coord(0,0),
        'dead': False,
        'sprinting': False,
        'image_file': 'app/assets/player.png',
        'moving_to': None,
        'chunk': None,
        'in_combat': False,
        'in_combat_with': [],
        'attack_cooldown': 0,
        'projectile_cooldown': 0
    }

    def init(self, **kwargs):
        self.image = pyglet.image.load(self.image_file)
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y)
        self.key_handler = key.KeyStateHandler()
        self.stats = Stats()


    @property
    def speed(self):
        walk_speed = self.stats.dex//2
        if self.sprinting:
            return walk_speed * SPRINT_MOD
        return walk_speed
    

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
        self.moving_to = None


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


    def attack(self):
        if not self.attack_cooldown:
            atk_range = 75
            for mob in self.chunk.mobs:
                if distance(*self.coord, *mob.coord) < atk_range:
                    self.in_combat = True
                    self.in_combat_with.append(mob)
                    self.do_damage(mob, d6(num=self.stats.str//2))
            self.attack_cooldown = 50


    def fire_proj(self):
        velocity = 10
        p_x = self.cursor_coord.x - self.center.x
        p_y = self.cursor_coord.y - self.center.y
        d = distance(self.center.x, self.center.y, 
                     self.cursor_coord.x, self.cursor_coord.y)
        r = velocity/d
        r_p = 30/d
        if not self.projectile_cooldown:
            proj = Projectile(owner=self,
                              chunk=self.chunk,
                              x=self.center.x+p_x*r_p,
                              y=self.center.y+p_y*r_p,
                              damage=d20(num=self.stats.int//3),
                              velocity_x=p_x*r,
                              velocity_y=p_y*r,
                              batch=self.chunk.draw_batch,
                              group=self.chunk.foreground)
            self.chunk.objects.append(proj)
            self.projectile_cooldown = 10


    def update_cooldowns(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1


    def do_damage(self, target, dmg):
        target.take_damage(self, dmg)


    def take_damage(self, source, dmg):
        self.in_combat = True
        self.in_combat_with.append(source)
        self.stats.hp -= dmg
        if self.stats.hp < 1:
            self.dead = True
        print(f'{self.name} took {dmg} damage from {source.name}!')


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


    def update(self):
        self.update_cooldowns()
        self.parse_keys()
        self.move()
        self.check_bounds()
        self.sprite.update(x=self.x, y=self.y)


    def draw(self):
        self.sprite.draw()
