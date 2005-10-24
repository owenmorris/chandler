"""
Canvas for calendaring blocks
"""

__copyright__ = "Copyright (c) 2004-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx
import wx.colheader

from repository.item.Monitors import Monitors

from datetime import datetime, timedelta, date, time
from PyICU import GregorianCalendar, DateFormatSymbols, ICUtzinfo

from osaf.pim.calendar import Calendar, TimeZoneInfo, formatTime
from osaf.pim import FilteredCollection, AbstractCollection
from application.dialogs import RecurrenceDialog

from osaf.framework.blocks import (
    DragAndDrop, Block, SplitterWindow, Styles,
    FocusEventHandlers, BoxContainer
    )
from osaf.framework.attributeEditors import AttributeEditors
from osaf.framework.blocks.calendar import CollectionCanvas

from osaf.framework.blocks.DrawingUtilities import DrawWrappedText, Gradients, color2rgb, rgb2color
from colorsys import rgb_to_hsv, hsv_to_rgb

from application import schema
from itertools import islice, chain
import copy
import logging

from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)

dateFormatSymbols = DateFormatSymbols()

TRANSPARENCY_DASHES = [255, 255, 0, 0, 255, 255, 0, 0]

def nth(iterable, n):
    return list(islice(iterable, n, n+1))[0]

# Widget overview
# 
# the composition of blocks is as follows
# CalendarContainer  is the Block for the entire summary view
# its children subblocks are as follows:
# 
# -------------------------------------------------------------
# | wxCalendarControl - block: CalendarControl                                       
# | [color selector]   <- June 2005 ->      [timezone] 
# |                                                           
# | also has the row of week/7-days buttons as an inset widget:
# |-------------------------------------------------------
# || wx.colheader.ColumnHeader  (instance name: weekColumnHeader)
# ||Week  Sun  Mon  Tue  Wed  Thu  Fri  +                     
# ||------------------------------------------------------
# |---------------------------------------------------------
# | SplitterWindow block, two children blocks
# | |---------------------------------------------------------
# | |wxAllDayEventsCanvas - block: AllDayEventsCanvas
# | | where the all-day events go
# | |---------------------------------------------------------
# | |wxTimedEventsCanvas - block: TimedEventsCanvas
# | | the main area that can have events at specific times
# | |
# | | [much bigger, not drawn to scale]
# | |
# | |-------------------------------------------------------
# -------------------------------------------------------------

def roundTo(v, r):
    """
    round down v to the nearest r
    """
    return (v/r)*r
    
class ColorInfo(object):
    def __init__(self, collection):
        assert hasattr (collection, 'color')
        color = collection.color
        self.hue = rgb_to_hsv(*color2rgb(color.red,color.green,color.blue))[0]
    
    # to be used like a property, i.e. prop = tintedColor(0.5, 1.0)
    # takes HSV 'S' and 'V' and returns an color based tuple property
    def tintedColor(saturation, value = 1.0):
        def getSaturatedColor(self):
            return rgb2color(*hsv_to_rgb(self.hue, saturation, value))
        return property(getSaturatedColor)
            
    def tupleProperty(*args):
        """
        untangle a tuple of property objects.
        
        If you try to just declare a tuple of attributes
        that are property objects, you end up with a tuple
        of property objects, rather than a tuple of evaluated
        property values
        """
        def demangledTupleGetter(self):
            return tuple([val.fget(self) for val in args])
        return property(demangledTupleGetter)
        
    # these are all for when this calendar is the 'current' one
    gradientLeft = tintedColor(0.4)
    gradientRight = tintedColor(0.2)
    outlineColor = tintedColor(0.5)
    textColor = tintedColor(0.67, 0.6)
    defaultColors = tupleProperty(gradientLeft, gradientRight, outlineColor, textColor)
    
    # when a user selects a calendar event, use these
    selectedGradientLeft = tintedColor(0.15)
    selectedGradientRight = tintedColor(0.05)
    selectedOutlineColor = tintedColor(0.5)
    selectedTextColor = tintedColor(0.67, 0.6)
    selectedColors = tupleProperty(selectedGradientLeft, selectedGradientRight, selectedOutlineColor, selectedTextColor)
    
    # 'visible' means that its not the 'current' calendar, but is still visible
    visibleGradientLeft = tintedColor(0.15)
    visibleGradientRight = tintedColor(0.15)
    visibleOutlineColor = tintedColor(0.3)
    visibleTextColor = tintedColor(0.4, 0.85)
    visibleColors = tupleProperty(visibleGradientLeft, visibleGradientRight, visibleOutlineColor, visibleTextColor)


class CalendarCollections(schema.Annotation):
    schema.kindInfo(annotates=AbstractCollection)
    masterEvents = schema.One(FilteredCollection)
        
