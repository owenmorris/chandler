""" Canvas for calendaring blocks
"""

__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx
import wx.colheader

from repository.item.Monitors import Monitors

from datetime import datetime, timedelta, date, time
from PyICU import GregorianCalendar, DateFormatSymbols, ICUtzinfo

import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.TimeZone import TimeZoneInfo, formatTime
import application.dialogs.RecurrenceDialog as RecurrenceDialog
# import osaf.pim.items as items

from osaf.framework.blocks import DragAndDrop
from osaf.framework.blocks import Block
from osaf.framework.blocks import ContainerBlocks
from osaf.framework.blocks import Styles, ColorType
from osaf.framework.blocks import Sendability
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
from osaf.framework.blocks.calendar import CollectionCanvas

import osaf.framework.blocks.DrawingUtilities as DrawingUtilities

from application import schema
import itertools
import copy
import logging

from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)

dateFormatSymbols = DateFormatSymbols()

TRANSPARENCY_DASHES = [255, 255, 0, 0, 255, 255, 0, 0]

"""Widget overview

the composition of blocks is as follows
CalendarContainer  is the Block for the entire summary view
its children subblocks are as follows:

-------------------------------------------------------------
| wxCalendarControl - block: CalendarControl                                       
| [color selector]   <- June 2005 ->      [timezone] 
|                                                           
| also has the row of week/7-days buttons as an inset widget:
|-------------------------------------------------------
|| wx.colheader.ColumnHeader  (instance name: weekColumnHeader)
||Week  Sun  Mon  Tue  Wed  Thu  Fri  +                     
||------------------------------------------------------
|---------------------------------------------------------
| SplitterWindow block, two children blocks
| |---------------------------------------------------------
| |wxAllDayEventsCanvas - block: AllDayEventsCanvas
| | where the all-day events go
| |---------------------------------------------------------
| |wxTimedEventsCanvas - block: TimedEventsCanvas
| | the main area that can have events at specific times
| |
| | [much bigger, not drawn to scale]
| |
| |-------------------------------------------------------
-------------------------------------------------------------
"""

def roundTo(v, r):
    """
    round down v to the nearest r
    """
    return (v/r)*r
    
class ColorInfo(object):

    # need to convert hues from 0..360 to 0..1.0 range
    # removed 60, 180, 90 for now because they looked too light
    hueList = [k/360.0 for k in [210, 120, 0, 30, 270, 240, 330]]
    lastHueIndex = 3 # hack for now, because the first 4 collections are already assigned

    def __init__(self, collection):
        color = getattr (collection, 'color', None)
        if color is not None:
            rgb = wx.Image_RGBValue (color.red, color.green, color.blue)
            self.hue = wx.Image.RGBtoHSV (rgb).hue
        else:
            self.hue = ColorInfo.getNextHue()
            try:
                dn = collection.displayName
            except:
                dn = str(collection)

            # the actual saturation and value are not important here,
            # its never used.
            rgb = wx.Image.HSVtoRGB (wx.Image_HSVValue (self.hue, 0.5, 1.0))
            collection.color = ColorType (rgb.red, rgb.green, rgb.blue, 255)
                                         
    @classmethod
    def getNextHue(cls):
        """
        returns the next hue following the one passed in
        For example,
        f.hue = nextHue(f.hue)
        """
        cls.lastHueIndex += 1
        cls.lastHueIndex %= len(cls.hueList)
        return cls.hueList[cls.lastHueIndex]
    
    # to be used like a property, i.e. prop = tintedColor(0.5, 1.0)
    # takes HSV 'S' and 'V' and returns an color based tuple property
    def tintedColor(saturation, value = 1.0):
        def getSaturatedColor(self):
            rgb = wx.Image.HSVtoRGB (wx.Image_HSVValue (self.hue, saturation, value))
            return rgb.red, rgb.green, rgb.blue
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
        
