__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"

"""The parent class that must be subclassed to create a Chandler
parcel viewer.
"""

import new, types, exceptions, sys, os
from wxPython.wx import *
from wxPython.xrc import *
from application.Parcel import Parcel
from application.Application import app

class ViewerParcel (Parcel):
    """
      The ViewerParcel set's up the following data for the parcel's use:

    self.path                      the path to the parcel directory
    
      And stores the with the non-persistent counterpart:

    counterpart.model              the persistent counterpart
    counterpart.resources          the model's resources
    
      To create a parcel you'll subclass ViewerParcel, and currently
    it's not necessary to call the superclass's __init__.
    """
    def Install(theClass):
        """
          The class method that is used to install the parcel Viewer. Check
        to see if we've been installed into the URLTree, and if not install.
        Classes may be "old style" (type (theClass) == types.ClassType) or
        "new style". The construction method is different in each case: see
        below.
          Currently we install by appending to the end of the list
        """
        found = false
        for parcel in app.model.URLTree:
            if parcel.__module__ == theClass.__module__:
                found = true
                break
            
        if not found:
            if type (theClass) == types.ClassType:
                instance = new.instance (theClass, {})
            else:
                instance = theClass.__new__ (theClass)
            instance.__init__()
            app.model.URLTree.append (instance)
        
    Install = classmethod (Install)

    def SynchronizeView (self):
        """
          If it isn't in the association we need to construct it and
        put it in the association.
        """
        container = app.wxMainFrame.FindWindowByName("ViewerParcel_container")
        if not app.association.has_key(id(self)):
            module = sys.modules[self.__class__.__module__]
            modulename = os.path.basename (module.__file__)
            modulename = os.path.splitext (modulename)[0]
            path = os.sep.join(module.__name__.split("."))
            path = path + ".xrc"

            """
              ViewerParcels must have a resource file with the same name as the
            module with an .xrc extension. We'll freeze the app.wxMainFrame
            while adding the panel, since it's temporarily owned by app.wxMainFrame
            and would otherwise cause it to be temporarily displayed on the screen
            """
            assert (os.path.exists (path))
            resources = wxXmlResource(path)
            app.wxMainFrame.Freeze ()
            panel = resources.LoadObject(app.wxMainFrame, modulename, "wxPanel")
            panel.Show (FALSE)
            app.wxMainFrame.Thaw ()
            assert (panel != None)
            
            app.association[id(self)] = panel
            panel.Setup(self, resources)

        else:
            panel = app.association[id(self)]
        """
          We'll check to see if we've got a parcel installed in the view, and
        if so we'll remove it from the association and destroy it. Only windows
        with the attribute "model" are removed from the association since on the
        Mac there are some extra scrollbars added below the viewer parcel
        container. Shortcut the case of setting the same window we've already set.
        """
        container = app.wxMainFrame.FindWindowByName("ViewerParcel_container")
        children = container.GetChildren ()
        if len (children) == 0 or children[0] != panel:
            for window in children:
                if hasattr (window, "model"):
                    app.association[id(window.model)].Deactivate()
                    del app.association[id(window.model)]
            container.DestroyChildren ()
            """
              Attach the new parcel to the view. Don't forget to show the panel
            which was temporarily hidden
            """
            app.applicationResources.AttachUnknownControl("ViewerParcel", panel)
            panel.Activate()
            panel.Show ()

class wxViewerParcel(wxPanel):
    def __init__(self):
        """
          There is a little magic incantation provided by Robin Dunn here
        to wire up the wxWindows object behind the wxPython object.
        wxPreFrame creates the wxWindows C++ object, which is stored
        in the this member. _setOORInfo store a back pointer in the C++
        object to the wxPython object.
          If you override __init__ don't forget to call the superclass.
        """
        value = wxPrePanel()
        self.this = value.this
        self._setOORInfo(self)

    def Setup(self, model, resources):
        """
          Set up model and resources for the convience of the parcel.
        OnInit gives the parcel a chance to wire up their events.
        """
        self.model = model
        self.resources = resources
        self.OnInit()

    def Activate(self):
        """
          Override to do tasks that need to happen just before your parcel is
        displayed.
        """
        self.addViewParcelMenu ()
    
    def Deactivate(self):
        """
          Override to do tasks that need to happen just before your parcel is
        replaced with anoter.
        """
        self.RemoveViewParcelMenu ()
    
    def GetMenuName(self):
        """
          Override to customize your parcel menu name.
        """
        return (self.model.displayName)

    def RemoveViewParcelMenu(self):
        """
          Override to customize your parcel menu.
        """
        menuBar = app.association[id(app.model.mainFrame)].GetMenuBar ()
        index = menuBar.FindMenu (self.GetMenuName())
        if index != wxNOT_FOUND:
            oldMenu = menuBar.Remove (index)
            del oldMenu

    def addViewParcelMenu(self):
        """
          Override to customize your parcel menu.
        """
        ignoreErrors = wxLogNull ()
        viewerParcelMenu = self.resources.LoadMenu ('ViewerParcelMenu')
        del ignoreErrors
        if (viewerParcelMenu != None):
            menuBar = app.association[id(app.model.mainFrame)].GetMenuBar ()
            index = menuBar.FindMenu (_('View'))
            assert (index != wxNOT_FOUND)
            menuBar.Insert (index + 1, viewerParcelMenu, self.GetMenuName())
            