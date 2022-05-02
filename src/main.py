
from ast import arguments
from calendar import formatstring
from distutils import text_file
from select import select
from tkinter import Menu, font
from turtle import Screen, Turtle
import pygame
from pygame.locals import *
import os
import sys
from random import randint, gauss
from copy import copy

from .bullet import Bullet
from .log import Log




class Spritesheet:
    def __init__(self, file):
        self.sheet = pygame.image.load(file).convert_alpha()

    def get_sprite(self, x, y, width, height):
        sprite = pygame.Surface([width, height]),pygame.SRCALPHA
        sprite.blit(self.sheet, (0, 0), (x, y, width, height))
        sprite.set_colorkey(Config.WHITE)
        return sprite

class Config:
    TILE_SIZE = 32
    WINDOW_WIDTH = 160
    WINDOW_HEIGHT = 320
    BLACK = (0, 0, 0)
    RED = (255,62,150)
    GREEN = (0, 255, 0)
    GREY = (128, 128, 128)
    WHITE = (255, 255, 255)
    FPS = 30
    MAX_GRAVITY = 0
    BG_SPEED = 0.3



class BaseSprite(pygame.sprite.Sprite):
    def __init__(self, game, x, y, x_pos=0, y_pos=0, width=Config.TILE_SIZE, height=Config.TILE_SIZE, layer=0, groups=None, spritesheet=None):
        self._layer = layer
        groups = (game.all_sprites, ) if groups == None else (game.all_sprites, groups)
        super().__init__(groups)
        self.game = game
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.width = width
        self.height = height

        if spritesheet == None:
            self.image = pygame.Surface([self.width, self.height])
            self.image.fill(Config.GREY)
        else:
            self.spritesheet = spritesheet
            self.image = self.spritesheet.get_sprite(
                self.x_pos,
                self.y_pos,
                self.width,
                self.height
            )
        self.rect = self.image.get_rect()
        self.rect.x = x * Config.TILE_SIZE
        self.rect.y = y * Config.TILE_SIZE

    def scale(self, factor=2):
        self.rect.width *= factor
        self.rect.height *= factor
        self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))


class PlayerSprite(BaseSprite):
    MAX_HP = 5

    def __init__(self, game, x, y, **kwargs):
        img_data = {
            'spritesheet': Spritesheet("res/player.png"),
        }
        super().__init__(game, x, y, groups=game.players, layer=1, **img_data, **kwargs)
        self.y_velocity = Config.MAX_GRAVITY
        self.speed = 5
        self.standing = False
        self.color = Config.RED
        self.anim_counter = 0
        self.animation_frames = [0, 32]
        self.current_frame = 0
        self.animation_duration = 30
        self.jump_force = 10
        self.movie_counter = 0

        self.rect.bottom = Config.WINDOW_HEIGHT * 4/5
        self.bullets: list[Bullet] = []
        self.logs: list[Log] = []

        self.hp = copy(self.MAX_HP)
        self.score = 0
        self.stage = 1
        