class CalendarCanvasItem(CollectionCanvas.CanvasItem):
    """
    Base class for calendar items. Covers:
     - editor position & size
     - text wrapping
    """
    
    timeHeight = 0
    
    def __init__(self, collection, primaryCollection, bounds, item, *args, **keywords):
        super(CalendarCanvasItem, self).__init__(bounds, item, *args, **keywords)

        # this is supposed to be set in Draw(), but sometimes this
        # object seems to exist before Draw() is called
        self.textOffset = wx.Point(self.textMargin, self.textMargin)

        # use PyICU to pre-cache the time string
        self.timeString = formatTime(self._item.startTime)

        self.colorInfo = ColorInfo(collection)

        self.isActive = primaryCollection is collection
                        
    def GetEditorPosition(self):
        """
        This returns a location to show the editor. By default it is the same
        as the default bounding box
        """
        position = self.GetBoundsRects()[0].GetPosition() + self.textOffset
                  
        # now offset to account for the time	
        position += (0, self.timeHeight)
        return position	
                  
    def GetMaxEditorSize(self):	
        size = self.GetBoundsRects()[0].GetSize()	
       
        # now offset to account for the time	
        size -= (13, self.timeHeight + self.textMargin*2)	
        return size
        
    
    def GetStatusPen(self, color):
        # probably should use styles to determine a good pen color
        item = self.GetItem()

        if (item.transparency == "confirmed"):
            pen = wx.Pen(color, 4)
        elif (item.transparency == "fyi"):
            pen = wx.Pen(color, 1)
        elif (item.transparency == "tentative"):
            if '__WXMAC__' in wx.PlatformInfo:
                pen = wx.Pen(color, 4, wx.USER_DASH)
                pen.SetDashes(TRANSPARENCY_DASHES)
            else:
                pen = wx.Pen(color, 4, wx.DOT)

        return pen

    def getEventColors(self, selected):
        """
        returns the appropriate tuple of selected, normal, and visible colors
        """
        
        if selected:
            return self.colorInfo.selectedColors
        elif self.isActive:
            return self.colorInfo.defaultColors
        
        return self.colorInfo.visibleColors
    
    def GetAnyTimeOrAllDay(self):	
        item = self.GetItem()
        anyTime = getattr(item, 'anyTime', False)
        allDay = getattr(item, 'allDay', False)
       
        return anyTime or allDay
             
                
    @staticmethod
    def FindFirstGapInSequence(seq):
        """
        Look for the first gap in a sequence - for instance::
          0,2,3: choose 1
          1,2,3: choose 0
          0,1,2: choose 3        
        """
        if not seq: return 0
        
        for index, value in enumerate(seq):
            if index != value:
                return index
                
        # didn't find any gaps, so just put it one higher
        return index+1
        
    def CanDrag(self):
        item = self.GetItem()
        return (item.isAttributeModifiable('startTime') and
                item.isAttributeModifiable('duration'))

    def CanChangeTitle(self):
        item = self.GetItem()
        return item.isAttributeModifiable('displayName')
    
    def Draw(self, dc, styles, brushOffset, selected, rightSideCutOff=False):
        # @@@ add a general cutoff parameter?
        item = self._item
        if item.isDeleted():
            return

        isAnyTimeOrAllDay = self.GetAnyTimeOrAllDay()	
        # Draw one event - an event consists of one or more bounds	
       
        clipRect = None	
        (cx,cy,cwidth,cheight) = dc.GetClippingBox()	
        if not cwidth == cheight == 0:	
            clipRect = wx.Rect(cx,cy,cwidth,cheight)	
        
        gradientLeft, gradientRight, outlineColor, textColor = \
            self.getEventColors(selected)
       
        dc.SetTextForeground(textColor)
       
        for rectIndex, itemRect in enumerate(self.GetBoundsRects()):
       
            brush = styles.brushes.GetGradientBrush(itemRect.x + brushOffset,
                                                    itemRect.width,
                                                    gradientLeft, gradientRight)	
            dc.SetBrush(brush)	
            dc.SetPen(wx.Pen(outlineColor))	
       
            # properly round the corners - first and last	
            # boundsRect gets some rounding, and they	
            # may actually be the same boundsRect	
            hasTopRightRounded = hasBottomRightRounded = False	
            drawEventText = False	
            if rectIndex == 0:	
                hasTopRightRounded = True	
                drawEventText = True	
       
            if rectIndex == len(self.GetBoundsRects())-1:	
                hasBottomRightRounded = True	
       
            # zero-duration events get fully rounded
            isAllDay = getattr(item, 'allDay', False)
            hasLeftRounded = ((not isAllDay and
                               Calendar.datetimeOp(item.startTime, '==',
                                                   item.endTime)) or
                              getattr(item, 'anyTime', False))
            
            self.DrawEventRectangle(dc, itemRect,
                                    hasLeftRounded,
                                    hasTopRightRounded,
                                    hasBottomRightRounded,
                                    rightSideCutOff)
            
            # if the left side is rounded, we don't need a status bar
            if not hasLeftRounded: 
                pen = self.GetStatusPen(outlineColor)
                pen.SetCap(wx.CAP_BUTT)
                dc.SetPen(pen)
                dc.DrawLine(itemRect.x+1, itemRect.y,
                            itemRect.x+1, itemRect.y + itemRect.height)

 
            self.textOffset = wx.Point(self.textMargin, self.textMargin)
            
            if hasLeftRounded:
                cornerRadius = 8
                self.textOffset.x += cornerRadius
            else:
                self.textOffset.x += 3

            # Shift text to account for rounded corners
            x = itemRect.x + self.textOffset.x
            y = itemRect.y + self.textOffset.y

            width = itemRect.width - self.textOffset.x - (self.textMargin)
            
            # only draw date/time on first item	
            if drawEventText:
                # only draw time on timed events
                if not isAnyTimeOrAllDay:
                    
                    # allow self.startTime to override the
                    # pre-formatted time string
                    startTime = getattr(self, 'startTime', None)
                    if startTime:
                        timeString = formatTime(startTime)
                    else:
                        timeString = self.timeString
                        
                    te = dc.GetFullTextExtent(timeString, styles.eventTimeFont)	
                    timeHeight = te[1]	
       
                    # add some space below the time
                    # (but on linux there isn't any room)
                    if '__WXGTK__' in wx.PlatformInfo:
                        timeBottomMargin = 1
                    else:
                        timeBottomMargin = 3

                    # draw the time if there is room for the time and at least
                    # one other line of text
                    # we need to precalculate how much room we have left
                    availableSpace = timeHeight*2 + timeBottomMargin + \
                                     self.textOffset.y*2
                    if (availableSpace < itemRect.height):
                        timeRect = wx.Rect(x, y, width, timeHeight)
                        
                        dc.SetFont(styles.eventTimeFont)	
                        self.timeHeight = \
                            DrawWrappedText(dc, timeString, timeRect)

                        y += self.timeHeight

                        # divider line after the time
                        dc.SetPen(wx.Pen(outlineColor))
                        dc.DrawLine(itemRect.x, y + 1,
                                    itemRect.x + itemRect.width, y + 1)
                        
                        y += timeBottomMargin
                        
                    else:	
                        self.timeHeight = 0	

                # we may have lost some room in the rectangle from	
                # drawing the time	
                lostHeight = y - itemRect.y                        
       
                # now draw the text of the event	
                textRect = wx.Rect(x, y,	
                                   width,	
                                   itemRect.height - lostHeight - self.textOffset.y)
       
                dc.SetFont(styles.eventLabelFont)
                if selected:
                    proxy = RecurrenceDialog.getProxy(u'ui', item)
                    DrawWrappedText(dc, proxy.displayName, textRect)
                else:
                    DrawWrappedText(dc, item.displayName, textRect)
       
        dc.DestroyClippingRegion()	
        if clipRect:	
            dc.SetClippingRect(clipRect)	
       
    def DrawEventRectangle(self, dc, rect,
                           hasLeftRounded=False,
                           hasTopRightRounded=True,
                           hasBottomRightRounded=True,
                           clipRightSide=False):
        """
        Make a rounded rectangle, optionally specifying if the top and bottom
        right side of the rectangle should have rounded corners. Uses
        clip rect tricks to make sure it is drawn correctly
        
        Side effect: Destroys the clipping region.
        """

        # if your left side is rounded, then everything must be rounded
        assert ((hasLeftRounded and
                 hasTopRightRounded and hasBottomRightRounded) or
                not hasLeftRounded)
        
        radius = 8
        diameter = radius * 2

        dc.DestroyClippingRegion()
        dc.SetClippingRect(rect)
        
        roundRect = wx.Rect(*rect)

        # left/right clipping
        if not hasLeftRounded:
            roundRect.x -= radius
            roundRect.width += radius

        if clipRightSide:
            roundRect.width += radius;
            
        # top/bottom clipping
        if not hasBottomRightRounded:
            roundRect.height += radius

        if not hasTopRightRounded:
            roundRect.y -= radius
            roundRect.height += radius

        # finally draw the clipped rounded rect
        dc.DrawRoundedRectangleRect(roundRect, radius)
        
        # draw the lefthand and possibly top & bottom borders
        (x,y,width,height) = rect
        if not hasLeftRounded:
            # vertical line down left side
            dc.DrawLine(x, y,  x, y + height)
        if not hasBottomRightRounded:
            # horizontal line across the bottom
            dc.DrawLine(x, y + height-1,  x + width, y + height-1)
        if not hasTopRightRounded:
            # horizontal line across the top
            dc.DrawLine(x, y, x+width, y)



class CalendarEventHandler(object):
    """
    Mixin to a widget class.
    
    ASSUMPTION: its blockItem is a CalendarBlock
    """

    def OnPrev(self, event):
        blockItem = self.blockItem
        blockItem.decrementRange()
        blockItem.postDateChanged()
        blockItem.synchronizeWidget()

    def OnNext(self, event):
        blockItem = self.blockItem
        blockItem.incrementRange()
        blockItem.postDateChanged()
        blockItem.synchronizeWidget()

    def OnToday(self, event):
        blockItem = self.blockItem
        today = CalendarBlock.startOfToday()
        
        blockItem.setRange(today)
        blockItem.postDateChanged()
        blockItem.synchronizeWidget()
        
    def OnTZChoice(self, event):
        control = event.GetEventObject()
        choiceIndex = control.GetSelection()
        if choiceIndex != -1:
            newTZ = control.GetClientData(choiceIndex)

            view = self.blockItem.itsView
            TimeZoneInfo.get(view=view).default = newTZ
            view.commit()
            
            self.blockItem.postEventByName("TimeZoneChange",
                                            {'tzinfo':newTZ})


