"""
@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import application.Globals as Globals

from twisted.internet import defer, reactor
import threading
from twisted.python import threadable

#required for using threads with the Reactor
threadable.init()
 

class TwistedReactorException(Exception):
      def __init__(self, *args):
            Exception.__init__(self, *args)
            

class TwistedReactorManager(threading.Thread):    
  
      """Run the Reactor in a Thread to prevent blocking the 
         Main Thread once reactor.run is called"""
    
      """Only one instance of the Reactor can be running at a time"""      
      _reactorRunning = False

      def __init__(self):
              threading.Thread.__init__(self)

              
      def run(self):
              if self._reactorRunning:
                    raise TwistedReactorException("Reactor Already Running")
              
              self._reactorRunning = True
              
              #call run passing a False flag indicating to the
              #reactor not to install sig handlers since sig handlers
              #only work on the main thread

              reactor.run(False)	     	                  
            
      def isReactorRunning(self):
              return self._reactorRunning
       
      def startReactor(self):
             if self._reactorRunning:
                    raise TwistedReactorException("Reactor Already Running")
             
             threading.Thread.start(self)
             
             #reactor.addSystemEventTrigger('after', 'shutdown', self.__reactorShutDown)

            
      def stopReactor(self):
            """may want a way to force thread to join if reactor does not shutdown
               properly"""
            
            if not self._reactorRunning:
                   raise TwistedReactorException("Reactor Not Running")
           
            reactor.callFromThread(reactor.stop)
             
 