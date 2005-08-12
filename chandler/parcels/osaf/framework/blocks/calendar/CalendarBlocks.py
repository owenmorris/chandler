""" Calendar Blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx
import wx.calendar
import wx.minical

from datetime import datetime, timedelta
from application import schema

from osaf.framework.blocks import Block
from osaf.framework.blocks import Styles
from osaf.framework.blocks import DrawingUtilities
from osaf.framework.blocks import ContainerBlocks
import CalendarCanvas

    
class wxMiniCalendar(wx.minical.MiniCalendar):
    def __init__(self, *arguments, **keywords):
        super (wxMiniCalendar, self).__init__(*arguments, **keywords)
        self.Bind(wx.minical.EVT_MINI_CALENDAR_SEL_CHANGED,
                  self.OnWXSelectItem)
        self.Bind(wx.minical.EVT_MINI_CALENDAR_DOUBLECLICKED, 
                  self.OnWXDoubleClick)

    def wxSynchronizeWidget(self):
        style = wx.minical.CAL_SUNDAY_FIRST | wx.minical.CAL_SHOW_SURROUNDING_WEEKS
        if '__WXMAC__' in wx.PlatformInfo:
            style |= wx.BORDER_SIMPLE
        else:
            style |= wx.BORDER_STATIC
        
        if isMainCalendarVisible() and self.blockItem.doSelectWeek:
            style |= wx.minical.CAL_HIGHLIGHT_WEEK
        self.SetWindowStyle(style)

    def OnWXSelectItem(self, event):
        self.blockItem.postEventByName ('SelectedDateChanged',
                                        {'start': self.getSelectedDate()})

    def OnWXDoubleClick(self, event):
        # Select the calendar filter
        self.blockItem.postEventByName ('ApplicationBarEvent', {})

        # Set the calendar to the clicked day
        self.blockItem.postEventByName ('SelectedDateChanged',
                                        {'start': self.getSelectedDate()})

    def getSelectedDate(self):
        wxdate = self.GetDate()
        date = datetime(wxdate.GetYear(),
                        wxdate.GetMonth() + 1,
                        wxdate.GetDay())
        return date

    def setSelectedDate(self, date):
        wxdate = wx.DateTimeFromDMY(date.day,
                                    date.month - 1,
                                    date.year)
        self.SetDate(wxdate)

    def setSelectedDateRange(self, start, end):
        self.resetMonth()
        self.setSelectedDate(start)

        if (start.month != end.month):
            endday = (datetime.replace(month=start.month+1) - start).days + 1
        else:
            endday = end.day + 1

        for day in range(start.day, endday):
            attr = wx.CalendarDateAttr(wx.WHITE, wx.BLUE, wx.WHITE,
                                       wx.SWISS_FONT)
            self.SetAttr(day, attr)

        today = datetime.today()
        if ((today.year == start.year) and (today.month == start.month)):
            self.SetHoliday(today.day)

        self.Refresh()

    def resetMonth(self):
        for day in range(1,32):
            self.ResetAttr(day)


def isMainCalendarVisible():
    # Heuristic: is the appbar calendar button selected (depressed)?
    calendarButton = Block.Block.findBlockByName("ApplicationBarEventButton")
    try:
        return calendarButton.selected
    except AttributeError:
        # Toolbar isn't rendered yet
        return False


class MiniCalendar(Block.RectangularChild):
    doSelectWeek = schema.One(schema.Boolean, initialValue = True)
    
    def __init__(self, *arguments, **keywords):
        super (MiniCalendar, self).__init__(*arguments, **keywords)

    def instantiateWidget(self):
        if '__WXMAC__' in wx.PlatformInfo:
            style = wx.BORDER_SIMPLE
        else:
            style = wx.BORDER_STATIC
        return wxMiniCalendar(self.parentBlock.widget,
                              Block.Block.getWidgetID(self), style=style)

    def onSelectedDateChangedEvent(self, event):
        self.widget.setSelectedDate(event.arguments['start'])
        
    def onSelectWeekEvent(self, event):
        self.doSelectWeek = event.arguments['doSelectWeek']
        self.widget.wxSynchronizeWidget()
        self.widget.Refresh()

    def onSelectItemEvent(self, event):
        self.widget.wxSynchronizeWidget()
        self.widget.Refresh()        


class PreviewArea(CalendarCanvas.CalendarBlock):
    maximumEventsDisplayed = 5 #Not at schema level .. unless user customization?
    
    def __init__(self, *arguments, **keywords):
        super(PreviewArea, self).__init__(*arguments, **keywords)
        self.rangeIncrement = timedelta(days=1)

    def onSelectItemEvent(self, event):
        self.widget.wxSynchronizeWidget()
        #self.widget.Refresh() 
        
    def instantiateWidget(self):
        return wxPreviewArea(self.parentBlock.widget, Block.Block.getWidgetID(self))


class wxPreviewArea(wx.Panel):
    margin = 4 #oh how I wish I had css :)
    
    def __init__(self, *arguments, **keywords):
        super(wxPreviewArea, self).__init__(*arguments, **keywords)
        self.currentDaysItems = []
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        charStyle = Styles.CharacterStyle()
        
        #see Bug 3625
        charStyle.fontSize = 11
        self.font = Styles.getFont(charStyle)
        self.fontHeight = Styles.getMeasurements(self.font).height
        
        charStyle.fontStyle = 'fakesuperscript'
        self.superscriptFont = Styles.getFont(charStyle)

        self.bigDigitWidth   = Styles.getMeasurements(self.font).digitWidth
        self.smallDigitWidth = Styles.getMeasurements(self.superscriptFont).digitWidth

        self.dashMargin = self.bigDigitWidth // 2
        self.eventTitleLeftMargin = int(self.bigDigitWidth * 1.5)
        self.text = ""
        
    def DrawEventLine(self, dc, y, item):
        #  A B  C  D  D E  F G
        #  | |  |  |  | |  | |
        #                    my allday or anytime event
        #  12 15   -  14 45  doctor's appointment
        #      9   -  11 10  happy hour
        #  @ 10 45           my at-time event
        
        # len(C->D) = len(D->E)  =  self.dashMargin
        # len(F->G) = self.eventTitleLeftMargin
        # A is at self.margin
        # there is no space between the hour and minute blocks.

        #should cache more of these calculations
        dc.SetFont(self.font)
        dashWidth, _ = dc.GetTextExtent('-')
        eventTitleOffset = 4*self.bigDigitWidth + 4*self.smallDigitWidth + \
                         dashWidth + 2*self.dashMargin + self.eventTitleLeftMargin
            
        if item.allDay or item.anyTime:
            dc.DrawText(item.displayName, eventTitleOffset, y)

        elif item.startTime == item.endTime:
            # at-time event
            start = "  @ "
            dc.DrawText(start, self.margin, y)
            startWidth, _ = dc.GetTextExtent(start)
            self.DrawTime(item.startTime.time(), dc, self.margin + startWidth, y, leftpad=False)
            dc.DrawText(item.displayName, eventTitleOffset, y)
            
        else:
            self.DrawTime(item.startTime.time(), dc, self.margin, y, rightalign=True)
            dashOffset = self.margin + 2*self.bigDigitWidth + 2*self.smallDigitWidth + self.dashMargin
            dc.DrawText('-', dashOffset, y)
            self.DrawTime(item.endTime.time(), dc, dashOffset + self.dashMargin + dashWidth, y, leftpad=False)
            dc.DrawText(item.displayName, eventTitleOffset, y)
        
    def DrawTime(self, time, dc, x, y, leftpad=True, rightalign=False):
        """
        @param time: a datetime.time object, its hour and minute get drawn with superscripts for the minutes
        does NOT change dc's font as a side effect.
        """
        oldFont = dc.GetFont()

        #tricky: we want to right-align the hour digit(s)
        #assumption: digits are monospaced (true of many but not all proportional fonts)
        # times new roman, arial, verdana, yes.  comic sans ms, no.
        hour = time.hour
        ##if hour == 0:  hour = 24
        hourstr = str(time.hour)
        if   len(hourstr) == 1 and leftpad:
            offset = self.bigDigitWidth
            hoursWidth = 2 * self.bigDigitWidth
        elif len(hourstr) == 1 and not leftpad:
            offset = 0
            hoursWidth = self.bigDigitWidth
        else:
            offset = 0
            hoursWidth = 2 * self.bigDigitWidth
        
        # and right align over the small digit space on the hour
        if time.minute == 0 and rightalign:
            offset += 2 * self.smallDigitWidth
            
        dc.SetFont(self.font)        
        dc.DrawText(str(time.hour), x+offset, y)
        
        
        if time.minute != 0: 
            minutestr = "%.2d" %time.minute  # zero pad <10
            dc.SetFont(self.superscriptFont)
            dc.DrawText(minutestr, x+hoursWidth, y)
        
        dc.SetFont(oldFont)
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.Draw(dc)

    def Draw(self, dc):
        """
        Draw all the items, based on what's in self.currentDaysItems
        @return the height of all the text drawn
        """
        dc.Clear()

        #White background
        dc.SetBackground(wx.WHITE_BRUSH)
        
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(*iter(self.GetRect()))
        
        dc.SetTextBackground( (255,255,255) )
        dc.SetTextForeground( (0,0,0) )
        dc.SetFont(self.font)
        
        m, r = self.margin, self.GetRect()
        dc.SetClippingRegion(m, m,  r.width - 2*m, r.height - 2*m)

        y = self.margin
        for i, item in enumerate(self.currentDaysItems):
            if i == self.blockItem.maximumEventsDisplayed:
                dc.DrawText("%d more confirmed..." %(len(self.currentDaysItems) - i),  
                            self.margin, y)
                y += self.fontHeight  #For end calculation
                break
            self.DrawEventLine(dc, y, item)
            y += self.fontHeight
        
        dc.DestroyClippingRegion()
        return y - self.margin

    def ChangeHeightAndAdjustContainers(self, newHeight):
        # @@@ hack until block-to-block attributes are safer to define: climb the tree
        wxSplitter = self.GetParent().GetParent()
        assert isinstance(wxSplitter, ContainerBlocks.wxSplitterWindow)

        currentHeight = self.GetSize()[1]
        heightDelta = currentHeight - newHeight
        
        # need to do 2 resizings. Freeze/Thaw are in hopes of elminiating the
        # flicker between them, but it doesn't seem to be doing much. The WX
        # docs say they're only "hints", but maybe this is using them wrong.
        
        self.GetParent().GetParent().Freeze()
        self.GetParent().Freeze()
        #adjust box container shared with minical.
        self.SetMinSize( (0, newHeight) )
        self.GetParent().Layout()
        
        #adjust splitter containing the box container
        wxSplitter.MoveSash(wxSplitter.GetSashPosition() + heightDelta)
        self.GetParent().Thaw()
        self.GetParent().GetParent().Thaw()
        
    def wxSynchronizeWidget(self):
        if isMainCalendarVisible():
            # disappear!
            self.ChangeHeightAndAdjustContainers(0)
            return

        inRange = list(self.blockItem.getItemsInCurrentRange(True, True))
        self.currentDaysItems = [item for item in inRange if item.transparency == "confirmed"]
        
        self.currentDaysItems.sort(cmp = self.SortForPreview)
        dc = wx.ClientDC(self)
        drawnHeight = self.Draw(dc)
        
        self.ChangeHeightAndAdjustContainers(drawnHeight + 2*self.margin)


    @staticmethod
    def SortForPreview(item1, item2):
        if (item1.anyTime or item1.allDay) and (item2.anyTime or item2.allDay):
            return cmp(item1.displayName, item2.displayName)
        if item1.anyTime or item1.allDay:
            return -1
        if item2.anyTime or item2.allDay:
            return 1
        if item1.startTime == item2.startTime:
            if item1.endTime == item2.endTime:
                return cmp(item1.displayName, item2.displayName)
            #duration
            return cmp(item1.endTime, item2.endTime)
        return cmp(item1.startTime, item2.startTime)
        

def dimTest():
    """find out the dimensions of digits in some font"""
    class TestFrame(wx.Frame):
        def __init__(self, *args, **kwds):
            super(TestFrame, self).__init__(*args, **kwds)
            self.Bind(wx.EVT_PAINT, self.OnPaint)
        def OnPaint(self, event):
            dc = wx.PaintDC(self)
            dc.Clear()
                    
            for d in range(10):
                dstr = str(d)
                dc.SetFont(Styles.getFont(Styles.CharacterStyle()))
                width, height = dc.GetTextExtent(dstr)
                print "%d has dimensions %d,%d" % (d,  width,height)            
        
    class TestApp(wx.App):
        def OnInit(self):
            frame = TestFrame(None, -1, "Test frame.")
            frame.Show(True)
            self.SetTopWindow(frame)
            return True
     
    app = TestApp(0)
    app.MainLoop()
    
