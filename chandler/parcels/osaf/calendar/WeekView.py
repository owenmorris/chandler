""" Week View (one of the view types of the Calendar View Parcel)

    Placeholder, not implemented yet.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from mx import DateTime

class WeekView:
    def __init__(self):
        pass
    
    def SynchronizeView(self, view):
        pass
    
class wxWeekView(wxPanel):
    def __init__(self):
        value = wxPrePanel()
        self.this = value.this
        self._setOORInfo(self)
        
    def OnInit(self):
        pass