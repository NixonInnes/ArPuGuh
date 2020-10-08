import pyglet

from app import world


def main():
    window = world.get_window()
    pyglet.clock.schedule_interval(world.update, 1/120.0)
    pyglet.app.run()

main()
