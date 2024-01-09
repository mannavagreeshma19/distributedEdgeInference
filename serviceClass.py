class service:

    #nodes is a list of all nodes running this network. 
    def __init__(self,  netName, startLayer, endLayer, listenPort, nextIP, nextPort, node, child=None, load=None):
        self.netName = netName
        self.startLayer = startLayer
        self.endLayer = endLayer
        self.listenPort = listenPort
        self.nextIP = nextIP
        self.nextPort = nextPort
        self.child = child
        self.node = node
        self.load=load

    def terminateServiceChain(self):
        self.node.endService(self) #sends message to node to shut me down. 
        if(self.child!=None):
            self.child.terminateServiceChain() #have children do the same
    
    def updateLoad(self, load):
        self.load=load
    
    def getVals(self):
        return self.netName, self.startLayer, self.endLayer, self.listenPort, self.nextIP, self.nextPort
    
    def getName(self):
        return self.netName
    
    def getPort(self):
        return self.listenPort
    
    def getNode(self):
        return self.node
    
    def getIP(self):
        return self.node.ip
    