__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from AgentThread import AgentThread
import logging, threading

class Agent:
    def __init__(self, agentID):
        """ initialize the dynamic state of the agent """
        self.agentID = agentID

        self.isRunning = False
        self.thread = AgentThread(self)

        self.log = logging.getLogger('Agent')
        self.__lock = threading.Lock()

    def Idle(self):
        """ sub-classes can override idle to do house-keeping, etc """
        # currently not called
        self.log.debug("looping in agent")
    
    def Suspend(self):
        self.__lock.acquire()
        try:
            if self.isRunning:
                self.thread.stop()
                self.thread.join()
                self.isRunning = False
        finally:
            self.__lock.release()

    def Resume(self):
        self.__lock.acquire()
        try:
            if not self.isRunning:
                self.isRunning = True
                self.thread.start()
        finally:
            self.__lock.release()

    def IsSuspended(self):
        self.__lock.acquire()
        try:
            return not self.isRunning
        finally:
            self.__lock.release()
    
    def Reset(self):
        """
          reset an agent to its initial state
          FIXME: not yet implemented
        """
        pass
