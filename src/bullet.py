import pygame as pg


vec = pg.math.Vector2


class Bullet:

    def __init__(self, x: int, y: int, vel: vec, color: tuple[int, int, int]):

        self.image = pg.Surface((5, 5), pg.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

        pg.draw.circle(self.image, (100, 0, 0), (2.5, 2.5), 2.5)
        self.velocity = vel

    def update(self):
        self.rect.update(self.rect.move(self.velocity))

    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)
