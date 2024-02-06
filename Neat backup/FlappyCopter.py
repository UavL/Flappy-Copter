'''

A simple "Flappy Bird like" game,
were you can cotroll a small Quadcopter with arrow keys.
The goal is to rach the highest score.

Made with the help from the "PyGame Flappy Bird Beginner Tutorial in Python" series
by Coding With Russ
https://www.youtube.com/playlist?list=PLjcN1EyupaQkz5Olxzwvo1OzDNaNLGWoJ

'''

import pygame
import os
from pygame.locals import *
from math import sin, cos, pi, sqrt
from random import randrange
import random
import neat

pygame.font.init()

win_width = 800
win_height = 900
FLOOR = 900
fps = 60

STAT_FONT = pygame.font.SysFont("Arial", 40)
END_FONT = pygame.font.SysFont("Arial", 70)
DRAW_LINES = False
player_width = 80

window = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Flappy Drone")

base_path = os.path.dirname(__file__)

stone_img = pygame.transform.scale(pygame.image.load(os.path.join(base_path,"Assets","Felsen.png")).convert_alpha(), (250, 500))
bg_img = pygame.transform.scale(pygame.image.load(os.path.join(base_path,"Assets","Cave.jpg")).convert_alpha(), (win_width, win_height))
drone_images = [pygame.transform.scale(pygame.image.load(os.path.join(base_path,"Assets","drone" + str(x) + ".png")), (player_width, int(0.3 * player_width))) for x in range(1,3)]
base_img = pygame.transform.scale(pygame.image.load(os.path.join(base_path,"Assets","ground.png")).convert_alpha(), (900, 220))
gen = 0

class Drone:
        IMGS = drone_images
        ANIMATION_TIME = 5

        def __init__(self, x_position, y_position):
            self.x_position = x_position
            self.y_position = y_position
            self.tilt = 0  # degrees to tilt
            # self.tick_count = 0
            self.y_speed = 0
            self.height = self.y_position
            self.img_count = 0
            self.img = self.IMGS[0]
            # Initialize physics variables
            self.angle = 0
            self.angular_speed = 0
            self.angular_acceleration = 0
            self.x_speed = 0
            self.x_acceleration = 0
            self.y_acceleration = 0
            # Physics constants
            self.gravity = 0.0981
            self.thruster_amplitude = 0.04
            self.diff_amplitude = 0.003
            self.thruster_mean = 0.04
            self.mass = 0.5
            self.arm = 25
            self.tick_count = 0

        def update(self, action):

            # Initialize accelerations
            self.angular_acceleration = 0
            self.y_acceleration = self.gravity
            thruster_left = self.thruster_mean
            thruster_right = self.thruster_mean

            if action[0] == 1:
                thruster_left += self.thruster_amplitude
                thruster_right += self.thruster_amplitude
            if action[1] == 1:
                thruster_left -= self.thruster_amplitude
                thruster_right -= self.thruster_amplitude

            self.x_acceleration += (-(thruster_left + thruster_right) * sin(self.angle * pi / 180) / self.mass)
            self.y_acceleration += (-(thruster_left + thruster_right) * cos(self.angle * pi / 180) / self.mass)
            self.angular_acceleration += self.arm * (thruster_right - thruster_left) / self.mass
            self.y_speed += self.y_acceleration
            self.height = self.y_position
            self.y_position += self.y_speed

        def draw(self, win):

            self.img_count += 1
            # animate the drone
            if self.img_count <= self.ANIMATION_TIME:
                self.img = self.IMGS[0]
            elif self.img_count <= self.ANIMATION_TIME*2:
                self.img = self.IMGS[1]
                self.img_count = 0

            # draw the drone on screen
            win.blit(self.img, (self.x_position, self.y_position))

        def get_mask(self):
            return pygame.mask.from_surface(self.img)


class Stone():
    gap = 200
    scroll_speed = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0
        self.bottom = 0

        self.stone_top = pygame.transform.flip(stone_img, False, True)
        self.stone_bottom = stone_img

        self.passed = False

        self.set_height()

    def set_height(self):
        self.height = random.randrange(200, 400)
        self.top = self.height - self.stone_top.get_height()
        self.bottom = self.height + self.gap

    def move(self):
        self.x -= self.scroll_speed

    def draw(self, win):
        # draw top
        win.blit(self.stone_top, (self.x, self.top))
        # draw bottom
        win.blit(self.stone_bottom, (self.x, self.bottom))


    def collide(self, drone, win):
        drone_mask = drone.get_mask()
        top_mask = pygame.mask.from_surface(self.stone_top)
        bottom_mask = pygame.mask.from_surface(self.stone_bottom)
        top_offset = (self.x - drone.x_position, self.top - round(drone.y_position))
        bottom_offset = (self.x - drone.x_position, self.bottom - round(drone.y_position))

        b_point = drone_mask.overlap(bottom_mask, bottom_offset)
        t_point = drone_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True

        return False

