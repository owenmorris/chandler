""" Table View (one of the view types of the Calendar View Parcel)

    wxGrid implementation, may use superwidget when it exists.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.grid import *
from mx import DateTime

from persistence import Persistent

from application.Application import app
from application.repository.Repository import Repository
from application.repository.Namespace import chandler

from parcels.OSAF.calendar.CalendarEvents import *

class TableViewer(Persistent):
    def __init__(self, calendarViewer):
        self.xrcClass = "wxPanel"
        self.xrcName = "TableViewer"
        self.displayName = _(" View Table ")
        
        self.calendarViewer = calendarViewer
        
        self.rangeIncrement = DateTime.RelativeDateTime(months=1)
        self.updateRange(DateTime.today())
        
    def UpdateItems(self):
        pass
        
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
        self.grid = wxGrid(self, -1)
        
        self._loadEvents()
        
        self.grid.CreateGrid(100, 3)
        # self.grid.SetColLabelSize(0)
        self.grid.SetColLabelValue(0, _("Start Time"))
        self.grid.SetColLabelValue(1, _("End Time"))
        self.grid.SetColLabelValue(2, _("Headline"))
        self.grid.SetRowLabelSize(0)        
        self.grid.SetSize(self.GetClientSize())
        
        self._fillGrid()
        
        EVT_SIZE(self, self.OnSize)
        EVT_CALENDAR_DATE(self, self.OnCalendarDate)
        
    def _loadEvents(self):
        lr = Repository()
        self.eventList = []
        for item in lr.thingList:
            url = item.GetAkoURL()
            if (url == chandler.Event):
                self.eventList.append(item)
        
    def _fillGrid(self):
        self.grid.ClearGrid()
        index = 0
        for item in self.eventList:
            if (self.model.isDateInRange(item.startTime)):
                self.grid.SetCellValue(index, 0, str(item.startTime))
                self.grid.SetCellValue(index, 1, str(item.duration))
                self.grid.SetCellValue(index, 2, item.headline)
                index = index + 1
        
    def OnSize(self, event):
        self.grid.SetSize(self.GetClientSize())
        self.grid.SetDefaultColSize(self.GetSize().width/3, TRUE)
                
    def OnCalendarDate(self, event):
        # self._loadEvents()
        self._fillGrid()
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
        self = self.model.rangeStart
        wx_start = wxDateTimeFromDMY(start.day, start.month - 1, start.year)
        return wx_start
    
    def getRange(self):
        return (self.model.rangeStart,
                self.model.rangeStart + self.model.rangeIncrement)
