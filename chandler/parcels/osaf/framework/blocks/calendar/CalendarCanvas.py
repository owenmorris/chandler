""" Canvas for calendaring blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import mx.DateTime as DateTime

import osaf.contentmodel.calendar.Calendar as Calendar

import osaf.framework.blocks.DragAndDrop as DragAndDrop
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.calendar.CollectionCanvas as CollectionCanvas

import application.Globals as Globals

class ColumnarCanvasItem(CollectionCanvas.CanvasItem):
    def __init__(self, *arguments, **keywords):
        super(ColumnarCanvasItem, self).__init__(*arguments, **keywords)
        
        self._resizeLowBounds = wx.Rect(self.bounds.x,
                                        self.bounds.y + self.bounds.height - 5,
                                        self.bounds.width, 5)
        
        self._resizeTopBounds = wx.Rect(self.bounds.x, self.bounds.y,
                                        self.bounds.width, 5)

    def isHitResize(self, point):
        """ Hit testing of a resize region.
        
        @param point: point in unscrolled coordinates
        @type point: wx.Point
        @return: True if the point hit the resize region
        @rtype: Boolean
        """
        return (self._resizeTopBounds.Inside(point) or
                self._resizeLowBounds.Inside(point))

    def getResizeMode(self, point):
        """ Returns the mode of the resize, either 'TOP' or 'LOW'.

        The resize mode is 'TOP' if dragging from the top of the event,
        and 'LOW' if dragging from the bottom of the event. None indicates
        that we are not resizing at all.

        @param point: drag start position in uscrolled coordinates
        @type point: wx.Point
        @return: resize mode, 'TOP', 'LOW' or None
        @rtype: string or None
        """
        
        if self._resizeTopBounds.Inside(point):
            return "TOP"
        if self._resizeLowBounds.Inside(point):
            return "LOW"
        return None


class CalendarEventHandler(object):

    """ Mixin to a widget class """

    def OnPrev(self, event):
        self.blockItem.decrementRange()
        self.blockItem.postDateChanged()
        self.wxSynchronizeWidget()

    def OnNext(self, event):
        self.blockItem.incrementRange()
        self.blockItem.postDateChanged()
        self.wxSynchronizeWidget()

    def OnToday(self, event):
        today = DateTime.today()
        self.blockItem.setRange(today)
        self.blockItem.postDateChanged()
        self.wxSynchronizeWidget()

class CalendarBlock(CollectionCanvas.CollectionBlock):
    """ Abstract block used as base Kind for Calendar related blocks.

    This base class can be used for any block that displays a collection of
    items based on a date range.

    @ivar rangeStart: beginning of the currently displayed range (persistent)
    @type rangeStart: mx.DateTime.DateTime
    @ivar rangeIncrement: increment used to find the next or prev block of time
    @type rangeIncrement: mx.DateTime.RelativeDateTime
    """
    
    def __init__(self, *arguments, **keywords):
        super(CalendarBlock, self).__init__(*arguments, **keywords)

    # Event handling
    
    def onSelectedDateChangedEvent(self, notification):
        """
        Sets the selected date range and synchronizes the widget.

        @param notification: notification sent on selected date changed event
        @type notification: osaf.framework.notifications.Notification
        @param notification['start']: start of the newly selected date range
        @type notification['start']: mx.DateTime.DateTime
        """
        self.setRange(notification.data['start'])
        self.widget.wxSynchronizeWidget()

    def postDateChanged(self):
        """
        Convenience method for changing the selected date.
        """
        event = Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectedDateChanged')
        self.Post(event, {'start':self.rangeStart})

    # Managing the date range

    def setRange(self, date):
        """ Sets the range to include the given date.

        @param date: date to include
        @type date: mx.DateTime.DateTime
        """
        self.rangeStart = date

    def isDateInRange(self, date):
        """ Does the given date currently appear on the calendar block?

        @type date: mx.DateTime.DateTime
        @return: True if the given date appears on the calendar
        @rtype: Boolean
        """
        begin = self.rangeStart
        end = begin + self.rangeIncrement
        return ((date >= begin) and (date < end))

    def incrementRange(self):
        """ Increments the calendar's current range """
        self.rangeStart += self.rangeIncrement

    def decrementRange(self):
        """ Decrements the calendar's current range """
        self.rangeStart -= self.rangeIncrement

    # Get items from the collection

    def getItemsByDate(self, date):
        """
        Convenience method to look for the items in the block's contents
        that appear on the given date. @@@ We may push this work down into
        ItemCollections and/or Queries.

        @type date: mx.DateTime.DateTime
        @return: the items in this collection that appear on the given date
        @rtype: list of Items
        """
        # make this a generator?
        items = []
        nextDate = date + DateTime.RelativeDateTime(days=1)
        for item in self.contents:
            if ((item.startTime >= date) and (item.startTime < nextDate)):
                items.append(item)
        return items