class Base:

    VEL = 5
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, drones, stones, base, score, gen, stone_ind):

    if gen == 0:
        gen = 1
    win.blit(bg_img, (0,0))

    for stone in stones:
        stone.draw(win)

    base.draw(win)
    for drone in drones:
        # draw lines from drone to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255, 0, 0),
                                 (drone.x+drone.img.get_width()/2, drone.y + drone.img.get_height()/2),
                                 (stones[stone_ind].x + stones[stone_ind].PIPE_TOP.get_width()/2, stones[stone_ind].height), 5)
                pygame.draw.line(win, (255, 0, 0),
                                 (drone.x+drone.img.get_width()/2, drone.y + drone.img.get_height()/2),
                                 (stones[stone_ind].x + stones[stone_ind].PIPE_BOTTOM.get_width()/2, stones[stone_ind].bottom), 5)
            except:
                pass
        drone.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (win_width - score_label.get_width() - 15, 10))

    pygame.display.update()

class FlappyCopter():

    def __init__(self):
        # Game constants
        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((win_width, win_height))

        # Initialize physics variables
        self.score = 0
        self.ground_scroll = 0
        self.distance_interval = 500
        self.stone_spawn_count = 0

        # stone group
        self.stone_group = pygame.sprite.Group()

        # drone group
        self.drone_group = pygame.sprite.Group()

    def reset(self):
        self.stone_group.empty()
        self.drone_group.empty()
        self.score = 0
        self.stone_spawn_count = 0
        self.ground_scroll = 0

    def draw_text(self, text, font, text_col, x, y):
        img = font.render(text, True, text_col)
        self.screen.blit(img, (x, y))

    def get_state(self, player):
        pos_x = player.x_position
        pos_y = player.y_position

        vel_x = player.x_speed
        vel_y = player.y_speed

        phi = player.angle
        omega = player.angular_speed

        if self.stone_group:
            stones = self.stone_group.sprites()
            if len(stones) > 2:
                stone_bot = stones[3]
                stone_top = stones[2]
            else:
                stone_bot = stones[1]
                stone_top = stones[0]
            stone_top_xy = stone_top.rect.topleft
            stone_bot_xy = stone_bot.rect.bottomright
        else:
            stone_top_xy = (850, 500)
            stone_bot_xy = (930, 300)

        state = [
            pos_x,
            pos_y,
            vel_x,
            vel_y,
            phi,
            omega,
            (stone_top_xy[0] - pos_x),
            (stone_top_xy[1] - pos_y),
            (stone_bot_xy[0] - pos_x),
            (stone_bot_xy[1] - pos_y)
        ]

        return state

    def main(self, genomes, config):

        global window, gen
        gen += 1

        nets = []
        players = []
        ge = []
        for genome_id, genome in genomes:
            genome.fitness = 0
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            nets.append(net)
            players.append(Drone(200, int(win_height / 2)))
            ge.append(genome)

        base = Base(FLOOR)
        stones = [Stone(700)]
        score = 0

        clock = pygame.time.Clock()

        run = True
        while run and len(players) > 0:
            clock.tick(fps)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    quit()

            stone_ind = 0
            if len(players) > 0:
                if len(stones) > 1 and players[0].x_position > stones[0].x + stones[0].stone_top.get_width():
                    stone_ind = 1

            for x, player in enumerate(players):
                ge[x].fitness += 0.01

                # send location
                output = nets[players.index(player)].activate((player.y_position, player.y_speed, abs(player.y_position - stones[stone_ind].height), abs(player.y_position - stones[stone_ind].bottom)))
                output = [1 if out > 0.5 else 0 for out in output]
                player.update(output)


            base.move()

            rem = []
            add_stone = False
            for stone in stones:
                stone.move()
                # check for collision
                for player in players:
                    if stone.collide(player, window):
                        ge[players.index(player)].fitness -= 1
                        nets.pop(players.index(player))
                        ge.pop(players.index(player))
                        players.pop(players.index(player))

                if stone.x + stone.stone_top.get_width() < 0:
                    rem.append(stone)

                if not stone.passed and stone.x < player.x_position:
                    stone.passed = True
                    add_stone = True

            if add_stone:
                score += 1
                for genome in ge:
                    genome.fitness += 5
                stones.append(Stone(win_width))

            for r in rem:
                stones.remove(r)

            for player in players:
                if player.y_position + player.img.get_height() - 10 >= FLOOR or player.y_position < -50:
                    nets.pop(players.index(player))
                    ge.pop(players.index(player))
                    players.pop(players.index(player))

            draw_window(window, players, stones, base, score, gen, stone_ind)
        print(score)
