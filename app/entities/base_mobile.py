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
from app.entities.base import Entity, Stats
from app.entities.projectile import Projectile
from app.system.dice import d6, d20
from app.system.utils import calc_1D_intersect, Coord, distance, RGB

SPRINT_MOD = 1.5

class MobileEntity(Entity):
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
        'dead': False,
        'image_file': 'app/assets/zombie.png',
        'moving_to': None,
        'chunk': None,
        'sprinting': False,
        'in_combat': False,
        #'in_combat_with': [],
        'attack_cooldown': 0,
        'projectile_cooldown': 0,
        'damage_text_color': (255,255,255,255),
        'chunk_container': 'npcs'
    }

    overwrite = {
    }

    def __init__(self, **kwargs):
        self.pre_init(**kwargs)
        super(MobileEntity, self).__init__(**kwargs)


    def init(self, **kwargs):
        self.in_combat_with = []
        self.image =load_image(self.image_file)
        self.sprite = Sprite(self.image, self.x, self.y)
        self.hp_image = load_image('app/assets/healthbar.png')
        self.hp_sprite = Sprite(self.hp_image,
                                self.x + 1,
                                self.y + self.height + 5)
        self.set_sprite_render(self.group)
        self.stats = Stats(modifiers=self.stat_modifiers)

        entity_container = getattr(self.chunk, self.chunk_container)
        if self.chunk and self not in entity_container:
            entity_container.append(self)

        self.post_init(**kwargs)


    def pre_init(self, **kwargs):
        self.attributes = {**self.attributes, **self.overwrite}


    def post_init(self, **kwargs):
        pass


    def set_sprite_render(self, group):
        self.sprite.batch = self.chunk.draw_batch
        self.sprite.group = group
        self.hp_sprite.batch = self.chunk.draw_batch
        self.hp_sprite.group = group


    @property
    def speed(self):
        walk_speed = self.stats.dex//3
        if self.sprinting:
            return walk_speed * config.sprint_modifier
        return walk_speed


    def check_state(self):
        if self.dead:
            self.on_death()
        elif self.in_combat:
            if not self.in_combat_with:
                self.in_combat = False
            else:
                self.do_combat()
        else:
            self.do_idle()


    def on_death(self):
        print(f'{self.name} died!')
        if self.in_combat:
            for entity in self.in_combat_with:
                if self in entity.in_combat_with:
                    entity.in_combat_with.remove(self)
        self.remove_from_chunk()
        self.sprite.delete()
        self.hp_sprite.delete()
        self.after_death()


    def remove_from_chunk(self):
        if self.chunk:
            container = getattr(self.chunk, self.chunk_container)
            if self in container:
                container.remove(self)
 

    def after_death(self):
        pass


    def do_combat(self):
        pass


    def do_idle(self):
        pass


    def check_bounds(self):
        if (self.x + self.width) > config.window_width:
            self.out_of_bounds('e')
        elif self.x < 0:
            self.out_of_bounds('w')
        elif (self.y + self.height) > config.window_height:
            self.out_of_bounds('n')
        elif self.y < 0:
            self.out_of_bounds('s')


    def out_of_bounds(self, direction):
        pass


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
        self.after_collision(obj)


    def after_collision(self, obj):
        pass


    def attack(self):
        if not self.attack_cooldown:
            atk_range = 75
            for entity in self.chunk.attackable_objects:
                if entity is not self:
                    if distance(*self.coord, *entity.coord) < atk_range:
                        self.in_combat = True
                        if entity not in self.in_combat_with:
                            self.in_combat_with.append(entity)
                        self.do_damage(entity, d6(num=self.stats.str//2))
                        self.attack_cooldown = 50


    def do_damage(self, target, dmg):
        target.take_damage(self, dmg)


    def take_damage(self, source, dmg):
        dmg_text = Label(f'{dmg}',
                         x=randint((self.x-5)//1, (self.x+self.width+5)//1),
                         y=self.y+self.height+15,
                         font_name='courier new',
                         color=self.damage_text_color,
                         bold=True,
                         batch=self.chunk.draw_batch,
                         group=self.chunk.foreground)
        clock.schedule_once(lambda df: dmg_text.delete(), 0.5)
        
        if (source is not None) and (source is not self):
            self.in_combat = True
            if source not in self.in_combat_with:
                self.in_combat_with.append(source)
        
        self.stats.hp -= dmg
        if self.stats.hp < 1:
            self.dead = True
        
        print(f'{self.name} ({self.stats.hp}/{self.stats.base_hp}) took {dmg} damage from {source.name}!')
        

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


    def update_sprites(self):
        self.sprite.update(x=self.x, y=self.y)
        self.hp_sprite.update(x=self.x + 1,
                              y=self.y + self.height + 5,
                              scale_x=self.stats.hp/self.stats.base_hp)


    def update(self):
        self.check_state()
        if not self.dead:
            self.update_cooldowns()
            self.move()
            self.check_bounds()
            self.update_sprites()
        else:
            self.after_death()


    def draw(self):
        self.sprite.draw()
