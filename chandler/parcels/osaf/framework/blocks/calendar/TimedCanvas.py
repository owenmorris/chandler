__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx

from application import schema
from datetime import datetime, timedelta, date, time
from CalendarCanvas import (
    CalendarCanvasItem, CalendarBlock, CalendarSelection,
    wxCalendarCanvas, roundTo, roundToColumnPosition
    )
from PyICU import FieldPosition, DateFormat, ICUtzinfo
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.TimeZone import TimeZoneInfo

from application.dialogs import RecurrenceDialog

class TimedEventsCanvas(CalendarBlock):

    def render(self, *args, **kwds):
        super(TimedEventsCanvas, self).render(*args, **kwds)

        prefs = schema.ns('osaf.framework.blocks.calendar', self.itsView).calendarPrefs
        self.itsView.watchItem(self, prefs, 'onCalendarPrefsChange')

    def onDestroyWidget(self, *args, **kwds):

        prefs = schema.ns('osaf.framework.blocks.calendar', self.itsView).calendarPrefs
        self.itsView.unwatchItem(self, prefs, 'onCalendarPrefsChange')
        super(TimedEventsCanvas, self).onDestroyWidget(*args, **kwds)
        

    def onCalendarPrefsChange(self, op, item, names):
        self.widget.SetWindowGeometry()
        self.widget.RealignCanvasItems()
        self.widget.Refresh()

    def instantiateWidget(self):
        super(TimedEventsCanvas, self).instantiateWidget()
        return wxTimedEventsCanvas(self.parentBlock.widget)