class CalendarCanvasItem(CollectionCanvas.CanvasItem):
    """
    Base class for calendar items. Covers:
    - editor position & size
    - text wrapping
    - conflict management
    """
    
    timeHeight = 0
    
    def __init__(self, *args, **keywords):
        super(CalendarCanvasItem, self).__init__(*args, **keywords)
        self._parentConflicts = []
        self._childConflicts = []
        # the rating of conflicts - i.e. how far to indent this.  Just
        # a simple zero-based ordering - not a pixel count!
        self._conflictDepth = 0

        # this is supposed to be set in Draw(), but sometimes this
        # object seems to exist before Draw() is called
        self.textOffset = wx.Point(self.textMargin, self.textMargin)
                        
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

    def GetAnyTimeOrAllDay(self):	
        item = self.GetItem()	
        try:	
            anyTime = item.anyTime	
        except AttributeError:	
            anyTime = False	
        try:	
            allDay = item.allDay	
        except AttributeError:	
            allDay = False	
       
        return anyTime or allDay
             
                
    def AddConflict(self, child):	
        """	
        Register a conflict with another event - this should only be done	
        to add conflicts with 'child' events, because the child is notified	
        about the parent conflicts	
        """
        # we might want to keep track of the inverse conflict as well,
        # for conflict bars
        child._parentConflicts.append(self)
        self._childConflicts.append(child)
        
    @staticmethod
    def FindFirstGapInSequence(seq):
        """
        Look for the first gap in a sequence - for instance
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
        
    def CalculateConflictDepth(self):
        """
        Calculate the 'depth', or indentation level, of the current item	
        This is done with the assumption that all parent conflicts have	
        already had their conflict depths calculated.	
        """
        # We'll find out the depth of all our parents, and then
        # see if there's an empty gap we can fill
        # this relies on parentDepths being sorted, which 
        # is true because the conflicts are added in 
        # the same order as the they appear in the calendar
        parentDepths = [parent._conflictDepth for parent in self._parentConflicts]
        self._conflictDepth = self.FindFirstGapInSequence(parentDepths)
        return self._conflictDepth
        
    def GetIndentLevel(self):
        """
        The calculated conflictdepth is the indentation level
        """
        return self._conflictDepth
        
    def GetMaxDepth(self):	
        """	
        This determines how 'deep' this item is: the maximum	
        Indent Level of ALL items that CONFLICT with this one.	
        e.g. 3 items might conflict, and they all might be indented by	
        one due to an earlier conflict, so the maximum 'depth' is 4.	
        """
        maxparents = maxchildren = 0
        if self._childConflicts:
            maxchildren = max([child.GetIndentLevel() for child in self._childConflicts])
        if self._parentConflicts:
            maxparents = max([parent.GetIndentLevel() for parent in self._parentConflicts])
        return max(self.GetIndentLevel(), maxchildren, maxparents)

        
    def Draw(self, dc, styles, brushOffset, selected, rightSideCutOff=False):
        # @@@ add a general cutoff parameter?
        item = self._item	
        if item.isDeleted():
            return
        
        time = item.startTime	
        isAnyTimeOrAllDay = self.GetAnyTimeOrAllDay()	
        # Draw one event - an event consists of one or more bounds	
       
        clipRect = None	
        (cx,cy,cwidth,cheight) = dc.GetClippingBox()	
        if not cwidth == cheight == 0:	
            clipRect = wx.Rect(cx,cy,cwidth,cheight)	
       
        gradientLeft, gradientRight, outlineColor, textColor = \
            styles.calendarControl.getEventColors(item, selected)
       
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
            hasLeftRounded = Calendar.datetimeOp(item.startTime, '==',
                                             item.endTime)
            
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

 
            dc.SetPen(wx.BLACK_PEN)	
       
            self.textOffset = wx.Point(self.textMargin, self.textMargin)
            
            if hasLeftRounded:
                cornerRadius = 8
                self.textOffset.x += cornerRadius
            else:
                self.textOffset.x += 3

            # Shift text to account for rounded corners
            x = itemRect.x + self.textOffset.x
            y = itemRect.y + self.textOffset.y
            width = itemRect.width - self.textOffset.x - (self.textMargin + 10)
            
            # only draw date/time on first item	
            if drawEventText:
                # only draw time on timed events
                if not isAnyTimeOrAllDay:
                    timeString = formatTime(time)
                    te = dc.GetFullTextExtent(timeString, styles.eventTimeFont)	
                    timeHeight = te[1]	
       
                    # draw the time if there is room	
                    if (timeHeight < itemRect.height/2):	
                        timeRect = wx.Rect(x, y, width, timeHeight)
                        
                        dc.SetFont(styles.eventTimeFont)	
                        self.timeHeight = \
                            DrawingUtilities.DrawWrappedText(dc, timeString, timeRect)

                        # add some space below the time
                        self.timeHeight += 3
                        y += self.timeHeight
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
                DrawingUtilities.DrawWrappedText(dc, item.displayName, textRect)	
       
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
        self.blockItem.decrementRange()
        self.blockItem.postDateChanged()
        self.wxSynchronizeWidget()

    def OnNext(self, event):
        self.blockItem.incrementRange()
        self.blockItem.postDateChanged()
        self.wxSynchronizeWidget()

    def OnToday(self, event):
        today = CalendarBlock.startOfToday()
        
        self.blockItem.setRange(today)
        self.blockItem.postDateChanged()
        self.wxSynchronizeWidget()
        
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


class CalendarBlock(Sendability, CollectionCanvas.CollectionBlock):
    """ Abstract block used as base Kind for Calendar related blocks.

    This base class can be used for any block that displays a collection of
    items based on a date range.

    its date range may change, but the collection of items
    may contain items that don't fall into the currently viewed range.

    @@@ move documentation out of docstrings to schema api .. it supports that
    right?
    
    @ivar rangeStart: beginning of the currently displayed range (persistent)
    @type rangeStart: datetime
    @ivar rangeIncrement: increment used to find the next or prev block of time
    @type rangeIncrement: timedelta

    @ivar selectedDate: within the current range. REFACTOR: why is this in
    this class? tons of the pre-refactor code used this variable though it was
    only declared in the subclass. The rule is now: selectedDate = rangeStart
    for basic behavior, but selectedDate can range within the date range, e.g.
    when on a week view and you want to have a specific selected date inside
    that. TODO: get rid of switches testing for its existence

    @type selectedDate: datetime
    """
    # @@@ method capitalization policy is inconsistent!
    

    rangeStart = schema.One(schema.DateTime)
    rangeIncrement = schema.One(schema.TimeDelta)
    selectedDate = schema.One(schema.DateTime)
    lastHue = schema.One(schema.Float, initialValue = -1.0)
    dayMode = schema.One(schema.Boolean)

    def getRangeEnd(self):	
        return self.rangeStart + self.rangeIncrement	
    rangeEnd = property(getRangeEnd)

    def __init__(self, *arguments, **keywords):
        super(CalendarBlock, self).__init__(*arguments, **keywords)

        self.rangeIncrement = timedelta(days=7)
        self.dayMode = False
        self.setRange(self.startOfToday())

        # watch for all color changes
        Monitors.attach(self, 'onColorChanged', 'set', 'color')

    def render(self, *args, **kwds):
        super(CalendarBlock, self).render(*args, **kwds)
        Monitors.attach(self, 'onColorChanged', 'set', 'color')

    def unRender(self, *args, **kwds):
        Monitors.detach(self, 'onColorChanged', 'set', 'color')
        super(CalendarBlock, self).unRender(*args, **kwds)
        
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
        """This says, this class has been rendered during this session"""
        cls._beenRendered = True
    @classmethod
    def getHasBeenRendered(cls):
        """Has this class been rendered during this session?"""
        return cls._beenRendered
    
    @staticmethod
    def startOfToday():
        today = date.today()
        start = time(tzinfo=ICUtzinfo.getDefault())
        return datetime.combine(today, start)
        
        
    # Event handling

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
    
    def onSelectedDateChangedEvent(self, event):
        """
        Sets the selected date range and synchronizes the widget.

        @param event: event sent on selected date changed event
        @type event: osaf.framework.blocks.Block.BlockEvent
        @param event.arguments['start']: start of the newly selected date range
        @type event.arguments['start']: datetime
        """
        self.setRange(event.arguments['start'])
        self.widget.wxSynchronizeWidget()

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
        """ Increments the calendar's current range """
        self.rangeStart += self.rangeIncrement
        if self.selectedDate:
            self.selectedDate += self.rangeIncrement

    def decrementRange(self):
        """ Decrements the calendar's current range """
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
        # three possible cases where we're "in range"
        # 1) start time is within range
        # 2) end time is within range
        # 3) start time before range, end time after
        return ((Calendar.datetimeOp(item.startTime, '>=', start) and
                 Calendar.datetimeOp(item.startTime, '<', end)) or 
                (Calendar.datetimeOp(item.endTime, '>=', start) and
                 Calendar.datetimeOp(item.endTime, '<', end)) or 
                (Calendar.datetimeOp(item.startTime, '<=', start) and
                 Calendar.datetimeOp(item.endTime, '>=', end)))

    def generateItemsInRange(self, date, nextDate, dayItems):

        # getOccurrencesBetween is potentially expensive, so
        # make sure we cache the ones we've already visited
        generatedUIDs = []
        generatedItems = []
        for item in self.contents:
            #logger.debug("got item %s" % str(item))

            if self.isDayItem(item) != dayItems:
                continue
            
            try:
                # not all items have UIDs
                icalUID = item.icalUID
                if icalUID not in generatedUIDs:
                    # This is the meat of it - ensure the items actually exist
                    newItems = item.getOccurrencesBetween(date, nextDate,
                                                          onlyGenerated=True)
                    generatedItems.extend(newItems)
                    #logger.debug("generated items: %s" % newItems)
                if icalUID is not None:
                    generatedUIDs.append(icalUID)
            except AttributeError:
                continue
            
        return generatedItems

    def getItemsInRange(self, date, nextDate, dayItems=False, timedItems=True):
        """
        Convenience method to look for the items in the block's contents
        that appear on the given date. We might be able to push this
        to Queries, but itemIsInRange is actually fairly complex.
        
        @type date: datetime
        @type nextDate: datetime
        
        @param dayItems: whether you want day items, or timed items
        @param allItems: overrides dayItems and gives you everything
        
        @return: the items in this collection that appear within the given range
        @rtype: generator of Items
        """
        
        defaultTzinfo = ICUtzinfo.getDefault()
        if date.tzinfo is None:
            date = date.replace(tzinfo=defaultTzinfo)
        else:
            date = date.astimezone(defaultTzinfo)

        defaultTzinfo = ICUtzinfo.getDefault()
        if nextDate.tzinfo is None:
            nextDate = nextDate.replace(tzinfo=defaultTzinfo)
        else:
            nextDate = nextDate.astimezone(defaultTzinfo)
        
        # this is annoying - for the moment we have to first make sure all the
        # generated items exist, then reiterate self.contents
        generatedItems = self.generateItemsInRange(date, nextDate, dayItems)

        for item in itertools.chain(self.contents, generatedItems):
            dayItem = self.isDayItem(item)
            daynessTest =  dayItem == dayItems  or  (not dayItem == timedItems)
            

            if (hasattr(item, 'startTime') and
                hasattr(item, 'duration') and
                daynessTest and
                self.itemIsInRange(item, date, nextDate)):
                # For the moment, master events can be overridden.  Until
                # this is changed (which should happen soon), don't display
                # events for which occurrenceFor is None.
                if item.occurrenceFor is None:
                    continue
                yield item

    def getItemsInCurrentRange(self, *arguments, **keywords):
        start, end = self.GetCurrentDateRange()
        return self.getItemsInRange(start,end, *arguments, **keywords)


    def GetCurrentDateRange(self):
        return (self.rangeStart,  self.rangeStart + self.rangeIncrement)

    #
    # Color stuff
    #
    def getEventColors(self, event, selected):
        """
        returns the appropriate tuple of selected, normal, and visible colors
        """
        collection = self.getContainingCollection(event)
        colorInfo = ColorInfo(collection)
        
        if selected:
            return colorInfo.selectedColors
        # collectionList[0] is the currently selected collection
        elif collection == self.contents.collectionList[0]:
            return colorInfo.defaultColors
        
        return colorInfo.visibleColors

    def getContainingCollection(self, event):
        """
        Get the eventColors object which contains all the right color tints
        for the given event. If the given event doesn't have color data,
        then we return the default one associated with the view
        """

        # generated events need to defer to their parent event
        if event.isGenerated:
            event = event.occurrenceFor
            
        collections = self.contents.collectionList
        firstSpecialCollection = None
        for coll in collections:

            # hack alert! The out-of-the-box collections aren't renameable, so
            # we'll rely on that to make sure we don't get 'All's color
            if (event in coll):
                if getattr(coll, 'renameable', True):
                    return coll
                else:
                    # save it for later, we might be returning it
                    firstSpecialCollection = coll
                    
        if firstSpecialCollection:
            return firstSpecialCollection

        assert False, "Don't have color info"
        
    def setCurrentCalendarColor(self, color):

        # collectionList[0] is the currently selected collection
        self.contents.collectionList[0].color = ColorType(*color)


