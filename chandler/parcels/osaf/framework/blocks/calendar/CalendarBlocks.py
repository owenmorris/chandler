""" Calendar Blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import time
from mx import DateTime

import application.SimpleCanvas as SimpleCanvas
import osaf.framework.blocks.Block as Block
import application.Globals as Globals
import repository.util.UUID as UUID

class CalendarItem(SimpleCanvas.wxSimpleDrawableObject):
    def __init__(self, canvas, item):
        SimpleCanvas.wxSimpleDrawableObject.__init__(self, canvas)
        self.item = item

    def PlaceItemOnCalendar(self):
        block = Globals.repository.find(self.canvas.blockUUID)
        width = block.dayWidth
        height = int(self.item.duration.hours * block.hourHeight)
        position = block.getPosFromDateTime(self.item.startTime)
        bounds = wx.Rect(position.x, position.y, width, height)
        self.SetBounds(bounds)

    def Draw(self, dc):
        # @@@ Scaffolding
        dc.SetBrush(wx.Brush(wx.Color(180, 192, 121)))
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        dc.DrawRoundedRectangle((1, 1),
                                (self.bounds.width - 1,
                                 self.bounds.height - 1),
                                radius=10)

        dc.SetTextForeground(wx.BLACK)
        dc.SetFont(wx.SWISS_FONT)
        time = self.item.startTime
        dc.DrawText(time.Format('%I:%M %p ') + self.item.headline, (10, 0))
        #dc.DrawText(self.item.headline, (10, 14))

    def DragHitTest(self, x, y):
        return False

    def SelectedHitTest(self, x, y):
        return False

    def EditHitTest(self, x, y):
        return False

    def ReSizeHitTest(self, x, y):
        return False


class wxWeekBlock(SimpleCanvas.wxSimpleCanvas):
    def __init__(self, *arguments, **keywords):
        SimpleCanvas.wxSimpleCanvas.__init__(self, *arguments, **keywords)
        self.scheduleUpdate = False
        self.lastUpdateTime = 0

        SimpleCanvas.wxSimpleCanvas.OnInit(self, None)

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        
        self.SetScrollRate(0,0)

    def wxSynchronizeWidget(self):
        block = Globals.repository.find(self.blockUUID)
        
        # populate canvas with drawable items for each event on the calendar
        for item in block.contentSpec:
            if block.isDateInRange(item.startTime):
                drawableObject = CalendarItem(self, item)
                self.zOrderedDrawableObjects.append(drawableObject)
                drawableObject.PlaceItemOnCalendar()

        # subscribe to repository changes
        # @@@ common code, should be refactored somehow
        try:
            subscription = self.subscriptionUUID
        except:
            events = [Globals.repository.find('//parcels/osaf/framework/item_changed'),
                      Globals.repository.find('//parcels/osaf/framework/item_added'),
                      Globals.repository.find('//parcels/osaf/framework/item_deleted')]
            self.subscriptionUUID = UUID.UUID()
            Globals.notificationManager.Subscribe(events,
                                                  self.subscriptionUUID,
                                                  block.contentSpec.onItemChanges)

        self.scheduleUpdate = False
        self.lastUpdateTime = time.time()

    def __del__(self):
        Globals.notificationManager.Unsubscribe(self.subscriptionUUID)
        del Globals.association[self.blockUUID]

    # Event handlers

    def OnSize(self, event):
        block = Globals.repository.find(self.blockUUID)
        newSize = self.GetSize()
        block.size.width = newSize.width
        block.size.height = newSize.height
        self.SetVirtualSize(newSize)
        for drawableObject in self.zOrderedDrawableObjects:
            drawableObject.PlaceItemOnCalendar()
        event.Skip()

    def OnIdle(self, event):
        if self.scheduleUpdate:
            if (time.time() - self.lastUpdateTime) > 1.0:
                self.wxSynchronizeWidget()
                self.Refresh()
        else:
            self.lastupdateTime = time.time()
        event.Skip()        

    def DrawBackground(self, dc):
        block = Globals.repository.find(self.blockUUID)
        
        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wx.Brush(wx.Colour(246, 250, 254)))
        size = self.GetVirtualSize()
        dc.DrawRectangle((0, 0), (size.width, size.height))
        
        # Set up the font
        dc.SetTextForeground(wx.Colour(63, 87, 119))
        dc.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))

        # Set the pen for the lines separating the days
        dc.SetPen(wx.Pen(wx.Colour(183, 183, 183)))

        # horizontal lines separating hours + hour legend
        year = DateTime.today()
        for j in range(block.hoursPerView):
            dc.DrawText(year.Format("%I %p"), (2, j * block.hourHeight))
            dc.SetPen(wx.Pen(wx.Colour(183, 183, 183)))
            dc.DrawLine((block.offset, j * block.hourHeight),
                        (block.size.width, j * block.hourHeight))
            dc.SetPen(wx.Pen(wx.Colour(225, 225, 225)))
            dc.DrawLine((block.offset, j * block.hourHeight + (block.hourHeight/2)),
                        (block.size.width,
                         j * block.hourHeight + (block.hourHeight/2)))
            year += DateTime.RelativeDateTime(hours=1)

        dc.SetPen(wx.BLACK_PEN)
        
        # Draw lines between the days
        for i in range(block.daysPerView):
            dc.DrawLine((block.offset + block.dayWidth * i, 0),
                        (block.offset + block.dayWidth * i, block.size.height))
        

class WeekBlock(Block.RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (WeekBlock, self).__init__(*arguments, **keywords)
        
        self.rangeIncrement = DateTime.RelativeDateTime(days=7)
        self.updateRange(DateTime.today() + self.rangeIncrement)

    def instantiateWidget(self, parent, parentWindow):
        canvas = wxWeekBlock(parentWindow,
                             Block.Block.getWidgetID(self))
        return canvas, None, None

    # Event handlers

    def NeedsUpdate(self):
        widget = Globals.association[self.itsUUID]
        widget.scheduleUpdate = True

    # Derived attributes
    
    def getHourHeight(self):
        return self.size.height / self.hoursPerView

    def getDayWidth(self):
        return self.size.width / self.daysPerView

    dayWidth = property(getDayWidth)
    hourHeight = property(getHourHeight)

    # date methods
    
    def isDateInRange(self, date):
        begin = self.rangeStart
        end = begin + self.rangeIncrement
        return ((date > begin) and (date < end))

    def updateRange(self, date):
        delta = DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))
        self.rangeStart = date + delta

    def incrementRange(self, date):
        self.rangeStart += self.rangeIncrement

    def decrementRange(self, date):
        self.rangeStart -= self.rangeIncrement

    def getPosFromDateTime(self, datetime):
        delta = datetime - self.rangeStart
        x = (self.dayWidth * delta.day) + self.offset
        y = int(self.hourHeight * (datetime.hour + datetime.minute/float(60)))
        return wx.Point(x, y)

class wxMonthBlock(SimpleCanvas.wxSimpleCanvas):
    def __init__(self, *arguments, **keywords):
        SimpleCanvas.wxSimpleCanvas.__init__(self, *arguments, **keywords)
        self.scheduleUpdate = False
        self.lastUpdateTime = 0

        SimpleCanvas.wxSimpleCanvas.OnInit(self, None)

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        
        self.SetScrollRate(0,0)
    
    def wxSynchronizeWidget(self):
        block = Globals.repository.find(self.blockUUID)

        # populate canvas with drawable items for each event on the calendar
        for item in block.contentSpec:
            if block.isDateInRange(item.startTime):
                drawableObject = CalendarItem(self, item)
                self.zOrderedDrawableObjects.append(drawableObject)

        # subscribe to repository changes
        # @@@ common code, should be refactored somehow
        try:
            subscription = self.subscriptionUUID
        except:
            events = [Globals.repository.find('//parcels/osaf/framework/item_changed'),
                      Globals.repository.find('//parcels/osaf/framework/item_added'),
                      Globals.repository.find('//parcels/osaf/framework/item_deleted')]
            self.subscriptionUUID = UUID.UUID()
            Globals.notificationManager.Subscribe(events,
                                                  self.subscriptionUUID,
                                                  block.contentSpec.onItemChanges)

            self.scheduleUpdate = False
            self.lastUpdateTime = time.time()

    def __del__(self):
        Globals.notificationManager.Unsubscribe(self.subscriptionUUID)
        del Globals.association[self.blockUUID]

    # Events

    def OnSize(self, event):
        block = Globals.repository.find(self.blockUUID)
        newSize = self.GetSize()
        block.size.width = newSize.width
        block.size.height = newSize.height
        self.SetVirtualSize(newSize)
        event.Skip()

    def OnIdle(self, event):
        if self.scheduleUpdate:
            if (time.time() - self.lastUpdateTime) > 1.0:
                self.wxSynchronizeWidget()
                self.Refresh()
        else:
            self.lastupdateTime = time.time()
        event.Skip()


    def DrawBackground(self, dc):
        block = Globals.repository.find(self.blockUUID)
        
        # Use the transparent pen for drawing the background rectangles
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Set up the font (currently uses the same font for all text)
        dc.SetTextForeground(wx.Colour(63, 87, 119))
        dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))        

        # Determine the starting day for the set of weeks to be shown
        # The Sunday of the week containing the first day of the month
        startDay = block.rangeStart + \
                   DateTime.RelativeDateTime(days=-6, weekday=(DateTime.Sunday, 0))
        
        # Paint the header
        dc.SetBrush(wx.Brush(wx.Colour(222, 231, 239)))
        dc.DrawRectangle((0, 0), (block.size.width, block.offset))
        
        today = DateTime.today()

        # Draw each day, the headers and the events in the day (for now)
        dc.SetPen(wx.TRANSPARENT_PEN)
        for week in range(block.weeksPerView):
            for day in range(block.daysPerWeek):
                currentDate = startDay + DateTime.RelativeDateTime(days=(week*7 + day))

                # Label the day, highlight today, give the day the right
                # background color based on the "range" month
                if (currentDate.month != block.rangeStart.month):
                    dc.SetBrush(wx.Brush(wx.Colour(246, 250, 254)))
                else:
                    dc.SetBrush(wx.Brush(wx.Colour(232, 241, 249)))
                    
                dc.DrawRectangle((block.dayWidth * day,
                                  block.dayHeight * week + block.offset),
                                 (block.dayWidth, block.dayHeight))
                
                if (currentDate == today):
                    dc.SetTextForeground(wx.RED)                    
                dc.DrawText(currentDate.Format("%d %b"), 
                            (block.dayWidth * day + 10,
                             block.dayHeight * week + block.offset))
                if (currentDate == today):
                    dc.SetTextForeground(wx.Colour(63, 87, 119))

        # Set the pen for drawing the month grid
        dc.SetPen(wx.Pen(wx.Colour(183, 183, 183)))
        
        # Draw vertical lines separating days and the names of the weekdays
        for i in range(block.daysPerWeek):
            weekday = startDay + DateTime.RelativeDateTime(days=i)
            dc.DrawText(weekday.Format('%A'), ((block.dayWidth * i) + 10, 0))
            if (i != 0):
                dc.DrawLine((block.dayWidth * i, 0),
                            (block.dayWidth * i, block.size.height))
        
        # Draw horizontal lines separating weeks
        for j in range(block.weeksPerView):
            dc.DrawLine((0, (j * block.dayHeight) + block.offset),
                        (block.size.width, 
                         (j* block.dayHeight) + block.offset))


class MonthBlock(Block.RectangularChild):

    def __init__(self, *arguments, **keywords):
        super (MonthBlock, self).__init__(*arguments, **keywords)
        self.rangeIncrement = DateTime.RelativeDateTime(months=1)
        self.updateRange(DateTime.today())

    def instantiateWidget(self, parent, parentWindow):
        canvas = wxMonthBlock(parentWindow,
                              Block.Block.getWidgetID(self))
        return canvas, None, None

    # Event handlers

    def NeedsUpdate(self):
        widget = Globals.association[self.itsUUID]
        widget.scheduleUpdate = True

    # Derived attributes
    
    def getDayWidth(self):
        return self.size.width / self.daysPerWeek

    def getDayHeight(self):
        return (self.size.height - self.offset) / self.weeksPerView

    dayWidth = property(getDayWidth)
    dayHeight = property(getDayHeight)

    # date methods

    def isDateInRange(self, date):
        begin = self.rangeStart
        end = begin + self.rangeIncrement
        return ((date > begin) and (date < end))

    def updateRange(self, date):
        self.rangeStart = DateTime.DateTime(date.year, date.month)

    def incrementRange(self, date):
        self.rangeStart += self.rangeIncrement

    def decrementRange(self, date):
        self.rangeStart -= self.rangeIncrement
    



