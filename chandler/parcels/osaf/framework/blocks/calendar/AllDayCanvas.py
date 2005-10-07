__copyright__ = "Copyright (c) 2004-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx

from application import schema
from datetime import datetime, timedelta, date, time
from CalendarCanvas import CalendarCanvasItem, CalendarBlock, wxCalendarCanvas, roundTo
from PyICU import GregorianCalendar, ICUtzinfo

import osaf.pim.calendar.Calendar as Calendar

class SparseMatrix(object):

    def __init__(self):
        self._grid = {}
    
    def Fill(self, x,y):
        self._grid.setdefault(x, {})[y] = True

    def Filled(self, x,y):
        if not self._grid.has_key(x):
            return False
        if not self._grid[x].has_key(y):
            return False
        return self._grid[x][y]

    def FitBlock(self, x1, x2, y):
        # are the cells grid[x1..x2][y] all false-valued?  (x2 inclusive.)
        for x in range(x1, x2+1):
            if self.Filled(x,y): return False
        return True

    def FitRange(self, startX, endX):
        """
        find the first available row that fits something that spans from
        startX to endX
        """
        y = 0
        while True:
            fitsHere = self.FitBlock(startX, endX, y)
            if fitsHere:
                # lay out into this spot
                for x in xrange(startX, endX+1):
                    self.Fill(x,y)
                return y
            y += 1
    
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
            self.blockItem.calendarContainer.eventLabelHeight + \
            AllDayCanvasItem.textMargin * 2 + 2

        self.collapsedHeight = int(0.5 * self.eventHeight)
        self.SetMinSize((-1,self.collapsedHeight))
        self.size = self.GetSize()
        
    def OnSize(self, event):
        self.size = self.GetSize()
        self.RebuildCanvasItems()
        
        self.Refresh()
        event.Skip()

    def wxSynchronizeWidget(self):
        #print "%s rebuilding canvas items" % self
        currentRange = self.GetCurrentDateRange()
        self.visibleItems = list(self.blockItem.getItemsInRange(currentRange,
                                                                dayItems=True))
        self.RebuildCanvasItems(resort=True)
        self.Refresh()

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
        
        brushOffset = self.GetPlatformBrushOffset()

        
        def drawCanvasItems(canvasItems, selected):
            for canvasItem in canvasItems:
                pastEnd = Calendar.datetimeOp(canvasItem.GetItem().endTime,
                                              '>',
                                              self.blockItem.rangeEnd)
                canvasItem.Draw(dc, styles, brushOffset,
                                selected, rightSideCutOff=pastEnd)

        unselectedBoxes = []
        
        if self.blockItem.selectAllMode:
            selectedBoxes = self.canvasItemList
        else:
            selection = self.blockItem.selection
            selectedBoxes = []
            for canvasItem in self.canvasItemList:
                
                # save the selected box to be drawn last
                item = canvasItem.GetItem()
                if item in selection:
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

        if Calendar.datetimeOp(item.endTime, '>', endDateTime):
            dayEnd = 6
        else:
            dayEnd = wxAllDayEventsCanvas.DayOfWeekNumber(item.endTime)
        return (dayStart, dayEnd)
        

    def RebuildCanvasItems(self, resort=False):
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        currentRange = self.GetCurrentDateRange()

        if resort:
            self.visibleItems.sort(self.sortByDurationAndStart)
        
        self.canvasItemList = []

        if self.blockItem.dayMode:
            width = self.size.width - drawInfo.scrollbarWidth - drawInfo.xOffset
        else:
            width = drawInfo.dayWidth

        size = self.GetSize()

        oldNumEventRows = self.numEventRows
        if self.blockItem.dayMode:
            # daymode, just stack all the events
            for row, item in enumerate(self.visibleItems):
                self.RebuildCanvasItem(item, width, 0,0, row)
            self.numEventRows = len(self.visibleItems)
            
        else:
            # weekmode: place all the items on a grid without
            # overlap. Items can span multiple columns. TODO: maybe
            # make this into two passes for layout & then Rebuild()ing
            # should be cleaner
            
            # conflict grid: 2-d "matrix" of booleans.  False == free spot
            # FIXME fixed number of rows.   Rigged up for grid[x][y] notation:
            # [[col1..], [col2..]] instead of the usual [[row1..], [row2..]]
            grid = SparseMatrix()
            
            numEventRows = 0

            for item in self.visibleItems:
                (dayStart, dayEnd) = \
                           self.GetColumnRange(item, currentRange)
                
                #search downward, looking for a spot where it'll fit
                row = grid.FitRange(dayStart, dayEnd)
                self.RebuildCanvasItem(item, width, dayStart, dayEnd, row)
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
    
    def RebuildCanvasItem(self, item, columnWidth, dayStart, dayEnd, gridRow):
        """
        @param columnWidth is pixel width of one column under the current view
        but all the other paramters though are grid-based, NOT datetime or pixel-based.
        """
        size = self.GetSize()
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        rect = wx.Rect((drawInfo.dayWidth * dayStart) + drawInfo.xOffset,
                       self.eventHeight * gridRow,
                       columnWidth * (dayEnd - dayStart + 1),
                       self.eventHeight)
 
        canvasItem = AllDayCanvasItem(rect, item)
        self.canvasItemList.append(canvasItem)
        
        # keep track of the current drag/resize box
        if (self.dragState and
            self.dragState.currentDragBox and
            self.dragState.currentDragBox.GetItem() == item):
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

    def OnBeginDragItem(self):
        pass

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
        dx = roundTo(dx, drawInfo.dayWidth)

        position = wx.Point(unscrolledPosition.x - dx,
                            unscrolledPosition.y - dy)
  
        item = dragState.currentDragBox.GetItem()
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
        event = Calendar.CalendarEvent(view=view)
        event.InitOutgoingAttributes()
        
        startTimetz = time(hour=event.startTime.hour,
                        minute=event.startTime.minute,
                        tzinfo=ICUtzinfo.getDefault())
        event.startTime = datetime.combine(newTime, startTimetz)
        event.duration = timedelta(hours=1)
        event.allDay = True
        event.anyTime = False

        # collectionList[0] is the currently selected collection
        event.addToCollection(self.blockItem.contents.collectionList[0])
        self.OnSelectItem(event)
        view.commit()
        return event

class AllDayCanvasItem(CalendarCanvasItem):
    textMargin = 2
    def __init__(self, *args, **kwargs):
        super(AllDayCanvasItem, self).__init__(*args, **kwargs)

    def GetBoundsRects(self):
        return [self._bounds]