class wxCalendarCanvas(CollectionCanvas.wxCollectionCanvas,
                  DragAndDrop.DropReceiveWidget, 
                  DragAndDrop.DraggableWidget,
                  DragAndDrop.ItemClipboardHandler):
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
        self.editor = wxInPlaceEditor(self, -1)
        
    def OnScroll(self, event):
        self.Refresh()
        event.Skip()

    def OnSelectItem(self, item):
        super(wxCalendarCanvas, self).OnSelectItem(item)

        # The following was removed for 0.5.04 because it causes the view
        # to be torn down and rerendered, whenever you were clicking around
        # multiple overlayed calendars. This was causing PyDeadObjectErrors
        # on the widgets. yuck.
        
        # tell the sidebar to select the collection    that contains
        # this event - makes the sidebar track the "current" calendar
        # as well as update the gradients correctly
        #coll = self.parent.blockItem.getContainingCollection(item)
        #if coll and coll != self.parent.blockItem.contents.collectionList[0]:
        #    self.parent.blockItem.SelectCollectionInSidebar(coll)
        #self.parent.wxSynchronizeWidget()


    def OnEditItem(self, box):
        styles = self.blockItem.calendarContainer
        position = self.CalcScrolledPosition(box.GetEditorPosition())
        size = box.GetMaxEditorSize()

        self.editor.SetItem(box.GetItem(), position, size, styles.eventLabelFont.GetPointSize())

    def GrabFocusHack(self):
        self.editor.SaveItem()
        self.editor.Hide()
        
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
        
        # thick pens with the line centered at x. Offset the legend border
        # because we want the righthand side of the line to be at X
        legendBorderX = drawInfo.dividerPositions[0] - self.legendBorderWidth/2
        dc.DrawLine(legendBorderX, 0,
                    legendBorderX, self.size.height)
        
        def drawDayLine(dayNum):
            x = drawInfo.dividerPositions[dayNum]
            dc.DrawLine(x, 0,   x, self.size.height)

        # the rest are minor, 1 pixel wide
        dc.SetPen(styles.minorLinePen)
        for dayNum in range(1, drawInfo.columns):
            drawDayLine(dayNum)


    def CreateEmptyEvent(self, startTime, allDay, anyTime):	
        """	
        shared routine to create an event, using the current view	
        also forces consumers to specify important fields	
        """	
        view = self.blockItem.itsView	
        event = Calendar.CalendarEvent(view=view)	
        event.InitOutgoingAttributes()	
       
        # start time is "optional" - callers still must specify None	
        # to be explicit that they want the default time	
        if startTime:	
            event.startTime = startTime	
        event.allDay = allDay	
        event.anyTime = anyTime	
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
        
    def getDateTimeFromPosition(self, position, mustBeInBounds=True):
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

        return newTime.replace(tzinfo=ICUtzinfo.getDefault())

    """
    Methods for Drag and Drop and Cut and Paste
    """
    def SelectedItems(self):
        selection = self.blockItem.selection
        if selection is None:
            return []
        return [selection]

    def AddItems(self, itemList):
        source = self.contents.collectionList[0]
        for item in itemList:	
            source.add (item)