class baum (pygame.sprite.Sprite):
    def _init_(self, game, x, y):
        img_data = {
        'spritesheet': Spritesheet("res/baum.png"),
        }
        super()._init_(game, x, y, groups=game.ground, layer=1)
        self.rect = self.image.get_rect()

    def animate(self, x_diff):
        self.anim_counter += abs(x_diff)
        new_frame = round(self.anim_counter / self.animation_duration) % len(self.animation_frames)
        if self.current_frame != new_frame:
            new_pos = self.animation_frames[new_frame]
            self.image = self.spritesheet.get_sprite(new_pos, self.y_pos, self.width, self.height)
            self.current_frame = new_frame
            self.anim_counter = self.anim_counter % (len(self.animation_frames) * self.animation_duration)

    
    def update(self):
        self.handle_movement()

        if self.rect.x>160 - Config.TILE_SIZE:
            self.rect.x = 160 - Config.TILE_SIZE
        if self.rect.x<0:
            self.rect.x = 0

        self.rect.y = self.rect.y - self.y_velocity
        self.check_collision()
        self.y_velocity = max(self.y_velocity - 0.5, Config.MAX_GRAVITY)
    
    bullet_to_remove = []
    for bullet in self.bullets:
            bullet.update()
            if bullet.rect.bottom < 0:
                bullet_to_remove.append(bullet)
        # we remove the bullet that went out of the screen
    _ = [self.bullets.remove(bullet) for bullet in bullet_to_remove]

        # same for logs
    logs_to_remove = []
    for log in self.logs:
        result = log.update()
        if result == "kill":
            logs_to_remove.append(log)
    _ = [self.logs.remove(log) for log in logs_to_remove]

    def shoot(self):
        self.bullets.append(Bullet(self.rect.centerx, self.rect.centery, pygame.Vector2(0, -5), (255, 0, 0)))

    def jump(self):
        if self.standing:
            self.y_velocity = self.jump_force
            self.standing = False

    def handle_movement(self):
        keys = pygame.key.get_pressed() 
        if keys[pygame.K_LEFT]:
            if self.rect.x > self.speed:
                self.rect.x = self.rect.x - self.speed
        if keys[pygame.K_RIGHT]:
            if self.rect.right < Config.WINDOW_WIDTH - self.speed:
                self.rect.x = self.rect.x + self.speed
        if keys[pygame.K_UP]:
            if self.rect.y > self.speed:
                self.rect.y = self.rect.y - self.speed      
        if keys[pygame.K_DOWN]:
            if self.rect.y > self.rect.y + self.speed:
                self.rect.bottom = self.rect.y - self.speed



    def update_camera(self):
        x_c, y_c = self.game.screen.get_rect().center
        x_diff = x_c - self.rect.centerx
        y_diff = y_c - self.rect.centery
        
        self.animate(x_diff)

    def is_standing(self, hit):
        if self.y_velocity > 0:
            return False
        if abs(hit.rect.top - self.rect.bottom) > abs(Config.MAX_GRAVITY):
            return False
        if abs(self.rect.left - hit.rect.right) <= abs(self.speed):
            return False
        if abs(hit.rect.left - self.rect.right) <= abs(self.speed):
            return False
        return True

    def hit_head(self, hit):
        if self.y_velocity < 0:
            return False
        if abs(self.rect.top - hit.rect.bottom) > abs(self.jump_force):
            return False
        if abs(self.rect.left - hit.rect.right) <= abs(self.speed):
            return False
        if abs(hit.rect.left - self.rect.right) <= abs(self.speed):
            return False
        return True


    def check_collision(self):
        hits = pygame.sprite.spritecollide(self, self.game.ground, False)
        for hit in hits:
            if self.is_standing(hit):
                self.rect.bottom = hit.rect.top
                break
            if self.hit_head(hit):
                self.y_velocity = 0
                self.rect.top = hit.rect.bottom
                break

        hits = pygame.sprite.spritecollide(self, self.game.ground, False)
        for hit in hits:
            hit_dir = hit.rect.x - self.rect.x
            if hit_dir < 0:
                self.rect.left = hit.rect.right
            else:
                self.rect.right = hit.rect.left

        self.rect.y += 1
        hits = pygame.sprite.spritecollide(self, self.game.ground, False)
        self.standing = True if hits else False
        self.rect.y -= 1


