__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Agent import Agent
import AgentControl
import application.Application

"""
The AgentManager Class is responsible for loading agents from the repository and launching them at
start-up.  It maintains a directory of agents and allows callers to manipulate them
"""

class AgentManager:
    
    def __init__(self):
        """
           initialize data structures then load the agents
        """
        self.notificationManager = application.Application.app.model.notificationManager

        self.agentMap = {}
        self.activeAgents = {}
        self.notificationHandledStatus = {}

    def Startup(self):
        self._RegisterAgents()
        self.StartAll()

    def Shutdown(self):
        self.StopAll()

    def _RegisterAgents(self):
        """ Iterate through the AgentItems in the repository and register them """

        agentItemKind = application.Application.app.repository.find('//Parcels/OSAF/AppSchema/AgentSchema/AgentItem')

        try:
            items = agentItemKind.items
        except AttributeError:
            items = []

        for item in items:
            agentID = item.getUUID()
            self.Register(agentID)
            # hook up the widget
            #widget = AgentControl.wxAgentControl(agentID)
            #widget.AddToToolBar()

    def IsRegistered(self, agentID):
        return self.agentMap.has_key(agentID)

    def Register(self, agentID):
        """ register an agent with the agent manager """
        if self.IsRegistered(agentID):
            return

        # register with the notification manager and subscribe to notifications
        if not self.notificationManager.IsRegistered(agentID):
            self.notificationManager.Register(agentID)

        # subscribe to notifications
        agentItem = application.Application.app.repository.find(agentID)
        agentItem.SubscribeToNotifications(self.notificationManager)

        # add to the map
        agent = Agent(agentID)
        self.agentMap[agentID] = agent

        application.Application.app.repository.commit()

    def Unregister(self, agentID):
        """ unregister an agent from the agent manager """
        if not self.IsRegistered(agentID):
            raise KeyError, 'Agent Not Registered'

        # unsubscribe to notifications
        agentItem = application.Application.app.repository.find(agentID)
        agentItem.UnsubscribeFromNotifications(self.notificationManager)

        del self.agentMap[agentID]

        application.Application.app.repository.commit()

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
        self.agentMap[agentID].Resume()

    def StartAll(self):
        for agentID in self.agentMap.keys():
            self.Start(agentID)

    def Stop(self, agentID):
        """ Suspends the agent """
        if not self.IsRegistered(agentID):
            raise KeyError, 'Agent Not Registered'
        self.agentMap[agentID].Suspend()

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
