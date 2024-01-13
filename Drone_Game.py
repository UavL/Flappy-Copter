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

# Game constants
FPS = 60
screen_width = 864
screen_height = 936

# Physics constants
gravity = 0.0981
# Propeller force for UP and DOWN
thruster_amplitude = 0.04
# Propeller force for LEFT and RIGHT rotations
diff_amplitude = 0.003
# By default, thruster will apply a force of thruster_mean
thruster_mean = 0.04
mass = 1
# Length from center of mass to propeller
arm = 25

# Initialize Pygame, load sprites
FramePerSec = pygame.time.Clock()
base_path = os.path.dirname(__file__)

pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))

#define font
font = pygame.font.SysFont('Arial', 60)

#define colours
white = (255, 255, 255)

# Loading player and target sprites
player_width = 80
player_animation_speed = 0.3
player = pygame.Rect((400, screen_height / 2, 80, int(player_width * 0.30)))
player = []
for i in range(1, 3):
    image = pygame.image.load(
        os.path.join(base_path,
            "Assets/drone"
            + str(i)
            + ".png"
        )
    )
    image.convert()
    player.append(
        pygame.transform.scale(image, (player_width, int(player_width * 0.30)))
    )

# Loading fonts
pygame.font.init()
info_font = pygame.font.SysFont('Arial', 30)
respawn_font = pygame.font.SysFont('Arial', 90)

# Initialize physics variables
(angle, angular_speed, angular_acceleration) = (0, 0, 0)
(x_position, x_speed, x_acceleration) = (400, 0, 0)
(y_position, y_speed, y_acceleration) = (int(screen_height / 2), 0, 0)
x_theoretical = 0


# Initialize game variables
score = 0
step = 0
dead = False
ground_scroll = 0
scroll_speed = 0
flying = False
pipe_gap = 200
pass_pipe = False
distance_interval = 500
distance_covered = 0
pipe_spawn_count = 0
respawn_timer = 3

#load images
bg = pygame.image.load(os.path.join(base_path,'Assets/bg.png'))
ground_img = pygame.image.load(os.path.join(base_path,'Assets/ground.png'))
button_img = pygame.image.load(os.path.join(base_path,'Assets/restart.png'))


def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))


def reset_game():
	pipe_group.empty()
	x_position = 400
	y_position = int(screen_height / 2)
	score = 0
	return score
	

class Pipe(pygame.sprite.Sprite):
	def __init__(self, x, y, position):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load(os.path.join(base_path,'Assets/pipe.png'))
		self.rect = self.image.get_rect()
		#position 1 is from the top, -1 is from the bottom
		if position == 1:
			self.image = pygame.transform.flip(self.image, False, True)
			self.rect.bottomleft = [x, y - int(pipe_gap / 2)]
		if position == -1:
			self.rect.topleft = [x, y + int(pipe_gap / 2)]

	def update(self, ):
		self.rect.x -= scroll_speed
		if self.rect.right < 0:
			self.kill()


pipe_group = pygame.sprite.Group()

# Game loop
while True:
		pygame.event.get()

		# Display background
		screen.blit(bg, (0,0))

		#playerhitbox_group.draw(screen)
		pipe_group.draw(screen)

		# draw the ground
		screen.blit(ground_img, (ground_scroll, 768))

		step += 1

		# check if drone has hit the ground
		if y_position >= 768:
			dead = True

		if y_position <= 0:
			dead = True


		distance_traveled_since_last_spawn = x_theoretical - (pipe_spawn_count * distance_interval)

		# checking the score
		if distance_traveled_since_last_spawn >= distance_interval and pipe_spawn_count >= 1:
			score += 1

		if dead == False:

			# Initialize accelerations
			x_acceleration = 0
			y_acceleration = gravity
			angular_acceleration = 0

			# Calculate propeller force in function of input
			thruster_left = thruster_mean
			thruster_right = thruster_mean
			pressed_keys = pygame.key.get_pressed()
			if pressed_keys[K_UP]:
				thruster_left += thruster_amplitude
				thruster_right += thruster_amplitude
			if pressed_keys[K_DOWN]:
				thruster_left -= thruster_amplitude
				thruster_right -= thruster_amplitude
			if pressed_keys[K_LEFT]:
				thruster_left -= diff_amplitude
			if pressed_keys[K_RIGHT]:
				thruster_right -= diff_amplitude

			# Calculate accelerations according to Newton's laws of motion
			x_acceleration += (
				-(thruster_left + thruster_right) * sin(angle * pi / 180) / mass
			)
			y_acceleration += (
				-(thruster_left + thruster_right) * cos(angle * pi / 180) / mass
			)
			angular_acceleration += arm * (thruster_right - thruster_left) / mass

			# Calculate speed
			x_speed += x_acceleration
			y_speed += y_acceleration
			angular_speed += angular_acceleration

			# Calculate position
			if x_speed < 0:
				x_position += x_speed

			y_position += y_speed
			angle += angular_speed
			x_theoretical += x_speed

			if x_speed > 0:
				scroll_speed = x_speed
			else:
				scroll_speed = 0


			# generate new pipes
			if distance_traveled_since_last_spawn >= distance_interval:
				pipe_height = random.randint(-100, 100)
				btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
				top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
				pipe_group.add(btm_pipe)
				pipe_group.add(top_pipe)
				pipes_spawned = True
				pipe_spawn_count += 1




			draw_text(str(score), font, white, int(screen_width / 2), 20)

			# draw and scroll the ground
			ground_scroll -= scroll_speed
			if abs(ground_scroll) > 35:
				ground_scroll = 0

			pipe_group.update()


		else:
			# Display respawn timer
			respawn_text = respawn_font.render(
				str(int(respawn_timer) + 1), True, (255, 255, 255)
			)
			respawn_text.set_alpha(124)
			screen.blit(
				respawn_text,
				(
					screen_width / 2 - respawn_text.get_width() / 2,
					screen_height / 2 - respawn_text.get_height() / 2,
				),
			)


			respawn_timer -= 1 / 60
			# Respawn
			if respawn_timer < 0:
				dead = False
				(angle, angular_speed, angular_acceleration) = (0, 0, 0)
				(x_position, x_speed, x_acceleration) = (400, 0, 0)
				(y_position, y_speed, y_acceleration) = (int(screen_height / 2), 0, 0)
				respawn_timer = 3
				score = 0


		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			if event.type == pygame.MOUSEBUTTONDOWN and flying == False and dead == False:
				flying = True


		# Display player
		player_sprite = player[int(step * player_animation_speed) % len(player)]
		player_copy = pygame.transform.rotate(player_sprite, angle)
		screen.blit(
			player_copy,
			(
				x_position - int(player_copy.get_width() / 2),
				y_position - int(player_copy.get_height() / 2),
			),
		)

		pygame.display.update()
		FramePerSec.tick(FPS)

print("Score : " + str(target_counter))