__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.item.Item import Item

"""
The Agent Class is the base class for all agents.  It holds the transient dynamic state of an agent,
and refers to its sister class, AgentItem, for the agent's persistent state
"""
class AgentItemFactory:
    def __init__(self, repository):
        self._container = repository.find("//Agents")
        self._kind = repository.find("//Schema/AgentsSchema/AgentItem")
        self.repository = repository
        
    def NewItem(self, agentName):
        item = AgentItem(agentName, self._container, self._kind)
        
        return item

class AgentItem(Item):

    def __init__(self, name, parent, kind, **_kwds):
        super(AgentItem, self).__init__(name, parent, kind, **_kwds)
    
    def GetName(self):
        """ return the name of the agent"""
        return self.agentName
    
    def GetRoles(self):
        """ return a list of strings, specified roles this agent can play"""
        return self.roles
   
    def GetOwner(self):
        """ return a string with the address of the owner of this agent"""
        return self.agentOwner
                
    def GetDescription(self):
        """ return a string with a description of the agent"""
        return self.agentDescription
    
    def SetDescription(self, newDescription):
        """ set a string with a description of the agent"""
        self.agentDescription = newDescription
    
    def GetRepertoire(self):
        """ return the repertoire, which contains possible conditions and actions"""
        return self.repertoire

    def SetRepertoire(self, newRepertoire):
        """ set the repertoire"""
        self.repertoire = newRepertoire
        
    # routines for notification management
    def GetActiveNotifications(self):
        """
          iterate through the instructions to get a list of notifications
          that are used by enabled instructions
        """
        notificationList = []
        for instruction in self.instructions:
            if instruction.enabled:
                instructionList = instruction.GetNotifications()
                notificationList += instructionList
        return notificationList
    
    def SubscribeToNotifications(self):
        """
          Subscribe to the notifications used by the active instructions 
        """
        notifications = self.GetActiveNotifications()
        
    def UnsubscribeFromNotifications(self):
        """
          Unsubscribe from the notifications used by the active instructions 
        """
        notifications = self.GetActiveNotifications()
        
    # method for manipulating instructions
    
    def GetInstructions(self):
        return self.instructions
    
    def AddInstruction(self, newInstruction):
        self.attach('instructions', newInstruction)
    
    def RemoveInstruction(self, instructionToRemove):
        self.detach('instructions', instructionToRemove)
    
    # methods concerning the agent's execution state
            
    def Suspend(self):
        pass
        
    def Resume(self):
        pass
        
    def IsSuspended(self):
        pass        

 