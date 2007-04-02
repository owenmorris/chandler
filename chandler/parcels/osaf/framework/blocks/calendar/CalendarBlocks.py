#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

"""
Calendar Blocks
"""

__parcel__ = "osaf.framework.blocks.calendar"

import wx
import wx.calendar
import minical

from application import schema

from osaf.framework.blocks import (
    Block, Styles, DrawingUtilities, ContainerBlocks, DragAndDrop
    )

from osaf import Preferences
import osaf.pim as pim
import CalendarCanvas
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim import EventStamp, has_stamp, isDead
from datetime import datetime, date, time, timedelta
from PyICU import ICUtzinfo
from i18n import ChandlerMessageFactory as _
from application import styles

from application.dialogs import RecurrenceDialog

if '__WXMAC__' in wx.PlatformInfo:
    PLATFORM_BORDER = wx.BORDER_NONE
else:
    PLATFORM_BORDER = wx.BORDER_STATIC

zero_delta = timedelta(0)
one_day = timedelta(1)

class wxMiniCalendar(DragAndDrop.DropReceiveWidget,
                     DragAndDrop.ItemClipboardHandler,
                     CalendarCanvas.CalendarNotificationHandler,
                     minical.PyMiniCalendar,
                     ):

    # Used to limit the frequency with which we repaint the minicalendar.
    # This used to be a real issue, but with the 0.6 notification system,
    # we could probably just rely on the usual wxSynchronize mechanism.
    _recalcCount = 1

    # In the case of adding new events, we may be able to get away
    # with just updating a few days on the minicalendar. In those
    # cases, _eventsToAdd will be non-None.
    _eventsToAdd = None

     # Note that _recalcCount wins over _eventsToAdd. That's
     # because more general changes (i.e. ones we don't know
     # how to optimize) require a full recalculation.

    def OnHover(self, x, y, dragResult):
        """
        Override this to perform an action when a drag cursor is
        hovering over the widget.

        @return: A wxDragResult other than dragResult if you want to change
                 the drag operation
        """
        (region, value) =  self.HitTest(wx.Point(x, y))
        if region in (minical.CAL_HITTEST_DAY,
                      minical.CAL_HITTEST_SURROUNDING_WEEK):
            if self.hoverDate != value:
                self.hoverDate = value
                self.Refresh()
        else:
            self.hoverDate = None

        # only allow drag and drop of items
        if self.GetDraggedFromWidget() is None:
            return wx.DragNone
        else:
            return dragResult

    def AddItems(self, itemList):
        """
        Override this to add the dropped items to your widget.
        """
        if self.hoverDate is not None:
            for item in itemList:
                proxy = RecurrenceDialog.getProxy(u'ui', item,
                                        endCallback=self.wxSynchronizeWidget)
                event = EventStamp(proxy)
                if not has_stamp(proxy, EventStamp):
                    event.add() # stamp as an event
                    event.anyTime = True
                oldTime = getattr(event, 'startTime', self.hoverDate).timetz()
                event.startTime = datetime.combine(self.hoverDate, oldTime)
                proxy.setTriageStatus('auto')

        self.hoverDate = None
        self.Refresh()

    def OnLeave(self):
        """
        Override this to perform an action when hovering terminates.
        """
        self.hoverDate = None

    def __init__(self, *arguments, **keywords):
        super (wxMiniCalendar, self).__init__(*arguments, **keywords)

        # on Linux, because there are no borders around windows, we
        # want a line separating the minicalendar and preview area,
        # bug 4273.  On Mac, the preview area and the minicalendar
        # don't have their own borders, so also draw the line.
        self.lineAboveToday = not '__WXMSW__' in wx.PlatformInfo

        self.Bind(minical.EVT_MINI_CALENDAR_SEL_CHANGED,
                  self.OnWXSelectItem)
        self.Bind(minical.EVT_MINI_CALENDAR_DOUBLECLICKED,
                  self.OnWXDoubleClick)
        self.Bind(minical.EVT_MINI_CALENDAR_UPDATE_BUSY,
                  self.setFreeBusy)
        self.Bind(wx.EVT_PAINT, self.OnPaint)


    def wxSynchronizeWidget(self, useHints=False):
        style = PLATFORM_BORDER
        if isMainCalendarVisible() and not self.blockItem.dayMode:
            style |= minical.CAL_HIGHLIGHT_WEEK
        self.SetWindowStyle(style)
        self.setFreeBusy(None, useHints)

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
        date = datetime.combine(self.GetDate(), time(tzinfo = ICUtzinfo.floating))
        return date

    def setFreeBusy(self, event, useHints=False):

        if self._recalcCount == 0:
            zerotime = time(tzinfo=ICUtzinfo.default)
            start = self.GetStartDate()
            start = datetime.combine(start, zerotime)

            # ugh, why can't timedelta just support months?
            end = minical.MonthDelta(start, 3)
            end = datetime.combine(end, zerotime)

            if useHints and self.HavePendingNewEvents():
                addedEvents = self.GetPendingNewEvents((start, end), expandRecurrence=False)

                # self._eventsToAdd is a set to deal with cases where
                # multiple notifications are received for a given
                # event.
                if self._eventsToAdd is None: self._eventsToAdd = set()

                # Include confirmed events only
                self._eventsToAdd.update(event for event in addedEvents if
                                         not isDead(event.itsItem) and 
                                         event.transparency == 'confirmed')
            else:
                self._eventsToAdd = None

        if self._eventsToAdd is None:
            self._recalcCount += 1

        if self._recalcCount or self._eventsToAdd:
            self.Refresh()

    def OnPaint(self, event):
        self._checkRedraw()
        event.Skip(True)

    def _checkRedraw(self):
        if self._recalcCount > 0 or self._eventsToAdd is not None:
            self._recalcCount = 0
            self._doDrawing()
            self._eventsToAdd = None

    def _doDrawing(self):

        startDate = self.GetStartDate()

        endDate = minical.MonthDelta(startDate, 3)

        numDays = (endDate - startDate).days
        busyFractions = {}
        defaultTzinfo = ICUtzinfo.default

        tzEnabled = schema.ns('osaf.pim',
                              self.blockItem.itsView).TimezonePrefs.showUI

        # The exact algorithm for the busy state is yet to be determined.
        # For now, just  get the confirmed items on a given day and calculate
        # their total duration.  As long as there is at least one event the
        # busy bar should be at least 1/4 height (so that it is visible).
        # A 100% full day is assumed to be 12 hours worth of appointments.

        def updateBusy(event, start):
            # Broken out into a separate function because we're going
            # to call it for each non-recurring events, and for each
            # individual occurrence of all the recurring events.
            # In the case of the latter, event may be the master, or
            # a modification; we're trying to avoid creating all the
            # items for individual computed occurrences.
            if (event.transparency == "confirmed" and
                (event.allDay or
                (not event.anyTime and event.duration != zero_delta))):

                assert(start.tzinfo is not None)

                # If timezones are enabled, we need to convert to the
                # default tzinfo here, so that date() below refers to
                # the correct timezone.
                if tzEnabled:
                    start = start.astimezone(defaultTzinfo)

                offset = (start.date() - startDate).days

                midnightStart = datetime.combine(event.startTime.date(),
                                                 time(0, tzinfo=defaultTzinfo))
                if event.allDay:
                    days = event.duration.days + 1
                else:
                    days = (event.endTime - midnightStart).days + 1

                for day in xrange(days):
                    if event.allDay:
                        hours = 12.0
                    elif event.anyTime:
                        hours = 1.0
                    else:
                        dayStart = max(event.startTime,
                                       midnightStart + timedelta(day))
                        dayEnd   = min(event.endTime,
                                       midnightStart + timedelta(day + 1))
                        duration = dayEnd - dayStart
                        # @@@ Wrong for multiday events -- Grant
                        hours = duration.seconds / (60 * 60) + 24*duration.days

                    # We set a minimum "Busy" value of 0.25 for any
                    # day with a confirmed event.
                    fraction = busyFractions.get(offset + day, 0.0)
                    fraction = max(fraction, 0.25)
                    fraction += (hours / 12.0)

                    busyFractions[offset + day] = min(fraction, 1.0)

        if self._eventsToAdd is not None:
            # First, set up busyFractions to contain the
            # existing values for all the dates of events
            # we're about to add
            for newEvent in self._eventsToAdd:
                offset = (newEvent.startTime.date() - startDate).days

                busyFractions[offset] = self.GetBusy(newEvent.startTime.date())

            # Now, update them all
            for newEvent in self._eventsToAdd:
                updateBusy(newEvent, newEvent.startTime)

            # Finally, update the UI
            for offset, busy in busyFractions.iteritems():
                eventDate = startDate + timedelta(days=offset)
                self.SetBusy(eventDate, busy)

        else:

            # Largely, this code is stolen from CalendarCanvas.py; it
            # would be good to refactor it at some point.
            self.blockItem.EnsureIndexes()

            startOfDay = time(0, tzinfo=ICUtzinfo.default)
            startDatetime = datetime.combine(startDate, startOfDay)
            endDatetime = datetime.combine(endDate, startOfDay)

            events = self.blockItem.contents
            view = self.blockItem.itsView

            for event, start in Calendar.iterBusyInfo(view, startDatetime,
                                                       endDatetime, events):                                                
                updateBusy(event, start)

            # Next, try to find all generated events in the given
            # datetime range

            offset = 0
            while (startDate < endDate):
                self.SetBusy(startDate, busyFractions.get(offset, 0.0))
                startDate += one_day
                offset += 1


