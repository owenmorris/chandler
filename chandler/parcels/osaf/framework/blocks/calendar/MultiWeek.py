#   Copyright (c) 2007-2009 Open Source Applications Foundation
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

import wx
from datetime import *
import itertools
import logging
from operator import add

from application import styles
from i18n import ChandlerMessageFactory as _
from osaf.framework.blocks import Block, Styles, ContainerBlocks
from osaf.pim import EventStamp
from CalendarCanvas import (CalendarContainer, wxCalendarContainer, IS_MAC,
                            IS_GTK, nth, wxCalendarControl, CalendarControl,
                            wxCalendarCanvas, dateFormatSymbols, 
                            GregorianCalendarInstance, ColorInfo)
from TimedCanvas import TimedEventsCanvas
from CalendarCanvas import CalendarCanvasBlock
from AllDayCanvas import SparseMatrix

from osaf.pim.calendar import formatTime, shortTZ
from osaf.framework.blocks.DrawingUtilities import DrawClippedText
from osaf.framework.blocks.Block import BaseWidget

import math, bisect

logger = logging.getLogger(__name__)

__all__ = ['MultiWeekContainer', 'wxMultiWeekContainer', 'wxMultiWeekControl',
           'MultiWeekControl', 'MultiWeekCanvas']

HEADER_HEIGHT = 16
HEADER_PADDING = 2
WEEK_LABEL_WIDTH = 16
TIME_PADDING = 4

(EMPTY_REGION, WEEK_REGION, DAY_REGION, CELL_EMPTY, CELL_NUMBER,
 CELL_EVENT) = range(6)

ONE_WEEK = timedelta(7)
ONE_DAY  = timedelta(1)

class MultiWeekContainer(CalendarContainer):
    def getWidget(self):
        return wxMultiWeekContainer(
            self.parentBlock.widget,
            self.getWidgetID(),
            wx.DefaultPosition,
            wx.DefaultSize,
            style=wxCalendarContainer.CalculateWXStyle(self)
        )
    
    def onNewItemEvent(self, event):
        # don't use calendar logic to create a new item
        event.arguments['continueBubbleUp'] = True
    
class wxMultiWeekContainer(wxCalendarContainer):        
    def calendarBlockWidgets(self):
        """Iterator over all widgets that render items."""
        # the first block is the calendar control, skip it
        block = itertools.islice(self.blockItem.childBlocks, 1, 2).next()
        widget = getattr(block, 'widget', None)        
        if widget is not None:
            yield widget


class MultiWeekCanvas(TimedEventsCanvas):
    def instantiateWidget(self):
        # skipping over TimedEventsCanvas's instantiateWidget
        CalendarCanvasBlock.instantiateWidget(self)
        return wxMultiWeekCanvas(self.parentBlock.widget)

    def onWeekStartChangedEvent(self, event):
        self.setRange(self.selectedDate)
        self.synchronizeWidget()
        self.widget.Refresh()


class MultiWeekControl(CalendarControl):
    def getWidget(self):
        return wxMultiWeekControl(self.parentBlock.widget, -1, 
                                  tzCharacterStyle=self.tzCharacterStyle)
    

class wxMultiWeekControl(wxCalendarControl):
    """
    This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons.
    """

    def OnSize(self, event):
        """
        Needs to be sub-classed to skip the sizeChanged hack which
        explicitly refreshes specific widgets.
        """

        sizeChanged = getattr(self, 'size', None) != self.GetSize()
        self._doDrawingCalculations()
        event.Skip()

    def setupHeader(self):
        # test this on GTK, do we really need this?
        if IS_GTK:
            self.xOffset = WEEK_LABEL_WIDTH + 6
        else:
            self.xOffset = WEEK_LABEL_WIDTH

    def wxSynchronizeWidget(self):
        selectedDate = self.blockItem.selectedDate
        startDate = self.blockItem.rangeStart

        # We're just synchronizing the control area,
        # so we only care if the visible range has changed
        if (selectedDate == self.currentSelectedDate and
            startDate == self.currentStartDate):
            return

        # update the calendar with the calender's color
        collection = self.blockItem.contentsCollection
        if collection is None:
            # not having anything to show is bad.  This can happen if
            # setContents is propagating but hasn't gotten to us yet.  Abort
            return

        # Update the month button given the selected date
        middleDate = startDate + ONE_WEEK
        months = dateFormatSymbols.getMonths()
        data = dict(currentMonth = months[middleDate.month - 1],
                    currentYear  = middleDate.year)

        self.monthText.SetLabel(_(u'%(currentMonth)s %(currentYear)d') % data)

        startOfDay = time(tzinfo=self.blockItem.itsView.tzinfo.floating)
        self.currentSelectedDate = datetime.combine(selectedDate, startOfDay)
        self.currentStartDate = datetime.combine(startDate, startOfDay)

        self.Layout()
            
        self.Refresh()

    def UpdateHeader(self):
        pass

    def ResizeHeader(self):
        pass

