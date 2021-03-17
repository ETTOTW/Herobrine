try:
    from malmo import MalmoPython
except:
    import MalmoPython
    
import os
import sys
import json
import random
import time
import numpy as np 
import matplotlib.pyplot as plt
from priority_dict import priorityDictionary as PQ
import HerobrineMalmoUtils as MalmoUtils

np.random.seed(0)

def create_malmo_obj():
    agent_host = MalmoPython.AgentHost()
    try:
        agent_host.parse( sys.argv )
    except RuntimeError as e:
        print('ERROR:',e)
        print(agent_host.getUsage())
        exit(1)
    if agent_host.receivedArgument("help"):
        print(agent_host.getUsage())
        exit(0)
    return agent_host

def create_mission(ind,agent_host,start, dropoff, pickup):
    my_mission = MalmoPython.MissionSpec(GetMissionXML(start), True)
    my_mission_record = MalmoPython.MissionRecordSpec()
    my_mission.requestVideo(800, 500)
    my_mission.setViewpoint(1)
    # Attempt to start a mission:
    max_retries = 3
    my_clients = MalmoPython.ClientPool()
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

    my_mission.drawBlock(int(pickup[0]), 1, int(pickup[1]), "redstone_block")
    my_mission.drawBlock(int(dropoff[0]), 1, int(dropoff[1]), "diamond_block")
        
    for retry in range(max_retries):
        try:
            agent_host.startMission( my_mission, my_clients, my_mission_record, 0, "%s-%d" % ('Herobrine', ind) )
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print("Error starting mission", ":",e)
                exit(1)
            else:
                time.sleep(2)

    world_state = agent_host.peekWorldState()
    while not world_state.has_mission_begun:
        time.sleep(0.1)
        world_state = agent_host.peekWorldState()
        for error in world_state.errors:
            print("Error:",error.text)
    time.sleep(1)
    return my_mission, world_state


