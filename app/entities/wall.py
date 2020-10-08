from pyglet.shapes import Rectangle

import config
from app.entities.base import Entity
from app.system.utils import RGB

class Wall(Entity):
    defaults = {
        'width': config.block_width,
        'height': config.block_height
    }

    attributes = {
        'color': RGB(255,255,255)
    }
    
    def init(self, **kwargs):
        self.shape = Rectangle(self.x, self.y,
                               height=self.height,
                               width=self.width,
                               color=self.color,
                               batch=self.batch)

    def on_collision(self, obj):
        pass

    def update(self):
        pass

    def draw(self):
        self.shape.draw()
