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

import sys
import os

STARTING_X_POS = 20
STARTING_Y_POS = 20
NEW_WINDOW_DELTA_X = 40
NEW_WINDOW_DELTA_Y = 40
COMPONENTS_DIRECTORY = "./components"

class osafApp(wxApp):
    def OnInit(self):
        """Does basic housecleaning setup.  Gets a list of all of the
        available  components and creates a ChandlerWindow."""
        wxInitAllImageHandlers()
        self.componentStrings = self.__GetComponentList()
        frame = ChandlerWindow(None, self, self.componentStrings, 
                               pos = wxPoint(STARTING_X_POS, STARTING_Y_POS))
        self.frames = [frame]
        frame.Show(true)
        
        return true

    def __GetComponentList(self):
        """Gets a list of each of the components for Chandler.  Among other
        things, this will include the email, calendar, and contacts
        components.  In order for a component to be successfully loaded, it
        must have it's own folder in the components directory of Chandler, 
        that folder must contain an __init__.py file, and it must have a file
        that subclasses ComponentLoader and is named 'Foldername'Loader.py.

        Returns a list of tuples, with each tuple containing the information
        necessary to load a single component.  The first item in the tuple is
        the name of the class that subclasses ComponentLoader and the second
        item is the path to that component."""
        sys.path.append(COMPONENTS_DIRECTORY)
        componentDirectory = os.listdir(COMPONENTS_DIRECTORY)

        componentStrings = []
        for package in componentDirectory:
            if package != 'CVS':                
                loaderName = string.capwords(package) + 'Loader'
                path = package + '.' + loaderName
                componentStrings.append((loaderName, path))
        return componentStrings    
    
    def OpenNewViewer(self, location):
        """Create a new ChandlerWindow and add it to the list of open
        windows.  Offsets the new window slightly so that they are not
        directly overlayed."""
        location.x += NEW_WINDOW_DELTA_X
        location.y += NEW_WINDOW_DELTA_Y
        frame = ChandlerWindow(None, self,  self.componentStrings, pos = location)
        self.frames.append(frame)
        frame.Show(true)    
        
    def RemoveWindow(self, win):
        """Remove the window from the list of open windows.  Should only be
        called right before the window is closed."""
        self.frames.remove(win)        

    def QuitApp(self):
        """Quit the application by closing all open windows."""
        windowsToClose = []
        # Make a copy of self.frames because it will change as we close
        #  individual windows
        for frame in self.frames:
            windowsToClose.append(frame)
        for frame in windowsToClose:
             frame.Close(true)

if __name__=="__main__":
    app = osafApp()
    app.MainLoop()

