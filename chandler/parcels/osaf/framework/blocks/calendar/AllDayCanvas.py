#   Copyright (c) 2004-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


__parcel__ = "osaf.framework.blocks.calendar"

import wx

from application import schema
from datetime import datetime, timedelta, date, time
from CalendarCanvas import (
    CalendarCanvasItem, CalendarBlock, CalendarSelection,
    wxCalendarCanvas, roundToColumnPosition, widgetGuardedCallback
    )
from CollectionCanvas import DragState
from PyICU import GregorianCalendar, ICUtzinfo
from osaf.pim.calendar.TimeZone import TimeZoneInfo
from osaf.pim import isDead

from application.dialogs import RecurrenceDialog
from osaf.pim.calendar import Calendar

from itertools import chain

class SparseMatrix(object):

    def __init__(self):
        self._grid = {}
        self.maxX = -1
        self.maxY = -1
    
    def Fill(self, x,y,value):
        """
        Fills the given space in the matrix with the given value
        """
        if x > self.maxX: self.maxX = x
        if y > self.maxY: self.maxY = y
        
        self._grid.setdefault(x, {})[y] = value

    def Filled(self, x,y):
        """
        Returns True or False to indicate if the given space is filled
        in the matrix
        """
        if not self._grid.has_key(x):
            return False
        if not self._grid[x].has_key(y):
            return False
        return True

    def Get(self, x, y, v=None):
        """
        Like dict.get - retrieves the value at x,y, returns None or v
        if the value isn't found
        """
        try:
            return self._grid[x][y]
        except KeyError:
            return v
        
    def FitBlock(self, x1, x2, y):
        """
        are the cells grid[x1..x2][y] all false-valued?  (x2 inclusive.)

        Just returns True/False, does not alter the matrix
        """
        for x in range(x1, x2+1):
            if self.Filled(x,y): return False
        return True

    def FillRange(self, startX, endX, value):
        """
        find the first available row that fits something that spans from
        startX to endX and fills it with the given value

        returns the row that got filled
        """
        y = 0
        while True:
            fitsHere = self.FitBlock(startX, endX, y)
            if fitsHere:
                # lay out into this spot
                for x in xrange(startX, endX+1):
                    self.Fill(x,y, value)
                return y
            y += 1

    def FindFirst(self, value):
        for x in sorted(self._grid.iterkeys()):
            for y in sorted(self._grid[x].iterkeys()):
                if self._grid[x][y] == value:
                    return x,y
        return -1,-1

    def GetWidth(self, x, y):
        """
        Get the width of the value at x,y - this will walk forward
        along the x axis until it finds a cell that is not x.
        """
        item = self.Get(x,y)
        for newX in xrange(x + 1, self.maxX+1):
            if self.Get(newX,y) != item:
                return newX - x
        return self.maxX - x + 1
        
    
class AllDayEventsCanvas(CalendarBlock):

    def instantiateWidget(self):
        super(AllDayEventsCanvas, self).instantiateWidget()
        return wxAllDayEventsCanvas(self.parentBlock.widget)