class CalendarBlock(FocusEventHandlers, CollectionCanvas.CollectionBlock):
    """
    Abstract block used as base Kind for Calendar related blocks.

    This base class can be used for any block that displays a collection of
    items based on a date range.

    Its date range may change, but the collection of items
    may contain items that don't fall into the currently viewed range.

    !@@@ move documentation out of docstrings to schema api .. it supports that right?
    
    @ivar rangeStart: beginning of the currently displayed range (persistent)
    @type rangeStart: datetime
    @ivar rangeIncrement: increment used to find the next or prev block of time
    @type rangeIncrement: timedelta

    @ivar selectedDate: within the current range. REFACTOR: why is this in
                        this class? tons of the pre-refactor code used this
                        variable though it was only declared in the subclass. 
                        The rule is now: selectedDate = rangeStart for basic
                        behavior, but selectedDate can range within the date 
                        range, e.g. when on a week view and you want to have 
                        a specific selected date inside that. 
                        TODO: get rid of switches testing for its existence

    @type selectedDate: datetime
    """
    # @@@ method capitalization policy is inconsistent!
    

    rangeStart = schema.One(schema.DateTime)
    rangeIncrement = schema.One(schema.TimeDelta)
    selectedDate = schema.One(schema.DateTime)
    lastHue = schema.One(schema.Float, initialValue = -1.0)
    dayMode = schema.One(schema.Boolean)
    calendarContainer = schema.One(schema.Item, required=True)

    def getRangeEnd(self):	
        return self.rangeStart + self.rangeIncrement	
    rangeEnd = property(getRangeEnd)

    def __init__(self, *arguments, **keywords):
        super(CalendarBlock, self).__init__(*arguments, **keywords)

        self.rangeIncrement = timedelta(days=7)
        self.dayMode = False
        self.setRange(self.startOfToday())

    def render(self, *args, **kwds):
        super(CalendarBlock, self).render(*args, **kwds)
        Monitors.attach(self, 'onColorChanged', 'set', 'color')

    def onDestroyWidget(self, *args, **kwds):
        Monitors.detach(self, 'onColorChanged', 'set', 'color')
        super(CalendarBlock, self).onDestroyWidget(*args, **kwds)
        
    #This is interesting. By Bug 3415 we want to reset the cal block's current
    #date to today at each chandler startup. CPIA has no general mechanism for
    #this, it assumes you want to persist everything. But we need CPIA
    #persistence because these blocks get render/unrender()'d all the time. So
    #we sign up for full repo persistence, but have to break it once per
    #session.

    #We do this by checking a class variable inside instantiateWidget()
    #(3-line boilerplate). We know the variable will be initialized only once
    #at chandler startup (module import time), so we then set it to True
    #thereafter.
    
    #Additional complication: we want each calendar block subclass to keep
    #track of whether it's been rendered or not -- as opposed to keeping track
    #of whether and cal block has been rendered. Therefore, in a subclass, ONLY
    #view and manipulate using the methods!
    
    # Envisioned usage is that a class gets instantiated/rendered multiple
    # times, but only one instance at one time.

    _beenRendered = False
    @classmethod
    def setHasBeenRendered(cls):
        """
        This says, this class has been rendered during this session
        """
        cls._beenRendered = True
    @classmethod
    def getHasBeenRendered(cls):
        """
        Has this class been rendered during this session?
        """
        return cls._beenRendered
    
    @staticmethod
    def startOfToday():
        today = date.today()
        start = time(tzinfo=ICUtzinfo.getDefault())
        return datetime.combine(today, start)
        
        
    def instantiateWidget(self):
        if not self.getHasBeenRendered():
            self.setRange( datetime.now().date() )
            self.setHasBeenRendered()

    # Event handling

    def onTimeZoneChangeEvent(self, event):
        self.synchronizeWidget()

    def onColorChanged(self, op, item, attribute):
        try:
            collections = self.contents.collectionList
            widget = self.widget
        except AttributeError, e:
            # sometimes self.contents hasn't been set yet,
            # or the widget hasn't been rendered yet
            return

        if item in collections:
            widget.Refresh()

    def EnsureIndexes(self):
        events = self.contents.rep
        # make sure there are indexes. 'compare' indexes use methods
        # on the items being compared, i.e. CalendarEventMixin
        if not events.hasIndex('startTime'):
            events.addIndex('startTime', 'compare', compare='cmpStartTime',
                            monitor=('startTime'))
        
        if not events.hasIndex('endTime'):
            # endTime is actually dependent on startTime/duration
            events.addIndex('endTime', 'compare', compare='cmpEndTime',
                            monitor=('startTime', 'duration'))

        # and make sure there is a FilteredCollection for
        # master events

        calendarCollections = CalendarCollections(self.contents)
        if getattr(calendarCollections, 'masterEvents', None) is None:
            masterEvents = FilteredCollection(parent=self.contents)
            masterEvents.filterExpression = "getattr(item, 'occurrences', None) is not None and getattr(item, 'rruleset', None) is not None"
            masterEvents.filterAttributes = ['occurrences', 'rruleset']
            masterEvents.source = self.contents
            masterEvents.rep.addIndex('__adhoc__', 'numeric')
            calendarCollections.masterEvents = masterEvents

    def setContentsOnBlock(self, item):
        super(CalendarBlock, self).setContentsOnBlock(item)

        self.EnsureIndexes()

    def onSelectWeekEvent(self, event):
        self.dayMode = not event.arguments['doSelectWeek']
        if self.dayMode:
            self.rangeIncrement = timedelta(days=1)
        else:
            self.rangeIncrement = timedelta(days=7)
        self.synchronizeWidget()


    def onSelectedDateChangedEvent(self, event):
        """
        Sets the selected date range and synchronizes the widget.

        @param event: event sent on selected date changed event
        @type event: osaf.framework.blocks.Block.BlockEvent
        @param event.arguments['start']: start of the newly selected date range
        @type event.arguments['start']: datetime
        """
        self.setRange(event.arguments['start'])
        self.synchronizeWidget()

    def postDateChanged(self, newdate=None):
        """
        Convenience method for changing the selected date.
        """
        if not newdate:
            try:
                newdate = self.selectedDate
            except AttributeError:
                raise Exception, "REFACTOR type error in old CalendarBlock code, discovered during refactoring, still need to fix!"

        self.postEventByName ('SelectedDateChanged',{'start':newdate})

    def postSelectWeek(self, doSelectWeek):
        """
        Convenience method for changing between day and week mode.
        """
        self.postEventByName ('SelectWeek', {'doSelectWeek':doSelectWeek})

    # Managing the date range

    def setRange(self, date):
        """
        REFACTOR: what this was supposed to do is
        "Sets the range to include the given date"
        but the old code didn't do that, and that's somewhat nontrivial: for a
        big rangeIncrement, what's rangeStart supposed to be? 

        this code's basic behavior works for the main cal canvases.  special case for week view.

        @param date: date to include
        @type date: datetime
        """

        date = datetime.combine(date, time())

        # basic behavior
        self.rangeStart = date
        self.selectedDate = self.rangeStart

        #the canvas CalendarBlocks of the main cal UI can switch between day and week modes.
        #when on week mode, have to figure out which week to select
        #the following dayMode-switchable behavior could be subclassed out
        if hasattr(self, 'dayMode') and not self.dayMode:
            calendar = GregorianCalendar()
            calendar.setTime(date)
            delta = timedelta(days=(calendar.get(calendar.DAY_OF_WEEK) -
                                    calendar.getFirstDayOfWeek()))
            self.rangeStart = date - delta
            self.selectedDate = date


    def incrementRange(self):
        """
        Increments the calendar's current range
        """
        self.rangeStart += self.rangeIncrement
        if self.selectedDate:
            self.selectedDate += self.rangeIncrement

    def decrementRange(self):
        """
        Decrements the calendar's current range
        """
        self.rangeStart -= self.rangeIncrement
        if self.selectedDate:
            self.selectedDate -= self.rangeIncrement


    @staticmethod
    def isDayItem(item):
        
        anyTime = False
        try:
            anyTime = item.anyTime
        except AttributeError:
            pass
        
        allDay = False
        try:
            allDay = item.allDay
        except AttributeError:
            pass

        return allDay or anyTime

        
    # Get items from the collection
    
    def itemIsInRange(self, item, start, end):
        """
        Helpful utility to determine if an item is within a given range
        Assumes the item has a startTime and endTime attribute
        """
        return (Calendar.datetimeOp(item.startTime, '<=', end) and
                Calendar.datetimeOp(item.endTime, '>=', start))

    def eventsInRange(self, date, nextDate, dayItems, timedItems):
        """
        An efficient generator to find all the items to be displayed
        between date and nextDate. This returns only actual events in the
        collection, and does not take recurring event occurences into
        account. (though any recurrence masters will of course be
        included in the result)

        The trick here is to use indexes on startTime/endTime to make
        sure that we don't access (and thus load) items more than we
        have to.

        We're looking for the intersection of:
        [All items that end after date] and
        [All items that start after nextDate]

        We find these subsets by looking for the first/last occurrence
        in the index of the end/starttime, and taking the first/last
        items from that list. This gives us two lists, which we intersect.
        """
        
        events = self.contents.rep
        view = self.itsView

        # callbacks to use for searching the indexes
        def mStart(key):
            # gets the last event starting before nextDate
            if Calendar.datetimeOp(nextDate, '>=', view[key].startTime):
                return 0
            return -1

        def mEnd(key):
            # gets the first event ending after date
            if Calendar.datetimeOp(date, '<=', view[key].endTime):
                return 0
            return 1

        assert events.hasIndex('startTime') and events.hasIndex('endTime')
        
        # do binary searches of the index to minimize the number of
        # times we test startTime/endTime
        lastStartKey = events.findInIndex('startTime', 'last', mStart)
        firstEndKey = events.findInIndex('endTime', 'first', mEnd)

        # we now have two lists of events:
        # [0..lastStartKey] in the 'startTime' index
        # [firstEndKey.. -1] in the 'endTime' index
        # lets find the intersections, based purely on UUID

        # we'll use the keys, which are UUIDs, to find the intersection, 
        # which prevents the actual item from loading
        if lastStartKey and firstEndKey:
            endItems = set(events.iterindexkeys('endTime',
                                                firstEndKey, None))
            for key in events.iterindexkeys('startTime',
                                            None, lastStartKey):
                # possible optimization, to also index allDay/anyTime
                # attributes as well
                if (key in endItems and
                    ((dayItems and timedItems) or
                     self.isDayItem(view[key]) == dayItems) and
                     view[key].rruleset is None):
                    yield view[key]

    def recurringEventsInRange(self, date, nextDate, dayItems, timedItems):
        masterEvents = CalendarCollections(self.contents).masterEvents
        for masterEvent in masterEvents:
            for event in masterEvent.getOccurrencesBetween(date, nextDate):
                # One or both of dayItems and timedItems must be
                # True. If both, then there's no need to test the
                # item's day-ness.  If only one is True, then
                # dayItems' value must match the return of
                # isDayItem.
                if ((event.occurrenceFor is not None) and
                    ((dayItems and timedItems) or
                     self.isDayItem(event) == dayItems)):
                        yield event

        
    def generateItemsInRange(self, date, nextDate, dayItems, timedItems):
        # wish we could put this somewhere more useful, but
        # self.contents can be set upon object initialization
        self.EnsureIndexes()

        normalEvents = self.eventsInRange(date, nextDate, dayItems, timedItems)
        recurringEvents = self.recurringEventsInRange(date, nextDate, dayItems, timedItems)
        return chain(normalEvents, recurringEvents)

    def getItemsInRange(self, (date, nextDate), dayItems=False, timedItems=False):
        """
        Convenience method to look for the items in the block's contents
        that appear on the given date. We might be able to push this
        to Queries, but itemIsInRange is actually fairly complex.
        
        @type date: datetime
        @type nextDate: datetime
        
        @param dayItems: return day items (items that have no start time)
        @param timedItems: return timed items
        
        @return: the items in this collection that appear within the given range
        @rtype: generator of Items
        """
        assert dayItems or timedItems, "dayItems or timedItems must be True"
        defaultTzinfo = ICUtzinfo.getDefault()
        if date.tzinfo is None:
            date = date.replace(tzinfo=defaultTzinfo)
        else:
            date = date.astimezone(defaultTzinfo)

        if nextDate.tzinfo is None:
            nextDate = nextDate.replace(tzinfo=defaultTzinfo)
        else:
            nextDate = nextDate.astimezone(defaultTzinfo)

        for item in self.generateItemsInRange(date, nextDate, dayItems, timedItems):
            if (hasattr(item, 'startTime') and hasattr(item, 'duration')):
                assert self.itemIsInRange(item, date, nextDate), \
                    "generateItemsInRange returned an item outside the range."
                yield item

    def getItemsInCurrentRange(self, *arguments, **keywords):
        currentRange = self.GetCurrentDateRange()
        return self.getItemsInRange(currentRange, *arguments, **keywords)


    def GetCurrentDateRange(self):
        return (self.rangeStart,  self.rangeStart + self.rangeIncrement)

    def getContainingCollection(self, event):
        """
        Get the collection which contains the event, since it has
        all the right color information.
        """

        # generated events need to defer to their parent event
        if event.occurrenceFor != event:
            event = event.getMaster()
            
        collections = self.contents.collectionList
        firstSpecialCollection = None
        for coll in collections:

            if (event in coll):
                if coll.outOfTheBoxCollection:
                    # save it for later, we might be returning it
                    firstSpecialCollection = coll
                else:
                    return coll
                    
        if firstSpecialCollection:
            return firstSpecialCollection

        # temporary check for M6
        # really, we should have gotten a wxSynchronizeWidget by now
        # so that if the event isn't in the above collections,
        # we shouldn't even be trying to draw it.
        trash = schema.ns('osaf.app', self.itsView).TrashCollection
        if event in trash:
            return trash

        assert False, "Don't have color info for %s" % event
        
    def setCurrentCalendarColor(self, color):

        # collectionList[0] is the currently selected collection
        self.contents.collectionList[0].color = ColorType(*color)


