__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
import application.Application # for repository

"""
The Agent Class is the base class for all agents.  It holds the transient dynamic state of an agent,
and refers to its sister class, AgentItem, for the agent's persistent state
"""
class AgentItem(Item):

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
    
    def SubscribeToNotifications(self, notificationManager):
        """
          Subscribe to the notifications used by the active instructions 
        """
        clientID = self.getUUID()
        notifications = self._GetActiveNotifications()
        for notification in notifications:
            notificationManager.Subscribe(notification, clientID)

    def UnsubscribeFromNotifications(self, notificationManager):
        """
          Unsubscribe from the notifications used by the active instructions 
        """
        clientID = self.getUUID()
        notifications = self._GetActiveNotifications()
        for notification in notifications:
            notificationManager.Unsubscribe(notification, clientID)


    # methods concerning the agent's status
    def UpdateStatus(self):
        """
          UpdateStatus calculates various status properties of the agent,
          which are kept in the status dictionary.  This method maintains
          the 'busyness' and 'urgency' attributes, but subclasses can
          override this to add new status attributes.

          UpdateStatus returns True if any aspect of the status has changed
          FIXME: Not implemented yet
        """

        try:
            if self.status == None:
                pass
        except:
            self.status = {}

        self.status['busyness'] = str(self._CalculateBusyness())
        self.status['urgency'] = str(self._CalculateUrgency())
        return True

    def StatusChanged(self):
        """ issue a 'status changed' notification for this agent """
        pass

    def GetStatus(self, attribute):
        return self.status[attribute]
 
    def DumpStatus(self):
        print self.getItemName()
        instructions = self.instructions
        for instruction in instructions:
            print "- Instruction"
            actions = instruction.GetActions()
            for action in actions:
                print "  -", action.GetName(), "[" + str(action.GetCompletionPercentage()) + "%]", action.GetMagicNumber()

    def _CalculateBusyness(self):
        # returns the average magic number of all the agent's actions
        i = 0
        n = 0.0
        instructions = self.instructions
        for instruction in instructions:
            actions = instruction.GetActions()
            for action in actions:
                n += action.GetMagicNumber()
                i += 1
        if i == 0:
            return 0.0
        return n / i

    def _CalculateUrgency(self):
        # n% of the total urgency should be the amount of busyness
        # over the norm
        return 0.0
