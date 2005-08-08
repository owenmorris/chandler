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
    margin = 4 #oh how I wish I had css
    
    def __init__(self, *arguments, **keywords):
        super(wxPreviewArea, self).__init__(*arguments, **keywords)
        self.currentDaysItems = []
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        charStyle = Styles.CharacterStyle()
        
        #see Bug 3625
        charStyle.fontSize = 11
        self.font = Styles.getFont(charStyle)
        self.fontHeight = Styles.getMeasurements(self.font).height
        
        self.text = ""

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.Draw(dc)

    def Draw(self, dc):
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
        for line in self.text.splitlines():
            dc.DrawText(line, self.margin, y)
            y += self.fontHeight
        dc.DestroyClippingRegion()
##         DrawingUtilities.DrawWrappedText(dc, self.text, self.GetRect())

    @staticmethod
    def TimeFormat(time):
        # @@@ needs to be locale specific using ?PyICU.  But then how would you
        # do spacing, vertical alignment?
        # TODO: superscripted minutes, vertical alignment/spacing
        if time.minute == 0:
            return "%d" % time.hour
        return "%d:%.2d" % (time.hour, time.minute)

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

        inRange = list(self.blockItem.getItemsInCurrentRange(allItems=True))
        self.currentDaysItems = [item for item in inRange if item.transparency == "confirmed"]
        
        self.text  = ""
        self.currentDaysItems.sort(cmp = self.SortForPreview)
        for i, item in enumerate(self.currentDaysItems):
            if i == self.blockItem.maximumEventsDisplayed:
                self.text += "%d more confirmed events...\n" % (len(self.currentDaysItems) - i,)
                break
            if item.allDay or item.anyTime:
                self.text += "%s\n" % item.displayName
            elif item.startTime == item.endTime:
                # at-time event
                self.text += "@ %s: %s\n" %(self.TimeFormat(item.startTime.time()), item.displayName)
            else:
                self.text += "%s - %s: %s\n" % (
                                self.TimeFormat(item.startTime.time()),
                                self.TimeFormat(item.endTime.time()),
                                item.displayName)
        if not self.text:
            self.ChangeHeightAndAdjustContainers(0)
            return
        
        
        dc = wx.ClientDC(self)
        self.Draw(dc)
        
        numLines = len(self.text.splitlines())
        self.ChangeHeightAndAdjustContainers(numLines * self.fontHeight + 2*self.margin)
        
        
        

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
        
