#!bin/env python

"""The main toolbar for Chandler.  Contains the main navigation
elements for the application, including Prev, Next, Location, and
thumbs for the toplevel views."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from wxPython.xrc import *
    
RESOURCE_FILE_LOCATION = "application/resources/location.xrc"
LOCATION_BAR_NAME = "LocationBar"

class LocationBar:
    def __init__(self, parent):
        """The information for the location bar is stored in a resource
        file.  To create the location bar we must just load it from the
        resource."""
        self.parent = parent
        self.resources = wxXmlResource(RESOURCE_FILE_LOCATION)
        self.locationBar = self.resources.LoadToolBar(self.parent, 
                                                      LOCATION_BAR_NAME)
        self.parent.SetToolBar(self.locationBar)

        id = XRCID("uriBox")
        self.uriBox = self.locationBar.FindWindowById(id)

        self.history = []
        self.future = []
        
        EVT_TOOL(self.parent, XRCID("prev"), self.__GoPrev)
        EVT_TOOL(self.parent, XRCID("next"), self.__GoNext)
        EVT_TOOL(self.parent, XRCID("stop"), self.__DoStop)
        EVT_TOOL(self.parent, XRCID("reload"), self.__DoReload)
        EVT_TOOL(self.parent, XRCID("home"), self.__GoHome)
        
        EVT_TEXT_ENTER(self.parent, XRCID("uriBox"), self.__GoToUri)
        
    def AddLocationHistory(self, uri):
        """Add the given view to the toolbar's history list.  The history
        contains the past views that have been visited as well as the view
        that is currently active (in the last position).  Adding a view to
        the history will clear the future list (used by the Next button)."""
        self.future = []
        self.history.append(uri)
        
    def SetUri(self, uri):
        """Sets the text of the uri text field in the location bar to reflect
        the current view."""
        self.uriBox.SetValue(uri)
        
    def __GoToUri(self, event):
        """When the user enters a location in the uri text box of the toolbar,
        we navigate to that uri.  If switching to that uri fails (because of
        a typo or because that uri does not exist), then we simply reset the
        text box to the current uri."""
        oldUri = self.history[len(self.history) - 1]
        newUri = self.uriBox.GetValue()
        try:
            self.parent.GoToUri(newUri)
        except:
            print "Failed to navigate to " + newUri
            self.uriBox.SetValue(oldUri)

    def __GoPrev(self, event):
        """Change to the most recent past view.  This moves you back one
        in the history of views that you have visited.  It causes the view
        that you are currently on to be added to the future list (for use
        with the Next button) and moves you to the last remembered view.
        This new view that you move to will now be the last element in the
        history list."""
        # The current view will always be in the history, so we need more
        # than 1 to be able to pop off a new view to visit.
        if len(self.history) > 1:
            currentLocation = self.history.pop()
            self.future.append(currentLocation)
            newLocationIndex = len(self.history) - 1
            newUri = self.history[newLocationIndex]
            self.parent.GoToUri(newUri, false)

    def __GoNext(self, event):
        """Change to the next view in your future list.  The Next button
        will only have an effect if the last navigation you did was to 
        use the Prev button.  If so, then the last item added to the future
        list will be popped off, added to the history list, and you will
        navigate to that view."""
        if len(self.future) > 0:
            newUri = self.future.pop()
            self.history.append(newUri)
            self.parent.GoToUri(newUri, false)

    def __DoStop(self, event):
        pass
    
    def __DoReload(self, event):
        pass
    
    def __GoHome(self, event):
        pass