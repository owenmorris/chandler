__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path

from AgentThread import *

class Agent:

    def __init__(self, agentItem, agentManager):
        """
           initialize the dynamic state of the agent, then launch the main loop thread
        """    
        self.model = agentItem
        self.agentManager = agentManager

        # initialize dynamic state
        self.status = {}       
        self.activeActions = {}
        self.instructionMap = {}
        
        self._BuildInstructionMap()
        
        self.isRunning = False

    # methods concerning agent identity 
    
    def GetName(self):
        """ return the user-oriented display name of the agent
        """
        return self.model.GetName()

    def GetRoles(self):
        """
          return a list of roles this agent can play
        """
        return self.model.roles
   
    def GetClientID(self):
        """
        return the agent's client ID, which is the associated items uuid
        """
        return self.model.getUUID()
    
    def GetOwner(self):
        """
          return the address of the owner of this agent
        """
        return self.model.owner
                
    def GetResume(self):
        return self.model.resume

    # methods concerning credentials - Not yet implemented in the model
    
    def GetCredentials(self):
        """
          return a list of credentials possessed by the agent
        """
        return []
        
    def AddCredential(self, newCredential):
        """
          add a new credential to the agent
        """
        pass
        
    def RemoveCredential(self, credential):
        """
          remove a credential from the agents list
        """
        pass
    
    # methods concerning the agent's status
    
    def GetStatus(self, attribute):
        """
          return the status associated with the passed-in attribute, or -1 if it's not defined
        """
        if self.status.has_key(attribute):
            return self.status[attribute]
        
        return -1
        
    def SetStatus(self, attribute, value):
        """
          Set the status associated with the passed-in attribute
        """
        self.status[attribute] = value
     
    def RemoveCompletedActions(self):
        """
           remove any actions that are completed from the queue
        """
        for action in self.activeActions.keys():
            if action.IsCompleted():
                del self.activeActions[action]
 
    def MakeTask(self, action, notification):
        """
           run the passed-in action asynchronously by making a task object to manage it
           FIXME:  not yet implemented
        """
        pass

    def UpdateStatus(self):
        """
          UpdateStatus calculates various status properties of the agent, which are kept
          in the status dictionary.  This method maintains the 'business' and 'urgency'
          attributes, but subclasses can override this to add new status attributes.
          
          UpdateStatus returns True if any aspect of the status has changed
          FIXME: Not implemented yet
        """

        self.SetStatus('busyness', self._CalculateBusyness())
        self.SetStatus('urgency', self._CalculateUrgency())
        return True
    
    def StatusChanged(self):
        """
         issue a 'status changed' notification for this agent
        """
        pass
 
     # routines that deal with instructions
     
    def GetInstructionsByName(self, notificationName):
        """
          return a list of active instructions associated with the passed-in notification
          if the notification name is 'all', return all the instructions
        """      
        instructions = []
        if notificationName == 'all':
            matchingInstructions = self.model.instructions
        else:
            matchingInstructions = self.instructionMap[notificationName]
             
        for instruction in matchingInstructions:
            if instruction.IsEnabled():
                instructions.append(instruction)
                
        return instructions
     
    def _BuildInstructionMap(self):
        """
           loop through the instructions to build a hash table, mapping notification types
           to a list of instructions that use the notification. 
        """
        instructionMap = {}
        instructionMap['polled'] = []
        
        for instruction in self.model.instructions:
            notifications = instruction.GetNotifications()
            for notification in notifications:
                if instructionMap.has_key(notification):
                    instructionMap[notification].append(instruction)
                else:
                    instructionMap[notification] = [instruction]

        self.instructionMap = instructionMap
         
    # methods concerning the agent's execution state
    
    def Idle(self):
        """
          sub-classes can override idle to do house-keeping, etc
        """
        if self.agentManager.debugMode:
            print "looping in agent", self.GetName()
    
    def Suspend(self):
        """
           suspend execution of the agent
        """
        # XXX we need to post a notification (will that cause a context
        # switch?) that the thread can wake up on.  Then join the thread
        # and wait for it to die
        self.isRunning = False

    def Resume(self):
        """
           resume execution of the agent
        """
        if not self.isRunning:
            self.isRunning = True
            AgentThread(self).start()
        
    def IsSuspended(self):
        """
           return True if the agent is suspended
        """
        return self.isRunning

    def Reset(self):
        """
          reset an agent to its initial state
          FIXME: not yet implemented
        """
        pass

    def DumpStatus(self):
        print self.GetName()
        for instruction in self.model.GetInstructions():
            print "- Instruction"
            for action in instruction.GetActions():
                print "  -", action.GetName(), "[" + str(action.GetCompletionPercentage()) + "%]", action.GetMagicNumber()

    def _CalculateBusyness(self):
        # returns the average magic number of all the agent's actions
        i = 0
        n = 0.0
        for instruction in self.model.GetInstructions():
            for action in instruction.GetActions():
                n += action.GetMagicNumber()
                i += 1
        if i == 0:
            return 0.0
        return n / i

    def _CalculateUrgency(self):
        # n% of the total urgency should be the amount of busyness
        # over the norm
        return 0.0