def isMainCalendarVisible():
    # Heuristic: is the appbar calendar button selected (depressed)?
    calendarButton = Block.Block.findBlockByName("ApplicationBarEventButton")
    try:
        return calendarButton.selected
    except AttributeError:
        # Toolbar isn't rendered yet
        return False


class MiniCalendar(CalendarCanvas.CalendarBlock):
    dayMode = schema.One(schema.Boolean, initialValue = True)

    previewArea = schema.One(
        defaultValue = None
    )
    
    schema.addClouds(
        copying = schema.Cloud (byCloud = [previewArea])
    )

    def AdjustSplit(self, splitterWindow, windowSize, position):
        widget = getattr (self, 'widget', None)
        if widget is not None:
            if splitterWindow.GetSplitMode() == wx.SPLIT_HORIZONTAL:
                height = windowSize - position
                headerHeight = widget.GetHeaderSize().height
                previewWidget = self.previewArea.widget
                previewHeight = previewWidget.GetSize()[1]
                monthHeight = widget.GetMonthSize().height
    
                newHeight = previewHeight
                numMonths = 0
                while (newHeight + 0.5 * monthHeight < height and
                       numMonths < 3 and
                       newHeight + monthHeight < windowSize):
                    if numMonths == 0:
                        newHeight += headerHeight
                    newHeight += monthHeight
                    numMonths += 1
                height = newHeight
                position = windowSize - height
            else:
                idealWidth, idealHeight = widget.CalcGeometry()
                if abs (idealWidth - position) < 25:
                    position = idealWidth
                else:
                    minimum = idealWidth / 2;
                    if position < minimum:
                        position = idealWidth / 2
                
        return position

    def render(self, *args, **kwds):
        super(MiniCalendar, self).render(*args, **kwds)

        tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        self.itsView.watchItem(self, tzPrefs, 'onTZPrefsChange')

    def onDestroyWidget(self, *args, **kwds):

        tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        self.itsView.unwatchItem(self, tzPrefs, 'onTZPrefsChange')

        super(MiniCalendar, self).onDestroyWidget(*args, **kwds)

    def onTZPrefsChange(self, op, item, names):
        self.widget.wxSynchronizeWidget()

    def instantiateWidget(self):
        return wxMiniCalendar(self.parentBlock.widget,
                              self.getWidgetID(), style=PLATFORM_BORDER)

    def onSelectedDateChangedEvent(self, event):
        self.widget.SetDate(event.arguments['start'].date())
        self.widget.Refresh()

    def onDayModeEvent(self, event):
        self.dayMode = event.arguments['dayMode']
        self.synchronizeWidget()
        self.widget.Refresh()

    def onSelectItemsEvent(self, event):
        self.synchronizeWidget()
        self.widget.Refresh()

    def onSetContentsEvent(self, event):
        #We want to ignore, because view changes could come in here, and we
        #never want to change our collection
        pass

