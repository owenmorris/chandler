__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import OSAF.framework.utils.indexer as indexer
import Agent, AgentControl
import logging

"""
The AgentManager Class is responsible for loading agents from the repository and launching them at
start-up.  It maintains a directory of agents and allows callers to manipulate them
"""

def makeLog():
    log = logging.getLogger('Agent')
    hdlr = logging.FileHandler('agent.log')
    hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)
    return log

class AgentManager:
    
    def __init__(self):
        """ initialize data structures then load the agents """

        self.agentMap = {}
        self.activeAgents = {}
        self.notificationHandledStatus = {}
        self.agentIndex = indexer.getIndex('agents')
        self.log = makeLog()

    def Startup(self):
        self._BuildMap()
        self.StartAll()

    def Shutdown(self):
        self.StopAll()

    def _BuildMap(self):
        for item in self.agentIndex.items:
            agentID = item.getUUID()
            if not self.agentMap.has_key(agentID):
                self.agentMap[agentID] = Agent.Agent(agentID)

    def IsRegistered(self, agentItem):
        return agentItem in self.agentIndex.items

    def Register(self, agentItem):
        """ register an agent with the agent manager """        
        if self.IsRegistered(agentItem):
            return

        self.agentIndex.append(agentItem)
        agentItem.getRepository().commit()

        agentID = agentItem.getUUID()
        self.agentMap[agentID] = Agent.Agent(agentID)

    def Unregister(self, agentItem):
        """ unregister an agent from the agent manager """
        if not self.IsRegistered(agentItem):
            raise KeyError, 'Agent Not Registered'

        self.agentIndex.removeValue('items', agentItem)
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
        if not Globals.notificationManager.IsRegistered(agentID):
            Globals.notificationManager.Register(agentID)

        # subscribe to notifications
        agentItem = Globals.repository.find(agentID)
        agentItem.SubscribeToNotifications()

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
        agentItem.UnsubscribeFromNotifications()

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
