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

    def synchronizeView (self):
        wxMainFrame = app.association[id(app.model.mainFrame)]
        """
          If it isn't in the association we need to construct it and
        put it in the association.
        """
        if not app.association.has_key(id(self)):
            module = sys.modules[self.__class__.__module__]
            modulename = os.path.basename (module.__file__)
            modulename = os.path.splitext (modulename)[0]
            path = os.sep.join(module.__name__.split("."))
            path = path + ".xrc"

            """
              ViewerParcels must have a resource file with the same name as the
            module with an .xrc extension
            """
            assert (os.path.exists (path))
            resources = wxXmlResource(path)
            panel = resources.LoadObject(wxMainFrame, modulename, "wxPanel")
            assert (panel != None)
            
            app.association[id(self)] = panel
            """
              Set up model and resources for the convience of the parcel.
            OnInit gives the parcel a chance to wire up their events.
            """
            panel.model = self
            panel.resources = resources
            panel.OnInit ()
        else:
            panel = app.association[id(self)]
        """
          We'll check to see if we've got a parcel installed in the view, and
        if so we'll remove it from the association and destroy it. Shortcut
        the case of setting the same window we've already set.
        """
        container = wxMainFrame.FindWindowByName("ViewerParcel_container")
        children = container.GetChildren ()
        if len (children) == 0 or children[0] != panel:
            for window in children:
                if window.__dict__.has_key("model"):
                    del app.association[id(window.model)]
            container.DestroyChildren ()
            """
              Attach the new parcel to the view.
            """
            app.applicationResources.AttachUnknownControl("ViewerParcel", panel)

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


