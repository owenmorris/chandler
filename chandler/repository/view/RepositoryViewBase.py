__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import twisted.internet.reactor as reactor
import repository.persistence.RepositoryError as RepositoryError
import logging as logging


class RepositoryViewBase(object): 
    """Base class that handles Repository view management.
       This is most useful when leveraging the Twisted
       asynchronous event loop."""
   
    def __init__(self, viewName = None):
        self.view = Globals.repository.createView(viewName)
        self.prevView = None       
        self.callChain = False
        self.log = self._getLog()

    def _getLog(self):
        """Can Extend"""
        log = logging.getLogger("framework_twisted")
        log.setLevel(logging.DEBUG)
        return log
            
    # Called from Reactor or in a Thread  
    def setViewCurrent(self):
        """Test that view set and unset was called in proper order"""
        assert self.callChain is False, "setViewCurrent called again before a restorePreviousView"
        
        assert self.prevView is None, "Nested prevView investigate"
        self.prevView = self.view.setCurrentView()
        self.callChain = True
       
         
    # Should be called from a Thread or in the Reactor
    def restorePreviousView(self):
        assert self.callChain is True, "restorePreviousView called before calling setViewCurrent"

        if self.prevView is not None:
             Globals.repository.setCurrentView(self.prevView)
             self.prevView = None
             
        self.callChain = False

    # Called from Reactor or in a Thread       
    def execInView(self, method, *args, **kw):
        """Handles View context switch and restore for the caller"""
        
        self.setViewCurrent()
        
        try:
            method(*args, **kw)         
   
        finally:
            self.restorePreviousView() 
            
    # Called from Reactor or in a Thread                
    def getCurrentView(self):
        return Globals.repository.getCurrentView(False)
     
    # Called from Reactor or in a Thread         
    def printCurrentView(self, printString = None):
        str = None
        
        if printString is None:
             self.log.info("Current View is: %s" % self.getCurrentView())
        else:
             self.log.info("[%s] Current View is: %s" % (printString, self.getCurrentView()))


    # Called from Reactor
    def commitView(self):
        """Runs a repository view commit in a thread to prevent blocking the 
           Twisted event loop. Commit resolution logic can be time consuming
           Let other Twisted events get processed while 
           the repository is handling the commit"""

        reactor.callInThread(self.__commitViewInThread)

    # Called from Thread       
    def _viewCommitSuccess(self):
         """Overide this method to handle any special cases required 
            after a view is committed. The default implementation will
            post the commit event back to the CPIA thread"""
   
         Globals.wxApplication.PostAsyncEvent(Globals.repository.commit)

    # Called from Thread
    def _viewCommitFailed(self):    
         """If the commit failed then conflicts must be resolved.
            Overide this method to handle resolution logic"""
        
         self.log.error("ViewCommitFailed")
        
    
    # Called in a thread from the Twisted thread pool
    def __commitViewInThread(self):
        """Tries to commit the view and call viewCommitSuccess or 
           viewCommitFailed.  Need to sync with Andi on
           what happens in the case of a conflict or 
           failed commit. This is still being resolved 
           by the repository team """

        self.setViewCurrent()

        try:
           self.view.commit()

        except RepositoryError:
           """This condition needs to be flushed out more"""
           self._viewCommitFailed()

        else:
           self._viewCommitSuccess()

        self.restorePreviousView()
