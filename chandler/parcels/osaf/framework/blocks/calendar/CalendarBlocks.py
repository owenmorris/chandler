""" Calendar Blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import wx.calendar
import wx.minical
import cPickle
from mx import DateTime

import osaf.contentmodel.calendar.Calendar as Calendar

import application.SimpleCanvas as SimpleCanvas
import osaf.framework.blocks.Block as Block


class CalendarItem(SimpleCanvas.wxSimpleDrawableObject):
    def __init__(self, canvas, item):
        super (CalendarItem, self).__init__ (canvas)
        self.item = item

    def OnMouseEvent(self, event):
        x, y = event.GetPositionTuple()
        if event.ButtonDown() and self.SelectedHitTest (x, y) :
            # self.canvas.editor.ClearItem()
            self.canvas.DeSelectAll()
            self.SetSelected()
            self.canvas.Update()
        
        if event.ButtonDown():

            if event.ButtonDown() and self.ReSizeHitTest(x, y):
                self.canvas.dragStart = wx.Point (self.bounds.x, self.bounds.y)
                self.canvas.CaptureMouse()
                self.canvas.dragCreateDrawableObject = self
                return True
            
            if event.ButtonDown() and self.DragHitTest(x, y):
                self.DoDrag(x, y)
                return True
        
            if event.ButtonDown() and self.EditHitTest(x, y):
                # self.canvas.editor.SetItem(self)
                return True
        
        event.Skip()
        return False

    def Draw(self, dc):
        # @@@ Scaffolding
        dc.SetBrush(wx.Brush(wx.Color(180, 192, 159)))
        if self.selected:
            dc.SetPen(wx.BLACK_PEN)
        else:
            dc.SetPen(wx.TRANSPARENT_PEN)
        
        dc.DrawRoundedRectangle((1, 1),
                                (self.bounds.width - 1,
                                 self.bounds.height - 1),
                                radius = 10)

        dc.SetTextForeground(wx.BLACK)
        dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, face="Verdana"))
        time = self.item.startTime
        self.DrawWrappedText(dc, time.Format('%I:%M %p ' ) + self.item.displayName, self.bounds.width - 1)

    def DrawWrappedText(self, dc, text, wrapLength):
        # @@@ hack hack hack 
        # Simple wordwrap to display the text, until we can
        # get the native text widgets to do it for us.
        offset = 5
         
        lines = text.splitlines()
        y = 0
        for line in lines:
            x = offset
            wrap = 0
            words = line.split(' ')
            for word in words:
                width, height = dc.GetTextExtent(word)
                if (x + width > wrapLength):
                    y += height
                    x = offset
                dc.DrawText(word, x, y)
                x += width
                width, height = dc.GetTextExtent(' ')
                dc.DrawText(' ', x, y)
                x += width
            y += height

    def DragHitTest(self, x, y):
        return self.visible
        #return (self.visible and not self.EditHitTest(x, y))

    def SelectedHitTest(self, x, y):
        return self.visible

    def EditHitTest(self, x, y):
        return False

    def ReSizeHitTest(self, x, y):
        reSizeBounds = wx.Rect(0, self.bounds.height - 20,
                               self.bounds.width, self.bounds.height)
        return self.visible and reSizeBounds.Inside((x,y))

    def DrawMask(self, dc):
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRoundedRectangle((1, 1),
                                (self.bounds.width - 1,
                                self.bounds.width - 1),
                                radius = 10)
   
    def ConvertDrawableObjectToDataObject(self, x, y):
        dataFormat = wx.CustomDataFormat("ChandlerItem")
        dragDropData = wx.CustomDataObject(dataFormat)
        data = cPickle.dumps((self.item.itsUUID, x, y), True)
        dragDropData.SetData(data)
        return dragDropData

    def SizeDrag(self, dragRect, startDrag, endDrag):
        position = dragRect.GetPosition()
        blockItem = self.canvas.blockItem
        self.item.startTime = blockItem.getDateTimeFromPosition(position.x,
                                                                position.y)

        endHour, endMin = blockItem.getTimeFromPosition(dragRect.GetBottom())
        self.item.endTime = DateTime.DateTime(self.item.startTime.year,
                                              self.item.startTime.month,
                                              self.item.startTime.day,
                                              endHour, endMin)
        if (self.item.duration.hours < .5):
            self.item.duration = DateTime.TimeDelta(.5)

        self.canvas.PlaceItemOnCalendar(self)

    def MoveTo(self, x, y):
        newTime = self.canvas.blockItem.getDateTimeFromPosition(x, y)
        self.item.ChangeStart(newTime)
        super(CalendarItem, self).MoveTo(x, y)

class wxCalendarBlock(SimpleCanvas.wxSimpleCanvas):
    def __init__(self, *arguments, **keywords):
        super (wxCalendarBlock, self).__init__(*arguments, **keywords)

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetScrollRate(0,0)
        self._initNavigationButtons()

        dataFormat = wx.CustomDataFormat("ChandlerItem")
        dropTargetDataObject = wx.CustomDataObject(dataFormat)
        dropTarget = SimpleCanvas.wxCanvasDropTarget(self, dropTargetDataObject)
        self.SetDropTarget(dropTarget)

    def _initNavigationButtons(self):
        today = DateTime.today()
        
        self.prevButton = wx.Button(self, -1, "prev")
        self.nextButton = wx.Button(self, -1, "next")
        self.todayButton = wx.Button(self, -1, today.Format("%B %d, %Y"))
        self.monthButton = wx.Button(self, -1, "September 8888")

        self.Bind(wx.EVT_BUTTON, self.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.OnNext, self.nextButton)
        self.Bind(wx.EVT_BUTTON, self.OnToday, self.todayButton)

    def displayItems(self):
        self.Freeze()

        for drawableObject in self.zOrderedDrawableObjects:
            if (self.blockItem.isDateInRange(drawableObject.item.startTime) and
                drawableObject.item.startTime.hour >= 6 and
                drawableObject.item.startTime.hour < 22):
                
                self.PlaceItemOnCalendar(drawableObject)
                drawableObject.Show(True)
            else:
                drawableObject.Show(False)
        self.Thaw()

    def renderDateChanged(self):
        self.monthButton.SetLabel(self.blockItem.rangeStart.Format("%B %Y"))
        self.displayItems()
        self.Refresh()

    def wxSynchronizeWidget(self):
        today = DateTime.today()
        self.todayButton.SetLabel(today.Format("%B %d, %Y"))
        self.monthButton.SetLabel(self.blockItem.rangeStart.Format("%B %Y"))

        # populate canvas with drawable items for each event on the calendar
        for item in self.blockItem.contents:
            drawableObject = CalendarItem(self, item)
            self.zOrderedDrawableObjects.append(drawableObject)
        self.displayItems()
        self._positionNavigationButtons()
        self.blockItem.postDateChanged()


    # Events

    def OnPrev(self, event):
        self.blockItem.decrementRange()
        self.blockItem.postDateChanged()
        self.renderDateChanged()

    def OnNext(self, event):
        self.blockItem.incrementRange()
        self.blockItem.postDateChanged()
        self.renderDateChanged()

    def OnToday(self, event):
        today = DateTime.today()
        self.blockItem.updateRange(today)
        self.blockItem.postDateChanged()
        self.renderDateChanged()

    def _positionNavigationButtons(self):
        (width, height) = self.monthButton.GetSize()
        x = (self.blockItem.size.width - width)/2
        self.monthButton.Move((x, 0))
        self.nextButton.Move((x + width, 0))
        (width, height) = self.prevButton.GetSize()
        self.prevButton.Move((x - width, 0))
        
        (width, height) = self.todayButton.GetSize()
        self.todayButton.Move((self.blockItem.size.width - width, 0))        

    def OnSize(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            newSize = self.GetSize()
            self.blockItem.size.width = newSize.width
            self.blockItem.size.height = newSize.height
            self.blockItem.setDirty(self.blockItem.VDIRTY, 'size', self.blockItem._values)   # Temporary repository hack -- DJA
            self.SetVirtualSize(newSize)
            self.displayItems()                        
            self._positionNavigationButtons()
            self.Refresh()
        event.Skip()

    def ConvertDataObjectToDrawableObject(self, dataObject, x, y, move):
        (uuid, hotx, hoty) = cPickle.loads(dataObject.GetData())
        blockItem = self.blockItem
        view = blockItem.itsView
        item = view.find(uuid)
        newTime = blockItem.getDateTimeFromPosition(x, y - hoty)
        
        if (move):
            item.ChangeStart(newTime)
        else: # copy
            pass

        newDrawableObject = CalendarItem(self, item)
        self.PlaceItemOnCalendar(newDrawableObject)

        view.commit()
        
        return newDrawableObject

    def CreateNewDrawableObject(self, dragRect, startDrag, endDrag):
        view = self.item.itsView
        newItem = Calendar.CalendarEvent(view=view)
        newItem.displayName = _("New Event")
        newDrawableObject = CalendarItem(self, newItem)
        newDrawableObject.SizeDrag(dragRect, startDrag, endDrag)

        view.commit()
        
        return newDrawableObject

class CalendarBlock(Block.RectangularChild):
    def __init__(self, *arguments, **keywords):
        super(CalendarBlock, self).__init__(*arguments, **keywords)

    def onSelectedDateChangedEvent(self, event):
        self.updateRange(event.arguments['start'])
        self.widget.renderDateChanged()

    def postDateChanged(self):
        self.postEventByName('SelectedDateChanged', {'start':self.rangeStart})

    # date methods

    def isDateInRange(self, date):
        begin = self.rangeStart
        end = begin + self.rangeIncrement
        return ((date > begin) and (date < end))

    def incrementRange(self):
        self.rangeStart += self.rangeIncrement

    def decrementRange(self):
        self.rangeStart -= self.rangeIncrement
    

class wxWeekBlock(wxCalendarBlock):
    def __init__(self, *arguments, **keywords):
        super (wxWeekBlock, self).__init__ (*arguments, **keywords)

    def PlaceItemOnCalendar(self, drawableObject):
        width = self.blockItem.dayWidth
        height = int(drawableObject.item.duration.hours * self.blockItem.hourHeight)
        x, y = self.blockItem.getPosFromDateTime(drawableObject.item.startTime)
        bounds = wx.Rect(x, y, width, height)
        drawableObject.SetBounds(bounds)

    def DrawBackground(self, dc):
        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        size = self.GetVirtualSize()
        dc.DrawRectangle((0, 0), (size.width, size.height))
        
        # Set up the font
        dc.SetTextForeground(wx.Colour(64, 64, 64))
        dc.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))

        # Set the pen for the lines separating the days
        dc.SetPen(wx.Pen(wx.Colour(183, 183, 183)))

        # horizontal lines separating hours + hour legend
        hour = DateTime.today() + DateTime.RelativeDateTime(hours=6)
        for j in range (self.blockItem.hoursPerView):
            dc.DrawText (hour.Format("%I"),
                         2, j * self.blockItem.hourHeight + self.blockItem.offset)
            dc.SetPen (wx.Pen(wx.Colour(204, 204, 204)))
            dc.DrawLine ((self.blockItem.offset,
                          j * self.blockItem.hourHeight + self.blockItem.offset),
                         (self.blockItem.size.width, j * self.blockItem.hourHeight + self.blockItem.offset))
            dc.SetPen(wx.Pen(wx.Colour(230, 230, 230)))
            dc.DrawLine ((self.blockItem.offset,
                          j * self.blockItem.hourHeight + (self.blockItem.hourHeight/2) + self.blockItem.offset),
                         (self.blockItem.size.width,
                          j * self.blockItem.hourHeight + (self.blockItem.hourHeight/2) + self.blockItem.offset))
            hour += DateTime.RelativeDateTime(hours=1)

        dc.SetPen(wx.Pen(wx.Colour(204, 204, 204)))

        if self.blockItem.daysPerView == 1:
            startDay = self.blockItem.rangeStart
        else:
            startDay = self.blockItem.rangeStart + DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))
        
        # Draw lines between the days
        for i in range (self.blockItem.daysPerView):
            currentDate = startDay + DateTime.RelativeDateTime(days=i)
            dc.DrawText (currentDate.Format("%b %d"), self.blockItem.offset + self.blockItem.dayWidth * i,
                                                       self.blockItem.offset - 20)
            dc.DrawLine ((self.blockItem.offset + self.blockItem.dayWidth * i, self.blockItem.offset),
                         (self.blockItem.offset + self.blockItem.dayWidth * i, self.blockItem.size.height))
        

class WeekBlock(CalendarBlock):
    def __init__(self, *arguments, **keywords):
        super (WeekBlock, self).__init__(*arguments, **keywords)
        
    def instantiateWidget(self):
        self.rangeIncrement = DateTime.RelativeDateTime(days=self.daysPerView)
        self.updateRange(DateTime.today() + self.rangeIncrement)

        widget = wxWeekBlock(self.parentBlock.widget,
                             Block.Block.getWidgetID(self))
        return widget

    # Derived attributes
    
    def getHourHeight(self):
        #return self.size.height / self.hoursPerView
        return (self.size.height - self.offset) / self.hoursPerView

    def getDayWidth(self):
        return (self.size.width - self.offset) / self.daysPerView

    dayWidth = property(getDayWidth)
    hourHeight = property(getHourHeight)

    # date methods
    
    def updateRange(self, date):
        if self.daysPerView == 1:
            self.rangeStart = date
        else:
            delta = DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))
            self.rangeStart = date + delta

    def getTimeFromPosition(self, y):
        hour = (y - self.offset) / self.hourHeight
        minutes = (((y - self.offset) % self.hourHeight) * 60) / self.hourHeight
        minutes = int(minutes/30) * 30
        return (hour + 6, minutes)

    def getDateFromPosition(self, x):
        daysFromStart = (x - self.offset) / self.dayWidth
        delta = DateTime.RelativeDateTime(days=daysFromStart)
        date = self.rangeStart + delta
        return (date.year, date.month, date.day)

    def getDateTimeFromPosition(self, x, y):
        year, month, day = self.getDateFromPosition(x)
        hour, minutes = self.getTimeFromPosition(y)
        datetime = DateTime.DateTime(year, month, day, hour, minutes)
        return datetime

    def getPosFromDateTime(self, datetime):
        delta = datetime - self.rangeStart
        x = (self.dayWidth * delta.day) + self.offset
        y = int(self.hourHeight * (datetime.hour - 6 + datetime.minute/float(60))) + self.offset
        return (x, y)

class wxMonthBlock(wxCalendarBlock):
    def __init__(self, *arguments, **keywords):
        super (wxMonthBlock, self).__init__ (*arguments, **keywords)

    def PlaceItemOnCalendar(self, drawableObject):
        width = self.blockItem.dayWidth
        height = 15
        x, y = self.blockItem.getPosFromDateTime(drawableObject.item.startTime)
        
        bounds = wx.Rect(x, y, width, height)
        drawableObject.SetBounds(bounds)

    def DrawBackground(self, dc):
        # Use the transparent pen for drawing the background rectangles
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Set up the font (currently uses the same font for all text)
        dc.SetTextForeground(wx.Colour(64, 64, 64))
        dc.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))        

        # Determine the starting day for the set of weeks to be shown
        # The Sunday of the week containing the first day of the month
        startDay = self.blockItem.rangeStart + \
                   DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))
        
        # Paint the header
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle((0, 0), (self.blockItem.size.width, self.blockItem.offset))
        
        today = DateTime.today()

        # Draw today in the upper right hand corner
        self.DrawAdjustedText(dc, today.Format("%b %d, %Y"))

        # Draw current month
        self.DrawCenteredText(dc, self.blockItem.rangeStart.Format("%B %Y"))
         
        # Draw each day, the headers and the events in the day (for now)
        dc.SetPen(wx.TRANSPARENT_PEN)
        for week in range(self.blockItem.weeksPerView):
            for day in range (self.blockItem.daysPerWeek):
                currentDate = startDay + DateTime.RelativeDateTime(days=(week*7 + day))

                # Label the day, highlight today, give the day the right
                # background color based on the "range" month
                if (currentDate.month != self.blockItem.rangeStart.month):
                    dc.SetBrush (wx.Brush(wx.Colour(230, 230, 230)))
                else:
                    dc.SetBrush (wx.WHITE_BRUSH)
                    
                dc.DrawRectangle ((self.blockItem.dayWidth * day,
                                   self.blockItem.dayHeight * week + self.blockItem.offset),
                                  (self.blockItem.dayWidth, self.blockItem.dayHeight))
                
                if (currentDate == today):
                    dc.SetTextForeground(wx.RED)                    
                dc.DrawText (currentDate.Format("%d"), 
                             self.blockItem.dayWidth * day + 10,
                              self.blockItem.dayHeight * week + self.blockItem.offset)
                if (currentDate == today):
                    dc.SetTextForeground(wx.Colour(64, 64, 64))

        # Set the pen for drawing the month grid
        dc.SetPen (wx.Pen(wx.Colour(204, 204, 204)))
        
        # Draw vertical lines separating days and the names of the weekdays
        for i in range (self.blockItem.daysPerWeek):
            weekday = startDay + DateTime.RelativeDateTime(days=i)
            dc.DrawText (weekday.Format('%A'),
                         (self.blockItem.dayWidth * i) + 10,
                          self.blockItem.offset - 20)
            if (i != 0):
                dc.DrawLine ((self.blockItem.dayWidth * i,
                              self.blockItem.offset),
                             (self.blockItem.dayWidth * i,
                              self.blockItem.size.height))
        
        # Draw horizontal lines separating weeks
        for j in range(self.blockItem.weeksPerView):
            dc.DrawLine ((0, (j * self.blockItem.dayHeight) + self.blockItem.offset),
                         (self.blockItem.size.width, 
                          (j* self.blockItem.dayHeight) + self.blockItem.offset))

    def DrawCenteredText(self, dc, text):
        (width, height) = dc.GetTextExtent(text)
        x = (self.blockItem.size.width - width)/2
        y = (self.blockItem.size.height - height)/2
        dc.DrawText(text, x, 0)

    def DrawAdjustedText(self, dc, text):
        (width, height) = dc.GetTextExtent(text)
        dc.DrawText(text, self.blockItem.size.width - width, 0)

class MonthBlock(CalendarBlock):

    def __init__(self, *arguments, **keywords):
        super (MonthBlock, self).__init__(*arguments, **keywords)
        
        self.rangeIncrement = DateTime.RelativeDateTime(months=1)
        self.updateRange(DateTime.today())

    def instantiateWidget(self):
        return wxMonthBlock(self.parentBlock.widget,
                            Block.Block.getWidgetID(self))

    # Derived attributes
    
    def getDayWidth(self):
        return self.size.width / self.daysPerWeek

    def getDayHeight(self):
        return (self.size.height - self.offset) / self.weeksPerView

    dayWidth = property(getDayWidth)
    dayHeight = property(getDayHeight)

    def updateRange(self, date):
        self.rangeStart = DateTime.DateTime(date.year, date.month)

    def getDateTimeFromPosition(self, x, y):
        # the first day displayed in the month view
        startDay = self.rangeStart + \
                   DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))

        # the number of days over
        deltaDays = x / self.dayWidth

        # the number of weeks down
        deltaWeeks = (y - self.offset) / self.dayHeight

        selectedDay = startDay + DateTime.RelativeDateTime(days=deltaDays,
                                                           weeks=deltaWeeks)
        return selectedDay

    def getPosFromDateTime(self, datetime):
        # the first day displayed in the month view
        startDay = self.rangeStart + \
                   DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))

        # the number of days separating the first day in the view
        # from the selected day
        dayDelta = datetime - startDay

        # place the event partway down the day, based on time
        timeDelta = ((float(datetime.hour)/24) * (self.dayHeight - 15))

        # count the number of days over
        x = self.dayWidth * (dayDelta.day % 7)

        # cound the number of weeks down, add header offset and time of day offset
        y = (self.dayHeight * (dayDelta.day / 7)) + self.offset + timeDelta

        return (x, y)


class wxMiniCalendar(wx.minical.wxMiniCalendar):
    def __init__(self, *arguments, **keywords):
        super (wxMiniCalendar, self).__init__(*arguments, **keywords)
        self.Bind(wx.minical.EVT_MINI_CALENDAR_SEL_CHANGED,
                  self.OnWXSelectItem)

    def wxSynchronizeWidget(self):
        self.SetWindowStyle(wx.minical.wxCAL_SUNDAY_FIRST |
                            wx.minical.wxCAL_SHOW_SURROUNDING_WEEKS)

    def Destroy(self):
        pass
        
    def OnWXSelectItem(self, event):
        self.blockItem.postEventByName ('SelectedDateChanged',
                                        {'start': self.getSelectedDate()})

    def getSelectedDate(self):
        wxdate = self.GetDate()
        mxdate = DateTime.DateTime(wxdate.GetYear(),
                                   wxdate.GetMonth() + 1,
                                   wxdate.GetDay())
        return mxdate

    def setSelectedDate(self, mxdate):
        wxdate = wx.DateTimeFromDMY(mxdate.day,
                                    mxdate.month - 1,
                                    mxdate.year)
        self.SetDate(wxdate)

    
    def setSelectedDateRange(self, mxstart, mxend):
        self.resetMonth()
        self.setSelectedDate(mxstart)
        
        if (mxstart.month != mxend.month):
            endday = mxstart.days_in_month + 1
        else:
            endday = mxend.day + 1
        
        for day in range(mxstart.day, endday):
            attr = wx.CalendarDateAttr(wx.WHITE, wx.BLUE, wx.WHITE,
                                       wx.SWISS_FONT)
            self.SetAttr(day, attr)
            
        today = DateTime.today()
        if ((today.year == mxstart.year) and (today.month == mxstart.month)):
            self.SetHoliday(today.day)
            
        self.Refresh()
    
    def resetMonth(self):
        for day in range(1,32):
            self.ResetAttr(day)

class MiniCalendar(Block.RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (MiniCalendar, self).__init__(*arguments, **keywords)

    def instantiateWidget(self):
        return wxMiniCalendar(self.parentBlock.widget,
                              Block.Block.getWidgetID(self))

    def onSelectedDateChangedEvent(self, event):
        self.widget.setSelectedDate(event.arguments['start'])


