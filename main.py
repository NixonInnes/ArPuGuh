import pyglet

from entities.world import World
from system.window import Window


def main():
    world = World()
    window = Window(world)
    pyglet.clock.schedule_interval(window.update, 1/120.0)
    pyglet.app.run()

main()
