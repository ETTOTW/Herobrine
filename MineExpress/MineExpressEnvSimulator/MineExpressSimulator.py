import gym
import time, MalmoUtils
import numpy as np
import json
from gym.spaces import Discrete
import os



class MineExpressSimulator(gym.Env):
    """
    Agent Actions:
        0: move north
        1: move south
        2: move east
        3: move west
        4: pickup package
        5: drop off package

    Package Status:
        0: (0, 0)
        1: (4, 0)
        2: (0, 4)
        3: (4, 3)
        4: out for delivery

    Package Destination:
        0: (0, 0)
        1: (4, 0)
        2: (0, 4)
        3: (4, 3)

    """
    
    def __init__(self, seed=None):
        Map = [
            "           ",
            " C-P P-P-C ",
            " : - - - - ",
            " P-P P-P-P ",
            " - - - - - ",
            " P-P:P:P-P ",
            " - - - - - ",
            " P P-P P-P ",
            " - - - - - ",
            " C P-P C-P ",
            "           "
        ]
        if seed is not None:
            np.random.seed(seed)
        
        self.map = np.asarray(Map, dtype='c')

        self.locations = [[0, 0], [4, 0], [0, 4], [4, 3]]

        self.max_x = 5
        self.max_z = 5
        self.action_num = 6
        self.state_num = 500
        
        self.action_space = Discrete(self.action_num)
        self.observation_space = Discrete(self.state_num)
    
    def reset(self):
        self.agent_loc = np.random.randint(0, 5, 2)
        self.package_loc = np.random.randint(0, len(self.locations))
        self.package_dest = np.random.randint(0, len(self.locations))
        while self.package_dest == self.package_loc:
            self.package_dest = np.random.randint(0, len(self.locations))
        self.state = self.getStateNumber()
        return  self.state
        
    def step(self, action: int):
        movement_list, cost_list = self.getObservation()
        reward = 0
        if action < 4:
            reward = cost_list[action]
        done = False
        
        if action == 0 and movement_list[0]:
            self.agent_loc[0] = max(self.agent_loc[0] - 1, 0)
        elif action == 1 and movement_list[1]:
            self.agent_loc[0] = min(self.agent_loc[0] + 1, self.max_x-1)
        elif action == 2 and movement_list[2]:
            self.agent_loc[1] = min(self.agent_loc[1] + 1, self.max_z-1)
        elif action == 3 and movement_list[3]:
            self.agent_loc[1] = max(self.agent_loc[1] - 1, 0)
        elif action == 4:
            if self.package_loc < 4 and self.agent_loc.tolist() == self.locations[self.package_loc]:
                self.package_loc = 4
            else:
                reward = -10
        elif action == 5:
            if self.agent_loc.tolist() == self.locations[self.package_dest] and self.package_loc == 4:
                self.package_loc = self.package_dest
                done = True
                reward = 20
            else:
                reward = -10
                
        self.last_action = action
        self.state = self.getStateNumber()

        return self.state, reward, done, f"last action: {self.last_action}"
    
    def getObservation(self):
        x, y = self.agent_loc
        x, y = 2*x+1, 2*y + 1
        
        obs = [self.map[x-1][y], self.map[x+1][y], self.map[x][y+1], self.map[x][y-1]]
        # print(obs)
        
        movement = [x != b" " for x in obs]
        cost = [-1 if x == b"-" else -4 for x in obs]
        
        return movement, cost

    def getStateNumber(self):
        return 4 * (5 * ((5 * self.agent_loc[0]) + self.agent_loc[1]) + self.package_loc) + self.package_dest

# if __name__ == "__main__":
#     mission = MineExpressSimulator(0)
#     mission.reset()
#     print(mission.agent_loc, mission.package_loc, mission.package_dest)
#
#     action_list = [0, 0, 2, 2, 2, 1, 1, 4, 5, 0, 0, 0, 0, 2, 4, 5, 1, 1, 3, 3, 3, 3, 0, 0, 4, 5, 0, 2, 3, 1, 1, 1, 1, 5, 1, 2, 3]
#     for a in action_list:
#         s, r, d, i = mission.step(a)
        # print(
        #     f"New State {s}, Reward {r}, Done {d}, Action {i}, A Loc {mission.agent_loc}, P Loc {mission.package_loc}, D Loc {mission.package_dest}")
#
#     mission.reset()
#     print(mission.agent_loc, mission.package_loc, mission.package_dest)
#     mission.reset()
#     print(mission.agent_loc, mission.package_loc, mission.package_dest)
#     mission.reset()
#     print(mission.agent_loc, mission.package_loc, mission.package_dest)
#     mission.reset()
#     print(mission.agent_loc, mission.package_loc, mission.package_dest)