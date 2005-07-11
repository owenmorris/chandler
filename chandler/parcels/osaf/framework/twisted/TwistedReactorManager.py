__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import twisted.internet.reactor as reactor
import threading
import twisted.python.threadable as threadable

from repository.persistence.Repository import RepositoryThread


"""required when using threads in Twisted"""
threadable.init()


class TwistedReactorException(Exception):
    """Exception Class raised by L{TwistedReactorManager}"""
    pass

class TwistedReactorManager(RepositoryThread):
    """Runs the Twisted Reactor in a Thread to prevent blocking of the
       Main Thread when C{reactor.run} is called. Only one instance of
       the TwistedReactorManager can be initialized at a time"""


    __reactorRunning = False

    def run(self):
        """
        This method is called by C{Threading.Thread} when the thread is started.

        It starts and runs the Twisted reactor.
        @return: C{None}
        """

        if self.__reactorRunning:
            raise TwistedReactorException("Reactor Already Running")

        self.__reactorRunning = True

        """call run passing a False flag indicating to the
           reactor not to install sig handlers. Sig handlers
           only work on the main thread"""

        reactor.run(False)

    def startReactor(self):
        """
        This method starts the Twisted Reactor thread and runs the Twisted Reactor.

        @return: C{None}
        """

        if self.__reactorRunning:
            raise TwistedReactorException("Reactor Already Running")

        self.start()


    def stopReactor(self):
        """
        This method stops the Twisted Reactor which will terminate the C{Thread} as it goes out of
        scope.

        @return: C{None}
        """

        if not self.__reactorRunning:
            raise TwistedReactorException("Reactor Not Running")

        reactor.callFromThread(reactor.stop)
        self.join()
