__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.utils.indexer as indexer
from repository.item.Item import Item

"""
The Agent Class is the base class for all agents.  It holds the transient dynamic state of an agent,
and refers to its sister class, AgentItem, for the agent's persistent state
"""

class AgentItem(Item):
    def __init__(self, *args):
        super(AgentItem, self).__init__(*args)
        indexer.getIndex('agents').addItem(self)

    def GetName(self):
        """ return the name of the agent """
        return self.getItemDisplayName()
    
    def GetRoles(self):
        """ return a list of strings, specified roles this agent can play """
        return self.roles
   
    def GetOwner(self):
        """ return a string with the address of the owner of this agent """
        return self.agentOwner
                
    def GetRepertoire(self):
        """ return the repertoire, which contains possible conditions and actions """
        return self.repertoire

    def SetRepertoire(self, newRepertoire):
        """ set the repertoire"""
        self.repertoire = newRepertoire

    # method for manipulating instructions
    
    def GetInstructions(self):
        return self.instructions

    def AddInstruction(self, newInstruction):
        self.addValue('instructions', newInstruction)
    
    def RemoveInstruction(self, instructionToRemove):
        self.detach('instructions', instructionToRemove)


    # routines for notification management

    def _GetActiveNotifications(self):
        """
          iterate through the instructions to get a list of notifications
          that are used by enabled instructions
        """
        notificationList = []
        instructions = self.instructions
        for instruction in instructions:
            if instruction.enabled:
                instructionList = instruction.GetNotifications()
                notificationList += instructionList
        return notificationList

    def SubscribeToNotifications(self, callback):
        """
          Subscribe to the notifications used by the active instructions 
        """
        clientID = self.itsUUID
        notifications = self._GetActiveNotifications()
        Globals.notificationManager.Subscribe(notifications, clientID, callback)

    def UnsubscribeFromNotifications(self):
        """
          Unsubscribe from the notifications used by the active instructions 
        """
        clientID = self.itsUUID
        Globals.notificationManager.Unsubscribe(clientID)


    # methods concerning the agent's status
    def _UpdateStatus(self):
        """
          UpdateStatus calculates various status properties of the agent,
          which are kept in the status dictionary.  This method maintains
          the 'busyness' and 'urgency' attributes, but subclasses can
          override this to add new status attributes.

          UpdateStatus returns True if any aspect of the status has changed
          FIXME: Not implemented yet
        """

        self.addValue('status', str(self._CalculateBusyness()), 'busyness')
        self.addValue('status', str(self._CalculateUrgency()), 'urgency')
        return True

    def StatusChanged(self):
        """ issue a 'status changed' notification for this agent """
        pass

    def GetStatus(self, attribute):
        return self.getValue('status', attribute, 0)
 
    def DumpStatus(self):
        print self.itsName
        instructions = self.instructions
        for instruction in instructions:
            print "- Instruction"
            actions = instruction.GetActions()
            for action in actions:
                print "  -", action.GetName(), "[" + str(action.GetCompletionPercentage()) + "%]", instruction.GetMagicNumber(action.itsUUID)

    def _CalculateBusyness(self):
        # returns the average magic number of all the agent's actions
        i = 0
        n = 0.0
        instructions = self.instructions
        for instruction in instructions:
            actions = instruction.GetActions()
            for action in actions:
                n += instruction.GetMagicNumber(action.itsUUID)
                i += 1
        if i == 0:
            return 0.0
        return n / i

    def _CalculateUrgency(self):
        # n% of the total urgency should be the amount of busyness
        # over the norm
        return 0.0
