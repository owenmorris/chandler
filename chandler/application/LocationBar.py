#!bin/env python

"""The main toolbar for Chandler.  Contains the main navigation
elements for the application, including Prev, Next, Location, and
thumbs for the toplevel views."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"


from wxPython.wx import *
from wxPython.xrc import *
    
class LocationBar:
    def __init__(self, parent):
        self.parent = parent
        self.resources = wxXmlResource ("application/resources/location.xrc")
        self.locationBar = self.resources.LoadToolBar(self.parent, "LocationBar")
        self.parent.SetToolBar(self.locationBar)

        self.history = []
        self.future = []
        
        EVT_TOOL(self.parent, XRCID("prev"), self.GoPrev)
        EVT_TOOL(self.parent, XRCID("next"), self.GoNext)
        EVT_TOOL(self.parent, XRCID("stop"), self.DoStop)
        EVT_TOOL(self.parent, XRCID("reload"), self.DoReload)
        EVT_TOOL(self.parent, XRCID("home"), self.GoHome)
        
    def AddLocationHistory(self, component, viewName):
        self.future = []
        tuple = (component, viewName)
        self.history.append(tuple)

    def GoPrev(self, event):
#        if self.history.count() < 1: return
#        newLocation = self.history.pop()
#        self.future.append(newLocation)
#        self.parent.SelectComponent(newLocation[0], newLocation[1])
         pass

    def GoNext(self, event):
#        if self.future.count() < 1: return
#        newLocation = self.future.pop()
#        self.
#        newLocation = self.history.pop()
#        self
        pass
    
    def DoStop(self, event):
        pass
    
    def DoReload(self, event):
        pass
    
    def GoHome(self, event):
        pass