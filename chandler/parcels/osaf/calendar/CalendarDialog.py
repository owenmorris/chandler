""" Calendar date picker and dialog.

    @@@ Uses wxCalendarCtrl. We may want to use wxCalendar,
        or write our own.
"""

__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.calendar import *
from wxPython.wx import *
from wxPython.xrc import *

# @@@ part of a hack to get wxCalendarCtrl to work with xrc
wx.wxCalendarCtrlPtr = wxCalendarCtrlPtr

class wxCalendarDialog(wxDialogPtr):
    def __init__(self, parent, date, resources):
        dialog = resources.LoadDialog(parent, 'CalendarCtrlDialog')
        wxDialogPtr.__init__(self, dialog.this)
        self.thisown = 1
        self.Center()
        self.calendar = self.FindWindowByName('CalendarCtrl')
        self.calendar.SetDate(date)
        self.SetAutoLayout(true)
        self.GetSizer().Fit(self)
        
    def GetSelectedDate(self):
        return self.calendar.GetDate()
        