class wxWeekPanel(wx.Panel, CalendarEventHandler):
    def __init__(self, *arguments, **keywords):
        super (wxWeekPanel, self).__init__ (*arguments, **keywords)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        self.headerCanvas = wxWeekHeaderCanvas(self, -1)
        self.columnCanvas = wxWeekColumnCanvas(self, -1)
        self.headerCanvas.parent = self
        self.columnCanvas.parent = self

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.headerCanvas, 0, wx.EXPAND)
        box.Add(self.columnCanvas, 1, wx.EXPAND)
        self.SetSizer(box)

    def OnEraseBackground(self, event):
        pass

    def OnInit(self):
        self.headerCanvas.OnInit()
        self.columnCanvas.OnInit()

    def wxSynchronizeWidget(self):
        self.headerCanvas.wxSynchronizeWidget()
        self.columnCanvas.wxSynchronizeWidget()

class wxWeekHeaderCanvas(CollectionCanvas.wxCollectionCanvas):
    def __init__(self, *arguments, **keywords):
        super (wxWeekHeaderCanvas, self).__init__ (*arguments, **keywords)

        self.SetSize((-1, 50))

    def OnInit(self):
        # Setup the navigation buttons
        today = DateTime.today()
        
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "application/images/backarrow.png")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "application/images/forwardarrow.png")
        self.todayButton = CollectionCanvas.CanvasTextButton(self, today.Format("%b %d, %Y"),
                                                             self.bigFont, self.bigFontColor,
                                                             self.bgColor)
        self.monthButton = CollectionCanvas.CanvasTextButton(self, " September 8888 ",
                                                             self.bigFont, self.bigFontColor,
                                                             self.bgColor)


        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add((0,0), 1, wx.EXPAND, 5)
        box.Add((0,0), 1, wx.EXPAND, 5)
        box.Add(self.prevButton, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        box.Add(self.monthButton, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        box.Add(self.nextButton, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        box.Add((0,0), 1, wx.EXPAND, 5)
        box.Add(self.todayButton, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(box)

        self.Bind(wx.EVT_BUTTON, self.parent.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.parent.OnNext, self.nextButton)
        self.Bind(wx.EVT_BUTTON, self.parent.OnToday, self.todayButton)

    def wxSynchronizeWidget(self):
        self.monthButton.SetLabel(self.parent.blockItem.rangeStart.Format("%B %Y"))
        self.Refresh()

    # Drawing code

    def _doDrawingCalculations(self, dc):
        # @@@ magic numbers
        self.size = self.GetVirtualSize()
        self.adjustedSize = self.parent.columnCanvas.GetVirtualSize()
        
        self.xOffset = self.adjustedSize.width / 8
        self.hourHeight = 40
        self.dayWidth = (self.adjustedSize.width - self.xOffset) / self.parent.blockItem.daysPerView
        self.dayHeight = self.hourHeight * 24

    def DrawBackground(self, dc):
        self._doDrawingCalculations(dc)

        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle((0, 0), (self.size.width, self.size.height))
        
        startDay = self.parent.blockItem.rangeStart

        # Draw the weekdays
        # @@@ Figure out the height of the text
        for day in range(self.parent.blockItem.daysPerView):
            currentDate = startDay + DateTime.RelativeDateTime(days=day)

            dc.SetTextForeground(self.bigFontColor)
            dc.SetFont(self.bigFont)
            dayName = currentDate.Format('%a %d')
            dayRect = wx.Rect(self.xOffset + (self.dayWidth * day),
                              self.size.height - 20,
                              self.dayWidth, 20)
            self.DrawCenteredText(dc, dayName, dayRect)

        # Draw a line across the bottom of the header
        dc.SetPen(wx.Pen(wx.Colour(179, 179, 179)))
        dc.DrawLine((0, self.size.height - 1),
                    (self.size.width, self.size.height - 1))
        dc.SetPen(wx.Pen(wx.Colour(204, 204, 204)))
        dc.DrawLine((0, self.size.height - 2),
                    (self.size.width, self.size.height - 2))
        dc.SetPen(wx.Pen(wx.Colour(179, 179, 179)))
        dc.DrawLine((0, self.size.height - 3),
                    (self.size.width, self.size.height - 3))

    def DrawCells(self, dc):
        pass

    def OnSelectItem(self, item):
        pass

class wxWeekColumnCanvas(CollectionCanvas.wxCollectionCanvas):
    def __init__(self, *arguments, **keywords):
        super (wxWeekColumnCanvas, self).__init__ (*arguments, **keywords)

        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)

    def OnScroll(self, event):
        self.Refresh()
        event.Skip()

    def wxSynchronizeWidget(self):
        self.Refresh()

    def OnInit(self):
        # @@@ rationalize drawing calculations...
        self.SetVirtualSize((self.GetVirtualSize().width, 40*24))
        self.SetScrollRate(0, 10)
        self.Scroll(0, (40*7)/10)

    def _doDrawingCalculations(self, dc):
        # @@@ magic numbers
        self.size = self.GetVirtualSize()
        self.xOffset = self.size.width / 8
        self.hourHeight = 40
        self.dayWidth = (self.size.width - self.xOffset) / self.parent.blockItem.daysPerView
        self.dayHeight = self.hourHeight * 24

    def DrawBackground(self, dc):
        self._doDrawingCalculations(dc)

        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle((0, 0), (self.size.width, self.size.height))

        # Set text properties for legend
        dc.SetTextForeground(self.bigFontColor)
        dc.SetFont(self.bigFont)

        # Use topTime to draw am/pm on the topmost hour
        topCoordinate = self.CalcUnscrolledPosition((0,0))
        topTime = self.getDateTimeFromPosition(wx.Point(topCoordinate[0],
                                                        topCoordinate[1]))

        # Draw the lines separating hours
        for hour in range(24):
            
            # Draw the hour legend
            if (hour > 0):
                if (hour == 1):
                    hourString = "am 1"
                elif (hour == 12): 
                    hourString = "pm 12"
                elif (hour > 12):
                    if (hour == (topTime.hour + 1)): # topmost hour
                        hourString = "pm %s" % str(hour - 12)
                    else:
                        hourString = str(hour - 12)
                else:
                    if (hour == (topTime.hour + 1)): # topmost hour
                        hourString = "am %s" % str(hour)
                    else:
                        hourString = str(hour)
                wText, hText = dc.GetTextExtent(hourString)
                dc.DrawText(hourString,
                            (self.xOffset - wText - 5,
                             hour * self.hourHeight - (hText/2)))
            
            # Draw the line between hours
            dc.SetPen(wx.Pen(wx.Colour(204, 204, 204)))
            dc.DrawLine((self.xOffset,
                         hour * self.hourHeight),
                        (self.size.width,
                         hour * self.hourHeight))

            # Draw the line between half hours
            dc.SetPen(wx.Pen(wx.Colour(230, 230, 230)))
            dc.DrawLine((self.xOffset,
                         hour * self.hourHeight + (self.hourHeight/2)),
                        (self.size.width,
                         hour * self.hourHeight + (self.hourHeight/2)))

        # Draw lines between days
        for day in range(self.parent.blockItem.daysPerView):
            dc.DrawLine((self.xOffset + (self.dayWidth * day), 0),
                        (self.xOffset + (self.dayWidth * day), self.size.height))

    def DrawCells(self, dc):
        self._doDrawingCalculations(dc)
        self.canvasItemList = []

        startDay = self.parent.blockItem.rangeStart
        
        for day in range(self.parent.blockItem.daysPerView):
            currentDate = startDay + DateTime.RelativeDateTime(days=day)
            rect = wx.Rect((self.dayWidth * day) + self.xOffset, 0,
                           self.dayWidth, self.size.height)
            self.DrawDay(dc, currentDate, rect)
                         

    def DrawDay(self, dc, date, rect):
        # Scaffolding, we'll get more sophisticated here

        # Set up fonts and brushes for drawing the events
        dc.SetTextForeground(wx.WHITE)
        dc.SetFont(self.smallFont)

        # Draw the events
        for item in self.parent.blockItem.getItemsByDate(date):
            time = item.startTime
            itemRect = wx.Rect(rect.x,
                               rect.y + int(self.hourHeight * (time.hour + time.minute/float(60))),
                               rect.width - 1,
                               int(item.duration.hours * self.hourHeight) - 1)
            self.canvasItemList.append(ColumnarCanvasItem(itemRect, item))

            # Draw one event
            headline = time.Format('%I:%M %p ') + item.displayName

            if (self.parent.blockItem.selection is item):
                dc.SetBrush(wx.Brush(wx.Colour(153, 153, 153)))
                dc.SetPen(wx.Pen(wx.Colour(128, 128, 128)))
            else:
                dc.SetBrush(wx.Brush(wx.Colour(204, 204, 204)))
                dc.SetPen(wx.Pen(wx.Colour(179, 179, 179)))
            
            dc.DrawRoundedRectangleRect(itemRect, radius=10)
            self.DrawWrappedText(dc, headline, itemRect)


    # handle mouse related actions: move, resize, create, select

    def OnSelectItem(self, item):
        self.parent.blockItem.selection = item
        self.parent.blockItem.postSelectionChanged()
        self.parent.wxSynchronizeWidget()

    def OnCreateItem(self, unscrolledPosition, createOnDrag):
        if createOnDrag:
            # @@@ disable until we work out repository issues
            # event.duration = DateTime.DateTimeDelta(0, 0, 60)
            #     x, y = self.getPositionFromDateTime(newTime)
            #     eventRect = wx.Rect(x, y,
            #          self.dayWidth - 1,
            #          int(event.duration.hours * self.hourHeight) - 1)
            pass
        else:
            # @@@ this code might want to live somewhere else, refactored
            newTime = self.getDateTimeFromPosition(unscrolledPosition)
            event = Calendar.CalendarEvent()
            event.InitOutgoingAttributes()
            event.ChangeStart(newTime)
            self.OnSelectItem(event)

            # @@@ Bug#1854 currently this is too slow,
            # and the notification causes flicker
            Globals.repository.commit()
        return None
    
    def OnResizingItem(self, unscrolledPosition):
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        item = self._dragBox.getItem()
        resizeMode = self._dragBox.getResizeMode(self._dragStartUnscrolled)
        delta = DateTime.DateTimeDelta(0, 0, 15)
        if (resizeMode == "LOW" and newTime > (item.startTime + delta)):
            item.endTime = newTime
        elif (resizeMode == "TOP" and newTime < (item.endTime - delta)):
            item.startTime = newTime
        self.Refresh()
    
    def OnDraggingItem(self, unscrolledPosition):
        dy = (self._dragStartUnscrolled.y - self._dragBox.bounds.y)
        position = wx.Point(unscrolledPosition.x, unscrolledPosition.y - dy)
        newTime = self.getDateTimeFromPosition(position)
        item = self._dragBox.getItem()
        if ((newTime.absdate != item.startTime.absdate) or
            (newTime.hour != item.startTime.hour) or
            (newTime.minute != item.startTime.minute)):
            item.ChangeStart(newTime)
            self.Refresh()

    def getDateTimeFromPosition(self, position):
        startDay = self.parent.blockItem.rangeStart
        # @@@ fixes Bug#1831, but doesn't really address the root cause
        # (the window is drawn with (0,0) virtual size on mac)
        if self.dayWidth > 0:
            deltaDays = (position.x - self.xOffset) / self.dayWidth
        else:
            deltaDays = 0
        deltaHours = (position.y) / self.hourHeight
        deltaMinutes = ((position.y % self.hourHeight) * 60) / self.hourHeight
        deltaMinutes = int(deltaMinutes/15) * 15
        newTime = startDay + DateTime.RelativeDateTime(days=deltaDays,
                                                       hours=deltaHours,
                                                       minutes=deltaMinutes)
        return newTime

    def getPositionFromDateTime(self, datetime):
        delta = datetime - self.parent.blockItem.rangeStart
        x = (self.dayWidth * delta.day) + self.xOffset
        y = int(self.hourHeight * (datetime.hour + datetime.minute/float(60)))
        return (x, y)
        
class WeekBlock(CalendarBlock):
    def __init__(self, *arguments, **keywords):
        super(WeekBlock, self).__init__ (*arguments, **keywords)

        # need to fix this
        self.daysPerView = 7
        self.rangeIncrement = DateTime.RelativeDateTime(days=self.daysPerView)
        self.setRange(DateTime.today())

    def instantiateWidget(self):
        return wxWeekPanel(self.parentBlock.widget,
                           Block.Block.getWidgetID(self))

    def setRange(self, date):
        if self.daysPerView == 7:
            # if in week mode, start at the beginning of the week
            delta = DateTime.RelativeDateTime(days=-6,
                                              weekday=(DateTime.Sunday, 0))
            self.rangeStart = date + delta
        else:
            # otherwise, stick with the given date
            self.rangeStart = date

class wxMonthCanvas(CollectionCanvas.wxCollectionCanvas, CalendarEventHandler):
    def __init__(self, *arguments, **keywords):
        super(wxMonthCanvas, self).__init__(*arguments, **keywords)

    def OnInit(self):

        # Setup the navigation buttons
        today = DateTime.today()
        
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "application/images/backarrow.png")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "application/images/forwardarrow.png")
        self.todayButton = CollectionCanvas.CanvasTextButton(self, today.Format("%b %d, %Y"),
                                                             self.bigFont, self.bigFontColor,
                                                             self.bgColor)
        self.monthButton = CollectionCanvas.CanvasTextButton(self, " September 8888 ",
                                                             self.bigFont, self.bigFontColor,
                                                             self.bgColor)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add((0,0), 1, wx.EXPAND, 5)
        box.Add((0,0), 1, wx.EXPAND, 5)
        box.Add(self.prevButton, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        box.Add(self.monthButton, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        box.Add(self.nextButton, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        box.Add((0,0), 1, wx.EXPAND, 5)
        box.Add(self.todayButton, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(box)
                                            
        self.Bind(wx.EVT_BUTTON, self.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.OnNext, self.nextButton)
        self.Bind(wx.EVT_BUTTON, self.OnToday, self.todayButton)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        self.Refresh()
        event.Skip()

    def wxSynchronizeWidget(self):
        self.monthButton.SetLabel(self.blockItem.rangeStart.Format("%B %Y"))
        self.Refresh()

    # Drawing logic

    def _doDrawingCalculations(self, dc):
        self.size = self.GetVirtualSize()
        self.yOffset = 50
        self.dayWidth = self.size.width / 7
        self.dayHeight = (self.size.height - self.yOffset) / 6
    
    def DrawBackground(self, dc):
        self._doDrawingCalculations(dc)

        # Use the transparent pen for drawing the background rectangles
        dc.SetPen(wx.TRANSPARENT_PEN)

        # Draw the background
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle((0,0), (self.size.width, self.size.height))
        
        # Set up pen for drawing the grid
        dc.SetPen(wx.Pen(wx.Colour(204, 204, 204)))

        # Draw the lines between the days
        for i in range(1, 7):
            dc.DrawLine((self.dayWidth * i, self.yOffset),
                        (self.dayWidth * i, self.size.height))

        # Draw the lines between the weeks
        for i in range(6):
            dc.DrawLine((0, (i * self.dayHeight) + self.yOffset),
                        (self.size.width,
                         (i * self.dayHeight) + self.yOffset))


    def DrawCells(self, dc):
        self._doDrawingCalculations(dc)
        self.canvasItemList = []
        
        # Delegate the drawing of each day
        startDay = self.blockItem.rangeStart + \
                   DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))

        # Draw each day in the month
        for week in range(6):
            for day in range(7):
                currentDate = startDay + DateTime.RelativeDateTime(days=(week*7 + day))
                rect = wx.Rect(self.dayWidth * day,
                               self.dayHeight * week + self.yOffset,
                               self.dayWidth,
                               self.dayHeight)
                self.DrawDay(dc, currentDate, rect)

        # Draw the weekdays
        for i in range(7):
            weekday = startDay + DateTime.RelativeDateTime(days=i)
            rect = wx.Rect(self.dayWidth * i,
                           self.yOffset - 20,
                           self.dayWidth, 20) # Related to font height?
            self.DrawWeekday(dc, weekday, rect)


    def DrawDay(self, dc, date, rect):
        # Scaffolding, we'll get more sophisticated here

        dc.SetTextForeground(self.bigFontColor)
        dc.SetFont(self.bigFont)

        # Draw the day header
        # Add logic to treat "today" or "not in current month" specially
        dc.DrawText(date.Format("%d"), (rect.x, rect.y))
        
        x = rect.x
        y = rect.y + 10
        w = rect.width
        h = 15

        dc.SetTextForeground(self.smallFontColor)
        dc.SetFont(self.smallFont)

        for item in self.blockItem.getItemsByDate(date):
            itemRect = wx.Rect(x, y, w, h)
            self.canvasItemList.append(CollectionCanvas.CanvasItem(itemRect, item))

            if (self.blockItem.selection is item):
                dc.SetPen(wx.BLACK_PEN)
                dc.SetBrush(wx.WHITE_BRUSH)
                dc.DrawRectangleRect(itemRect)
                
            self.DrawWrappedText(dc, item.displayName, itemRect)
            y += h

    def DrawWeekday(self, dc, weekday, rect):
        dc.SetTextForeground(self.bigFontColor)
        dc.SetFont(self.bigFont)

        dayName = weekday.Format('%a')
        self.DrawCenteredText(dc, dayName, rect)

    # handle mouse related actions: move, create

    def OnCreateItem(self, unscrolledPosition, createOnDrag):
        if not createOnDrag:
            # @@@ this code might want to live somewhere else, refactored
            newTime = self.getDateTimeFromPosition(unscrolledPosition)
            event = Calendar.CalendarEvent()
            event.InitOutgoingAttributes()
            event.ChangeStart(DateTime.DateTime(newTime.year, newTime.month,
                                                newTime.day,
                                                event.startTime.hour,
                                                event.startTime.minute))
            self.OnSelectItem(event)
            
            # @@@ Bug#1854 currently this is too slow,
            # and the notification causes flicker
            Globals.repository.commit()
        return None

    def OnDraggingItem(self, unscrolledPosition):
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        item = self._dragBox.getItem()
        if (newTime.absdate != item.startTime.absdate):
            item.ChangeStart(DateTime.DateTime(newTime.year, newTime.month,
                                               newTime.day,
                                               item.startTime.hour,
                                               item.startTime.minute))
            self.Refresh()

    def getDateTimeFromPosition(self, position):
        # x and y in whole canvas coordinates
        
        # the first day displayed in the month view
        startDay = self.blockItem.getStartDay()

        # the number of days over
        deltaDays = position.x / self.dayWidth

        # the number of weeks over
        deltaWeeks = (position.y - self.yOffset) / self.dayHeight

        newDay = startDay + DateTime.RelativeDateTime(days=deltaDays,
                                                      weeks=deltaWeeks)
        return newDay
    

class MonthBlock(CalendarBlock):
    def __init__(self, *arguments, **keywords):
        super(MonthBlock, self).__init__(*arguments, **keywords)

        self.rangeIncrement = DateTime.RelativeDateTime(months=1)
        self.setRange(DateTime.today())

    def instantiateWidget(self):
        return wxMonthCanvas(self.parentBlock.widget,
                             Block.Block.getWidgetID(self))

    def setRange(self, date):
        # override set range to pick the first day of the month
        self.rangeStart = DateTime.DateTime(date.year, date.month)

    def getStartDay(self):
        """ Returns the starting day of the month displayed.
        """
        startDay = self.rangeStart + \
                   DateTime.RelativeDateTime(days=-6,
                                             weekday=(DateTime.Sunday, 0))
        return startDay

    







