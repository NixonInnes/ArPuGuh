from pyglet.shapes import Rectangle

from system.component import PhysicalComponent

class Wall(PhysicalComponent):
    def __init__(self, *args, **kwargs):
        super(Wall, self).__init__(*args, **kwargs)
        self.width = kwargs.get('width', 10)
        self.height = kwargs.get('height', 10)
        self.color = kwargs.get('color', (255,255,255))
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
