__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"

"""The parent class that must be subclassed to create a Chandler
parcel viewer.
"""

import new, types
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
        """
        module = theClass.__module__
        if not app.model.URLTree.has_key(module):
            if type (theClass) == types.ClassType:
                instance = new.instance (theClass, {})
            else:
                instance = theClass.__new__ (theClass)
            instance.__init__()
            app.model.URLTree[module] = instance
        
    Install = classmethod (Install)

    def synchronizeView (self):
        pass
    
        #name1  = wxTextCtrl(wxWindow, -1, '', wxPoint(50, 10), wxSize(100, -1))
        #app.applicationResources.AttachUnknownControl ("ViewerParcel", name1)

        #name2  = wxTextCtrl(wxWindow, -1, '', wxPoint(50, 10), wxSize(100, -1))
        #app.applicationResources.AttachUnknownControl ("ViewerParcel", name2)
