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
        """Add the given view to the toolbar's history list.  Adding a view to
        the history will clear the future list (used by the Next button).  The
        view that has been most recently added to history will be the one used
        by the Prev button."""
#        self.future = []
#        tuple = (component, viewName)
#        self.history.append(tuple)
        pass

    def GoPrev(self, event):
#        if len(self.history) < 1: return
#        newLocation = self.history.pop()
#        self.future.append(newLocation)
#        self.parent.SelectComponent(newLocation[0], newLocation[1], false)
        pass

    def GoNext(self, event):
#        if len(self.future) < 1: return
#        newLocation = self.future.pop()
#        self.history.append(newLocation)
#        self.parent.SelectComponent(newLocation[0], newLocation[1], false)
        pass

    def DoStop(self, event):
        pass
    
    def DoReload(self, event):
        pass
    
    def GoHome(self, event):
        pass