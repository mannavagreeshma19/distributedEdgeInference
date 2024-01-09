import json
import socket
import time


class Node:

    #class variable that tracks all created nodes (alive and dead).
    nodeList=[]

    #class variable that tracks running networks. Contains Entry point only. 
    netList=[]

    @classmethod
    def findByIp(cls, ip):
        for node in cls.nodeList:
            if node.ip == ip:
                return node
        return False
    
    @classmethod
    def isRunning(cls, netName):
        print(f"Searching for {netName}\n")
        for i in cls.netList:
            print(i.getName())
            if i.getName()==netName:
                return (i.getIP(),i.getPort())
        return False
    
    @classmethod
    def usable(cls, timeToDeath, ramRequirement):
        '''returns only nodes that are alive and meet some ram requirement'''
        # Filter nodes based on RAM requirement
        filtered_nodes = [node for node in cls.nodeList if node.canFit(ramRequirement) and node.alive(timeToDeath)]

        # Sort the filtered nodes by available CPU power
        sorted_nodes = sorted(filtered_nodes, key=lambda node: node.cpu * (1 - node.cpuUtilization / 100), reverse=True)

        return sorted_nodes
    
    @classmethod
    def nodeStats(cls):
        '''returns all alive nodes and how much ram/ compute they have available. Use to schedule.'''
        living_nodes = []
        for node in cls.nodeList:
            # Calculate available RAM
            available_ram = node.ram * (1 - node.ramUtilization / 100)
            living_nodes.append((node, available_ram))
        return living_nodes
    
    def __init__(self, ip, port=1026, cpu=100, ram=8, cpuUtilization=0, ramUtilization=0, nets=[], portList=[]):

        self.ip=ip
        self.port=port

        self.cpu=cpu#in Gflops
        self.ram=ram#in GB
        self.cpuUtilization=cpuUtilization#0-100
        self.ramUtilization=ramUtilization#0-100
        
        self.nets=[]
        self.portList=portList#[list of used ports] Note:only use ports>=1050

        self.lastUpdated=time.time()#time since this node has checked in.

        Node.nodeList.append(self)

    def update(self, cpuUtilization=0, ramUtilization=0, nets=[], portList=[]):
        self.cpuUtilization=cpuUtilization
        self.ramUtilization=ramUtilization
        
        self.portList=portList #Could also cause collision w other programs if updates are too slow. 
                              

        self.lastUpdated=time.time()

        '''if nets does not contain an expected network then an error has occured in that network. Handle this in the future. '''

    def getLastUpdated(self):
        return self.lastUpdated
    
    def getAvailablePort(self):
        # Convert self.portList to a set for faster lookup
        portSet = set(self.portList)
        # Add ports used by services in self.nets to the set
        for service in self.nets:
            portSet.add(service.getPort())
        # Iterate over the range and check for availability
        for i in range(1050, 65635):  # 65635 is exclusive
            if i not in portSet:
                return i
        # Return False if no available port is found
        return False
    
    def getNets(self):
        return self.nets
    
    def getPortList(self):
        return self.portList
    
    def canFit(self, required):
        return (self.ram*(1-self.ramUtilization/100))>=required

    def startService(self, network):
        netName, startLayer, endLayer, listenPort, nextIP, nextPort=network.getVals()
        source = "master"
        task = "bringup"
        message = f"{netName} {startLayer} {endLayer} {listenPort} {nextIP} {nextPort}"
        data = {
            'source': source,
            'task': task,
            'netName': netName,
            'listenPort': listenPort,
            'startLayer': startLayer,
            'message': message
                }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.ip, self.port))
                sock.sendall(json.dumps(data).encode('utf-8'))
                print(f"Sent to {self.ip}:{self.port} - Task: {task}, Message: {message}")
            except ConnectionRefusedError:
                print(f"Connection to {self.ip}:{self.port} refused. Make sure the server is running.")
                return False
            except Exception as e:
                print(f"An error occurred: {e}")
                return False

        # Updating the Node.netList for network-wide tracking
        if startLayer == 0:
            new_entry = network
            if new_entry not in Node.netList:
                Node.netList.append(new_entry)

        # Updating self.nets to track networks on this node
        new_net = network
        if new_net not in self.nets:
            self.nets.append(new_net)

        # Updating self.portList to track used ports on this node
        if listenPort not in self.portList:
            self.portList.append(listenPort)

        return True


    #Broken function
    def endService(self, network):
        netName, startLayer, endLayer, listenPort, nextIP, nextPort=network.getVals()
        source="master"
        task="shutdown"
        data = {
        'source':source,
        'task': task,
        'netName': netName,
        'listenPort': listenPort,

                }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.ip, self.port))
                sock.sendall(json.dumps(data).encode('utf-8'))
                print(f"Sent to {self.ip}:{self.port} - Task: {task}")
            except ConnectionRefusedError:
                print(f"Connection to {self.ip}:{self.port} refused. Make sure the server is running.")
                return False
            except Exception as e:
                print(f"An error occurred: {e}")
                return False
        # Updating the Node.netList for network-wide tracking
        if startLayer == 0:
            entry_to_remove = network
            if entry_to_remove in Node.netList:
                Node.netList.remove(entry_to_remove)

        # Updating self.nets to remove the network from this node
        net_to_remove = network
        if net_to_remove in self.nets:
            self.nets.remove(net_to_remove)

        # Updating self.portList to free up the port
        if listenPort in self.portList:
            self.portList.remove(listenPort)

        return True
    
    def nodeReset(self):
        task="reset"
        data={
            'task':task
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.ip, self.port))
                sock.sendall(json.dumps(data).encode('utf-8'))
                print(f"Sent to {self.ip}:{self.port} - Task: {task}!")
            except ConnectionRefusedError:
                print(f"Connection to {self.ip}:{self.port} refused. Make sure the server is running.")
                return False
            except Exception as e:
                print(f"An error occurred: {e}")
                return False
        Node.nodeList=list(set(Node.nodeList).discard(self))
        return True

    def __str__(self):
        output = f"Node IP: {self.ip}, Port: {self.port}\n"
        return output


def alive(self, secondsToDead):
    return time.time()-self.lastUpdated< secondsToDead