class wxInPlaceEditor(wx.TextCtrl):
    def __init__(self, *arguments, **keywords):
        
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
                # MSW behavior truncates titles that doesn't fit in the event window.
                # TE_PROCESS_ENTER is supposedly not needed when using TE_MULTILINE flag.
                # (in fact raises assertion error), but it apparently *is* needed to
                # not allow newlines in the input field. (at least in GTK.)
                style |= wx.TE_PROCESS_ENTER 
                                             

        super(wxInPlaceEditor, self).__init__(style=style,
                                              *arguments, **keywords)
        
        self.item = None
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnTextEnter)
        self.Hide()

        #self.editor.Bind(wx.EVT_CHAR, self.OnChar)
        parent = self.GetParent()
        parent.Bind(wx.EVT_SIZE, self.OnSize)

    def SaveItem(self):
        if ((self.item != None) and (not self.IsBeingDeleted())):
            if self.item.displayName != self.GetValue():
                proxy = RecurrenceDialog.getProxy(u'ui', self.item)
                proxy.displayName = self.GetValue()
        
    def OnTextEnter(self, event):
        self.SaveItem()
        self.Hide()
        event.Skip()

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
        
        #self.SetSelection(-1, -1) # is ignored.
        self.Show()
        self.SetFocus()
        self.SetSelection(-1, -1)

    def OnSize(self, event):
        self.Hide()
        event.Skip()

        
