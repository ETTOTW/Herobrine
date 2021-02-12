# Rllib docs: https://docs.ray.io/en/latest/rllib.html

try:
    from malmo import MalmoPython
except:
    import MalmoPython

import sys
import time
import json
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import randint

import gym, ray
from gym.spaces import Discrete, Box
from ray.rllib.agents import ppo

from tqdm import tqdm


class DiamondCollector(gym.Env):
    
    def __init__(self, env_config):
        # Static Parameters
        self.size = 50
        self.reward_density = .1
        self.penalty_density = .02
        self.obs_size = 5
        
        # todo: 100 steps
        self.max_episode_steps = 100
        # todo: 10 frequency
        self.log_frequency = 10
        self.action_dict = {
            0: 'move 1',  # Move one block forward
            1: 'turn 1',  # Turn 90 degrees to the right
            2: 'turn -1',  # Turn 90 degrees to the left
            3: 'attack 1'  # Destroy block
        }
        
        # Rllib Parameters
        self.action_space = Box(low=-1, high=1, shape=(3,))
        
        # self.action_space = Discrete(len(self.action_dict))
        
        self.observation_space = Box(0, 1, shape=(2 * self.obs_size * self.obs_size,), dtype=np.float32)
        
        # Malmo Parameters
        self.agent_host = MalmoPython.AgentHost()
        try:
            self.agent_host.parse(sys.argv)
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agent_host.getUsage())
            exit(1)
        
        # DiamondCollector Parameters
        self.obs = None
        self.allow_break_action = False
        self.episode_step = 0
        self.episode_return = 0
        self.returns = []
        self.steps = []
        
        self.pbar = tqdm(total=50000)
    
    def reset(self):
        """
        Resets the environment for the next episode.

        Returns
            observation: <np.array> flattened initial obseravtion
        """
        # Reset Malmo
        world_state = self.init_malmo()
        
        # Reset Variables
        self.returns.append(self.episode_return)
        current_step = self.steps[-1] if len(self.steps) > 0 else 0
        self.steps.append(current_step + self.episode_step)
        self.episode_return = 0
        self.episode_step = 0
        
        # Log
        if len(self.returns) > self.log_frequency + 1 and \
                len(self.returns) % self.log_frequency == 0:
            self.log_returns()
        
        # Get Observation
        self.obs, self.allow_break_action = self.get_observation(world_state)
        
        return self.obs
    
    def step(self, action):
        """
        Take an action in the environment and return the results.

        Args
            action: <int> index of the action to take

        Returns
            observation: <np.array> flattened array of obseravtion
            reward: <int> reward from taking action
            done: <bool> indicates terminal state
            info: <dict> dictionary of extra information
        """
        
        # print(action)
        
        def getObservation():
            world_state = self.agent_host.getWorldState()
            for error in world_state.errors:
                print("Error:", error.text)
            self.obs, self.allow_break_action = self.get_observation(world_state)
        
        # Get Action
        # command = action[2]
        # if command > 0 and self.allow_break_action:
        #     self.agent_host.sendCommand(f"move 0")
        #     self.agent_host.sendCommand(f"turn 0")
        #     time.sleep(0.1)
        #     getObservation()
        #     if self.allow_break_action:
        #         self.agent_host.sendCommand(f"attack 1")
        #         while (self.allow_break_action):
        #             getObservation()
        #             time.sleep(0.01)
        #         time.sleep(0.1)
        #         self.agent_host.sendCommand(f"attack 0")
        #
        # self.agent_host.sendCommand(f"move {action[0]}")
        # self.agent_host.sendCommand(f"turn {action[1]}")
        # time.sleep(0.1)
        #
        # self.episode_step += 1
        self.pbar.update()
        
        # Get Observation
        world_state = self.agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:", error.text)
        self.obs, self.allow_break_action = self.get_observation(world_state)
        
        # Get Done
        done = not world_state.is_mission_running
        
        # Get Reward
        reward = 0
        for r in world_state.rewards:
            reward += r.getValue()
        self.episode_return += reward
        
        return self.obs, reward, done, dict()
    
    def get_mission_xml(self):
        self.size = 8
        
        map = np.zeros((16, 16))
        
        for i in range(0, 16, 3):
            map[i] = np.ones(16)
            map[:, i] = np.ones(16)
            
            for j in range(1, 14, 3):
                map[i, j:j + 2] = list(np.random.binomial(1, 0.25, 1) + 1) * 2
                map[j:j + 2, i] = list(np.random.binomial(1, 0.25, 1) + 1) * 2
        
        spawnPoint = np.random.randint(0, 7, 2)
        while (map[spawnPoint[0], spawnPoint[1]] == 0):
            spawnPoint = np.random.randint(0, 7, 2)
        
        endPoint = np.random.randint(8, 15, 2)
        while (map[endPoint[0], endPoint[1]] == 0):
            endPoint = np.random.randint(8, 15, 2)
        
        mapXML = ""
        
        for x in range(self.size, -self.size, -1):
            for y in range(self.size, -self.size, -1):
                
                if map[x + self.size - 1][y + self.size - 1] == 0:
                    mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='air' />"
                elif x + self.size - 1 == spawnPoint[0] and y + self.size - 1 == spawnPoint[1]:
                    mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='emerald_block' />"
                elif x + self.size - 1 == endPoint[0] and y + self.size - 1 == endPoint[1]:
                    mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='redstone_block' />"
                elif map[x + self.size - 1][y + self.size - 1] == 1:
                    mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='diamond_block' />"
                elif map[x + self.size - 1][y + self.size - 1] == 2:
                    mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='soul_sand' />"
        
        return f"""
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <About>
        <Summary>Diamond Collector</Summary>
    </About>
    <ServerSection>
        <ServerInitialConditions>
            <Time>
                <StartTime>12000</StartTime>
                <AllowPassageOfTime>false</AllowPassageOfTime>
            </Time>
            <Weather>clear</Weather>
        </ServerInitialConditions>
        <ServerHandlers>
            <FlatWorldGenerator generatorString="3;1*minecraft:bedrock,1*minecraft:lava;0;"/>
            <DrawingDecorator>
                            
                {mapXML}

            </DrawingDecorator>
            <ServerQuitWhenAnyAgentFinishes/>
        </ServerHandlers>
    </ServerSection>

    <AgentSection mode="Survival">
        <Name>CS175DiamondCollector</Name>
        <AgentStart>
            <Placement x="{spawnPoint[0] - self.size+1 + 0.5}" y="11" z="{spawnPoint[1] - self.size+1 + 0.5}" pitch="45" yaw="0"/>
            <Inventory>
                <InventoryItem slot="0" type="diamond_pickaxe"/>
            </Inventory>
        </AgentStart>
        <AgentHandlers>

            <RewardForCollectingItem>
                <Item type='diamond' reward='1'/>
            </RewardForCollectingItem>

            <RewardForTouchingBlockType>
                <Block type='lava' reward='-1'/>
            </RewardForTouchingBlockType>

            <ContinuousMovementCommands/>

            <ObservationFromFullStats/>
            <ObservationFromRay/>
            <ObservationFromGrid>
                <Grid name="floorAll">
                    <min x="-{str(int(self.obs_size / 2))}" y="-1" z="-{str(int(self.obs_size / 2))}"/>
                    <max x="{str(int(self.obs_size / 2))}" y="0" z="{str(int(self.obs_size / 2))}"/>
                </Grid>
            </ObservationFromGrid>

            <AgentQuitFromReachingCommandQuota>
                <Quota commands="move" quota="{self.max_episode_steps}"/>
                <Quota commands="turn" quota="{self.max_episode_steps}"/>
                <Quota commands="attack" quota="{2 * self.max_episode_steps}"/>
            </AgentQuitFromReachingCommandQuota>

            <AgentQuitFromTouchingBlockType>
                <Block type="bedrock"/>
            </AgentQuitFromTouchingBlockType>
        </AgentHandlers>
    </AgentSection>
</Mission>
"""
    
    def init_malmo(self):
        """
        Initialize new malmo mission.
        """
        my_mission = MalmoPython.MissionSpec(self.get_mission_xml(), True)
        my_mission_record = MalmoPython.MissionRecordSpec()
        my_mission.requestVideo(800, 500)
        my_mission.setViewpoint(1)
        
        max_retries = 3
        my_clients = MalmoPython.ClientPool()
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000))  # add Minecraft machines here as available
        
        for retry in range(max_retries):
            try:
                self.agent_host.startMission(my_mission, my_clients, my_mission_record, 0, 'DiamondCollector')
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Error starting mission:", e)
                    exit(1)
                else:
                    time.sleep(2)
        
        world_state = self.agent_host.getWorldState()
        while not world_state.has_mission_begun:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            for error in world_state.errors:
                print("\nError:", error.text)
        
        return world_state
    
    def get_observation(self, world_state):
        """
        Use the agent observation API to get a flattened 2 x 5 x 5 grid around the agent.
        The agent is in the center square facing up.

        Args
            world_state: <object> current agent world state

        Returns
            observation: <np.array> the state observation
            allow_break_action: <bool> whether the agent is facing a diamond
        """
        obs = np.zeros((2 * self.obs_size * self.obs_size,))
        allow_break_action = False
        
        while world_state.is_mission_running:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')
            
            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                
                # todo
                
                # Get observation
                grid = observations['floorAll']
                for i, x in enumerate(grid):
                    obs[i] = x == 'diamond_ore' or x == 'lava'
                
                # Rotate observation with orientation of agent
                obs = obs.reshape((2, self.obs_size, self.obs_size))
                yaw = observations['Yaw']
                if yaw >= 225 and yaw < 315:
                    obs = np.rot90(obs, k=1, axes=(1, 2))
                elif yaw >= 315 or yaw < 45:
                    obs = np.rot90(obs, k=2, axes=(1, 2))
                elif yaw >= 45 and yaw < 135:
                    obs = np.rot90(obs, k=3, axes=(1, 2))
                obs = obs.flatten()
                
                allow_break_action = observations['LineOfSight']['type'] == 'diamond_ore'
                
                break
        
        return obs, allow_break_action
    
    def log_returns(self):
        """
        Log the current returns as a graph and text file

        Args:
            steps (list): list of global steps after each episode
            returns (list): list of total return of each episode
        """
        box = np.ones(self.log_frequency) / self.log_frequency
        returns_smooth = np.convolve(self.returns[1:], box, mode='same')
        plt.clf()
        plt.plot(self.steps[1:], returns_smooth)
        plt.title('Diamond Collector')
        plt.ylabel('Return')
        plt.xlabel('Steps')
        plt.savefig('returns.png')
        
        with open('returns.txt', 'w') as f:
            for step, value in zip(self.steps[1:], self.returns[1:]):
                f.write("{}\t{}\n".format(step, value))


if __name__ == '__main__':
    ray.init()
    trainer = ppo.PPOTrainer(env=DiamondCollector, config={
        'env_config': {},  # No environment parameters to configure
        'framework': 'torch',  # Use pyotrch instead of tensorflow
        'num_gpus': 0,  # We aren't using GPUs
        'num_workers': 0  # We aren't using parallelism
    })
    
    while True:
        print(trainer.train())
