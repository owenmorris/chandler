"""
Calendar Blocks
"""

__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx
import wx.calendar
import minical

from application import schema

from osaf.framework.blocks import (
    Block, Styles, DrawingUtilities, ContainerBlocks
    )

from osaf.framework import Preferences
import osaf.pim as pim
import CalendarCanvas
import osaf.pim.calendar.Calendar as Calendar
from datetime import datetime, date, time, timedelta
from PyICU import ICUtzinfo
from i18n import OSAFMessageFactory as _


class wxMiniCalendar(CalendarCanvas.CalendarNotificationHandler,
                     minical.PyMiniCalendar):

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


    def __init__(self, *arguments, **keywords):
        super (wxMiniCalendar, self).__init__(*arguments, **keywords)
        self.Bind(minical.EVT_MINI_CALENDAR_SEL_CHANGED,
                  self.OnWXSelectItem)
        self.Bind(minical.EVT_MINI_CALENDAR_DOUBLECLICKED, 
                  self.OnWXDoubleClick)
        self.Bind(minical.EVT_MINI_CALENDAR_UPDATE_BUSY,
                  self.setFreeBusy)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def wxSynchronizeWidget(self, useHints=False):
        if '__WXMAC__' in wx.PlatformInfo:
            style = wx.BORDER_SIMPLE
        else:
            style = wx.BORDER_STATIC
        
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
                addedEvents = self.GetPendingNewEvents((start, end))
                
                # self._eventsToAdd is a set to deal with cases where
                # multiple notifications are received for a given
                # event.
                if self._eventsToAdd is None: self._eventsToAdd = set()
                
                # Include confirmed events only
                self._eventsToAdd.update(item for item in addedEvents if
                                         item.transparency == 'confirmed')
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
        
        tzEnabled = schema.ns('osaf.app',
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
            if event.transparency == "confirmed":

                if event.allDay:
                    hours = 12.0
                else:
                    # @@@ Wrong for multiday events -- Grant
                    hours = event.duration.seconds / (60 * 60)

                assert(start.tzinfo is not None)
                
                # If timezones are enabled, we need to convert to the
                # default tzinfo here, so that date() below refers to
                # the correct timezone.
                if tzEnabled:
                    start = start.astimezone(defaultTzinfo)
            
                # @@@ [grant] Again, multiday events
                offset = (start.date() - startDate).days
                
                # We set a minimum "Busy" value of 0.25 for any
                # day with a confirmed event.
                fraction = busyFractions.get(offset, 0.0)
                fraction = max(fraction, 0.25)
                fraction += (hours / 12.0)
                
                busyFractions[offset] = min(fraction, 1.0)
                
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
            
            # First, look at all non-generated events
            startOfDay = time(0, tzinfo=ICUtzinfo.default)
            startDatetime = datetime.combine(startDate, startOfDay)
            endDatetime = datetime.combine(endDate, startOfDay)

            events = self.blockItem.contents
            view = self.blockItem.itsView            
            
            for item in Calendar.eventsInRange(view, startDatetime, endDatetime,
                                               events):                                                
                    updateBusy(item, item.startTime)
    
            # Next, try to find all generated events in the given
            # datetime range
            

           # The following iteration over keys comes from Calendar.py

            pimNs = schema.ns('osaf.pim', view)
            allEvents = pimNs.events
            masterEvents = pimNs.masterEvents

            tzprefs = schema.ns('osaf.app', view).TimezonePrefs
            if tzprefs.showUI:
                startIndex = 'effectiveStart'
                endIndex   = 'recurrenceEnd'
            else:
                startIndex = 'effectiveStartNoTZ'
                endIndex   = 'recurrenceEndNoTZ'
    
    
            keys = Calendar.getKeysInRange(view,
                    startDatetime, 'effectiveStartTime', startIndex, allEvents,
                    endDatetime, 'recurrenceEnd', endIndex, masterEvents,
                    events, '__adhoc__',
                    tzprefs.showUI)

    
            for key in keys:
                masterEvent = view[key]
                rruleset = masterEvent.createDateUtilFromRule()
                
                # If timezones have been disabled in the UI, we want to
                # use the event's timezone for comparisons, since that
                # timezone determines what date each occurrence occurs on.
                tzinfo = masterEvent.effectiveStartTime.tzinfo
                if not tzEnabled:
                    startDatetime = startDatetime.replace(tzinfo=tzinfo)
                    endDatetime = endDatetime.replace(tzinfo=tzinfo)
                
                modifications = list(masterEvent.modifications or [])
                
                for recurDatetime in rruleset.between(startDatetime, endDatetime,
                                                      True):
                    # Now see if recurDatetime matches any of our modifications
                    matchingMod = None
                    
                    for mod in modifications:
                        if recurDatetime == mod.recurrenceID:
                            matchingMod = mod
                            break
                            
                    
                    if matchingMod is None:
                        # OK, an unmodified occurrence. Just
                        # go ahead and update
                        updateBusy(masterEvent, recurDatetime)
                    else:
                        # Aha, we found a matching modification. We
                        # need to make sure it still falls inside the
                        # range of datetimes we're interested in.
                        modStart = matchingMod.startTime
                        
                        # To do the comparison, we need to make sure
                        # the naivetes of modStart, startDatetime and
                        # endDatetime all match.
                        if modStart.tzinfo is None:
                            modStart = modStart.replace(tzinfo=tzinfo)
                        else:
                            modStart = modStart.astimezone(tzinfo)
                            
                        if (modStart >= startDatetime and
                            modStart <= endDatetime):
                            
                            updateBusy(matchingMod, modStart)
    
            offset = 0
            timeDeltaDay = timedelta(days=1)
            while (startDate < endDate):
                self.SetBusy(startDate, busyFractions.get(offset, 0.0))
                startDate += timeDeltaDay
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
    dayMode = schema.One(schema.Boolean, initialValue = True)

    def render(self, *args, **kwds):
        super(MiniCalendar, self).render(*args, **kwds)

        tzPrefs = schema.ns('osaf.app', self.itsView).TimezonePrefs
        self.itsView.watchItem(self, tzPrefs, 'onTZPrefsChange')

    def onDestroyWidget(self, *args, **kwds):

        tzPrefs = schema.ns('osaf.app', self.itsView).TimezonePrefs
        self.itsView.unwatchItem(self, tzPrefs, 'onTZPrefsChange')

        super(MiniCalendar, self).onDestroyWidget(*args, **kwds)

    def onTZPrefsChange(self, op, item, names):
        self.widget.wxSynchronizeWidget()

    def instantiateWidget(self):
        if '__WXMAC__' in wx.PlatformInfo:
            style = wx.BORDER_SIMPLE
        else:
            style = wx.BORDER_STATIC
        return wxMiniCalendar(self.parentBlock.widget,
                              self.getWidgetID(), style=style)

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

    def onSelectAllEventUpdateUI(self, event):
        event.arguments['Enable'] = False
    
    def instantiateWidget(self):
        if not self.getHasBeenRendered():
            self.setRange( datetime.now().date() )
            self.setHasBeenRendered()        
        return wxPreviewArea(self.parentBlock.widget, 
                             self.getWidgetID(),
                             timeCharStyle = self.timeCharacterStyle,
                             eventCharStyle = self.eventCharacterStyle)


class wxPreviewArea(CalendarCanvas.CalendarNotificationHandler, wx.Panel):
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
            
        # Draw each event            
        y = self.vMargin
        previewPrefs = schema.ns("osaf.framework.blocks.calendar",
                                 self.blockItem.itsView).previewPrefs
        for i, item in enumerate(self.currentDaysItems):
            if item.isDeleted():
                # This is to fix bug 4322, after removing recurrence,
                # OnPaint gets called before wxSynchronizeWidget, so
                # self.currentDaysItems has deleted items in it.
                continue
            if i == previewPrefs.maximumEventsDisplayed - 1:
                numEventsLeft = (len(self.currentDaysItems) - i)
                if numEventsLeft > 1:
                    dc.SetFont(self.eventFont)
                    # this is the number of events that are not displayed
                    # in the preview pane because there wasn't enough room
                    dc.DrawText(_(u"%(numberOfEvents)d more confirmed...") % {'numberOfEvents': numEventsLeft},
                                self.hMargin, y + self.eventFontOffset)
                    y += self.lineHeight  #For end calculation
                    break

            if not (item.allDay or item.anyTime):
                # Draw the time
                dc.SetFont(self.timeFont)
                formattedTime = pim.shortTimeFormat.format(item.startTime)
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
        
    def wxSynchronizeWidget(self, useHints=False):
        # We now want the preview area to always appear.  If the
        # calendar is visible, however, we always want the preview
        # area to describe today, rather than the currently selected
        # day.
        minical = Block.Block.findBlockByName("MiniCalendar")
        if isMainCalendarVisible() or not minical:
            today = datetime.today()
            startDay = datetime.combine(today, time(0))
        else:
            startDay = minical.widget.getSelectedDate()
        startDay = startDay.replace(tzinfo=ICUtzinfo.default)
        endDay = startDay + timedelta(days=1)

        if useHints and self.HavePendingNewEvents():
            addedEvents = self.GetPendingNewEvents((startDay, endDay))
            
            addedEvents = set(item for item in addedEvents
                                if item.transparency == 'confirmed')

            if len(addedEvents) == 0:
                return # No "interesting" new events
            for item in addedEvents:
                if item not in self.currentDaysItems:
                    self.currentDaysItems.append(item)
        else:
            inRange = self.blockItem.getItemsInRange((startDay, endDay), dayItems=True, timedItems=True)
            self.currentDaysItems = [item for item in inRange if item.transparency == "confirmed"]
        
        self.currentDaysItems.sort(cmp = self.SortForPreview)
        dc = wx.ClientDC(self)
        drawnHeight = self.Draw(dc)

        if drawnHeight == 0:
            newHeight = 0
        else:
            newHeight = drawnHeight + 2*self.vMargin
        self.ChangeHeightAndAdjustContainers(newHeight)


    @staticmethod
    def SortForPreview(item1, item2):
        if item1.isStale() or item2.isStale():
            # sort stale or deleted items first, False < True
            return cmp(not item1.isStale(), not item2.isStale())
        if (item1.anyTime or item1.allDay) and (item2.anyTime or item2.allDay):
            return cmp(item1.displayName, item2.displayName)
        if item1.anyTime or item1.allDay:
            return -1
        if item2.anyTime or item2.allDay:
            return 1
        return (cmp(item1.startTime, item2.startTime)
               or cmp(item1.duration, item2.duration)
               or cmp(item1.displayName, item2.displayName))

