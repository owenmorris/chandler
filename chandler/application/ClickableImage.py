__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


import os
from wxPython.wx import *

class ClickableImage(wxStaticBitmap):
    def __init__(self, parent, imgLocation, onClickMethod, userData):
        """Creates the wxStaticBitmap, stores the appropriate method
        and userData to be passed to that method, and sets up a handler
        for the click event"""
        osLocation = apply(os.path.join, tuple(imgLocation.split('/')))
        img = wxImage(osLocation, wxBITMAP_TYPE_GIF).ConvertToBitmap()
        wxStaticBitmap.__init__(self, parent, -1, img, wxPoint(0, 0), 
                                wxSize(img.GetWidth(), img.GetHeight()))

        self.OnClickMethod = onClickMethod
        self.userData = userData

        EVT_LEFT_DOWN(self, self.OnClick)
        
    def OnClick(self, event):
        """When the ClickableImage receives a left down event, this
        method is called which simply passes the userData to the
        appropriate method."""
        self.OnClickMethod(self.userData)
        
        
