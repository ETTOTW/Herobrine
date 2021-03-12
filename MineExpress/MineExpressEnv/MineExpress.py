import gym, ray, torch
import math, time, MalmoUtils
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
    
    def __init__(self, seed = None):
        if seed is not None:
            np.random.seed(seed)
        self.mission = MalmoUtils.MalmoInitializer()
        self.absolute_position = \
            [[(2.5, 2.5), (12.5, 2.5), (22.5, 2.5), (32.5, 2.5), (42.5, 2.5)],
             [(2.5, 12.5), (12.5, 12.5), (22.5, 12.5), (32.5, 12.5), (42.5, 12.5)],
             [(2.5, 22.5), (12.5, 22.5), (22.5, 22.5), (32.5, 22.5), (42.5, 22.5)],
             [(2.5, 32.5), (12.5, 32.5), (22.5, 32.5), (32.5, 32.5), (42.5, 32.5)],
             [(2.5, 42.5), (12.5, 42.5), (22.5, 42.5), (32.5, 42.5), (42.5, 42.5)]]
        
        self.locations = [[0, 0],[4, 0], [0, 4], [4, 3]]
        
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
            self.mission.sendCommand("quit")
            time.sleep(0.1)
        
        self.mission.initMalmo(self.getMission(), "MineExpress")
        
        time.sleep(0.5)
        
        return self.state
    
    def step(self, action):
        movement_list = self.getObservation()
        # print(movement_list)
        reward = -1
        done = False
        
        if action == 0 and movement_list[0]:
            self.agent_loc[0] = max(self.agent_loc[0] - 1, 0)
            self.actionHandler(action)
        elif action == 1 and movement_list[1]:
            self.agent_loc[0] = min(self.agent_loc[0] + 1, self.max_x)
            self.actionHandler(action)
        elif action == 2 and movement_list[2]:
            self.agent_loc[1] = min(self.agent_loc[1] + 1, self.max_z)
            self.actionHandler(action)
        elif action == 3 and movement_list[3]:
            self.agent_loc[1] = max(self.agent_loc[1] - 1, 0)
            self.actionHandler(action)
        elif action == 4:
            if self.package_loc < 4 and self.agent_loc.tolist() == self.locations[self.package_loc]:
                self.actionHandler(action)
                self.package_loc = 4
            else:
                reward -= 10
        elif action == 5:
            if self.agent_loc.tolist() == self.locations[self.package_dest] and self.package_loc == 4:
                self.package_loc = self.package_dest
                self.actionHandler(action)
                done = True
                reward += 20
            elif self.agent_loc.tolist() in self.locations and self.package_loc == 4:
                self.package_loc = self.locations.index(self.agent_loc.tolist())
                self.actionHandler(action)
                reward -= 10
            else:
                reward -= 10
        
        time.sleep(0.3)
        world_state = self.mission.getWorldState()
        if not world_state.is_mission_running:
            done = True
        for r in world_state.rewards:
            reward += r.getValue()
        
        self.last_action = action
        self.state = self.getStateNumber(self.agent_loc, self.package_loc, self.package_dest)
        
        time.sleep(0.5)
        
        return self.state, reward, done, f"last action: {self.last_action}"
    
    def actionHandler(self, action):
        useChestProcess = \
            ["setPitch 90", "use 1", "use 0", "swapInventoryItems chest:0 0", "tpy 10", "tpy 2", "setPitch 0"]
        
        if action == 0:
            self.mission.sendCommand("setYaw 180")
            time.sleep(0.1)
            for i in range(0, 10):
                self.mission.sendCommand("movenorth")
                time.sleep(0.1)
        elif action == 1:
            self.mission.sendCommand("setYaw 0")
            time.sleep(0.1)
            for i in range(0, 10):
                self.mission.sendCommand("movesouth 1")
                time.sleep(0.1)
        elif action == 2:
            self.mission.sendCommand("setYaw -90")
            time.sleep(0.1)
            for i in range(0, 10):
                self.mission.sendCommand("moveeast 1")
                time.sleep(0.1)
        elif action == 3:
            self.mission.sendCommand("setYaw 90")
            time.sleep(0.1)
            for i in range(0, 10):
                self.mission.sendCommand("movewest 1")
                time.sleep(0.1)
        elif action in {4, 5}:
            for cmd in useChestProcess:
                self.mission.sendCommand(cmd)
                time.sleep(0.1)
    
    def getMission(self):
        start_pos = self.absolute_position[self.agent_loc[0]][self.agent_loc[1]]
        
        mission = MalmoUtils.MissionHandler("mission.xml")
        mission.set("FileWorldGenerator", src=f"{os.getcwd()}\\MineExpressWorld")
        mission.insert("DrawingDecorator", "DrawBlock", type="redstone_block", x=f"{self.package_loc}", y="2", z="-10")
        mission.insert("AgentStart", "Placement", x=f"{start_pos[0]}", y=f"{2}", z=f"{start_pos[1]}", pitch="0",
                       yaw="180")
        return str(mission)
    
    def getObservation(self):
        world_state = self.mission.getWorldState()
        while world_state.is_mission_running:
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
                
                path_list = {"stone", "soul_sand"}
                north = True if grid[0][3] in path_list else False
                south = True if grid[6][3] in path_list else False
                east = True if grid[3][6] in path_list else False
                west = True if grid[3][0] in path_list else False
                return (north, south, east, west)
        raise
    
    def getStateNumber(self, agent_loc, package_loc, package_dest):
        return 4 * (5 * ((5 * agent_loc[0]) + agent_loc[1]) + package_loc) + package_dest


if __name__ == "__main__":
#     mission = MineExpress(0)
#
#     time.sleep(1)
#     print(mission.package_loc, mission.package_dest)
#
#     print(mission.agent_loc)
#     s, r, d, i  = mission.step(0)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(0)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(2)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(2)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(2)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(1)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(1)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(4)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     print(mission.agent_loc)
#     s, r, d, i  = mission.step(0)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(0)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     print(mission.agent_loc)
#     s, r, d, i  = mission.step(3)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(3)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(3)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(1)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(1)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)
#     s, r, d, i  = mission.step(5)
#     print(mission.agent_loc)
#     print(s,r,d,i)
#     time.sleep(0.2)

    mission = MineExpress(0)
    mission.reset()
    print(1)
    mission.step(0)

    mission.reset()
    mission.step(0)
    print(2)