class PreviewPrefs(Preferences):
    maximumEventsDisplayed = schema.One(schema.Integer, initialValue=5)

class PreviewArea(CalendarCanvas.CalendarBlock):
    timeCharacterStyle = schema.One(Styles.CharacterStyle)
    eventCharacterStyle = schema.One(Styles.CharacterStyle)
    linkCharacterStyle = schema.One(Styles.CharacterStyle)

    miniCalendar = schema.One(
        inverse = MiniCalendar.previewArea,
        defaultValue = None
    )

    schema.addClouds(
        copying = schema.Cloud (
            byRef = [timeCharacterStyle, eventCharacterStyle, linkCharacterStyle],
            byCloud = [miniCalendar])
    )

    schema.initialValues(
        rangeIncrement = lambda self: one_day
    )

    def onSelectItemsEvent(self, event):
        self.synchronizeWidget()
        #self.widget.Refresh()

    def onSetContentsEvent(self, event):
        #We want to ignore, because view changes could come in here, and we
        #never want to change our collection
        pass

    def onSelectAllEventUpdateUI(self, event):
        event.arguments['Enable'] = False

    def instantiateWidget(self):
        if not self.getHasBeenRendered():
            self.setRange( datetime.now().date() )
            self.setHasBeenRendered()
        if '__WXMAC__' in wx.PlatformInfo:
            # on the Mac, borders around the minical and preview area look weird,
            # but we want one around our parent.  Modifying our parent is quite
            # a hack, but it works rather nicely.
            self.parentBlock.widget.SetWindowStyle(wx.BORDER_SIMPLE)
        return wxPreviewArea(self.parentBlock.widget,
                             self.getWidgetID(),
                             timeCharStyle = self.timeCharacterStyle,
                             eventCharStyle = self.eventCharacterStyle,
                             linkCharStyle = self.linkCharacterStyle)


