#!bin/env python

"""The chandler application.  The application itself simply tracks open
ChandlerWindows."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from wxPython.xrc import *

from application.ChandlerWindow import ChandlerWindow
from application.XmlReader import XmlReader

import sys
import os

STARTING_X_POS = 20
STARTING_Y_POS = 20
NEW_WINDOW_DELTA_X = 40
NEW_WINDOW_DELTA_Y = 40
DEFAULT_X_PERCENTAGE = .8
DEFAULT_Y_PERCENTAGE = .9
COMPONENTS_DIRECTORY = "./components"
PREFS_LOCATION = "./application/resources/preferences.xrc"

class osafApp(wxApp):
    def OnInit(self):
        """Does basic housecleaning setup.  Gets a list of all of the
        available  components and creates a ChandlerWindow."""
        wxInitAllImageHandlers()
#        InitDatabase() #
        self._frames = []
        self._componentStrings = self.__GetComponentList()
        self.__LoadPrefs()
        frame = ChandlerWindow(None, self, self._componentStrings, 
                               size = self._windowSize,
                               pos = wxPoint(STARTING_X_POS, STARTING_Y_POS))
        self._frames.append(frame)
        frame.Show(true)
        
        return true

    def __LoadPrefs(self):
        """Reads the preferences from an xml file."""
        self._reader = XmlReader()
        self._prefs = self._reader.ReadXmlFile(PREFS_LOCATION)
        
        x = string.atoi(self._prefs["preferences"]["windowSize"]["x"])
        y = string.atoi(self._prefs["preferences"]["windowSize"]["y"])
        if x == -1 or y == -1:
            x = wxSystemSettings_GetMetric(wxSYS_SCREEN_X)
            x = x * DEFAULT_X_PERCENTAGE
            y = wxSystemSettings_GetMetric(wxSYS_SCREEN_Y)
            y = y * DEFAULT_Y_PERCENTAGE                        
        self.SetWindowSize((x, y))
                    
    def SetWindowSize(self, size):
        """Sets the default size for a new ChandlerWindow."""
        self._windowSize = size
        
    def __SavePrefs(self):
        """Saves the preferences out to an xml file."""
        self._reader.OutputXmlFile(PREFS_LOCATION, self._prefs)
    
    def __GetComponentList(self):
        """Gets a list of each of the components for Chandler.  Among other
        things, this will include the email, calendar, and contacts
        components.  In order for a component to be successfully loaded, it
        must have it's own folder in the components directory of Chandler, 
        that folder must contain an __init__.py file, and it must have a file
        that subclasses Component and is named the same as the package name,
        but with a capitalized first letter.

        Returns a list of tuples, with each tuple containing the information
        necessary to load a single component.  The first item in the tuple is
        the name of the class that subclasses ComponentLoader and the second
        item is the path to that component."""
        sys.path.append(COMPONENTS_DIRECTORY)
        componentDirectory = os.listdir(COMPONENTS_DIRECTORY)

        componentStrings = []
        for package in componentDirectory:
            if package != 'CVS':
                componentName = string.capwords(package)
                path = package + '.' + componentName
                componentStrings.append((componentName, path))
        return componentStrings    
    
    def OpenNewViewer(self, location):
        """Create a new ChandlerWindow and add it to the list of open
        windows.  Offsets the new window slightly so that they are not
        directly overlayed."""
        location.x += NEW_WINDOW_DELTA_X
        location.y += NEW_WINDOW_DELTA_Y
        frame = ChandlerWindow(None, self,  self._componentStrings, 
                               size = self._windowSize, pos = location)
        self._frames.append(frame)
        frame.Show(true)    
        
    def RemoveWindow(self, win):
        """Remove the window from the list of open windows.  Should only be
        called right before the window is closed."""
        self._frames.remove(win)
        # If it is the last open frame, then we output the prefences
        # to a file.
        if len(self._frames) == 0:
            self.__SavePrefs()

    def QuitApp(self):
        """Quit the application by closing all open windows."""
        windowsToClose = self._frames[:]
        for frame in windowsToClose:
             frame.Close(true)

if __name__=="__main__":
    app = osafApp()
    app.MainLoop()

