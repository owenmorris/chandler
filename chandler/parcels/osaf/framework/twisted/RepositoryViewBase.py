__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals

class RepositoryViewBase(object): 
   
    def __init__(self, viewName = None):
        self.repository = Globals.repository
        self.view = self.repository.createView(viewName)
        self.viewName = viewName
        self.prevView = None       
        self.printCurrentView()
            
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