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
        if not app.association.has_key(id(self)):
            module = sys.modules[self.__class__.__module__]
            basename = os.path.basename (module.__file__)
            basename = os.path.splitext (basename)[0]
            path = self.path + os.sep + basename + ".xrc"
            """
              ViewerParcels must have a resource file named parcel.xrc
            """
            assert (os.path.exists (path))
            resources = wxXmlResource(path)
            wxMainFrame = app.association[id(app.model.mainFrame)]
            panel = resources.LoadObject(wxMainFrame, "CalendarView", "wxPanel")
            app.applicationResources.AttachUnknownControl ("ViewerParcel", panel)
            panel.model = self
            panel.OnInit ()
            panel.Layout()
