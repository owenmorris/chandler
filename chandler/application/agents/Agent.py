__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path
import thread
import time
import random

from wxPython.wx import wxWakeUpIdle

from model.Action import *

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
        
        # launch the agent's main loop thread
        self.isRunning = True
        thread.start_new(self.Mainloop, ())
        
    # methods concerning agent identity 
    
    def GetName(self):
        """ return the user-oriented display name of the agent
        """
        return self.model.getItemName()

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
 
    def MakeTask(self, action, actionData):
        """
           run the passed-in action asynchronously by making a task object to manage it
           FIXME:  not yet implemented
        """
        pass
    
    def LaunchNewActions(self, newActions, actionData):
        """
          launch the actions in the passed-in list
        """ 
        result = None
        for action in newActions:
            if action.IsAsynchronous():
                self.MakeTask(action, actionData)
            else:
                confirmFlag = action.NeedsConfirmation()
                if action.UseWxThread() or confirmFlag:
                    actionProxy = DeferredAction(action, self, confirmFlag, actionData)
                    self.agentManager.application.deferredActions.append(actionProxy)
                    
                    # call wxWakeUpIdle to give a chance for idle handlers to process the deferred action
                    wxWakeUpIdle()
                    
                else:
                    result = action.Execute(self, actionData)
                
    def UpdateStatus(self):
        """
          UpdateStatus calculates various status properties of the agent, which are kept
          in the status dictionary.  This method maintains the "business" and "urgency
          attributes, but subclasses can override this to add new status attributes.
          
          UpdateStatus returns True if any aspect of the status has changed
          FIXME: Not implemented yet
        """
        return False
    
    def StatusChanged(self):
        """
         issue a 'status changed' notification for this agent
        """
        pass
 
     # routines that deal with instructions
     
    def GetInstructions(self, notificationName):
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
        self.instructionMap = {}
        self.instructionMap['polled'] = []
        
        for instruction in self.model.instructions:
            notifications = instruction.GetNotifications()
            for notification in notifications:
                if self.instructionMap.has_key(notification):
                    self.instructionMap[notification].append(instruction)
                else:
                    self.instructionMap[notification] = [instruction]
         
    def ExecuteInstructions(self, instructions, notification):
        """
          here is the interpreter loop that executes a list of instructions
        """
        if notification != None:
            notificationData = notification.data
        else:
            notificationData = None
        
        for instruction in instructions:
            newActions = instruction.GetNewActions(notification)
            self.LaunchNewActions(newActions, notificationData)
            
    # here is the agent's main loop, which fetches notifications and evaluates conditions
    def Mainloop(self):
        clientID = self.GetClientID()
        
        while self.isRunning:
            self.RemoveCompletedActions()
            
            # loop, fetching notifications and handing them off to the appropriate instructions
            notificationManager = self.agentManager.application.model.notificationManager
            notification = notificationManager.GetNextNotification(clientID)

            while notification != None:
                # get instructions associated with the notification
                instructions = self.GetInstructions(notification.name)
                self.ExecuteInstructions(instructions, notification)
                notification = notificationManager.GetNextNotification(clientID)

            # now execute instructions that aren't dependent on notifications
            instructions = self.GetInstructions('polled')
            self.ExecuteInstructions(instructions, None)
            
            # run status handlers and update the status dictionary
            if self.UpdateStatus():
                self.StatusChanged()
            
            self.Idle()
            
            # sleep for an average time of one second.  Perhaps the average time should be
            # adjustable per agent
            time.sleep(2.0 * random.random())
            
    # methods concerning the agent's execution state
    
    def Idle(self):
        """
          sub-classes can override idle to do house-keeping, etc
        """
        #print "looping in agent", self.GetName()
        pass
    
    def Suspend(self):
        """
           suspend execution of the agent
        """
        self.isRunning = False
        
        
    def Resume(self):
        """
           resume execution of the agent
           FIXME: not yet implemented
        """
        pass
        
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
    
    
    