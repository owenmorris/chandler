#!bin/env python

"""The Chandler application.  First loads the persistence dictionary and
then tells the window manager to send a Notify message to each of its
windows.  From there it just begins the main application loop."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from application.persist.Persist import Storage
from application.WindowManager import WindowManager


class osafApp(wxApp):
    def OnInit(self):
        """Does basic housecleaning setup.  Gets a list of all of the
        available  components and creates a ChandlerWindow."""
        wxInitAllImageHandlers()   
        self.__InitDatabase()
        self._windowManager.NotifyAllWindows()

        return true

    def __InitDatabase(self):
        """Sets up the persistence dictionary so that we can resume the 
        state that we were in when we quit.  The main thing that we are
        persisting for now is the window manager.  It has references to 
        any windows that had been open."""
        self._storage = Storage("_CHANDLER_APP_")
        # This section should use a more clean wrapper to ZODB, but the
        # current one (Persist.persist) causes a new windowManager to be
        # allocated even if there was one persisted.  This has unwanted 
        # side effects.  The persistence API will be changing, and once 
        # it does, this should use the new method.
        if not self._storage.dbroot.has_key('windowManager'):
            self._windowManager = WindowManager()
            self._storage.dbroot['windowManager'] = self._windowManager
        else:
            self._windowManager = self._storage.dbroot['windowManager']
            
        # We want to commit here, but if we do, later commits are ignored.
        # This is a result of ZODB not realizing that the class
        # has changed and thus not writing it to disk after the second
        # commit.
        #self._storage.commit("Storing window manager")
    

if __name__=="__main__":
    storage = Storage("_CHANDLER_APP_")
    
    app = osafApp()
    app.MainLoop()
    # This doesn't belong here, but due to the commit problem we are having
    # with ZODB, we must commit only once when the application is quiting
    # Begin
    app._storage.commit("End of application")
    app._storage.close()
    # End