##############################################################################################################################################################################################################
################# new refactored classes under construction ###################
############# these have to move eventually, together for now #################

class CalendarContainer(ContainerBlocks.BoxContainer):

    calendarControl = schema.One(schema.Item, required=True)
    characterStyle = schema.One(Styles.CharacterStyle, required=True)
    boldCharacterStyle = schema.One(Styles.CharacterStyle, required=True)
    bigBoldCharacterStyle = schema.One(Styles.CharacterStyle, required=True)

    schema.addClouds(
        copying = schema.Cloud(byRef = [characterStyle, 
                                        boldCharacterStyle, 
                                        bigBoldCharacterStyle, 
                                        ])
    )

    def __init__(self, *arguments, **keywords):
        super(CalendarContainer, self).__init__(*arguments, **keywords)

    def InitializeStyles(self):

        #XXX: [i18n] The colors and fonts should be configurable for i18n and accessibility
        #     or at least should come from the host OS
        defaultFont = Styles.getFont(self.characterStyle)
        defaultBoldFont = Styles.getFont(self.boldCharacterStyle)
        defaultBigBoldFont = Styles.getFont(self.bigBoldCharacterStyle)

        self.monthLabelFont = defaultBigBoldFont
        self.monthLabelColor = wx.Colour(64, 64, 64)

        self.eventLabelFont = defaultFont
        self.eventLabelColor = wx.BLACK
        self.eventLabelHeight = Styles.getMeasurements(defaultFont).height
        
        self.eventTimeFont = defaultBoldFont
        
        self.legendFont = defaultFont
        self.legendColor = wx.Colour(128,128,128)

        self.bgColor = wx.WHITE

        self.majorLineColor = wx.Colour(204, 204, 204)
        self.minorLineColor = wx.Colour(217, 217, 217)
 
        self.majorLinePen = wx.Pen(self.majorLineColor)
        self.minorLinePen = wx.Pen(self.minorLineColor)
        self.selectionBrush = wx.Brush(wx.Colour(229, 229, 229))
        self.todayBrush = wx.Brush(wx.Colour(242,242,242))

        #self.Bind(wx.EVT_SIZE, self.OnSize) ## REFACTOR: from the old wx one.
        #hmm. probably dont need because old code did drawing calculations
        #here?
        
        # gradient cache
        self.brushes = DrawingUtilities.Gradients()

    def instantiateWidget(self):
        self.InitializeStyles()
        
        w = super(CalendarContainer, self).instantiateWidget()

        # minimum 45 pixels per column
        w.SetMinSize((8*45, -1))

        return w


