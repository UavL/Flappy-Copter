import torch
import random
import numpy as np
from collections import deque
from DroneGame import Pipe,Drone,FlappyCopter
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0
        self.gamma = 0.9
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = Linear_QNet(9,1000,4)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game):
        pos_y = game.player.x_position

        vel_x = game.player.x_speed
        vel_y = game.player.y_speed

        phi = game.player.angle
        omega = game.player.angular_speed

        if game.pipe_group:
            pipes = game.pipe_group.sprites()
            if game.distance_traveled_since_last_spawn >= game.distance_interval and game.pipe_spawn_count > 1:
                pipe_bot = pipes[2]
                pipe_top = pipes[3]
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

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else: 
            mini_sample = self.memory
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        

    def train_short_memory(self,  state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves
        self.epsilon = 80 - self.n_games
        final_move =  [0,0,0,0]
        if random.randint(0,200) < self.epsilon:
            move = random.sample(range(-100, 100), 4)
            final_move = [1 if x>0.5 else 0 for x in move]
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            final_move = [1 if x>0.5 else 0 for x in prediction]
        
        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = FlappyCopter()
    total_score = deque(maxlen=12)
    while True:
        state_old = agent.get_state(game)

        final_move = agent.get_action(state_old)

        #play game and get new state
        reward, done, score  = game.play_step(final_move)
        print('Reward:', game.reward)
        state_new = agent.get_state(game)

        #train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)
        
        #remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            #train long memory
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score.append(score)
            mean_score = np.mean(total_score)
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)

if __name__ == '__main__':
    train()
