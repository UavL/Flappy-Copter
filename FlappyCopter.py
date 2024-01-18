import pygame
import os
from pygame.locals import *
from math import sin, cos, pi, sqrt
from random import randrange
import random
import neat

pygame.init()

screen_width = 864
screen_height = 936



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

		self.distance_traveled_since_last_spawn = 0
		self.distance_covered = 0

		self.rect.center = [self.x_position, self.y_position]
		self.clicked = False

		# Physics constants
		self.gravity = 0.0981
		self.thruster_amplitude = 0.04
		self.diff_amplitude = 0.003
		self.thruster_mean = 0.04
		self.mass = 1
		self.arm = 25

	def update(self,action):
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

	def update(self,scroll_sp):
		self.rect.x -= scroll_sp
		if self.rect.right < 0:
			self.kill()

class FlappyCopter():

	def __init__(self):
		# Game constants
		self.clock = pygame.time.Clock()

		self.screen = pygame.display.set_mode((screen_width, screen_height))

		# Initialize physics variables
		self.score = 0
		self.ground_scroll = 0
		self.distance_interval = 500
		self.pipe_spawn_count = 0

		# pipe group
		self.pipe_group = pygame.sprite.Group()

		# drone group
		self.drone_group = pygame.sprite.Group()

	# def respawn_timer(self):
	# 	# Display respawn timer
	# 	respawn_text = font.render(
	# 		str(int(self.respawn_timer) + 1), True, (0, 0, 0))
	# 	respawn_text.set_alpha(124)
	# 	self.screen.blit(
	# 		respawn_text,
	# 		(screen_width / 2 - respawn_text.get_width() / 2,
	# 			screen_height / 2 - respawn_text.get_height() / 2,),)

	# 	self.respawn_timer -= 1 / 60

	def reset(self):
		self.pipe_group.empty()
		self.drone_group.empty()
		self.score = 0
		self.pipe_spawn_count = 0
		self.ground_scroll = 0
			

	def draw_text(self, text, font, text_col, x, y):
		img = font.render(text, True, text_col)
		self.screen.blit(img, (x, y))

	def get_state(self,player):
		pos_x = player.x_position
		pos_y = player.y_position

		vel_x = player.x_speed
		vel_y = player.y_speed

		phi = player.angle
		omega = player.angular_speed

		if self.pipe_group:
			pipes = self.pipe_group.sprites()
			if len(pipes) > 2:
				pipe_bot = pipes[3]
				pipe_top = pipes[2]
			else:
				pipe_bot = pipes[1]
				pipe_top = pipes[0]
			pipe_top_xy = pipe_top.rect.topleft
			pipe_bot_xy = pipe_bot.rect.bottomright
		else:	
			pipe_top_xy = (850,500)
			pipe_bot_xy = (930,300)    

		state = [
			pos_x,
            pos_y, 
            vel_x, 
            vel_y, 
            phi, 
            omega, 
            (pipe_top_xy[0]-pos_x), 
            (pipe_top_xy[1]-pos_y), 
            (pipe_bot_xy[0]-pos_x), 
            (pipe_bot_xy[1]-pos_y)
        ]

		return state
	
	def main(self, genomes, config):
		nets = []
		ge = []
		players = []

		for g_id, g in genomes:
			g.fitness = 0
			net = neat.nn.FeedForwardNetwork.create(g,config)
			nets.append(net)
			players.append(Drone(400, int(screen_height / 2)))
			ge.append(g)			
				

		for player in players:	
			self.drone_group.add(player)

		ticks = 0
		furthest = 0
		scroll_speed = 0
		running = True
		while running:
			ticks += 1
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					run = False
					pygame.quit()
					quit()
			
			self.clock.tick(fps)

			# Display background
			self.screen.blit(bg, (0,0))

			for x, player in enumerate(players):
				output = nets[players.index(player)].activate(self.get_state(player))
				output = [1 if out>0 else 0 for out in output]
				player.update(output)
				self.drone_group.draw(self.screen)
			
			

			# draw the ground
			self.screen.blit(ground_img, (self.ground_scroll, 768))

			# collision check and
			# check if drone has hit the bottom or top
			self.next_up = 0
			self.diff = 0
			for x, player in enumerate(players):
				if pygame.sprite.spritecollideany(player, self.pipe_group.sprites()) or (player.rect.bottom >= 768 or player.rect.top <= 0):
					if x == furthest:
						self.next_up = x
						self.diff = player.rect.x
					ge[x].fitness -= 6
					ge[x].fitness += player.distance_covered/160
					players.pop(x)
					nets.pop(x)
					ge.pop(x)
					self.drone_group.remove(player)
			
			furthest_distance = 0
			changed = False
			for x, player in enumerate(players):
				if player.distance_covered >= furthest_distance:
					furthest_distance = player.distance_covered
					furthest = x
					changed = True
			if changed == False:
				furthest = 0
			# Game loop
			if not len(players) == 0:
				running = True
			else: 
				running = False
				break

			if self.next_up > 0:
				dif = (self.diff-players[furthest].rect.x)
				for player in players:
					player.rect.x += dif
				self.pipe_group.update(-dif)

			if ticks > 1800:
				for x, player in enumerate(players):
					if player.distance_covered < 5:
						ge[x].fitness -= 10
				running = False
				break

			if players[furthest].x_speed > 0:
				scroll_speed = players[furthest].x_speed
				for x, player in enumerate(players):
					player.rect.x -= scroll_speed
			else:
				scroll_speed = 0
				players[furthest].rect.x += players[furthest].x_speed

			for x, player in enumerate(players):
				player.distance_covered += player.x_speed

				# checking the score and fitness
				player.distance_traveled_since_last_spawn = player.distance_covered - (self.pipe_spawn_count * self.distance_interval)
				if player.distance_traveled_since_last_spawn >= self.distance_interval and self.pipe_spawn_count >= 1:
					self.score += 1
					ge[x].fitness += 6 * self.score
			
			self.draw_text(str(players[furthest].distance_covered), font, (255, 255, 255), int(screen_width / 2), 890)

			# generate new pipes
			if players[furthest].distance_traveled_since_last_spawn >= self.distance_interval:
				pipe_height = random.randint(-100, 100)
				btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
				top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
				self.pipe_group.add(btm_pipe)
				self.pipe_group.add(top_pipe)
				self.pipe_spawn_count += 1
			
			self.draw_text(str(self.score), font, (255, 255, 255), int(screen_width / 2), 20)

			# draw and scroll the ground
			self.ground_scroll -= scroll_speed

			if abs(self.ground_scroll) > 35:
				self.ground_scroll = 0

			#for n, pipe in enumerate(self.pipe_group):
			#	pipe.update(scroll_speed)
			#	print(self.pipe_group.sprites()[n].rect.x)

			self.pipe_group.update(scroll_speed)
			self.pipe_group.draw(self.screen)


			pygame.display.update()
		self.reset()