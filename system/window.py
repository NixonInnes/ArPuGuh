import os
from math import sqrt
from pyglet import image
from pyglet.sprite import Sprite
from pyglet.window import key, Window as PyWindow
from pyglet.shapes import Rectangle
from pyglet.graphics import Batch, OrderedGroup
from random import randint

import config
from system.utils import Coord
from entities.player import Player
from entities.mob import Mob
from entities.wall import Wall


class Window(PyWindow):
    def __init__(self, world, *args, **kwargs):
        self.world = world
        self.alive = True
        super(Window, self).__init__(*args, 
                                    width=config.window_width, 
                                    height=config.window_height,
                                    fullscreen=True,
                                    **kwargs)
        self.game_objects = []
        self.window_grid = []
        self.draw_batch = Batch()
        self.background = OrderedGroup(0)
        self.foreground = OrderedGroup(1)
        self.player = None
        self.init_player()
        #self.add_walls(30)
        #self.add_mobs(5)
        self.load_tile(world.get_origin())

    def load_tile(self, tile):
        self.game_objects.clear()
        self.tile = tile
        self.add_mobs(randint(3, 7))
        self.game_objects.append(self.player)
        if not os.path.isfile(self.tile.img_file):
            self.tile.build_img()
        bg_img = image.load(self.tile.img_file)
        self.tile_sprite = Sprite(bg_img, 0, 0, 
                                  batch=self.draw_batch, 
                                  group=self.background)
        for block in self.tile.blocks:
            if block.collidable:
                wall = Wall(x=block.x,
                            y=block.y,
                            width=block.width,
                            height=block.height,
                            color=block.color,
                            # Note: don't really need to draw these
                            #color=(255,0,0),
                            #batch=self.draw_batch
                            )
                self.game_objects.append(wall)

    def init_player(self, name='player'):
        player = Player(x=config.window_width//2,
                        y=config.window_height//2,
                        width=50,
                        height=50,
                        name=name,
                        batch=self.draw_batch,
                        group=self.foreground)
        self.player = player
        self.push_handlers(self.player.key_handler)
        self.game_objects.append(player)


    def add_mobs(self, n):
        for i in range(n):
            mob = Mob(x=randint(0, config.window_width),
                      y=randint(0, config.window_height),
                      width=50,
                      height=50,
                      batch=self.draw_batch,
                      group=self.foreground)
            self.game_objects.append(mob)


    def draw(self):
        self.clear()
        self.draw_batch.draw()


    def update(self, time):
        #self.tile_sprite.update()
        for obj in self.game_objects:
            obj.update()
            for other_obj in self.game_objects:
                if other_obj is obj:
                    continue
                if obj.mobile and obj.collides_with(other_obj):
                    # TODO: Sum collision movements & resolve in one
                    if other_obj.collidable:
                        #print(f'{obj.name} ** {other_obj.name}')
                        obj.on_collision(other_obj)
        self.check_player_bounds()
        #print(self.player.x, self.player.y)


    def check_player_bounds(self):
        if (self.player.x + self.player.width) > config.window_width:
            self.load_tile(self.tile.e)
            self.player.x = 0
        
        elif self.player.x < 0:
            self.load_tile(self.tile.w)
            self.player.x = config.window_width - self.player.width

        elif (self.player.y + self.player.height) > config.window_height:
            self.load_tile(self.tile.n)
            self.player.y = 0

        elif self.player.y < 0:
            self.load_tile(self.tile.s)
            self.player.y = config.window_height - self.player.height

    def on_mouse_press(self, x, y, button, modifiers):
        if modifiers & key.MOD_SHIFT:
            self.player.sprint = True
        else:
            self.player.sprint = False
        x = x - self.player.width/2
        y = y - self.player.width/2
        self.player.move_target = Coord(x, y)


    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.player.move_target:
            if modifiers & key.MOD_SHIFT:
                self.player.sprint = True
            else:
                self.player.sprint = False
            x = x - self.player.width/2
            y = y - self.player.width/2
            self.player.move_target = Coord(x, y)


    def on_mouse_release(self, x, y, button, modifier):
        self.player.move_target = None

    def on_draw(self):
        self.draw()