class wxTimedEventsCanvas(wxCalendarCanvas):
    def __init__(self, parent, *arguments, **keywords):
        super(wxTimedEventsCanvas, self).__init__(parent, *arguments, **keywords)

        # @@@ rationalize drawing calculations...
        
        self._bgSelectionStartTime = None
        self._bgSelectionEndTime = None

        self.canvasItemList = []
        # determines if we're dragging the start or the end of an event, usually
        # the end
        self._bgSelectionDragEnd = True

    def wxSynchronizeWidget(self, useHints=False):
        currentRange = self.GetCurrentDateRange()
        self._doDrawingCalculations()

        # The only hints we understand are event additions.
        # So, if any other kind of hints have been received,
        # fall back to a full synchronize.
        
        numAdded = 0 # The events may not be timed, or may fall
                     # outside our range, etc,
                     
        if useHints and self.HavePendingNewEvents():
            addedEvents = self.GetPendingNewEvents(currentRange)
            
            defaultTzinfo = ICUtzinfo.default
            
            def fixTimezone(d):
                if d.tzinfo is None:
                    return d.replace(tzinfo=defaultTzinfo)
                else:
                    return d.astimezone(defaultTzinfo)
                    
            date, nextDate = (fixTimezone(d) for d in currentRange)


            primaryCollection = self.blockItem.contents.collectionList[0]
            
            def insertInSortedList(eventList, newElement):
                # Could binary search here, but hopefully we're never
                # displaying that many events ... ?
                insertIndex = 0
                
                for event in eventList:
                    if event is newElement:
                        return False
                    if self.sortByStartTime(event, newElement) > 0:
                        break
                    
                    insertIndex += 1

                eventList.insert(insertIndex, newElement)
                return True
                

            itemsOnCanvas = [canvasItem.item for canvasItem in self.canvasItemList]
            for event in addedEvents:

                # skip all-day items, and items we've already drawn
                if (Calendar.isDayItem(event) or
                    event in itemsOnCanvas):
                    continue

                if insertInSortedList(self.visibleItems, event):
                    collection = self.blockItem.getContainingCollection(
                                                                 event)
                    canvasItem = TimedCanvasItem(collection, 
                                    primaryCollection, event, self)
                    self.canvasItemList.append(canvasItem)

                    numAdded += 1


            if numAdded > 0:
                # self.canvasItemList is supposed to be in the same
                # order as self.visibleItems
                keyFn = (lambda ci: ci.item.startTime)
                self.canvasItemList.sort(cmp, keyFn)

        else:
            self.ClearPendingNewEvents()
            self.visibleItems = list(self.blockItem.getItemsInRange(currentRange, 
                                                                    timedItems=True))

            self.MakeCanvasItems(resort=True)

        self.RealignCanvasItems()
        self.Refresh()

        if numAdded == 1:
            self.EditCurrentItem()

    def OnSize(self, event):
        # print "wxTimedEventsCanvas.OnSize()  to %s, %sx%s" %(self.GetPosition(), self.GetSize().width, self.GetSize().height)
        self.SetWindowGeometry()
        self._doDrawingCalculations()

        self.RefreshCanvasItems()
        event.Skip()

    def SetWindowGeometry(self):
        calendarContainer = self.blockItem.calendarContainer
        maxTextHeight = max(calendarContainer.eventLabelMeasurements.height,
                            calendarContainer.eventTimeMeasurements.height)
        
        # make sure the half-hour slot is big enough to hold one line of text
        calendarPrefs = schema.ns("osaf.framework.blocks.calendar",
                                  self.blockItem.itsView).calendarPrefs

        self.size = self.GetSize()
        self.hourHeight = calendarPrefs.getHourHeight(self.size.height,
                                                      maxTextHeight)
        self.size.height = self.hourHeight * 24
        self.size.width -= wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X) + 1
        
        self.SetVirtualSize(self.size)
        
        self._scrollYRate = self.hourHeight/3
        if self._scrollYRate == 0:
            self._scrollYRate = 1
        self.SetScrollRate(0, self._scrollYRate)
        

    def OnInit(self):
        super (wxTimedEventsCanvas, self).OnInit()

        self.SetWindowGeometry()
        
        # not sure why this doesn't scroll us to the middle
        #middle = self.size.height / 2 - self.GetSize().height/2
        # self.Scroll(0, middle/self._scrollYRate)

        self.Scroll(0, (self.hourHeight*7)/self._scrollYRate)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def ScaledScroll(self, dx, dy):
        (scrollX, scrollY) = self.CalcUnscrolledPosition(0,0)
        scrollX += dx
        scrollY += dy
        
        # rounding ensures we scroll at least one unit
        if dy < 0:
            rounding = -self._scrollYRate
        else:
            rounding = self._scrollYRate

        scaledY = (scrollY // self._scrollYRate) + rounding
        self.Scroll(scrollX, scaledY)
        
    def _doDrawingCalculations(self):

        # @@@ magic numbers
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        self.xOffset = drawInfo.xOffset

    def GetLocaleHourStrings(self, hourrange, dc):
        """
        use PyICU to format the hour, because some locales
        use a 24 hour clock
        """
        timeFormatter = DateFormat.createTimeInstance(DateFormat.SHORT)
        dummyDate = date.today()

        # This is nasty - we have to try the different formats to see
        # which one the current locale uses, we'll use 4pm as an
        # example, since its in the afternoon
        for fieldID in (DateFormat.HOUR1_FIELD,
                        DateFormat.HOUR_OF_DAY1_FIELD,
                        DateFormat.HOUR0_FIELD,
                        DateFormat.HOUR_OF_DAY0_FIELD):

            hourFP = FieldPosition(fieldID)
            timeString = timeFormatter.format(datetime.combine(dummyDate,
                                                               time(hour=16)),
                                              hourFP)
            # stop when we get a valid string
            if hourFP.getBeginIndex() != hourFP.getEndIndex():
                break

        assert hourFP.getBeginIndex() != hourFP.getEndIndex(), \
               "Dont' have an hour in the current locale's time format"

        for hour in hourrange:
            timedate = time(hour=hour, tzinfo=ICUtzinfo.default)
            hourdate = datetime.combine(dummyDate, timedate)
            timeString = timeFormatter.format(hourdate, hourFP)
            (start, end) = (hourFP.getBeginIndex(),hourFP.getEndIndex())
            hourString = unicode(timeString)[start:end]
            textExtent = dc.GetTextExtent(hourString)
            yield hour, hourString, textExtent

    def DrawBackground(self, dc):
        styles = self.blockItem.calendarContainer

        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)

        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        # add an extra 10 pixels because wx is adding 4-5 extra pixels
        # at the bottom of the virtual window.
        dc.DrawRectangle(0, 0, self.size.width+1, self.size.height + 10)

        self.ShadeToday(dc)
        self.DrawBackgroundSelection(dc)

        # Set text properties for legend
        dc.SetTextForeground(styles.legendColor)
        dc.SetFont(styles.legendFont)

        # Draw the lines separating hours
        halfHourHeight = self.hourHeight/2

        if not hasattr(self, 'localeHourStrings'):
            self.localeHourStrings = \
                list(self.GetLocaleHourStrings(range(24), dc))

        # we'll need these for hour formatting
        for hour,hourString,textExtent in self.localeHourStrings:

            if hour > 0:
                # Draw the hour legend
                wText, hText = textExtent
                dc.DrawText(hourString,
                            self.xOffset - wText - 5,
                            hour * self.hourHeight - (hText/2))
            
            # Draw the line between hours
            dc.SetPen(styles.majorLinePen)
            dc.DrawLine(self.xOffset,
                        hour * self.hourHeight,
                        self.size.width+1,
                        hour * self.hourHeight)

            # Draw the line between half hours
            dc.SetPen(styles.minorLinePen)
            dc.DrawLine(self.xOffset,
                        hour * self.hourHeight + halfHourHeight,
                        self.size.width+1,
                        hour * self.hourHeight + halfHourHeight)

        # Draw a final, bottom hour line
        dc.SetPen(styles.majorLinePen)
        dc.DrawLine(self.xOffset,
                    self.size.height,
                    self.size.width+1,
                    self.size.height)
        self.DrawDayLines(dc)
        
        legendBorderX = self.xOffset - self.legendBorderWidth/2 - 1
        pen = wx.Pen(styles.legendColor, self.legendBorderWidth)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)
        
        # hardcode this for now - eventually this should be a preference
        workdayHourStart = 9 # 9am
        workdayHourEnd = 17  # 5pm
        
        dc.DrawLine(legendBorderX, workdayHourStart*self.hourHeight,
                    legendBorderX, workdayHourEnd * self.hourHeight + 1)
        

    def DrawBackgroundSelection(self, dc):
        styles = self.blockItem.calendarContainer
        # draw selection stuff (highlighting)
        if (self._bgSelectionStartTime and self._bgSelectionEndTime):
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(styles.selectionBrush)
            
            rects = \
                self.GenerateBoundsRects(self._bgSelectionStartTime,
                                         self._bgSelectionEndTime)
            for rect in rects:
                dc.DrawRectangleRect(rect)

    @staticmethod
    def sortByStartTime(item1, item2):
        """
        Comparison function for sorting, mostly by start time
        """
        dateResult = cmp(item1.startTime, item2.startTime)
        
        # when two items start at the same time, we actually want to show the
        # SHORTER event last, so that painting draws it on top
        if dateResult == 0:
            dateResult = cmp(item2.endTime, item1.endTime)
        return dateResult

    def RebuildCanvasItems(self, resort=False):
        self.MakeCanvasItems(resort)
        self.RealignCanvasItems()

    def MakeCanvasItems(self, resort=False):
        """
        makes new canvas items based on self.visibleItems
        """
        if resort:
            self.visibleItems.sort(self.sortByStartTime)
        
        self.canvasItemList = []
        
        dragState = self.dragState
        if (dragState and
            dragState.currentDragBox):
            currentDragItem = dragState.currentDragBox.item
        else:
            currentDragItem = None
            
        primaryCollection = self.blockItem.contentsCollection
        
        # First generate a sorted list of TimedCanvasItems
        for item in self.visibleItems:
            collection = self.blockItem.getContainingCollection(item)
            canvasItem = TimedCanvasItem(collection, primaryCollection,
                                         item, self)
            self.canvasItemList.append(canvasItem)

            # if we're dragging, update the drag state to reflect the
            # newly rebuild canvasItem
            # (should probably happen in CollectionCanvas?)
            if currentDragItem is item:
                dragState.currentDragBox = canvasItem
                
    def RealignCanvasItems(self):
        """
        Takes the existing self.canvasItemList, and realigns the
        rectangles to deal with conflicts and the current drag state,
        and then resorts it to be in drawing order.
        """
        if self.dragState is not None:
            currentDragBox = self.dragState.currentDragBox
        else:
            currentDragBox = None
            
        # now generate conflict info
        self.CheckConflicts()

        # next, generate bounds rectangles for each canvasitem
        for canvasItem in self.canvasItemList:
            # drawing rects should be updated to reflect conflicts
            if (currentDragBox is canvasItem and
                currentDragBox.CanDrag()):

                (newStartTime, newEndTime) = self.GetDragAdjustedTimes()

                # override the item's start time for when the time string
                # is actually displayed in the time
                canvasItem.startTime = newStartTime
                
                canvasItem.UpdateDrawingRects(newStartTime, newEndTime)
            else:
                canvasItem.UpdateDrawingRects()
            
        # canvasItemList has to be sorted by depth
        # should be relatively quick because the canvasItemList is already
        # sorted by startTime. If no conflicts, this is an O(n) operation
        # (note that as of Python 2.4, sorts are stable, so this remains safe)
        self.canvasItemsByDate = self.canvasItemList
        self.canvasItemList = sorted(self.canvasItemsByDate,
                                     key=TimedCanvasItem.GetDrawingOrderKey)

    def DrawCells(self, dc):
        styles = self.blockItem.calendarContainer
        
        # Set up fonts and brushes for drawing the events
        dc.SetTextForeground(wx.BLACK)
        dc.SetBrush(wx.WHITE_BRUSH)

        # finally, draw the items

        def drawCanvasItems(canvasItems, selected):
            for canvasItem in canvasItems:
                canvasItem.Draw(dc, styles, selected)

        unselectedBoxes = []
        selectedBoxes = []
        contents = CalendarSelection(self.blockItem.contents)
        for canvasItem in self.canvasItemList:

            item = canvasItem.item

            # for some reason, we're getting paint events before
            # widget synchronize events, so item isn't always in contents

            # save the selected box to be drawn last
            if item in contents:
                if contents.isItemSelected(item):
                    selectedBoxes.append(canvasItem)
                else:
                    unselectedBoxes.append(canvasItem)
                    
        drawCanvasItems(unselectedBoxes, False)
        drawCanvasItems(selectedBoxes, True)

    def CheckConflicts(self):
        assert sorted(self.visibleItems, self.sortByStartTime) == self.visibleItems
        for itemIndex, canvasItem in enumerate(self.canvasItemList):
            # since these are sorted, we only have to check the items 
            # that come after the current one

            # XXX should I use itertools to avoid excess temp lists?
            # That would be islice(self.canvasItemList, itemIndex+1, None)
            canvasItem.FindConflicts(self.canvasItemList[itemIndex+1:])

            # We've found all past and future conflicts of this one,
            # so count of up the conflicts
            canvasItem.CalculateConflictDepth()

    # handle mouse related actions: move, resize, create, select
    
    def OnSelectItem(self, item):
        if item:
            # clear background selection when an existing item is selected
            self._bgSelectionStartTime = self._bgSelectionEndTime = None
        
        super(wxTimedEventsCanvas, self).OnSelectItem(item)
        
    def OnSelectNone(self, unscrolledPosition):
        selectedTime = self.getDateTimeFromPosition(unscrolledPosition)
        
        # only select something new if there's no existing selection, or if 
        # we're outside of an existing selection
        if (not self._bgSelectionStartTime or
            (selectedTime < self._bgSelectionStartTime) or
            (selectedTime > self._bgSelectionEndTime)):
            self._bgSelectionStartTime = self.getDateTimeFromPosition(unscrolledPosition)
            self._bgSelectionDragEnd = True
            self._bgSelectionEndTime = self._bgSelectionStartTime + \
                timedelta(hours=1)

        super(wxTimedEventsCanvas, self).OnSelectNone(unscrolledPosition)
        self.Refresh()

    def OnNavigateItem(self, direction):

        # find the first selected canvas item:
        currentCanvasItem = self.SelectedCanvasItem()
        if currentCanvasItem is None:
            return

        newItemIndex = -1
        canvasItemIndex = self.canvasItemsByDate.index(currentCanvasItem)

        # Using canvasItemsByDate rather than drawing-order-based
        # canvasItemList
        if direction == "UP":
            newItemIndex = canvasItemIndex - 1
        elif direction == "DOWN":
            newItemIndex = canvasItemIndex + 1
            
        elif direction in ("LEFT", "RIGHT"):
            # try to go back or forward one day, and find the nearest event
            currentDate = currentCanvasItem.item.startTime.date()
            if direction == "LEFT":
                delta = -1
                searchEnd = -1
            else:                       # "RIGHT"
                delta = 1
                searchEnd = len(self.canvasItemsByDate)
                
            newItemIndex = canvasItemIndex + delta
            foundDecentItem = False
            
            for idx in range(newItemIndex, searchEnd, delta):
                newCanvasItem = self.canvasItemsByDate[idx]
                newDate = newCanvasItem.item.startTime.date()
                
                if foundDecentItem:
                    # we've already gone back/forward at least a day, so if we
                    # hit another whole day, then we've gone too far
                    if newDate != bestDate:
                        break
                    
                    # look to see if there is something even better
                    newTimeDiff = abs(newCanvasItem.item.startTime - bestTime)
                    if newTimeDiff < timeDiff:
                        timeDiff = newTimeDiff
                        newItemIndex = idx
                    
                    
                elif newDate != currentDate:
                    foundDecentItem = True
                    
                    # found first/last item in a different date. Save
                    # for now as it is the best we have so far
                    bestTime = currentCanvasItem.item.startTime.replace(
                        year=newDate.year, month=newDate.month,
                        day=newDate.day)
                    
                    bestDate = newDate
                    
                    newItemIndex = idx
                    timeDiff = abs(newCanvasItem.item.startTime - bestTime)
                

        if 0 <= newItemIndex < len(self.canvasItemsByDate):
            self.OnSelectItem(self.canvasItemsByDate[newItemIndex].item)
            
    def OnCreateItem(self, unscrolledPosition, displayName = None):
        
        # if a region is selected, then use that for the event span
        newTime, duration = self.GetNewEventTime(unscrolledPosition)
        
        kwargs = dict(startTime=newTime, duration=duration, anyTime=False)
        if displayName is not None:
            kwargs['displayName'] = displayName
        
        event = self.CreateEmptyEvent(**kwargs)

        # now try to insert the event onto the canvas without too many
        # redraws, and allow the user to start dragging if they are
        # still holding down the mouse button (doesn't quite work yet)
        collection = self.blockItem.contentsCollection
        canvasItem = TimedCanvasItem(collection, collection, event, self)
        
        # only problem here is that we haven't checked for conflicts
        canvasItem.UpdateDrawingRects()
        canvasItem.setResizeMode(canvasItem.RESIZE_MODE_END)
        return canvasItem

    def EditCurrentItem(self):
        """
        Extend EditCurrentItem to cause edits when a background region is
        selected to create an empty item then edit it.
        """
        canvasItem = self.SelectedCanvasItem()
        if canvasItem is None and self._bgSelectionStartTime is not None:
            canvasItem = self.OnCreateItem(None, displayName = '')
        if canvasItem is not None:
            self.OnEditItem(canvasItem)

    def GetNewEventTime(self, unscrolledPosition=None):
        """
        Returns a reasonable startTime and duration for creation of an
        event, taking into account.
        """
        if (self._bgSelectionStartTime):
            # first try selection, if any
            newTime = self._bgSelectionStartTime
            duration = self._bgSelectionEndTime - newTime
            
        elif unscrolledPosition:
            newTime = self.getDateTimeFromPosition(unscrolledPosition)
            duration = timedelta(hours=1)
            
        else:
            # next try the current time today, if visible
            duration = timedelta(hours=1)
            
            now = datetime.now(ICUtzinfo.default)
            startDay, endDay = self.blockItem.GetCurrentDateRange()
            if startDay <= now <= endDay:
                # if today is in view, try to create the time about an
                # hour from now.
                newTime = now + timedelta(hours=1)
                newTime = newTime.replace(minute=roundTo(now.minute,15))
            elif self.blockItem.dayMode:
                # create the time at noon on the current day
                newTime = startDay + timedelta(hours=12)
                
            else:
                # finally, just throw it in the middle of the current view
                newTime = startDay + timedelta(days=3, hours=12)
        
        defaultTz = TimeZoneInfo.get(self.blockItem.itsView).default
        newTime = newTime.replace(tzinfo=defaultTz)
                
        return newTime, duration

    def GetCanvasItemAt(self, unscrolledPosition):
        """
        Similar to the one in CollectionCanvas, but take selection
        into account, because sometimes items on the bottom of a stack
        of conflicting events is the currently selected one.
        """
        firstHit = None
        contents = CalendarSelection(self.blockItem.contents)
        for canvasItem in reversed(self.canvasItemList):
            if canvasItem.isHit(unscrolledPosition):
                # this one is in the selection, so we can return
                # immediately
                item = canvasItem.item
                if contents.isItemSelected(item):
                    return canvasItem
                
                # otherwise, save the first hit for later, in case we
                # don't hit a selected item
                if not firstHit:
                    firstHit = canvasItem

        # if we got this far, none of the items at unscrolledPosition
        # were selected, so we can just return the first one we hit,
        # if any
        return firstHit

    def OnBeginResizeItem(self):
        if not self.dragState.currentDragBox.CanDrag():
            self.WarnReadOnlyTime([self.dragState.currentDragBox.item])
            return False
        self.StartDragTimer()
        return True
        
    def OnEndResizeItem(self):
        self.FinishDrag()
        self.StopDragTimer()
        self.dragState.originalDragBox.ResetResizeMode()
        
    def OnResizingItem(self, unscrolledPosition):
        self.RefreshCanvasItems()
    
    def OnDragTimer(self):
        """
        This timer goes off while we're dragging/resizing
        """
        if self.dragState is not None:
            scrolledPosition = self.CalcScrolledPosition(self.dragState.currentPosition)
            self.ScrollIntoView(scrolledPosition)
    
    def StartDragTimer(self):
        self.scrollTimer = wx.PyTimer(self.OnDragTimer)
        self.scrollTimer.Start(100, wx.TIMER_CONTINUOUS)
    
    def StopDragTimer(self):
        self.scrollTimer.Stop()
        self.scrollTimer = None
        
    def OnBeginDragItem(self):
        if not self.dragState.currentDragBox.CanDrag():
            self.WarnReadOnlyTime([self.dragState.currentDragBox.item])
            return False
        self.StartDragTimer()
        return True

    def FinishDrag(self):
        currentCanvasItem = self.dragState.currentDragBox
        if not currentCanvasItem.CanDrag():
            return

        proxy = RecurrenceDialog.getProxy(u'ui', currentCanvasItem.item,
                                          cancelCallback=self.RefreshCanvasItems)
        
        (startTime, endTime) = self.GetDragAdjustedTimes()
        duration = endTime - startTime
        proxy.duration = duration
        proxy.startTime = startTime
        
    def OnEndDragItem(self):
        try:
            self.FinishDrag()
        finally:
            # make sure the drag timer stops no matter what!
            self.StopDragTimer()
        self.RefreshCanvasItems()
        
    def OnDraggingNone(self, unscrolledPosition):
        dragDateTime = self.getDateTimeFromPosition(unscrolledPosition)
        if self._bgSelectionDragEnd:
            self._bgSelectionEndTime = dragDateTime
        else:
            self._bgSelectionStartTime = dragDateTime
            
        if (self._bgSelectionEndTime < self._bgSelectionStartTime):
            # swap values, drag the other end
            self._bgSelectionDragEnd = not self._bgSelectionDragEnd
            (self._bgSelectionStartTime, self._bgSelectionEndTime) = \
                (self._bgSelectionEndTime, self._bgSelectionStartTime)
        self.Refresh()
            
        
    def OnDraggingItem(self, unscrolledPosition):
        self.RefreshCanvasItems()

    def GetDragAdjustedStartTime(self, tzinfo):
        """
        When a moving drag is originated within a canvasItem, the drag
        originates from a point within the canvasItem, represented by
        dragOffset

        During a drag, you need to put a canvasItem at currentPosition,
        but you also want to make sure to round it to the nearest dayWidth,
        so that the event will sort of stick to the current column until
        it absolutely must move
        """
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        dx,dy = self.dragState.dragOffset
        dx = roundToColumnPosition(dx, drawInfo.columnPositions)
        
        position = self.dragState.currentPosition - (dx, dy)

        result = self.getDateTimeFromPosition(position, tzinfo=tzinfo)
        
        if tzinfo is None:
            result = result.replace(tzinfo=None)
            
        return result

    def GetDragAdjustedTimes(self):
        """
        Return a new start/end time for the currently selected event, based
        on the current position and drag state. Handles both move and
        resize drags
        """
        item = self.dragState.originalDragBox.item
        resizeMode = self.dragState.originalDragBox.resizeMode
        
        tzinfo = item.startTime.tzinfo

        if resizeMode is None:
            # moving an item, need to adjust just the start time
            # for the relative position of the mouse in the item
            newStartTime = self.GetDragAdjustedStartTime(tzinfo)
            newEndTime = newStartTime + item.duration

        # top/bottom resizes: just set the appropriate start/end
        # to where the mouse is
        else:
            dragTime = self.getDateTimeFromPosition(
                                self.dragState.currentPosition,
                                tzinfo=tzinfo)
            # getDateTimeFromPosition always sets a non-None tzinfo, even if
            # it's passed tzinfo=None, so we need to make sure that "floating"
            # events don't acquire a timezone.
            if tzinfo is None:
                dragTime = dragTime.replace(tzinfo=None)
                
            if resizeMode == TimedCanvasItem.RESIZE_MODE_START:
                newStartTime = dragTime
                newEndTime = item.endTime
            elif resizeMode == TimedCanvasItem.RESIZE_MODE_END:
                newEndTime = dragTime
                newStartTime = item.startTime

        if newEndTime < newStartTime:
            newEndTime = newStartTime + timedelta(minutes=15)

        return (newStartTime, newEndTime)
                    
    def getRelativeTimeFromPosition(self, drawInfo, position):
        """
        Get just the hours/minutes from the canvas
        """
        deltaHours = position.y / self.hourHeight
        deltaMinutes = ((position.y % self.hourHeight) * 60) / self.hourHeight

        # round up/down to nearest 15 minutes
        deltaMinutes = round(float(deltaMinutes)/15)*15
        return timedelta(hours=deltaHours, minutes=deltaMinutes)
        
    def getPositionFromDateTime(self, datetime):
        (startDay, endDay) = self.GetCurrentDateRange()
        
        if datetime.tzinfo is None:
            datetime = datetime.replace(tzinfo=ICUtzinfo.default)
        else:
            datetime = datetime.astimezone(ICUtzinfo.default)
            
        if datetime.date() < startDay.date() or \
           datetime.date() > endDay.date():
            raise ValueError, "Must be visible on the calendar"
        
        delta = (datetime - startDay)
        x,width = self.getColumnForDay(delta.days)
        y = int(self.hourHeight * (datetime.hour + datetime.minute/float(60)))
        return x,y,width

    def MakeRectForRange(self, startTime, endTime):
        """
        Turn a datetime range into a single rectangle that can be
        drawn on the screen
        """
        startX, startY, width = self.getPositionFromDateTime(startTime)
        
        duration = (endTime - startTime)
        duration = duration.days * 24 + duration.seconds / float(3600)
        if duration <= 0.5:
            duration = 0.5
            
        height = int(duration * self.hourHeight)
        
        return wx.Rect(startX, startY, width+1, height+1)
    
    def GenerateBoundsRects(self, startTime, endTime):
        """
        Generate a bounds rectangle for each day period. For example, an event
        that goes from noon monday to noon wednesday would have three bounds rectangles::
            one from noon monday to midnight
            one for all day tuesday
            one from midnight wednesday morning to noon wednesday
        """

        # calculate how many unique days this appears on 
        defaultTzinfo = ICUtzinfo.default
        
        if startTime.tzinfo is None:
            startTime = startTime.replace(tzinfo=defaultTzinfo)
        else:
            startTime = startTime.astimezone(defaultTzinfo)


        if endTime.tzinfo is None:
            endTime = endTime.replace(tzinfo=defaultTzinfo)
        else:
            endTime = endTime.astimezone(defaultTzinfo)
        
        # Safe to do comparison here because we've made sure
        # that neither datetime is naive
        days = 1 + (endTime.date() - startTime.date()).days
        
        currentDayStart = datetime.combine(startTime, 
                                           time(tzinfo=startTime.tzinfo))
        for i in xrange(days):
            # first calculate the midnight time for the beginning and end
            # of the current day
            currentDayEnd = currentDayStart + timedelta(days=1)
            
            # ok to use min, max, since startTime, endTime are not naive
            boundsStartTime = max(startTime, currentDayStart)
            boundsEndTime = min(endTime, currentDayEnd)
            
            try:
                rect = self.MakeRectForRange(boundsStartTime,
                                             boundsEndTime)
                yield rect
            except ValueError:
                pass
                
            currentDayStart = currentDayEnd
        
