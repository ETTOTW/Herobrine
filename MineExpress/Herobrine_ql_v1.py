try:
    from malmo import MalmoPython
except:
    import MalmoPython

import os
import sys
import time
import json
import random
import numpy as np
import csv

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

def create_mission(ind,agent_host):
    my_mission = MalmoPython.MissionSpec(GetMissionXML(), True)
    my_mission_record = MalmoPython.MissionRecordSpec()
    my_mission.requestVideo(800, 500)
    my_mission.setViewpoint(1)
    # Attempt to start a mission:
    max_retries = 3
    my_clients = MalmoPython.ClientPool()
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available
    for i in range(len(legalPosList)):
        if i == itemPosId:
            my_mission.drawBlock(legalPosList[itemPosId][0],1,legalPosList[itemPosId][1],"emerald_block")
        elif i == destPosId:
            my_mission.drawBlock(legalPosList[destPosId][0],1,legalPosList[destPosId][1],"diamond_block")
        else:
            my_mission.drawBlock(legalPosList[i][0],1,legalPosList[i][1],"stone")
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
    return my_mission

def GetMissionXML(size=2):
    '''
    original map without gap
    
    '''
    blockPosXML = ""
    for x in range(-size, size+1):
        for z in range(-size, size+1):
            blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='soul_sand' />".format(x,z)
            blockPosXML += "<DrawBlock x='{}'  y='1' z='{}' type='grass' />".format(x,z)
    
    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

              <About>
                <Summary>Herobrine Project</Summary>
              </About>

            <ServerSection>
              <ServerInitialConditions>
                <Time>
                    <StartTime>3000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <Weather>clear</Weather>
              </ServerInitialConditions>
              <ServerHandlers>
                  <FlatWorldGenerator generatorString="3;2*9,3*0;1;"/>
                  <DrawingDecorator>''' + \
                      "<DrawCuboid x1='{}' x2='{}' y1='2' y2='4' z1='{}' z2='{}' type='air'/>".format(-size, size, -size, size) + \
                      blockPosXML + \
                      '''<DrawBlock x='1' y='1' z='-1' type='water'/>
                      <DrawBlock x='0' y='1' z='0' type='soul_sand'/>
                  </DrawingDecorator>
                  <ServerQuitWhenAnyAgentFinishes/>
                  <ServerQuitFromTimeUp timeLimitMs="1000000"/>
                </ServerHandlers>
              </ServerSection>

              <AgentSection mode="Survival">
                <Name>Agent</Name>
                <AgentStart>
                    <Placement x='0.5' y='2' z='0.5' pitch="45" yaw='0'/>
                    <Inventory>
                        <InventoryItem slot="9" type="cookie" quantity="1"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                    <DiscreteMovementCommands/>
                    <InventoryCommands/>
                    <ChatCommands/>
                    <ObservationFromFullStats/>
                    <ObservationFromGrid>
                        <Grid name="floor">
                            <min x="0" y="-1" z="0"/>
                            <max x="0" y="1" z="0"/>
                        </Grid>
                    </ObservationFromGrid>
                    <RewardForTouchingBlockType>
                        <Block type = "grass" reward="-1" behaviour="oncePerTimeSpan"/>
                        <Block type = "soul_sand" reward="-1" behaviour="oncePerTimeSpan"/>
                        <Block type = "stone" reward="-1" behaviour="oncePerTimeSpan"/>
                        <Block type = "diamond_block" reward="-1" behaviour="oncePerTimeSpan"/>
                        <Block type = "emerald_block" reward="-1" behaviour="oncePerTimeSpan"/>
                        <Block type = "water" reward="-10"  behaviour="onceOnly"/> 
                    </RewardForTouchingBlockType>
                    <RewardForSendingMatchingChatMessage>
                        <ChatMatch reward="20" regex="legal pick up" description="matches the object."/>
                        <ChatMatch reward="20" regex="legal drop off" description="matches the object."/>
                        <ChatMatch reward="-10" regex="cannot drop off here" description="matches the object."/>
                        <ChatMatch reward="-10" regex="cannot pick up here" description="matches the object."/>
                    </RewardForSendingMatchingChatMessage>
                    <AgentQuitFromReachingCommandQuota>
                        <Quota commands = "jump" quota = "2"/> 
                    </AgentQuitFromReachingCommandQuota>
                    <AgentQuitFromTouchingBlockType>
                        <Block type = "water"/>
                    </AgentQuitFromTouchingBlockType>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''
 
    
