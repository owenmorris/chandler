""" Calendar Viewer Parcel Events
"""

__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *

# @@@ Create a better name: need a namespace? for calendar and for chandler?
# @@@ Figure out how to deal with label and range

wxEVT_CALENDAR_DATE = wxNewEventType()

def EVT_CALENDAR_DATE(window, function):
    """The date range displayed by the calendar viewer changed"""
    window.Connect(-1, -1, wxEVT_CALENDAR_DATE, function)
    
class CalendarDateEvent(wxPyCommandEvent):
    def __init__(self, windowId):
        wxPyCommandEvent.__init__(self, wxEVT_CALENDAR_DATE, windowId)
        
    def Clone(self):
        self.__class__(self.GetId())
        
        