class wxCalendarCanvas(CollectionCanvas.wxCollectionCanvas):
    """
    Base class for all calendar canvases - handles basic item selection, 
    date ranges, and so forth

    ASSUMPTION: blockItem is a CalendarBlock
    """
    legendBorderWidth = 3
    def __init__(self, *arguments, **keywords):
        super (wxCalendarCanvas, self).__init__ (*arguments, **keywords)

        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        
    def OnInit(self):
        super(wxCalendarCanvas, self).OnInit()
        self.editor = wxInPlaceEditor(self, defocusCallback=self.SetPanelFocus)
        
    def OnScroll(self, event):
        self.Refresh()
        event.Skip()

    def OnSelectItem(self, item):
        super(wxCalendarCanvas, self).OnSelectItem(item)
        # tell the sidebar to select the collection that contains
        # this event - makes the sidebar track the "current" calendar
        # as well as update the gradients correctly
        if item is not None:
            collection = self.blockItem.getContainingCollection(item)
            if (collection is not None and
                collection != self.blockItem.contents.collectionList[0]):
                self.blockItem.SelectCollectionInSidebar(collection)


    def OnEditItem(self, box):
        if not box.CanChangeTitle():
            return
        
        styles = self.blockItem.calendarContainer
        position = self.CalcScrolledPosition(box.GetEditorPosition())
        size = box.GetMaxEditorSize()

        self.editor.SetItem(box.GetItem(), position, size, styles.eventLabelFont.GetPointSize())

    def GrabFocusHack(self):
        if self.editor.IsShown():
            self.editor.SaveAndHide()

    def RefreshCanvasItems(self, resort=False):
        self.RebuildCanvasItems(resort)
        self.Refresh()
        
    def GetCurrentDateRange(self):
        return self.blockItem.GetCurrentDateRange()

    def GetPlatformBrushOffset(self):
        """
        On Mac, the brushes are relative to the toplevel window. We have
        to walk up the parent window chain to find our offset within the parent
        window.

        Other platforms, the brush is offset from the current window.
        """
        if '__WXMAC__' in wx.PlatformInfo:
            brushOffset = 0
            p = self
            while not p.IsTopLevel():
                brushOffset += p.GetPosition().x
                p = p.GetParent()
        else:
            brushOffset = 0

        return brushOffset

    def ShadeToday(self, dc):
        """
        shade the background of today, if today is in view
        """

        # first make sure today is in view
        today = datetime.today()
        startDay, endDay = self.blockItem.GetCurrentDateRange()
        if (today < startDay or endDay < today):
            return

        styles = self.blockItem.calendarContainer
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        # rectangle goes from top to bottom, but the 
        dayNum = Calendar.datetimeOp(today, '-', startDay).days
        x = drawInfo.dividerPositions[dayNum]
        y = 0
        (width, height) = (drawInfo.dividerPositions[dayNum+1]-x,
                           self.size.height)
        dc.SetBrush(styles.todayBrush)
        dc.DrawRectangle(x,y,width, height)

    def DrawDayLines(self, dc):
        """
        Draw lines between days
        """

        styles = self.blockItem.calendarContainer
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        # the legend border is major
        dc.SetPen(wx.Pen(styles.majorLineColor, self.legendBorderWidth))
        
        # thick pens with the line centered at x - 1. Offset the
        # legend border because we want the righthand side of the line
        # to be at x - 1
        legendBorderX = drawInfo.dividerPositions[0] - self.legendBorderWidth/2 - 1
        dc.DrawLine(legendBorderX, 0,
                    legendBorderX, self.size.height)
        
        def drawDayLine(dayNum):
            x = drawInfo.dividerPositions[dayNum]
            dc.DrawLine(x, 0,   x, self.size.height)

        # the rest are minor, 1 pixel wide
        dc.SetPen(styles.minorLinePen)
        for dayNum in range(1, drawInfo.columns):
            drawDayLine(dayNum)


    def CreateEmptyEvent(self, startTime, duration, allDay, anyTime):	
        """	
        shared routine to create an event, using the current view	
        also forces consumers to specify important fields	
        """	
        view = self.blockItem.itsView	
        event = Calendar.CalendarEvent(view=view, startTime=startTime, duration=duration)
        event.InitOutgoingAttributes()	
       
        # start time is "optional" - callers still must specify None	
        # to be explicit that they want the default time	
        if startTime is not None:
            event.startTime = startTime
        if duration is not None:
            event.duration = duration
            
        event.allDay = allDay	
        event.anyTime = anyTime
        
        # collectionList[0] is the currently selected collection
        self.blockItem.contents.collectionList[0].add (event)
        
        self.OnSelectItem(event)

        # Put the focus into the Detail View
        detailRoot = self.blockItem.findBlockByName("DetailRoot")
        if detailRoot:
            detailRoot.focus()

        self.blockItem.itsView.commit()
        return event	
        

    def getBoundedPosition(self, position, drawInfo, mustBeInBounds=True):
        # first make sure we're within the top left boundaries
        yPosition = max(position.y, 0)
        if mustBeInBounds:
            xPosition = max(position.x, drawInfo.xOffset)
        else:       
            xPosition = position.x

        # next make sure we're within the bottom right boundaries
        height = self.size.height - 1# was GetMinSize().GetWidth()???
            
        yPosition = min(yPosition, height)
        if mustBeInBounds:
            xPosition = min(xPosition, 
                            drawInfo.xOffset + drawInfo.dayWidth * drawInfo.columns - 1)
        return wx.Point(xPosition, yPosition)
        
    def getDateTimeFromPosition(self, position, tzinfo=None, mustBeInBounds=True):
        """
        calculate the date based on the x,y coordinates on the canvas
        
        @param mustBeInBounds: if true, restrict to dates the user
                               currently can see/scroll to.
        """

        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        position = \
            self.getBoundedPosition(position, drawInfo, mustBeInBounds)

        # @@@ fixes Bug#1831, but doesn't really address the root cause
        # (the window is drawn with (0,0) virtual size on mac)
        if drawInfo.dayWidth > 0:
            deltaDays = (position.x - drawInfo.xOffset) / drawInfo.dayWidth
        else:
            deltaDays = 0
            
        startDay = self.blockItem.rangeStart
        deltaDays = timedelta(days=deltaDays)
        deltaTime = self.getRelativeTimeFromPosition(drawInfo, position)
        newTime = startDay + deltaDays + deltaTime

        newTime = newTime.replace(tzinfo=ICUtzinfo.getDefault())
        if tzinfo:
            newTime = newTime.astimezone(tzinfo)
        return newTime

    def IsValidDragPosition(self, unscrolledPosition):
        # checking y-bounds conflicts with calls to ScrollIntoView()
        # not (0 < unscrolledPosition.y < self.size.height)):
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        if (not (drawInfo.xOffset < unscrolledPosition.x < self.size.width)):
            return False
        return super(wxCalendarCanvas, self).IsValidDragPosition(unscrolledPosition)
        
    # Methods for Drag and Drop and Cut and Paste
    def SelectedItems(self):
        return self.blockItem.selection

    def AddItems(self, itemList):
        source = self.blockItem.contents.collectionList[0]
        for item in itemList:	
            item.addToCollection(source)


