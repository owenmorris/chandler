""" Canvas for calendaring blocks
"""

__version__ = "$Revision: 5838 $"
__date__ = "$Date: 2005-06-30 19:40:14 -0700 (Thu, 30 Jun 2005) $"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar.refactor"

import wx
import wx.colheader
import wx.lib.colourselect as colourselect

from datetime import datetime, timedelta, date, time
from PyICU import GregorianCalendar, DateFormatSymbols, FieldPosition, DateFormat

import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.ContentModel as ContentModel

from osaf.framework.blocks import DragAndDrop
from osaf.framework.blocks import Block
from osaf.framework.blocks import ContainerBlocks
from osaf.framework.blocks import Styles
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
from osaf.framework.blocks.calendar import CollectionCanvas

import osaf.framework.blocks.DrawingUtilities as DrawingUtilities

from application import schema
from colorsys import *
import copy

dateFormatSymbols = DateFormatSymbols()

"""Widget overview
REFACTOR: UPDATE FOR BLOCKIFICATION
CalendarContainer  is the Block for the entire week view
its widget is a wxCalendarContainer
that contains 3 widgets:
    wxCalendarControl
    wxAllDayEventsCanvas
    wxTimedEventsCanvas

here is wxCalendarContainer, taking up the center area of Chandler:
----------------------------------------------------------
| wxCalendarControl                                       
| [color selector]    June 2005                  <- ->      
|                                                           
| also has the row of week/7-days buttons as an inset widget:
|-------------------------------------------------------
|| wx.colheader.ColumnHeader  (instance name: weekColumnHeader)
||Week  Sun  Mon  Tue  Wed  Thu  Fri  +                     
||------------------------------------------------------
|---------------------------------------------------------
| wxAllDayEventsCanvas
|  where the all-day events go
|---------------------------------------------------------
| wxTimedEventsCanvas
|  the main area that can have events at specific times
|
|  [much bigger, not drawn to scale]
|
|
----------------------------------------------------------
"""

# from ASPN/Python Cookbook
class CachedAttribute(object):
    def __init__(self, method):
        self.method = method
        self.name = method.__name__
        
    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst, self.name, result)
        return result

class CalendarData(ContentModel.ContentItem):

    calendarColor = schema.One(Styles.ColorStyle)

    # need to convert hues from 0..360 to 0..1.0 range
    hueList = [k/360.0 for k in [210, 120, 60, 0, 240, 90, 330, 30, 180, 270]]
    
    @classmethod
    def getNextHue(cls, oldhue):
        """
        returns the next hue following the one passed in
        For example,
        f.hue = nextHue(f.hue)
        """
        found = False
        for hue in cls.hueList:
            if found: return hue
            if hue == oldhue:
                found = True
        return cls.hueList[0]
    
    def _setEventColor(self, color):
        self.calendarColor.backgroundColor = color

        # clear cached values
        try:
            del self.eventHue
        except AttributeError:
            pass
        
    def _getEventColor(self):
        return self.calendarColor.backgroundColor
        
    # this is the actual RGB value for eventColor
    eventColor = property(_getEventColor, _setEventColor)
    
    @CachedAttribute
    def eventHue(self):
        c = self.eventColor
        rgbvalues = (c.red, c.green, c.blue)
        hsv = rgb_to_hsv(*DrawingUtilities.color2rgb(*rgbvalues))
        return hsv[0]
    
    # to be used like a property, i.e. prop = tintedColor(0.5, 1.0)
    # takes HSV 'S' and 'V' and returns an color based tuple property
    def tintedColor(saturation, value = 1.0):
        def getSaturatedColor(self):
            hsv = (self.eventHue, saturation, value)
            return DrawingUtilities.rgb2color(*hsv_to_rgb(*hsv))
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
    visibleGradientLeft = tintedColor(0.3)
    visibleGradientRight = tintedColor(0.3)
    visibleOutlineColor = tintedColor(0.4)
    visibleTextColor = tintedColor(0.5, 0.95)
    visibleColors = tupleProperty(visibleGradientLeft, visibleGradientRight, visibleOutlineColor, visibleTextColor)
        
class CalendarCanvasItem(CollectionCanvas.CanvasItem):
    """
    Base class for calendar items. Covers:
    - editor position & size
    - text wrapping
    - conflict management
    """
    
    def __init__(self, *args, **keywords):
        super(CalendarCanvasItem, self).__init__(*args, **keywords)
        self._parentConflicts = []
        self._childConflicts = []
        # the rating of conflicts - i.e. how far to indent this
        self._conflictDepth = 0
                
        # the total depth of all conflicts - i.e. the maximum simultaneous 
        # conflicts with this item, including this one
        self._totalConflictDepth = 1
        
    def GetEditorPosition(self):
        """
        This returns a location to show the editor. By default it is the same
        as the default bounding box
        """
        return self._bounds.GetPosition()
        
    def GetDragOrigin(self):
        """
        This is just a stable coordinate that we can use so that when dragging
        items around, for example you can use this to know consistently where 
        the mouse started relative to this origin
        """
        return self._bounds.GetPosition()

    def GetMaxEditorSize(self):
        return self._bounds.GetSize()

    def GetStatusPen(self, color):
        # probably should use styles to determine a good pen color
        item = self.GetItem()

        if (item.transparency == "confirmed"):
            pen = wx.Pen(color, 4)
        elif (item.transparency == "fyi"):
            pen = wx.Pen(color, 1)
        elif (item.transparency == "tentative"):
            if '__WXMAC__' in wx.PlatformInfo:
                # @@@ the dash array may need to be a global, due to wx persistance limitations
                pen = wx.Pen(color, 4, wx.USER_DASH)
                pen.SetDashes([255, 255, 0, 0, 255, 255, 0, 0])
            else:
                pen = wx.Pen(color, 4, wx.DOT)

        return pen
        
    # Drawing utility -- scaffolding, we'll try using editor/renderers
    @staticmethod
    def DrawWrappedText(dc, text, rect):
        """
        Simple wordwrap - draws the text into the current DC
        
        returns the height of the text that was written
        """
        
        result = []
        
        lines = text.splitlines()
        y = rect.y
        totalHeight = 0
        for line in lines:
            x = rect.x
            wrap = 0
            for word in line.split():
                width, height = dc.GetTextExtent(word)

                # first see if we want to jump to the next line
                # (careful not to jump if we're already at the beginning of the line)
                if (x != rect.x and x + width > rect.x + rect.width):
                    y += height
                    totalHeight += height
                    x = rect.x
                
                # if we're out of vertical space, just return
                if (y + height > rect.y + rect.height):
                    return totalHeight
                   
                # if we wrapped but we still can't fit the word,
                # just truncate it    
                if (x == rect.x and width > rect.width):
                    CalendarCanvasItem.DrawClippedText(dc, word, x, y, rect.width)
                    y += height
                    totalHeight += height
                    continue
                
                dc.DrawText(word, x, y)
                x += width
                width, height = dc.GetTextExtent(' ')
                dc.DrawText(' ', x, y)
                x += width
            totalHeight += height
        return totalHeight

    @staticmethod
    def DrawClippedText(dc, word, x, y, maxWidth):
        # keep shortening the word until it fits
        for i in xrange(len(word), 0, -1):
            smallWord = word[0:i] # + "..."
            (width, height) = dc.GetTextExtent(smallWord)
            if width <= maxWidth:
                dc.DrawText(smallWord, x, y)
                return
                
    def AddConflict(self, child):
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
        for index, value in enumerate(seq):
            if index != value:
                return index
                
        # didn't find any gaps, so just put it one higher
        return index+1
        
    def CalculateConflictDepth(self):
        if not self._parentConflicts:
            return 0
        
        # We'll find out the depth of all our parents, and then
        # see if there's an empty gap we can fill
        # this relies on parentDepths being sorted, which 
        # is true because the conflicts are added in 
        # the same order as the they appear in the calendar
        parentDepths = [parent._conflictDepth for parent in self._parentConflicts]
        self._conflictDepth = self.FindFirstGapInSequence(parentDepths)
        return self._conflictDepth
        
    def GetIndentLevel(self):
        # this isn't right. but its a start
        # it should be some wierd combination of 
        # maximum indent level of all children + 1
        return self._conflictDepth
        
    def GetMaxDepth(self):
        maxparents = maxchildren = 0
        if self._childConflicts:
            maxchildren = max([child.GetIndentLevel() for child in self._childConflicts])
        if self._parentConflicts:
            maxparents = max([parent.GetIndentLevel() for parent in self._parentConflicts])
        return max(self.GetIndentLevel(), maxchildren, maxparents)
        

