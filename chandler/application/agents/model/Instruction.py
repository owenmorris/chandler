__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from Action import Action
import logging
import application.Application # for repository

"""
The Instruction Class associates a list of conditions with a list of actions.  It is called
from the agent's main loop to evaluate conditions and execute actions.
"""
class Instruction(Item):
    def getLog(self):
        try:
            return self.log
        except AttributeError:
            self.log = logging.getLogger('Agent')
            return self.log

    def IsEnabled(self):
        return self.enabled

    def SetEnabled(self, enableFlag):
        self.enabled = enableFlag
        
    def SetCondition(self, newCondition):
        self.condition = newCondition
    
    def GetActions(self):
        return self.actions
    
    def AddAction(self, newAction):
        self.addValue('actions', newAction)
        pass
        
    def RemoveAction(self, actionToRemove):
        self.detach('actions', actionToRemove)
        pass
 
    def GetNotifications(self):
        """
          return a list of notifications associated with this instructions by
          asking the condition.
        """
        notifications = []
        if self.enabled and self.condition != None:
            notifications = self.condition.GetNotifications()
                
        return notifications
    
    def _GetNewActions(self, notification):
        """
          evaluate an instruction's condition, and return
          a list of actions to be executed if the condition is satisfied
        """
        actionsToLaunch = []
        if not self.enabled:
            return actionsToLaunch

        if self.condition.IsSatisfied(notification):
            actions = self.actions
            for action in actions:
                actionsToLaunch.append(action)

        return actionsToLaunch

    def Execute(self, agent, notification):
        self.getLog().debug('Instruction::Execute')

        result = None

        actions = self._GetNewActions(notification)
        for action in actions:
            self.getLog().debug(action)

            if action.IsAsynchronous():
                # agent.MakeTask(action, notification)
                pass
            elif action.UseWxThread() or action.NeedsConfirmation():
                actionProxy = DeferredAction(action.getUUID())

                app = application.Application.app
                lock = app.PostAsyncEvent(actionProxy.Execute, agent.getUUID(), notification)
                #while lock.locked():
                #    yield 'wait', 1.0
                #yield 'go', 0
                yield 'condition', lock.locked, False
                yield 'condition', None, True
                result = None
            else:
                self.getLog().debug('running action')
                result = action.Execute(agent, notification)

            self.getLog().debug('ExecuteActions - yielding')
            yield result