class wxPreviewArea(CalendarCanvas.CalendarNotificationHandler, wx.Panel):
    vMargin = 4 # space above & below text
    hMargin = 6 # space on sides
    midMargin = 6 # space between time & date

    def __init__(self, parent, id, timeCharStyle, eventCharStyle, linkCharStyle,
                 *arguments, **keywords):
        super(wxPreviewArea, self).__init__(parent, id, *arguments, **keywords)
        self.currentDaysItems = []
        self._avoidDrawing = False
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.SetWindowStyle(PLATFORM_BORDER)

        self.useToday = True
        self.maximized = False
        self.titleFont = Styles.getFont(timeCharStyle)

        self.timeFont = Styles.getFont(timeCharStyle)
        self.eventFont = Styles.getFont(eventCharStyle)
        self.linkFont = Styles.getFont(linkCharStyle)
        self.labelPosition = -1 # Note that we haven't measured things yet.

    def OnSize(self, event):

        # necessary when sidebar is resized
        if '__WXMAC__' not in wx.PlatformInfo:
            self.Refresh(False)

    def OnPaint(self, event):

        if not self._avoidDrawing:
            dc = wx.PaintDC(self)
            self.Draw(dc)

    def _getItem(self, event):
        """
        Return the appropriate item, None if there are no items, or -1 for the
        expand/contract line.
        
        """
        if len(self.currentDaysItems) == 0:
            return None
        maxEvents = schema.ns("osaf.framework.blocks.calendar",
                     self.blockItem.itsView).previewPrefs.maximumEventsDisplayed

        dayLength = len(self.currentDaysItems)

        pos = (event.GetPosition().y - self.vMargin) / self.lineHeight
        if self.useToday:
            pos -= 1
        if (dayLength > maxEvents and ((not self.maximized and
                                        pos == maxEvents - 1) or
                                       (self.maximized and pos == dayLength))):
            return -1
        else:
            pos = max(0, pos)
            pos = min(len(self.currentDaysItems) - 1, pos)
            return self.currentDaysItems[pos].itsItem

    def ExpandOrContract(self):
        self.maximized = not self.maximized
        self.Resize()

    def OnDClick(self, event):
        item = self._getItem(event)
        if item == -1:
            self.ExpandOrContract()
            return
        elif item is None:
            return        
        self._avoidDrawing = True
        # Select the calendar filter
        self.blockItem.postEventByName ('ApplicationBarEvent', {})

        goto = schema.ns('osaf.framework.blocks.calendar',
                         self.blockItem.itsView).GoToCalendarItem

        # Set the calendar to the clicked day
        self.blockItem.post(goto, {'item': item})

        self._avoidDrawing = False

    def OnClick(self, event):
        item = self._getItem(event)
        if item == -1:
            self.ExpandOrContract()
            return
        elif item is None:
            return
        sidebarBPB = Block.Block.findBlockByName("SidebarBranchPointBlock")
        sidebarBPB.childBlocks.first().postEventByName (
           'SelectItemsBroadcast', {'items':[item]}
            )
        self.Refresh()

    def Draw(self, dc):
        """
        Draw all the items, based on what's in self.currentDaysItems

        @return the height of all the text drawn
        """
        # Set up drawing & clipping

        unselectedColor = styles.cfg.get('preview', 'UnSelectedText')
        selectedColor =   styles.cfg.get('preview', 'SelectedText')

        unselectedBackground = styles.cfg.get('preview',
                                              'UnSelectedTextBackground')
        selectedBackground =   styles.cfg.get('preview',
                                              'SelectedTextBackground')

        dc.Clear()
        brush =  wx.Brush(unselectedBackground, wx.SOLID)
        dc.SetBackground(brush)
        dc.SetBrush(brush)
        dc.SetPen(wx.Pen(unselectedBackground))
        dc.DrawRectangle(*iter(self.GetRect()))


        dc.SetTextBackground( unselectedBackground )
        dc.SetTextForeground( unselectedColor )
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
            genericTime = pim.shortTimeFormat.format(datetime(2005,1,1,12,00))
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

        y = self.vMargin
        # Draw title if appropriate
        if self.useToday:
            todayText = _("Today's events")
            dc.SetFont(self.timeFont)
            dc.DrawText(todayText, self.hMargin, y)
            y += self.lineHeight

        # Draw each event
        previewPrefs = schema.ns("osaf.framework.blocks.calendar",
                                 self.blockItem.itsView).previewPrefs
        for i, event in enumerate(self.currentDaysItems):
            if isDead(event.itsItem):
                # This is to fix bug 4322, after removing recurrence,
                # OnPaint gets called before wxSynchronizeWidget, so
                # self.currentDaysItems has deleted items in it.
                continue

            if (not self.maximized and
                i == previewPrefs.maximumEventsDisplayed - 1 and
                len(self.currentDaysItems) - i > 1):
                break

            if not (event.allDay or event.anyTime):
                # Draw the time
                dc.SetFont(self.timeFont)
                formattedTime = pim.shortTimeFormat.format(event.startTime)
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
            dc.DrawText(event.summary, x, y + self.eventFontOffset)

            y += self.lineHeight

        if len(self.currentDaysItems) > previewPrefs.maximumEventsDisplayed:
            if self.maximized:
                expandText = _(u"- minimize")
            else:
                # this is the number of events that are not displayed
                # in the preview pane because there wasn't enough room
                numEventsLeft = (len(self.currentDaysItems) -
                                 (previewPrefs.maximumEventsDisplayed - 1))
                expandText = _(u"+ %(numberOfEvents)d more...") %  \
                                  {'numberOfEvents': numEventsLeft}

            dc.SetFont(self.linkFont)
            dc.DrawText(expandText, self.hMargin, y + self.eventFontOffset)
            y += self.lineHeight


        dc.DestroyClippingRegion()
        return y - self.vMargin

    def ChangeHeightAndAdjustContainers(self, newHeight):
        boxContainer = self.GetParent()
        for splitter in self.blockItem.miniCalendar.splitters:
            if splitter.orientationEnum == 'Horizontal':
                break
        wxSplitter = splitter.widget
        assert isinstance (wxSplitter, ContainerBlocks.wxSplitterWindow)

        currentHeight = self.GetSize()[1]
        heightDelta = currentHeight - newHeight

        #adjust box container shared with minical.
        self.SetMinSize( (0, newHeight) )
        boxContainer.Layout()

        #adjust splitter containing the box container
        wxSplitter.AdjustAndSetSashPosition (wxSplitter.GetSashPosition() + heightDelta)

    def Resize(self):
        dc = wx.ClientDC(self)
        drawnHeight = self.Draw(dc)

        if drawnHeight == 0:
            newHeight = 0
        else:
            newHeight = drawnHeight + 2*self.vMargin
        self.ChangeHeightAndAdjustContainers(newHeight)

    def wxSynchronizeWidget(self, useHints=False):
        # We now want the preview area to always appear.  If the
        # calendar is visible, however, we always want the preview
        # area to describe today, rather than the currently selected
        # day.
        minical = Block.Block.findBlockByName("MiniCalendar")
        if isMainCalendarVisible() or not minical:
            self.useToday = True
            today = datetime.today()
            startDay = datetime.combine(today, time(0))
        else:
            self.useToday = False
            startDay = minical.widget.getSelectedDate()
        startDay = startDay.replace(tzinfo=ICUtzinfo.default)
        endDay = startDay + one_day

        if useHints and self.HavePendingNewEvents():
            addedEvents = self.GetPendingNewEvents((startDay, endDay))

            addedEvents = set(item for item in addedEvents
                              if not isDead(item.itsItem) and 
                              item.transparency == 'confirmed')

            if len(addedEvents) == 0:
                return # No "interesting" new events
            for item in addedEvents:
                if item not in self.currentDaysItems:
                    self.currentDaysItems.append(item)
        else:
            inRange = self.blockItem.getEventsInRange((startDay, endDay),
                                              dayItems=True, timedItems=True)
            self.currentDaysItems = [event for event in inRange
                                       if event.transparency == "confirmed"]

        self.currentDaysItems.sort(cmp = self.SortForPreview)
        self.Resize()


    @staticmethod
    def SortForPreview(event1, event2):
        def bad(stamp_or_item):
            # reject items if they're dead OR if they've lost their EventStamp
            item = getattr(stamp_or_item, 'itsItem', stamp_or_item)
            return isDead(item) or not has_stamp(item, EventStamp)
        
        if bad(event1) or bad(event2):
            # sort stale or deleted items first, False < True
            return cmp(not bad(event1), not bad(event2))
        if (event1.anyTime or event1.allDay) and (event2.anyTime or event2.allDay):
            return cmp(event1.summary, event2.summary)
        if event1.anyTime or event1.allDay:
            return -1
        if event2.anyTime or event2.allDay:
            return 1
        return (cmp(event1.startTime, event2.startTime)
               or cmp(event1.duration, event2.duration)
               or cmp(event1.summary, event2.summary))
