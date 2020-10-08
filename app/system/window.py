from pyglet.window import key, Window as PyWindow

import config
from app.system.utils import Coord


class Window(PyWindow):
    
    def __init__(self, world, player, *args, **kwargs):
        super(Window, self).__init__(*args, 
                                    width=config.window_width, 
                                    height=config.window_height,
                                    #fullscreen=True,
                                    **kwargs)

        self.world = world
        self.player = player
        
    def draw(self):
        self.clear()
        if self.player:
            self.player.chunk.draw_batch.draw()


    def update(self):
        pass

   
    def on_mouse_press(self, x, y, button, modifiers):
        if modifiers & key.MOD_SHIFT:
            self.player.sprinting = True
        else:
            self.player.sprinting = False
        x = x - self.player.width/2
        y = y - self.player.width/2
        self.player.moving_to = Coord(x, y)


    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.player.moving_to:
            if modifiers & key.MOD_SHIFT:
                self.player.sprinting = True
            else:
                self.player.sprinting = False
            x = x - self.player.width/2
            y = y - self.player.width/2
            self.player.moving_to = Coord(x, y)


    def on_mouse_release(self, x, y, button, modifier):
        self.player.sprinting = False
        self.player.moving_to = None

    
    def on_draw(self):
        self.draw()
