__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import Scheduler
import threading, logging

class AgentThread(threading.Thread):
    """
      here is the agent's main loop, which fetches notifications and evaluates
      conditions
    """
    def __init__(self, agent):
        super(AgentThread, self).__init__()
        self.setDaemon(True)
        self.agent = agent
        self.agentID = agent.agentID
        self.setName('AgentThread(' + str(self.agentID) + ')')
        self.scheduler = Scheduler.Scheduler()
        self.log = logging.getLogger('Agent')

    def _NewNotification(self, notification):
        #print 'checking for notification'
        self.scheduler.schedule(0, False, 0, self._HandleNotification, notification)

    def _HandleNotification(self, notification):
        self.log.debug('got notification %s', notification.event)
        agentItem = Globals.repository[self.agentID]
        instructions = self._GetInstructionsByEvent(agentItem, notification.event)
        result = _ExecuteInstructions(agentItem, instructions, notification)
        self.log.debug(result)
        return result

    def run(self):
        repository = Globals.repository

        # XXX
        # it isn't clear why this is needed here, but if it isn't here
        # the repository deadlocks when we try to find()
        repository.commit()

        # Get this threads agent item view
        agentItem = repository.find(self.agentID)

        # subscribe to notifications
        agentItem.SubscribeToNotifications(self._NewNotification)

        self.instructionMap = _BuildInstructionMap(agentItem)

        # schedule all instructions with times
        self._ScheduleInstructions(agentItem)

        # Start the scheduler
        self.scheduler.start()

    def stop(self):
        self.scheduler.stop()

    def _GetInstructionsByEvent(self, agentItem, event):
        """
          return a list of active instructions associated with the passed-in
          notification if the notification name is 'all',
          return all the instructions
        """
        instructions = []
        matchingInstructions = self.instructionMap[event.itsUUID]

        for instruction in matchingInstructions:
            if instruction.IsEnabled():
                instructions.append(instruction)

        return instructions

    def _ScheduleInstructions(self, agentItem):
        # this function is really ugly.. i should clean it up :)
        instructions = agentItem.GetInstructions()
        for instruction in instructions:
            try:
                schedule = instruction.schedule
            except AttributeError:
                continue

            try:
                startTime = schedule.startTime.ticks()
            except AttributeError:
                startTime = None

            try:
                repeatFlag = schedule.repeatFlag
            except AttributeError:
                repeatFlag = False

            if repeatFlag:
                try:
                    repeatDelay = schedule.repeatDelay.seconds
                except AttributeError:
                    repeatDelay = 0

            if startTime:
                self.scheduler.scheduleabs(startTime, repeatFlag, repeatDelay, _ExecuteInstructions, agentItem, [instruction], None)
            else:
                self.scheduler.schedule(repeatDelay, repeatFlag, repeatDelay, _ExecuteInstructions, agentItem, [instruction], None)


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
            nID = notification.itsUUID
            if instructionMap.has_key(nID):
                instructionMap[nID].append(instruction)
            else:
                instructionMap[nID] = [instruction]

    return instructionMap

def _ExecuteInstructions(agentItem, instructions, notification):
    """
    here is the interpreter loop that executes a list of instructions
    """
    log = logging.getLogger('Agent')

    for instruction in instructions:
        result = instruction.Execute(agentItem, notification)
        log.debug('_ExecuteInstructions - yielding')
        yield result

