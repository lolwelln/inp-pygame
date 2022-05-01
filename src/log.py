import pygame as pg


class Log:

    def __init__(self, x_dep, dy, vel: pg.Vector2, player_instance, config):
        self.image = pg.image.load("res/baum.png").convert_alpha()
        self.image = pg.transform.smoothscale(self.image, (self.image.get_width()//2, self.image.get_width()//2))

        self.rect = self.image.get_rect(x=x_dep, bottom=-dy)

        if self.rect.x + (w := self.image.get_width()) > config.WINDOW_WIDTH:
            self.rect.x = config.WINDOW_WIDTH - w

        self.vel = vel
        self.player = player_instance
        self.config = config

    def update(self):
        self.rect.update(self.rect.move(self.vel))
        if self.rect.colliderect(self.player.rect):
            self.player.deal_damage()
            return "kill"

        if True in [self.rect.colliderect(bullet.rect) for bullet in self.player.bullets] or \
                self.rect.y > self.config.WINDOW_HEIGHT * 4 / 5:
            self.player.score += 10 * self.player.stage
            return "kill"

    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)
