#!bin/env python

"""This class is the data layer of the main window which represents
the Chandler application.  A ChandlerWindow contains all of the appropriate
navigation elements along with a main display area representing the current
view.  This data piece of a window is what gets persisted.  When the actual
wx layer is requested, we see if we already have one laying around, and if
not, create one."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from wxPython.wx import *

from persist.Persist import Persistent
from wxChandlerWindow import wxChandlerWindow
from ComponentInterface import ComponentInterface

class ChandlerWindow(Persistent):
    def __init__(self, parent, windowManager, componentStrings, id = -1, 
                 title = "Chandler", pos = (-1, -1), size = (-1, -1)):
        """Sets up the data associated with a ChandlerWindow."""
        self._parent = parent
        self._windowManager = windowManager
        self._componentStrings = componentStrings
        self._id = id
        self._title = title
        self._pos = pos
        self._size = size
        self.componentInterface = ComponentInterface(self)
        self._wxWindow = None

    def Notify(self):
        """Called whenever a window should respond to an action.  Notify will
        cause the window to look at its data and figure out if anything needs
        to be done (i.e. redraw part of the window)."""
        # Not yet implemented.
        # What is here is just a stub.  Eventually Notify will do much more
        # than just showing the window
        try:
            self._wxWindow.Show(true)
        except:
            self._wxWindow = wxChandlerWindow(self._parent,
                                              self,
                                              self._componentStrings,
                                              self._id,
                                              self._title,
                                              self._pos,
                                              self._size)
            a = self._pos
            self._wxWindow.Show(true)

                    
    def MenuNewEvent(self):
        """Called when the new window menu item has been selected.  Tells the
        window manager to create a new window."""
        self._windowManager.NewWindow()
        
    def MenuQuitEvent(self):
        """Called when the quit menu item has been selected.  Tells the
        window manager to quit the application by closing all open 
        windows."""
        self._windowManager.QuitApp()

    def OnSize(self, event):
        """Called whenever this window is resized.  We just store the size
        of the window in case we ever have to recreate the wx layer (for 
        example, after quitting and restarting)."""
        self._size = self._wxWindow.GetSizeTuple()
        self._windowManager.SetSize(self._size)
        event.Skip()
        
    def OnMove(self, event):
        """Called whenever this window is moved.  We just store the position
        of the window in case we ever have to recreate the wx layer (for 
        example, after quiting and restarting)."""
        self._pos = self._wxWindow.GetPositionTuple()
        event.Skip()

    def OnClose(self, event):
        """Called whenever this window is to be closed.  First, we remove
        ourself from the list of open windows, then we send a close message
        to the wxChandlerWindow so that the wx objects can be cleaned."""
        self._windowManager.RemoveWindow(self)
        self._wxWindow.OnClose()
        self._wxWindow = None
        
    def OnQuit(self):
        """Called whenever the app is quiting.  We send a close message to 
        the wxChandlerWindow so that the wx objects can be cleaned up and
        we erase our reference to it, since the wx layer will not be 
        persisted."""
        self._wxWindow.OnClose()
        self._wxWindow = None
        
    def GoToUri(self, uri, doAddToHistory = true):
        """Navigates this window to the supplied uri.  If doAddToHistory
        is true, then we add the uri to the history list (we won't want
        to add it if GoToUri is a result of the back button having been
        pressed)."""
        self._wxWindow.GoToUri(uri, doAddToHistory)