class MineExpressBaseline():
    def __init__(self, itemPosId=0, destPosId=1, legalPos=4, training=True):  
        self.legalPos = legalPos
        self.itemPosId = itemPosId
        self.destPosId = destPosId
        assert(itemPosId<legalPos-1 and destPosId<(legalPos-1) and itemPosId!=destPosId)
        
        self.max_epsilon = 0.9
        self.min_epsilon = 0.1
        self.decay = 0.01
        self.epsilon = self.max_epsilon
        self.alpha = 0.1
        self.gamma = 0.6
        self.q_table = {} 
        
        # in the format "{x}:{z}:{packageInd}:{dropOffInd}"
        
        self.prev_s = None
        self.prev_a= None
        self.actions = {
            0: 'movesouth 1',
            1: 'movenorth 1',
            2: 'moveeast 1',
            3: 'movewest 1',
            4: 'pickup', # pickup
            5: 'dropoff' # drop off
            
        }
        self.itemPosIds = [p for p in range(-1,legalPos)]
        self.destPosIds = [p for p in range(legalPos)]
        self.block_dict = {
            "base": 'grass',
            "slower": 'soul_sand', 
            "pickup": 'emerald_block',
            "dropoff": 'diamond_block'
        }
        self.debug = True 
        self.training = training
        if self.training == False:
            self.epsilon = 0
        self.nCommand = 0 # number of actions executed so far
        
    def start_new_mission(self,itemPosId):
        self.itemPosId = itemPosId
        self.prev_s = None
        self.prev_a = None
        self.nCommand = 0
        
    def write_to_csv(self):
        w = csv.writer(open("q_table.csv","w"))
        for key,val in self.q_table.items():
            w.writerow([key]+val)
        #w.close()
    
    def read_from_csv(self, file = "q_table.csv"):
        self.q_table = dict()
        with open(file) as ifile:
            csv_reader = csv.reader(ifile)
            for row in csv_reader:
                if len(row)!=0:
                    self.q_table[row[0]] = [float(i) for i in row[1:]]
    
    def print_q_table(self):
        print("**q_table**")
        for state,action in self.q_table.items():
            print("state: ", state, " ", action)
        print()    
            
    def get_pos(self, world_state):
        '''
        return 
            current x and z position
            block type below the agent
        '''
        if world_state.number_of_observations_since_last_state > 0:
            obs = json.loads( world_state.observations[-1].text )
            pos_x = obs[u'XPos']-0.5
            pos_z = obs[u'ZPos']-0.5
            floor = np.array(obs[u'floor'])
            floor = floor[ np.all([floor!="air",floor!="water"],axis = 0) ][0]
            #slot0 = obs[u'InventorySlot_0_size']
            #slot9 = obs[u'InventorySlot_9_size']
            """
            if self.debug:
                pos_y = obs[u'YPos']
                print("current position")
                print("pos_x, pos_z, pos_y: ", pos_x, pos_z, pos_y)
                print("block bellow: ", floor)
                #print("slot0, slot9:", slot0, slot9)
                print()
            """
            return pos_x, pos_z, floor
        else:
            return None,None,None
    
    
    def get_state(self, pos_x, pos_z):
        state = "%d:%d:%d:%d" % (pos_x,pos_z,self.itemPosId,self.destPosId)
        if state not in self.q_table:
            self.q_table[state] = ([0]*len(self.actions))
        return state
        
    def update_e(self):
        self.epsilon = self.epsilon-self.decay if (self.epsilon > self.min_epsilon) else self.epsilon
        
    def update_q_table(self, curr_r, curr_s):
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q = self.q_table[self.prev_s][self.prev_a]
            
            if self.debug:
                print("***update_q_table****")
                print("prev_a= ", self.prev_a)
                print("old_q " , self.prev_s, " = ", self.q_table[self.prev_s])
                
            self.q_table[self.prev_s][self.prev_a] = old_q + self.alpha * (curr_r
                + self.gamma*max(self.q_table[curr_s]) - old_q)
            
            if self.debug:
                print("new_q=" , self.q_table[self.prev_s])

    
    def choose_step(self, curr_s):
        r = random.random()
        if  r < self.epsilon:
            a = random.randint(0, len(self.actions) - 1)
        else:
            q = np.array(self.q_table[curr_s])
            a = random.choice(np.argwhere(q == max(q)))[0]
        if self.debug:
            print("***choose_step****")
            if r < self.epsilon:
                print("random step=",a)
            else:
                print("q=", self.q_table[curr_s])
                print("best step=",a)
        return a
             
             
    def act(self, world_state,agent_host,curr_r):
        self.nCommand+=1
        if self.debug:
            print()
            print("----------------------")
            print("command ",self.nCommand,":")
            print("----------------------")
            
        curr_x, curr_z, curr_block = self.get_pos(world_state)
        curr_s = self.get_state(curr_x,curr_z)
        
        if self.debug:
            print("position(before)= (%d,%d), %s, %d" %(curr_x,curr_z,curr_block,self.itemPosId))
            
        self.update_q_table(curr_r,curr_s)
        action = self.choose_step(curr_s)
        if self.debug:
            print("action= ", self.actions[action])
        if action == 4:
            if curr_block == self.block_dict["pickup"] and self.itemPosId != -1:
                self.itemPosId = -1
                agent_host.sendCommand("chat " + "legal pick up")
                agent_host.sendCommand("swapInventoryItems 0 9")
                agent_host.sendCommand("jump 1")
            else:
                agent_host.sendCommand("chat " + "cannot pick up here")
        elif action == 5:
            if curr_block == self.block_dict["dropoff"] and self.itemPosId == -1:
                agent_host.sendCommand("chat " + "legal drop off")
                agent_host.sendCommand("swapInventoryItems 0 9")
                time.sleep(0.2) # current mission end, avoid losing final reward
                agent_host.sendCommand("jump 1")
            else:
                agent_host.sendCommand("chat " + "cannot drop off here")
        else:
            agent_host.sendCommand(self.actions[action])
        time.sleep(0.2)
        
        self.prev_s = curr_s
        self.prev_a = action
        return curr_r
        
    def checkAction(self,world_state,agent_host,prev_x,prev_z):
        res = 1
        print("**checkAction**")
        while world_state.is_mission_running:
            world_state = agent_host.peekWorldState()
            curr_x, curr_z, curr_block = self.get_pos(world_state)
            if self.prev_a == 4 or self.prev_a == 5:
                print("action:", self.prev_a, "; pre x and z:", prev_x, prev_z, "; curr x and z:", curr_x, curr_z)
                return 
            elif self.prev_a == 0 and prev_z+1 == curr_z and prev_x == curr_x:
                print("action:", self.prev_a, "; pre x and z:", prev_x, prev_z, "; curr x and z:", curr_x, curr_z)
                return
            elif self.prev_a == 1 and prev_z-1 == curr_z and prev_x == curr_x:
                print("action:", self.prev_a, "; pre x and z:", prev_x, prev_z, "; curr x and z:", curr_x, curr_z)
                return  
            elif self.prev_a == 2 and prev_z == curr_z and prev_x+1 == curr_x:
                print("action:", self.prev_a, "; pre x and z:", prev_x, prev_z, "; curr x and z:", curr_x, curr_z)
                return
            elif self.prev_a == 3 and prev_z == curr_z and prev_x-1 == curr_x:
                print("action:", self.prev_a, "; pre x and z:", prev_x, prev_z, "; curr x and z:", curr_x, curr_z)
                return
            res+=1
            if res >= 100000:
                print("action cannot be executed")
                agent_host.sendCommand("jump 1")
                agent_host.sendCommand("jump 1")
    
    def run(self, agent_host):
        # wait for a valid observation
        world_state = agent_host.peekWorldState()
        while world_state.is_mission_running and all(e.text=='{}' for e in world_state.observations):
            world_state = agent_host.peekWorldState()
        world_state = agent_host.getWorldState()
        for err in world_state.errors:
            print(err)
        
        total_reward = 0
        curr_r = 0

        prev_x, prev_z, prev_block = self.get_pos(world_state)
        if self.debug:
            print("Initial position: %d, %d, %s" %(prev_x,prev_z,prev_block))
        total_reward += self.act(world_state,agent_host,curr_r)
        
        
        while world_state.is_mission_running:
            world_state = agent_host.peekWorldState()
            while world_state.is_mission_running and all(e.text=='{}' for e in world_state.observations):
                world_state = agent_host.peekWorldState()
            '''
            while world_state.is_mission_running and sum(r.getValue() for r in world_state.rewards) == 0:
                world_state = agent_host.peekWorldState()
                res+=1
                if 990000 < res and res < 1000000:
                    print("error finding rewards")
                    agent_host.sendCommand("jump 1")
                    agent_host.sendCommand("jump 1")
            '''
            self.checkAction(world_state, agent_host, prev_x, prev_z)
            world_state = agent_host.getWorldState()
            for err in world_state.errors:
                print(err)
            
            print('epsilon:',self.epsilon)
            curr_x, curr_z, curr_block = self.get_pos(world_state)
            curr_r = sum(r.getValue() for r in world_state.rewards)
            if self.debug:
                print("position(after)= (%d,%d), %s, %d" %(curr_x,curr_z,curr_block,self.itemPosId))
                print("reward= ",curr_r)
            prev_x = curr_x
            prev_z = curr_z
            self.print_q_table()
            if not world_state.is_mission_running:
                break
            #input("press to continue:")
            agent.update_e()
            total_reward += self.act(world_state, agent_host, curr_r)
            if self.nCommand == 3:
                self.write_to_csv()
        total_reward += curr_r
        if self.prev_s is not None and self.prev_a is not None:
            old_q = self.q_table[self.prev_s][self.prev_a]
            self.q_table[self.prev_s][self.prev_a] = old_q + self.alpha * ( curr_r - old_q )

        return total_reward
    

# Create default Malmo objects:
agent_host = create_malmo_obj()
agent_host.setRewardsPolicy(MalmoPython.RewardsPolicy.LATEST_REWARD_ONLY)
num_repeats = 10000
cumulative_rewards = []
reward=0

legalPosList = [[2,-1],[-2,-2],[2,2],[-2,2]]
itemPosId=0
destPosId=1
legalPos=4

agent = MineExpressBaseline(itemPosId, destPosId, legalPos)
# agent.read_from_csv("5x5map_after 142mission_trained.csv")

# constant pickup and dropoff position for now
for i in range(num_repeats):
    my_mission = create_mission(i,agent_host)
    agent.start_new_mission(itemPosId)
    print("Mission", (i+1), "running.")
    
    cumulative_reward = agent.run(agent_host)
    print('Cumulative reward: %d' % cumulative_reward)
    cumulative_rewards += [ cumulative_reward ]
    
    print("Mission", (i+1), "ended")
    print()
    time.sleep(1)
    # Mission has ended.