class TimedCanvasItem(CalendarCanvasItem):
    resizeBufferSize = 5
    textMargin = 3
    RESIZE_MODE_START = 1
    RESIZE_MODE_END = 2
    def __init__(self, item, calendarCanvas, *arguments, **keywords):
        super(TimedCanvasItem, self).__init__(None, item)
        
        # this is really annoying that we need to keep a reference back to 
        # the calendar canvas in every single TimedCanvasItem, but we
        # need it for drawing hints.. is there a better way?
        self._calendarCanvas = calendarCanvas

    def UpdateDrawingRects(self):
        item = self.GetItem()
        indent = self.GetIndentLevel() * 5
        width = self.GetMaxDepth() * 5
        self._boundsRects = list(self.GenerateBoundsRects(self._calendarCanvas,
                                                          item.startTime,
                                                          item.endTime, indent, width))
        self._bounds = self._boundsRects[0]

        r = self._boundsRects[-1]
        self._resizeLowBounds = wx.Rect(r.x, r.y + r.height - self.resizeBufferSize,
                                        r.width, self.resizeBufferSize)
        
        r = self._boundsRects[0]
        self._resizeTopBounds = wx.Rect(r.x, r.y,
                                        r.width, self.resizeBufferSize)
        

    def isHitResize(self, point):
        """ Hit testing of a resize region.
        
        @param point: point in unscrolled coordinates
        @type point: wx.Point
        @return: True if the point hit the resize region
        @rtype: Boolean
        """
        return (self._resizeTopBounds.Inside(point) or
                self._resizeLowBounds.Inside(point))

    def isHit(self, point):
        """
        User may have clicked in any of the possible bounds
        """
        for rect in self._boundsRects:
            if rect.Inside(point):
                return True
        return False

    def getResizeMode(self, point):
        """ Returns the mode of the resize, either RESIZE_MODE_START or
        RESIZE_MODE_END.

        The resize mode is RESIZE_MODE_START if dragging from the top of the
        event, and RESIZE_MODE_END if dragging from the bottom of the
        event. None indicates that we are not resizing at all.

        @param point: drag start position in uscrolled coordinates
        @type point: wx.Point
        @return: resize mode, RESIZE_MODE_START, RESIZE_MODE_END or None
        @rtype: string or None
        """
        
        if hasattr(self, '_forceResizeMode'):
            return self._forceResizeMode
            
        if self._resizeTopBounds.Inside(point):
            return self.RESIZE_MODE_START
        if self._resizeLowBounds.Inside(point):
            return self.RESIZE_MODE_END
        return None
        
    def SetResizeMode(self, mode):
        self._forceResizeMode = mode
        
    def ResetResizeMode(self):
        if hasattr(self, '_forceResizeMode'):
            del self._forceResizeMode
    
    @staticmethod
    def GenerateBoundsRects(calendarCanvas, startTime, endTime, indent=0, width=0):
        """
        Generate a bounds rectangle for each day period. For example, an event
        that goes from noon monday to noon wednesday would have three bounds rectangles:
            one from noon monday to midnight
            one for all day tuesday
            one from midnight wednesday morning to noon wednesday
        """
        # calculate how many unique days this appears on 
        days = endTime.toordinal() - startTime.toordinal() + 1
        
        for i in xrange(days):
            
            # first calculate the midnight time for the beginning and end
            # of the current day
            absDay = startTime.toordinal() + i
            absDayStart = datetime.fromordinal(absDay)
            absDayEnd = datetime.fromordinal(absDay + 1)
            
            boundsStartTime = max(startTime, absDayStart)
            boundsEndTime = min(endTime, absDayEnd)
            
            try:
                rect = TimedCanvasItem.MakeRectForRange(calendarCanvas, boundsStartTime, boundsEndTime)
                rect.x += indent
                rect.width -= width
                yield rect
            except ValueError:
                pass
        
    @staticmethod
    def MakeRectForRange(calendarCanvas, startTime, endTime):
        """
        Turn a datetime range into a rectangle that can be drawn on the screen
        This is a static method, and can be used outside this class
        """
        startPosition = calendarCanvas.getPositionFromDateTime(startTime)
        
        # ultimately, I'm not sure that we should be asking the calendarCanvas
        # directly for dayWidth and hourHeight, we probably need some system 
        # instead similar to getPositionFromDateTime where we pass in a duration
        duration = (endTime - startTime)
        duration = duration.days * 24 + duration.seconds / float(3600)
        (cellWidth, cellHeight) = (calendarCanvas.dayWidth, int(duration * calendarCanvas.hourHeight))
        
        return wx.Rect(startPosition.x, startPosition.y, cellWidth, cellHeight)

    def Draw(self, dc, boundingRect, styles, brushOffset, selected):
        item = self._item

        time = item.startTime

        # Draw one event - an event consists of one or more bounds
        lastRect = self._boundsRects[-1]
            
        clipRect = None   
        (cx,cy,cwidth,cheight) = dc.GetClippingBox()
        if not cwidth == cheight == 0:
            clipRect = wx.Rect(cx,cy,cwidth,cheight)

        gradientLeft, gradientRight, outlineColor, textColor = \
            styles.blockItem.getEventColors(item, selected)
        
        dc.SetTextForeground(textColor)
        
        for rectIndex, itemRect in enumerate(self._boundsRects):        
            
            brush = styles.brushes.GetGradientBrush(itemRect.x + brushOffset, 
                                                    itemRect.width, 
                                                    gradientLeft, gradientRight)
            dc.SetBrush(brush)
            dc.SetPen(wx.Pen(outlineColor))

            # properly round the corners - first and last
            # boundsRect gets some rounding, and they
            # may actually be the same boundsRect
            hasTopRightRounded = hasBottomRightRounded = False
            drawTime = False
            if rectIndex == 0:
                hasTopRightRounded = True
                drawTime = True
            if rectIndex == len(self._boundsRects)-1:
                hasBottomRightRounded = True

            self.DrawDRectangle(dc, itemRect, hasTopRightRounded, hasBottomRightRounded)

            pen = self.GetStatusPen(outlineColor)
            pen.SetCap(wx.CAP_BUTT)
            dc.SetPen(pen)
            
            # this refers to the left-hand top/bottom corners - for now
            # with D-shaped events, they are always square, but eventually
            # certain types of events will have rounded corners and we'll
            # have to accomodate them
            cornerRadius = 0
            dc.DrawLine(itemRect.x+1, itemRect.y + (cornerRadius*3/4),
                        itemRect.x+1, itemRect.y + itemRect.height - (cornerRadius*3/4))
            dc.SetPen(wx.BLACK_PEN)

            # Shift text
            x = itemRect.x + self.textMargin + 3
            y = itemRect.y + self.textMargin
            width = itemRect.width - (self.textMargin + 10)
            height = 15
            timeRect = wx.Rect(x, y, width, height)
            
            # only draw date/time on first item
            if drawTime:
                timeString = "%d:%s" %((time.hour % 12) or 12,
                                       time.strftime("%M %p"))
                te = dc.GetFullTextExtent(timeString, styles.eventTimeFont)
                timeHeight = te[1]
                
                # draw the time if there is room
                if (timeHeight < itemRect.height/2):
                    dc.SetFont(styles.eventTimeFont)
                    textHeight = self.DrawWrappedText(dc, timeString, timeRect)
                    y += textHeight
                
                textRect = wx.Rect(x, y, width, itemRect.height - (y - itemRect.y))
                
                dc.SetFont(styles.eventLabelFont)
                self.DrawWrappedText(dc, item.displayName, textRect)
        
        dc.DestroyClippingRegion()
        if clipRect:
            dc.SetClippingRect(clipRect)

    def DrawDRectangle(self, dc, rect, hasTopRightRounded=True, hasBottomRightRounded=True):
        """
        Make a D-shaped rectangle, optionally specifying if the top and bottom
        right side of the rectangle should have rounded corners. Uses
        clip rect tricks to make sure it is drawn correctly
        
        Side effect: Destroys the clipping region.
        """

        radius = 8
        diameter = radius * 2

        dc.DestroyClippingRegion()
        dc.SetClippingRect(rect)
        
        roundRect = wx.Rect(rect.x, rect.y, rect.width, rect.height)
        
        # first widen the whole thing left, this makes sure the 
        # left rounded corners aren't drawn
        roundRect.x -= radius
        roundRect.width += radius
        
        # now optionally push the other rounded corners off the top or bottom
        if not hasBottomRightRounded:
            roundRect.height += radius
            
        if not hasTopRightRounded:
            roundRect.y -= radius
            roundRect.height += radius
        
        # finally draw the clipped rounded rect
        dc.DrawRoundedRectangleRect(roundRect, radius)
        
        # draw the lefthand side border, to stay consistent all
        # the way around the rectangle
        dc.DrawLine(rect.x, rect.y, rect.x, rect.y + rect.height)

