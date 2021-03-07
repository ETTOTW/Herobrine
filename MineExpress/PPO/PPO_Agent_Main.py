import gym, ray, torch
import math, time, MalmoUtils
import numpy as np
import json
from tqdm import tqdm
import matplotlib.pyplot as plt
from scipy.spatial import distance
from gym.spaces import Discrete, Box
from ray.rllib.agents import ppo
from gym.envs.toy_text import discrete

class MineExpress(gym.Env):
    
    def __init__(self, env_config):
        self.field_size = 16
        self.soul_sand_density = 0.30
        self.actions = {
            0: 'move 1',
            1: 'move -1',
            2: 'strafe 1',
            3: 'strafe -1'
        }
        
        self.action_space = Discrete(len(self.actions))
        self.observation_space = Box(0, 1, shape=(3, self.field_size ** 2), dtype=np.float32)
        
        self.mission = MalmoUtils.MalmoInitializer()
        

        self.rewards = []
        self.current_reward = 0
        self.step_counter = 0
        self.mission_counter = 0
        self.spawn_point = None
        self.end_point = None
        self.pos = None
        self.distance = None
    
    def reset(self):
        world_state = self.mission.initMalmo(self.getMission())
        
        print(self.current_reward)
        
        self.rewards.append(self.current_reward)
        self.current_reward = 0
        self.mission_counter += 1
        
        self.getLog()
        
        obs, isBlock = self.getObservation(world_state)
        
        return obs
    
    def step(self, action):
        
        world_state = self.mission.getWorldState()
        obs, is_block = self.getObservation(world_state)
        
        command = self.actions[action]
        
        # print(command, self.pos, distance.euclidean(self.pos, self.end_point))
        
        if command  == "move 1"  and self.pos[1] < self.field_size-1 and is_block[self.pos[0], self.pos[1]+1] == 1:
            self.mission.sendCommand(command, 3)
        elif command  == "move -1" and self.pos[1] > 0 and is_block[self.pos[0], self.pos[1]-1]  == 1:
            self.mission.sendCommand(command, 3)
        elif command  == "strafe 1"  and self.pos[0] > 0 and is_block[self.pos[0]-1, self.pos[1]] == 1:
            self.mission.sendCommand(command, 3)
        elif command  == "strafe -1"  and self.pos[0] < self.field_size-1 and is_block[self.pos[0]+1, self.pos[1]] == 1:
            self.mission.sendCommand(command, 3)

        time.sleep(0.2)
        
        self.step_counter += 1
        

        world_state = self.mission.getWorldState()
        obs, is_block = self.getObservation(world_state)
        
        done = not world_state.is_mission_running
        
        reward = 0
        current_dst = distance.cityblock(self.pos, self.end_point)
        if self.distance is not None and current_dst < self.distance:
            reward += 0.5
        elif self.distance is not None and current_dst > self.distance:
            reward -= 0.5
        self.distance = current_dst
            
        for r in world_state.rewards:
            reward += r.getValue()
        

        
        self.current_reward += reward
        
        print(reward,self.current_reward, current_dst)
        
        return obs, reward, done, dict()
        
    
    def getMission(self):
        
        mission = MalmoUtils.MissionHandler("mission.xml")
        
        mission.insert("DrawingDecorator", "DrawCuboid", x1=f"{-1}", x2=f"{self.field_size}", y1=f"{9}", y2=f"{9}",
                       z1=f"{-1}", z2=f"{self.field_size}", type='barrier')
        
        for i in range(0, self.field_size, 3):
            for j in range(0, self.field_size, 3):
                mission.insert("DrawingDecorator", "DrawBlock", x=f"{i}", y=f"{10}", z=f"{j}", type="gold_block")
                
                if j < self.field_size - 1:
                    if np.random.binomial(1, self.soul_sand_density) == 0:
                        mission.insert("DrawingDecorator", "DrawCuboid", x1=f"{i}", x2=f"{i}", y1=f"{10}", y2=f"{10}",
                                       z1=f"{j + 1}", z2=f"{j + 2}", type='diamond_block')
                    else:
                        mission.insert("DrawingDecorator", "DrawCuboid", x1=f"{i}", x2=f"{i}", y1=f"{10}", y2=f"{10}",
                                       z1=f"{j + 1}", z2=f"{j + 2}", type='soul_sand')
                    
                    if np.random.binomial(1, self.soul_sand_density) == 0:
                        mission.insert("DrawingDecorator", "DrawCuboid", x1=f"{j + 1}", x2=f"{j + 2}", y1=f"{10}",
                                       y2=f"{10}", z1=f"{i}", z2=f"{i}", type='diamond_block')
                    else:
                        mission.insert("DrawingDecorator", "DrawCuboid", x1=f"{j + 1}", x2=f"{j + 2}", y1=f"{10}",
                                       y2=f"{10}", z1=f"{i}", z2=f"{i}", type='soul_sand')
        
        self.spawn_point = np.array((np.random.choice(range(0, self.field_size, 3)), 0))
        self.end_point = np.array((np.random.choice(range(0, self.field_size, 3)), self.field_size - 1))
        
        if self.pos is None:
            self.pos = self.spawn_point
        
        mission.insert("DrawingDecorator", "DrawBlock", x=f"{self.spawn_point[0]}", y=f"{10}",
                       z=f"{self.spawn_point[1]}", type="emerald_block")
        mission.insert("DrawingDecorator", "DrawBlock", x=f"{self.end_point[0]}", y=f"{10}", z=f"{self.end_point[1]}",
                       type="redstone_block")
        
        mission.insert("AgentStart", "Placement", x=f"{self.spawn_point[0] + 0.5}", y=f"{11}",
                       z=f"{self.spawn_point[1] + 0.5}", pitch="45", yaw="0")
        
        mission.insert("Grid", "min", x=f"{0}", y=f"{10}", z=f"{0}")
        mission.insert("Grid", "max", x=f"{self.field_size-1}", y=f"{10}", z=f"{self.field_size-1}")
        
        mission.write("test.xml")
        
        return str(mission)
    
    def getObservation(self, world_state):
        obs = np.zeros((3, self.field_size ** 2))
        is_block = np.zeros(self.field_size ** 2)
        
        while world_state.is_mission_running:
            time.sleep(0.2)
            world_state = self.mission.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')
            
            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                
                # Get observation
                grid = observations['floor']
                
                x_pos = math.floor(observations["XPos"])
                z_pos = math.floor(observations["ZPos"])
                
                self.pos = np.array([x_pos, z_pos])
                
                for i, x in enumerate(grid):
                    if x == "diamond_block":
                        obs[0, i] = 1
                    elif x == "soul_sand":
                        obs[1, i] = 1
                    
                    is_block[i] = x in {"diamond_block", "soul_sand", "redstone_block", "emerald_block"}
                
                obs = obs.reshape((3, 16, 16))
                is_block = is_block.reshape(16, 16)
                obs[2, self.end_point[0], self.end_point[1]] = 1
                obs[2, x_pos, z_pos] = 1
                
                obs = obs.reshape((3, self.field_size ** 2))
                # print(obs, is_block)
                break
        is_block = is_block.reshape(self.field_size, self.field_size)
        
        return obs, is_block
    
    def getLog(self):
        plt.ion()
        plt.clf()
        plt.plot(range(0, len(self.rewards)), self.rewards)
        plt.show()
        plt.ion()
        
if __name__ == "__main__":
    ray.init()
    trainer = ppo.PPOTrainer(env=MineExpress, config={
        'env_config': {},  # No environment parameters to configure
        'framework': 'torch',  # Use pyotrch instead of tensorflow
        'num_gpus': 1,  # We aren't using GPUs
        'num_workers': 0  # We aren't using parallelism
    })

    while True:
        print(trainer.train())
    
    