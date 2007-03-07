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
    wxCalendarCanvas, roundTo, roundToColumnPosition, widgetGuardedCallback,
    wxInPlaceEditor
    )
from CollectionCanvas import DragState
from PyICU import FieldPosition, DateFormat, ICUtzinfo
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim import isDead
from osaf.pim.calendar.TimeZone import TimeZoneInfo, coerceTimeZone

from time import time as epochtime
from itertools import chain, islice
from osaf.framework.blocks.Block import WithoutSynchronizeWidget
from osaf.pim.structs import SizeType

from application.dialogs import RecurrenceDialog

IS_MAC = '__WXMAC__' in wx.PlatformInfo

class TimedEventsCanvas(CalendarBlock):

    scrollY = schema.One(schema.Integer, initialValue = -1)

    def onSetFocusEvent (self, event):
        self.widget.SetFocus()

    def render(self, *args, **kwds):
        super(TimedEventsCanvas, self).render(*args, **kwds)

        prefs = schema.ns('osaf.framework.blocks.calendar', self.itsView).calendarPrefs
        self.itsView.watchItem(self, prefs, 'onCalendarPrefsChange')

        tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        self.itsView.watchItem(self, tzPrefs, 'onTZPrefsChange')

    def onDestroyWidget(self, *args, **kwds):

        prefs = schema.ns('osaf.framework.blocks.calendar', self.itsView).calendarPrefs
        self.itsView.unwatchItem(self, prefs, 'onCalendarPrefsChange')

        tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        self.itsView.unwatchItem(self, tzPrefs, 'onTZPrefsChange')

        super(TimedEventsCanvas, self).onDestroyWidget(*args, **kwds)
        

    def onCalendarPrefsChange(self, op, item, names):
        self.widget.SetWindowGeometry()
        self.widget.RealignCanvasItems()
        self.widget.Refresh()

    def onTZPrefsChange(self, op, item, names):
        self.widget.SetWindowGeometry()
        self.widget.wxSynchronizeWidget()

    def instantiateWidget(self):
        super(TimedEventsCanvas, self).instantiateWidget()
        return wxTimedEventsCanvas(self.parentBlock.widget)

    def setRange(self, date):
        super(TimedEventsCanvas, self).setRange(date)
        if getattr(self, 'widget', None):
            self.widget.orderLast = []


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
        
        self.orderLast = []
        self.drawOrderedCanvasItems = []
        self.xOffset = 0
        
    def setScroll(self):
        scrollY = self.blockItem.scrollY
        if scrollY < 0:
            # A scrollY value of -1 (it's initial value) is used as way to
            # specify a scroll position of 6AM, which is difficult to calculate
            # during repository creation time because it depends on runtime
            # window sizes.
            scrollY = (self.hourHeight * 6) / self.GetScrollPixelsPerUnit()[1]
        self.Scroll(0, scrollY)

    def wxSynchronizeWidget(self, useHints=False):
        self.SetSize ((self.blockItem.size.width, self.blockItem.size.height))
        self.setScroll()
        currentRange = self.GetCurrentDateRange()
        self._doDrawingCalculations()

        # The only hints we understand are event additions.
        # So, if any other kind of hints have been received,
        # fall back to a full synchronize.
        
        numAdded = 0 # The events may not be timed, or may fall
                     # outside our range, etc,
                     
        if useHints and self.HavePendingNewEvents():
            removals = []
            for i in self.visibleItems:
                # clean up visibleItems, removing stale items and events that
                # have become masters 
                if isDead(i.itsItem) or i.isRecurrenceMaster():
                    self.visibleItems.remove(i)
                    removals.append(i.itsItem)
            for canvasItem in self.canvasItemList:
                if canvasItem.item in removals:
                    self.canvasItemList.remove(canvasItem)
             
            addedEvents = self.GetPendingNewEvents(currentRange)
            
            defaultTzinfo = ICUtzinfo.default
            
            def fixTimezone(d):
                if d.tzinfo is None:
                    return d.replace(tzinfo=defaultTzinfo)
                else:
                    return d.astimezone(defaultTzinfo)
                    
            date, nextDate = (fixTimezone(d) for d in currentRange)


            primaryCollection = self.blockItem.contentsCollection
            
            def insertInSortedList(itemList, newElement, attr=None):
                # iterate over itemList, if attr isn't None, get attr to find
                # the event to be sorted against. Could do a binary search, too
                # bad bisect doesn't accept a cmp argument...
                insertIndex = 0

                new = newElement                
                if attr is not None:
                    new = getattr(newElement, attr)
                
                for item in itemList:
                    if attr is not None:
                        item = getattr(item, attr)
                    if self.sortByStartTime(item, new) > 0:
                        break
                    
                    insertIndex += 1

                itemList.insert(insertIndex, newElement)
            
            
            for event in addedEvents:

                # skip all-day items, and items we've already drawn
                if (Calendar.isDayEvent(event) or event in self.visibleItems):
                    continue

                insertInSortedList(self.visibleItems, event)
                collection = self.blockItem.getContainingCollection(event, primaryCollection)
                canvasItem = TimedCanvasItem(collection, primaryCollection,
                                             event, self)
                
                insertInSortedList(self.canvasItemList, canvasItem, 'event')
                numAdded += 1

        else:
            self.ClearPendingNewEvents()
            self.visibleItems = list(self.blockItem.getEventsInRange(currentRange, 
                                                                    timedItems=True))

            self.MakeCanvasItems(resort=True)

        self.RealignCanvasItems()
        self.Refresh()

        if numAdded == 1 and getattr(self, 'justCreatedCanvasItem', None):
            self.OnSelectItem(self.justCreatedCanvasItem.item)
            self.justCreatedCanvasItem = None
            self.EditCurrentItem()

    @WithoutSynchronizeWidget
    def OnSize(self, event):
        self.SetWindowGeometry()
        self._doDrawingCalculations()

        self.RefreshCanvasItems(resort=False)
        newSize = self.GetSize()
        self.blockItem.size = SizeType (newSize.width, newSize.height)
        self.setScroll()
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
        

    def OnHover (self, x, y, dragResult):
        """
        Scroll the canvas in the y axis if the cursor is in the top or bottom
        half hour.
        
        """
        if not hasattr(self, 'lastHover'):
            self.lastHover = epochtime() - 1 # one second ago
        if epochtime() > self.lastHover + .05: # 20 scrolls a second
            self.ScrollIntoView(wx.Point(x, y), self.hourHeight)
        
        return super(wxTimedEventsCanvas, self).OnHover(x, y, dragResult)

    def OnLeave(self):
        """
        Stop the drag timer when we leave.        
        """
        self.StopDragTimer()
        return super(wxTimedEventsCanvas, self).OnLeave()

    def makeCoercedCanvasItem(self, x, y, item):
        primaryCollection = self.blockItem.contentsCollection
        collection = self.blockItem.getContainingCollection(item, primaryCollection)
        canvasItem = TimedCanvasItem(collection, primaryCollection, item, self)        
        
        unscrolledPosition = wx.Point(*self.CalcUnscrolledPosition(x, y))
        event = canvasItem.event
        start = self.getDateTimeFromPosition(unscrolledPosition,
                                             event.startTime.tzinfo)
        end = start + max(event.duration, timedelta(hours=1))
        
        canvasItem.UpdateDrawingRects(start, end)
        
        self.coercedCanvasItem  = canvasItem
        noop = lambda x: None
        self.dragState = DragState(canvasItem, self, noop,
                                   noop, self.FinishDrag,
                                   unscrolledPosition)
        self.dragState.dragged = True
        
        self.dragState._dragStarted = True
        self.dragState.originalDragBox = canvasItem
        self.dragState.currentPosition = unscrolledPosition
        self.dragState._dragDirty = True

    def OnInit(self):
        super (wxTimedEventsCanvas, self).OnInit()
        self.editor = wxInPlaceEditor(self, defocusCallback=self.SetPanelFocus)

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
            rounding = -1
        else:
            rounding = 1

        scaledY = (scrollY // self._scrollYRate) + rounding
        self.Scroll(scrollX, scaledY)
        self.blockItem.scrollY = self.GetViewStart()[1]

    def ScrollToEvent(self, event, buffer=10):
        (startDay, endDay) = self.GetCurrentDateRange()

        # scroll both end and start time into view, if possible
        if event.endTime < endDay:
            x,y,width = self.getPositionFromDateTime(event.endTime)
            self.ScrollIntoView(self.CalcScrolledPosition(wx.Point(x,y)),buffer)

        if event.startTime > startDay:
            x,y,width = self.getPositionFromDateTime(event.startTime)
            self.ScrollIntoView(self.CalcScrolledPosition(wx.Point(x,y)),buffer)

            
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
            # timeFormatter.format will alter hourFP in place
            timeFormatter.format(datetime.combine(dummyDate, time(hour=16)),
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
            
            if IS_MAC:
                dc.SetAntiAliasing(False)
            
            # Draw the line between hours
            dc.SetPen(styles.majorLinePen)
            dc.DrawLine(self.xOffset,
                        hour * self.hourHeight,
                        self.size.width+1,
                        hour * self.hourHeight)
            
            # Draw a line for noon, bug 5781
            if hour == 12:
                dc.DrawLine(10,                       12 * self.hourHeight,
                            self.xOffset - wText - 8, 12 * self.hourHeight)

            # Draw the line between half hours
            dc.SetPen(styles.minorLinePen)
            dc.DrawLine(self.xOffset,
                        hour * self.hourHeight + halfHourHeight,
                        self.size.width+1,
                        hour * self.hourHeight + halfHourHeight)

            if IS_MAC:
                dc.SetAntiAliasing(True)

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
    def sortByStartTime(event1, event2):
        """
        Comparison function for sorting, mostly by start time
        """
        if isDead(event1.itsItem) or isDead(event2.itsItem):
            # sort stale or deleted items first, False < True
            return cmp(not isDead(event1.itsItem),
                       not isDead(event2.itsItem))
                       
        dateResult = cmp(event1.startTime, event2.startTime)
        
        # when two events start at the same time, we actually want to show the
        # SHORTER event last, so that painting draws it on top
        if dateResult == 0:
            dateResult = cmp(event2.endTime, event1.endTime)
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
        
        canvasItemList = []
        
        dragState = self.dragState
        if (dragState and
            dragState.currentDragBox):
            currentDragItem = dragState.currentDragBox.item
        else:
            currentDragItem = None
            
        primaryCollection = self.blockItem.contentsCollection
                
        # First generate a sorted list of TimedCanvasItems
        for event in self.visibleItems:
            if isDead(event.itsItem):
                continue
            collection = self.blockItem.getContainingCollection(event.itsItem, primaryCollection)
            canvasItem = TimedCanvasItem(collection, primaryCollection,
                                         event, self)
            canvasItemList.append(canvasItem)

            # if we're dragging, update the drag state to reflect the
            # newly rebuild canvasItem
            # (should probably happen in CollectionCanvas?)
            if currentDragItem is event.itsItem:
                dragState.currentDragBox = canvasItem

        if self.coercedCanvasItem is not None and dragState is not None:
            canvasItemList.append(self.coercedCanvasItem)
            dragState.currentDragBox = self.coercedCanvasItem

        # have to do this last, because MakeCanvasItems occasionally recurses
        self.canvasItemList = canvasItemList

                
    def RealignCanvasItems(self):
        """
        Takes the existing self.canvasItemList and realigns the
        rectangles to deal with conflicts and the current drag state.
        
        """
        if self.dragState is not None:
            currentDragBox = self.dragState.currentDragBox
        else:
            currentDragBox = None
        
        # now generate conflict info
        self.CheckConflicts()

        self.SetDrawOrder()

        # next, generate bounds rectangles for each canvasitem
        for canvasItem in self.canvasItemList:
            if not isDead(canvasItem.item):
                # drawing rects should be updated to reflect conflicts
                if (currentDragBox is canvasItem and
                    currentDragBox.CanDrag()):
    
                    (newStartTime, newEndTime) = self.GetDragAdjustedTimes()
    
                    # override the item's start time for when the time string
                    # is actually displayed in the time
                    canvasItem.startTime = newStartTime
                    canvasItem.endTime   = newEndTime
                    
                    canvasItem.UpdateDrawingRects(newStartTime, newEndTime)
                else:
                    canvasItem.UpdateDrawingRects()


    def DrawCells(self, dc):
        styles = self.blockItem.calendarContainer
        
        # Set up fonts and brushes for drawing the events
        dc.SetTextForeground(wx.BLACK)
        dc.SetBrush(wx.WHITE_BRUSH)

        contents = CalendarSelection(self.blockItem.contents)

        for canvasItem in self.drawOrderedCanvasItems:
            # drawOrderedCanvasItems can be out of date if another view deletes
            # an item (isDead() will be True), or if a RefreshCanvasItems
            # hasn't yet occurred after a deletion.
            if isDead(canvasItem.item) or canvasItem.item not in contents:
                continue
            selected = contents.isItemSelected(canvasItem.item)
            canvasItem.Draw(dc, styles, selected)

    def SetDrawOrder(self):
        """
        Calculate the order of canvas items, taking selection, history, and
        active collection into account.
        
        """
        ordered       = []
        selectedBoxes = []
        activeBoxes   = []
        orderLastMap  = {}
        contents = CalendarSelection(self.blockItem.contents)

        draggedOutItem = self._getHiddenOrClearDraggedOut()

        for canvasItem in self.canvasItemList:
            item = canvasItem.item
            
            if item is draggedOutItem or isDead(item):
                # don't render deleted items or items we're dragging out of the
                # canvas
                continue

            if item in contents:
                if contents.isItemSelected(item):
                    selectedBoxes.append(canvasItem)
                elif item in self.orderLast:
                    orderLastMap[item] = canvasItem
                elif canvasItem.isActive:
                    activeBoxes.append(canvasItem)
                else:
                    ordered.append(canvasItem)

        ordered.extend(activeBoxes)
        ordered.extend(orderLastMap.get(i) for i in self.orderLast if \
                       orderLastMap.get(i) is not None)
        ordered.extend(selectedBoxes)
        
        self.drawOrderedCanvasItems = ordered

    def CheckConflicts(self):
        assert (sorted([i for i in self.visibleItems if not isDead(i.itsItem)],
                       self.sortByStartTime) == 
                [i for i in self.visibleItems if not isDead(i.itsItem)])
        for itemIndex, canvasItem in enumerate(self.canvasItemList):
            if self.coercedCanvasItem is not canvasItem \
               and not isDead(canvasItem.item):
                   # since these are sorted, we only have to check the items 
                   # that come after the current one
                   canvasItem.FindConflicts(islice(self.canvasItemList,
                                                   itemIndex+1, None))
       
                   # We've found all past and future conflicts of this one,
                   # so count of up the conflicts
                   canvasItem.CalculateConflictDepth()

    # handle mouse related actions: move, resize, create, select
    
    def OnSelectItem(self, item):
        if item:
            # clear background selection when an existing item is selected
            self._bgSelectionStartTime = self._bgSelectionEndTime = None
            # put recently selected items in a list of items to be displayed 
            # on top of other items
            if item in self.orderLast:
                self.orderLast.remove(item)
            self.orderLast.append(item)
            for i, canvasItem in enumerate(self.drawOrderedCanvasItems):
                if canvasItem.item is item:
                    del self.drawOrderedCanvasItems[i]
                    self.drawOrderedCanvasItems.append(canvasItem)
                    break
            
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

        # no items to select
        if len(self.canvasItemList) == 0:
            return

        # find the first selected canvas item:
        currentCanvasItem = self.SelectedCanvasItem()
        if currentCanvasItem is None:
            # nothing currently selected, just select the middle item
            # (should probably select one that is guaranteed to be visible)
            middle = len(self.canvasItemList)/2
            currentCanvasItem = self.canvasItemList[middle]
            self.OnSelectItem(currentCanvasItem.item)
            return

        newItemIndex = -1
        canvasItemIndex = self.canvasItemList.index(currentCanvasItem)

        if direction == "UP":
            newItemIndex = canvasItemIndex - 1
        elif direction == "DOWN":
            newItemIndex = canvasItemIndex + 1
            
        elif direction in ("LEFT", "RIGHT"):
            # try to go back or forward one day, and find the nearest event
            currentDate = currentCanvasItem.event.startTime.date()
            if direction == "LEFT":
                delta = -1
                searchEnd = -1
            else:                       # "RIGHT"
                delta = 1
                searchEnd = len(self.canvasItemList)
                
            newItemIndex = canvasItemIndex + delta
            foundDecentItem = False
            
            for idx in range(newItemIndex, searchEnd, delta):
                newCanvasItem = self.canvasItemList[idx]
                newDate = newCanvasItem.event.startTime.date()
                
                if foundDecentItem:
                    # we've already gone back/forward at least a day, so if we
                    # hit another whole day, then we've gone too far
                    if newDate != bestDate:
                        break
                    
                    # look to see if there is something even better
                    newTimeDiff = abs(newCanvasItem.event.startTime - bestTime)
                    if newTimeDiff < timeDiff:
                        timeDiff = newTimeDiff
                        newItemIndex = idx
                    
                    
                elif newDate != currentDate:
                    foundDecentItem = True
                    
                    # found first/last item in a different date. Save
                    # for now as it is the best we have so far
                    bestTime = currentCanvasItem.event.startTime.replace(
                        year=newDate.year, month=newDate.month,
                        day=newDate.day)
                    
                    bestDate = newDate
                    
                    newItemIndex = idx
                    timeDiff = abs(newCanvasItem.event.startTime - bestTime)
                

        if 0 <= newItemIndex < len(self.canvasItemList):
            self.OnSelectItem(self.canvasItemList[newItemIndex].item)
            
    def OnCreateItem(self, unscrolledPosition, displayName = None):
        
        # if a region is selected, then use that for the event span
        newTime, duration = self.GetNewEventTime(unscrolledPosition)
        
        kwargs = dict(startTime=newTime, duration=duration, anyTime=False)
        if displayName is not None:
            kwargs['summary'] = displayName
        
        event = self.CreateEmptyEvent(**kwargs)

        # now try to insert the event onto the canvas without too many
        # redraws, and allow the user to start dragging if they are
        # still holding down the mouse button (doesn't quite work yet)
        collection = self.blockItem.contentsCollection
        canvasItem = TimedCanvasItem(collection, collection, event, self)
        
        # set a flag so when wxSynchronizeWidgets happens, the newly created
        # item is edited
        self.justCreatedCanvasItem = canvasItem
        
        # only problem here is that we haven't checked for conflicts
        canvasItem.UpdateDrawingRects()
        canvasItem.setResizeMode(canvasItem.RESIZE_MODE_END)
        return canvasItem

    def EditCurrentItem(self, keyPressed = False):
        """
        Extend EditCurrentItem to cause edits when a background region is
        selected to create an empty item then edit it.
        """
        canvasItem = self.SelectedCanvasItem()
        if canvasItem is None and self._bgSelectionStartTime is not None:
            if keyPressed:
                # an empty displayName (rather than the default, "New Event")
                # is used as a flag to indicate that a key has been pressed
                # when the inPlaceEditor sets its contents
                canvasItem = self.OnCreateItem(None, '')
            else:
                canvasItem = self.OnCreateItem(None)
        if canvasItem is not None:
            self.OnEditItem(canvasItem)

    def GetNewEventTime(self, unscrolledPosition=None):
        """
        Returns a reasonable startTime and duration for creation of an
        event, on the hour less than 60 minutes later than the current time,
        and the current day of the week if in week mode.
        """
        defaultTz = TimeZoneInfo.get(self.blockItem.itsView).default
        startDay, endDay = self.blockItem.GetCurrentDateRange()
        
        if (self._bgSelectionStartTime and 
            (self._bgSelectionStartTime <= endDay and
             self._bgSelectionEndTime   >= startDay)):
            # if any part of selection is visible, use selection
            newTime = self._bgSelectionStartTime
            duration = self._bgSelectionEndTime - newTime
            
        elif unscrolledPosition:
            newTime = self.getDateTimeFromPosition(unscrolledPosition)
            duration = timedelta(hours=1)
            
        else:
            # implements bug 5820, use the current time and the currently
            # displayed day or the appropriate weekday
            duration = timedelta(hours=1)

            now = datetime.now(defaultTz)
            
            newTime = datetime.combine(startDay.date(), now.time())
            newTime += timedelta(minutes=60)
            newTime = newTime.replace(minute=roundTo(newTime.minute, 60),
                                      second=0, microsecond=0)

            if self.blockItem.dayMode:
                if newTime.date() != startDay.date():
                    # this could happen if the current time is, say 11:10PM
                    newTime = datetime.combine(startDay.date(), newTime.time())
            else:
                # move newTime to the appropriate day of the week
                days = (now.isoweekday() - startDay.isoweekday()) % 7
                if newTime.date() != startDay.date() and days == 6:
                    # transition from one week to the next, move it backwards
                    # rather than putting it out of view
                    days -= 7                
                newTime += timedelta(days)
                
        newTime = newTime.replace(tzinfo=defaultTz)
                
        return newTime, duration

    def GetCanvasItemAt(self, unscrolledPosition):
        """
        Similar to the one in CollectionCanvas, but take selection
        into account, because sometimes items on the bottom of a stack
        of conflicting events is the currently selected one.
        """
        for canvasItem in reversed(self.drawOrderedCanvasItems):
            if not isDead(canvasItem.item) and \
               canvasItem.isHit(unscrolledPosition):
                return canvasItem


    def OnBeginResizeItem(self):
        if not self.dragState.currentDragBox.CanDrag():
            self.WarnReadOnlyTime([self.dragState.currentDragBox.item])
            return False
        self.StartDragTimer()
        return True
        
    def OnEndResizeItem(self):
        # get canvasItem before FinishDrag sets self.dragState to None
        canvasItem = self.dragState.originalDragBox
        self.FinishDrag()
        self.StopDragTimer()
        canvasItem.ResetResizeMode()
        
    def OnResizingItem(self, unscrolledPosition):
        self.RefreshCanvasItems(resort=False)
    
    def OnDragTimer(self):
        """
        This timer goes off while we're resizing
        """
        if self.dragState is not None:
            scrolledPosition = self.CalcScrolledPosition(self.dragState.currentPosition)
            self.ScrollIntoView(scrolledPosition, self.hourHeight)
    
    def StartDragTimer(self):
        self.scrollTimer = wx.PyTimer(self.OnDragTimer)
        self.scrollTimer.Start(100, wx.TIMER_CONTINUOUS)
    
    def StopDragTimer(self):
        # drags of object from outside Chandler won't initiate timer
        if hasattr(self, 'scrollTimer') and self.scrollTimer is not None:
            self.scrollTimer.Stop()
        self.scrollTimer = None
        
    def OnBeginDragItem(self):
        self.StartDragTimer()
        return True

    def FinishDrag(self):
        self.fileDragPosition = None
        currentCanvasItem = self.dragState.currentDragBox
        if not currentCanvasItem.CanDrag():
            return

        currentCanvasItem.startTime = currentCanvasItem.endTime = None

        callback = widgetGuardedCallback(self.blockItem,
                                         self.wxSynchronizeWidget)
        proxy = RecurrenceDialog.getProxy(u'ui', currentCanvasItem.item,
                                          endCallback=callback)
        
        self.activeProxy = proxy
        
        if self.dragState.dragged:
            (startTime, endTime) = self.GetDragAdjustedTimes()
            duration = endTime - startTime
            stampedProxy = Calendar.EventStamp(proxy)
            stampedProxy.duration = duration
            stampedProxy.startTime = startTime
        
            if self.coercedCanvasItem is not None:
                self.coercedCanvasItem = None
                stampedProxy.allDay = stampedProxy.anyTime = False
        self.dragState = None
        
    def OnEndDragItem(self):
        try:
            self.FinishDrag()
        finally:
            # make sure the drag timer stops no matter what!
            self.StopDragTimer()
        self.RefreshCanvasItems(resort=True)
        
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
        self.RefreshCanvasItems(resort=False)

    def GetDragAdjustedTimes(self):
        """
        Return a new start/end time for the currently selected event, based
        on the current position and drag state. Handles both move and
        resize drags
        """
        tzprefs = schema.ns('osaf.pim', self.blockItem.itsView).TimezonePrefs
        useTZ = tzprefs.showUI
        
        event = Calendar.EventStamp(self.dragState.originalDragBox.item)
        resizeMode = self.dragState.originalDragBox.resizeMode
        
        oldTZ = event.startTime.tzinfo
        
        if useTZ:
            tzinfo = oldTZ
        else:
            tzinfo = ICUtzinfo.floating

        if resizeMode is None:
            # moving an event, need to adjust just the start time
            # for the relative position of the mouse in the event
            newStartTime = self.GetDragAdjustedStartTime(tzinfo)
            newEndTime = newStartTime + event.duration

        # top/bottom resizes: just set the appropriate start/end
        # to where the mouse is
        else:
            dragTime = self.getDateTimeFromPosition(
                                self.dragState.currentPosition,
                                tzinfo=tzinfo)
                
            if resizeMode == TimedCanvasItem.RESIZE_MODE_START:
                newStartTime = dragTime
                newEndTime = event.endTime
            elif resizeMode == TimedCanvasItem.RESIZE_MODE_END:
                newEndTime = dragTime
                newStartTime = event.startTime

        if newEndTime < newStartTime:
            newEndTime = newStartTime + timedelta(minutes=15)

        if not useTZ:
            newEndTime   = newEndTime.replace(tzinfo = oldTZ)
            newStartTime = newStartTime.replace(tzinfo = oldTZ)

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
        
        datetime = coerceTimeZone(datetime, ICUtzinfo.default)
            
        if datetime.date() < startDay.date() or \
           datetime.date() >= endDay.date():
            raise ValueError, "Must be visible on the calendar"
        
        delta = (datetime.date() - startDay.date())
        x,width = self.getColumnForDay(delta.days)
        y = int(self.hourHeight * (datetime.hour + datetime.minute/float(60)))
        return x,y,width

    def MakeRectForRange(self, startTime, endTime):
        """
        Turn a datetime range into a single rectangle that can be
        drawn on the screen
        """
        startX, startY, width = self.getPositionFromDateTime(startTime)
        
        # calculating height from duration leads to variations in end position
        # when the start time is dragged, so instead calculate the bottom from 
        # endTime
        
        days = (endTime.date() - startTime.date()).days
        
        height = int(self.hourHeight *
                     (24 * days + endTime.hour + endTime.minute/60.0) - startY)
        height = max(height, self.hourHeight / 2 + self.hourHeight % 2)
        
        return wx.Rect(startX, startY, width+1, height+1)
    
    def GenerateBoundsRects(self, startTime, endTime):
        """
        Generate a bounds rectangle for each day period. For example, an event
        that goes from noon monday to noon wednesday would have three bounds rectangles::
            one from noon monday to midnight
            one for all day tuesday
            one from midnight wednesday morning to noon wednesday
        """

        # put events onto the canvas translated into the local timezone,
        # unless timezone display is off.
        if schema.ns('osaf.pim', self.blockItem.itsView).TimezonePrefs.showUI:
            startTime = coerceTimeZone(startTime, ICUtzinfo.default)
            endTime   = coerceTimeZone(endTime,   ICUtzinfo.default)
        else:
            startTime = startTime.replace(tzinfo=ICUtzinfo.floating)
            endTime   = endTime.replace(tzinfo=ICUtzinfo.floating)

        # calculate how many unique days this appears on 
        days = 1 + (endTime.date() - startTime.date()).days
        if endTime.time() == time(0) and days > 1:
            # events that end at midnight end on the next day, but don't have
            # any duration then, so they have one fewer rects
            days -= 1
        
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

    def belongsOnCanvas(self, item):
        # Return False if this item no longer belongs on this canvas
        event = Calendar.EventStamp(item)
        return not (event.allDay or event.anyTime)
        
class TimedCanvasItem(CalendarCanvasItem):
    resizeBufferSize = 5
    textMargin = 2
    swatchAdjust = 0
    
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
        self.resizeMode = None

    def UpdateDrawingRects(self, startTime=None, endTime=None):

        # allow caller to override start/end time
        item = self.item
        if item == self._calendarCanvas.activeProxy:
            # items and proxies compare as equal, but they're not quite
            event = Calendar.EventStamp(self._calendarCanvas.activeProxy)
        else:
            event = self.event

        if not startTime:
            startTime = event.startTime
            
        if not endTime:
            # We're not using the calculated attribute (self.endTime), because
            # proxy handling of changed attributes isn't smart enough to handle
            # calculated attributes
            endTime = startTime + event.duration
       
        if self._calendarCanvas.blockItem.dayMode:
            # in day mode, canvasitems are drawn side-by-side
            maxDepth = self.GetMaxDepth()
            indentLevel = self.GetIndentLevel()
            def UpdateForConflicts(rect):
                rect.width /= (maxDepth + 1)
                rect.x += rect.width * indentLevel
        else:
            # in week mode, if there is a conflict, make the event be
            # 80% of the available width
            newWidthPercent = .80
            indentPercent = 1-newWidthPercent
            
            level = self.GetIndentLevel()
            indent = level * indentPercent
            conflicts = self.GetMaxDepth()

            def UpdateForConflicts(rect):
                if conflicts > 0:
                    delta = int(rect.width * indent / conflicts)
                    rect.x += delta
                    # make sure the last lozenge overlaps the right hand border
                    if level == conflicts:
                        rect.width = rect.width - delta
                    else:
                        rect.width *= newWidthPercent
                    

        self._boundsRects = \
            list(self._calendarCanvas.GenerateBoundsRects(startTime, endTime))

        for rect in self._boundsRects:
            UpdateForConflicts(rect)

        if self._boundsRects:   # is empty when events not in calendar range
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
            if isDead(conflict.item):
                continue
            # we know we're done when we stop hitting conflicts
            # 
            # have a guarantee that conflict.startTime >= event.endTime
            # Since item.endTime < item.startTime, we know we're
            # done

            # plus, we also have to make sure that two zero-length
            # events that have the same start time still conflict
            
            if ((conflict.event.startTime >= self.event.endTime) and
                (conflict.event.startTime != self.event.startTime)):
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
        if self not in child._beforeConflicts:
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
