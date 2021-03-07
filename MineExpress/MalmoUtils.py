import sys, time
import xml.etree.ElementTree as et

try:
    from malmo import MalmoPython
except:
    import MalmoPython

et.register_namespace("", 'http://ProjectMalmo.microsoft.com')
namespace = {'d': 'http://ProjectMalmo.microsoft.com'}


class MissionHandler:
    
    def __init__(self, fileName: str):
        self.missionTree = et.parse(fileName)
        self.missionTreeRoot = self.missionTree.getroot()
    
    def __str__(self):
        return et.tostring(self.missionTreeRoot, encoding='unicode', method="xml")
    
    def getNode(self, tag):
        node = self.missionTreeRoot.find(f".//d:{tag}", namespace)
        assert node is not None, \
            "Tag Does Not Exist, Check The Tag Parameter Or The Identifier In The XML"
        return node
    
    def set(self, tag, replaceTag=None, **attrib):
        node = self.getNode(tag)
        if replaceTag is not None:
            node.tag = replaceTag
        for key, value in attrib.items():
            node.set(key, value)
    
    def insert(self, tag, newTag, **attrib):
        node = self.getNode(tag)
        node.append(et.Element(newTag, attrib))
    
    def write(self, fileName):
        self.missionTree.write(fileName, encoding='UTF-8', xml_declaration=True)


class MalmoInitializer:
    def __init__(self):
        self.agentHost = MalmoPython.AgentHost()
        try:
            self.agentHost.parse(sys.argv)
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agentHost.getUsage())
            exit(1)
    
    def initMalmo(self, missionXML, missionName):
        
        my_mission = MalmoPython.MissionSpec(missionXML, True)
        my_mission.requestVideo(800, 500)
        my_mission.setViewpoint(1)
        my_mission_record = MalmoPython.MissionRecordSpec()
        
        max_retries = 3
        my_clients = MalmoPython.ClientPool()
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000))  # add Minecraft machines here as available
        
        for retry in range(max_retries):
            try:
                self.agentHost.startMission(my_mission, my_clients, my_mission_record, 0, missionName)
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Error starting mission:", e)
                    exit(1)
                else:
                    time.sleep(2)
        
        world_state = self.agentHost.getWorldState()
        while not world_state.has_mission_begun:
            time.sleep(0.1)
            world_state = self.agentHost.getWorldState()
            for error in world_state.errors:
                print("\nError:", error.text)
        
        return world_state
    
    def getWorldState(self):
        world_state = self.agentHost.getWorldState()
        for error in world_state.errors:
            print("Error:", error.text)
        return world_state
    
    def sendCommand(self, command: str, times=1):
        for i in range(0, times):
            self.agentHost.sendCommand(command)
            time.sleep(0.1)
