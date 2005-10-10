"""
Calendar Blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx
import wx.calendar
import wx.minical

from application import schema

from osaf.framework.blocks import Block
from osaf.framework.blocks import Styles
from osaf.framework.blocks import DrawingUtilities
from osaf.framework.blocks import ContainerBlocks
import CalendarCanvas
import osaf.pim.calendar.Calendar as Calendar
from datetime import datetime, date, time, timedelta
from PyICU import ICUtzinfo
from osaf.framework.attributeEditors import DateTimeAttributeEditor
from i18n import OSAFMessageFactory as _


class wxMiniCalendar(wx.minical.MiniCalendar):

    # Used to limit the frequency with which we repaint the minicalendar
    _redrawCount = 1

    def __init__(self, *arguments, **keywords):
        super (wxMiniCalendar, self).__init__(*arguments, **keywords)
        self.Bind(wx.minical.EVT_MINI_CALENDAR_SEL_CHANGED,
                  self.OnWXSelectItem)
        self.Bind(wx.minical.EVT_MINI_CALENDAR_DOUBLECLICKED, 
                  self.OnWXDoubleClick)
        self.Bind(wx.minical.EVT_MINI_CALENDAR_UPDATE_BUSY,
                  self.setFreeBusy)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def wxSynchronizeWidget(self):
        style = wx.minical.CAL_SUNDAY_FIRST | wx.minical.CAL_SHOW_SURROUNDING_WEEKS | wx.minical.CAL_SHOW_BUSY
        if '__WXMAC__' in wx.PlatformInfo:
            style |= wx.BORDER_SIMPLE
        else:
            style |= wx.BORDER_STATIC
        
        if isMainCalendarVisible() and self.blockItem.doSelectWeek:
            style |= wx.minical.CAL_HIGHLIGHT_WEEK
        self.SetWindowStyle(style)
        self.setFreeBusy(None)

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

    def setFreeBusy(self, event):
        self._redrawCount += 1
        self.Refresh()

    def OnPaint(self, event):
        self._checkRedraw()
        event.Skip(True)

    def _checkRedraw(self):
        if self._redrawCount > 0:
            self._redrawCount = 0

            startWxDate = self.GetStartDate();
            endWxDate = startWxDate + wx.DateSpan.Month() + wx.DateSpan.Month() + wx.DateSpan.Month()

            startDate = date(startWxDate.GetYear(),
                            startWxDate.GetMonth() + 1,
                            startWxDate.GetDay())

            month = startDate.month + 3
            if month > 12:
                endDate = startDate.replace(year=startDate.year+1,
                                            month=month - 12)
            else:
                endDate = startDate.replace(month=month)

            numDays = (endDate - startDate).days
            busyFractions = {}
            defaultTzinfo = ICUtzinfo.getDefault()
            
            # The exact algorithm for the busy state is yet to be determined.  For now, just 
            # get the confirmed items on a given day and calculate their total duration.  As long
            # as there is at least one event the busy bar should be at least 1/4 height (so that it
            # is visible).  A 100% full day is assumed to be 12 hours worth of appointments.
            for item in self.blockItem.getItemsInRange(
                (datetime.combine(startDate, time(0)),
                 datetime.combine(endDate, time(0))),
                timedItems=True, dayItems=True):
    
                if item.transparency == "confirmed":
                    # @@@ Multiday events -- Grant???
                    if item.startTime.tzinfo is not None:
                        startTime = item.startTime.astimezone(defaultTzinfo)
                    else:
                        startTime = item.startTime
                    offset = (startTime.date() - startDate).days
                    
                    # We set a minimum "Busy" value of 0.25 for any
                    # day with a confirmed event.
                    fraction = busyFractions.get(offset, 0.25)
            
                    if item.allDay:
                        hours = 12.0
                    else:
                        # Seems wrong for events > 1 day in duration
                        hours = (item.duration.seconds / (60 * 60) )
                        
                    fraction += (hours / 12.0)
                    
                    busyFractions[offset] = min(fraction, 1.0)
    
            offset = 0
            while (startDate < endDate):
                self.SetBusy(startWxDate, busyFractions.get(offset, 0.0))
                startWxDate += wx.DateSpan.Day()
                startDate += timedelta(days=1)
                offset += 1
    
    def AdjustSplit(self, splitter, height):
        headerHeight = self.GetHeaderSize().height
        previewWidget = Block.Block.findBlockByName("PreviewArea").widget
        previewHeight = previewWidget.GetSize()[1]
        monthHeight = self.GetMonthSize().height
        
        newHeight = monthHeight + headerHeight + previewHeight
        numMonths = 1
        while ( ( (newHeight + 0.5 * monthHeight) < height) and numMonths < 3 ):
            newHeight += monthHeight
            numMonths += 1
        return newHeight
            
def isMainCalendarVisible():
    # Heuristic: is the appbar calendar button selected (depressed)?
    calendarButton = Block.Block.findBlockByName("ApplicationBarEventButton")
    try:
        return calendarButton.selected
    except AttributeError:
        # Toolbar isn't rendered yet
        return False


class MiniCalendar(CalendarCanvas.CalendarBlock):
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
        self.synchronizeWidget()
        self.widget.Refresh()

    def onSelectItemsEvent(self, event):
        self.synchronizeWidget()
        self.widget.Refresh()        

    def onSetContentsEvent(self, event):
        #We want to ignore, because view changes could come in here, and we
        #never want to change our collection
        pass
    
class PreviewArea(CalendarCanvas.CalendarBlock):
    timeCharacterStyle = schema.One(Styles.CharacterStyle)
    eventCharacterStyle = schema.One(Styles.CharacterStyle)
    maximumEventsDisplayed = schema.One(schema.Integer, initialValue=5)

    schema.addClouds(
        copying = schema.Cloud(byRef=[timeCharacterStyle, eventCharacterStyle])
    )

    def __init__(self, *arguments, **keywords):
        super(PreviewArea, self).__init__(*arguments, **keywords)
        self.rangeIncrement = timedelta(days=1)

    def onSelectItemsEvent(self, event):
        self.synchronizeWidget()
        #self.widget.Refresh() 
    def onSetContentsEvent(self, event):
        #We want to ignore, because view changes could come in here, and we
        #never want to change our collection
        pass
    
    def instantiateWidget(self):
        if not self.getHasBeenRendered():
            self.setRange( datetime.now().date() )
            self.setHasBeenRendered()        
        return wxPreviewArea(self.parentBlock.widget, 
                             Block.Block.getWidgetID(self),
                             timeCharStyle = self.timeCharacterStyle,
                             eventCharStyle = self.eventCharacterStyle)


class wxPreviewArea(wx.Panel):
    _redrawCount = 1
    vMargin = 4 # space above & below text
    hMargin = 6 # space on sides
    midMargin = 6 # space between time & date
    
    def __init__(self, parent, id, timeCharStyle, eventCharStyle,
                 *arguments, **keywords):
        super(wxPreviewArea, self).__init__(parent, id, *arguments, **keywords)
        self.currentDaysItems = []
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        self.timeFont = Styles.getFont(timeCharStyle)
        self.eventFont = Styles.getFont(eventCharStyle)
        self.labelPosition = -1 # Note that we haven't measured things yet.
                
    def OnPaint(self, event):
        self._checkRedraw()
        dc = wx.PaintDC(self)
        self.Draw(dc)

    def Draw(self, dc):
        """
        Draw all the items, based on what's in self.currentDaysItems
        
        @return the height of all the text drawn
        """        
        # Set up drawing & clipping
        dc.Clear()
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(*iter(self.GetRect()))
        dc.SetTextBackground( (255,255,255) )
        dc.SetTextForeground( (0,0,0) )
        r = self.GetRect()
        dc.SetClippingRegion(self.hMargin, self.vMargin,
                             r.width - (2 * self.hMargin),
                             r.height - (2 * self.vMargin))

        if self.labelPosition == -1:
            # First time - do a little measuring
            # Each line is going to be:
            # (hMargin)(12:00 AM)(midMargin)(Event name)
            # and we'll draw the time aligned with the colon.
            # If the locale doesn't use AM/PM, it won't show; so, format a
            # generic time and see how it looks:
            timeFormat = DateTimeAttributeEditor.shortTimeFormat
            genericTime = timeFormat.format(datetime(2005,1,1,12,00))
            self.timeSeparator = ':'
            #XXX [18n] Localizing the time separator is an issue
            # it forces the localizer to understand these programming semantics
            for c in genericTime: # @@@ This might need work
                if c in (_(u':.')): # Which time separator actually got used?
                    self.timeSeparator = c
                    break
            dc.SetFont(self.timeFont)
            preSep = genericTime[:genericTime.find(self.timeSeparator)]
            self.colonPosition = dc.GetTextExtent(preSep)[0] + self.hMargin
            self.labelPosition = dc.GetTextExtent(genericTime)[0] \
                                 + self.hMargin + self.midMargin
            
            self.timeFontHeight = Styles.getMeasurements(self.timeFont).height 
            self.eventFontHeight = Styles.getMeasurements(self.eventFont).height 
            self.lineHeight = max(self.timeFontHeight, self.eventFontHeight)
            self.timeFontOffset = (self.lineHeight - self.timeFontHeight)
            self.eventFontOffset = (self.lineHeight - self.eventFontHeight)
            
        # Draw each event            
        y = self.vMargin
        for i, item in enumerate(self.currentDaysItems):
            if i == self.blockItem.maximumEventsDisplayed:
                #XXX: [i18n] what is this text for?
                #     It will be hard for a translator to work with
                #     since it is vague
                dc.SetFont(self.eventFont)
                dc.DrawText(_(u"%(unknownValue)d more confirmed...") % {'unknownValue': (len(self.currentDaysItems) - i)},
                            self.hMargin, y + self.eventFontOffset)
                y += self.lineHeight  #For end calculation
                break

            if not (item.allDay or item.anyTime):
                # Draw the time
                dc.SetFont(self.timeFont)
                formattedTime = DateTimeAttributeEditor.shortTimeFormat.\
                                format(item.startTime)
                preSep = formattedTime[:formattedTime.find(self.timeSeparator)]
                prePos = self.colonPosition - dc.GetTextExtent(preSep)[0]
                dc.DrawText(formattedTime, prePos, y + self.timeFontOffset)
                # Draw the event text to the right of the time.
                x = self.labelPosition 
            else:
                # Draw allDay/anyTime events at the left margin
                x = self.hMargin
            
            # Draw the event text. It'll be clipped automatically because we
            # set a clipregion above.
            dc.SetFont(self.eventFont)
            dc.DrawText(item.displayName, x, y + self.eventFontOffset)

            y += self.lineHeight
        
        dc.DestroyClippingRegion()
        return y - self.vMargin

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
        self._redrawCount += 1
        
    def _checkRedraw(self):
        if self._redrawCount > 0:
            self._redrawCount = 0

            if isMainCalendarVisible():
                # disappear!
                self.ChangeHeightAndAdjustContainers(0)
                return

            inRange = list(self.blockItem.getItemsInCurrentRange(dayItems=True,
                                                               timedItems=True))
            self.currentDaysItems = [item for item in inRange if item.transparency == "confirmed"]
        
            self.currentDaysItems.sort(cmp = self.SortForPreview)
            dc = wx.ClientDC(self)
            drawnHeight = self.Draw(dc)
        
            self.ChangeHeightAndAdjustContainers(drawnHeight + (2 * self.vMargin))


    @staticmethod
    def SortForPreview(item1, item2):
        if (item1.anyTime or item1.allDay) and (item2.anyTime or item2.allDay):
            return cmp(item1.displayName, item2.displayName)
        if item1.anyTime or item1.allDay:
            return -1
        if item2.anyTime or item2.allDay:
            return 1
        return Calendar.datetimeOp(item1.startTime, 'cmp', item2.startTime) \
               or cmp(item1.duration, item2.duration) \
               or cmp(item1.displayName, item2.displayName)

