__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import twisted.internet.reactor as reactor
import threading
import twisted.python.threadable as threadable

"""required when using threads in Twisted"""
threadable.init()
 

class TwistedReactorException(Exception):
    pass 

class TwistedReactorManager(threading.Thread):    
  
    """Run the Reactor in a Thread to prevent blocking the 
       Main Thread once reactor.run is called"""
    
    """Only one instance of the Reactor can be running at a time"""      
    __reactorRunning = False

    def run(self):
        if self.__reactorRunning:
            raise TwistedReactorException("Reactor Already Running")
              
        self.__reactorRunning = True
              
        """call run passing a False flag indicating to the
           reactor not to install sig handlers since sig handlers
           only work on the main thread"""

        reactor.run(False)	     	                  
            
    def startReactor(self):
        if self.__reactorRunning:
            raise TwistedReactorException("Reactor Already Running")
             
        self.start()
             
            
    def stopReactor(self):
        """may want a way to force thread to join if reactor does not shutdown
           properly"""
            
        if not self.__reactorRunning:
            raise TwistedReactorException("Reactor Not Running")
           
        reactor.callFromThread(reactor.stop)