class GroundSprite(BaseSprite):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, groups=game.ground, layer=0)
        self.image.fill(Config.GREEN)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font(None, 30)
        self.font2 = pygame.font.Font(None,20)
        self.ui_font = pygame.font.Font(None, 20)
        self.screen = pygame.display.set_mode( (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT) ) 
        self.clock = pygame.time.Clock()
        self.bg = pygame.image.load("res/bg-small.png").convert()
        self.bg_ground = pygame.image.load("res/Ground.png").convert()
        self.bg_x = 0

        self.delay_between_logs = 1000
        self.last_log_time = 0
        self.started = 0
        self.stage = 1
    
    def load_map(self, mapfile):
        with open(mapfile, "r") as f:
            for (y, lines) in enumerate(f.readlines()):
                for (x, c) in enumerate(lines):
                    if c == "b":
                        GroundSprite(self, x, y)
                    if c == "p":
                        self.player = PlayerSprite(self, x, y)

    def spawn_logs(self):
        if pygame.time.get_ticks() - self.last_log_time > self.delay_between_logs:
            for _ in range(1+self.stage // 2):
                self.player.logs.append(Log(randint(0, Config.WINDOW_WIDTH), randint(-40, 0), pygame.Vector2(0, abs(gauss(4, 2+self.stage/10))+1), self.player, Config))
            self.last_log_time = pygame.time.get_ticks()

    def game_over(self):
        bg = self.screen.copy()
        layer = pygame.Surface((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        layer.fill((0, 0, 0))
        layer.set_alpha(128)

        game_over_text = self.font.render("Game Over !", True, (255, 255, 255))
        press_text = self.font2.render("Press any key to restart!", True, (255, 255, 255))
        score_text = self.font.render(f"Your score: {self.player.score}", True, (255, 255, 255))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    self.new()
                    return

            self.screen.blit(bg, (0, 0))
            self.screen.blit(layer, (0, 0))

            self.screen.blit(game_over_text, game_over_text.get_rect(center=(Config.WINDOW_WIDTH//2,
                                                                             Config.WINDOW_HEIGHT/3)))
            self.screen.blit(score_text, game_over_text.get_rect(center=(Config.WINDOW_WIDTH//2,
                                                                         Config.WINDOW_HEIGHT//2)))

            if (pygame.time.get_ticks() // 500) % 2 == 1:
                self.screen.blit(press_text, press_text.get_rect(center=(Config.WINDOW_WIDTH//2,
                                                                         Config.WINDOW_HEIGHT*2/3)))

            self.clock.tick(Config.FPS)
            pygame.display.flip()

    def new(self):
        self.playing = True

        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.ground = pygame.sprite.LayeredUpdates()
        self.players = pygame.sprite.LayeredUpdates()

        self.load_map("maps/level-01.txt")
        self.started = pygame.time.get_ticks()

        self.player.hp = copy(self.player.MAX_HP)
        self.player.logs = []
        self.player.bullet = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.player.shoot()

    def update(self):
        # each stage increase the number of logs spawned, and their velocity (each stage
        self.stage = (pygame.time.get_ticks() - self.started) // 4000 + 1
        if self.stage > 10:
            self.stage = 10
        self.player.stage = self.stage
        self.all_sprites.update()
        self.spawn_logs()

    def draw(self):
        self.screen.blit(self.bg, (self.bg_x, 0))
        tmp_bg = pygame.transform.flip(self.bg, True, False)
        second_x = Config.WINDOW_WIDTH + self.bg_x
        if self.bg_x > 0:
            second_x -= 2*Config.WINDOW_WIDTH
        self.screen.blit(tmp_bg, (second_x, 0))
        self.all_sprites.draw(self.screen)
        for bullet in self.player.bullets:
            bullet.draw(self.screen)
        for log in self.player.logs:
            log.draw(self.screen)
        self.screen.blit(self.bg_ground, (0, Config.WINDOW_HEIGHT*4/5))

        render_hp = self.ui_font.render("HP: "+str(self.player.hp)+" / "+str(self.player.MAX_HP), True, (255, 255, 255))
        render_stage = self.ui_font.render("Stage: "+str(self.stage), True, (255, 255, 255))
        render_score = self.ui_font.render("Score: "+str(self.player.score), True, (255, 255, 255))
        dy = Config.WINDOW_HEIGHT * 4 / 5 + 15
        pygame.draw.rect(self.screen, (255, 0, 0), [10, dy-2, Config.WINDOW_WIDTH-20, render_hp.get_height()+4],
                         width=2, border_radius=10)
        pygame.draw.rect(self.screen, (255, 0, 0), [10, dy - 2, self.player.hp*(Config.WINDOW_WIDTH - 20)/5,
                                                    render_hp.get_height() + 4], border_radius=10)
        self.screen.blit(render_hp, render_hp.get_rect(centerx=(Config.WINDOW_WIDTH//2), y=dy))
        dy += render_hp.get_height() + 4
        self.screen.blit(render_stage, render_stage.get_rect(centerx=Config.WINDOW_WIDTH//2, y=dy))
        dy += render_stage.get_height() + 4
        self.screen.blit(render_score, render_score.get_rect(centerx=Config.WINDOW_WIDTH//2, y=dy))
        
        if self.player.hp == 0:
            self.game_over()

        pygame.display.update()

    def game_loop(self):
        while self.playing:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)

    def welcome(self):
        
        display_text = self.font.render('KOKOSHKA', False, (255, 255, 255))
        press_text = self.font2.render('Press any key to start', False, (255, 255, 255))

        while True:
            for event in pygame.event.get():
                print(event)
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

                if event.type == pygame.KEYDOWN:
                    return

            self.screen.blit(self.bg, (0, 0))

            self.screen.blit(display_text, display_text.get_rect(center=(Config.WINDOW_WIDTH//2,
                                                                         Config.WINDOW_HEIGHT//2 - 50)))
            if (pygame.time.get_ticks() // 500) % 2 == 1:
                self.screen.blit(press_text, press_text.get_rect(center=(Config.WINDOW_WIDTH//2,
                                                                         Config.WINDOW_HEIGHT//2 + 50)))

            pygame.display.flip()
            self.clock.tick(Config.FPS)
        
def main():
    g = Game()

    g.welcome()

    g.new()
    
    g.game_loop()


    pygame.quit()
    sys.exit()
