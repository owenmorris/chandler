""" Columnar View (one of the view types of the Calendar View Parcel)
    Similar to the 'week view' or 'work week view' in other calendars, this
    view is meant to display calendar data by day and time of day. The days
    are aligned in columns, and the vertical axis is the time of day. Note
    that the 'day view' also uses this class, but only one column is used.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.xrc import *

from mx import DateTime
from persistence.dict import PersistentDict
from persistence import Persistent

from application.Application import app

from parcels.OSAF.calendar.ColumnarHeadView import ColumnarHeadView
from parcels.OSAF.calendar.ColumnarTimeView import ColumnarTimeView
from parcels.OSAF.calendar.ColumnarFootView import ColumnarFootView

from parcels.OSAF.calendar.CalendarEvents import *

# @@@ Note, lots in common with MonthViewer, perhaps create a common
#     superclass

class ColumnarViewer(Persistent):
    def __init__(self, calendarView):
        self.xrcClass = "wxPanel"
        self.xrcName = "ColumnarViewer"
        self.displayName = _(" View Week ")
        self.calendarView = calendarView
        
        self.daysPerView = 7
        self.hoursPerView = 24
        
        self.offset = 40
        
        # @@@ not sure how/if this should be initialized
        #     read from xrc, prefs, etc.
        self.viewWidth = 500
        
        self.rangeIncrement = DateTime.RelativeDateTime(days=7)
        self.updateRange(DateTime.today())
        self._initSubViews()
        
    def _initSubViews(self):
        # @@@ create the models for the subviews
        self.headModel = ColumnarHeadView(self)
        self.timeModel = ColumnarTimeView(self)
        self.footModel = ColumnarFootView(self)
        
    def SynchronizeView(self, view):
        view.OnInit(self)

        view.headView = self._syncSubView(view, self.headModel)
        view.timeView = self._syncSubView(view, self.timeModel)
        view.footView = self._syncSubView(view, self.footModel)
        
    def _syncSubView(self, view, subViewModel):
        """Find the view for this model, and sync them up.
           The subViews observe the parent view: they will be notified
           when the date changes.
        """
        subView = XRCCTRL(view, subViewModel.xrcName)
        subViewModel.SynchronizeView(subView)
        app.association[id(subViewModel)] = subView
        return subView
        
   # UpdateItems is called when the view changes; tell the model to reload the events
    def UpdateItems(self):
        self.timeModel.UpdateItems()

    # Methods for changing the model
        
    def updateRange(self, date):
        delta = DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))
        self.rangeStart = date + delta
        
    def incrementRange(self):
        self.rangeStart += self.rangeIncrement
        
    def decrementRange(self):
        self.rangeStart -= self.rangeIncrement
        
    # receive remote objects by passing the call on to the time model
    def AddObjectsToView(self, url, objectList, lastFlag):
            self.timeModel.AddObjectsToView(url, objectList, lastFlag)

    # Methods for looking at the model

    def getRangeEnd(self):
        return self.rangeStart + DateTime.RelativeDateTime(days=6)
        
    def getDayWidth(self):
        return (self.viewWidth - self.offset)/self.daysPerView

    dayWidth = property(getDayWidth)
    rangeEnd = property(getRangeEnd)
    
class wxColumnarViewer(wxPanel):
    def __init__(self):
        value = wxPrePanel()
        self.this = value.this
        self._setOORInfo(self)
        
    def OnInit(self, model):
        self.model = model

        # Only bind erase background on Windows for flicker reasons
        if wxPlatform == '__WXMSW__':
            EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)
            
        EVT_CALENDAR_DATE(self, self.OnCalendarDate)
            
    # Handle events        
        
    def OnEraseBackground(self, event):
        pass
    
    def OnCalendarDate(self, event):
        """ In response to a date change event, all sub-views
            need to change the date range.
        """
        self.headView.UpdateDateRange()
        self.timeView.UpdateDateRange()
        self.footView.UpdateDateRange()
        event.Skip()
    
    # Update methods, usually called by event handlers to update the view.
        
    def UpdateColumnarWidth(self, viewWidth):
        """ Change the width, called when resizing the view.
            The timeView actually notices the size event: its width
            determines the weekWidth, etc.
        """
        self.model.viewWidth = viewWidth
        self.headView.UpdateSize()
        self.timeView.UpdateSize()
        self.footView.UpdateSize()

        #@@@ For Bug#421 on the mac
        self.Refresh()
        
    def UpdateDisplay(self):
        """ Update the display. Before doing a refresh, update bounds.
        """
        self.timeView.UpdateSize()
        self.Refresh()
        
    # Navigation methods, these methods cause the date range
    # to be changed. The model is changed, and wxPython events
    # are fired off for notification.
    
    def DecrementDateRange(self):
        self.model.decrementRange()
        newEvent = CalendarDateEvent(self.GetId())
        self.GetEventHandler().ProcessEvent(newEvent)
        
    def IncrementDateRange(self):
        self.model.incrementRange()
        newEvent = CalendarDateEvent(self.GetId())
        self.GetEventHandler().ProcessEvent(newEvent)
        
    def ChangeDateRange(self, date):
        self.model.updateRange(date)
        newEvent = CalendarDateEvent(self.GetId())
        self.GetEventHandler().ProcessEvent(newEvent)
    
    # Methods to ask the view for information
        
    def getRangeString(self):
        start = self.model.rangeStart
        end = self.model.rangeEnd
        rangeString = start.Format("%B %d - ") + end.Format("%d, %Y")
        return rangeString
    
    def getRangeDate(self):
        start = self.model.rangeStart
        wx_start = wxDateTimeFromDMY(start.day, start.month - 1, start.year)
        return wx_start
    
    def getRange(self):
        return (self.model.rangeStart, self.model.rangeEnd)

