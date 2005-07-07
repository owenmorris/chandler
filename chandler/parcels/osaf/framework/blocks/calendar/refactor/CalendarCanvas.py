#### Under refactoring.
# enable by toggling comments in main/parcel.xml (SummaryCalendarViewRefactor)
# to do
#
#
# 1) figure out where to put drawing calculations
# 2) correct & dynamic spacing for CalendarControl
# 3) port over AllDayEventsCanvas to be a block
#   3.5 ?listen & send  SelectItemBroadcast's
# 4) port over TimedEventsCanvas to be a block
# 5) split off ColumnHeader out of CalendarControl
#

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

the composition of blocks is as follows
CalendarContainer  is the Block for the entire summary view
its children subblocks are as follows:

-------------------------------------------------------------
| wxCalendarControl - block: CalendarControl                                       
| [color selector]    June 2005                  <- ->      
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
            styles.calendarControl.getEventColors(item, selected)
        
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
        
        #styles.calendarControl is hacky
        gradientLeft, gradientRight, outlineColor, textColor = \
            styles.calendarControl.getEventColors(item, selected)
        
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

    @@@ move documentation out of docstrings to schema api .. it supports that
    right?
    
    @ivar rangeStart: beginning of the currently displayed range (persistent)
    @type rangeStart: datetime
    @ivar rangeIncrement: increment used to find the next or prev block of time
    @type rangeIncrement: timedelta

    @ivar selectedDate: within the current range.  REFACTOR: why is this in
    this class?  tons of the pre-refactor code used this variable though it was
    only declared in the subclass.  The rule is now:
    selectedDate = rangeStart for basic behavior, but selectedDate can range
    within the date range, e.g. when on a week view and you want to have a
    specific selected date inside that.

    @type selectedDate: datetime
    """
    # @@@ method capitalization policy is inconsistent!

    rangeStart = schema.One(schema.DateTime)
    rangeIncrement = schema.One(schema.TimeDelta)
    selectedDate = schema.One(schema.DateTime)
    lastHue = schema.One(schema.Float, initialValue = -1.0)
 
    def __init__(self, *arguments, **keywords):
        super(CalendarBlock, self).__init__(*arguments, **keywords)


        self.rangeIncrement = timedelta(days=7)
        self.dayMode = False
        self.setRange(self.startOfToday())


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
        """REFACTOR: what this was supposed to do is
                    "Sets the range to include the given date"
        but the old code didn't do that, and that's somewhat nontrivial: for a
        big rangeIncrement, what's rangeStart supposed to be? 

        this code's basic behavior works for the main cal canvases.  special case for week view.

        @param date: date to include
        @type date: datetime
        """

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
        self.editor = wxInPlaceEditor(self, -1) 
        
    def OnScroll(self, event):
        self.Refresh()
        event.Skip()

    def OnSelectItem(self, item):
        self.blockItem.postSelectItemBroadcast(item)

        # REFACTOR: dont know if this will work, yet
        # tell the sidebar to select the collection    that contains
        # this event - makes the sidebar track the "current" calendar
        # as well as update the gradients correctly
        coll = self.blockItem.getContainingCollection(item)
        if coll and coll != self.blockItem.contents.source.first():
            self.blockItem.SelectCollectionInSidebar(coll)
        #self.parent.wxSynchronizeWidget()
    
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
    calendarControl = schema.One(schema.Item, required=True)

    def __init__(self, *arguments, **keywords):
        super(CalendarContainer, self).__init__(*arguments, **keywords)

    def instantiateWidget(self):
        # This is where all the styles come from
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



        

class AllDayEventsCanvas(CalendarBlock):
    calendarContainer = schema.One(schema.Item, required=True)
    dayMode = schema.One(schema.Boolean, initialValue=False)

    def instantiateWidget(self):
        w = wxAllDayEventsCanvas(self.parentBlock.widget, Block.Block.getWidgetID(self))
        return w

    def onSelectWeekEvent(self, event):
## attempted optimization
##         newDayMode = not event.arguments['doSelectWeek']
##         areSame = bool(self.dayMode) == bool(newDayMode)
##         if areSame: return
        self.dayMode = not event.arguments['doSelectWeek']
        if self.dayMode:
            self.rangeIncrement = timedelta(days=1)
        else:
            self.rangeIncrement = timedelta(days=7)
        self.widget.wxSynchronizeWidget()

    def onSelectedDateChangedEvent(self, event):
        self.setRange(event.arguments['start'])
        self.widget.wxSynchronizeWidget()

    def onSelectItemBroadcast(self, event):
        print "allday evt cvs  receives SIB"
        self.selection = event.arguments['item'] #??? untested, this is the goal

class wxAllDayEventsCanvas(wxCalendarCanvas):
    def __init__(self, *arguments, **keywords):
        super (wxAllDayEventsCanvas, self).__init__ (*arguments, **keywords)

        self.SetMinSize((-1,25))
        self.size = self.GetSize()
        self.fixed = True

    def OnInit(self):
        super (wxAllDayEventsCanvas, self).OnInit()
        
        # Event handlers
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        self.size = self.GetSize()
        self.RebuildCanvasItems()
        
        self.Refresh()
        event.Skip()

    def wxSynchronizeWidget(self):
        self.RebuildCanvasItems()
        self.Refresh()

    def DrawBackground(self, dc):
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        
        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle(0, 0, self.size.width, self.size.height)

        self.DrawDayLines(dc)

        # Draw one extra line after the last day of the week,
        # to line up with the scrollbar below
        dc.DrawLine(self.size.width - drawInfo.scrollbarWidth, 0,
                    self.size.width - drawInfo.scrollbarWidth, self.size.height)

    def DrawCells(self, dc):
        
        styles = self.blockItem.calendarContainer

        dc.SetFont(styles.eventLabelFont)
        
        selectedBox = None
        brushOffset = self.GetPlatformBrushOffset()

        for canvasItem in self.canvasItemList:
            # save the selected box to be drawn last
            item = canvasItem.GetItem()
            if self.blockItem.selection is item:
                selectedBox = canvasItem
            else:
                canvasItem.Draw(dc, styles, brushOffset, False)
        
        if selectedBox:
            selectedBox.Draw(dc, styles, brushOffset, True)

        # Draw a line across the bottom of the header
        dc.SetPen(styles.majorLinePen)
        dc.DrawLine(0, self.size.height - 1,
                    self.size.width, self.size.height - 1)
        dc.DrawLine(0, self.size.height - 4,
                    self.size.width, self.size.height - 4)
        dc.SetPen(styles.minorLinePen)
        dc.DrawLine(0, self.size.height - 2,
                    self.size.width, self.size.height - 2)
        dc.DrawLine(0, self.size.height - 3,
                    self.size.width, self.size.height - 3)

    def RebuildCanvasItems(self):
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        self.canvasItemList = []

        if self.blockItem.dayMode:
            width = self.size.width - drawInfo.scrollbarWidth - drawInfo.xOffset
        else:
            width = drawInfo.dayWidth

        self.fullHeight = 0
        size = self.GetSize()
        for day in range(drawInfo.columns):
            currentDate = self.blockItem.rangeStart + timedelta(days=day)
            rect = wx.Rect((drawInfo.dayWidth * day) + drawInfo.xOffset, 0,
                           width, size.height)
            self.RebuildCanvasItemsByDay(currentDate, rect)

    def RebuildCanvasItemsByDay(self, date, rect):
        x = rect.x
        y = rect.y
        w = rect.width
        h = 15

        for item in self.blockItem.getDayItemsByDate(date):
            itemRect = wx.Rect(x, y, w, h)
            
            canvasItem = AllDayCanvasItem(itemRect, item)
            self.canvasItemList.append(canvasItem)
            
            # keep track of the current drag/resize box
            if self._currentDragBox and self._currentDragBox.GetItem() == item:
                self._currentDragBox = canvasItem

            y += itemRect.height
            
        if (y > self.fullHeight):
            self.fullHeight = y

    def getDateTimeFromPosition(self, position):
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        # bound the position by the available space that the user 
        # can see/scroll to
        yPosition = max(position.y, 0)
        xPosition = max(position.x, drawInfo.xOffset)
        
        if (self.fixed):
            height = self.GetMinSize().GetWidth()
        else:
            height = self.fullHeight
            
        yPosition = min(yPosition, height)
        d = drawInfo
        xPosition = min(xPosition, d.xOffset + d.dayWidth * d.columns - 1)

        if self.blockItem.dayMode:
            newDay = self.blockItem.rangeStart
        elif drawInfo.dayWidth > 0:
            deltaDays = (xPosition - drawInfo.xOffset) / drawInfo.dayWidth
            newDay = self.blockItem.rangeStart + timedelta(days=deltaDays)
        else:
            newDay = self.blockItem.rangeStart
        return newDay


    def OnCreateItem(self, unscrolledPosition):
        view = self.blockItem.itsView
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        event = Calendar.CalendarEvent(view=view)
        event.InitOutgoingAttributes()
        event.ChangeStart(datetime(newTime.year, newTime.month, newTime.day,
                                   event.startTime.hour,
                                   event.startTime.minute))
        event.endTime = event.startTime + timedelta(hours=1)
        event.allDay = True
        event.anyTime = False

        self.blockItem.contents.source.first().add(event)
        self.OnSelectItem(event)
        view.commit()
        return event

    def OnDraggingItem(self, unscrolledPosition):
        if self.blockItem.dayMode:
            return
        
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        item = self._currentDragBox.GetItem()
        if (newTime.toordinal() != item.startTime.toordinal()):
            item.ChangeStart(datetime(newTime.year, newTime.month, newTime.day,
                                      item.startTime.hour,
                                      item.startTime.minute))
            self.Refresh()

    def OnEditItem(self, box):
        position = box.GetEditorPosition()
        size = box.GetMaxEditorSize()

        self.editor.SetItem(box.GetItem(), position, size, size.height)





class TimedEventsCanvas(CalendarBlock):
    calendarContainer = schema.One(schema.Item, required=True)
    dayMode = schema.One(schema.Boolean)

    def instantiateWidget(self):
        w = wxTimedEventsCanvas(self.parentBlock.widget)
        return w

    def onSelectWeekEvent(self, event):
## attempted optimization
##         newDayMode = not event.arguments['doSelectWeek']
##         areSame = bool(self.dayMode) == bool(newDayMode)
##         if areSame: return
        self.dayMode = not event.arguments['doSelectWeek']
        if self.dayMode:
            self.rangeIncrement = timedelta(days=1)
        else:
            self.rangeIncrement = timedelta(days=7)
        self.widget.wxSynchronizeWidget()

    def onSelectedDateChangedEvent(self, event):
        self.setRange(event.arguments['start'])
        self.widget.wxSynchronizeWidget()

    def onSelectItemBroadcast(self, event):
        print "timed evt cvs  receives SIB"
        # TODO: copy from AllDay the final code there

class wxTimedEventsCanvas(wxCalendarCanvas):
    def __init__(self, parent, *arguments, **keywords):
        super(wxTimedEventsCanvas, self).__init__(parent, *arguments, **keywords)

        # @@@ rationalize drawing calculations...
        self.hourHeight = 40
        
        self._scrollYRate = 10
        
        self._bgSelectionStartTime = None
        self._bgSelectionEndTime = None
        
        # determines if we're dragging the start or the end of an event, usually
        # the end
        self._bgSelectionDragEnd = True

        self.size = self.GetSize()
        self.size.width -= wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
        self.size.height = self.hourHeight * 24
        self.SetVirtualSize(self.size)

    def wxSynchronizeWidget(self):
        self._doDrawingCalculations()
        self.RebuildCanvasItems()
        self.Refresh()

    def OnSize(self, event):
        self._doDrawingCalculations()
        self.RebuildCanvasItems()
        self.Refresh()


    def OnInit(self):
        super (wxTimedEventsCanvas, self).OnInit()
        
        self.SetScrollRate(0, self._scrollYRate)
        self.Scroll(0, (self.hourHeight*7)/self._scrollYRate)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

    def ScaledScroll(self, dx, dy):
        (scrollX, scrollY) = self.CalcUnscrolledPosition(0,0)
        scrollX += dx
        scrollY += dy
        
        # rounding ensures we scroll at least one unit
        if dy < 0:
            rounding = -self._scrollYRate
        else:
            rounding = self._scrollYRate

        scaledY = (scrollY // self._scrollYRate) + rounding
        self.Scroll(scrollX, scaledY)
        
    def _doDrawingCalculations(self):

        # @@@ magic numbers

        # FIXME: on wxPython-Mac v2.6.0, this returns negative and otherwise bogus dimension values: e.g., [-15, 960]
        #self.size = self.GetVirtualSize()
        self.size = self.GetSize()
        self.size.width -= wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
        self.size.height = self.hourHeight * 24
        self.SetVirtualSize(self.size)

        self.dayHeight = self.hourHeight * 24

        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        self.xOffset = drawInfo.xOffset

        if self.blockItem.dayMode:
            self.dayWidth = drawInfo.middleWidth
        else:
            self.dayWidth = drawInfo.dayWidth
    
    @staticmethod
    def GetLocaleHourStrings(hourrange):
        """
        use PyICU to format the hour, because some locales
        use a 24 hour clock
        """
        timeFormatter = DateFormat.createTimeInstance()
        hourFP = FieldPosition(DateFormat.HOUR1_FIELD)
        dummyDate = date.today()
        
        for hour in hourrange:
            hourdate = datetime.combine(dummyDate, time(hour))
            timeString = timeFormatter.format(hourdate, hourFP)
            (start, end) = (hourFP.getBeginIndex(),hourFP.getEndIndex())
            hourString = str(timeString)[start:end]
            yield hour, hourString

    def DrawBackground(self, dc):
        styles = self.blockItem.calendarContainer
        self._doDrawingCalculations()

        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)

        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle(0, 0, self.size.width, self.size.height + 10)

        # Set text properties for legend
        dc.SetTextForeground(styles.legendColor)
        dc.SetFont(styles.legendFont)

        # Draw the lines separating hours
        halfHourHeight = self.hourHeight/2

        # we'll need these for hour formatting
        for hour,hourString in self.GetLocaleHourStrings(range(24)):

            if hour > 0:
                # Draw the hour legend
                wText, hText = dc.GetTextExtent(hourString)
                dc.DrawText(hourString,
                            self.xOffset - wText - 5,
                            hour * self.hourHeight - (hText/2))
            
            # Draw the line between hours
            dc.SetPen(styles.majorLinePen)
            dc.DrawLine(self.xOffset,
                        hour * self.hourHeight,
                        self.size.width,
                        hour * self.hourHeight)

            # Draw the line between half hours
            dc.SetPen(styles.minorLinePen)
            dc.DrawLine(self.xOffset,
                        hour * self.hourHeight + halfHourHeight,
                        self.size.width,
                        hour * self.hourHeight + halfHourHeight)

        self.DrawDayLines(dc)
        
        legendBorderX = self.xOffset - self.legendBorderWidth/2
        pen = wx.Pen(styles.legendColor, self.legendBorderWidth)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)
        
        # hardcode this for now - eventually this should be a preference
        workdayHourStart = 9 # 9am
        workdayHourEnd = 17  # 5pm
        
        dc.DrawLine(legendBorderX, workdayHourStart*self.hourHeight,
                    legendBorderX, workdayHourEnd * self.hourHeight + 1)

        """
        # draw lines between columns
        dc.SetPen(styles.minorLinePen)
        for day in xrange(1, self.parent.columns):
            dc.DrawLine(self.xOffset + (self.dayWidth * day), 0,
                        self.xOffset + (self.dayWidth * day), self.size.height)
        """

        # draw selection stuff
        if (self._bgSelectionStartTime and self._bgSelectionEndTime):
            dc.SetPen(styles.majorLinePen)
            dc.SetBrush(styles.selectionBrush)
            
            rects = \
                TimedCanvasItem.GenerateBoundsRects(self,
                                                       self._bgSelectionStartTime,
                                                       self._bgSelectionEndTime)
            for rect in rects:
                dc.DrawRectangleRect(rect)

    @staticmethod
    def sortByStartTime(item1, item2):
        """
        Comparison function for sorting, mostly by start time
        """
        dateResult = cmp(item1.startTime, item2.startTime)
        
        # when two items start at the same time, we actually want to show the
        # SHORTER event last, so that painting draws it on top
        if dateResult == 0:
            dateResult = cmp(item2.endTime, item1.endTime)
        return dateResult

    def RebuildCanvasItems(self):
        
        self.canvasItemList = []

        (startDay, endDay) = self.GetCurrentDateRange()
        
        # we sort the items so that when drawn, the later events are drawn last
        # so that we get proper stacking
        visibleItems = list(self.blockItem.getItemsInRange(startDay, endDay))
        visibleItems.sort(self.sortByStartTime)
                
        
        # First generate a sorted list of TimedCanvasItems
        for item in visibleItems:
                                               
            canvasItem = TimedCanvasItem(item, self)
            self.canvasItemList.append(canvasItem)

            if self._currentDragBox and self._currentDragBox.GetItem() == item:
                self._currentDragBox = canvasItem                

        # now generate conflict info
        self.CheckConflicts()
        
        for canvasItem in self.canvasItemList:
            # drawing rects should be updated to reflect conflicts
            canvasItem.UpdateDrawingRects()
            
        # canvasItemList has to be sorted by depth
        # should be relatively quick because the canvasItemList is already
        # sorted by startTime. If no conflicts, this is an O(n) operation
        # (note that as of Python 2.4, sorts are stable, so this remains safe)
        self.canvasItemList.sort(key=TimedCanvasItem.GetIndentLevel)
        
    def DrawCells(self, dc):
        styles = self.blockItem.calendarContainer
        
        # Set up fonts and brushes for drawing the events
        dc.SetTextForeground(wx.BLACK)
        dc.SetBrush(wx.WHITE_BRUSH)

        selectedBox = None        
        # finally, draw the items
        boundingRect = wx.Rect(self.xOffset, 0, self.size.width, self.size.height)
        brushOffset = self.GetPlatformBrushOffset()
        for canvasItem in self.canvasItemList:

            item = canvasItem.GetItem()
            
            # save the selected box to be drawn last
            if self.blockItem.selection is item:
                selectedBox = canvasItem
            else:
                canvasItem.Draw(dc, boundingRect, styles,  brushOffset, False)
            
        # now draw the current item on top of everything else
        if selectedBox:
            selectedBox.Draw(dc, boundingRect, styles, brushOffset, True)

    def CheckConflicts(self):
        for itemIndex, canvasItem in enumerate(self.canvasItemList):
            # since these are sorted, we only have to check the items 
            # that come after the current one
            for innerItem in self.canvasItemList[itemIndex+1:]:
                # we know we're done when we stop hitting conflicts
                # 
                # have a guarantee that innerItem.startTime >= item.endTime
                # Since item.endTime < item.startTime, we know we're
                # done
                if innerItem.GetItem().startTime >= canvasItem.GetItem().endTime: break
                
                # item and innerItem MUST conflict now
                canvasItem.AddConflict(innerItem)
            
            # we've now found all conflicts for item, do we need to calculate
            # depth or anything?
            # first theory: leaf children have a maximum conflict depth?
            canvasItem.CalculateConflictDepth()

    def OnKeyPressed(self, event):
        # create an event here - unfortunately the panel can't get focus, so it
        # can't recieve keystrokes yet...
        pass
            
    # handle mouse related actions: move, resize, create, select
    
    def OnSelectItem(self, item):
        if item:
            # clear background selection when an existing item is selected
            self._bgSelectionStartTime = self._bgSelectionEndTime = None
        
        super(wxTimedEventsCanvas, self).OnSelectItem(item)
        
    def OnSelectNone(self, unscrolledPosition):
        selectedTime = self.getDateTimeFromPosition(unscrolledPosition)
        
        # only select something new if there's no existing selection, or if 
        # we're outside of an existing selection
        if (not self._bgSelectionStartTime or
            selectedTime < self._bgSelectionStartTime or
            selectedTime > self._bgSelectionEndTime):
            self._bgSelectionStartTime = self.getDateTimeFromPosition(unscrolledPosition)
            self._bgSelectionDragEnd = True
            self._bgSelectionEndTime = self._bgSelectionStartTime + \
                timedelta(hours=1)

        # set focus on the calendar so that we can receive key events
        # (as of this writing, wxPanel can't receive focus, so this is a no-op)
        self.SetFocus()
        super(wxTimedEventsCanvas, self).OnSelectNone(unscrolledPosition)

    def OnEditItem(self, box):
        styles = self.blockItem.calendarContainer
        position = self.CalcScrolledPosition(box.GetEditorPosition())
        size = box.GetMaxEditorSize()

        textPos = wx.Point(position.x + 8, position.y + 15)
        textSize = wx.Size(size.width - 13, size.height - 20)

        self.editor.SetItem(box.GetItem(), textPos, textSize, styles.eventLabelFont.GetPointSize()) 

    def OnCreateItem(self, unscrolledPosition):
        # @@@ this code might want to live somewhere else, refactored
        view = self.blockItem.itsView
        event = Calendar.CalendarEvent(view=view)
        
        # if a region is selected, then use that for the event span
        if (self._bgSelectionStartTime):
            newTime = self._bgSelectionStartTime
            duration = self._bgSelectionEndTime - self._bgSelectionStartTime
        else:
            newTime = self.getDateTimeFromPosition(unscrolledPosition)
            duration = timedelta(hours=1)
            
        event.InitOutgoingAttributes()
        event.ChangeStart(newTime)
        event.allDay = False
        event.anyTime = False
        event.duration = duration

        # ugh, this is a hack to work around the whole ItemCollection stuff
        # see bug 2749 for some background
        self.blockItem.contents.source.first().add(event)
        
        self.OnSelectItem(event)

        # @@@ Bug#1854 currently this is too slow,
        # and the event causes flicker
        #view.commit()
        canvasItem = TimedCanvasItem(event, self)
        
        # only problem here is that we haven't checked for conflicts
        canvasItem.UpdateDrawingRects()
        canvasItem.SetResizeMode(canvasItem.RESIZE_MODE_END)
        return canvasItem
        
    def OnBeginResizeItem(self):
        self._lastUnscrolledPosition = self._dragStartUnscrolled
        self.StartDragTimer()
        pass
        
    def OnEndResizeItem(self):
        self.StopDragTimer()
        self._originalDragBox.ResetResizeMode()
        pass
        
    def OnResizingItem(self, unscrolledPosition):
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        item = self._currentDragBox.GetItem()
        resizeMode = self.GetResizeMode()
        delta = timedelta(minutes=15)
        
        # make sure we're changing by at least delta 
        if (resizeMode == TimedCanvasItem.RESIZE_MODE_END and 
            newTime > (item.startTime + delta)):
            item.endTime = newTime
        elif (resizeMode == TimedCanvasItem.RESIZE_MODE_START and 
              newTime < (item.endTime - delta)):
            item.startTime = newTime
        self.Refresh()
    
    def OnDragTimer(self):
        """
        This timer goes off while we're dragging/resizing
        """
        scrolledPosition = self.CalcScrolledPosition(self._dragCurrentUnscrolled)
        self.ScrollIntoView(scrolledPosition)
    
    def StartDragTimer(self):
        self.scrollTimer = ClosureTimer(self.OnDragTimer)
        self.scrollTimer.Start(100, wx.TIMER_CONTINUOUS)
    
    def StopDragTimer(self):
        self.scrollTimer.Stop()
        self.scrollTimer = None
        
    def OnBeginDragItem(self):
        self.StartDragTimer()
        pass
        
    def OnEndDragItem(self):
        self.StopDragTimer()
        pass
        
    def OnDraggingNone(self, unscrolledPosition):
        dragDateTime = self.getDateTimeFromPosition(unscrolledPosition)
        if self._bgSelectionDragEnd:
            self._bgSelectionEndTime = dragDateTime
        else:
            self._bgSelectionStartTime = dragDateTime
            
        if (self._bgSelectionEndTime < self._bgSelectionStartTime):
            # swap values, drag the other end
            self._bgSelectionDragEnd = not self._bgSelectionDragEnd
            (self._bgSelectionStartTime, self._bgSelectionEndTime) = \
                (self._bgSelectionEndTime, self._bgSelectionStartTime)
        self.Refresh()
            
        
    def OnDraggingItem(self, unscrolledPosition):
        # at the start of the drag, the mouse was somewhere inside the
        # dragbox, but not necessarily exactly at x,y
        #
        # so account for the original offset within the ORIGINAL dragbox so the 
        # mouse cursor stays in the same place relative to the original box
        
        # We need to figure out where the original drag started,
        # so the mouse stays in the same position relative to
        # the origin of the item
        (boxX,boxY) = self._originalDragBox.GetDragOrigin()
        dy = self._dragStartUnscrolled.y - boxY
        
        # dx is tricky: we want the user to be able to drag left/right within
        # the confines of the current day, but if they cross a day threshold,
        # then we want to shift the whole event over one day
        # to do this, we need to round dx to the nearest dayWidth
        dx = self._dragStartUnscrolled.x - boxX
        dx = int(dx/self.dayWidth) * self.dayWidth
        position = wx.Point(unscrolledPosition.x - dx, unscrolledPosition.y - dy)
        
        newTime = self.getDateTimeFromPosition(position)
        item = self._currentDragBox.GetItem()
        if ((newTime.toordinal() != item.startTime.toordinal()) or
            (newTime.hour != item.startTime.hour) or
            (newTime.minute != item.startTime.minute)):
            item.ChangeStart(newTime)
            self.RebuildCanvasItems()
            
            # this extra paint is actually unnecessary because ContainerBlock is
            # giving us too many paints on a drag anyway. Why? hmm.
            #self.Refresh()

    def GetResizeMode(self):
        """
        Helper method for drags
        """
        return self._originalDragBox.getResizeMode(self._dragStartUnscrolled)

    def getDateTimeFromPosition(self, position):
        #that is, the drawing info not already within this object
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        # bound the position by the available space that the user 
        # can see/scroll to
        yPosition = max(position.y, 0)
        xPosition = max(position.x, self.xOffset)
        
        yPosition = min(yPosition, self.hourHeight * 24 - 1)
        xPosition = min(xPosition, self.xOffset + self.dayWidth * drawInfo.columns - 1)
        
        (startDay, endDay) = self.GetCurrentDateRange()

        # @@@ fixes Bug#1831, but doesn't really address the root cause
        # (the window is drawn with (0,0) virtual size on mac)
        if self.dayWidth > 0:
            deltaDays = (xPosition - self.xOffset) / self.dayWidth
        else:
            deltaDays = 0
        
        deltaHours = yPosition / self.hourHeight
        deltaMinutes = ((yPosition % self.hourHeight) * 60) / self.hourHeight
        deltaMinutes = int(deltaMinutes/15) * 15
        newTime = startDay + timedelta(days=deltaDays,
                                       hours=deltaHours,
                                       minutes=deltaMinutes)
        return newTime

    def getPositionFromDateTime(self, datetime):
        (startDay, endDay) = self.GetCurrentDateRange()
        
        if datetime < startDay or \
           datetime > endDay:
            raise ValueError, "Must be visible on the calendar"
            
        delta = datetime - startDay
        x = (self.dayWidth * delta.days) + self.xOffset
        y = int(self.hourHeight * (datetime.hour + datetime.minute/float(60)))
        return wx.Point(x, y)

    
class CalendarControl(CalendarBlock):

    ## TODO: integrate alecf's r5851 widget changes

    dayMode = schema.One(schema.Boolean)
    daysPerView = schema.One(schema.Integer, initialValue=7) #REFACTOR should move to parcel.xml like old calcon
    calendarContainer = schema.One(schema.Item)

    def __init__(self, *arguments, **keywords):
        super(CalendarControl, self).__init__(*arguments, **keywords)

        
    def instantiateWidget(self):
        ## written by KCP in old CalendarContainer code, since we know instantiateWidget()
        ## is after this has been loaded by parcel.xml.  @@@ is onSetContentsEvent a
        ## better place to put it?  or better yet, some method that the calcon
        ## calls once all its children are instantiated (is there such a method
        ## somewhere?)
        

        w = wxCalendarControl(self.parentBlock.widget, Block.Block.getWidgetID(self))
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

        #Set rangeStart
        # start at the beginning of the week (Sunday midnight)
        # code currently DUPLICATED with CalendarBlock.setRange()
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

#### REFACTOR should NOT be needed here since cal ctrl doesnt need to know about specific days...?
            
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
    """This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons"""

    def __init__(self, *arguments, **keywords):
        super(wxCalendarControl, self).__init__(*arguments, **keywords)
        

    def OnInit(self):
        self.currentSelectedDate = None
        self.currentStartDate = None

        self.SetBackgroundColour(self.blockItem.parentBlock.bgColor)
        self.SetMaxSize((-1, 80)) 

        # Set up sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        navigationRow = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add((7,7), 0, wx.EXPAND)
        sizer.Add(navigationRow, 0, wx.EXPAND)
        sizer.Add((5,5), 0, wx.EXPAND)

        # beginnings of color in the calendar
        self.colorSelect = colourselect.ColourSelect(self, -1, size=wx.Size(30,15))
        self.Bind(colourselect.EVT_COLOURSELECT, self.OnSelectColor)
        navigationRow.Add((7,7), 0, wx.EXPAND)
        navigationRow.Add(self.colorSelect, 0, wx.ALIGN_CENTER)

        today = date.today()
        today = datetime(today.year, today.month, today.day)
        styles = self.blockItem.calendarContainer

        self.monthText = wx.StaticText(self, -1)
        self.monthText.SetFont(styles.monthLabelFont)
        self.monthText.SetForegroundColour(styles.monthLabelColor)

        navigationRow.Add((0,0), 1)

        navigationRow.Add(self.monthText, 0, wx.ALIGN_CENTER)
        
        navigationRow.Add((0,0), 1)
        
        # top row - left/right buttons, anchored to the right
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "backarrow.png")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "forwardarrow.png")
        self.Bind(wx.EVT_BUTTON, self.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.OnNext, self.nextButton)

        navigationRow.Add(self.prevButton, 0, wx.ALIGN_CENTER)
        
        
        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.nextButton, 0, wx.ALIGN_CENTER)
        navigationRow.Add((7,7), 0)
        
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

        self._doDrawingCalculations() #hopefully this is early enough

    def OnSelectColor(self, event):
        c = event.GetValue().Get()

        # REFACTOR.  a new CPIA event?  each canvas tracks its own color currently
#        self.blockItem.setCalendarColor(c)
        
        # REFACTOR: need to tell canvases to Refresh()
        self.Refresh()

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

        # the old "+" sign column now should do nothing when clicked...
        if (colIndex == 8):
            return False #@@@ whats the return value supposed to be??
        
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
        

        #print self.size, self.xOffset, self.dayWidth, self.columns #convenient interactive way to learn what these variables are, since they're tricky to describe verbally

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

