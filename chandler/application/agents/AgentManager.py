__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item

from Agent import Agent
import AgentControl
import application.Globals as Globals

"""
The AgentManager Class is responsible for loading agents from the repository and launching them at
start-up.  It maintains a directory of agents and allows callers to manipulate them
"""
def findAgentManager(repository):
    am = repository.find('//Data/AgentManager')
    if am:
        return am

    data = repository.find('//Data')
    if not data:
        data = Item('Data', repository, None)

    # make new agent manager
    KIND_PATH = '//Parcels/OSAF/AppSchema/AgentSchema/AgentManager'
    kind = repository.find(KIND_PATH)
    am = kind.newItem('AgentManager', data)

    return am

class AgentManager:
    
    def __init__(self):
        """
           initialize data structures then load the agents
        """
        self.notificationManager = Globals.notificationManager

        self.agentMap = {}
        self.activeAgents = {}
        self.notificationHandledStatus = {}
        self.model = None

    def Startup(self):
        if not self.model:
            self.model = findAgentManager(Globals.repository)

        self._BuildMap()
        self.StartAll()

    def Shutdown(self):
        self.StopAll()

    def _BuildMap(self):
        for item in self.model.items:
            agentID = item.getUUID()
            if not self.agentMap.has_key(agentID):
                self.agentMap[agentID] = Agent(agentID)

    def IsRegistered(self, agentItem):
        try:
            return agentItem in self.model.items
        except:
            return False

    def Register(self, agentItem):
        """ register an agent with the agent manager """        
        if self.IsRegistered(agentItem):
            return

        repository = agentItem.getRepository()

        if not self.model:
            self.model = findAgentManager(repository)

        self.model.addValue('items', agentItem)
        repository.commit()

        agentID = agentItem.getUUID()
        self.agentMap[agentID] = Agent(agentID)

    def Unregister(self, agentItem):
        """ unregister an agent from the agent manager """
        if not self.IsRegistered(agentItem):
            raise KeyError, 'Agent Not Registered'

        self.model.removeValue('items', agentItem)
        agentItem.getRepository().commit()

        agentID = agentItem.getUUID()
        del self.agentMap[agentID]

    def AgentMatches(self, agent, name, role, owner):
        """ 
          return True if the passed-in agent matches the passed-in criteria
          FIXME: this isn't implemented yet
        """
        return True
    
    def LookUpAgents(self, name, role, owner):
        """
          return a list of agents that meet the passed-in criteria.  If a parameter is None,
          it's ignored.  Wildcards will be supported eventually, but not yet
        """
        resultAgents = []
        registeredAgents = self.agentMap.values()
        for agent in registeredAgents:
            if self.AgentMatches(name, role, owner):
                resultAgents.append(agent)
                
        return resultAgents
    
    def GetAgentFromItem(self, agentID):
        if not self.agentMap.has_key(agentID):
            raise KeyError, 'Agent Not Registered'
        return self.agentMap[agentID]

    def Start(self, agentID):
        if not self.IsRegistered(agentID):
            raise KeyError, 'Agent Not Registered'

        # register with the notification manager and subscribe to notifications
        if not self.notificationManager.IsRegistered(agentID):
            self.notificationManager.Register(agentID)

        # subscribe to notifications
        agentItem = Globals.repository.find(agentID)
        agentItem.SubscribeToNotifications(self.notificationManager)

        # hook up the widget
        #widget = AgentControl.wxAgentControl(agentID)
        #widget.AddToToolBar()

        self.agentMap[agentID].Resume()

    def StartAll(self):
        for agentID in self.agentMap.keys():
            self.Start(agentID)

    def Stop(self, agentID):
        """ Suspends the agent """
        if not self.IsRegistered(agentID):
            raise KeyError, 'Agent Not Registered'
        self.agentMap[agentID].Suspend()

        # unsubscribe to notifications
        agentItem = Globals.repository.find(agentID)
        agentItem.UnsubscribeFromNotifications(self.notificationManager)

    def StopAll(self):
        """ Stops all the Agents """
        for agentID in self.agentMap.keys():
            self.Stop(agentID)        

    # the following routines maintain the 'handled' state associated with a notification
    # we will probably have a more elaborate model for coordinating actions between agents
    # soon, but this simple scheme suffices for the original implementation
    
    def GetHandledStatus(self, notification):
        id = notification.GetID()
        if self.notificationHandledStatus.has_key(id):
            return self.notificationHandledStatus[id]
        return False
    
    def SetHandledStatus(self, notification, newStatus):
        self.notificationHandledStatus[notification.GetID()] = newStatus

    def DeleteHandledStatus(self, notification):
        id = notification.GetID()
        if self.notificationHandledStatus.has_key(id):
            del self.notificationHandledStatus[id]
