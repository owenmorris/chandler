__copyright__ = "Copyright (c) 2004-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx

from application import schema
from datetime import datetime, timedelta, date, time
from CalendarCanvas import (
    CalendarCanvasItem, CalendarBlock, CalendarSelection,
    wxCalendarCanvas, roundToColumnPosition
    )
from PyICU import GregorianCalendar, ICUtzinfo

from osaf.pim.calendar import Calendar

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
        self.RefreshCanvasItems()
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
                           if self.blockItem.isDayItem(event)]
                                
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
            self.visibleItems = list(
                self.blockItem.getItemsInRange(currentRange, dayItems=True))
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
                pastEnd = Calendar.datetimeOp(canvasItem.item.endTime,
                                              '>=',
                                              self.blockItem.rangeEnd)
                canvasItem.Draw(dc, styles,
                                selected, rightSideCutOff=pastEnd)

        unselectedBoxes = []
        
        contents = CalendarSelection(self.blockItem.contents)
        selectedBoxes = []
        for canvasItem in self.canvasItemList:

            # save the selected box to be drawn last
            item = canvasItem.item
            
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
    def GetColumnRange(item, (startDateTime, endDateTime)):
        # get first and last column of its span
        if Calendar.datetimeOp(item.startTime, '<', startDateTime):
            dayStart = 0
        else:
            dayStart = wxAllDayEventsCanvas.DayOfWeekNumber(item.startTime)

        # this is a really wacky corner case. Since all day events
        # tend to end at midnight on their last day, it sometimes
        # appears as if they don't actually extend into that day. This
        # means that events that 'end' on midnight, on exactly
        # endDateTime, need to be thought of as extending PAST
        # endDateTime.
        if Calendar.datetimeOp(item.endTime, '>=', endDateTime):
            dayEnd = 6
        else:
            dayEnd = wxAllDayEventsCanvas.DayOfWeekNumber(item.endTime)

        return (dayStart, dayEnd)
        

    def RebuildCanvasItems(self, resort=False):
        currentRange = self.GetCurrentDateRange()

        if resort:
            self.visibleItems.sort(self.sortByDurationAndStart)
        
        self.canvasItemList = []

        size = self.GetSize()

        oldNumEventRows = self.numEventRows
        if self.blockItem.dayMode:
            # daymode, just stack all the events
            for row, item in enumerate(self.visibleItems):
                self.RebuildCanvasItem(item, 0,0, row)
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

            for item in self.visibleItems:
                (dayStart, dayEnd) = \
                           self.GetColumnRange(item, currentRange)
                
                #search downward, looking for a spot where it'll fit
                row = self.grid.FillRange(dayStart, dayEnd, item)
                self.RebuildCanvasItem(item, dayStart, dayEnd, row)
                numEventRows = max(row+1, self.numEventRows)

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
            self.GetParent().MoveSash(self.expandedHeight)
            self.blockItem.calendarContainer.calendarControl.widget.ResetSashState()

    def GetExpandedHeight(self):
        """
        precondition: self.numEventRows must be correctly set
        """
        return int((self.numEventRows + .5) * self.eventHeight)
    
    expandedHeight = property(GetExpandedHeight)
    
    def RebuildCanvasItem(self, item, dayStart, dayEnd, gridRow):
        """
        @param columnWidth is pixel width of one column under the
        @param dayStart is the day-column (0-based) of the first day
        @param dayEnd is the day-column (0-based) of the last day
        @param gridRow is the row (0-based) in the grid
        """
        size = self.GetSize()
        calendarBlock = self.blockItem

        startX, width = self.getColumnForDay(dayStart, dayEnd)
        
        rect = wx.Rect(startX, self.eventHeight * gridRow,
                       width, self.eventHeight)

        collection = calendarBlock.getContainingCollection(item)
        canvasItem = AllDayCanvasItem(collection, calendarBlock.contentsCollection,
                                      rect, item)
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
        cal.setTime(datetime)
        
        return (cal.get(cal.DAY_OF_WEEK) - cal.getFirstDayOfWeek())

    @staticmethod
    def sortByDurationAndStart(item1, item2):
        """
        Comparison callback function for sorting
        """

        # ORDER BY duration, date
        spanResult = cmp(item2.duration, item1.duration)
        if spanResult != 0:
            return spanResult
        else:
            return Calendar.datetimeOp(item1.startTime, 'cmp', item2.startTime)
        
        # another possibililty is ORDER BY date, duration
        #dateResult = cmp(item1.startTime, item2.startTime)
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
        if not self.dragState.currentDragBox.CanDrag():
            self.WarnReadOnlyTime([self.dragState.currentDragBox.item])
            return False
        return True

    def OnDraggingItem(self, unscrolledPosition):
        if self.blockItem.dayMode:
             #no dragging allowed.
             return
        
        # we have to deduce the offset, so you can begin a drag in any
        # cell of a multi-day event. Code borrowed from
        # wxTimedEventsCanvas.OnDraggingItem()
        dragState = self.dragState
        
        if not dragState.currentDragBox.CanDrag():
            return
        
        (boxX,boxY) = dragState.originalDragBox.GetDragOrigin()
        
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        dx, dy = dragState.dragOffset
        
        # but if the event starts before the current week adjust dx,
        # make it negative: where the event would start on the screen,
        # if it was drawn
        
        # hack alert! We shouldn't need to adjust this
        dx = roundToColumnPosition(dx, drawInfo.columnPositions)

        position = wx.Point(unscrolledPosition.x - dx,
                            unscrolledPosition.y - dy)
  
        item = dragState.currentDragBox.item
        newTime = self.getDateTimeFromPosition(position, mustBeInBounds=False)
        
        oldStartTime = item.startTime
        tzinfo = oldStartTime.tzinfo
        
        if tzinfo is None or newTime.tzinfo is None:
            newTime = newTime.replace(tzinfo=tzinfo)
        else:
            newTime = newTime.astimezone(tzinfo)
        
        # bounding rules are: at least one cell of the event must stay visible.
        if Calendar.datetimeOp(newTime, '>=', self.blockItem.rangeEnd):
            newTime = self.blockItem.rangeEnd - timedelta(days=1)
            newTime = newTime.replace(tzinfo=ICUtzinfo.getDefault())
        elif Calendar.datetimeOp(newTime + item.duration, '<',
             self.blockItem.rangeStart):
            newTime = self.blockItem.rangeStart - item.duration
            newTime = newTime.replace(tzinfo=ICUtzinfo.getDefault())
        
        if tzinfo is None:
            oldStartTime = \
                item.startTime.replace(tzinfo=ICUtzinfo.getDefault())
        else:
            oldStartTime = \
                item.startTime.astimezone(ICUtzinfo.getDefault())
        # [@@@] grant .toordinal() & tzinfo?
        
        if (newTime.date() != oldStartTime.date()):
            item.startTime = datetime(newTime.year, newTime.month, newTime.day,
                                      item.startTime.hour, item.startTime.minute, tzinfo=tzinfo)
            self.Refresh()

    def getRelativeTimeFromPosition(self, drawInfo, position):
        """
        on the all-day canvas, there is no notion of hour/minutes
        """
        return timedelta()
    
    def OnCreateItem(self, unscrolledPosition):
        view = self.blockItem.itsView
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        
        event = self.CreateEmptyEvent(startTime=newTime, allDay=True, anyTime=True)

        self.OnSelectItem(event)
        view.commit()
        return event

class AllDayCanvasItem(CalendarCanvasItem):
    textMargin = 2
    def GetBoundsRects(self):
        return [self._bounds]