class AllDayCanvasItem(CalendarCanvasItem):
    def __init__(self, *args, **kwargs):
        super(AllDayCanvasItem, self).__init__(*args, **kwargs)

    def Draw(self, dc, styles, brushOffset, selected):
        item = self._item
        itemRect = self._bounds
        
        gradientLeft, gradientRight, outlineColor, textColor = \
            styles.blockItem.getEventColors(item, selected)
        
        if selected:
            brush = styles.brushes.GetGradientBrush(itemRect.x + brushOffset,
                                                    itemRect.width,
                                                    gradientLeft,
                                                    gradientRight)
            pen = wx.Pen(outlineColor)
        else:
            brush = wx.TRANSPARENT_BRUSH
            pen = wx.TRANSPARENT_PEN

        dc.SetTextForeground(textColor)
        dc.SetPen(pen)
        dc.SetBrush(brush)
        dc.DrawRectangleRect(itemRect)
                
        # draw little rectangle to the left of the item
        pen = self.GetStatusPen(outlineColor)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)
        dc.DrawLine(itemRect.x + 2, itemRect.y + 3,
                    itemRect.x + 2, itemRect.y + itemRect.height - 3)
        dc.SetPen(wx.BLACK_PEN)

        # Shift text
        textRect = copy.copy(itemRect)
        textRect.x += 5
        textRect.width -= 7
        self.DrawWrappedText(dc, item.displayName, textRect)

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
        today = date.today()
        today = datetime(today.year, today.month, today.day)
        self.blockItem.setRange(today)
        self.blockItem.postDateChanged()
        self.wxSynchronizeWidget()

class ClosureTimer(wx.Timer):
    """
    Helper class because targets may need to recieve multiple different timers
    """
    def __init__(self, callback, *args, **kwargs):
        super(ClosureTimer, self).__init__(*args, **kwargs)
        self._callback = callback
        
    def Notify(self):
        self._callback()

