__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path
import thread
import time
import os

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
 
    # here are some utilities called from the agent's main loop
    def FetchNotifications(self):
        """
          return a list of pending notifications from the notification manager
        """
        notifications = []
        clientID = self.GetClientID()
        moreToDo = True
        
        while moreToDo:
            notification = self.agentManager.application.model.notificationManager.GetNextNotification(clientID)
            if notification != None:
                notifications.append(notification)
            else:
                moreToDo = False
                
        return notifications
    
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
        for action in newActions:
            if action.IsAsynchronous():
                self.MakeTask(action, actionData)
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
     
    # here is the agent's main loop, which fetches notifications and evaluates conditions
    def Mainloop(self):
        while self.isRunning:
            notifications = self.FetchNotifications()
            self.RemoveCompletedActions()
             # give each enabled instruction a chance to specify some actions
            for instruction in self.model.instructions:
                if instruction.enabled:
                    (newActions, actionData) = instruction.GetNewActions(notifications)             
                    if len(newActions) > 0:
                        self.LaunchNewActions(newActions, actionData)
            
            # run status handlers and update the status dictionary
            if self.UpdateStatus():
                self.StatusChanged()
            
            self.Idle()
            # FIXME: randomize sleep time so all the agents don't wake up at once
            time.sleep(1.5)
            
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
    
    
    