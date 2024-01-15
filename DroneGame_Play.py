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
from FlappyCopter import FlappyCopter, Drone, Pipe
			

if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
	game = FlappyCopter()
	local_dir = os.path.dirname(__file__)
	config_path = os.path.join(local_dir, 'config-feedforward.txt')
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
								neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
			
	if os.path.isfile(os.path.join(local_dir,'winner.pkl')):
				with open(os.path.join(local_dir,'winner.pkl'), "rb") as f:
					genome = pickle.load(f)
				genomes = [(1, genome)]
				game.main(genomes,config)
	else:
		print("The File 'winner.pkl' was not found in the current directory")