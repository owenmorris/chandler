""" Month View (one of the view types of the Calendar View Parcel)

    Minimal implementation, so that we can demonstrate how we change view types.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from mx import DateTime

from persistence.dict import PersistentDict
from persistence import Persistent

from application.Application import app

from application.SimpleCanvas import wxSimpleCanvas

from OSAF.calendar.CalendarEvents import *

# @@@ Note, lots in common with ColumnarViewer, perhaps create a common
#     superclass

class MonthViewer(Persistent):
    def __init__(self, calendarViewer):
        self.xrcClass = "wxScrolledWindow"
        self.xrcName = "MonthViewer"  
        self.displayName = _(" View Month ")
        
        self.calendarViewer = calendarViewer
        
        self.daysPerWeek = 7
        self.weeksPerView = 6
        self.offset = 20
        
        # @@@ set this correctly
        self.viewWidth = 500
        self.viewHeight = 500
        
        self.rangeIncrement = DateTime.RelativeDateTime(months=1)
        self.updateRange(DateTime.today())
        
    def SynchronizeView(self, view):
        view.OnInit(self)
        app.association[id(self)] = view
    
    # receive remote objects by passing it on to the wxColumnarTimeView that actually holds them
    def AddObjectsToView(self, url, objectList, lastFlag):
        viewer = app.association[id(self)]
        viewer.AddObjectsToView(url, objectList, lastFlag)

    def UpdateItems(self):
        viewer = app.association[id(self)]
        viewer._loadEvents()
        viewer.Refresh()
        
    # Methods for changing the model
        
    def updateRange(self, date):
        self.rangeStart = DateTime.DateTime(date.year, date.month)

    def incrementRange(self):
        self.rangeStart += self.rangeIncrement
        
    def decrementRange(self):
        self.rangeStart -= self.rangeIncrement
    
    # Methods for looking at the model
            
    def getDayWidth(self):
        return self.viewWidth / self.daysPerWeek
    
    def getDayHeight(self):
        return (self.viewHeight - self.offset) / self.weeksPerView
    
    dayWidth = property(getDayWidth)
    dayHeight = property(getDayHeight)
    
class wxMonthViewer(wxSimpleCanvas):
    def __init__(self):
        value = wxPreScrolledWindow()
        self.this = value.this
        self._setOORInfo(self)
        
    def OnInit(self, model):
        self.model = model
        self.eventList = []
        
        dataFormat = wxCustomDataFormat("ChandlerItem")
        dropTargetDataObject = wxCustomDataObject()
        wxSimpleCanvas.OnInit(self, dropTargetDataObject)

        self.SetScrollRate(0,0)
        
        self._loadEvents()
        
        EVT_SIZE(self, self.OnSize)
        EVT_CALENDAR_DATE(self, self.OnCalendarDate)
        
    def _loadEvents(self):
        remoteAddress = self.model.calendarViewer.remoteAddress
        overlay = self.model.calendarViewer.overlayRemoteItems
        
        if remoteAddress != None:
            if app.jabberClient.RequestRemoteObjects(remoteAddress, 'Calendar'):
                self.remoteLoadInProgress = true
            else:
                self.remoteLoadInProgress = false
                message = _("Sorry, but %s is not present!") % (remoteAddress)
                wxMessageBox(message)

        if remoteAddress == None or overlay:
            self.eventList = []
            for item in app.repository.find("//Calendar"):
                self.eventList.append(item)
        
    # receive remote objects by adding to the object list
    # redraw after the last one
    def AddObjectsToView(self, url, objectList, lastFlag):
         for item in objectList:
             self.eventList.append(item)
            
         if lastFlag:
             self.Refresh()
                
    # Handle events             
             
    def OnSize(self, event):
        newSize = event.GetSize()
        self.model.viewWidth = newSize.width
        self.model.viewHeight = newSize.height
        self.SetVirtualSize(newSize)
        event.Skip()

    def OnCalendarDate(self, event):
        self._loadEvents()
        self.Refresh()
        event.Skip()
        
    # Update methods, usually called by event handlers to update the view.

    def UpdateDisplay(self):
        """ Update the display, just do a redraw.
        """
        self.Refresh()
        
    # Canvas drawing methods
    
    def DrawBackground(self, dc):
        # Use the transparent pen for drawing the background rectangles
        dc.SetPen(wxTRANSPARENT_PEN)

        # @@@ temporary hack (ok, this whole method is a temporary hack!)
        #     paint the days square by square to overwrite the text
        #     overflow
        # Paint the entire background
        # dc.SetBrush(wxBrush(wxColour(246, 250, 254)))
        # dc.DrawRectangle(0, 0, self.model.viewWidth, self.model.viewHeight)
        
        # Set up the font (currently uses the same font for all text)
        dc.SetTextForeground(wxColour(63, 87, 119))
        dc.SetFont(wxFont(8, wxSWISS, wxNORMAL, wxBOLD))        

        # Determine the starting day for the set of weeks to be shown
        # The Sunday of the week containing the first day of the month
        startDay = self.model.rangeStart + \
                 DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))
        
        # Paint the header
        dc.SetBrush(wxBrush(wxColour(222, 231, 239)))
        dc.DrawRectangle(0, 0, self.model.viewWidth, self.model.offset)
        
        today = DateTime.today()
            
        # @@@ hack hack hack we'll move this to drawable objects
        # Draw each day, the headers and the events in the day (for now)
        dc.SetPen(wxTRANSPARENT_PEN)
        for week in range(self.model.weeksPerView):
            for day in range(self.model.daysPerWeek):
                currentDate = startDay + DateTime.RelativeDateTime(days=(week*7 + day))

                # Label the day, highlight today, give the day the right
                # background color based on the "range" month
                if (currentDate.month != self.model.rangeStart.month):
                    dc.SetBrush(wxBrush(wxColour(246, 250, 254)))
                else:
                    dc.SetBrush(wxBrush(wxColour(232, 241, 249)))
                    
                dc.DrawRectangle(self.model.dayWidth * day,
                                 self.model.dayHeight * week + self.model.offset,
                                 self.model.dayWidth, self.model.dayHeight)
                
                if (currentDate == today):
                    dc.SetTextForeground(wxRED)                    
                dc.DrawText(currentDate.Format("%d %b"), 
                            self.model.dayWidth * day + 10,
                            self.model.dayHeight * week + self.model.offset)
                if (currentDate == today):
                    dc.SetTextForeground(wxColour(63, 87, 119))                    
                
                # @@@ major hack, we'll do this differently
                self.DrawEventsForDate(dc, currentDate,
                                       self.model.dayWidth * day,
                                       self.model.dayHeight * week + self.model.offset)

        # Set the pen for drawing the month grid
        dc.SetPen(wxPen(wxColour(183, 183, 183)))
        
        # Draw vertical lines separating days and the names of the weekdays
        for i in range(self.model.daysPerWeek):
            weekday = startDay + DateTime.RelativeDateTime(days=i)
            dc.DrawText(weekday.Format('%A'), (self.model.dayWidth * i) + 10, 0)
            if (i != 0):
                dc.DrawLine(self.model.dayWidth * i, 0,
                            self.model.dayWidth * i, self.model.viewHeight)
        
        # Draw horizontal lines separating weeks
        for j in range(self.model.weeksPerView):
            dc.DrawLine(0, (j * self.model.dayHeight) + self.model.offset,
                        self.model.viewWidth, 
                        (j* self.model.dayHeight) + self.model.offset)
            

    def DrawEventsForDate(self, dc, date, x, y):
        """@@@ Hack helper method that walks all the events and displays the ones on this day.
           Inefficient indeed, more proof of concept.
        """
        dc.SetFont(wxFont(8, wxSWISS, wxNORMAL, wxNORMAL))
        dc.SetTextForeground(wxBLACK)
        dc.SetBackgroundMode(wxSOLID)
        nextDay = date + DateTime.RelativeDateTime(days=1)
        count = 0
        for item in self.eventList:
            if item.IsRemote():
                dc.SetTextBackground(wxColor(180, 192, 121))
            else:
                dc.SetTextBackground(wxColor(180, 192, 159))
            if (item.startTime > date and item.startTime < nextDay):
                count += 1
                monthHeadline = item.startTime.Format('%I%p ').lower() + item.headline.replace('\n', ' ')
                #if monthHeadline[0] == '0':
                dc.DrawText(monthHeadline, x + 5, y + count * 15)
        dc.SetFont(wxFont(8, wxSWISS, wxNORMAL, wxBOLD))
        dc.SetTextForeground(wxColour(63, 87, 119))
        dc.SetTextBackground(wxWHITE)
        dc.SetBackgroundMode(wxTRANSPARENT)
                
        
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
        """ Returns a wxDateTime object, the start of the selected range for this view.
        """
        start = self.model.rangeStart
        wx_start = wxDateTimeFromDMY(start.day, start.month - 1, start.year)
        return wx_start
    
    def getRange(self):
        return (self.model.rangeStart, 
                self.model.rangeStart + self.model.rangeIncrement)
    
