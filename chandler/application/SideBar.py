__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"


from wxPython.wx import *
from application.Application import app
from Persistence import Persistent, PersistentDict


class SideBar(Persistent):
    """
      SideBar is the side bar in the ChandlerWindow and is the model
    counterpart of the wxSideBar view object (see below)..
    """
    def __init__(self):
        """
          sideBarURLTree is the subset of the app.model.URLTree visible in ChandlerWindow.
        """
        self.sideBarURLTree = PersistentDict.PersistentDict()
        
    def SynchronizeView(self):
        """
          Notifies the window's wxPython counterpart that they need to
        synchronize themselves to match their peristent model counterpart.
        Whenever the application's URLTree is changed, the sidebar is
        notified with the SynchronizeView to update the sideBarURLTree
        to reflect changes
        """
        if not app.association.has_key(id(self)):
            wxWindow = wxSideBar ()
            app.association[id(self)] = wxSideBar ()
            wxWindow.OnInit (self)
        else:
            wxWindow = app.association[id(self)]
        
        # Add code here to recurse through sideBarURLTree and app.model.URLTree
        # to update for any changes.


class wxSideBar(wxTreeCtrl):
    def __init__(self):
        """
          wxSideBar is the view counterpart to SideBar. Wire up the wxWindows
        object behind the wxPython object. wxPreFrame creates the wxWindows
        C++ object, which is stored in the this member. _setOORInfo store a
        back pointer in the C++ object to the wxPython object.
        """
        value = wxPreTreeCtrl ()
        self.this = value.this
        self._setOORInfo (self)
        """
          Check to see if we've already created the persistent counterpart,
        if not create it, otherwise get it. Finally add it to the association.
        """
        if not app.model.mainFrame.__dict__.has_key('SideBar'):
            self.model = SideBar()
            app.model.mainFrame.SideBar = self.model
        else:
            self.model = app.model.mainFrame.SideBar
        """
           The model persists, so it can't store a reference to self, which
        is a wxApp object. We use the association to keep track of the
        wxPython object associated with each persistent object.
        """
        app.association[id(self.model)] = self
        """
           There isn't a EVT_DESTROY function, so we'll implement it do
        what the function would have done.
        """
        EVT_WINDOW_DESTROY (self, self.OnDestroy)

    def OnDestroy(self, event):
        """
          Remove from the association when the sidebar is destroyed.
        """
        del app.association[id(self.model)]
    
     