#!bin/env python

"""The chandler application.  The application itself simply tracks open
ChandlerWindows."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"


from wxPython.wx import *
from wxPython.xrc import *


from application.ChandlerWindow import ChandlerWindow

class osafApp(wxApp):
    def OnInit(self):
        wxInitAllImageHandlers()
        self.frame = ChandlerWindow(None, self, pos=wxPoint(20,20))
#        self.frames = [frame]
        self.frame.Show(true)
        
        return true

#    def OpenNewViewer(self, location):
#        """Create a new ChandlerWindow and add it to the list of open windows.
#        Offsets the new window slightly so that they are not directly overlayed."""
#        location.x += 40
#        location.y += 40
#        frame = ChandlerWindow(None, self, self.components, pos=location)
#        self.frames.append(frame)
#        frame.Show(true)    
        
#    def RemoveWindow(self, win):
#        """Remove the window from the list of open windows.  Should only be called
#        right before the window is closed."""
#        self.frames.remove(win)        

    def QuitApp(self):
        self.frame.Close(true)
#        """Quit the application by closing all open windows."""
#        windowsToClose = []
#        # Make a copy of self.frames because it will change as we close
#        #  individual windows
#        for frame in self.frames:
#            windowsToClose.append(frame)
#        for frame in windowsToClose:
#             frame.Close(true)

if __name__=="__main__":
    app = osafApp(1)
    app.MainLoop()

