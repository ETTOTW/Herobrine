import gym
import time, MalmoUtils
import numpy as np
import json
from gym.spaces import Discrete
import os


class MineExpress(gym.Env):
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
        if seed is not None:
            np.random.seed(seed)
        self.mission = MalmoUtils.MalmoInitializer()
        self.absolute_position = \
            [[(2.5, 2.5), (12.5, 2.5), (22.5, 2.5), (32.5, 2.5), (42.5, 2.5)],
             [(2.5, 12.5), (12.5, 12.5), (22.5, 12.5), (32.5, 12.5), (42.5, 12.5)],
             [(2.5, 22.5), (12.5, 22.5), (22.5, 22.5), (32.5, 22.5), (42.5, 22.5)],
             [(2.5, 32.5), (12.5, 32.5), (22.5, 32.5), (32.5, 32.5), (42.5, 32.5)],
             [(2.5, 42.5), (12.5, 42.5), (22.5, 42.5), (32.5, 42.5), (42.5, 42.5)]]
        
        self.locations = [[0, 0], [4, 0], [0, 4], [4, 3]]
        
        self.max_x = 5
        self.max_z = 5
        self.action_num = 6
        self.state_num = 500
        
        self.action_space = Discrete(self.action_num)
        self.observation_space = Discrete(self.state_num)
        
        # self.reset()
    
    def reset(self):
        # Reset init State
        self.agent_loc = np.random.randint(0, 5, 2)
        self.package_loc = np.random.randint(0, len(self.locations))
        self.package_dest = np.random.randint(0, len(self.locations))
        while self.package_dest == self.package_loc:
            self.package_dest = np.random.randint(0, len(self.locations))
        self.state = self.getStateNumber(self.agent_loc, self.package_loc, self.package_dest)
        self.last_action = None
        
        world_state = self.mission.getWorldState()
        if world_state.is_mission_running:
            time.sleep(0.1)
            self.mission.sendCommand("quit")
            time.sleep(0.2)
        
        self.mission.initMalmo(self.getMission(), "MineExpress")
        
        # time.sleep(0.5)
        
        return self.state
    
    def step(self, action: int):
        movement_list, cost_list = self.getObservation()
        
        reward = 0
        if action < 4:
            reward = cost_list[action]
        done = False
        
        if action == 0 and movement_list[0]:
            self.agent_loc[0] = max(self.agent_loc[0] - 1, 0)
            self.actionHandler(action)
        elif action == 1 and movement_list[1]:
            self.agent_loc[0] = min(self.agent_loc[0] + 1, self.max_x - 1)
            self.actionHandler(action)
        elif action == 2 and movement_list[2]:
            self.agent_loc[1] = min(self.agent_loc[1] + 1, self.max_z - 1)
            self.actionHandler(action)
        elif action == 3 and movement_list[3]:
            self.agent_loc[1] = max(self.agent_loc[1] - 1, 0)
            self.actionHandler(action)
        elif action == 4:
            if self.package_loc < 4 and self.agent_loc.tolist() == self.locations[self.package_loc]:
                self.actionHandler(action)
                self.package_loc = 4
                # reward = 5
            else:
                reward = -10
        elif action == 5:
            if self.agent_loc.tolist() == self.locations[self.package_dest] and self.package_loc == 4:
                self.package_loc = self.package_dest
                self.actionHandler(action)
                done = True
                reward = 20
            # elif self.agent_loc.tolist() in self.locations and self.package_loc == 4:
            #     self.package_loc = self.locations.index(self.agent_loc.tolist())
            #     # self.actionHandler(action)
            #     reward = -10
            else:
                reward = -10
        
        self.last_action = action
        self.state = self.getStateNumber(self.agent_loc, self.package_loc, self.package_dest)
        
        return self.state, reward, done, f"last action: {self.last_action}"
    
    # def actionHandler(self, action):
    #     useChestProcess = \
    #         ["use 1", "use 0", "swapInventoryItems chest:0 0", "tpy 10", "tpy 2"]
    #
    #     if action in {0, 1, 2, 3}:
    #         x, y = self.agent_loc
    #         x, y = self.absolute_position[x][y]
    #         self.mission.sendCommand(f"tp {x} 2 {y}")
    #         # time.sleep(0.1)
    #
    #     elif action in {4, 5}:
    #         for cmd in useChestProcess:
    #             self.mission.sendCommand(cmd)
    #             # time.sleep(0.1)
    
    # def actionHandler(self, action):
    #     useChestProcess = \
    #         ["setPitch 90", "use 1", "use 0", "swapInventoryItems chest:0 0", "tpy 10", "tpy 2", "setPitch 45"]
    #
    #     if action == 0:
    #         self.mission.sendCommand("setYaw 180")
    #         time.sleep(0.1)
    #         for i in range(0, 10):
    #             self.mission.sendCommand("movenorth")
    #             time.sleep(0.1)
    #     elif action == 1:
    #         self.mission.sendCommand("setYaw 0")
    #         time.sleep(0.1)
    #         for i in range(0, 10):
    #             self.mission.sendCommand("movesouth 1")
    #             time.sleep(0.1)
    #     elif action == 2:
    #         self.mission.sendCommand("setYaw -90")
    #         time.sleep(0.1)
    #         for i in range(0, 10):
    #             self.mission.sendCommand("moveeast 1")
    #             time.sleep(0.1)
    #     elif action == 3:
    #         self.mission.sendCommand("setYaw 90")
    #         time.sleep(0.1)
    #         for i in range(0, 10):
    #             self.mission.sendCommand("movewest 1")
    #             time.sleep(0.1)
    #     elif action in {4, 5}:
    #         for cmd in useChestProcess:
    #             self.mission.sendCommand(cmd)
    #             time.sleep(0.1)
    
    
    def actionHandler(self, action):
        useChestProcess = \
            ["setPitch 90", "use 1", "use 0", "swapInventoryItems chest:0 0", "tpy 10", "tpy 2", "setPitch 60"]

        if action == 0:
            self.mission.sendCommand("movenorth 1", 10)
        elif action == 1:
            self.mission.sendCommand("movesouth 1", 10)
        elif action == 2:
            self.mission.sendCommand("moveeast 1", 10)
        elif action == 3:
            self.mission.sendCommand("movewest 1", 10)
        elif action in {4, 5}:
            for cmd in useChestProcess:
                self.mission.sendCommand(cmd)
    
    def getMission(self):
        start_pos = self.absolute_position[self.agent_loc[0]][self.agent_loc[1]]
        
        mission = MalmoUtils.MissionHandler("mission.xml")
        mission.set("FileWorldGenerator", src=f"{os.getcwd()}\\MineExpressWorld")
        mission.insert("DrawingDecorator", "DrawBlock", type="redstone_block", x=f"{self.package_loc}", y="2", z="-10")
        mission.insert("AgentStart", "Placement", x=f"{start_pos[0]}", y=f"{2}", z=f"{start_pos[1]}", pitch="60",
                       yaw="180")
        return str(mission)
    
    def getObservation(self):
        world_state = self.mission.getWorldState()
        while world_state.is_mission_running:
            time.sleep(0.1)
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')
            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                
                # Get observation
                grid = observations['floor']
                grid = np.array(grid).reshape((2, 7, 7))
                
                if all([x in {"bedrock", "air"} for x in grid[0].flatten()]):
                    grid = grid[1]
                else:
                    grid = grid[0]
                
                obs = [grid[0][3], grid[6][3], grid[3][6], grid[3][0]]
                
                movement = [x in {"stone", "soul_sand"} for x in obs]
                cost = [-1 if x == "stone" else -4 for x in obs]
                
                return movement, cost
            world_state = self.mission.getWorldState()
        raise
    
    def getStateNumber(self, agent_loc, package_loc, package_dest):
        return 4 * (5 * ((5 * agent_loc[0]) + agent_loc[1]) + package_loc) + package_dest
    
    def getAbsolutePosition(self):
        x, y = self.agent_loc
        return self.absolute_position[x][y]