def GetMissionXML(start):
    blockPosXML = ""
    xs = [i for i in range(0,9)]
    zs = [i for i in range(0,9)]
    for x in xs:
        for z in zs:
            if x%2 == 0 or z%2==0:
                blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='stone' />".format(x,z)
            if x%2 == 0 and z%2==0:
                 blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='emerald_block' />".format(x,z)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='soul_sand' />".format(0,1)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='soul_sand' />".format(3,4)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='soul_sand' />".format(5,4)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='grass' />".format(3,0)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='grass' />".format(3,2)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='grass' />".format(5,8)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='grass' />".format(5,6)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='grass' />".format(7,0)
    blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='grass' />".format(7,3)
        
    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            
                <About>
                    <Summary>Mine Express</Summary>
                </About>
                  
                <ServerSection>
                     <ServerInitialConditions>
                         <Time>
                             <StartTime>3000</StartTime>
                             <AllowPassageOfTime>false</AllowPassageOfTime>
                        </Time>
                        <AllowSpawning>false</AllowSpawning>
                        <Weather>clear</Weather>
                    </ServerInitialConditions>
                    <ServerHandlers>
                        <FlatWorldGenerator generatorString="3;2*2;1;village"/>
                        <DrawingDecorator>''' + \
                            "<DrawCuboid x1='{}' x2='{}' y1='2' y2='3' z1='{}' z2='{}' type='air'/>".format(-20, 20, -20, 20) + \
                            blockPosXML + \
                            '''
                        </DrawingDecorator>
                        <ServerQuitWhenAnyAgentFinishes/>
                    </ServerHandlers>
                </ServerSection>
                  
                <AgentSection mode="Survival">
                    <Name>Courier HeroBrine</Name>
                    <AgentStart>''' + \
                        "<Placement x='{}' y='2' z='{}' pitch='45' yaw='0'/>".format(start[0]+0.5,start[1]+0.5) + \
                    '''
                    </AgentStart>
                    <AgentHandlers>
                        <DiscreteMovementCommands/>
                        <InventoryCommands/>
                        <ObservationFromFullStats/>
                        <ObservationFromGrid>
                            <Grid name="floorAll"> 
                                <min x='-40' y='-1' z='-40'/>
                                <max x='40' y='-1' z='40'/>
                            </Grid>
                        </ObservationFromGrid>
                        <AgentQuitFromReachingCommandQuota>
                            <Quota commands = "use" quota = "1"/> 
                        </AgentQuitFromReachingCommandQuota>
                    </AgentHandlers>
                </AgentSection>
            </Mission>'''

class MineExpressDijkstra():
    def __init__(self):
        self.mission = MalmoUtils.MalmoInitializer()
        self.position = [i for i in range(0,9,2)]
        self.grid = []
        self.action_dict = {
            0: 'movenorth 1',
            1: 'movesouth 1',
            2: 'moveeast 1',
            3: 'movewest 1'
        }
        self.block_dict = {
            "pickup": 'redstone_block',
            "dropoff": 'diamond_block',
            "slower": 'soul_sand', 
            "pos": 'emerald_block',
        }
        self.start_grid, self.pickup_grid, self.dropoff_grid = None,None,None
        self.absolute_position = \
            [[(0, 0), (2, 0), (4, 0), (6, 0), (8, 0)],
             [(0, 2), (2, 2), (4, 2), (6, 2), (8, 2)],
             [(0, 4), (2, 4), (4, 4), (6, 4), (8, 4)],
             [(0, 6), (2, 6), (4, 6), (6, 6), (8, 6)],
             [(0, 8), (2, 8), (4, 8), (6, 8), (8, 8)]]
        
    def start_new_mission(self):
        self.agent_loc = np.random.randint(0, 5, 2)
        self.agent_loc = self.absolute_position[self.agent_loc[0]][self.agent_loc[1]]
        self.package_loc = np.random.randint(0, 4)
        self.package_dest = np.random.randint(0, 4)
        while self.package_dest == self.package_loc:
            self.package_dest = np.random.randint(0, 4)
        self.package_loc = box_locations[self.package_loc]
        self.package_dest = box_locations[self.package_dest]
        return self.agent_loc, self.package_loc, self.package_dest
    
    def find_dest(self):
        for i in range(len(self.grid)):
            if self.grid[i] == 'redstone_block':
                self.pickup_grid = i
            if self.grid[i] == 'diamond_block':
                self.dropoff_grid = i
        
        
    def dijkstra_shortest_path(self, start, end):
        pre_grids = PQ()
        grid_dist = PQ()
        grid_dist[start] = 0
        pre_grids[start] = -1
        while grid_dist:
            cur = grid_dist.smallest()
            for g in [-81,81,-1,1]:
                g+=cur
                if 0>g or g>=len(self.grid):
                    continue
                if g in pre_grids:
                    continue
                if self.grid[g] == "grass":
                    continue
                if self.grid[g] == "soul_sand":
                    if g not in grid_dist or grid_dist[g] > grid_dist[cur]+4:
                        grid_dist[g] = grid_dist[cur]+4
                        pre_grids[g] = cur
                elif self.grid[g] == "stone":
                    if g not in grid_dist or grid_dist[g] > grid_dist[cur]+1:
                        grid_dist[g] = grid_dist[cur]+1
                        pre_grids[g] = cur
                else:
                    if g not in grid_dist or grid_dist[g] > grid_dist[cur]:
                        grid_dist[g] = grid_dist[cur]
                        pre_grids[g] = cur
            del grid_dist[cur]
        result = []
        cur = end
        while pre_grids[cur] != -1:
            result.insert(0,cur)
            cur = pre_grids[cur]
        result.insert(0,start)
        return result
    
    def calc_reward(self, path_list):
        reward = 0
        for g in path_list:
            if self.grid[g] == "soul_sand":
                reward-=4
            if self.grid[g] == "stone":
                reward-=1
        print("reward from cal:", reward)
        return reward
    
    def extract_action_list_from_path(self, path_list):
        action_trans = {-81: 'movenorth 1', 81: 'movesouth 1', -1: 'movewest 1', 1: 'moveeast 1'}
        alist = []
        for i in range(len(path_list) - 1):
            curr_block, next_block = path_list[i:(i + 2)]
            alist.append(action_trans[next_block - curr_block])   
        return alist
    
    def run(self, world_state):
        while world_state.is_mission_running:
            #sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')
        
            if world_state.number_of_observations_since_last_state > 0:
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                self.grid = observations.get(u'floorAll', 0)
                break
        
        self.start_grid = int((len(self.grid)-1)/2)
        self.find_dest()
        print("Output (start,pickup,dropoff)", (i+1), ":", (self.start_grid, self.pickup_grid, self.dropoff_grid))
        path1 = self.dijkstra_shortest_path(self.start_grid, self.pickup_grid)
        path2 = self.dijkstra_shortest_path(self.pickup_grid, self.dropoff_grid)
        reward = self.calc_reward(path1)
        reward += self.calc_reward(path2)
        print("Output (path length1)", (i+1), ":", len(path1))
        print("Output (path length2)", (i+1), ":", len(path2))
        action_list1 = self.extract_action_list_from_path(path1)
        action_list2 = self.extract_action_list_from_path(path2)
        return action_list1,action_list2, reward

    def save_reward(self,rewards):
        with open('returns.txt', 'w') as f:
            for i in range(len(rewards)):
                f.write("{}\t{}\n".format(i+1, rewards[i])) 
                
        plt.clf()
        plt.plot(range(1,len(rewards)+1), rewards)
        plt.title('Dijkstra For Herobrine')
        plt.ylabel('Reward')
        plt.xlabel('num_repeats')
        plt.savefig('returns.png')

        
    
box_locations = [[0, 0], [0, 8], [8, 0], [6, 8]]
agent_host = create_malmo_obj()

itemPosId=0
destPosId=1
legalPos=4

agent = MineExpressDijkstra()
cumulative_rewards = []
num_repeats = 100
for i in range(num_repeats):
    reward=0
    start, pickup, dropoff = agent.start_new_mission()
    my_mission,world_state = create_mission(i,agent_host,start,pickup,dropoff)
    print("Mission", (i+1), "running.")
    
    action_list1,action_list2,reward = agent.run(world_state)
    
    time.sleep(0.1)
    '''
    for action_index in range(len(action_list1)):
        agent_host.sendCommand(action_list1[action_index])
        time.sleep(0.2)
    for action_index in range(len(action_list2)):
        agent_host.sendCommand(action_list2[action_index])
        time.sleep(0.2)
    '''
    agent_host.sendCommand("use 1")
    time.sleep(1)
    world_state = agent_host.getWorldState()
    while world_state.is_mission_running:
        world_state = agent_host.getWorldState()
    reward += 20
    print("reward:",reward)
    cumulative_rewards+=[reward]
    agent.save_reward(cumulative_rewards)
    print()
    
    print("Mission", (i+1), "ended")
    print()
    time.sleep(1)


