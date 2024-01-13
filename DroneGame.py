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

screen_width = 864
screen_height = 936
scroll_speed = 0


#define font
font = pygame.font.SysFont('Arial', 60)

fps = 60

base_path = os.path.dirname(__file__)


#load images
bg = pygame.image.load(os.path.join(base_path,"Assets/bg.png"))
ground_img = pygame.image.load(os.path.join(base_path,"Assets/ground.png"))


class Drone(pygame.sprite.Sprite):
	def __init__(self, x_position, y_position):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		self.index = 0
		self.player_width = 80
		self.counter = 0
		for num in range(1, 3):
			img = pygame.image.load(os.path.join(base_path,f'Assets/drone{num}.png'))
			img = pygame.transform.scale(img, (self.player_width, int(self.player_width * 0.3)))
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

		self.rect.center = [self.x_position, self.y_position]
		self.clicked = False

		# Physics constants
		self.gravity = 0.0981
		self.thruster_amplitude = 0.04
		self.diff_amplitude = 0.003
		self.thruster_mean = 0.04
		self.mass = 1
		self.arm = 25

	def update(self,action,state):

		if state == False:
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

			if action[0] == 1:
				thruster_left += self.thruster_amplitude
				thruster_right += self.thruster_amplitude
			if action[1] == 1:
				thruster_left -= self.thruster_amplitude
				thruster_right -= self.thruster_amplitude
			if action[2] == 1:
				thruster_left -= self.diff_amplitude
			if action[3] == 1:
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
		self.pipe_gap = 200
		self.image = pygame.image.load(os.path.join(base_path,"Assets/pipe.png"))
		self.rect = self.image.get_rect()
		#position 1 is from the top, -1 is from the bottom
		if position == 1:
			self.image = pygame.transform.flip(self.image, False, True)
			self.rect.bottomleft = [x, y - int(self.pipe_gap / 2)]
		if position == -1:
			self.rect.topleft = [x, y + int(self.pipe_gap / 2)]

	def update(self,action,state):
		self.rect.x -= scroll_speed
		if self.rect.right < 0:
			self.kill()

class FlappyCopter():

	def __init__(self):
		# Game constants
		self.clock = pygame.time.Clock()

		self.screen = pygame.display.set_mode((screen_width, screen_height))

		# Initialize physics variables
		self.score = 0
		self.game_over = False
		self.ground_scroll = 0
		self.distance_interval = 500
		self.distance_covered = 0
		self.pipe_spawn_count = 0
		self.respawn_timer = 3
		self.reward = 0
		self.distance_traveled_since_last_spawn = 0
		self.frame_iteration = 0

		# pipe group
		self.pipe_group = pygame.sprite.Group()

		# drone group
		self.drone_group = pygame.sprite.Group()
		self.player = Drone(400, int(screen_height / 2))
		self.drone_group.add(self.player)

	def respawn_timer(self):
		# Display respawn timer
		respawn_text = font.render(
			str(int(self.respawn_timer) + 1), True, (0, 0, 0))
		respawn_text.set_alpha(124)
		self.screen.blit(
			respawn_text,
			(screen_width / 2 - respawn_text.get_width() / 2,
				screen_height / 2 - respawn_text.get_height() / 2,),)

		self.respawn_timer -= 1 / 60

	def reset(self):
		self.pipe_group.empty()
		self.drone_group.empty()
		self.player = Drone(400, int(screen_height / 2))
		self.drone_group.add(self.player)
		self.score = 0
		self.game_over = False
		self.respawn_timer = 3
		self.frame_iteration = 0
		self.reward = 0
		self.distance_traveled_since_last_spawn = 0
		self.distance_covered = 0
		self.pipe_spawn_count = 0
		self.ground_scroll = 0
			

	def draw_text(self, text, font, text_col, x, y):
		img = font.render(text, True, text_col)
		self.screen.blit(img, (x, y))

	def play_step(self,action):
		self.frame_iteration += 1
		self.reward += 0.05

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
		
		# Game loop
		game_over = False

		self.clock.tick(fps)

		# Display background
		self.screen.blit(bg, (0,0))

		self.drone_group.update(action,game_over)
		self.drone_group.draw(self.screen)
		self.pipe_group.draw(self.screen)

		# draw the ground
		self.screen.blit(ground_img, (self.ground_scroll, 768))

		# collision
		if pygame.sprite.groupcollide(self.drone_group, self.pipe_group, False, False):
				self.reward = -30
				game_over = True
				return self.reward, game_over, self.score

		# check if drone has hit the bottom or top
		if self.player.rect.bottom >= 768 or self.player.rect.top <= 0 or self.player.rect.left <=0:
				self.reward = -30
				game_over = True
				return self.reward, game_over, self.score


		if game_over == False:

				if self.player.x_speed > 0:
					scroll_speed = self.player.x_speed
					self.distance_covered += self.player.x_speed
				else:
					scroll_speed = 0

				# checking the score
				self.distance_traveled_since_last_spawn = self.distance_covered - (self.pipe_spawn_count * self.distance_interval)
				if self.distance_traveled_since_last_spawn >= self.distance_interval and self.pipe_spawn_count >= 1:
					self.score += 1
					self.reward += 3

				# generate new pipes
				if self.distance_traveled_since_last_spawn >= self.distance_interval:
					pipe_height = random.randint(-100, 100)
					btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
					top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
					self.pipe_group.add(btm_pipe)
					self.pipe_group.add(top_pipe)
					#pipes_spawned = True
					self.pipe_spawn_count += 1

				self.draw_text(str(self.score), font, (255, 255, 255), int(screen_width / 2), 20)

				# draw and scroll the ground
				self.ground_scroll -= scroll_speed
				if abs(self.ground_scroll) > 35:
					self.ground_scroll = 0

				self.pipe_group.update(action,game_over)

		if game_over == True:

				self.respawn_timer()
				# Respawn
				self.reset()


		pygame.display.update()
		return self.reward, game_over, self.score
