__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import threading

class AgentThread(threading.Thread):
    """
      here is the agent's main loop, which fetches notifications and evaluates
      conditions
    """
    def __init__(self, agent):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("AgentThread(" + agent.GetName() + ")")
        self.agent = agent

    def run(self):
        agent = self.agent
        clientID = agent.GetClientID()
        notificationManager = agent.agentManager.notificationManager

        # loop, fetching notifications and handing them off to the appropriate instructions
        while agent.isRunning:
            agent.RemoveCompletedActions()

            notification = notificationManager.WaitForNextNotification(clientID)

            # get instructions associated with the notification
            instructions = agent.GetInstructionsByName(notification.name)
            self._ExecuteInstructions(agent, instructions, notification)

            # XXX these will only get processed when their is a notification..
            # need to come up with something more clever here.
            # 
            # XXX Run a timer to fire a notification every so often for these
            # polled instructions
            # now execute instructions that aren't dependent on notifications
            instructions = agent.GetInstructionsByName('polled')
            self._ExecuteInstructions(agent, instructions, None)

            # run status handlers and update the status dictionary
            if agent.UpdateStatus():
                agent.StatusChanged()

            # XXX do we need to call this at all?
            agent.Idle()

    def _ExecuteInstructions(self, agent, instructions, notification):
        """
          here is the interpreter loop that executes a list of instructions
        """
        for instruction in instructions:
            newActions = instruction.GetNewActions(notification)
            instruction.ExecuteActions(agent, newActions, notification)
