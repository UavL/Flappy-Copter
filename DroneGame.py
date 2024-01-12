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

pygame.init()

# Game constants
clock = pygame.time.Clock()
fps = 60

screen_width = 864
screen_height = 936

screen = pygame.display.set_mode((screen_width, screen_height))

#define font
font = pygame.font.SysFont('Arial', 60)

# Initialize physics variables
score = 0
game_over = False
ground_scroll = 0
scroll_speed = 0
pipe_gap = 200
distance_interval = 500
distance_covered = 0
pipe_spawn_count = 0
player_width = 80
respawn_timer = 3

#load images
bg = pygame.image.load('Assets/bg.png')
ground_img = pygame.image.load('Assets/ground.png')

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

class Drone(pygame.sprite.Sprite):
	def __init__(self, x_position, y_position):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		self.index = 0
		self.counter = 0
		for num in range(1, 3):
			img = pygame.image.load(f'Assets/drone{num}.png')
			img = pygame.transform.scale(img, (player_width, int(player_width * 0.3)))
			self.images.append(img)
		self.image = self.images[self.index]
		self.rect = self.image.get_rect()

		# Initialize physics variables
		self.angle = 0
		self.angular_speed = 0
		self.angular_acceleration = 0
		self.x_position = 400
		self.x_speed = 0
		self.x_acceleration = 0
		self.y_position = int(screen_height / 2)
		self.y_speed = 0
		self.y_acceleration = 0

		self.rect.center = [x_position, y_position]
		self.clicked = False

		# Physics constants
		self.gravity = 0.0981
		self.thruster_amplitude = 0.04
		self.diff_amplitude = 0.003
		self.thruster_mean = 0.04
		self.mass = 1
		self.arm = 25

	def update(self):

		if game_over == False:
			#handle the animation
			self.counter += 1
			rotor_cooldown = 4

			if self.counter > rotor_cooldown:
				self.counter = 0
				self.index += 1
				if self.index >= len(self.images):
					self.index = 0
			self.image = self.images[self.index]

			# Initialize accelerations
			self.angular_acceleration = 0
			self.x_acceleration = 0
			self.y_acceleration = self.gravity
			thruster_left = self.thruster_mean
			thruster_right = self.thruster_mean

			pressed_keys = pygame.key.get_pressed()
			if pressed_keys[K_UP]:
				thruster_left += self.thruster_amplitude
				thruster_right += self.thruster_amplitude
			if pressed_keys[K_DOWN]:
				thruster_left -= self.thruster_amplitude
				thruster_right -= self.thruster_amplitude
			if pressed_keys[K_LEFT]:
				thruster_left -= self.diff_amplitude
			if pressed_keys[K_RIGHT]:
				thruster_right -= self.diff_amplitude

			# Calculating accelerations with Newton's laws of motions
			self.x_acceleration += (
					-(thruster_left + thruster_right) * sin(self.angle * pi / 180) / self.mass
			)
			self.y_acceleration += (
					-(thruster_left + thruster_right) * cos(self.angle * pi / 180) / self.mass
			)
			self.angular_acceleration += self.arm * (thruster_right - thruster_left) / self.mass

			self.x_speed += self.x_acceleration
			self.y_speed += self.y_acceleration
			self.angular_speed += self.angular_acceleration

			self.x_position += self.x_speed
			self.y_position += self.y_speed
			self.angle += self.angular_speed

			if self.x_speed < 0:
				self.rect.x += self.x_speed

			self.rect.y += self.y_speed
			self.image = pygame.transform.rotate(self.images[self.index], self.angle)


class Pipe(pygame.sprite.Sprite):
	def __init__(self, x, y, position):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load('Assets/pipe.png')
		self.rect = self.image.get_rect()
		#position 1 is from the top, -1 is from the bottom
		if position == 1:
			self.image = pygame.transform.flip(self.image, False, True)
			self.rect.bottomleft = [x, y - int(pipe_gap / 2)]
		if position == -1:
			self.rect.topleft = [x, y + int(pipe_gap / 2)]

	def update(self):
		self.rect.x -= scroll_speed
		if self.rect.right < 0:
			self.kill()


# pipe group
pipe_group = pygame.sprite.Group()

# drone group
drone_group = pygame.sprite.Group()
player = Drone(400, int(screen_height / 2))
drone_group.add(player)

# Game loop
run = True
while run:

		clock.tick(fps)

		# Display background
		screen.blit(bg, (0,0))

		drone_group.update()
		drone_group.draw(screen)
		pipe_group.draw(screen)

		# draw the ground
		screen.blit(ground_img, (ground_scroll, 768))

		# collision
		if pygame.sprite.groupcollide(drone_group, pipe_group, False, False):
				game_over = True

		# check if drone has hit the bottom or top
		if player.rect.bottom >= 768 or player.rect.top <= 0 or player.rect.left <=0:
				game_over = True


		if game_over == False:

				if player.x_speed > 0:
					scroll_speed = player.x_speed
					distance_covered += player.x_speed
				else:
					scroll_speed = 0

				# checking the score
				distance_traveled_since_last_spawn = distance_covered - (pipe_spawn_count * distance_interval)
				if distance_traveled_since_last_spawn >= distance_interval and pipe_spawn_count >= 1:
					score += 1

				# generate new pipes
				if distance_traveled_since_last_spawn >= distance_interval:
					pipe_height = random.randint(-100, 100)
					btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
					top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
					pipe_group.add(btm_pipe)
					pipe_group.add(top_pipe)
					pipes_spawned = True
					pipe_spawn_count += 1

				draw_text(str(score), font, (255, 255, 255), int(screen_width / 2), 20)

				# draw and scroll the ground
				ground_scroll -= scroll_speed
				if abs(ground_scroll) > 35:
					ground_scroll = 0

				pipe_group.update()

		if game_over == True:

				# Display respawn timer
				respawn_text = font.render(
					str(int(respawn_timer) + 1), True, (0, 0, 0))
				respawn_text.set_alpha(124)
				screen.blit(
					respawn_text,
					(screen_width / 2 - respawn_text.get_width() / 2,
						screen_height / 2 - respawn_text.get_height() / 2,),)

				respawn_timer -= 1 / 60
				# Respawn
				if respawn_timer <= 0:
					pipe_group.empty()
					drone_group.empty()
					player = Drone(400, int(screen_height / 2))
					drone_group.add(player)
					score = 0
					game_over = False
					respawn_timer = 3


		for event in pygame.event.get():
				if event.type == pygame.QUIT:
					run = False


		pygame.display.update()

print("Score : " + str(score))
pygame.quit()