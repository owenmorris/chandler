""" Table View (one of the view types of the Calendar View Parcel)

    wxGrid implementation, may use superwidget when it exists.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.gizmos import *

from mx import DateTime

from persistence import Persistent

from application.Application import app

from OSAF.calendar.CalendarEvents import *

class TableViewer(Persistent):
    def __init__(self, calendarViewer):
        self.xrcClass = "wxPanel"
        self.xrcName = "TableViewer"
        self.displayName = _(" View Table ")
        
        self.calendarViewer = calendarViewer
        
        self.rangeIncrement = DateTime.RelativeDateTime(months=1)
        self.updateRange(DateTime.today())
        
    def UpdateItems(self):
        viewer = app.association[id(self)]
        viewer._loadEvents()
        viewer._displayEvents()
        viewer.Refresh()
        
    def SynchronizeView(self, view):
        view.OnInit(self)
        app.association[id(self)] = view
        
    def updateRange(self, date):
        self.rangeStart = DateTime.DateTime(date.year, date.month)
        
    def incrementRange(self):
        self.rangeStart += self.rangeIncrement
        
    def decrementRange(self):
        self.rangeStart -= self.rangeIncrement
        
    def isDateInRange(self, date):
        # @@@ Perhaps a general utility?
        begin = self.rangeStart
        end = begin + self.rangeIncrement
        return ((date > begin) and (date < end))

class wxTableViewer(wxPanel):
    def __init__(self):
        value = wxPrePanel()
        self.this = value.this
        self._setOORInfo(self)
        
    def OnInit(self, model):
        self.model = model

        self.list = wxListCtrl(self, style=wxLC_REPORT)
        self.list.InsertColumn(0, _('Headline'))
        self.list.InsertColumn(1, _('Start Time'))
        self.list.InsertColumn(2, _('Duration'))
        
        self._loadEvents()
        self._displayEvents()
        
        EVT_SIZE(self, self.OnSize)
        EVT_CALENDAR_DATE(self, self.OnCalendarDate)
        
    def _columnSorter(self, key1, key2):
        return key1 > key2
        
    def _loadEvents(self):
        self.eventList = []
        for item in app.repository.find("//Calendar"):
            self.eventList.append(item)
        
    def _displayEvents(self):
        self.list.DeleteAllItems()
        index = 0;
        for item in self.eventList:
            if (self.model.isDateInRange(item.startTime)):
                if (item.duration.hours > 1):
                    hourString = "%s hours" % item.duration.hours
                elif (item.duration.hours < 1):
                    hourString = "%d minutes" % item.duration.minutes
                else:
                    hourString = "1 hour"
                startString = item.startTime.Format('%x %I:%M %p')
                self.list.InsertStringItem(index, item.headline)
                self.list.SetStringItem(index, 1, startString)
                self.list.SetStringItem(index, 2, hourString)
                self.list.SetItemData(index, item.startTime)
                index = index + 1
        self.list.SortItems(self._columnSorter)
        
    def OnSize(self, event):
        self.list.SetSize(self.GetClientSize())
                
    def OnCalendarDate(self, event):
        self._loadEvents()
        self._displayEvents()
        self.Refresh()
        event.Skip()
        
    def UpdateDisplay(self):
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
        rangeString = start.Format("%B, %Y")
        return rangeString
    
    def getRangeDate(self):
        start = self.model.rangeStart
        wx_start = wxDateTimeFromDMY(start.day, start.month - 1, start.year)
        return wx_start
    
    def getRange(self):
        return (self.model.rangeStart,
                self.model.rangeStart + self.model.rangeIncrement)
