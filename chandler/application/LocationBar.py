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
        self._parent = parent
        self._resources = wxXmlResource(RESOURCE_FILE_LOCATION)
        self.locationBar = self._resources.LoadToolBar(self._parent, 
                                                      LOCATION_BAR_NAME)
        self._parent.SetToolBar(self.locationBar)

        id = XRCID("uriBox")
        self._uriBox = self.locationBar.FindWindowById(id)

        self._history = []
        self._future = []
        
        self.__CreateEvents()
        
    def AddLocationHistory(self, uri):
        """Add the given view to the toolbar's history list.  The history
        contains the past views that have been visited as well as the view
        that is currently active (in the last position).  Adding a view to
        the history will clear the future list (used by the Next button)."""
        self._future = []
        self._history.append(uri)
        
    def SetUri(self, uri):
        """Sets the text of the uri text field in the location bar to reflect
        the current view."""
        self._uriBox.SetValue(uri)

    def __CreateEvents(self):
        """Creates all of the events for the location bar."""
        EVT_TOOL(self._parent, XRCID("prev"), self.__GoPrev)
        EVT_TOOL(self._parent, XRCID("next"), self.__GoNext)
        EVT_TOOL(self._parent, XRCID("stop"), self.__DoStop)
        EVT_TOOL(self._parent, XRCID("reload"), self.__DoReload)
        EVT_TOOL(self._parent, XRCID("home"), self.__GoHome)
        
        EVT_TEXT_ENTER(self._parent, XRCID("uriBox"), self.__GoToUri)
        
    def __GoToUri(self, event):
        """When the user enters a location in the uri text box of the toolbar,
        we navigate to that uri.  If switching to that uri fails (because of
        a typo or because that uri does not exist), then we simply reset the
        text box to the current uri."""
        oldUri = self._history[-1]
        newUri = self._uriBox.GetValue()
        try:
            self._parent.GoToUri(newUri)
        except:
            print "Failed to navigate to " + newUri
            self._uriBox.SetValue(oldUri)

    def __GoPrev(self, event):
        """Change to the most recent past view.  This moves you back one
        in the history of views that you have visited.  It causes the view
        that you are currently on to be added to the future list (for use
        with the Next button) and moves you to the last remembered view.
        This new view that you move to will now be the last element in the
        history list."""
        # The current view will always be in the history, so we need more
        # than 1 to be able to pop off a new view to visit.
        if len(self._history) > 1:
            currentLocation = self._history.pop()
            self._future.append(currentLocation)
            newUri = self._history[-1]
            self._parent.GoToUri(newUri, false)

    def __GoNext(self, event):
        """Change to the next view in your future list.  The Next button
        will only have an effect if the last navigation you did was to 
        use the Prev button.  If so, then the last item added to the future
        list will be popped off, added to the history list, and you will
        navigate to that view."""
        if len(self._future) > 0:
            newUri = self._future.pop()
            self._history.append(newUri)
            self._parent.GoToUri(newUri, false)

    def __DoStop(self, event):
        pass
    
    def __DoReload(self, event):
        pass
    
    def __GoHome(self, event):
        pass