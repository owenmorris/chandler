__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Item import Item

"""
The Repertoire Class holds conditions and actions that aren't associated with particular instructions,
to allow the user to add new instructions
"""
class Repertoire(Item):

    def GetConditions(self):
        return self.possibleConditions
    
    def AddCondition(self, newCondition):
        self.addValue('possibleConditions', newCondition)
    
    def RemoveCondition(self, conditionToRemove):
        self.detach('possibleConditions', conditionToRemove)
    
    def GetActions(self):
        return self.possibleActions
    
    def AddAction(self, newAction):
        self.addValue('possibleActions', newAction)
    
    def RemoveAction(self, actionToRemove):
        self.detach('possibleActions', actionToRemove)

        