class CanvasSplitterWindow(ContainerBlocks.SplitterWindow):
    def instantiateWidget(self):
        wxSplitter = super(CanvasSplitterWindow, self).instantiateWidget()
        
        #we use a proxy because at this splitter's instantiateWidget time,
        #it's not wise to rely on calctrl's widget existence.
        wxSplitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, 
                        lambda event: self.parentBlock.calendarControl.widget.OnSashPositionChange(event))
    
        return wxSplitter


class CalendarControl(CalendarBlock):
    dayMode = schema.One(schema.Boolean)
    daysPerView = schema.One(schema.Integer, initialValue=7) #ready to phase out?
    calendarContainer = schema.One(schema.Item)
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
        """i believe, as of now only calctrl sends SelectWeek events anyways.. but just in case...
        this code probably wont work from external SW events right now."""
        self.dayMode = not event.arguments['doSelectWeek']
        self.widget.wxSynchronizeWidget()

    def setRange(self, date):
        """we need to override CalendarBlock's because the cal ctrl always has
        its range over an entire week, even if a specific day is selected (and
        dayMode is true)"""
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
    """This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons"""

    def __init__(self, parent, id, tzCharacterStyle, *arguments, **keywords):
        super(wxCalendarControl, self).__init__(parent, id, *arguments, **keywords)
    
        self.allDayCloseArrowImage = wx.GetApp().GetImage("AllDayCloseArrow_whitebg.png")
        self.allDayOpenArrowImage = wx.GetApp().GetImage("AllDayOpenArrow_whitebg.png")
        self.allDayBlankArrowImage = wx.GetApp().GetImage("AllDayBlankArrow_whitebg.png")


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
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "backarrow.png")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "forwardarrow.png")
        self.Bind(wx.EVT_BUTTON, self.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.OnNext, self.nextButton)

        self.tzChoice = self.MakeTimezoneChoice(tzCharacterStyle)

        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.prevButton, 0, wx.ALIGN_CENTER)
        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.nextButton, 0, wx.ALIGN_CENTER)
        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.monthText, 0, wx.ALIGN_CENTER)
        navigationRow.Add((0,0), 1)
        
        navigationRow.Add(self.tzChoice, 0)
        navigationRow.Add((1,1), 0)

        
        # finally the last row, with the header
        self.weekColumnHeader = wx.colheader.ColumnHeader(self)
        
        # turn this off for now, because our sizing needs to be exact
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_ProportionalResizing,False)

        #these labels get overriden by wxSynchronizeWidget()
        #XXX: [i18n] These Header labels need to leverage PyICU for the display names
        headerLabels = ["Week", "S", "M", "Tu", "W", "Th", "F", "S", '']
        for header in headerLabels:
            self.weekColumnHeader.AppendItem(header, wx.colheader.CH_JUST_Center, 0, bSortEnabled=False)

        self.weekColumnHeader.SetBitmapJustification(8, wx.colheader.CH_JUST_Center)
        self.weekColumnHeader.SetBitmapRef(8, self.allDayBlankArrowImage)
        self.Bind(wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnDayColumnSelect, self.weekColumnHeader)

        # set up initial selection
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_VisibleSelection,True)
        sizer.Add(self.weekColumnHeader, 0, wx.EXPAND)
        
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
        # [@@@] grant: On Linux, ICUtzinfo.getDefault() returns "PDT",
        # not "US/Pacific". Should we do something to figure out
        # that it's equivalent?

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
        for (i,width) in enumerate(drawInfo.columnWidths):
            self.weekColumnHeader.SetUIExtent(i, (0,width))

    def OnSize(self, event):
        self._doDrawingCalculations()
        self.ResizeHeader()
        event.Skip()
        
    def wxSynchronizeWidget(self):
        selectedDate = self.blockItem.selectedDate
        startDate = self.blockItem.rangeStart

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
        if (startDate.month == lastDate.month):
            monthText = _("%s %d") %(months[selectedDate.month - 1],
                                   selectedDate.year)
        else:
            monthText = _("%s - %s %d") %(months[startDate.month - 1],
                                        months[lastDate.month - 1],
                                        lastDate.year)
     
        self.monthText.SetLabel(monthText)

        today = date.today()
        # ICU makes this list 1-based, 1st element is an empty string, so that
        # shortWeekdays[Calendar.SUNDAY] == 'short name for sunday'
        shortWeekdays = dateFormatSymbols.getShortWeekdays()
        firstDay = GregorianCalendar().getFirstDayOfWeek()

        for day in xrange(7):
            actualDay = ((day + firstDay - 1) % 7)
            currentDate = startDate + timedelta(days=day)
            if currentDate.date() == today:
                dayName = _("Today")
            else:
                dayName = u"%s %02d" %(shortWeekdays[actualDay + 1],
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
        wxAllDay = self.GetAllDayWidget()
        wxSplitter = wxAllDay.GetParent()
        wxTimed = wxSplitter.GetWindow2()
        
        #Would be asserts, but they fail in simple boundary cases (e.g. really
        #short window) until wx's SplitterWindow can be massively bugfixed
        if __debug__:
            ht = lambda widget: widget.GetSize()[1]
            sumIsHappy =   ht(wxSplitter)  ==  ht(wxAllDay) + ht(wxTimed) + wxSplitter.GetSashSize()
            sashIsAllDayHeight =   wxSplitter.GetSashPosition() == ht(wxAllDay)
            if not (sumIsHappy and sashIsAllDayHeight):
                logger.debug("Calendar splitter sanity check FAILED.  sumIsHappy: %s\t sashIsAllDayHeight: %s" % (sumIsHappy, sashIsAllDayHeight))
                return
            logger.debug("min pane size: %s" % wxSplitter.GetMinimumPaneSize())
            logger.debug("wxTimed height: %s" % wxTimed.GetSize()[1])
            logger.debug("BEFORE: curHeight=%d allday's size=%s  collHeight=%d, expHeight=%d" %(ht(wxAllDay), wxAllDay.GetSize(), wxAllDay.collapsedHeight, wxAllDay.expandedHeight))
            
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
            self.OnSashPositionChange()
        else:
            logger.debug("Collapse to %s" %wxAllDay.collapsedHeight)
            wxAllDay.autoExpandMode = False
            wxAllDay.GetParent().MoveSash(wxAllDay.collapsedHeight)
            self.OnSashPositionChange()
        event.Skip()
    

    def GetAllDayWidget(self):
        # @@@ hack that depends on tree structure! would be better to have an
        # allDay reference in calcontainer or calctrl, but that causes
        # initialization order weirdness
        # ALTERNATIVE: findBlockByName?
        return list(list(self.blockItem.parentBlock.childrenBlocks)[1].childrenBlocks)[0].widget
    
    def OnSashPositionChange(self, event=None):
        wxAllDay = self.GetAllDayWidget()
        position = wxAllDay.GetParent().GetSashPosition()
        sashsize = wxAllDay.GetParent().GetSashSize()
        #would write as assert, but keeps failing during block render()'ing
        if event and not position == event.GetSashPosition():
            logger.debug("event & splitter sash positions MISMATCH")
 
        if position < 0:
            #yes, this does happen quite a bit during block rendering
            pass
        elif position - sashsize <= wxAllDay.collapsedHeight:
            #change just the bitmap?  or autoExpandMode as well?
            wxAllDay.autoExpandMode = False
            self.weekColumnHeader.SetBitmapRef(8, self.allDayOpenArrowImage)
        elif position - sashsize > wxAllDay.collapsedHeight:
            wxAllDay.autoExpandMode = True
            self.weekColumnHeader.SetBitmapRef(8, self.allDayCloseArrowImage)
        
        if event: event.Skip()
    
    def OnDaySelect(self, day):
        """callback when a specific day is selected from column header.
        @param day: is 0-6"""
            
        startDate = self.blockItem.rangeStart
        selectedDate = startDate + timedelta(days=day)
        
        self.blockItem.postSelectWeek(False)
        self.blockItem.postDateChanged(selectedDate)

    def OnWeekSelect(self):
        """callback when the "week" button is clicked on column header."""
        self.blockItem.postSelectWeek(True)
        self.blockItem.postDateChanged(self.blockItem.rangeStart)

    ########## used to be in wxCalendarContainer, then CalendarContainer.  lets try putting here...
    def _doDrawingCalculations(self):
        """sets a bunch of drawing variables.  Some more drawing variables are created lazily
        outside of this function."""

        self.scrollbarWidth = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)

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
            styles.brushes.ClearCache()
        

    def _getColumns(self):
        if self.blockItem.dayMode:
            return 1
        else:
            return self.blockItem.daysPerView

    columns = property(_getColumns)


    def _getDividerPositions(self):
        """tuple of divider lines for the canvases.
        unlike columnWidths, this IS sensitive whether you're viewing one day
        vs. week"""
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

##from util.autolog import *
##logmodule(__name__, "wx.*")