class wxAllDayEventsCanvas(wxCalendarCanvas):
    legendBorderWidth = 1

    def __init__(self, *arguments, **keywords):
        super (wxAllDayEventsCanvas, self).__init__ (*arguments, **keywords)
        self.autoExpandMode = True #though we start at collapsed height
        self.numEventRows = 0

    def OnInit(self):
        super (wxAllDayEventsCanvas, self).OnInit()
        
        # Event handlers
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
        self.eventHeight = \
            self.blockItem.calendarContainer.eventLabelMeasurements.height + \
            AllDayCanvasItem.textMargin * 2 + 2

        self.collapsedHeight = int(0.5 * self.eventHeight)
        self.SetMinSize((-1,self.collapsedHeight))
        self.size = self.GetSize()
        
    def OnSize(self, event):
        self.size = self.GetSize()
        self.RefreshCanvasItems(resort=False)
        event.Skip()

    def wxSynchronizeWidget(self, useHints=False):
        #print "%s rebuilding canvas items" % self
        currentRange = self.GetCurrentDateRange()
        
        # The only hints we understand are event additions.
        # So, if any other kind of hints have been received,
        # fall back to a full synchronize.
        if useHints and self.HavePendingNewEvents():
            addedEvents = \
                self.GetPendingNewEvents(currentRange)
            addedEvents = [event for event in addedEvents
                           if Calendar.isDayEvent(event)]
                                
            numAdded = 0
            
            for event in addedEvents:
                
                if not event in self.visibleItems:
                    self.visibleItems.append(event)
                    numAdded += 1
                
            if numAdded > 0:
                self.RefreshCanvasItems(resort=True)

            if numAdded == 1:
                self.EditCurrentItem()
        else:
            self.ClearPendingNewEvents()
            self.visibleItems = list(
                self.blockItem.getEventsInRange(currentRange, dayItems=True))
            self.RefreshCanvasItems(resort=True)

            

    def DrawBackground(self, dc):
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        
        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle(0, 0, self.size.width, self.size.height)

        self.ShadeToday(dc)
        self.DrawDayLines(dc)

        # Draw one extra line after the last day of the week,
        # to line up with the scrollbar below
        dc.DrawLine(self.size.width - drawInfo.scrollbarWidth, 0,
                    self.size.width - drawInfo.scrollbarWidth, self.size.height)

    def DrawCells(self, dc):
        styles = self.blockItem.calendarContainer

        dc.SetFont(styles.eventLabelFont)
        
        def drawCanvasItems(canvasItems, selected):
            for canvasItem in canvasItems:
                pastEnd = canvasItem.event.endTime >= self.blockItem.rangeEnd
                canvasItem.Draw(dc, styles,
                                selected, rightSideCutOff=pastEnd)

        unselectedBoxes = []
        
        contents = CalendarSelection(self.blockItem.contents)
        selectedBoxes = []

        draggedOutItem = self._getHiddenOrClearDraggedOut()
        
        for canvasItem in self.canvasItemList:

            # save the selected box to be drawn last
            item = canvasItem.item
            if item == draggedOutItem or isDead(item):
                # don't render items we're dragging out of the canvas
                continue      
            
            # for some reason, we're getting paint events before
            # widget synchronize events
            if item in contents:
                if contents.isItemSelected(item):
                    selectedBoxes.append(canvasItem)
                else:
                    unselectedBoxes.append(canvasItem)

        drawCanvasItems(unselectedBoxes, False)
        drawCanvasItems(selectedBoxes, True)
            
    @staticmethod
    def GetColumnRange(itemStart, itemEnd, (startDateTime, endDateTime)):
        # get first and last column of its span
        if itemStart < startDateTime:
            dayStart = 0
        else:
            dayStart = wxAllDayEventsCanvas.DayOfWeekNumber(itemStart)

        # this is a really wacky corner case. Since all day events
        # tend to end at midnight on their last day, it sometimes
        # appears as if they don't actually extend into that day. This
        # means that events that 'end' on midnight, on exactly
        # endDateTime, need to be thought of as extending PAST
        # endDateTime.
        if itemEnd >= endDateTime:
            dayEnd = 6
        else:
            dayEnd = wxAllDayEventsCanvas.DayOfWeekNumber(itemEnd)

        return (dayStart, dayEnd)

    def FinishDrag(self):
        self.fileDragPosition = None
        currentCanvasItem = self.dragState.currentDragBox
        if not currentCanvasItem.CanDrag():
            return

        callback = widgetGuardedCallback(self.blockItem,
                                         self.wxSynchronizeWidget)
        proxy = RecurrenceDialog.getProxy(u'ui', currentCanvasItem.item,
                                          endCallback=callback)
        
        if self.dragState.dragged:
            (startTime, endTime) = self.GetDragAdjustedTimes()
            duration = endTime - startTime
            (startTime, endTime) = self.GetDragAdjustedTimes()
            duration = endTime - startTime
            stampedProxy = Calendar.EventStamp(proxy)
            stampedProxy.duration = duration
            stampedProxy.startTime = startTime

            if self.coercedCanvasItem is not None:
                self.coercedCanvasItem = None
                stampedProxy.allDay = True

    def makeCoercedCanvasItem(self, x, y, item):
        event = Calendar.EventStamp(item)
        unscrolledPosition = wx.Point(*self.CalcUnscrolledPosition(x, y))
        start = self.getDateTimeFromPosition(unscrolledPosition,
                                             event.startTime.tzinfo)
        end = start + max(event.duration, timedelta(hours=1))
        
        colStart, colEnd = self.GetColumnRange(start, end, 
                                               self.GetCurrentDateRange())
        
        canvasItem = self.GetCanvasItem(event, colStart, colEnd, 0)
        
        self.coercedCanvasItem  = canvasItem
        noop = lambda x: None
        self.dragState = DragState(canvasItem, self, noop,
                                   noop, self.FinishDrag,
                                   unscrolledPosition)
        self.dragState.dragged = True

        canvasItem.resizeMode = None
        self.dragState._dragStarted = True
        self.dragState.originalDragBox = canvasItem
        self.dragState.currentPosition = unscrolledPosition
        self.dragState._dragDirty = True        
        
    def OnEndDragItem(self):
        self.FinishDrag()
        self.RebuildCanvasItems(resort=True)


    def GetDragAdjustedTimes(self):
        """
        Return a new start/end time for the currently selected event, based
        on the current position and drag state. Handles both move and
        resize drags
        """
        tzprefs = schema.ns('osaf.app', self.blockItem.itsView).TimezonePrefs
        useTZ = tzprefs.showUI
        
        event = self.dragState.originalDragBox.event
        #resizeMode = self.dragState.originalDragBox.resizeMode
        
        oldTZ = event.startTime.tzinfo        
        
        if useTZ:
            tzinfo = oldTZ
        else:
            tzinfo = ICUtzinfo.floating

        #if resizeMode is None:
            # moving an item, need to adjust just the start time
            # for the relative position of the mouse in the item
        newStartTime = self.GetDragAdjustedStartTime(tzinfo)
        newEndTime = newStartTime + event.duration

        # top/bottom resizes: just set the appropriate start/end
        # to where the mouse is
        #else:
            #pass # ignore for now
            #dragTime = self.getDateTimeFromPosition(
                                #self.dragState.currentPosition,
                                #tzinfo=tzinfo)
                
            #if resizeMode == TimedCanvasItem.RESIZE_MODE_START:
                #newStartTime = dragTime
                #newEndTime = event.endTime
            #elif resizeMode == TimedCanvasItem.RESIZE_MODE_END:
                #newEndTime = dragTime
                #newStartTime = event.startTime

        if newEndTime < newStartTime:
            newEndTime = newStartTime + timedelta(minutes=15)

        if not useTZ:
            newEndTime   = newEndTime.replace(tzinfo = oldTZ)
            newStartTime = newStartTime.replace(tzinfo = oldTZ)

        return (newStartTime, newEndTime)

    def RebuildCanvasItems(self, resort=False):
        currentRange = self.GetCurrentDateRange()

        if resort:
            self.visibleItems.sort(self.sortByDurationAndStart)
        
        self.canvasItemList = []

        size = self.GetSize()

        oldNumEventRows = self.numEventRows
        if self.blockItem.dayMode:
            # daymode, just stack all the events
            for row, event in enumerate(self.visibleItems):
                if not isDead(event.itsItem):
                    self.RebuildCanvasItem(event, 0,0, row)
            self.numEventRows = len(self.visibleItems)
            
        else:
            # weekmode: place all the items on a grid without
            # overlap. Items can span multiple columns. TODO: maybe
            # make this into two passes for layout & then Rebuild()ing
            # should be cleaner
            
            # conflict grid: 2-d "matrix" of booleans.  False == free spot
            # FIXME fixed number of rows.   Rigged up for grid[x][y] notation:
            # [[col1..], [col2..]] instead of the usual [[row1..], [row2..]]
            self.grid = SparseMatrix()
            
            numEventRows = 0

            def addCanvasItem(item, start, end):
                #search downward, looking for a spot where it'll fit
                (dayStart, dayEnd) = \
                           self.GetColumnRange(start, end, currentRange)
                row = self.grid.FillRange(dayStart, dayEnd, item)
                self.RebuildCanvasItem(item, dayStart, dayEnd, row)
                numEventRows = max(row+1, self.numEventRows)
                
            newTime = None
            if self.dragState is not None:
                newTime = self.GetDragAdjustedStartTime(ICUtzinfo.default)
                # if the dragged item isn't from the allday canvas, it won't
                # appear in self.visibleItems
                if self.coercedCanvasItem is not None:
                    event = self.coercedCanvasItem.event
                    addCanvasItem(event, newTime, newTime + event.duration)

            for event in self.visibleItems:
                if not isDead(event.itsItem):
                    if newTime is not None and \
                       event.itsItem is self.dragState.originalDragBox.item:
    
                        # bounding rules are: at least one cell of the event
                        # must stay visible.
                        if newTime >= self.blockItem.rangeEnd:
                            newTime = self.blockItem.rangeEnd - timedelta(days=1)
                        elif newTime + event.duration < self.blockItem.rangeStart:
                            newTime = self.blockItem.rangeStart - event.duration
    
                        start = newTime
                    else:
                        start = event.effectiveStartTime
                    
                    end  = start + event.duration
                    addCanvasItem(event, start, end)

            self.numEventRows = numEventRows
            
        if (self.numEventRows and
            self.numEventRows > oldNumEventRows and
            self.autoExpandMode):
            self.ExpandIfNeeded()

    def ExpandIfNeeded(self):
        """
        Expand to make all events visible, but never contract to do so.
        """
        currentHeight = self.GetSize()[1]
        if currentHeight < self.expandedHeight:
            self.GetParent().AdjustAndSetSashPosition(self.expandedHeight)
            self.blockItem.calendarContainer.calendarControl.widget.ResetSashState()

    def GetExpandedHeight(self):
        """
        precondition: self.numEventRows must be correctly set
        """
        return int((self.numEventRows + .5) * self.eventHeight)
    
    expandedHeight = property(GetExpandedHeight)
    
    def GetCanvasItem(self, item, dayStart, dayEnd, gridRow):
        size = self.GetSize()
        calendarBlock = self.blockItem

        startX, width = self.getColumnForDay(dayStart, dayEnd)
        
        # overlap all-day canvas items by one pixel
        rect = wx.Rect(startX, (self.eventHeight - 1) * gridRow,
                       width + 1, self.eventHeight)

        collection = calendarBlock.getContainingCollection(item, calendarBlock.contentsCollection)
        return AllDayCanvasItem(collection, calendarBlock.contentsCollection,
                                      rect, item)
    
    def RebuildCanvasItem(self, item, dayStart, dayEnd, gridRow):
        """
        @param columnWidth is pixel width of one column under the
        @param dayStart is the day-column (0-based) of the first day
        @param dayEnd is the day-column (0-based) of the last day
        @param gridRow is the row (0-based) in the grid
        """
        canvasItem = self.GetCanvasItem(item, dayStart, dayEnd, gridRow)
        self.canvasItemList.append(canvasItem)
        
        # keep track of the current drag/resize box
        if (self.dragState and
            self.dragState.currentDragBox and
            self.dragState.currentDragBox.item == item):
            self.dragState.currentDragBox = canvasItem

    @staticmethod
    def DayOfWeekNumber(datetime):
        """
        evaluate datetime's position in the week: 0-6 (sun-sat)
        """
        cal = GregorianCalendar()
        cal.setTimeZone(datetime.tzinfo.timezone)
        cal.setTime(datetime)
        
        return (cal.get(cal.DAY_OF_WEEK) - cal.getFirstDayOfWeek())

    @staticmethod
    def sortByDurationAndStart(event1, event2):
        """
        Comparison callback function for sorting
        """
        if isDead(event1.itsItem) or isDead(event2.itsItem):
            # sort stale or deleted items first, False < True
            return cmp(not isDead(event1.itsItem),
                       not isDead(event2.itsItem))
        
        # ORDER BY duration, date
        spanResult = cmp(event2.duration, event1.duration)
        if spanResult != 0:
            return spanResult
        else:
            return cmp(event1.startTime, event2.startTime)
        
        # another possibililty is ORDER BY date, duration
        #dateResult = cmp(event1.startTime, event2.startTime)
        #if dateResult != 0:
            #return dateResult
        #return spanResult

    def OnNavigateItem(self, direction):
        currentItem = self.SelectedCanvasItem()
        if currentItem is None:
            return

        # find current position in matrix... yuck.
        x,y = self.grid.FindFirst(currentItem.item)

        # we initially start with x as a range because events can span
        # multiple columns
        xr = xrange(x, x+self.grid.GetWidth(x,y))
        yr = (y,)

        # now we expand those ranges to look for events beyond the
        # current item, depending on the direction we're going
        if direction == "UP":
            yr = xrange(y - 1, -1, -1)
        elif direction == "DOWN":
            yr = xrange(y + 1, self.grid.maxY + 1, 1)
        elif direction == "LEFT":
            xr = xrange(x - 1, -1, -1)
        elif direction == "RIGHT":
            xr = xrange(x + 1, self.grid.maxX + 1, 1)

        # finally walk the grid starting just past the current item,
        # looking for a new item... if we find it then select it.
        for newX in xr:
            for newY in yr:
                item = self.grid.Get(newX, newY)
                if item is not None and item != currentItem.item:
                    self.OnSelectItem(item)
                    return
            

    def OnBeginDragItem(self):
        return True

    def OnDraggingItem(self, unscrolledPosition):
        self.RefreshCanvasItems(resort=False)


    def getRelativeTimeFromPosition(self, drawInfo, position):
        """
        on the all-day canvas, there is no notion of hour/minutes
        """
        return timedelta()
    
    def OnCreateItem(self, unscrolledPosition):
        view = self.blockItem.itsView
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        newTime = newTime.replace(tzinfo=TimeZoneInfo.get(view).default)
        
        event = self.CreateEmptyEvent(startTime=newTime, allDay=True,
                                      anyTime=True)

        self.OnSelectItem(event.itsItem)
        view.commit()
        return event

    def belongsOnCanvas(self, item):
        # Return False if this item no longer belongs on this canvas
        event = Calendar.EventStamp(item)
        return event.allDay or event.anyTime

class AllDayCanvasItem(CalendarCanvasItem):
    resizeBufferSize = 5
    textMargin = 2
    swatchAdjust = 1

    def __init__(self, *args, **keywords):
        super(AllDayCanvasItem, self).__init__(*args, **keywords)

        # tweak the height for all day canvas items
        self.textOffset.y = self.textMargin - 1

    def GetBoundsRects(self):
        return [self._bounds]

    def UpdateDrawingRects(self, startTime=None, endTime=None):
        # allow caller to override start/end time
        event = self.event
        
        if not startTime:
            startTime = event.startTime
            
        if not endTime:
            endTime = event.endTime
        
        #self._calendarCanvas.GenerateBoundsRects(startTime, endTime)        
        
        b = self._bounds
        self._resizeLeftBounds  = wx.Rect(b.x, b.y, self.resizeBufferSize, 
                                          b.height)
        self._resizeRightBounds = wx.Rect(b.x + b.width - self.resizeBufferSize,
                                          b.y, self.resizeBufferSize, b.height)

    def GetEditorPosition(self):
        """
        This returns a location to show the editor.
        """
        position = self.GetBoundsRects()[0].GetPosition() + self.textOffset

        # now offset to account for the time
        position += (0, self.timeHeight + 3)
        return position
