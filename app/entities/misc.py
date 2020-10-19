from pyglet import clock
from pyglet.image import load as load_image
from pyglet.sprite import Sprite

from app.entities.base import Entity


class TemporaryEntity(Entity):
    defaults = {
        'width': 48,
        'height': 48,
    }

    attributes = {
        'image_file': 'app/assets/corpse.png',
        'chunk': None,
        'timer': 60
    }

    def init(self, **kwargs):
        self.image = load_image(self.image_file)
        self.sprite = Sprite(self.image, self.x, self.y,
                             batch=self.batch, group=self.group)
        self.chunk.objects.append(self)

        clock.schedule_once(self.delete, self.timer)

    def delete(self, dt):
        if self in self.chunk.objects:
            self.chunk.objects.remove(self)
        self.sprite.delete()

    def update(self):
        pass

    def draw(self):
        self.sprite.draw()


