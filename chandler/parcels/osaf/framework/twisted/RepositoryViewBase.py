__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from twisted.internet import reactor 

class RepositoryViewBase(object): 
    """Base class that handles Repository view management.
       This is most useful when leveraging the Twisted
       asynchronous event loop."""
   
    def __init__(self, viewName = None):
        self.repository = Globals.repository
        self.view = self.repository.createView(viewName)
        self.viewName = viewName
        self.prevView = None       
            
    #Called from Reactor or in a Thread  
    def setViewCurrent(self):
        self.prevView = self.view.setCurrentView()
    
    #should be called from a Thread but can be called in Reactor
    def restorePreviousView(self):
        if self.prevView is not None:
             self.repository.setCurrentView(self.prevView)
     
    
    #Called from Reactor or in a Thread       
    def execInView(self, method, *args, **kw):
        """Handles View context switch and restore for the caller"""
        
        self.setViewCurrent()
        
        try:
            method(*args, **kw)         
   
        finally:
            self.restorePreviousView() 
            
    #Called from Reactor or in a Thread                
    def getCurrentView(self):
        return self.repository.getCurrentView(False)
     
    #Called from Reactor or in a Thread         
    def printCurrentView(self, printString = None):
        if printString is None:
            print "Current View is: ", self.getCurrentView()
            
        else:
            print "[%s] Current View is: %s" % (printString, self.getCurrentView())

    #Called from Reactor
    def commitView(self):
        """Runs a repository view commit in a thread to prevent blocking the 
           Twisted event loop. Commit resolution logic can be time consuming
           Let other Twisted events get processed while 
           the repository is handling the commit"""

        reactor.callInThread(self.__commitViewInThread)

    #Called from Reactor       
    def viewCommitSuccess(self):
         """Overide this method to handle any special cases required 
            after a view is committed. The default implementation will
            post the commit event back to the CPIA thread"""

         Globals.wxApplication.PostAsyncEvent(MainThreadCommit)

    #Called from Reactor
    def viewCommitFailed(self):    
         """If the commit failed then conflicts must be resolved.
            Overide this method to handle resolution logic"""
         pass
    
    #Called in a thread from the Twisted thread pool
    def __commitViewInThread(self):
        """Tries to commit the view and call viewCommitSuccess or 
           viewCommitFailed.  Need to sync with Andi on
           what happens in the case of a conflict or 
           failed commit. This is still being resolved 
           by the repository team """

        self.setViewCurrent()

        try:
           self.view.commit()
           self.viewCommitSuccess()

        except:
           """This condition needs to be flushed out more"""
           self.viewCommitFailed()

        self.restorePreviousView()

def MainThreadCommit():
    Globals.repository.commit()
