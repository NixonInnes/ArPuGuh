import pyglet

import config
from app.entities.base import Entity
from app.system.utils import RGB, Coord

class Projectile(Entity):
    defaults = {
        'width': 5,
        'height': 5,
        'mobile': True,
    }

    attributes = {
        'owner': None,
        'chunk': None,
        'image_file': 'app/assets/projectiles/ball.png',
        'speed': 3,
        'velocity_x': 0.0,
        'velocity_y': 0.0,
        'damage': 1
    }
    
    def init(self, **kwargs):
        self.image = pyglet.image.load('app/assets/projectiles/ball.png')
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y, 
                                           batch=kwargs.get('batch', None),
                                           group=kwargs.get('group', None))


    def check_bounds(self):
        if (self.x + self.width) > config.window_width:
            self.dead = True
        elif self.x < 0:
            self.dead = True
        elif (self.y + self.height) > config.window_height:
            self.dead = True
        elif self.y < 0:
            self.dead = True


    def on_collision(self, obj):
        if obj is not self.owner:
            self.do_damage(obj)
            self.dead = True

        
    def do_damage(self, target):
        target.take_damage(self.owner, self.damage)


    def check_status(self):
        if self.dead:
            self.chunk.objects.remove(self)
            self.sprite.delete()


    def update(self):
        self.check_status()
        if self.sprite and not self.dead:
            self.x += self.velocity_x
            self.y += self.velocity_y
            self.check_bounds()
            self.sprite.update(x=self.x, y=self.y)


    def draw(self):
        self.shape.draw()