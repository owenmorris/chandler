""" Month Navigator, one way of navigating through time in
    the calendar parcel. Provides one or more small month
    views. The user can change the date range of other local
    views by the selection in the Month Navigator.
    
    @@@ Currently using wxCalendarCtrl as the base for the
    Month Navigator, I expect that we'll want to write our
    own control. Alternatively, we might want to start with
    wxPython's wxCalendar.
    
    @@@ Known problems: 
    + If the selected range is on a week with a month boundary, 
      the-right-thing(tm) doesn't happen. We're not going to 
      spend a lot of energy on the problem until we figure out 
      our plan for the month navigator widget.
    + Looks pretty ugly, some platforms more so than others.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.calendar import *
from wxPython.wx import *
from wxPython.xrc import *

from persistence import Persistent

from parcels.OSAF.calendar.CalendarEvents import *

from mx import DateTime

class MonthNavigator(Persistent):
    def __init__(self):
        pass
        
    def SynchronizeView(self, view):
        view.OnInit(self)
        

class wxMonthNavigator(wxCalendarCtrl):
    def __init__(self):
        value = wxPreCalendarCtrl()
        self.this = value.this
        self._setOORInfo(self)
        
    def OnInit(self, model):
        self.model = model
        self.SetWindowStyle(wxCAL_SUNDAY_FIRST | 
                            wxCAL_SHOW_SURROUNDING_WEEKS)
        
        EVT_CALENDAR_DATE(self.GetParent(), self.OnCalendarDate)
        
    def OnCalendarDate(self, event):
        event.Skip()
        
    def GetSelectedDate(self):
        wxdate = self.GetDate()
        mxdate = DateTime.DateTime(wxdate.GetYear(),
                                   wxdate.GetMonth() + 1,
                                   wxdate.GetDay())
        return mxdate
    
    def SetSelectedDate(self, mxdate):
        wxdate = wxDateTimeFromDMY(mxdate.day, 
                                   mxdate.month -1,
                                   mxdate.year)
        self.SetDate(wxdate)
        
    def SetSelectedDateRange(self, mxstart, mxend):
        self.ResetMonth()
        self.SetSelectedDate(mxstart)
        
        if (mxstart.month != mxend.month):
            endday = mxstart.days_in_month + 1
        else:
            endday = mxend.day + 1
        
        for day in range(mxstart.day, endday):
            attr = wxCalendarDateAttr(wxWHITE, wxBLUE, wxWHITE, wxSWISS_FONT)
            self.SetAttr(day, attr)
            
        today = DateTime.today()
        if ((today.year == mxstart.year) and (today.month == mxstart.month)):
            self.SetHoliday(today.day)
            
        self.Refresh()
    
    def ResetMonth(self):
        for day in range(1,32):
            self.ResetAttr(day)
         
        