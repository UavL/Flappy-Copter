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
import pickle
from neat.parallel import ParallelEvaluator

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

	def update(self):
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
		self.pipe_spawn_count = 0
		self.respawn_timer = 3
		self.reward = 0

		# pipe group
		self.pipe_group = pygame.sprite.Group()

		# drone group
		self.drone_group = pygame.sprite.Group()

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
		self.score = 0
		self.game_over = False
		self.reward = 0
		self.pipe_spawn_count = 0
		self.ground_scroll = 0
			

	def draw_text(self, text, font, text_col, x, y):
		img = font.render(text, True, text_col)
		self.screen.blit(img, (x, y))

	def get_state(self,player):
		pos_y = player.x_position

		vel_x = player.x_speed
		vel_y = player.y_speed

		phi = player.angle
		omega = player.angular_speed

		if self.pipe_group:
			pipes = self.pipe_group.sprites()
			if player.distance_traveled_since_last_spawn >= game.distance_interval and game.pipe_spawn_count > 2:
				pipe_bot = pipes[0]
				pipe_top = pipes[1]
			else:
				pipe_bot = pipes[0]
				pipe_top = pipes[1]
			pipe_top_xy = pipe_top.rect.bottomleft
			pipe_bot_xy = pipe_bot.rect.topright
		else:	
			pipe_top_xy = (1000,500)
			pipe_bot_xy = (1000,500)    

		state = [
            pos_y, 
            vel_x, 
            vel_y, 
            phi, 
            omega, 
            pipe_top_xy[0], 
            pipe_top_xy[1], 
            pipe_bot_xy[0], 
            pipe_bot_xy[1]
        ]

		return state
	
	def main(self, genomes, config):
		self.pipe_group = pygame.sprite.Group()
		self.pipe_group.empty()
		self.drone_group.empty()
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
				output = [1 if out>0.5 else 0 for out in output]
				player.update(output)
				self.drone_group.draw(self.screen)
			
			

			# draw the ground
			self.screen.blit(ground_img, (self.ground_scroll, 768))

			# collision check and
			# check if drone has hit the bottom or top
			for x, player in enumerate(players):
				if pygame.sprite.spritecollideany(self.drone_group.sprites()[x], self.pipe_group.sprites()):
					ge[x].fitness -= 2
					ge[x].fitness += player.distance_covered/160
					players.pop(x)
					nets.pop(x)
					ge.pop(x)

				if player.rect.bottom >= 768 or player.rect.top <= 0:
					ge[x].fitness -= 2
					ge[x].fitness += player.distance_covered/160
					players.pop(x)
					nets.pop(x)
					ge.pop(x)


			furthest_distance = 0
			for x, player in enumerate(players):
				if player.distance_covered >= furthest_distance:
					furthest_distance = player.distance_covered
					furthest = x

			# Game loop
			if not len(players) == 0:
				running = True
			else: 
				running = False
				break

			if ticks > 5000:
				for x, player in enumerate(players):
					if player.distance_covered < 5:
						ge[x].fitness -= 60
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
					ge[x].fitness += 5
			
			self.draw_text(str(players[furthest].distance_covered), font, (255, 255, 255), int(screen_width / 2), 890)

			# generate new pipes
			if players[furthest].distance_traveled_since_last_spawn >= self.distance_interval:
				pipe_height = random.randint(-100, 100)
				btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
				top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
				self.pipe_group.add(btm_pipe)
				self.pipe_group.add(top_pipe)
				pipes_spawned = True
				self.pipe_spawn_count += 1

			self.draw_text(str(self.score), font, (255, 255, 255), int(screen_width / 2), 20)

			# draw and scroll the ground
			self.ground_scroll -= scroll_speed

			if abs(self.ground_scroll) > 35:
				self.ground_scroll = 0

			for n, pipe in enumerate(self.pipe_group):
				pipe.update()
				print(self.pipe_group.sprites()[n].rect.x)

			self.pipe_group.update()
			self.pipe_group.draw(self.screen)


			pygame.display.update()

	def run(self,config_file):
			config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
								neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

			# Create the population, which is the top-level object for a NEAT run.
			p = neat.Population(config)

			# Add a stdout reporter to show progress in the terminal.
			p.add_reporter(neat.StdOutReporter(True))
			stats = neat.StatisticsReporter()
			p.add_reporter(stats)
			#p.add_reporter(neat.Checkpointer(5))

			#per = ParallelEvaluator(num_workers=4, eval_function=self.main)

			# Run for up to 50 generations.
			winner = p.run(self.main, 2)

			with open("winner.pkl", "wb") as f:
				pickle.dump(winner, f)
				f.close()

			# show final stats
			print('\nBest genome:\n{!s}'.format(winner))

if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
	game = FlappyCopter()
	local_dir = os.path.dirname(__file__)
	config_path = os.path.join(local_dir, 'config-feedforward.txt')
	game.run(config_path)