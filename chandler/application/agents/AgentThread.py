__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import Scheduler
import threading
import logging
import application.Application # for repository

class AgentThread(threading.Thread):
    """
      here is the agent's main loop, which fetches notifications and evaluates
      conditions
    """
    def __init__(self, agent):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.agent = agent
        self.agentID = agent.agentID
        self.setName("AgentThread(" + str(self.agentID) + ")")
        self.scheduler = Scheduler.Scheduler()
        self.log = logging.getLogger('Agent')

    def _CheckForNotifications(self, notificationManager, agentItem):
        #print 'checking for notification'
        notification = notificationManager.GetNextNotification(self.agentID)
        if notification:
            self.scheduler.schedule(0, False, self._HandleNotification, notification, agentItem)

    def _HandleNotification(self, notification, agentItem):
        self.log.debug('got notification %s', notification.GetName())
        instructions = self._GetInstructionsByName(agentItem, notification.name)
        result = _ExecuteInstructions(agentItem, instructions, notification)
        self.log.debug(result)
        return result

    def run(self):
        app = application.Application.app
        repository = app.repository

        # XXX
        # it isn't clear why this is needed here, but if it isn't here
        # the repository deadlocks when we try to find()
        repository.commit()

        # Get this threads agent item view
        agentItem = repository.find(self.agentID)

        self.instructionMap = _BuildInstructionMap(agentItem)

        # XXX Set up a scheduler to look for new notifications until the
        #     notification manager can give us callbacks
        notificationManager = app.model.notificationManager
        self.scheduler.schedule(0.1, True, self._CheckForNotifications, notificationManager, agentItem)

        # Start the scheduler
        self.scheduler.start()

    def stop(self):
        self.scheduler.stop()

    def _GetInstructionsByName(self, agentItem, notificationName):
        """
          return a list of active instructions associated with the passed-in
          notification if the notification name is 'all',
          return all the instructions
        """
        instructions = []
        if notificationName == 'all':
            matchingInstructions = agentItem.GetInstructions()
        else:
            matchingInstructions = self.instructionMap[notificationName]

        for instruction in matchingInstructions:
            if instruction.IsEnabled():
                instructions.append(instruction)

        return instructions

def _BuildInstructionMap(agentItem):
    """
    loop through the instructions to build a hash table, mapping
    notification types to a list of instructions that use the
    notification. 
    """
    instructionMap = {}
    instructionMap['polled'] = []

    instructions = agentItem.GetInstructions()
    for instruction in instructions:
        notifications = instruction.GetNotifications()
        for notification in notifications:
            if instructionMap.has_key(notification):
                instructionMap[notification].append(instruction)
            else:
                instructionMap[notification] = [instruction]

    return instructionMap

def _ExecuteInstructions(agentItem, instructions, notification):
    """
    here is the interpreter loop that executes a list of instructions
    """
    log = logging.getLogger('Agent')

    log.debug('_ExecuteInstructions')
    for instruction in instructions:
        result = instruction.Execute(agentItem, notification)
        log.debug('_ExecuteInstructions - yielding')
        yield result