class TimedCanvasItem(CalendarCanvasItem):
    resizeBufferSize = 5
    textMargin = 4
    
    RESIZE_MODE_START = 1
    RESIZE_MODE_END = 2
    
    def __init__(self, collection, primaryCollection, item, calendarCanvas, *arguments, **keywords):
        super(TimedCanvasItem, self).__init__(collection, primaryCollection,
                                              None, item,
                                              *arguments, **keywords)
        
        # this is really annoying that we need to keep a reference back to 
        # the calendar canvas in every single TimedCanvasItem, but we
        # need it for drawing hints.. is there a better way?
        self._calendarCanvas = calendarCanvas

        # conflict management - the list of items that this item
        # conflicts with, that begin either before or after this event
        # begins
        self._beforeConflicts = []
        self._afterConflicts = []
        
        # the rating of conflicts - i.e. how far to indent this.  Just
        # a simple zero-based ordering - not a pixel count!
        self._conflictDepth = 0

    def UpdateDrawingRects(self, startTime=None, endTime=None):

        # allow caller to override start/end time
        item = self.item
        
        if not startTime:
            startTime = item.startTime
            
        if not endTime:
            endTime = item.endTime
       
        if self._calendarCanvas.blockItem.dayMode:
            # in day mode, canvasitems are drawn side-by-side
            maxDepth = self.GetMaxDepth()
            indentLevel = self.GetIndentLevel()
            def UpdateForConflicts(rect):
                rect.width /= (maxDepth + 1)
                rect.x += rect.width * indentLevel
        else:
            # in week mode, stagger the canvasitems by 5 pixels            
            indent = self.GetIndentLevel() * 10
            widthAdjust = self.GetMaxDepth() * 10
            def UpdateForConflicts(rect):
                rect.width -= widthAdjust
                rect.x += indent

        self._boundsRects = \
            list(self._calendarCanvas.GenerateBoundsRects(startTime, endTime))

        for rect in self._boundsRects:
            UpdateForConflicts(rect)

        self._bounds = self._boundsRects[0]

        # Store top/bottom resize rects for fast hit-testing to update
        # the cursor
        r = self._boundsRects[-1]
        self._resizeLowBounds = wx.Rect(r.x, r.y + r.height - self.resizeBufferSize,
                                        r.width, self.resizeBufferSize)
        
        r = self._boundsRects[0]
        self._resizeTopBounds = wx.Rect(r.x, r.y,
                                        r.width, self.resizeBufferSize)

    def GetBoundsRects(self):
        return self._boundsRects

    def isHitResize(self, point):
        """
        Hit testing of a resize region.
        
        @param point: point in unscrolled coordinates
        @type point: wx.Point
        @return: True if the point hit the resize region
        @rtype: Boolean
        """
        return (self._resizeTopBounds.Inside(point) or
                self._resizeLowBounds.Inside(point))

    def isHit(self, point):
        """
        User may have clicked in any of the possible bounds
        """
        for rect in self._boundsRects:
            if rect.Inside(point):
                return True
        return False

    def getResizeMode(self, point):
        """
        Returns the mode of the resize, either RESIZE_MODE_START or
        RESIZE_MODE_END.

        The resize mode is RESIZE_MODE_START if dragging from the top of the
        event, and RESIZE_MODE_END if dragging from the bottom of the
        event. None indicates that we are not resizing at all.

        The whole _forceResizeMode is to make sure that we stay in the same
        mode during a drag, even if we mouseover another region that would
        cause a different drag mode

        AF: This should really be handled automatically by the dragging code

        @param point: drag start position in uscrolled coordinates
        @type point: wx.Point
        @return: resize mode, RESIZE_MODE_START, RESIZE_MODE_END or None
        @rtype: string or None
        """
        
        if hasattr(self, '_forceResizeMode'):
            return self._forceResizeMode
            
        if self._resizeTopBounds.Inside(point):
            return self.RESIZE_MODE_START
        if self._resizeLowBounds.Inside(point):
            return self.RESIZE_MODE_END
        return None
        
    def setResizeMode(self, mode):
        self._forceResizeMode = mode

    def ResetResizeMode(self):
        if hasattr(self, '_forceResizeMode'):
            del self._forceResizeMode

    def StartDrag(self, position):
        self.resizeMode = self.getResizeMode(position)
    

    def FindConflicts(self, possibleConflicts):
        """
        Search through the list of possible conflicts, which need to
        be sorted such that any possible conflicts are at the start of
        the list
        """
        for conflict in possibleConflicts:
            # we know we're done when we stop hitting conflicts
            # 
            # have a guarantee that conflict.startTime >= item.endTime
            # Since item.endTime < item.startTime, we know we're
            # done

            # plus, we also have to make sure that two zero-length
            # events that have the same start time still conflict
            if ((conflict.item.startTime >= self.item.endTime) and
                (conflict.item.startTime != self.item.startTime)):
                 break

            # item and conflict MUST conflict now
            self.AddConflict(conflict)
            
    def AddConflict(self, child):	
        """	
        Register a conflict with another event - this should only be done
        to add conflicts with 'child' events, because the child is notified
        about the parent conflicts	
        """
        # we might want to keep track of the inverse conflict as well,
        # for conflict bars
        child._beforeConflicts.append(self)
        self._afterConflicts.append(child)
        
    def CalculateConflictDepth(self):
        """
        Calculate the 'depth', or indentation level, of the current item
        This is done with the assumption that all parent conflicts have	
        already had their conflict depths calculated.	
        """
        # We'll find out the depth of all our parents, and then
        # see if there's an empty gap we can fill
        # this relies on parentDepths being sorted, which 
        # is true because the conflicts are added in 
        # the same order as the they appear in the calendar
        parentDepths = [parent._conflictDepth for parent in self._beforeConflicts]
        self._conflictDepth = self.FindFirstGapInSequence(parentDepths)
        return self._conflictDepth
        
    def GetIndentLevel(self):
        """
        The calculated conflictdepth is the indentation level
        """
        return self._conflictDepth
        
    def GetMaxDepth(self):	
        """	
        This determines how 'deep' this item is: the maximum	
        Indent Level of ALL items that CONFLICT with this one.	
        e.g. 3 items might conflict, and they all might be indented by	
        one due to an earlier conflict, so the maximum 'depth' is 4.	
        """
        maxparents = maxchildren = 0
        if self._afterConflicts:
            maxchildren = max([child.GetIndentLevel() for child in self._afterConflicts])
        if self._beforeConflicts:
            maxparents = max([parent.GetIndentLevel() for parent in self._beforeConflicts])
        return max(self.GetIndentLevel(), maxchildren, maxparents)

    def GetDrawingOrderKey(self):
        """
        Drawing order defined first by activeness, then level of indent
        """
        return (self.isActive, self.GetIndentLevel())