class CalendarBlock(CollectionCanvas.CollectionCanvas):
    """ Abstract block used as base Kind for Calendar related blocks.

    This base class can be used for any block that displays a collection of
    items based on a date range.

    its date range may change, but the collection of items
    may contain items that don't fall into the currently viewed range.

    REFACTOR: split logic into (1) dealing with range/selected dates, and (2)
    collections of items ... bcs calctrl doesnt need (2)... or maybe just set
    contents=None there...

    @@@ move documentation out of docstrings to schema api .. it supports that
    right?
    
    @ivar rangeStart: beginning of the currently displayed range (persistent)
    @type rangeStart: datetime
    @ivar rangeIncrement: increment used to find the next or prev block of time
    @type rangeIncrement: timedelta

    @ivar selectedDate: within the current range.  REFACTOR: why the hell is
    this in this class?  i THINK that selectedDate = rangeStart
    always... unless, as in the old calcon class, they can be different... so
    there you override set, get range()...

    @type selectedDate: datetime
    """
    # @@@ method capitalization policy is inconsistent!

    rangeStart = schema.One(schema.DateTime)
    rangeIncrement = schema.One(schema.TimeDelta)
    selectedDate = schema.One(schema.DateTime)
    
    def __init__(self, *arguments, **keywords):
        super(CalendarBlock, self).__init__(*arguments, **keywords)


    @staticmethod
    def startOfToday():
        today = date.today()
        return datetime(today.year, today.month, today.day)
        
        
    # Event handling
    
    def onSelectedDateChangedEvent(self, event):
        """
        Sets the selected date range and synchronizes the widget.

        @param event: event sent on selected date changed event
        @type event: osaf.framework.blocks.Block.BlockEvent
        @param event['start']: start of the newly selected date range
        @type event['start']: datetime
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
        """Sets the range to include the given date.

        @param date: date to include
        @type date: datetime
        """
        self.rangeStart = date
        self.selectedDate = self.rangeStart

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

    # Get items from the collection

    def getDayItemsByDate(self, date):
        nextDate = date + timedelta(days=1)
        for item in self.contents:
            try:
                anyTime = item.anyTime
            except AttributeError:
                anyTime = False
            try:
                allDay = item.allDay
            except AttributeError:
                allDay = False

            # @@@MOR Since two datetime objects with differing timezone
            # naivete can't be compared, ignore startTime's timezone (via
            # the replace( ) calls below); pardon my naivete if this is wrong.

            if (item.hasLocalAttributeValue('startTime') and
                (allDay or anyTime) and
                (item.startTime.replace(tzinfo=None) >= date) and
                (item.startTime.replace(tzinfo=None) < nextDate)):
                yield item

    def itemIsInRange(self, item, start, end):
        """
        Helpful utility to determine if an item is within a given range
        Assumes the item has a startTime and endTime attribute
        """
        # three possible cases where we're "in range"
        # 1) start time is within range
        # 2) end time is within range
        # 3) start time before range, end time after
        return (((item.startTime >= start) and
                 (item.startTime < end)) or 
                ((item.endTime >= start) and
                 (item.endTime < end)) or 
                ((item.startTime <= start) and
                 (item.endTime >= end)))

    def getItemsInRange(self, date, nextDate):
        """
        Convenience method to look for the items in the block's contents
        that appear on the given date. We might be able to push this
        to Queries, but itemIsInRange is actually fairly complex.
        
        @type date: datetime
        @type nextDate: datetime
        @return: the items in this collection that appear within the given range
        @rtype: list of Items
        """
        for item in self.contents:
            try:
                anyTime = item.anyTime
            except AttributeError:
                anyTime = False
            try:
                allDay = item.allDay
            except AttributeError:
                allDay = False
            if (item.hasLocalAttributeValue('startTime') and
                item.hasLocalAttributeValue('endTime') and
                (not allDay and not anyTime) and
                self.itemIsInRange(item, date, nextDate)):
                yield item

    def GetCurrentDateRange(self):
        return (self.rangeStart,  self.rangeStart + self.rangeIncrement)

    def StampedCalendarData(self, collection):
        if not isinstance(collection, CalendarData):
            collection.StampKind('add', CalendarData.getKind(view=collection.itsView))
            # XXX really, the object should be lazily creating this.
            
            colorstyle = Styles.ColorStyle(view=self.itsView)
            # make copies, because initialValue ends up being shared, because
            # it is isn't immutable
            colorstyle.foregroundColor = copy.copy(colorstyle.foregroundColor)
            colorstyle.backgroundColor = copy.copy(colorstyle.backgroundColor)
            
            collection.calendarColor = colorstyle

            self.setupNextHue()
        return collection
            
    #
    # Color stuff
    #
    def getCalendarData(self):
        """
        Returns a CalendarData object that can be used to persistently store
        calendar color data, and associate it with the collection.
        
        At the moment, this stamps the current itemcollection as a CalendarData
        """
        return self.StampedCalendarData(self.contents.source.first())            
                            
    calendarData = property(getCalendarData)

    def setupNextHue(self):
        c = self.contents.source.first().calendarColor.backgroundColor
        self.lastHue = CalendarData.getNextHue(self.lastHue)
        (c.red, c.green, c.blue) = DrawingUtilities.rgb2color(*hsv_to_rgb(self.lastHue, 1.0, 1.0))
        
        
    def getEventColors(self, event, selected):
        calData = self.getEventCalendarData(event)
        
        if selected:
            return calData.selectedColors
        elif calData == self.contents.source.first():
            return calData.defaultColors
        
        return calData.visibleColors


    def getEventCalendarData(self, event):
        """
        Get the eventColors object which contains all the right color tints
        for the given event. If the given event doesn't have color data,
        then we return the default one associated with the view
        """
        coll = self.getContainingCollection(event)
        return self.StampedCalendarData(coll)
    
    def getContainingCollection(self, event):
        collections = self.contents.source
        selectedCollection = collections.first()
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

        # this seems unlikely.. should we assert? do we even need calendarData?
        return self.calendarData

    def setCalendarColor(self, color):
        """
        Set the base color from which all tints are determined. Note that
        this will lazily stamp the selected collection
        """
        ec = copy.copy(self.calendarData.eventColor)
        (ec.red, ec.green, ec.blue) = color
        self.calendarData.eventColor = ec



     
class OLDCalendarContainer(CalendarBlock):

    daysPerView = schema.One(schema.Integer)
    dayMode = schema.One(schema.Boolean)
    lastHue = schema.One(schema.Float, initialValue = -1.0)

    def __init__(self, *arguments, **keywords):
        super(OLDCalendarContainer, self).__init__ (*arguments, **keywords)

## REFACTOR being hacked apart and away
            
    def instantiateWidget(self):
        # @@@ KCP move to a callback that gets called from parcel loader
        # after item has all of its attributes assigned from parcel xml
        self.initAttributes()
        
        w = OLDwxCalendarContainer(self.parentBlock.widget,
                           Block.Block.getWidgetID(self))

        ### widget-centric code still works



class wxCalendarCanvas(CollectionCanvas.wxCollectionCanvas):
    """
    Base class for all calendar canvases - handles basic item selection, 
    date ranges, and so forth
    """
    def __init__(self, *arguments, **keywords):
        super (wxCalendarCanvas, self).__init__ (*arguments, **keywords)

        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        
    def OnInit(self):
        self.editor = wxInPlaceEditor(self, -1) 
        
    def OnScroll(self, event):
        self.Refresh()
        event.Skip()

    def OnSelectItem(self, item):
        self.parent.blockItem.selection = item
        self.parent.blockItem.postSelectItemBroadcast()

        # tell the sidebar to select the collection that contains
        # this event - makes the sidebar track the "current" calendar
        # as well as update the gradients correctly
        coll = self.parent.blockItem.getContainingCollection(item)
        if coll and coll != self.parent.blockItem.contents.source.first():
            self.parent.blockItem.SelectCollectionInSidebar(coll)
        #self.parent.wxSynchronizeWidget()
    
    def GrabFocusHack(self):
        self.editor.SaveItem()
        self.editor.Hide()
        
    def GetCurrentDateRange(self):
        return self.parent.blockItem.GetCurrentDateRange()

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


## REFACTOR: being refactored away
class OLDwxCalendarContainer(CalendarEventHandler, 
                  DragAndDrop.DropReceiveWidget, 
                  DragAndDrop.DraggableWidget,
                  DragAndDrop.ItemClipboardHandler,
                  wx.Panel):
    def __init__(self, *arguments, **keywords):
        super (OLDwxCalendarContainer, self).__init__ (*arguments, **keywords)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        


    def _doDrawingCalculations(self):
        """sets a bunch of drawing variables"""
        self.size = self.GetSize()
        
        try:
            oldDayWidth = self.dayWidth
        except AttributeError:
            oldDayWidth = -1

        self.dayWidth = (self.size.width - self.scrollbarWidth) / (self.blockItem.daysPerView + 1)

        ### calculate column widths for the all-7-days week view case
        # column layout rules are funky (e.g. bug 3290)
        # - all 7 days are fixed at self.dayWidth
        # - the last column (expando-button) is fixed
        # - the "Week" column is the same as self.dayWidth, plus leftover pixels
        columnCount = 9
        dayWidths = (self.dayWidth,) * 7

        self.middleWidth = self.dayWidth*7
        self.xOffset = self.GetSize().width - self.middleWidth - self.scrollbarWidth
        self.columnWidths = (self.xOffset,) +dayWidths+ (self.scrollbarWidth,)

        # the gradient brushes are based on dayWidth, so blow it away
        # when dayWidth changes
        if oldDayWidth != self.dayWidth:
            self.brushes.ClearCache()
        
        if self.blockItem.dayMode:
            self.columns = 1
        else:
            self.columns = self.blockItem.daysPerView        

        #print self.size, self.xOffset, self.dayWidth, self.columns #convenient interactive way to learn what these variables are, since they're tricky to describe verbally


    def _getDividerPositions(self):
        """tuple of divider lines for the wxWeek{Header,Column}Canvas's.
        unlike columnWidths, this IS sensitive whether you're viewing one day
        vs. week"""
        cw = self.columnWidths
        if self.blockItem.dayMode:
            lastDividerPos = sum(cw)
            return (cw[0], lastDividerPos)
        else:
            ## e.g. 10,40,40,40 => 0,10,50,90
            cumulSums =  [sum(cw[:i]) for i in range(len(cw))]
            return cumulSums[1:]

    dividerPositions = property(_getDividerPositions)

    def OnEraseBackground(self, event):
        pass

    def OnInit(self):
        self._doDrawingCalculations()
        self.calendarControl.OnInit()
        self.allDayEventsCanvas.OnInit()
        self.timedEventsCanvas.OnInit()
        
    def OnSize(self, event):
        self._doDrawingCalculations()
        event.Skip()

    def wxSynchronizeWidget(self):
        
        self._doDrawingCalculations()
        #self.Layout()
        self.calendarControl.wxSynchronizeWidget()
        self.allDayEventsCanvas.wxSynchronizeWidget()
        self.timedEventsCanvas.wxSynchronizeWidget()
        
    def PrintCanvas(self, dc):
        self.timedEventsCanvas.PrintCanvas(dc)

    def OnExpand(self):
        self.allDayEventsCanvas.toggleSize()
        self.Layout()
        
        
    """
    Methods for Drag and Drop and Cut and Paste
    """
    def SelectedItems(self):
        selection = self.blockItem.selection
        if selection is None:
            return []
        return [selection]

    def DeleteSelection(self):
        try:
            self.blockItem.DeleteSelection()
        except AttributeError:
            pass

    def AddItems(self, itemList):
        """ @@@ Need to complete this for Paste to work """

class OLDwxCalendarControl(wx.Panel):
    """This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons"""

    currentSelectedDate = None
    currentStartDate = None
    
    def OnInit(self):
        self.SetBackgroundColour(self.parent.bgColor) ##REFACTOR: cal ctrl wants this

##  REFACTOR: old funky layout code.  how do we put this back in to the block calcon?
##         box = wx.BoxSizer(wx.VERTICAL)
##         box.Add(self.calendarControl, 0, wx.EXPAND)
##         box.Add(self.allDayEventsCanvas, 0, wx.EXPAND)
##         box.Add(self.timedEventsCanvas, 1, wx.EXPAND)
##         self.SetSizer(box)



        # Set up sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        navigationRow = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add((5,5), 0, wx.EXPAND)
        sizer.Add(navigationRow, 0, wx.EXPAND)
        sizer.Add((5,5), 0, wx.EXPAND)

        # beginnings of  in the calendar
        self.colorSelect = colourselect.ColourSelect(self, -1, size=wx.Size(30,15))
        self.Bind(colourselect.EVT_COLOURSELECT, self.parent.OnSelectColor)
        navigationRow.Add((5,5), 0, wx.EXPAND)
        navigationRow.Add(self.colorSelect, 0, wx.CENTER)

        today = date.today()
        today = datetime(today.year, today.month, today.day)
        styles = self.parent

        self.monthText = wx.StaticText(self, -1)
        self.monthText.SetFont(styles.monthLabelFont)
        self.monthText.SetForegroundColour(styles.monthLabelColor)

        navigationRow.Add((0,0), 1)
        
        # add vertical margins above/below the month 
        monthSizer = wx.BoxSizer(wx.VERTICAL)
        monthSizer.Add((7,7),0)
        monthSizer.Add(self.monthText, 0)
        monthSizer.Add((5,5), 0)
        
        navigationRow.Add(monthSizer, 0, wx.ALIGN_CENTER)
        navigationRow.Add((0,0), 1)
        
        # top row - left/right buttons, anchored to the right
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "backarrow.png")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "forwardarrow.png")
        self.Bind(wx.EVT_BUTTON, self.parent.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.parent.OnNext, self.nextButton)

        navigationRow.Add(self.prevButton, 0, wx.CENTER)
        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.nextButton, 0, wx.CENTER)
        navigationRow.Add((5,5), 0)
        
        # finally the last row, with the header
        self.weekColumnHeader = wx.colheader.ColumnHeader(self)
        
        # turn this off for now, because our sizing needs to be exact
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_ProportionalResizing,False)
        headerLabels = ["Week", "S", "M", "T", "W", "T", "F", "S", "+"]
        for header in headerLabels:
            self.weekColumnHeader.AppendItem(header, wx.colheader.CH_JUST_Center, 5, bSortEnabled=False)
        self.Bind(wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnDayColumnSelect, self.weekColumnHeader)

        # set up initial selection
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_VisibleSelection,True)
        self.UpdateHeader()
        sizer.Add(self.weekColumnHeader, 0, wx.EXPAND)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
        self.Layout()

    def UpdateHeader(self):
        if self.parent.blockItem.dayMode:
            # ugly back-calculation of the previously selected day
            reldate = self.parent.blockItem.selectedDate - \
                      self.parent.blockItem.rangeStart
            self.weekColumnHeader.SetSelectedItem(reldate.days+1)
        else:
            self.weekColumnHeader.SetSelectedItem(0)

    def ResizeHeader(self):
        for (i,width) in enumerate(self.parent.columnWidths):
            self.weekColumnHeader.SetUIExtent(i, (0,width))

    def OnSize(self, event):
        self.ResizeHeader()
        event.Skip()
        
    def wxSynchronizeWidget(self):
        selectedDate = self.parent.blockItem.selectedDate
        startDate = self.parent.blockItem.rangeStart

        if (selectedDate == self.currentSelectedDate and
            startDate == self.currentStartDate):
            return

        # update the calendar with the calender's color
        self.colorSelect.SetColour(self.parent.blockItem.calendarData.eventColor.wxColor())

        # Update the month button given the selected date
        lastDate = startDate + timedelta(days=6)
        months = dateFormatSymbols.getMonths()
        if (startDate.month == lastDate.month):
            monthText = u"%s %d" %(months[selectedDate.month - 1],
                                   selectedDate.year)
        else:
            monthText = u"%s - %s %d" %(months[startDate.month - 1],
                                        months[lastDate.month - 1],
                                        lastDate.year)
     
        self.monthText.SetLabel(monthText)

        today = date.today()
        today = datetime(today.year, today.month, today.day)

        # ICU makes this list 1-based, 1st element is an empty string, so that
        # shortWeekdays[Calendar.SUNDAY] == 'short name for sunday'
        shortWeekdays = dateFormatSymbols.getShortWeekdays()
        firstDay = GregorianCalendar().getFirstDayOfWeek()

        for day in xrange(7):
            actualDay = ((day + firstDay - 1) % 7)
            currentDate = startDate + timedelta(days=day)
            if currentDate == today:
                dayName = "Today"
            else:
                dayName = u"%s %02d" %(shortWeekdays[actualDay + 1],
                                       currentDate.day)
            self.weekColumnHeader.SetLabelText(day+1, dayName)
            
        self.currentSelectedDate = selectedDate
        self.currentStartDate = startDate
        
        self.Layout()
        
    def OnDayColumnSelect(self, event):
        """
        dispatches to appropriate events in self.parent, 
        based on the column selected
        """
        
        colIndex = self.weekColumnHeader.GetSelectedItem()
        
        # column 0, week button
        if (colIndex == 0):
            return self.parent.OnWeekSelect()
            
        # last column, the "+" expand button
        # (this may change...)
        if (colIndex == 8):
            # re-fix selection so that the expand button doesn't stay selected
            self.UpdateHeader()
            return self.parent.OnExpand()
        
        # all other cases mean a day was selected
        # OnDaySelect takes a zero-based day, and our first day is in column 1
        return self.parent.OnDaySelect(colIndex-1)


class wxInPlaceEditor(wx.TextCtrl):
    def __init__(self, *arguments, **keywords):
        super(wxInPlaceEditor, self).__init__(style=wx.TE_PROCESS_ENTER | wx.NO_BORDER,
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
            self.item.displayName = self.GetValue()
        
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

        # GTK doesn't like making the editor taller than
        # the font, plus it doesn't honor the NOBORDER style
        # so we have to include 4 pixels for each border
        if '__WXGTK__' in wx.PlatformInfo:
            newSize.height = pointSize + 8

        font = wx.Font(pointSize, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        self.SetFont(font)

        # move the frame so that the default Mac Aqua focus "halo"
        # is aligned with the outer event frame
        if '__WXMAC__' in wx.PlatformInfo:
            position.x -= 4
            newSize.width += 4

        self.SetSize(newSize)
        self.Move(position)

        self.SetInsertionPointEnd()
        self.SetSelection(-1, -1)
        self.Show()
        self.SetFocus()

    def OnSize(self, event):
        self.Hide()
        event.Skip()

        
##############################################################################################################################################################################################################
################# new refactored classes under construction ###################
############# these have to move eventually, together for now #################

class CalendarContainer(ContainerBlocks.BoxContainer):

    selectedDate = schema.One(schema.DateTime)
    lastHue = schema.One(schema.Float, initialValue = -1.0)

    def __init__(self, *arguments, **keywords):
        super(CalendarContainer, self).__init__(*arguments, **keywords)

    def instantiateWidget(self):

        # REFACTOR: put all the drawing constant-like things from wxcalcon.OnInit here for now...
        self.scrollbarWidth = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X) #REFACTOR: where's this used?
        
        # This is where all the styles come from - eventually should probably
        # be moved up to the block
        if '__WXMAC__' in wx.PlatformInfo:
            
            bigFont = wx.Font(13, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            bigBoldFont = wx.Font(13, wx.NORMAL, wx.NORMAL, wx.BOLD)
            smallFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL,
                                face="Verdana")
            smallBoldFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD,
                                    face="Verdana")
        else:
            bigFont = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            bigBoldFont = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.BOLD)
            smallFont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL,
                                face="Verdana")
            smallBoldFont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD,
                                         face="Verdana")

        self.monthLabelFont = bigBoldFont
        self.monthLabelColor = wx.Colour(64, 64, 64)
        
        self.eventLabelFont = smallFont
        self.eventLabelColor = wx.BLACK
        
        self.eventTimeFont = smallBoldFont
        
        self.legendFont = bigFont
        self.legendColor = wx.Colour(128,128,128)

        self.bgColor = wx.WHITE

        self.majorLineColor = wx.Colour(204, 204, 204)
        self.minorLineColor = wx.Colour(229, 229, 229)
        
        self.majorLinePen = wx.Pen(self.majorLineColor)
        self.minorLinePen = wx.Pen(self.minorLineColor)
        self.selectionBrush = wx.Brush(wx.Colour(217, 217, 217)) # or 229?
        self.selectionPen = wx.Pen(wx.Colour(102,102,102))

#        self.Bind(wx.EVT_SIZE, self.OnSize) ## REFACTOR: from the old wx one.
#        hmmmmm.  probably dont need because old code did drawing calculations
#        here!
        
        # gradient cache
        self.brushes = DrawingUtilities.Gradients()


        ##............ OK, finally instantiate the widget .............
        
        w = super(CalendarContainer, self).instantiateWidget()

        # minimum 45 pixels per column REFACTOR: have to put it here since
        # we're using a generic widget (whatever BoxContainer gives us)
        w.SetMinSize((8*45, -1))

        return w

        
## REFACTOR: make a global singleton of this.  is this wise???
class wxVerticalSpacingInfo(object):
    def SetWidth(self, width):
        self.width = width
    def GetColumns(self):
        pass


## REFACTOR or maybe

## def CalculateColumnWidths(dayWidth, totalWidth):
##     """knows all the leftover space logic and stuff, can be called by anyone, returns tuple of widths for 9 columns"""
##     ### calculate column widths for the all-7-days week view case
##     # column layout rules are funky (e.g. bug 3290)
##     # - all 7 days are fixed at self.dayWidth
##     # - the last column (expando-button) is fixed
##     # - the "Week" column is the same as self.dayWidth, plus leftover pixels
##     dayWidths = (self.dayWidth,) * 7
    
##     middleWidth = self.dayWidth*7
##     xOffset = self.GetSize().width - self.middleWidth - self.scrollbarWidth
##     self.columnWidths = (self.xOffset,) +dayWidths+ (self.scrollbarWidth,)
    
##     pass
    
        

class AllDayEventsCanvas(Block.RectangularChild):
    """Currently, a very light wrapper around the widget"""
    calendarContainer = schema.One(schema.Item, required=True)

    def instantiateWidget(self):
        ## REFACTOR: more args for id etc.
        w = wxAllDayEventsCanvas(self.parentBlock.widget)
        return w

    def onSelectedDateChangedEvent(self, event):
        print "allday evt cvs  receives SDC"#, event
    def onSelectItemBroadcast(self, event):
        print "allday evt cvs  receives SIB"

class wxAllDayEventsCanvas(wx.StaticText):
    def __init__(self, parent, *args, **kwds):
        super(wxAllDayEventsCanvas, self).__init__(parent, -1, "AllDayEventsCanvas")
    def OnInit(self):
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeft)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRight)
    def OnLeft(self, event):
        print "allday evt cvs Left"
    def OnRight(self, event):
        print "allday evt cvs Right"


class TimedEventsCanvas(Block.RectangularChild):
    """Currently, a very light wrapper around the widget"""
    calendarContainer = schema.One(schema.Item, required=True)

    def instantiateWidget(self):
        w = wxTimedEventsCanvas(self.parentBlock.widget)
        return w

    def onSelectedDateChangedEvent(self, event):
        print "timed evt cvs  receives SDC"#, event
    def onSelectWeekEvent(self, event):
        print "timed evt cvs  receives SW"#, event
    def onSelectItemBroadcast(self, event):
        print "allday evt cvs  receives SIB", event

class wxTimedEventsCanvas(wx.StaticText):
    def __init__(self, parent, *args, **kwds):
        super(wxTimedEventsCanvas, self).__init__(parent, -1, "TimedEventsCanvas")
    def OnInit(self):
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeft)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRight)
    def OnLeft(self, event):
        print "timed evt cvs Left"
    def OnRight(self, event):
        print "timed evt cvs Right"
    
    
class CalendarControl(CalendarBlock): #Block.RectangularChild):

    # REFACTOR: how did these get set up in the first place in the old code?
    # the old wxcalcon did NOT have initialValues ...
    selectedDate = schema.One(schema.DateTime)
    dayMode = schema.One(schema.Boolean)  #, initialValue=True)
    daysPerView = schema.One(schema.Integer, initialValue=7) #REFACTOR should move to parcel.xml like old calcon

    def __init__(self, *arguments, **keywords):
        super(CalendarControl, self).__init__(*arguments, **keywords)

        
    def instantiateWidget(self):
        ## written by KCP in old CalendarContainer code, since we know instantiateWidget()
        ## is after this has been loaded by parcel.xml.  @@@ is onSetContentsEvent a
        ## better place to put it?  or better yet, some method that the calcon
        ## calls once all its children are instantiated (i've heard rumors
        ## there is such a method somewhere
        
        self.rangeIncrement = timedelta(days=7)

        self.dayMode = False
        self.setRange(self.startOfToday())

        w = wxCalendarControl(self.parentBlock.widget)
        return w

    def onSelectedDateChangedEvent(self, event):
        ## REFACTOR TODO: delete this method and use inherited from CalendarBlock
        print "cal ctrl receives SDC:"#, event
        self.setRange(event.arguments['start'])
        #print "cal ctrl after processing SDC: new \n\trangeStart=%s\n\tselDate=%s\n\trangeIncr=%s" %(self.rangeStart, self.selectedDate, self.rangeIncrement)

        self.widget.wxSynchronizeWidget()
        
    def onSelectWeekEvent(self, event):
        """i believe, as of now only calctrl sends SelectWeek events anyways.. but just in case..."""
        print "cal ctrl receives SW"
        self.dayMode = not event.arguments['doSelectWeek']
        self.widget.wxSynchronizeWidget()

    def setRange(self, date):
        """this version works over weeks, and it knows about self.dayMode"""
        print "cal ctrl setRange for",date
        #Set rangeStart
        if self.daysPerView == 7:
            # start at the beginning of the week (Sunday midnight)
            calendar = GregorianCalendar()
            calendar.setTime(date)
            
            delta = timedelta(days=(calendar.get(calendar.DAY_OF_WEEK) -
                                    calendar.getFirstDayOfWeek()))
            self.rangeStart = date - delta
        else:
            #always 7 days viewed with current design, should never get here
            #REFACTOR: should just eliminate daysPerView?
            assert False, "seems to be legacy code?"
            self.rangeStart = date

        #Set selectedDate.  if on week mode, sel'd date is always Sunday midnight.
        if self.dayMode:
            self.selectedDate = date
        else:
            self.selectedDate = self.rangeStart

#### should NOT be needed here since cal ctrl doesnt need to know about specific days...?
            
##     def GetCurrentDateRange(self):
##         """unlike CalendarBlock.GetCurrentDateRange(), need to check dayMode"""
##         if self.dayMode:
##             startDay = self.selectedDate
##             endDay = startDay + timedelta(days = 1)
##         else:
##             startDay = self.rangeStart
##             endDay = startDay + self.rangeIncrement
##         return (startDay, endDay)                   


class wxCalendarControl(wx.Panel, CalendarEventHandler):
##     def OnInit(self):
##         self.Bind(wx.EVT_LEFT_DOWN, self.OnLeft)
##         self.Bind(wx.EVT_RIGHT_DOWN, self.OnRight)
##     def OnLeft(self, event):
##         print "cal ctrl Left"
##     def OnRight(self, event):
##         print "cal ctrl Right"
    """This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons"""

    def __init__(self, *arguments, **keywords):
        super(wxCalendarControl, self).__init__(*arguments, **keywords)
        

    def OnInit(self):
        self.currentSelectedDate = None
        self.currentStartDate = None


        self.SetBackgroundColour( (255,255,255) )  #self.parent.bgColor) REFACTOR

        # Set up sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        navigationRow = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add((5,5), 0, wx.EXPAND)
        sizer.Add(navigationRow, 0, wx.EXPAND)
        sizer.Add((5,5), 0, wx.EXPAND)

        # beginnings of color in the calendar
        self.colorSelect = colourselect.ColourSelect(self, -1, size=wx.Size(30,15))
        self.Bind(colourselect.EVT_COLOURSELECT, self.OnSelectColor)
        navigationRow.Add((5,5), 0, wx.EXPAND)
        navigationRow.Add(self.colorSelect, 0, wx.CENTER)

        today = date.today()
        today = datetime(today.year, today.month, today.day)
        styles = self.blockItem.parentBlock

        self.monthText = wx.StaticText(self, -1)
        self.monthText.SetFont(styles.monthLabelFont)
        self.monthText.SetForegroundColour(styles.monthLabelColor)

        navigationRow.Add((0,0), 1)
        
        # add vertical margins above/below the month 
        monthSizer = wx.BoxSizer(wx.VERTICAL)
        monthSizer.Add((7,7),0)
        monthSizer.Add(self.monthText, 0)
        monthSizer.Add((5,5), 0)
        
        navigationRow.Add(monthSizer, 0, wx.ALIGN_CENTER)
        navigationRow.Add((0,0), 1)
        
        # top row - left/right buttons, anchored to the right
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "backarrow.png")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "forwardarrow.png")
        self.Bind(wx.EVT_BUTTON, self.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.OnNext, self.nextButton)

        navigationRow.Add(self.prevButton, 0, wx.CENTER)
        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.nextButton, 0, wx.CENTER)
        navigationRow.Add((5,5), 0)
        
        # finally the last row, with the header
        self.weekColumnHeader = wx.colheader.ColumnHeader(self)
        
        # turn this off for now, because our sizing needs to be exact
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_ProportionalResizing,False)
        headerLabels = ["Week", "S", "M", "T", "W", "T", "F", "S", "+"]
        for header in headerLabels:
            self.weekColumnHeader.AppendItem(header, wx.colheader.CH_JUST_Center, 5, bSortEnabled=False)
        self.Bind(wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnDayColumnSelect, self.weekColumnHeader)

        # set up initial selection
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_VisibleSelection,True)
        self.UpdateHeader()
        sizer.Add(self.weekColumnHeader, 0, wx.EXPAND)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
        self.Layout()

    def OnSelectColor(self, event):
        c = event.GetValue().Get()

        # REFACTOR
#        self.blockItem.setCalendarColor(c)
        
        # just cause a repaint - hopefully this cascades to child windows? REFACTOR: no more child windows!
        self.Refresh()

    def UpdateHeader(self):
        if self.blockItem.dayMode:
            # ugly back-calculation of the previously selected day
            reldate = self.blockItem.selectedDate - \
                      self.blockItem.rangeStart
            print "update header:",reldate.days+1
            self.weekColumnHeader.SetSelectedItem(reldate.days+1)
        else:
            self.weekColumnHeader.SetSelectedItem(0)

    def ResizeHeader(self):
        # REFACTOR: was
        #        for (i,width) in enumerate(self.parent.columnWidths):
        width = 50
        for i in range(8):
            self.weekColumnHeader.SetUIExtent(i, (0,width))

    def OnSize(self, event):
        self.ResizeHeader()
        event.Skip()
        
    def wxSynchronizeWidget(self):
        selectedDate = self.blockItem.selectedDate
        startDate = self.blockItem.rangeStart

        if (selectedDate == self.currentSelectedDate and
            startDate == self.currentStartDate):
            return

        # update the calendar with the calender's color  REFACTOR
#        self.colorSelect.SetColour(self.parent.blockItem.calendarData.eventColor.wxColor())

        # Update the month button given the selected date
        lastDate = startDate + timedelta(days=6)
        months = dateFormatSymbols.getMonths()
        if (startDate.month == lastDate.month):
            monthText = u"%s %d" %(months[selectedDate.month - 1],
                                   selectedDate.year)
        else:
            monthText = u"%s - %s %d" %(months[startDate.month - 1],
                                        months[lastDate.month - 1],
                                        lastDate.year)
     
        self.monthText.SetLabel(monthText)

        today = date.today()
        today = datetime(today.year, today.month, today.day)

        # ICU makes this list 1-based, 1st element is an empty string, so that
        # shortWeekdays[Calendar.SUNDAY] == 'short name for sunday'
        shortWeekdays = dateFormatSymbols.getShortWeekdays()
        firstDay = GregorianCalendar().getFirstDayOfWeek()

        for day in xrange(7):
            actualDay = ((day + firstDay - 1) % 7)
            currentDate = startDate + timedelta(days=day)
            if currentDate == today:
                dayName = "Today"
            else:
                dayName = u"%s %02d" %(shortWeekdays[actualDay + 1],
                                       currentDate.day)
            self.weekColumnHeader.SetLabelText(day+1, dayName)
            
        self.currentSelectedDate = selectedDate
        self.currentStartDate = startDate
        
        self.Layout()

        #REFACTOR: attempting to update correctly...
        self.UpdateHeader()
        self.weekColumnHeader.Refresh()
        self.Refresh()
        
    def OnDayColumnSelect(self, event):
        
        colIndex = self.weekColumnHeader.GetSelectedItem()
        
        # column 0, week button
        if (colIndex == 0):
            return self.OnWeekSelect()

        ### REFACTOR: this is under the chopping block...
##         # last column, the "+" expand button (this may change...)
        if (colIndex == 8):
            return False #@@@ whats the return value supposed to be??
        
##             # re-fix selection so that the expand button doesn't stay selected
##             self.UpdateHeader()
##             return self.parent.OnExpand()
        
        # all other cases mean a day was selected
        # OnDaySelect takes a zero-based day, and our first day is in column 1
        return self.OnDaySelect(colIndex-1)


    
    def OnDaySelect(self, day):
        """callback when a specific day is selected from column header.
        @param day: is 0-6"""
            
        startDate = self.blockItem.rangeStart
        selectedDate = startDate + timedelta(days=day)
        print "DAY SELECT: ", day, " for date:", selectedDate
        
        self.blockItem.postSelectWeek(False)
        self.blockItem.postDateChanged(selectedDate)

    def OnWeekSelect(self):
        """callback when the "week" button is clicked on column header."""
        #print "wx callback: OnWeekSelect"
        self.blockItem.postSelectWeek(True)
        self.blockItem.postDateChanged(self.blockItem.rangeStart)