class wxInPlaceEditor(AttributeEditors.wxEditText):
    def __init__(self, parent, defocusCallback=None, *arguments, **keywords):
        
        # Windows and Mac add an extra vertical scrollbar for TE_MULTILINE,
        # and GTK does not. Further, if GTK is not multiline, then the single
        # line mode looks really wonky with a huge cursor. The undocumented
        # flag TE_NO_VSCROLL solves the former problem but introduces another:
        # text does not scroll at all. On MSW, not only does the text not
        # scroll, but also what text does not fit in the editor window gets
        # truncated. (!)
        #
        # FIXME: eventually, this TextCtrl style should be (for all platforms,
        # pending fixes in wx):
        # style = wx.NO_BORDER | wx.TE_NO_VSCROLL | wx.TE_MULTILINE
        
        # For now, we will differentiate based on platform: 
        
        style = wx.NO_BORDER
        
        if   '__WXMAC__' in wx.PlatformInfo:
                # Mac behavior doesn't allow any scrolling
                style |= wx.TE_MULTILINE 
                style |= wx.TE_NO_VSCROLL 

        elif '__WXGTK__' in wx.PlatformInfo:
                # GTK behavior works well with the multiline
                style |= wx.TE_MULTILINE
                style |= wx.TE_NO_VSCROLL
                #style |= wx.TE_PROCESS_ENTER # this works but causes an assertion error

        else:
                # MSW behavior truncates titles that doesn't fit in
                # the event window.  TE_PROCESS_ENTER is supposedly
                # not needed when using TE_MULTILINE flag.  (in fact
                # raises assertion error), but it apparently *is*
                # needed to not allow newlines in the input field. (at
                # least in GTK.)
                style |= wx.TE_PROCESS_ENTER 
                                             

        super(wxInPlaceEditor, self).__init__(parent,
                                              -1, "", wx.DefaultPosition,
                                              (-1, -1),
                                              style=style,
                                              *arguments, **keywords)

        self.defocusCallback = defocusCallback
        self.item = None
        self._unfocusing = False
        self.Hide()

        #self.editor.Bind(wx.EVT_CHAR, self.OnChar)
        parent = self.GetParent()
        parent.Bind(wx.EVT_SIZE, self.OnSize)

    def SaveItem(self):
        if ((self.item != None) and (not self.IsBeingDeleted())):
            if self.item.displayName != self.GetValue():
                parentBlock = self.GetParent()
                proxy = RecurrenceDialog.getProxy(u'ui', self.item, cancelCallback=parentBlock.RefreshCanvasItems)
                proxy.displayName = self.GetValue()

    def ResetFocus(self):
        if self.defocusCallback:
            self.defocusCallback()
        
    def SaveAndHide(self):
        assert self.IsShown(), "Shouldn't be saving the editor value if it isn't visible!"
        self.SaveItem()
        self._unfocusing = True
        self.Hide()
        self.ResetFocus()
        self._unfocusing = False
        
    def OnEnterPressed(self, event):
        """
        for now, no need to display
        """
        self.SaveAndHide()
        event.Skip()

    def OnKillFocus(self, event):
        super(wxInPlaceEditor, self).OnKillFocus(event)
        if not self._unfocusing:
            self.SaveAndHide()

    def OnChar(self, event):
        if (event.KeyCode() == wx.WXK_RETURN):
            if self.item != None:
                self.item.displayName = self.GetValue()
            self.Hide()
        event.Skip()

    def SetItem(self, item, position, size, pointSize):
        self.item = item
        self.SetValue(item.displayName)

        newSize = wx.Size(size.width, size.height)

        font = wx.Font(pointSize, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        self.SetFont(font)

        # move the frame so that the default Mac Aqua focus "halo"
        # is aligned with the outer event frame
        if '__WXMAC__' in wx.PlatformInfo:
            position.x -= 1
            newSize.width += 4
            newSize.height -= 1

        self.SetSize(newSize)
        self.Move(position)

        self.SetInsertionPointEnd()

        #Note: It appears that setting the selection before self.Show() causes
        #      the selection to get discarded. (so we set it after.)
        
        self.Show()
        self.SetFocus()
        self.SetSelection(-1, -1)

    def OnSize(self, event):
        self.Hide()
        event.Skip()

        
class CalendarContainer(BoxContainer):
    """
    The highlevel container that holds:
    - the controller
    - the various canvases
    """
    calendarControl = schema.One(schema.Item, required=True)

    monthLabelStyle = schema.One(Styles.CharacterStyle, required=True)
    eventLabelStyle = schema.One(Styles.CharacterStyle, required=True)
    eventTimeStyle = schema.One(Styles.CharacterStyle, required=True)
    legendStyle = schema.One(Styles.CharacterStyle, required=True)
    
    schema.addClouds(
        copying = schema.Cloud(byRef = [monthLabelStyle, 
                                        eventLabelStyle, 
                                        eventTimeStyle,
                                        legendStyle,
                                        ])
    )

    def __init__(self, *arguments, **keywords):
        super(CalendarContainer, self).__init__(*arguments, **keywords)

    def InitializeStyles(self):

        # Map styles to fonts
        for stylename in ('monthLabel', 'eventLabel', 'eventTime', 'legend'):
            style = getattr(self, stylename + 'Style')
            setattr(self, stylename + 'Font', 
                    Styles.getFont(style))
            
        self.monthLabelColor = wx.Colour(64, 64, 64)

        self.eventLabelColor = wx.BLACK
        self.eventLabelHeight = \
            Styles.getMeasurements(self.eventLabelFont).height
        
        self.legendColor = wx.Colour(128,128,128)

        self.bgColor = wx.WHITE

        self.majorLineColor = wx.Colour(204, 204, 204)
        self.minorLineColor = wx.Colour(217, 217, 217)
 
        self.majorLinePen = wx.Pen(self.majorLineColor)
        self.minorLinePen = wx.Pen(self.minorLineColor)
        self.selectionBrush = wx.Brush(wx.Colour(229, 229, 229))
        self.todayBrush = wx.Brush(wx.Colour(242,242,242))

        # gradient cache
        self.brushes = Gradients()

    def instantiateWidget(self):
        self.InitializeStyles()
        
        w = super(CalendarContainer, self).instantiateWidget()
        if '__WXMAC__' in wx.PlatformInfo:
            w.SetWindowStyle(wx.BORDER_SIMPLE)
        else:
            w.SetWindowStyle(wx.BORDER_STATIC)

        # minimum 45 pixels per column
        w.SetMinSize((8*45, -1))

        return w

    def onNewEvent(self, event):
        """
        Create a new event from the menu - try to use contextual information
        from the view to create it in a normal place
        """
        ourKind = Calendar.CalendarEvent.getKind(self.itsView)
        kindParam = getattr(event, 'kindParameter', ourKind)
        # if we're not creating our own kind, let someone else handle it
        if kindParam is not ourKind:
            event.arguments['continueBubbleUp'] = True
        else:
            # this is a little bit of a hack, because we know we want to get
            # to the timed events canvas
            calendarSplitter = nth(self.childrenBlocks, 1)
            timedEventsBlock = nth(calendarSplitter.childrenBlocks, 1)
            timedEventsCanvas = timedEventsBlock.widget
    
            startTime, duration = timedEventsCanvas.GetNewEventTime()
            newEvent = timedEventsCanvas.CreateEmptyEvent(startTime, duration, False, False)
            
            # return the list of items created
            return [newEvent]
    
class CanvasSplitterWindow(SplitterWindow):
    calendarControl = schema.One(schema.Item, required=True)
    def instantiateWidget(self):
        wxSplitter = super(CanvasSplitterWindow, self).instantiateWidget()
        
        wxSplitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,
                        self.OnSashPositionChanged)
    
        return wxSplitter

    def OnSashPositionChanged(self, event):
        #would write as assert, but keeps failing during block render()'ing
        if __debug__:
            position = self.widget.GetSashPosition()
            if not position == event.GetSashPosition():
                logger.debug("event & splitter sash positions MISMATCH")
        self.calendarControl.widget.ResetSashState()
        event.Skip()


