from pyglet import app, image, clock
from pyglet.window import Window, key

window = Window(500, 500)
sq_size = 20
sq_x, sq_y = 0, 0


@window.event
def on_draw():
    window.clear()
    draw_square(sq_x, sq_y, sq_size)


def draw_square(x, y, size, colour=(255, 255, 255, 0)):
    img = image.create(size, size, image.SolidColorImagePattern(colour))
    img.blit(x, y)


@window.event
def on_key_press(symbol, modifiers):
    global sq_x, sq_y

    if symbol == key.LEFT:
        sq_x -= sq_size

    elif symbol == key.RIGHT:
        sq_x += sq_size

    elif symbol == key.UP:
        sq_y += sq_size

    elif symbol == key.DOWN:
        sq_y -= sq_size

app.run()