# UI Model for a week - may be extended later
class MultiWeekWeek(object):
    def __init__(self):
        self.days = [MultiWeekDay(), MultiWeekDay(), MultiWeekDay(),
                        MultiWeekDay(), MultiWeekDay(), MultiWeekDay(), MultiWeekDay()]
        self.isVisible = True
        self.bounds = None

class MultiWeekDay(object):
    def __init__(self):
        self.events = []
        self.isVisible = True
        self.bounds = None
        self.eventsAndBounds = None

class wxMultiWeekCanvas(BaseWidget, wxCalendarCanvas):
    """
    Ancestry:
        wxCollectionCanvas --> wxCalendarCanvas --> wxMultiWeekCanvas

    Description:
        wxMultiWeekCanvas handles the rendering of the multiweek view. It overrides the
        method OnPaint(), which is bound to wx.EVT_PAINT in wxCollectionCanvas. Instead
        of a Device Context (DC), the multiweek view uses a Graphics Context (GC),  which
        has a more advanced API.
    """
    @apply
    def visibleWeeks():
        "The number of weeks visible in the multi-week view"
        def fget(self):
            return self._visibleWeekCount
        def fset(self, value):
            # you can't set the number of visibile weeks, but if there is no
            # fset method, the attribute just gets overwritten
            pass
        return property(**locals())

    @apply
    def totalWeeks():
        "The total number of weeks represented in the multi-week view"
        def fget(self):
            return len(self._weeks)
        def fset(self, value):
            delta = value - len(self._weeks)
            self._visibleWeekCount += delta
            assert(self._visibleWeekCount == value)
            if delta > 0:
                # if the new value is larger, extend the list with more MultiWeekWeek objects
                for i in xrange(len(self._weeks), value):
                    # is there a better way to do this in Python?
                    self._weeks.append(MultiWeekWeek())
            elif delta < 0:
                # if the new value is smaller, truncate the list
                del self._weeks[value : len(self._weeks)]
        return property(**locals())

    @apply
    def visibleDaysPerWeek():
        "The number of days displayed for each week"
        # Just wrap the value for now.
        def fget(self):
            return self._visibleDaysPerWeek
        def fset(self, value):
            self._visibleDaysPerWeek = value
        return property(**locals())

    @apply
    def firstVisibleDay():
        "The first day on each row"
        def fget(self):
            return self._firstVisibleDay
        def fset(self, value):
            self._firstVisibleDay = value
        return property(**locals())

    def __init__(self, *arguments, **keywords):
        super (wxMultiWeekCanvas, self).__init__ (*arguments, **keywords)
        # default to showing 7 days -- HELPME is there a better idiom for this?
        self._weeks = [MultiWeekWeek(), MultiWeekWeek(), MultiWeekWeek(), MultiWeekWeek(), MultiWeekWeek(), MultiWeekWeek()]
        # how many days are visible for each week
        self._visibleDaysPerWeek = 7
        # what day is at the left side of a week (0=Sun, 1=Mon, ... 6=Sat)
        self._firstVisibleDay = 0
        # how many weeks to display - will always be < self.visibleWeeks
        self._visibleWeekCount = 6
        self._dayMargin = (3, 2)
        # turn off editor
        self.editor = None
        # track multi-day events
        self._multiDayEvents = []
        # keep track of available "slots" for drawing events
        self._eventSlots = SparseMatrix()
        # should we use the multiWeekControl's column positions, or
        # calculate our own?
        self._shouldCalculateColumnPositions = False

        # rendering
        self.styles = Block.Block.findBlockByName("MultiWeekCalendarView")
        self._dayPen = self.styles.minorLinePen
        self._weekPen = self._dayPen
        self._noonStrokePen = wx.Pen(wx.Colour(100, 100, 100, 255), 1)
        self._noonStrokePen.SetCap(wx.CAP_BUTT)
        self._weekBrush = wx.Brush(wx.Colour(255, 255, 255, 128)) # 128 == half transparent
        self._eraseBrush = wx.Brush(wx.Colour(255, 255, 255))
        self._erasePen = wx.Pen("white", 1)
        self._zeroPen = wx.Pen("white", 0)
        self._thisMonthColour = wx.Colour(0, 0, 0, 255)
        self._otherMonthColour = wx.Colour(128, 128, 128, 128)
        self._otherMonthBrush = wx.Brush(wx.Colour(0, 0, 0, 128))
        self._otherMonthAllDayBrush = wx.Brush(wx.Colour(225, 225, 225, 128))
        self._textBrush = wx.Brush(wx.Colour(255, 255, 255, 128)) # 128 == half transparent
        self._textPen = self._dayPen
        

        self._font = self.styles.eventLabelFont
        self._timeFont = self.styles.eventTimeFont
        self._textFont = self.styles.eventLabelFont # eventTimeFont
        # set up superscript
        size = self.styles.eventTimeStyle.fontSize * .7
        if IS_MAC:
            # on the Mac anti-aliasing stops at 8px by default (user can change to be lower)
            size = max(size, 9)
        self._superscriptFont = Styles.getFont(size=size)


        self._todayBrush = self.styles.todayBrush
        
        self.multiWeekControl = Block.Block.findBlockByName("MainMultiWeekControl")
        # the widget's block isn't fully baked yet, initialize to None
        self._rangeStart = self._rangeEnd = self._month = None

        # initialize bitmaps
        self.weekdayBitmaps = None
        self.weekNumberBitmaps = {}
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        
        self.measure = wx.ClientDC(self)
        self.measure.SetFont(self._font)
        self.doDrawingCalculations()
        
    def SetWindowGeometry(self):
        self.Refresh()

    def DrawCanvas(self, dc):
        dc.BeginDrawing()
        gc = wx.GraphicsContext.Create(dc)
        self.DrawBackground(gc)
        self.DrawWeeks(gc)
        dc.EndDrawing()

    def PrintCanvas(self, dc):
        # [grant] This is a bit of a cheesy hack ... Basically, in cases where
        # we are scaling to print, we want to be able to adjust our internal
        # metrics, fonts, etc as needed, and then reset them all when we're
        # done (i.e. when we're going back to displaying on-screen). So, we
        # temporary replace __setattr__ on our class so as to detect all
        # attribute changes, and then restore them (and __setattr__!) in a
        # finally block.
        originalValues = {}
        originalSetattr = type(self).__setattr__
        
        def saveAndSet(obj, key, value):
            # Store to originalValues only if this is the first setting
            # of this attribute!
            if obj is self and not key in originalValues and hasattr(self, key):
                originalValues[key] = getattr(self, key)
            # Make sure to set the value, eh :)
            originalSetattr(obj, key, value)
            
        type(self).__setattr__ = saveAndSet

        try:
            if dc.GetUserScale()[1] != 1.0:
                # Redo our calculations based on the real font sizes.
                self.measure = wx.ClientDC(self)
                self.measure.SetFont(self._font)
                self.doDrawingCalculations()
        

            dc.BeginDrawing()
            w, h = dc.GetSize()
            # We need to create a 24-bit bitmap to work around a win32 bitmap bug
            bitmap = wx.EmptyBitmap(w, h, -1)
            mdc = wx.MemoryDC(bitmap)
            mdc.SetBackground(wx.WHITE_BRUSH)
            mdc.Clear()
            gc = wx.GraphicsContext.Create(mdc)
    
            self._shouldCalculateColumnPositions = True
            self.DrawBackground(gc)
            self.DrawWeeks(gc)
            self._shouldCalculateColumnPositions = False
    
            dc.DrawBitmap(bitmap, 0, 0)
            dc.EndDrawing()
        finally:
            type(self).__setattr__ = originalSetattr
            for attr, value in originalValues.iteritems():
                setattr(self, attr, value)

    def doDrawingCalculations(self):
        self.dateWidth, self.stringHeight = self.measure.GetTextExtent("31")

    def makeBitmap(self, text, rotate=False, padding=HEADER_PADDING):
        width, height = self.measure.GetTextExtent(text)
        if rotate:
            height, width = width, height
        # We need to create a 24-bit bitmap to work around a win32 bitmap bug
        bitmap = wx.EmptyBitmap(width + 2*padding, height + 2*padding, 24)
        mdc = wx.MemoryDC(bitmap)
        mdc.SetFont(self._font)
        mdc.SetBackground(wx.WHITE_BRUSH)
        mdc.Clear()
        if not rotate:
            mdc.DrawText(text, padding, padding)
        else:
            mdc.DrawRotatedText(text, padding, padding + height, 90)
        del mdc
        return bitmap

    def DrawBackground(self, gc):
        if self.weekdayBitmaps is None:
            names = dateFormatSymbols.getWeekdays()
            # ICU makes this list 1-based, skip the first empty element
            self.weekdayBitmaps = [self.makeBitmap(n) for n in names[1:]]

        control = self.multiWeekControl.widget
        positions = self.GetColumnPositions()
        widths = control.columnWidths
        
        firstDay = GregorianCalendarInstance.getFirstDayOfWeek()
        for day in xrange(7):
            column = day + 1
            dayBitmap = self.weekdayBitmaps[(day + firstDay - 1) % 7]
            width, height = dayBitmap.GetSize()
            dy = max(HEADER_HEIGHT - height, 0)
            columnPosition, columnWidth = positions[column], widths[column]
            if columnWidth <= width:
                dx = columnPosition
                width = columnWidth
            else:
                dx = columnPosition + (columnWidth - width) / 2
            gc.DrawBitmap(dayBitmap, dx, dy, width, height)

    def DrawWeeks(self, gc):
        columnPositions = self.GetColumnPositions()
        weekIndex = 0
        startDate = self._rangeStart
        for visibleWeekIndex in xrange(0, self.visibleWeeks):
            while not self.WeekIsVisible(weekIndex):
                self.DrawCollapsedWeek(gc, weekIndex, columnPositions)
                weekIndex += 1
            self.DrawWeek(gc, weekIndex, columnPositions, startDate)
            startDate += ONE_WEEK
            weekIndex += 1

    def WeekIsVisible(self, weekIndex):
        return self._weeks[weekIndex].isVisible

    def DrawCollapsedWeek(self, gc, index, columnPositions):
        pass

    def DrawWeek(self, gc, weekIndex, columnPositions, startDate):
        week = self._weeks[weekIndex]
        gc.SetFont(self._font)
        week._bounds = self._BoundsForLogicalWeek(weekIndex, columnPositions)
        dateToRender = startDate
        assert self.visibleDaysPerWeek < len(columnPositions)
        for dayIndex in xrange(0, self.visibleDaysPerWeek):
            left = columnPositions[dayIndex+1]
            right = columnPositions[dayIndex+2]
            day = week.days[dayIndex]
            day._bounds = wx.Rect(left, week._bounds.top, right-left, week._bounds.height)
            self.DrawDay(gc, dateToRender, day)
            dateToRender += ONE_DAY

        # draw week number label for the last day of the week
        weekNumber = (startDate + timedelta(6)).isocalendar()[1]
        bitmap = self.weekNumberBitmaps.get(weekNumber)
        if not bitmap:
            text = _("Week %(weekNumber)s") % dict(weekNumber=weekNumber)
            bitmap = self.makeBitmap(text, rotate=True)
            self.weekNumberBitmaps[weekNumber] = bitmap
            
        width, height = bitmap.GetSize()
        dx = columnPositions[1] - width
        dy = week._bounds.top + (week._bounds.height - height) / 2
        gc.DrawBitmap(bitmap, dx, dy, width, height)


    def DrawDay(self, gc, dateToRender, day):
        defaultTz = self.blockItem.itsView.tzinfo.default

        dayString = "%d" % dateToRender.day # TODO i10n?
        
        # create a new rect to deflate in place
        dayBounds = wx.Rect(*day._bounds)
        dayBounds.Deflate(*self._dayMargin)

        if dateToRender.date() == datetime.now(defaultTz).date():
            self.DrawTodayBackground(gc, day._bounds)

        gc.SetPen(self._weekPen)
        gc.SetBrush(self._weekBrush)
        gc.DrawRectangle(*day._bounds)
        
        fontColor = (self._thisMonthColour if dateToRender.month == self._month
                                           else self._otherMonthColour)
        gc.SetFont(self._font, fontColor)
        stringWidth = gc.GetTextExtent(dayString)[0]

        # draw date in top-right corner
        gc.DrawText(dayString, dayBounds.right - stringWidth, dayBounds.top)
        self.DrawDayEvents(gc, dayBounds, dateToRender, fontColor, day)

    def DrawDayEvents(self, gc, dayBounds, dateToRender, fontColor, day):
        # draw events
        eventTop = dayBounds.top + self.stringHeight
        block = self.blockItem
        view = block.itsView
        primaryCollection = block.contentsCollection
        
        maxTimeStr = "23"
        gc.SetFont(self._timeFont)
        maxHourWidth = gc.GetTextExtent(maxTimeStr)[0]
        gc.SetFont(self._superscriptFont)
        maxMinuteWidth = gc.GetTextExtent(maxTimeStr)[0]
        
        noonStrokeWidth = maxMinuteWidth + maxHourWidth
        noonStrokeDrawn = False
        drawNoonStroke  = False
        oneDay = timedelta(1)

        gc.Clip(*dayBounds)
        
        for event in self.dayToEvents[dateToRender.date()]:
            eventTitle = event.itsItem.displayName
            if event.allDay:
                eventTitle = event.itsItem.displayName
                extraWidth = 1
                gc.SetPen(self._zeroPen)
                collection = block.getContainingCollection(event.itsItem, primaryCollection)
                colorInfo = ColorInfo(collection)

                #                    GradientLeft       GradientRight       Outline             Text
                #                    ============       =============       =======             ====
                ## defaultColors     [(204, 0, 0),	    (255, 50, 50),	    (255, 50, 50),	    (255, 255, 255)]
                ## defaultFYIColors  [(255, 226, 226),	(255, 242, 242),	(255, 50, 50),	    (204, 0, 0)]
                ## selectedColors    [(127, 0, 0),	    (204, 0, 0),	    (204, 0, 0),	    (255, 255, 255)]
                ## selectedFYIColors [(255, 170, 170),	(255, 216, 216),	(255, 50, 50),	    (204, 0, 0)]
                ## visibleColors     [(255, 170, 170),	(255, 170, 170),	(255, 170, 170),	(204, 0, 0)]
                ## visibleFYIColors  [(255, 242, 242),	(255, 242, 242),	(255, 216, 216),	(204, 0, 0)]

                if dateToRender.month != self._month:
                    gc.SetFont(self._font, self._otherMonthColour)
                    bgColour = wx.Colour(*colorInfo.defaultFYIColors[0])
                else:
                    gc.SetFont(self._textFont, colorInfo.selectedColors[3])
                    bgColour = wx.Colour(*colorInfo.defaultColors[1])

                #gc.SetBrush(wx.Brush(wx.Colour(colorInfo.defaultColors[1])))
                # workaround - the line above always gives black
                bgColour.alpha = 128
                gc.SetBrush(wx.Brush(bgColour))

                gc.DrawRoundedRectangle(dayBounds.left, eventTop, dayBounds.width, self.stringHeight, self.stringHeight/2)
                DrawClippedText(gc, eventTitle,
                                dayBounds.left + extraWidth + self.stringHeight/2, eventTop,
                                dayBounds.width - extraWidth - 1 - self.stringHeight/2)
                eventTop += self.stringHeight
                #if (event.startTime + event.duration).date() <= dateToRender.date():
                #    self._multiDayEvents.remove(event)
                continue

            elif event.anyTime:
                extraWidth = 1

            else:
                drawNoonStroke = True
                gc.SetFont(self._timeFont, fontColor)
                timeStr = formatTime(view, event.startTime, justHour=True)
                timeWidth = gc.GetTextExtent(timeStr)[0]
                gc.DrawText(timeStr, dayBounds.left, eventTop)
                if event.startTime.minute != 0:
                    minuteStr = "%02d" % event.startTime.minute
                    gc.SetFont(self._superscriptFont, fontColor)
                    gc.DrawText(minuteStr, dayBounds.left + timeWidth, eventTop)
                    timeWidth += gc.GetTextExtent(minuteStr)[0]
                else:
                    timeWidth += 2
                extraWidth = timeWidth + TIME_PADDING
            
            if dateToRender.month != self._month:
                gc.SetFont(self._font, self._otherMonthColour)
            else:
                collection = block.getContainingCollection(event.itsItem,
                                                           primaryCollection)
                colorInfo = ColorInfo(collection)
                gc.SetFont(self._textFont, colorInfo.selectedColors[0])
            
            # gc.DrawClippedRect is occasionally off by a pixel, so give
            # extra margin.
            DrawClippedText(gc, eventTitle,
                            dayBounds.left + extraWidth, eventTop,
                            dayBounds.width - extraWidth - 1)
            
            if (drawNoonStroke and not noonStrokeDrawn and
                event.startTime.hour >= 12):
                gc.SetPen(self._noonStrokePen)
                gc.StrokeLine(dayBounds.left, int(eventTop),
                              dayBounds.left + noonStrokeWidth, int(eventTop))
                noonStrokeDrawn = True

            eventTop += self.stringHeight

        if drawNoonStroke and not noonStrokeDrawn:
            gc.SetPen(self._noonStrokePen)
            gc.StrokeLine(dayBounds.left, int(eventTop),
                          dayBounds.left + noonStrokeWidth, int(eventTop))
        gc.ResetClip()

    def DrawTodayBackground(self, gc, bounds):
        gc.SetBrush(self._todayBrush)
        gc.SetPen(self._zeroPen)
        gc.DrawRectangle(*bounds)

    def _BoundsForLogicalWeek(self, index, columnPositions):
        # chop the client rect into 6 vertical slices
        r = self.GetClientRect()
        h = r.GetHeight() - HEADER_HEIGHT
        increment = h / float(self.visibleWeeks)
        r.top = increment * index + HEADER_HEIGHT
        r.bottom = r.top + increment
        r.left = columnPositions[1]
        logger.debug("bounds for week %d: [%d, %d, %d, %d]" % ((index,) + r.Get()))
        return r

    def wxSynchronizeWidget(self):
        self._rangeStart = self.blockItem.rangeStart
        self._rangeEnd = self.blockItem.rangeEnd
        self._month = (self._rangeStart + ONE_WEEK).month
        self.totalWeeks = (self._rangeEnd - self._rangeStart).days / 7
        
        self.visibleEvents = self.blockItem.calendarContainer.widget.visibleEvents

        self.eventToDays = {}
        self.dayToEvents = {}        

        for event in self.visibleEvents:
            # for now, don't worry about multi-day events and recurring events
            date = event.effectiveStartTime.date()
            self.eventToDays[event] = [date]
            self.dayToEvents.setdefault(date, []).append(event)
            endTime = event.startTime + event.duration
            if event.allDay and endTime.date() > date:
                eventDate = event.effectiveStartTime + ONE_DAY
                while eventDate.date() <= endTime.date():
                    self.dayToEvents.setdefault(eventDate.date(), []).append(event)
                    eventDate += ONE_DAY

        day = self._rangeStart.date()
        while day <= self._rangeEnd.date():
            # set an empty list as default, sort based on start time
            self.dayToEvents.setdefault(day, []).sort(key=EventStamp.getEffectiveStartTime)
            day += ONE_DAY
        
        self.Refresh()


    def wxHandleChanges(self, changes):
        # changes is an iterable of (op, event), redraw appropriately
        # - just skip this and make it always call wxSynchronizeWidget
        self.wxSynchronizeWidget()
        #for op, event in changes:
            #change, op = self.handleOneChange(op, event)

    def GetColumnPositions(self):
        if self._shouldCalculateColumnPositions:
            daysPerWeek = self.visibleDaysPerWeek # usually 7
            bounds = self.GetClientRect()

            # the starting point for day widths - an integer, rounded down
            baseDayWidth = bounds.width / daysPerWeek

            # due to rounding there may be up to 6 extra pixels to distribute
            leftover = bounds.width - baseDayWidth*daysPerWeek

            # evenly distribute the leftover into a tuple of the right length
            # for instance, leftover==4 gives us (0,0,0,1,1,1,1)
            leftoverWidths = (0,) * (daysPerWeek-leftover) + (1,) * leftover

            # now add the extra bits to the individual columns
            columnWidths = (baseDayWidth,) * daysPerWeek # like  (80,80,80,80,80,80,80)
            # with 5 leftover, this makes them like (80,80,81,81,81,81,81)
            columnWidths = tuple(map(add, columnWidths, leftoverWidths))

            ## e.g. 10,40,40,40 => 0,10,50,90
            columnPositions = (bounds.left,) + tuple(sum(columnWidths[:i])
                                         for i in range(len(columnWidths))) + (bounds.right,)
        else:
            columnPositions = self.multiWeekControl.widget.columnPositions
            logger.debug(("call column positions: ", columnPositions))
        return columnPositions

    def GetClickData(self, point):
        """Return a region constant and the data associated with it."""
        x, y = point
        if y <= HEADER_HEIGHT:
            # eventually do something with clicks on days
            return EMPTY_REGION, None

        positions = self.GetColumnPositions()
        r = self.GetClientRect()
        h = r.GetHeight() - HEADER_HEIGHT
        increment = h / float(self.visibleWeeks)
        row = int((y - HEADER_HEIGHT) / increment)

        column = bisect.bisect(positions, x) - 1

        if column == 0:
            return WEEK_REGION, self._rangeStart + ONE_WEEK * row
        else:
            day_column = column - 1
            date = self._rangeStart + ONE_WEEK*row + ONE_DAY*day_column
            x -= positions[column]
            y -= HEADER_HEIGHT + increment*row
            width = positions[column + 1] - positions[column]
            if y <= self.stringHeight:
                if x <= width - self.dateWidth:
                    return CELL_EMPTY, date
                else:
                    return CELL_NUMBER, date
            else:
                events = self.dayToEvents[date.date()]
                eventIndex = int(y / self.stringHeight) - 1
                if eventIndex > len(events) - 1:
                    return CELL_EMPTY, date
                else:
                    return CELL_EVENT, events[eventIndex]
            
        return EMPTY_REGION, None

    def OnClick(self, event):
        block = self.blockItem
        position = event.GetPosition()
        constant, data = self.GetClickData(position)
        if constant == WEEK_REGION:
            block.postDateChanged(data)
            # this causes the widget to be deleted, for some reason this
            # causes a wx C++ exception, so using CallAfter to delay the call
            wx.CallAfter(block.postEventByName, 'ViewAsWeekCalendar', {})
        elif constant == CELL_NUMBER:
            block.postDateChanged(data)
            wx.CallAfter(block.postEventByName, 'ViewAsDayCalendar', {})
        elif constant == CELL_EVENT:
            self.OnSelectItem(data.itsItem)
        elif constant in (EMPTY_REGION, CELL_EMPTY):
            self.OnSelectItem(None)

    def OnDClick(self, event):
        block = self.blockItem
        position = event.GetPosition()
        constant, data = self.GetClickData(position)
        if constant == CELL_EMPTY:
            view = block.itsView
            event = self.CreateEmptyEvent(startTime=data, allDay=False,
                                          anyTime=True)
            self.OnSelectItem(event.itsItem)
            view.commit()
        elif constant == CELL_EVENT:
            self.blockItem.postEventByName('EditItems',
                                           {'items': [data.itsItem]})

    def OnMouseEvent(self, event):
        event.Skip()

    def OnSize(self, event):
        self.Refresh()
        event.Skip()

    def RebuildCanvasItems(self, resort=False):
        # called by CalendarCanvas, line 1631, in RefreshCanvasItems()
        pass

# (look at TimedCanvas.wxTimedEventsCanvas)
# inherits a bunch of stuff we don't care about...

#Jeffrey: OnInit - I don't understand why this is different from __init__
#Reid: OnInit is what wx calls on the app object, and it's supposed to create
#   windows and UI objects. I guess the method name trickled down, although it
#   doesn't really need to

#wxSynchronizeWidget - normal, calculate events, call Refresh