class CalendarControl(CalendarBlock):
    dayMode = schema.One(schema.Boolean)
    daysPerView = schema.One(schema.Integer, initialValue=7) #ready to phase out?
    tzCharacterStyle = schema.One(Styles.CharacterStyle)

    schema.addClouds(
        copying = schema.Cloud(byRef = [tzCharacterStyle])
    )

    def __init__(self, *arguments, **keywords):
        super(CalendarControl, self).__init__(*arguments, **keywords)


    def instantiateWidget(self):
        if not self.getHasBeenRendered():
            self.setRange( datetime.now().date() )
            self.setHasBeenRendered()
        w = wxCalendarControl(self.parentBlock.widget, -1, 
                              tzCharacterStyle=self.tzCharacterStyle)
        return w

    def onSelectedDateChangedEvent(self, event):
        super(CalendarControl, self).onSelectedDateChangedEvent(event)

    def onSelectWeekEvent(self, event):
        """
        I believe, as of now only calctrl sends SelectWeek events anyways.. but just in case...
        this code probably wont work from external SW events right now.
        """
        self.dayMode = not event.arguments['doSelectWeek']
        self.synchronizeWidget()

    def setRange(self, date):
        """
        We need to override CalendarBlock's because the cal ctrl always has
        its range over an entire week, even if a specific day is selected (and
        dayMode is true)
        """
        assert self.daysPerView == 7, "daysPerView is a legacy variable, keep it at 7 plz"
        
        date = datetime.combine(date, time())

        #Set rangeStart
        # start at the beginning of the week (Sunday midnight)
        # refactor to use DayOfWeekNumber
        calendar = GregorianCalendar()
        calendar.setTime(date)
        delta = timedelta(days=(calendar.get(calendar.DAY_OF_WEEK) -
                                calendar.getFirstDayOfWeek()))
        self.rangeStart = date - delta

        #Set selectedDate.  if on week mode, sel'd date is always Sunday midnight.
        if self.dayMode:
            self.selectedDate = date
        else:
            self.selectedDate = self.rangeStart


