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
        if self.blockItem.doSelectWeek:
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

# BUG 3536: doSelectWeek/weekMode starts off as False for the minical, but the main calendar starts off True.
# Both behaviors seem appropriate for each area.
# Need to reconcile.  Maybe switching to calendar view should trigger minical to be in doSelectWeek mode?
# But if you switch out, does it stay on week mode?  no, it should go back to day mode... which day though?
# the original?
# where do we store that then?
#    -brendano

class MiniCalendar(Block.RectangularChild):
    doSelectWeek = schema.One(schema.Boolean, initialValue = False)
    
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


class PreviewArea(CalendarCanvas.CalendarBlock):
    weekMode = schema.One(schema.Boolean, initialValue = False)
        
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
        charStyle.fontSize = 8
        self.font = Styles.getFont(charStyle)
        self.fontHeight = Styles.getMeasurements(self.font).height

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.Draw(dc)

    def Draw(self, dc):
        dc.Clear()
        dc.SetBackground( wx.WHITE_BRUSH )
        
        dc.SetTextBackground( (255,255,255) )
        dc.SetTextForeground( (0,0,0) )
        
        dc.SetFont(self.font)
        dc.DrawText(self.text, 0,0)
        
    def wxSynchronizeWidget(self):

        self.text  = "stub: PreviewArea goes here\n"

        try:
            self.currentDaysItems = list(self.blockItem.getItemsInCurrentRange(True, True))
        except:
            self.text += "contents not set, so no events displayed\n"
            self.text += "but if you do set you'll get\n"
            self.text += "a strange layout bug (?!)\n"
        
        if self.blockItem.weekMode:
            self.text += "whole week selected so\n"
            self.text += "this pane should disappear (?)\n"
            
        else:
            self.text += "for day starting: %s\n" % self.blockItem.rangeStart
            self.text += "over timespan: %s\n" %self.blockItem.rangeIncrement
            self.text += "there are %d events:\n" % len(self.currentDaysItems)
            for item in self.currentDaysItems:
                if item.allDay or item.anyTime:
                    self.text += "%s\n" % item.displayName
                elif item.startTime == item.endTime:
                    # at-time event
                    self.text += "%s: %s\n" %(item.displayName, item.startTime.time())
                else:
                    self.text += "%s: %s - %s\n" % (item.displayName, item.startTime.time(), item.endTime.time())
                    
        numLines = len(self.text.split('\n'))
        self.SetMinSize( (-3, numLines * self.fontHeight + 3) )
        self.GetParent().Layout()
        self.GetParent().GetParent().Layout()
        
        dc = wx.ClientDC(self)
        self.Draw(dc)
