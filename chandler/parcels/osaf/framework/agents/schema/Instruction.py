__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from Action import Action
import logging
import time
import application.Application # for application

class Timer:
    def __init__(self):
        self.starttime = time.time()
        self.count = 0
        self.executeTime = 0 # amount of time spent executing

    def getNumber(self):
        try:
            running = time.time() - self.starttime # seconds
            #averagetime = self.executeTime / self.count
            return self.executeTime / running
        except:
            return -1

    def update(self, length):
        self.count += 1
        self.executeTime += length

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
        try:
            if self.enabled:
                notifications = self.condition.GetNotifications()
                return notifications

        except AttributeError:
            pass

        return []
    
    def _GetNewActions(self, notification):
        """
          evaluate an instruction's condition, and return
          a list of actions to be executed if the condition is satisfied
        """
        if self.enabled:
            if not self.hasAttributeValue('condition') or \
                   self.condition.IsSatisfied(notification):
                return self.actions

        return []

    def Execute(self, agent, notification):
        self.getLog().debug('Instruction::Execute')

        result = None

        actions = self._GetNewActions(notification)
        for action in actions:
            start = time.clock()
            
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

            end = time.clock() - start
            actionID = action.getUUID()
            """
            if not self.hasAttributeValue('timers'):
                self.timers = {}
            try:
                timer = self.timers[actionID]
            except:
                timer = Timer()
                self.timers[actionID] = timer
            timer.update(end - start)
            """
            yield result

    def GetMagicNumber(self, actionID):
        try:
            return self.timers[actionID].getNumber()
        except:
            return 0.0