class wxCalendarControl(wx.Panel, CalendarEventHandler):
    """
    This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons
    """

    def __init__(self, parent, id, tzCharacterStyle, *arguments, **keywords):
        super(wxCalendarControl, self).__init__(parent, id, *arguments, **keywords)
    
        app = wx.GetApp()
        self.allDayCloseArrowImage = app.GetImage("AllDayCloseArrow_whitebg.png")
        self.allDayOpenArrowImage = app.GetImage("AllDayOpenArrow_whitebg.png")
        self.allDayBlankArrowImage = app.GetImage("AllDayBlankArrow_whitebg.png")


        self.currentSelectedDate = None
        self.currentStartDate = None

        self.SetMaxSize((-1, 80)) 

        # Set up sizers
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ugly! We have to add left/right/center so that
        # the month text remains centered
        navigationRow = wx.BoxSizer(wx.HORIZONTAL)
        
        
        sizer.Add((7,7), 0, wx.EXPAND)
        sizer.Add(navigationRow, 0, wx.EXPAND)
        sizer.Add((5,5), 0, wx.EXPAND)

        self.monthText = wx.StaticText(self, -1)
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "CalBackArrow")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "CalForwardArrow")
        self.Bind(wx.EVT_BUTTON, self.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.OnNext, self.nextButton)

        self.tzChoice = self.MakeTimezoneChoice(tzCharacterStyle)

        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.prevButton, 0, wx.ALIGN_CENTER)
        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.nextButton, 0, wx.ALIGN_CENTER)
        navigationRow.Add((10,1), 0)
        navigationRow.Add(self.monthText, 0, wx.ALIGN_CENTER)
        navigationRow.Add((0,0), 1)
        
        navigationRow.Add(self.tzChoice, 0)
        navigationRow.Add((1,1), 0)

        
        # finally the last row, with the header
        weekColumnHeader = \
            self.weekColumnHeader = wx.colheader.ColumnHeader(self)
        
        # turn this off for now, because our sizing needs to be exact
        weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_ProportionalResizing,False)

        #these labels get overriden by wxSynchronizeWidget()
        #XXX: [i18n] These Header labels need to leverage PyICU for the display names
        headerLabels = [_(u"Week"), "S", "M", "Tu", "W", "Th", "F", "S", '']
        for header in headerLabels:
            weekColumnHeader.AppendItem(header, wx.colheader.CH_JUST_Center,
                                        0, bSortEnabled=False)
            
        expandoColumn = len(headerLabels) - 1
        weekColumnHeader.SetBitmapJustification(expandoColumn,
                                                wx.colheader.CH_JUST_Center)
        weekColumnHeader.SetBitmapRef(expandoColumn, self.allDayBlankArrowImage)
        self.Bind(wx.colheader.EVT_COLUMNHEADER_SELCHANGED,
                  self.OnDayColumnSelect, weekColumnHeader)

        # set up initial selection
        weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_VisibleSelection,
                                      True)
        sizer.Add(weekColumnHeader, 0, wx.EXPAND)
        
        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
        self.Layout()

    def OnInit(self):
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetBackgroundColour(self.blockItem.parentBlock.bgColor)
        
        styles = self.blockItem.calendarContainer
        self.monthText.SetFont(styles.monthLabelFont)
        self.monthText.SetForegroundColour(styles.monthLabelColor)
        
        self.UpdateHeader()
        self._doDrawingCalculations() #hopefully this is early enough

    def MakeTimezoneChoice(self, tzCharacterStyle):

        tzChoice = wx.Choice(self)
        font = Styles.getFont(tzCharacterStyle)
        if font is not None:
            tzChoice.SetFont(font)

        # self.blockItem hasn't been set yet, because
        # CalendarControl.instantiateWidget() hasn't returned.
        # So, we get the repo view from our parent's blockItem.
        view = self.GetParent().blockItem.itsView
        info = TimeZoneInfo.get(view=view)
        defaultTzinfo = info.canonicalTimeZone(info.default)
        
        # Now, populate the wxChoice with TimeZoneInfo.knownTimeZones
        selectIndex = -1
        for name, zone in info.iterTimeZones():
            index = tzChoice.Append(name, clientData=zone)
            
            if defaultTzinfo.timezone == zone.timezone:
                # [@@@] grant: Should be defaultTzinfo == zone; PyICU bug?
                selectIndex = index
        
        if selectIndex is -1:
            tzChoice.Insert(unicode(defaultTzinfo), 0, clientData=zone)
            selectIndex = 0

        tzChoice.Select(selectIndex)

        self.Bind(wx.EVT_CHOICE, self.OnTZChoice, tzChoice)

        return tzChoice
        
    def UpdateHeader(self):
        if self.blockItem.dayMode:
            # ugly back-calculation of the previously selected day
            reldate = self.blockItem.selectedDate - \
                      self.blockItem.rangeStart
            self.weekColumnHeader.SetSelectedItem(reldate.days+1)
        else:
            self.weekColumnHeader.SetSelectedItem(0)

    def ResizeHeader(self):
        drawInfo = self
        self.weekColumnHeader.Freeze()
        for (i,width) in enumerate(drawInfo.columnWidths):
            self.weekColumnHeader.SetUIExtent(i, (0,width))
        self.weekColumnHeader.Thaw()

    def OnSize(self, event):
        self._doDrawingCalculations()
        self.ResizeHeader()
        event.Skip()

    def wxSynchronizeWidget(self, **hints):
        selectedDate = self.blockItem.selectedDate
        startDate = self.blockItem.rangeStart

        # We're just synchronizing the control area,
        # so we only care if the visible range has changed
        if (selectedDate == self.currentSelectedDate and
            startDate == self.currentStartDate):
            return

        # update the calendar with the calender's color
        collection = self.blockItem.contents.collectionList[0]
        
        # force the creation of the .color attribute
        # XXX temporary - really this should somehow generate automatically
        colorInfo = ColorInfo(collection)

        # Update the month button given the selected date
        lastDate = startDate + timedelta(days=6)
        months = dateFormatSymbols.getMonths()
        year = lastDate.year
        if (startDate.month == lastDate.month):
            monthText = _(u'%(currentMonth)s %(currentYear)d') % \
                        dict( currentMonth= months[selectedDate.month - 1],
                              currentYear = year )
        else:
            monthText = _(u'%(currentMonth1)s - %(currentMonth2)s %(currentYear)d') % \
                        dict(currentMonth1= months[startDate.month - 1],
                         currentMonth2= months[lastDate.month - 1],
                         currentYear=   year )

        self.monthText.SetLabel(monthText)

        today = date.today()
        # ICU makes this list 1-based, 1st element is an empty string, so that
        # shortWeekdays[Calendar.SUNDAY] == 'short name for sunday'
        shortWeekdays = dateFormatSymbols.getShortWeekdays()
        firstDay = GregorianCalendar().getFirstDayOfWeek()

        for day in xrange(7):
            actualDay = ((day + firstDay - 1) % 7)
            currentDate = startDate + timedelta(days=day)
            dayName = u"%s %d" %(shortWeekdays[actualDay + 1],
                                 currentDate.day)
            self.weekColumnHeader.SetLabelText(day+1, dayName)
            
        self.currentSelectedDate = datetime.combine(selectedDate, time())
        self.currentStartDate = datetime.combine(startDate, time())
        
        self.Layout()

        #REFACTOR: attempting to update correctly... maybe elim some Refresh()'s?
        self.UpdateHeader()
        self.weekColumnHeader.Refresh()
        self.Refresh()
        
    def OnDayColumnSelect(self, event):
        
        colIndex = self.weekColumnHeader.GetSelectedItem()
        
        # column 0, week button
        if (colIndex == 0):
            return self.OnWeekSelect()

        # the expando-button
        if (colIndex == 8):
            self.UpdateHeader()
            self.OnExpandButtonClick(event)
            return False #@@@ whats the return value mean? -brendano
        
        # all other cases mean a day was selected
        # OnDaySelect takes a zero-based day, and our first day is in column 1
        return self.OnDaySelect(colIndex-1)


    # Should this height logic should move to wxAllDayEventsCanvas?
    # yes: most of it centers around properties of the all day area
    # no: procedurally more clear if all here, and some info from the splitter is important
    
    def OnExpandButtonClick(self, event):
        wxAllDay = self.GetAllDayBlock().widget
        wxSplitter = self.GetSplitterWidget()
        wxTimed = wxSplitter.GetWindow2()
        
        #Would be asserts, but they fail in simple boundary cases (e.g. really
        #short window) until wx's SplitterWindow can be massively bugfixed
        if __debug__:
            height = lambda widget: widget.GetSize()[1]
            sumIsHappy = (height(wxSplitter) ==
                          height(wxAllDay) + height(wxTimed) +
                          wxSplitter.GetSashSize())
            sashIsAllDayHeight = (wxSplitter.GetSashPosition() ==
                                  height(wxAllDay))
            if not (sumIsHappy and sashIsAllDayHeight):
                logger.debug("Calendar splitter sanity check FAILED. "
                             "sumIsHappy: %s\t sashIsAllDayHeight: %s" %
                             (sumIsHappy, sashIsAllDayHeight))
                return
            logger.debug("min pane size: %s" % wxSplitter.GetMinimumPaneSize())
            logger.debug("wxTimed height: %s" % wxTimed.GetSize()[1])
            logger.debug("BEFORE: curHeight=%d allday's size=%s "
                         "collHeight=%d, expHeight=%d" %
                         (height(wxAllDay), wxAllDay.GetSize(),
                          wxAllDay.collapsedHeight, wxAllDay.expandedHeight))
            
        # There are two possible "expanded" heights of the all day area
        #  (1) wxAllDay.expandedHeight, which is the needed size to show all events
        #  (2) the biggest it can be if you drag the splitter all the way to the bottom

        # here we back-calculate (2) with heuristics i HOPE always are true
        # from the wx splitter. Their correctness should be ensured by the
        # sumIsHappy check.        
        maxAllDayHeightConstrainedByWindow = wxSplitter.GetSize()[1] - wxSplitter.GetSashSize() - wxSplitter.GetMinimumPaneSize()
        logger.debug("max from window: %s" % maxAllDayHeightConstrainedByWindow)
        
        effectiveExpandedHeight = min( wxAllDay.expandedHeight,
                                       maxAllDayHeightConstrainedByWindow)
        currentHeight = wxAllDay.GetSize()[1]
        if (currentHeight >= wxAllDay.collapsedHeight and
            currentHeight < effectiveExpandedHeight):
            logger.debug("Expand to %s" % wxAllDay.expandedHeight)
            wxAllDay.GetParent().MoveSash(wxAllDay.expandedHeight)
            wxAllDay.autoExpandMode = True
            self.ResetSashState()
        else:
            logger.debug("Collapse to %s" %wxAllDay.collapsedHeight)
            wxAllDay.autoExpandMode = False
            wxAllDay.GetParent().MoveSash(wxAllDay.collapsedHeight)
            self.ResetSashState()
        event.Skip()
    

    def GetAllDayBlock(self):
        # @@@ hack that depends on tree structure! would be better to have an
        # allDay reference in calcontainer or calctrl, but that causes
        # initialization order weirdness
        # ALTERNATIVE: findBlockByName?
        return list(list(self.blockItem.parentBlock.childrenBlocks)[1].childrenBlocks)[0]

    def GetSplitterWidget(self):
        # @@@ Another hack. This will all be refactored soon, I
        # promise -alecf
        allDayArea = self.GetAllDayBlock()
        return allDayArea.parentBlock.widget

    def ResetSashState(self):
        wxAllDay = self.GetAllDayBlock().widget
        splitter = self.GetSplitterWidget()
        position = splitter.GetSashPosition()
        sashsize = splitter.GetSashSize()
 
        if position < 0:
            #yes, this does happen quite a bit during block rendering
            pass
        elif position - sashsize <= wxAllDay.collapsedHeight:
            wxAllDay.autoExpandMode = False
            self.weekColumnHeader.SetBitmapRef(8, self.allDayOpenArrowImage)
            
        elif position - sashsize > wxAllDay.collapsedHeight:
            wxAllDay.autoExpandMode = True
            self.weekColumnHeader.SetBitmapRef(8, self.allDayCloseArrowImage)
        
    def OnDaySelect(self, day):
        """
        Callback when a specific day is selected from column header.
        
        @param day: is 0-6
        """
        startDate = self.blockItem.rangeStart
        selectedDate = startDate + timedelta(days=day)
        
        self.blockItem.postSelectWeek(False)
        self.blockItem.postDateChanged(selectedDate)

    def OnWeekSelect(self):
        """
        Callback when the 'week' button is clicked on column header.
        """
        self.blockItem.postSelectWeek(True)
        self.blockItem.postDateChanged(self.blockItem.rangeStart)

    ########## used to be in wxCalendarContainer, then CalendarContainer.  lets try putting here...
    def _doDrawingCalculations(self):
        """
        Sets a bunch of drawing variables.  Some more drawing variables are created lazily
        outside of this function.
        """
        self.scrollbarWidth = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X) + 1

        self.size = self.GetSize()
        
        try:
            oldDayWidth = self.dayWidth
        except AttributeError:
            oldDayWidth = -1

        self.dayWidth = ((self.size.width - self.scrollbarWidth) / 
                         (self.blockItem.daysPerView + 1))

        ### calculate column widths for the all-7-days week view case
        # column layout rules are funky (e.g. bug 3290)
        # - all 7 days are fixed at self.dayWidth
        # - the last column (expando-button) is fixed
        # - the "Week" column is the same as self.dayWidth, plus leftover pixels
        columnCount = 9
        dayWidths = (self.dayWidth,) * 7

        self.middleWidth = self.dayWidth*7
        self.xOffset = self.size.width - self.middleWidth - self.scrollbarWidth
        self.columnWidths = (self.xOffset,) +dayWidths+ (self.scrollbarWidth,)

        # the gradient brushes are based on dayWidth, so blow it away
        # when dayWidth changes
        styles = self.blockItem.calendarContainer
        if oldDayWidth != self.dayWidth:
            # Really, the gradients cache should be managing this for us,
            # so that we may smoothly change sizes without loosing too much
            # information
            styles.brushes.ClearCache()
        

    def _getColumns(self):
        if self.blockItem.dayMode:
            return 1
        else:
            return self.blockItem.daysPerView

    columns = property(_getColumns)


    def _getDividerPositions(self):
        """
        Tuple of divider lines for the canvases.
        
        unlike columnWidths, this IS sensitive whether you're viewing one day
        vs. week
        """
        if not hasattr(self, 'columnWidths'):
            self._doDrawingCalculations()
        cw = self.columnWidths
        if self.blockItem.dayMode:
            lastDividerPos = sum(cw)
            return (cw[0], lastDividerPos)
        else:
            ## e.g. 10,40,40,40 => 0,10,50,90
            cumulSums =  [sum(cw[:i]) for i in range(len(cw))]
            return cumulSums[1:]

    dividerPositions = property(_getDividerPositions)

