from random import randint


class Dice:
    def __init__(self, sides):
        self.sides = sides

    def __call__(self, num=1, get_rolls=False):
        rolls = [randint(1, self.sides) for _ in range(num)]
        if get_rolls:
            return rolls
        return sum(rolls)


d6 = Dice(6)
d20 = Dice(20)
