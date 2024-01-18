import torch
import math

class model()
    def __init__(self):
        self.NN = torch.nn.Sequential(
            torch.nn.Linear(1,10),
            torch.nn.ReLU(),
            torch.nn.Linear(10,50),
            torch.nn.ReLU(),
            torch.nn.Linear(50,10),
            torch.nn.ReLU(),
            torch.nn.Linear(10,10),
            torch.nn.ReLU(),
            torch.nn.Linear(10,4))
        self.Loss = torch.nn.MSELoss()
        self.optim = torch.optim.Adam( params=self.NN.parameters(), lr=0.001)

    def out(self,input):
        return self.NN(input)
    
    def pred()

    def train_step()