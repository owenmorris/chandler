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
        calendarButton = Block.Block.findBlockByName("ApplicationBarEventButton")
        try:
            if calendarButton.selected and self.blockItem.doSelectWeek:
                style |= wx.minical.CAL_HIGHLIGHT_WEEK
        except AttributeError:
            # Toolbar hasn't been rendered yet
            pass
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

# BUG 3536: doSelectWeek/weekMode starts off as False for the minical, but the main calendar starts off True.
# Both behaviors seem appropriate for each area.
# Need to reconcile.  Maybe switching to calendar view should trigger minical to be in doSelectWeek mode?
# But if you switch out, does it stay on week mode?  no, it should go back to day mode... which day though?
# the original?
# where do we store that then?
#    -brendano

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
    weekMode = schema.One(schema.Boolean, initialValue = False)
    
    maximumEventsDisplayed = 8  # @@@ make a parcel.xml-level attribute?
    
    def __init__(self, *arguments, **keywords):
        super(PreviewArea, self).__init__(*arguments, **keywords)
        self.rangeIncrement = timedelta(days=1)

    def onSelectWeekEvent(self, event):
        self.weekMode = event.arguments['doSelectWeek']        
        self.widget.wxSynchronizeWidget()

    def instantiateWidget(self):
        return wxPreviewArea(self.parentBlock.widget, Block.Block.getWidgetID(self))

class wxPreviewArea(wx.Panel):
    def __init__(self, *arguments, **keywords):
        super(wxPreviewArea, self).__init__(*arguments, **keywords)
        self.currentDaysItems = []
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        charStyle = Styles.CharacterStyle()
        charStyle.fontSize = 9
        self.font = Styles.getFont(charStyle)
        self.fontHeight = Styles.getMeasurements(self.font).height

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.Draw(dc)

    def Draw(self, dc):
        if self.blockItem.weekMode: return

        dc.Clear()

        #White background
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(*iter(self.GetRect()))
        
        dc.SetTextBackground( (255,255,255) )
        dc.SetTextForeground( (0,0,0) )
        
        dc.SetFont(self.font)
        y = 0
        for line in self.text.splitlines():
            dc.DrawText(line, 0, y)
            y += self.fontHeight
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
        # @@@ hack until block-to-block attribs are safe to use: climb the tree
        wxSplitter = self.GetParent().GetParent()
        assert isinstance(wxSplitter, ContainerBlocks.wxSplitterWindow)

        currentHeight = self.GetSize()[1]
        heightDelta = currentHeight - newHeight
        
        # need to do 2 resizings.  Would be nice to do the first without repainting
        
        #adjust box container shared with minical.
        self.SetMinSize( (0, newHeight) )
        self.GetParent().Layout()
        
        #adjust splitter containing the box container
        wxSplitter.SetSashPosition(wxSplitter.GetSashPosition() + heightDelta)
        
        
    def wxSynchronizeWidget(self):
        if self.blockItem.weekMode:
            # disappear!
            self.ChangeHeightAndAdjustContainers(0)
            return

        inRange = list(self.blockItem.getItemsInCurrentRange(True, True))
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
        
        numLines = len(self.text.splitlines())
        self.ChangeHeightAndAdjustContainers(numLines * self.fontHeight + 3)
        
        dc = wx.ClientDC(self)
        self.Draw(dc)

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
        