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

    def __init__(self, name, parent, kind, **_kwds):
        super(Instruction, self).__init__(name, parent, kind, **_kwds)
     
    def AddCondition(self, newCondition):
        self.attach('conditions', newCondition)
        
    def RemoveCondition(self, conditionToRemove):
        self.detach('conditions', conditionToRemove)
        
    def AddAction(self, newAction):
        self.attach('actions', newAction)
        
    def RemoveAction(self, actionToRemove):
        self.detach('actions', actionToRemove)
 
    def GetNotifications(self):
        """
          return a list of notifications associated with this instructions by
          iterating through the conditions.
        """
        notifications = []
        if self.enabled:
            for condition in self.conditions:
                notifications += condition.GetNotifications()
                
        return notifications
    
    def GetNewActions(self, notificationList):
        """
          key routine to evaluate an instructions conditions, and return
          a list of actions to be executed if it passes the conditions,
          as well as data derived from the condition to pass to the actions
        """
        actionsToLaunch = []
        conditionData = None
        
        # FIXME:  for now, we assume all the conditions are in 'OR' mode: if any are true, the instruction
        # will fire.  This will soon change
        for condition in self.conditions:
            (conditionResult, conditionData) = condition.DetermineCondition(notificationList)
            if conditionResult:
                for action in self.actions:
                    actionsToLaunch.append(action)
                break
            
        return (actionsToLaunch, conditionData)
    
   