__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.item.Item import Item

"""
The Instruction Class associates a list of conditions with a list of actions.  It is called
from the agent's main loop to evaluate conditions and execute actions.
"""
class InstructionFactory:
    def __init__(self, repository):
        self._container = repository.find("//Agents")
        self._kind = repository.find("//Schema/AgentsSchema/Instruction")
        self.repository = repository
        
    def NewItem(self):
        item = Instruction(None, self._container, self._kind)              
        return item

class Instruction(Item):

    def IsEnabled(self):
        return self.enabled

    def SetEnabled(self, enableFlag):
        self.enabled = enableFlag
        
    def SetCondition(self, newCondition):
        self.condition = newCondition
    
    # even though an instruction only has a single condition, support an AddCondition method
    # so Instruction can share a common interface with Repertoire
    def AddCondition(self, newCondition):
        self.condition = newCondition
        
    def GetActions(self):
        return self.actions
    
    def AddAction(self, newAction):
        self.attach('actions', newAction)
        
    def RemoveAction(self, actionToRemove):
        self.detach('actions', actionToRemove)
 
    def GetNotifications(self):
        """
          return a list of notifications associated with this instructions by
          asking the condition.
        """
        notifications = []
        if self.enabled and self.condition != None:
            notifications = self.condition.GetNotifications()
                
        return notifications
    
    def GetNewActions(self, notification):
        """
          evaluate an instruction's condition, and return
          a list of actions to be executed if the condition is satisfied
        """
        actionsToLaunch = []
        if not self.enabled:
            return actionsToLaunch
        
        if self.condition.IsSatisfied(notification):
            for action in self.actions:
                actionsToLaunch.append(action)
                        
        return actionsToLaunch
    
   
