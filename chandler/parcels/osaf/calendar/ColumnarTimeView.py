""" Columnar Time View (the middle section of the columnar view)
    With typical calendar data, this scrolling view is meant to display events
    with start and end times.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cPickle
import copy

from wxPython.wx import *
from wxPython.xrc import *
from mx import DateTime
from persistence import Persistent
from persistence.dict import PersistentDict

from application.Application import app
from application.SimpleCanvas import wxSimpleCanvas

from OSAF.calendar.model.CalendarEvent import CalendarEventFactory

from OSAF.calendar.ColumnarItem import ColumnarItem
from OSAF.calendar.ColumnarItemEditor import ColumnarItemEditor
from OSAF.calendar.ColumnarSubView import ColumnarSubView, wxColumnarSubView
from OSAF.calendar.CalendarEvents import *

class ColumnarTimeView (ColumnarSubView):
    def __init__(self, columnarView):
        ColumnarSubView.__init__(self, columnarView)
        self.xrcName = "ColumnarTimeView"
        self.hourHeight = 50
        self.freebusy = 10
        self.minHours = 0.5
    
    def getShowFreeBusy(self):
        return self.columnarView.calendarView.showFreeBusy
        
    def getHoursPerView(self):
        return self.columnarView.hoursPerView
    
    def getDayHeight(self):
        return self.columnarView.hoursPerView * self.hourHeight
    
    hoursPerView = property(getHoursPerView)
    dayHeight = property(getDayHeight)
    viewHeight = property(getDayHeight)
    showFreeBusy = property(getShowFreeBusy)
    
    def getTimeFromPos(self, y):
        """Given a y coordinate, find the coorresponding time.
        """
        hour = y / self.hourHeight
        minutes = ((y % self.hourHeight) * 60) / self.hourHeight
        minutes = int(minutes / 30) * 30
        return (hour, minutes)
    
    def getDateFromPos(self, x):
        """Given an x coordinate, find the corresponding date.
        """
        daysFromStart = (x - self.offset) / self.dayWidth
        delta = DateTime.RelativeDateTime(days=daysFromStart)
        date = self.columnarView.rangeStart + delta
        return (date.year, date.month, date.day)
    
    def getDateTimeFromPos(self, position):
        """Given a position in the window (wxPoint), find the date and time.
        """
        year, month, day = self.getDateFromPos(position.x)
        hour, minutes = self.getTimeFromPos(position.y)
        datetime = DateTime.DateTime(year, month, day, hour, minutes)
        return datetime

    def getPosFromDateTime(self, datetime):
        """Given a datetime, find the corresponding position in the window.
           Returns a wxPoint.
        """
        delta = datetime - self.columnarView.rangeStart
        x = (self.dayWidth * delta.day) + self.offset
        y = int(self.hourHeight * (datetime.hour + datetime.minute/float(60)))
        return wxPoint(x, y)
    
    def isDateInRange(self, date):
        """Determine if the given date is in the display range.
        """
        # @@@ This method is currently used to see if a given event should be
        #     in the corresponding view. Once we have real queries, this 
        #     mechanism may change.
        begin = self.columnarView.rangeStart
        end = begin + self.columnarView.rangeIncrement
        return ((date > begin) and (date < end))

    # receive remote objects by passing it on to the wxColumnarTimeView that actually holds them
    def AddObjectsToView(self, url, objectList, lastFlag):
        viewer = app.association[id(self)]
        viewer.AddObjectsToView(url, objectList, lastFlag)
 
    def UpdateItems(self):
        viewer = app.association[id(self)]
        remoteAddress = self.columnarView.calendarView.remoteAddress
        viewer._loadEvents()
        viewer._displayEvents()
        
class wxColumnarTimeView(wxColumnarSubView):

    def OnInit(self, model):
        dataFormat = wxCustomDataFormat("ChandlerItem")
        dropTargetDataObject = wxCustomDataObject(dataFormat)
        self.remoteAddress = None

        wxColumnarSubView.OnInit(self, model, dropTargetDataObject)

        self.editor = ColumnarItemEditor(self)
        self.editor.Hide()
        
        # @@@ What should the scrollrate be? Where to scroll to start?
        # @@@ Remove magic numbers
        self.SetScrollRate(0, 5)
        self.Scroll(0, 100)
        
        self.autoCreateDistance = self.model.hourHeight * self.model.minHours

        self._loadEvents()
        self._displayEvents()
        
        EVT_MENU(self, wxID_CLEAR, self.OnDelete)
        EVT_MENU(self.GetParent().GetParent(), XRCID("MenuDeleteCalendar"), self.OnDelete)

        EVT_SIZE(self, self.OnSize)

    def OnDelete(self, event):
        objectToRemove = self.FindSelectedObject()
        if objectToRemove:
            self.DeleteItem(objectToRemove)
            del objectToRemove
        
            app.repository.commit()
            
            self.editor.ClearItem()
            self.Refresh()
        
    def FindSelectedObject(self):
        selectedObject = None
        for drawableObject in self.zOrderedDrawableObjects:
            if (drawableObject.selected):
                selectedObject = drawableObject
        return selectedObject
                
    def DeleteItem(self, drawableObject):
        self.zOrderedDrawableObjects.remove(drawableObject)
        drawableObject.item.delete()
        del drawableObject.item
        
    # Displaying events based on repository
    # @@@ Scaffolding in lieu of a repository with a query language
    
    def _loadEvents(self):
        """Load the events from the repository, creating a ColumnarItem
           for every Event item.
        """
        # @@@ check this one, clears the canvas of objects
        self.zOrderedDrawableObjects[0:] = []

        remoteAddress = self.model.columnarView.calendarView.remoteAddress
        overlay = self.model.columnarView.calendarView.overlayRemoteItems
 
        if remoteAddress != None:
            if app.jabberClient.RequestRemoteObjects(remoteAddress, 'Calendar'):
                self.remoteLoadInProgress = True
            else:
                self.remoteLoadInProgress = False
                message = _("Sorry, but %s is not present!") % (remoteAddress)
                wxMessageBox(message)
        
        if remoteAddress == None or overlay:
            for item in app.repository.find("//Calendar"):
                eventObject = ColumnarItem(self, item)
                self.zOrderedDrawableObjects.append(eventObject)

    # receive remote objects by adding them to the list, and redrawing when we receive the last one
    def AddObjectsToView(self, url, objectList, lastFlag):
        for item in objectList:
            eventObject = ColumnarItem(self, item)
            self.zOrderedDrawableObjects.append(eventObject)
            
        if lastFlag:
            self._displayEvents()
            
    def _displayEvents(self):
        """Display all events in the current time range.
        """
        # @@@ Currently a hack, we have a list of all events,
        #     and hide/show events in the current time range
        # Note: set the bounds and visibility without doing a refresh,
        #       we want one global refresh

        self.Freeze()
        self.editor.ClearItem()
        for columnarItem in self.zOrderedDrawableObjects:
            if self.model.isDateInRange(columnarItem.item.startTime):
                columnarItem.PlaceItemOnCalendar()
                columnarItem.Show(True)
            else:
                columnarItem.Show(False)
        self.Thaw()
                
    def UpdateDateRange(self):
        self._loadEvents()
        self._displayEvents()
        self.Refresh()
        
    def OnSize(self, event):
        self.GetParent().UpdateColumnarWidth(self.GetClientSize().width)
        event.Skip()

    def UpdateSize(self):
        self.SetVirtualSize((self.model.viewWidth, self.model.viewHeight))
        for columnarItem in self.zOrderedDrawableObjects:
            columnarItem.PlaceItemOnCalendar()
        self.editor.OnSize()
        
    # SimpleCanvas methods to override
        
    def DrawBackground(self, dc):
        # Use the transparent pen for painting the background
        dc.SetPen(wxTRANSPARENT_PEN)

        # Paint the entire background
        dc.SetBrush(wxBrush(wxColour(246, 250, 254)))
        size = self.GetVirtualSize()
        dc.DrawRectangle(0, 0, size.x, size.y)
        #dc.DrawRectangle(0, 0, self.model.viewWidth, self.model.dayHeight)

        # Set up the font
        dc.SetTextForeground(wxColour(63, 87, 119))
        dc.SetFont(wxFont(9, wxSWISS, wxNORMAL, wxBOLD))

        # Set the pen for drawing between days
        dc.SetPen(wxPen(wxColour(183, 183, 183)))
        
        # free busy bar, optional 
        if (self.model.showFreeBusy):
            dc.SetBrush(wxWHITE_BRUSH)
            for i in range(self.model.daysPerView):
                dc.DrawRectangle(self.model.offset + self.model.dayWidth * i, 0,
                                 self.model.freebusy, self.model.dayHeight)

        # horizontal lines separating hours + hour legend
        year = DateTime.today()
        for j in range(self.model.hoursPerView):
            dc.DrawText(year.Format("%I %p"), 2, j * self.model.hourHeight)
            dc.SetPen(wxPen(wxColour(183, 183, 183)))
            dc.DrawLine(self.model.offset, j * self.model.hourHeight,
                        self.model.viewWidth, j * self.model.hourHeight)
            dc.SetPen(wxPen(wxColour(225, 225, 225)))
            dc.DrawLine(self.model.offset, j * self.model.hourHeight + (self.model.hourHeight/2),
                        self.model.viewWidth, j * self.model.hourHeight + (self.model.hourHeight/2))
            year += DateTime.RelativeDateTime(hours=1)

        dc.SetPen(wxBLACK_PEN)

        # vertical lines separating days
        for i in range(self.model.daysPerView):
            dc.DrawLine(self.model.offset + self.model.dayWidth * i, 0,
                        self.model.offset + self.model.dayWidth * i, 
                        self.model.dayHeight)            

    def ConvertDataObjectToDrawableObject(self, dataObject, x, y, move):
        # Moves the item, or creates a new one
        (path, hotx, hoty) = cPickle.loads(dataObject.GetData())
        item = app.repository.find(path)
        newTime = self.model.getDateTimeFromPos(wxPoint(x, y - hoty))
        
        if (move):
            item.ChangeStart(newTime)
        else:
            newItem = CalendarEventFactory(app.repository).NewItem()
            newItem.duration = item.duration
            newItem.setAttributeValue("headline", item.headline)
            newItem.ChangeStart(newTime)
            
            item = newItem
            
        newItemObject = ColumnarItem(self, item)
        newItemObject.PlaceItemOnCalendar()

        app.repository.commit()
        
        return newItemObject
    
    def CreateNewDrawableObject(self, dragRect, startDrag, endDrag):
        # don't create an object in a remote view
        # FIXME: eventually, we'll be able to with the right permissions
        remoteAddress = self.model.columnarView.calendarView.remoteAddress
        if remoteAddress != None:
            wxMessageBox(_("Sorry, but you can't add a new object to a remote calendar"))
            return None
        
        newItem = CalendarEventFactory(app.repository).NewItem()
        
        newItem.setAttributeValue("headline", "")
        self.Freeze()
        newEventObject = ColumnarItem(self, newItem)
        newEventObject.SizeDrag(dragRect, startDrag, endDrag)
        self.Thaw()
        
        self.editor.ClearItem()
        
        # add object to the local repository (addObject commits the object)
        app.repository.commit()
        
        return newEventObject
