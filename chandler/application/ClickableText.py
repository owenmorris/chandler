__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *

class ClickableText(wxStaticText):
    def __init__(self, parent, text, onClickMethod, userData, id = -1):
        """Creates the wxStaticText, stores the appropriate method
        and userData to be passed to that method, and sets up a handler
        for the click event."""
        wxStaticText.__init__(self, parent, id, text)
        
        self.OnClickMethod = onClickMethod
        self.userData = userData

        EVT_LEFT_DOWN(self, self.OnClick)
        
    def OnClick(self, event):
        """When the ClickableText receives a left down event, this
        method is called which simply passes the userData to the
        appropriate method."""
        self.OnClickMethod(self.userData)

            