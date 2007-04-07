#   Copyright (c) 2004-2006 Open Source Applications Foundation
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
Canvas for calendaring blocks.
"""

__parcel__ = "osaf.framework.blocks.calendar"

import wx
import wx.colheader

from osaf.pim import isDead
from repository.item.Monitors import Monitors
from repository.item.Item import MissingClass
from chandlerdb.item.ItemError import NoSuchItemInCollectionError

from datetime import datetime, timedelta, date, time
from PyICU import GregorianCalendar, DateFormatSymbols, ICUtzinfo, TimeZone

from osaf.pim.calendar import (Calendar, TimeZoneInfo, formatTime, DateTimeUtil,
                               shortTZ)
from osaf.pim import ContentCollection, has_stamp
from osaf.usercollections import UserCollection
from application.dialogs import RecurrenceDialog, Util, TimeZoneList

from osaf.sharing import ChooseFormat, CalDAVFreeBusyConduit, FreeBusyAnnotation

from osaf.framework.blocks import (
    DragAndDrop, Block, SplitterWindow, Styles, BoxContainer, BlockEvent, ViewEvent
    )
from osaf.framework.attributeEditors import AttributeEditors
from osaf.framework.blocks.DrawingUtilities import (DrawWrappedText, Gradients,
                DrawClippedText, color2rgb, rgb2color, vector)

from osaf.framework.blocks.calendar import CollectionCanvas
from osaf.preferences import CalendarHourMode, CalendarPrefs

from colorsys import rgb_to_hsv, hsv_to_rgb

from application import schema

from operator import add
from itertools import islice, chain
from bisect import bisect
import copy
import logging
from application import styles as confstyles
from application.Application import registerStringForId, unregisterStringForId

from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

dateFormatSymbols = DateFormatSymbols()

# On Mac and Linux, origins for painting gradients have been
# offset at one time or another.  Most recently Linux was
# having problems, but now Linux appears to be working correctly,
# so the code enabled by ENABLE_DEVICE_ORIGIN isn't currently
# used on any platform
ENABLE_DEVICE_ORIGIN = False

NORMAL_RADIUS   = 6
ONE_LINE_RADIUS = 8

SWATCH_HEIGHT = 5 # not counting border
SWATCH_WIDTH  = 3 # not counting border
SWATCH_BORDER = 1
SWATCH_SEPARATION = 2

SWATCH_WIDTH_VECTOR  = vector([SWATCH_WIDTH  + 2*SWATCH_BORDER, 0])
SWATCH_HEIGHT_VECTOR = vector([0, SWATCH_HEIGHT + 2*SWATCH_BORDER])

IS_MAC = '__WXMAC__' in wx.PlatformInfo
IS_GTK = '__WXGTK__' in wx.PlatformInfo
    
# add some space below the time (but on linux there isn't any room)
if '__WXGTK__' in wx.PlatformInfo:
    TIME_BOTTOM_MARGIN = 0
else:
    TIME_BOTTOM_MARGIN = 2

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
# | <--> June 2005                  [timezone] 
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
    Round down v to the nearest r.
    """
    return (v/r)*r

def roundToColumnPosition(v, columnList):
    """
    Round down to the nearest column value.
    """
    index = bisect(columnList, v)-1
    if index >= 0:
        return columnList[index]
    elif v < 0:
        return columnList[0]
    else:
        return columnList[-1]

def widgetGuardedCallback(block, function):
    """Call callback function only if the given object has a widget."""
    def callback():
        if getattr(block, 'widget', None) is not None:
            function()
    return callback

# hue -> colorName mapping
hueMap = dict((int(v), k) for k, v in confstyles.cfg.items('colors'))
suffixes = 'GradientLeft', 'GradientRight', 'Outline', 'Text'
colorCache = {}

def colorValWithDefault(hue, name):
    try:
        return colorCache[str(hue) + name]
    except KeyError:
        hueDegrees = int(hue*360)
        hueName = hueMap.get(hueDegrees)
        if hueName is None:
            # int rounds floats down, try rounding up
            hueName = hueMap.get(hueDegrees + 1)
        if hueName is not None:
            val = confstyles.cfg.get('calendarcanvas', hueName + name)
            if val is not None:
                ret = float(val)
                colorCache[str(hue) + name] = ret
                return ret
        ret = confstyles.cfg.getfloat('calendarcanvas', name)
        colorCache[str(hue) + name] = ret
        return ret

def getLozengeTypeColor(hue, lozengeType):
    return rgb2color(*hsv_to_rgb(hue,
                        colorValWithDefault(hue, lozengeType + 'Saturation'),
                        colorValWithDefault(hue, lozengeType + 'Value'))
                     )

def getHueForCollection(collection):
    color = UserCollection(collection).ensureColor().color
    return rgb_to_hsv(*color2rgb(color.red,color.green,color.blue))[0]

class ColorInfo(object):
    saturatedColorsCache = {}
    
    def __init__(self, collection):
        # sometimes this happens when getContainingCollection fails to find a collection
        assert collection is not None, "Can't get color for None"
        self.hue = getHueForCollection(collection)
    
    def getColorsProperty(prefix):
        """
        takes HSV 'S' and 'V' from conf files, hue from self, returns a tuple of
        four RGB colors.
        
        """
        def getSaturatedColors(self):
            try:
                return ColorInfo.saturatedColorsCache[str(self.hue) + prefix]
            except KeyError:
                names = [prefix + suffix for suffix in suffixes]    
                ret = [getLozengeTypeColor(self.hue, name) for name in names]
                ColorInfo.saturatedColorsCache[str(self.hue) + prefix] = ret
                return ret

        return property(getSaturatedColors)
    
    defaultColors     = getColorsProperty('UnSelected')
    selectedColors    = getColorsProperty('Selected')
    visibleColors     = getColorsProperty('Overlay')
    defaultFYIColors  = getColorsProperty('UnSelectedFYI')
    selectedFYIColors = getColorsProperty('SelectedFYI')
    visibleFYIColors  = getColorsProperty('OverlayFYI')


# wrapper around 
class CalendarSelection(schema.Annotation):
    """
    Wrapper around ContentCollection to provide specialized knowledge
    about selection of recurrence.

    Recurring items don't appear in the current collection, only the
    master events do. This means that we have to build a separate
    container (self.selectedOccurrences) just for recurring items that
    are selected.

    Then we can just treat selection as the union between the
    ContentCollection (in self.itsItem) and the list of occurrences.
    """

    schema.kindInfo(annotates=ContentCollection)
    selectedOccurrences = schema.Many(schema.Item, defaultValue=set())

    def delegated(method):
        """
        Method decorator that delegates method calls
        with the same name, rather than call the function.
        """

        def ActualMethod(self, item):
            if item.hasTrueAttributeValue(Calendar.EventStamp.occurrenceFor.name):
                return method(self, item)
            else:
                # call an identically named function in the outer
                # (annotated) item
                methodName = method.__name__
                unboundMethod = getattr(type(self.itsItem), methodName)
                return unboundMethod(self.itsItem, item)

        return ActualMethod

    def __getattr__(self, name):
        return getattr(self.itsItem, name)

    # these mimic the behavior of the collection

    # first, delegated methods
    @delegated
    def __contains__(self, item):
        return self.itsItem.__contains__(Calendar.EventStamp(item).getMaster().itsItem)

    @delegated
    def isItemSelected(self, item):
        return item in self.selectedOccurrences

    @delegated
    def selectItem(self, item):
        self.selectedOccurrences.add(item)

    @delegated
    def unselectItem(self, item):
        self.selectedOccurrences.remove(item)

    def setSelectionToItem(self, item):
        if item.hasTrueAttributeValue(Calendar.EventStamp.recurrenceID.name):
            self.itsItem.clearSelection()
            self.selectedOccurrences = set((item,))
        else:
            self.selectedOccurrences = set()
            self.itsItem.setSelectionToItem(item)
            
    def isSelectionEmpty(self):
        if not self.itsItem.isSelectionEmpty():
            return False

        for item in self.selectedOccurrences:
            if not isDead(item):
                return False

        return True
    
    def iterSelection(self):
        for item in self.selectedOccurrences:
            if not isDead(item):
                # we could remove Nones and itemrefs, but to do that we'd
                # have to create a separate list (can't remove from a set while
                # iterating it), and that wouldn't be compatible with being a
                # generator, so for now (till recurrence selection changes)
                # just ignore bogus refs, they'll get deleted the next time
                # selection changes
                yield item
        for item in self.itsItem.iterSelection():
            yield item

    def clearSelection(self):
        self.itsItem.clearSelection()
        self.selectedOccurrences = set()

zero_delta = timedelta(0)

class CalendarCanvasItem(CollectionCanvas.CanvasItem):
    """
    Base class for calendar items. Covers:
     - editor position & size
     - text wrapping
    """

    timeHeight = 0

    def __init__(self, collection, primaryCollection, bounds, item, *args, **keywords):
        super(CalendarCanvasItem, self).__init__(bounds, item, *args, **keywords)

        self.textOffset = wx.Point(self.textMargin + NORMAL_RADIUS / 2,
                                   self.textMargin + 1)

        # use PyICU to pre-cache the time string
        self.timeString = formatTime(self.event.startTime, noTZ=True)

        self.colorInfo = ColorInfo(collection)
        
        self.collection = collection
        self.primaryCollection = primaryCollection

        pim_ns = schema.ns('osaf.pim', collection.itsView)
        self.ignoreCollections =  [pim_ns.allCollection, pim_ns.inCollection,
                                   pim_ns.outCollection]
        

        self.isActive = primaryCollection is collection

    def GetEditorPosition(self):
        """
        This returns a location to show the editor. By default it is
        the same as the default bounding box.
        """
        position = self.GetBoundsRects()[0].GetPosition() + self.textOffset

        # now offset to account for the time
        position += (0, self.timeHeight + 1)
        return position

    def GetMaxEditorSize(self):
        size = self.GetBoundsRects()[0].GetSize()

        # now offset to account for the time	
        size -= (12, self.timeHeight + self.textMargin*2 + 3)
        return size

    def invertColors(self):
        return (self.anyOrZero() or self.event.transparency == 'fyi')
    
    def dashedLine(self):
        return self.event.transparency == 'tentative'
    
    def anyOrZero(self):
        event = self.event
        return ((event.anyTime or event.duration == zero_delta)
                 and not event.allDay)
        
    
    
    def getEventColors(self, selected):
        """
        Returns the appropriate tuple of selected, normal, and visible colors.
        """
        if self.invertColors():
            if selected:
                return self.colorInfo.selectedFYIColors
            elif self.isActive:
                return self.colorInfo.defaultFYIColors
    
            return self.colorInfo.visibleFYIColors
        else:
            if selected:
                return self.colorInfo.selectedColors
            elif self.isActive:
                return self.colorInfo.defaultColors
    
            return self.colorInfo.visibleColors
            
    @staticmethod
    def FindFirstGapInSequence(seq):
        """
        Look for the first gap in a sequence - for instance::
          0,2,3: choose 1
          1,2,3: choose 0
          0,1,2: choose 3        
        """
        if not seq: return 0

        for index, value in enumerate(sorted(seq)):
            if index != value:
                return index

        # didn't find any gaps, so just put it one higher
        return index+1

    def CanDrag(self):
        item = self.event.getMaster().itsItem
        return (item.isAttributeModifiable(Calendar.EventStamp.startTime.name) and
                item.isAttributeModifiable(Calendar.EventStamp.duration.name))

    def CanChangeTitle(self):
        item = self.event.getMaster().itsItem
        return item.isAttributeModifiable(Calendar.EventStamp.summary.name)
    
    def SetTimeHeight(self, dc, styles, timeString = 'DummyValue'):
        """Initialize timeHeight for displaying edit window."""
        if Calendar.isDayEvent(self.event):                
            self.timeHeight = 0
        else:
            timeHeight = dc.GetFullTextExtent(timeString,
                                              styles.eventTimeFont)[1]
            minAvailableSpace = timeHeight*2 + TIME_BOTTOM_MARGIN + \
                                self.textOffset.y*2
            if (self.GetBoundsRects()[0].height < minAvailableSpace):
                timeHeight = 0

            self.timeHeight = timeHeight

        return self.timeHeight
                


    def Draw(self, dc, styles, selected, leftSideCutoff=False, 
             rightSideCutOff=False):
        # @@@ add a general cutoff parameter?
        event = self.event
        # recurring items, when deleted or stamped non-Calendar, are sometimes
        # passed to Draw before wxSynchronize is called, ignore those items
        
        if (event.itsItem.isDeleted() or
            not has_stamp(event, Calendar.EventStamp)):
            return
        isAnyTimeOrAllDay = Calendar.isDayEvent(event)
        allCollection = schema.ns('osaf.pim', event.itsItem.itsView).allCollection
        # Draw one event - an event consists of one or more bounds
       
        clipRect = None
        (cx,cy,cwidth,cheight) = dc.GetClippingBox()
        if not cwidth == cheight == 0:
            clipRect = (cx,cy,cwidth,cheight)
        
        gradientLeft, gradientRight, outlineColor, textColor = \
            self.getEventColors(selected)
       
        dc.SetTextForeground(textColor)
        for rectIndex, itemRect in enumerate(self.GetBoundsRects()):

            if not itemRect.IsEmpty() and itemRect.width > 2:

                # properly round the corners - first and last	
                # boundsRect gets some rounding, and they	
                # may actually be the same boundsRect	
                hasTopRightRounded = hasBottomRightRounded = False	
                drawEventText = False	
                    
                if isAnyTimeOrAllDay:
                    timeHeight = 0
                else:
                    # When a canvas item is being dragged, it will have a
                    # startTime set on it different from event.starTime. If
                    # this isn't set, use the cached timeString
                    startTime = getattr(self, 'startTime', None)
                    if startTime:
                        # don't use a time zone when drawing the startTime
                        timeString = formatTime(startTime, noTZ=True)
                    else:
                        timeString = self.timeString
                    timeHeight = self.SetTimeHeight(dc, styles, timeString)

                if timeHeight > 0:
                    radius = NORMAL_RADIUS
                else:
                    radius = ONE_LINE_RADIUS

                if rectIndex == 0:
                    hasTopRightRounded = True
                    drawEventText = True
              
                if rectIndex == len(self.GetBoundsRects())-1:
                    hasBottomRightRounded = True
           
                hasLeftRounded = not leftSideCutoff 

                dc.SetBrush(wx.WHITE_BRUSH)
                dc.SetPen(wx.Pen(wx.WHITE, 1))

                # draw white outline
                self.DrawEventRectangle(dc, itemRect, wx.WHITE_BRUSH, radius,
                                        hasLeftRounded, hasTopRightRounded,
                                        hasBottomRightRounded, rightSideCutOff)

                # new, smaller itemRect
                itemRect = wx.Rect(itemRect.x + 1, itemRect.y + 1,
                                   itemRect.width - 2, itemRect.height - 2)

                if ENABLE_DEVICE_ORIGIN:
                    brushOffset = 0
                else:
                    brushOffset = itemRect.x

                brush = styles.brushes.GetGradientBrush(brushOffset,
                                                        itemRect.width,
                                                        gradientLeft, gradientRight)

                # draw the normal canvas item
                dc.SetBrush(brush)
                dc.SetPen(wx.Pen(outlineColor, 1))
                
                self.DrawEventRectangle(dc, itemRect, brush, radius,
                                        hasLeftRounded, hasTopRightRounded,
                                        hasBottomRightRounded, rightSideCutOff,
                                        self.dashedLine(), styles)
                    
    
                # Shift text to account for rounded corners
                x = itemRect.x + self.textOffset.x
                y = itemRect.y + self.textOffset.y
    
                width = itemRect.width - self.textOffset.x - self.textMargin

                lostBottom = 0

                # only draw date/time on first item
                if drawEventText:
                    # collection swatches should be drawn if the item is
                    # in at least one other collection (not counting out of the 
                    # box collections).
                    
                    master = event.getMaster().itsItem
                    colls = len([i for i in getattr(master, 'appearsIn', []) if
                                 i not in self.ignoreCollections])
                    # for some reason primaryCollection and allCollection don't
                    # compare as equal when they ought to, so compare UUIDs
                    drawSwatches = (colls > 1 or (colls == 1 and
                                            (self.primaryCollection.itsUUID == 
                                             allCollection.itsUUID)))
                    
                    # only draw time on timed events
                    if not isAnyTimeOrAllDay and timeHeight > 0:
                        timeRect = (x, y, width, timeHeight)
                        dc.SetFont(styles.eventTimeFont)
                        # draw start time
                        DrawWrappedText(dc, timeString, timeRect,
                                        styles.eventTimeMeasurements)
                        
                        # calculate where to draw timezone
                        textWidth = dc.GetFullTextExtent(timeString,
                                          styles.eventTimeFont)[0]
                        
                        # set up superscript font
                        size = styles.eventTimeStyle.fontSize * .7
                        if IS_MAC:
                            # on the Mac anti-aliasing seems to stop at 8px
                            size = max(size, 9)
                        superscript = Styles.getFont(size=size)
                        
                        # Draw timezone string.
                        # This logic assumes the timezone should be to the right
                        # of the time string.  This isn't necessarily true,
                        # so this isn't really localized yet.
                        if textWidth < width:
                            tzString = shortTZ(event.startTime)
                            if len(tzString) > 0:
                                dc.SetFont(superscript)
                                DrawClippedText(dc, tzString, x + textWidth,
                                                y, width - textWidth,
                                                timeHeight)
                        
                        y += self.timeHeight + TIME_BOTTOM_MARGIN

                        # draw end time (which should only be set when dragging)
                        endTime = getattr(self, 'endTime', None)
                        if endTime:
                            timeString = formatTime(endTime, noTZ=True)
                            tzString = shortTZ(event.startTime)
                            
                            textWidth = dc.GetFullTextExtent(timeString,
                                                        styles.eventTimeFont)[0]
                            tzWidth = 0
                            if len(tzString) > 0:
                                tzWidth   = dc.GetFullTextExtent(tzString,
                                                                 superscript)[0]
                            
                            rightMargin = max(radius/2,self.textMargin)
                            if drawSwatches:
                                rightMargin = (rightMargin + SWATCH_WIDTH +
                                               2*SWATCH_BORDER)

                            rightAlignStart = max(x, x + width - 
                                            (textWidth + tzWidth + rightMargin))
                            bottomStart = (y - 2*self.textOffset.y -
                                           2*timeHeight + itemRect.height)
                            rectWidth = (width - rightMargin + 
                                         x - rightAlignStart)
                            timeRect = (rightAlignStart, bottomStart,
                                        rectWidth, timeHeight)
                            dc.SetFont(styles.eventTimeFont)

                            DrawWrappedText(dc, timeString, timeRect,
                                            styles.eventTimeMeasurements)

                            if len(tzString) > 0:
                                dc.SetFont(superscript)

                                DrawClippedText(dc, tzString,
                                                rightAlignStart + textWidth,
                                                bottomStart,
                                                rectWidth - textWidth,
                                                timeHeight)                              
                            
                            lostBottom = timeHeight + self.textOffset.y
                                

    
                    # we may have lost some room in the rectangle from	
                    # drawing the time	
                    lostHeight = y - itemRect.y + lostBottom
    
                    # for some reason text measurement on the mac is off,
                    # and text tends to look smooshed to the edge, so we
                    # give it a 5 pixel buffer there
                    
                    rightMargin = 0
                    
                    if drawSwatches:

                        margin = max(radius/2, self.textMargin)
                        yMargin = vector([0, margin])

                        bottomRight = vector(
                               [itemRect.x + itemRect.width - margin, 
                                itemRect.y + itemRect.height - margin])
                        topRight = vector([itemRect.x + itemRect.width - margin,
                                           itemRect.y + lostHeight + margin])

                        if timeHeight > 0:
                            # if the time was drawn, add yMargin back in, 
                            # because lostHeight includes ample margin
                            topLeft = topRight - SWATCH_WIDTH_VECTOR - yMargin
                            
                            self.DrawCollectionSwatches(dc, topLeft,
                                                        bottomRight, True)

                            rightMargin += (margin + SWATCH_WIDTH +
                                            2 * SWATCH_BORDER)
                        else:
                            textWidth = dc.GetFullTextExtent(event.summary,
                                              styles.eventLabelFont)[0]                            
                            
                            oneWidth = (SWATCH_SEPARATION + SWATCH_WIDTH +
                                        2*SWATCH_BORDER)
                            doubleWidth = (margin + 2 * oneWidth -
                                           SWATCH_SEPARATION)
                            
                            # position swatches in the middle of the lozenge
                            
                            if textWidth > width - rightMargin - doubleWidth:
                                left = topRight[0] - doubleWidth
                            else:
                                left = x + textWidth
                            
                            right = topRight[0]
                            top = itemRect.y + radius - self.swatchAdjust
                            bottom = top + SWATCH_HEIGHT + 2 * SWATCH_BORDER 
     
                            count = self.DrawCollectionSwatches(dc, 
                                                        vector([left, top]),
                                                        vector([right, bottom]),
                                                        vertical=False)
                            
                            rightMargin += (margin + count * oneWidth -
                                            SWATCH_SEPARATION)

                    if IS_MAC:
                        rightMargin += 5
                    
                    # now draw the text of the event
                    textRect = (x,y,width - rightMargin,
                                itemRect.height - lostHeight - self.textOffset.y)
           
                    dc.SetFont(styles.eventLabelFont)
                    drawingItem = event.itsItem
                    if selected:
                        drawingItem = RecurrenceDialog.getProxy(u'ui', drawingItem)
                    DrawWrappedText(dc, drawingItem.displayName, textRect,
                                    styles.eventLabelMeasurements)
       
        dc.DestroyClippingRegion()
        if clipRect:
            dc.SetClippingRegion(*clipRect)

    def DrawCollectionSwatches(self, dc, topLeft, bottomRight, vertical=True):
        """
        topLeft and bottomRight must be vectors (lists which can be added and
        subtracted like vectors)
        """
        master = self.event.getMaster().itsItem
        app_ns = schema.ns('osaf.app', self.event.itsItem.itsView)
        sidebarCollections = app_ns.sidebarCollection
        allCollection = schema.ns('osaf.pim', self.event.itsItem.itsView).allCollection
        if self.isActive:
            fillColorLozengeType = 'UnSelectedGradientRight'
            outlinePre1 = 'Selected'
        else:
            fillColorLozengeType = 'OverlayGradientRight'
            outlinePre1 = 'Overlay'
        if self.invertColors():
            outlinePre2 = 'FYISwatchOutline'
        else:
            outlinePre2 = 'SwatchOutline'

        hue = getHueForCollection(self.collection)
        outlineColor = getLozengeTypeColor(hue, outlinePre1 + outlinePre2)
        dc.SetPen(wx.Pen(outlineColor, SWATCH_BORDER))

        if vertical:
            delta = SWATCH_HEIGHT_VECTOR + vector([0, SWATCH_SEPARATION])
        else:
            delta = SWATCH_WIDTH_VECTOR  + vector([SWATCH_SEPARATION, 0])

        if IS_MAC:
            dc.SetAntiAliasing(False)

        count = 0
        for coll in reversed([i for i in sidebarCollections if 
                              master in i and i is not self.collection and 
                              i not in self.ignoreCollections]):
            swatchBR = bottomRight - count * delta
            swatchTL = swatchBR - SWATCH_HEIGHT_VECTOR - SWATCH_WIDTH_VECTOR
            
            if swatchTL[0] < topLeft[0] or swatchTL[1] < topLeft[1]:
                break
            else:
                hue = getHueForCollection(coll)
                fillColor = getLozengeTypeColor(hue, fillColorLozengeType)
                brush = wx.TheBrushList.FindOrCreateBrush(fillColor, wx.SOLID)
                dc.SetBrush(brush)

                dc.DrawRectangle(*swatchTL.join(swatchBR - swatchTL))
                count += 1
                
        if IS_MAC:
            dc.SetAntiAliasing(True)

        return count

    def DrawEventRectangle(self, dc, rect, brush, radius,
                           hasLeftRounded=False,
                           hasTopRightRounded=True,
                           hasBottomRightRounded=True,
                           clipRightSide=False,
                           addDashes = False,
                           styles = None):
        """
        Make a rounded rectangle, optionally specifying if the top and bottom
        right side of the rectangle should have rounded corners.
        Uses clip rect tricks to make sure it is drawn correctly.

        Side effect: Destroys the clipping region.
        """
        if addDashes:
            dashColor = self.colorInfo.selectedFYIColors[3]
            outlinePen = wx.Pen(dashColor, 1)
            dc.SetPen(outlinePen)
        diameter = radius * 2

        dc.DestroyClippingRegion()
        dc.SetClippingRect(rect)

        (oldOriginX, oldOriginY) = dc.GetDeviceOrigin()
        (rectX,rectY,width,height) = rect

        if ENABLE_DEVICE_ORIGIN:
            dc.SetDeviceOrigin(oldOriginX + rectX, oldOriginY + rectY)

            # total hack - see bug 4870
            # reset the brush so it recognizes the new device origin
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetBrush(brush)
            x = y = 0
        else:
            (x, y) = (rectX, rectY)

        # left/right clipping
        if not hasLeftRounded:
            x -= radius
            width += radius

        if clipRightSide:
            width += radius;
            
        # top/bottom clipping
        if not hasBottomRightRounded:
            height += radius

        if not hasTopRightRounded:
            y -= radius
            height += radius

        # finally draw the clipped rounded rect
        dc.DrawRoundedRectangle(x, y, width, height, radius)
        dash_pattern = [2,1,4,1]
        
        def drawVertical(brush = None):
            if brush:
                dc.SetBrush(brush)
                dc.DrawRectangle(x, y+radius, 1, height - diameter)
                dc.DrawRectangle(x+width-1, y+radius, 1, height - diameter)
            else:
                dc.DrawLine(x, y+radius,  x, y+height-radius)                #left 
                dc.DrawLine(x+width-1, y+radius, x+width-1, y+height-radius) #right

        def drawHorizontal(brush = None):
            if brush:
                dc.SetBrush(brush)
                dc.DrawRectangle(x+radius, y, width - diameter, 1)
                dc.DrawRectangle(x+radius, y+height-1, width - diameter, 1)                
            else:
                dc.DrawLine(x+radius, y,  x + width-radius, y)               #top 
                dc.DrawLine(x+radius, y+height-1, x+width-radius, y+height-1)#bottom


        if IS_MAC and addDashes:
            dc.SetAntiAliasing(False)
            dc.SetPen(wx.Pen(wx.WHITE, 0, wx.TRANSPARENT))

            drawHorizontal(styles.brushes.GetDash(x, dash_pattern, dashColor,
                                                  'Horizontal'))

            drawVertical(styles.brushes.GetDash(y, dash_pattern, dashColor,
                                                'Vertical'))
            # we ought to be storing the result of GetAntiAliasing, but that
            # appears to always return False, so for now we just assume we're
            # anti-aliasing
            dc.SetAntiAliasing(True)

        elif addDashes:
            # draw white under dashes
            dc.SetPen(wx.Pen(wx.WHITE, 1))
            drawHorizontal()
            drawVertical()

            # draw dashes
            outlinePen.SetStyle(wx.USER_DASH)
            outlinePen.SetCap(wx.CAP_BUTT)
            outlinePen.SetDashes(dash_pattern)
            dc.SetPen(outlinePen)
            drawHorizontal()
            drawVertical()

        if ENABLE_DEVICE_ORIGIN:
            dc.SetDeviceOrigin(oldOriginX, oldOriginY)


class CalendarEventHandler(object):
    """
    Mixin to a widget class.
    
    ASSUMPTION: its blockItem is a CalendarBlock.
    """

    def onGoToPrevEvent(self, event):
        blockItem = self.blockItem
        blockItem.decrementRange()
        blockItem.postDateChanged(self.blockItem.selectedDate)
        blockItem.synchronizeWidget()

    def onGoToNextEvent(self, event):
        blockItem = self.blockItem
        blockItem.incrementRange()
        blockItem.postDateChanged(self.blockItem.selectedDate)
        blockItem.synchronizeWidget()

    def onGoToTodayEvent(self, event):
        blockItem = self.blockItem
        today = CalendarBlock.startOfToday()
        
        blockItem.setRange(today)
        blockItem.postDateChanged(self.blockItem.selectedDate)
        blockItem.synchronizeWidget()
        
    def OnTZChoice(self, event):
        control = event.GetEventObject()
        choiceIndex = control.GetSelection()
        if choiceIndex != -1:
            view = self.blockItem.itsView
            oldTZ = TimeZoneInfo.get(view).default
            newTZ = control.GetClientData(choiceIndex)
            if newTZ == TimeZoneList.TIMEZONE_OTHER_FLAG:
                newTZ = TimeZoneList.pickTimeZone(view)
                if newTZ is None:
                    newTZ = oldTZ
                TimeZoneList.buildTZChoiceList(view, control, newTZ)

            if newTZ != oldTZ:
                TimeZoneInfo.get(view).default = newTZ
                view.commit()
                
                self.blockItem.postEventByName("TimeZoneChange",
                                               {'tzinfo':newTZ})

class CalendarNotificationHandler(object):
    """
    Mixin to a wx class to deal with item notifications.
    """
    def __init__(self, *args, **kwds):
        super(CalendarNotificationHandler, self).__init__(*args, **kwds)
        self._pendingNewEvents = set()

    def onItemNotification(self, notificationType, data):
        if (notificationType == 'collectionChange'):
            op, coll, name, uuid = data
            if op == 'add':
                self._pendingNewEvents.add(uuid)
            elif op == 'remove' and uuid in self._pendingNewEvents:
                self._pendingNewEvents.remove(uuid)

    def ClearPendingNewEvents(self):
        self._pendingNewEvents = set()
        
    def GetPendingNewEvents(self, (startTime, endTime), expandRecurrence=True):

        # Helper method for optimizing the display of
        # newly created events in various calendar widgets.
        # (See Bug:4118).
        # 
        # The return value will be a list of all the events
        # (i.e. non-recurring events and individual occurrences of
        # recurring events) that overlap the range between the datetime
        # arguments startTime and endTime.
        # 
        # The idea is that you can call this from wxSynchronizeWidget(),
        # and do a full redraw if you get back [], or do less work
        # if you get a list of events.
        #
        # The returned list may be empty (e.g. if an event is added
        # outside the given range).
        #
        # XXX: [grant] This call now occurs too late to trigger a full
        # redraw. As a result, we're triggering an unnecessary load
        # of events for the minicalendar in this case.
        #
        addedEvents = []
        for itemUUID in self._pendingNewEvents:
            try:
                item = self.blockItem.itsView[itemUUID]
            except KeyError:
                # print "Couldn't find new item %s" % itemUUID
                continue
                
            if has_stamp(item, Calendar.EventStamp):
                event = Calendar.EventStamp(item)
            
                if (hasattr(event, 'startTime') and
                    hasattr(event, 'duration')):
                    
                    if expandRecurrence and event.rruleset is not None:
                        addedEvents.extend(event.getOccurrencesBetween(startTime, endTime))
                    elif not (event.startTime > endTime or event.endTime < startTime):
                        addedEvents.append(event)
                    else:
                        addedEvents.append(event)

        self._pendingNewEvents = set()
        return addedEvents

    def HavePendingNewEvents(self):
        return len(self._pendingNewEvents)>0


# ATTENTION: do not put mixins here - put them in CollectionBlock
# instead, to keep them more general
class CalendarBlock(CollectionCanvas.CollectionBlock):
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
    """
    # @@@ method capitalization policy is inconsistent!


    rangeStart = schema.One(schema.DateTime)
    rangeIncrement = schema.One(schema.TimeDelta, initialValue=timedelta(days=7))
    lastHue = schema.One(schema.Float, initialValue = -1.0)
    dayMode = schema.One(schema.Boolean,initialValue = False)
    calendarContainer = schema.One(schema.Item, required=True)

    def getRangeEnd(self):
        return self.rangeStart + self.rangeIncrement	
    rangeEnd = property(getRangeEnd)

    def __setup__(self):
        self.setRange(self.startOfToday())

    def render(self, *args, **kwds):
        super(CalendarBlock, self).render(*args, **kwds)
        Monitors.attach(self, 'onColorChanged', 'set', 'osaf.usercollections.UserCollection.color')

    def onDestroyWidget(self, *args, **kwds):
        Monitors.detach(self, 'onColorChanged', 'set', 'osaf.usercollections.UserCollection.color')
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
        This says this class has been rendered during this session.
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
        start = time(tzinfo=ICUtzinfo.default)
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
            collections = getattr(self.contents, 'collectionList',
                                  [self.contents])
            if item in collections:
                self.widget.RefreshCanvasItems(resort=False)
        except AttributeError:
            # sometimes self.contents hasn't been set yet, or the
            # widget hasn't been rendered yet, or the widget doesn't
            # support RefreshCanvasItems. That's fine.
            return

    def EnsureIndexes(self):
        # events needs to have an index or iterindexkeys will load items,
        # is that true?
        Calendar.ensureIndexed(self.contents)
        
    def setContentsOnBlock(self, *args, **kwds):
        super(CalendarBlock, self).setContentsOnBlock(*args, **kwds)

        self.EnsureIndexes()

    def onDayModeEvent(self, event):
        self.closeEditor()
        self.dayMode = event.arguments['dayMode']
        if self.dayMode:
            self.rangeIncrement = timedelta(days=1)
            newDay = event.arguments['newDay']
            if newDay is not None:
                self.setRange(newDay)
        else:
            self.rangeIncrement = timedelta(days=7)
            self.setRange(self.rangeStart)
        self.synchronizeWidget()

    def onSelectedDateChangedEvent(self, event):
        """
        Sets the selected date range and synchronizes the widget.

        @param event: event sent on selected date changed event.
                      event.arguments['start']: start of the newly selected date range
        @type event: osaf.framework.blocks.Block.BlockEvent.
                     event.arguments['start']: C{datetime}
        """
        self.setRange(event.arguments['start'])
        self.synchronizeWidget()

    def postDateChanged(self, newdate=None):
        """
        Convenience method for changing the selected date.
        """
        if newdate is None:
            newdate = self.rangeStart

        self.postEventByName ('SelectedDateChanged',{'start':newdate})

    def postDayMode(self, dayMode, newDay=None):
        """
        Convenience method for changing between day and week mode.
        """
        self.postEventByName ('DayMode', {'dayMode': dayMode, 'newDay' : newDay})
        
    def getFreeBusyCollections(self):
        """
        Convenience method, returns any selected or overlaid collections
        whose conduit is a CalDAVFreeBusyConduit.

        """
        hits = []
        try:
            collections = getattr(self.contents, 'collectionList',
                                  [self.contents])
        except AttributeError:
            # sometimes self.contents hasn't been set yet. That's fine.
            return hits
        
        for collection in collections:
            shares = getattr(collection, 'shares', [])
            for share in shares:
                if isinstance(share.conduit, CalDAVFreeBusyConduit):
                    hits.append(collection)
                    break
        
        return hits

    def closeEditor(self):
        if (getattr(self, 'widget', None) and 
            getattr(self.widget, 'GrabFocusHack', None)):
            self.widget.GrabFocusHack()

    # Managing the date range

    def setRange(self, date):
        """
        Sets the range to include the given date, given the current view.
        For week view, it will start the range at the beginning of the week.
        For day view, it will set the range to start at the given date

        @param date: date to include
        @type date: datetime
        """
        self.closeEditor()
        date = datetime.combine(date, time(tzinfo=ICUtzinfo.floating))

        if self.dayMode:
            self.rangeStart = date
            number = 1
        else:
            calendar = GregorianCalendar()
            calendar.setTimeZone(ICUtzinfo.default.timezone)
            calendar.setTime(date)
            delta = timedelta(days=(calendar.get(calendar.DAY_OF_WEEK) -
                                    calendar.getFirstDayOfWeek()))
            self.rangeStart = date - delta
            number = 7
        
        # get an extra day on either side of the displayed range, because
        # timezone displayed could be earlier or later than UTC
        fb_date = self.rangeStart.date() - timedelta(1)
        dates = [fb_date + n * timedelta(1) for n in range(number + 2)]
 
        for col in self.getFreeBusyCollections():
            annotation = FreeBusyAnnotation(col)
            for date in dates:
                annotation.addDateNeeded(self.itsView, date)    

    def incrementRange(self):
        """
        Increments the calendar's current range.
        """
        self.closeEditor()
        self.rangeStart += self.rangeIncrement

    def decrementRange(self):
        """
        Decrements the calendar's current range.
        """
        self.closeEditor()
        self.rangeStart -= self.rangeIncrement

    # Get items from the collection

    def eventIsInRange(self, event, start, end):
        """
        Helpful utility to determine if an event is within a given range.
        Assumes the event has a startTime and endTime attribute.
        """
        tzprefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        if tzprefs.showUI:
            return ((event.effectiveStartTime <= end) and
                    (event.effectiveEndTime >= start))
        else:
            return ((event.effectiveStartTime.replace(tzinfo=None) <=
                                         end.replace(tzinfo=None)) and
                      (event.effectiveEndTime.replace(tzinfo=None) >=
                                       start.replace(tzinfo=None)))

    def generateEventsInRange(self, date, nextDate, dayItems, timedItems):
        # wish we could put this somewhere more useful, but
        # self.contents can be set upon object initialization
        self.EnsureIndexes()

        args = self.itsView, date, nextDate, self.contents, dayItems, timedItems
        normalEvents = Calendar.eventsInRange(*args)
        recurringEvents = Calendar.recurringEventsInRange(*args)
        
        return chain(normalEvents, recurringEvents)

    def getEventsInRange(self, (date, nextDate), dayItems=False, timedItems=False):
        """
        Convenience method to look for the events in the block's contents
        that appear on the given date. We might be able to push this
        to Queries, but eventIsInRange is actually fairly complex.

        @type date: datetime
        @type nextDate: datetime

        @param dayItems: return day events (events that have no start time)
        @param timedItems: return timed events

        @return: the events in this collection that appear within the given range
        @rtype: generator of Items
        """
        assert dayItems or timedItems, "dayItems or timedItems must be True"
        defaultTzinfo = ICUtzinfo.default
        if date.tzinfo is None:
            date = date.replace(tzinfo=defaultTzinfo)
        else:
            date = date.astimezone(defaultTzinfo)

        if nextDate.tzinfo is None:
            nextDate = nextDate.replace(tzinfo=defaultTzinfo)
        else:
            nextDate = nextDate.astimezone(defaultTzinfo)

        for event in self.generateEventsInRange(date, nextDate, dayItems, timedItems):
            if (hasattr(event, 'startTime') and hasattr(event, 'duration')):
                assert self.eventIsInRange(event, date, nextDate), \
                    "generateEventsInRange returned an event outside the range."
                yield event

    def GetCurrentDateRange(self):
        return (self.rangeStart,  self.rangeStart + self.rangeIncrement)

    def getContainingCollection(self, item, defaultCollection=None):
        """
        Get the collection which contains the event, since it has
        all the right color information.
        """

        event = Calendar.EventStamp(item)
        
        # generated events need to defer to their parent event
        if event.occurrenceFor is not item:
            event = event.getMaster()
            item = event.itsItem
            
        collections = self.contents.collectionList
        firstSpecialCollection = None
        for coll in collections:

            if (item in coll):
                if UserCollection(coll).outOfTheBoxCollection:
                    # save it for later, we might be returning it
                    firstSpecialCollection = coll
                else:
                    return coll
                    
        if firstSpecialCollection:
            return firstSpecialCollection

        #assert False, "Don't have color info for %s" % event
        
        return defaultCollection
        
    def setCurrentCalendarColor(self, color):

        # contentsCollection is the currently selected collection
        UserCollection(self.contentsCollection).color = ColorType(*color)

    def GetSelection(self):
        return CalendarSelection(self.contents)

    def CanAdd(self):
        return (super(CalendarBlock, self).CanAdd() and
                UserCollection(self.contentsCollection).canAdd)

# ATTENTION: do not put mixins here - put them in wxCollectionCanvas
# instead, to keep them more general
class wxCalendarCanvas(CalendarNotificationHandler, CollectionCanvas.wxCollectionCanvas):
    """
    Base class for all calendar canvases - handles basic item selection,
    date ranges, and so forth.

    ASSUMPTION: blockItem is a CalendarBlock.
    """
    legendBorderWidth = 3
    def __init__(self, *arguments, **keywords):
        super (wxCalendarCanvas, self).__init__ (*arguments, **keywords)

        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        
    def OnInit(self):
        super(wxCalendarCanvas, self).OnInit()
    
    def OnScroll(self, event):
        self.Refresh()
        if not wx.GetApp().ignoreSynchronizeWidget:
            # The test is a workaround for the fact that Linux sends a 
            # spurious scroll-to-the-top event when creating the widget.
            # This means scrolling up to midnight will be persisted
            # slightly before midnight
            if not IS_GTK or self.GetViewStart()[1] > 0:
                self.blockItem.scrollY = self.GetViewStart()[1]
        event.Skip()

    def OnSelectItem(self, item):
        super(wxCalendarCanvas, self).OnSelectItem(item)
        # tell the sidebar to select the collection that contains
        # this event - makes the sidebar track the "current" calendar
        # as well as update the gradients correctly
        if item is not None:
            collection = self.blockItem.getContainingCollection(item)
            if (collection is not None and
                collection is not self.blockItem.contentsCollection):
                self.blockItem.SelectCollectionInSidebar(collection)


    def OnEditItem(self, canvasItem):
        if not canvasItem.CanChangeTitle():
            self.WarnReadOnlyTitle([canvasItem.item])
            return
        
        styles = self.blockItem.calendarContainer
        if canvasItem.timeHeight == 0:
            canvasItem.SetTimeHeight(wx.ClientDC(self), styles)        
        
        position = self.CalcScrolledPosition(canvasItem.GetEditorPosition())
        size = canvasItem.GetMaxEditorSize()

        self.editor.SetItem(canvasItem.item, position, size, styles.eventLabelFont.GetPointSize())

    def OnFilePaste(self):
        for filename in self.fileDataObject.GetFilenames():
            item = ChooseFormat.importFile(filename, self.blockItem.itsView,
                                           selectedCollection=True)
            # if the file was ics, None will be returned
            if item is not None:
                self.StampDraggedItem(item)

    def OnEmailPaste(self, text):
        item = ChooseFormat.importEmail(text, self.blockItem.itsView,
                                        selectedCollection=True)
        self.StampDraggedItem(item)
        

    def StampDraggedItem(self, item):
        if ((not has_stamp(item, Calendar.EventStamp)) and 
           getattr(self, 'fileDragPosition', None) is not None):
            startTime = self.getDateTimeFromPosition(self.fileDragPosition)
            event = Calendar.EventStamp(item)
            event.add()
            # make the event's middle happen at startTime
            event.startTime = startTime - timedelta(minutes=30)
            event.duration = timedelta(hours=1)
            event.allDay = event.anyTime = False
            
        item.setTriageStatus('auto')
                
    def GrabFocusHack(self):
        if self.editor.IsShown():
            self.editor.SaveAndHide()

    def onItemNotification(self, notificationType, data):
        # Work around bug 6137 and bug 3727: If an item changes
        # while we're editing it, finish editing.
        if (notificationType == 'collectionChange'):
            op, coll, name, uuid = data
            if op == 'changed' and self.editor.event is not None and \
               self.editor.event.itsItem.itsUUID == uuid and \
               not self.belongsOnCanvas(self.editor.event.itsItem):
                self.GrabFocusHack()
        super(wxCalendarCanvas, self).onItemNotification(notificationType, data)

    def belongsOnCanvas(self, item):
        # Return False if this item no longer belongs on this canvas
        # (overridden by our specialized canvases)
        return True
    
    def RefreshCanvasItems(self, resort=True):
        self.RebuildCanvasItems(resort)
        self.Refresh()
        
    def GetCurrentDateRange(self):
        return self.blockItem.GetCurrentDateRange()

    def ShadeToday(self, dc):
        """
        Shade the background of today, if today is in view.
        """

        # don't shade today in day mode
        if self.blockItem.dayMode:
            return

        # next make sure today is in view
        today = datetime.today().replace(tzinfo=ICUtzinfo.default)
        startDay, endDay = self.blockItem.GetCurrentDateRange()
        if (today < startDay or endDay < today):
            return

        styles = self.blockItem.calendarContainer
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        # rectangle goes from top to bottom, but the 
        dayNum = (today - startDay).days
        x = drawInfo.columnPositions[dayNum+1]
        y = 0
        (width, height) = (drawInfo.columnWidths[dayNum+1],
                           self.size.height)
        dc.SetBrush(styles.todayBrush)
        dc.DrawRectangle(x,y,width, height)

    def DrawDayLines(self, dc):
        """
        Draw lines between days.
        """

        styles = self.blockItem.calendarContainer
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        # the legend border is major
        dc.SetPen(wx.Pen(styles.majorLineColor, self.legendBorderWidth))

        # thick pens with the line centered at x - 1. Offset the
        # legend border because we want the righthand side of the line
        # to be at x - 1
        legendBorderX = drawInfo.columnPositions[1] - self.legendBorderWidth/2 - 1
        
        # save old anti-aliasing value and turn off anti-aliasing
        oldAA = dc.GetAntiAliasing()
        dc.SetAntiAliasing(False)

        dc.DrawLine(legendBorderX, 0,
                    legendBorderX, self.size.height)
        
        def drawDayLine(dayNum):
            x = drawInfo.columnPositions[dayNum+1]
            dc.DrawLine(x, 0,   x, self.size.height)

        # the rest are minor, 1 pixel wide
        dc.SetPen(styles.minorLinePen)
        for dayNum in range(1, drawInfo.columns):
            drawDayLine(dayNum)

        # restore previous value for anti-aliasing
        dc.SetAntiAliasing(oldAA)


    def CreateEmptyEvent(self, **initialValues):
        """
        Shared routine to create an event, using the current view
        also forces consumers to specify important fields.
        """
        view = self.blockItem.itsView

        event = Calendar.CalendarEvent(itsView=view)
        event.InitOutgoingAttributes()
        for kv in initialValues.iteritems():
            setattr(event, *kv)

        item = event.itsItem
        self.blockItem.contentsCollection.add(item)

        self.OnSelectItem(item)
        item.setTriageStatus('auto')

        view.commit()
        return event


    def getBoundedPosition(self, position, drawInfo, mustBeInBounds=True):
        # first make sure we're within the top left boundaries
        yPosition = position.y
        if mustBeInBounds:
            yPosition = max(yPosition, 0)
        if mustBeInBounds:
            xPosition = max(position.x, drawInfo.xOffset)
        else:       
            xPosition = position.x

        # next make sure we're within the bottom right boundaries
        height = self.size.height - 1# was GetMinSize().GetWidth()???
            
        yPosition = min(yPosition, height)
        xPosition = min(xPosition, drawInfo.xOffset + drawInfo.middleWidth - 1)
        return wx.Point(xPosition, yPosition)

    def GetDragAdjustedStartTime(self, tzinfo):
        """
        When a moving drag is originated within a canvasItem, the drag
        originates from a point within the canvasItem, represented by
        dragOffset.

        During a drag, you need to put a canvasItem at currentPosition,
        but you also want to make sure to round it to the nearest dayWidth,
        so that the event will sort of stick to the current column until
        it absolutely must move.
        """
        if self.dragState is None or not hasattr(self.dragState, 'dragOffset'):
            return
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        dx,dy = self.dragState.dragOffset
        dx = roundToColumnPosition(dx, drawInfo.columnPositions)

        position = self.dragState.currentPosition - (dx, dy)

        result = self.getDateTimeFromPosition(position, tzinfo=tzinfo,
                                              mustBeInBounds=False)

        if tzinfo is None:
            result = result.replace(tzinfo=None)

        return result

    def getDayFromPosition(self, position):
        """Determine the day from the given position, return a date."""
        startDay = self.blockItem.rangeStart.date()
        if self.blockItem.dayMode:
            return startDay
        else:
            drawInfo = self.blockItem.calendarContainer.calendarControl.widget
            # find the first column holding position.x
            # subtract one to ignore the "Week" column, plus one more because
            # bisect will skip over the lower pixel boundary for the column
            deltaDays = bisect(drawInfo.columnPositions, position.x) - 2
            return startDay + timedelta(deltaDays)
            
    def getDateTimeFromPosition(self, position, tzinfo=None, mustBeInBounds=True):
        """
        Calculate the date based on the x,y coordinates on the canvas.

        @param mustBeInBounds: if True, restrict to dates the user
                               currently can see/scroll to.
        """

        drawInfo = self.blockItem.calendarContainer.calendarControl.widget
        position = self.getBoundedPosition(position, drawInfo, mustBeInBounds)

        midnight = time(0, tzinfo = ICUtzinfo.default)
        newDay = datetime.combine(self.getDayFromPosition(position), midnight)
        newTime = newDay + self.getRelativeTimeFromPosition(drawInfo, position)

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
        return CalendarSelection(self.blockItem.contents).iterSelection()

    def AddItems(self, itemList):
        source = self.blockItem.contentsCollection
        for item in itemList:	
            item.addToCollection(source)

    def WarnReadOnlyTitle(self, items):
        """
        For now just give a generic warning.
        Eventually it would be nice to give a specific reason.
        """
        Util.ok(self, _(u'Warning'), _(u'This item is read-only. You cannot change the title of read-only items.'))

    def WarnReadOnlyTime(self, items):
        """
        For now just give a generic warning.
        Eventually it would be nice to give a specific reason.
        """
        Util.ok(self, _(u'Warning'), _(u'This item is read-only. You cannot change the time of read-only items.'))

    def getColumnForDay(self, dayStart, dayEnd=None):
        """
        Returns position,width for the given zero-based day(s).
        """
        drawInfo = self.blockItem.calendarContainer.calendarControl.widget

        if self.blockItem.dayMode:
            return (drawInfo.columnPositions[1], drawInfo.middleWidth)
        else:
            if dayEnd is None:
                dayEnd = dayStart
            return (drawInfo.columnPositions[dayStart + 1],
                    sum(drawInfo.columnWidths[dayStart + 1:dayEnd+2]))

    def SaveCharTyped(self, event):
        """
        Capture the first key press that began the edit.
        """
        key = unichr(event.GetUnicodeKey())

        # Setting the insertion point seems to work when several keys are typed
        # before the edit widget is displayed, but perhaps there's a better
        # way to achieve this?

        self.editor.SetInsertionPoint(0)
        self.editor.SetValue(key)
        self.editor.SetInsertionPointEnd()

    def wxSynchronizeWidget(self, useHints=False):
        # clear notifications
        self.ClearPendingNewEvents()

class wxInPlaceEditor(AttributeEditors.wxEditText):

    event = None
    _unfocusing = False
    
    def __init__(self, parent, defocusCallback=None, allowMultiLine=True,
                 *arguments, **keywords):
        
        # Windows and Mac add an extra vertical scrollbar for TE_MULTILINE,
        # GTK doesn't. Further, if GTK is not multiline, then the single
        # line mode looks really wonky with a huge cursor.
        #
        # The undocumented flag TE_NO_VSCROLL solves these problems but
        # introduces another: text does not scroll at all on Mac and MSW. On
        # MSW, not only does the text not scroll, but you can't enter text
        # beyond the size of the editor if TE_NO_VSCROLL and TE_MULTILINE are
        # both set, so on Windows we stick with the a single line for now
        style = wx.NO_BORDER | wx.TE_PROCESS_ENTER | wx.TE_NO_VSCROLL 
        if '__WXMSW__' not in wx.PlatformInfo and allowMultiLine:
            style |= wx.TE_MULTILINE

        super(wxInPlaceEditor, self).__init__(parent,
                                              -1, "", wx.DefaultPosition,
                                              (-1, -1),
                                              style=style,
                                              *arguments, **keywords)

        self.defocusCallback = defocusCallback
        self.Hide()

        self.Bind(wx.EVT_CHAR, self.OnChar)
        parent = self.GetParent()
        parent.Bind(wx.EVT_SIZE, self.OnSize)

    def SaveItem(self):
        if ((self.event is not None) and (not self.IsBeingDeleted())):
            if self.event.summary != self.GetValue():
                parentBlock = self.GetParent()
                proxy = RecurrenceDialog.getProxy(u'ui', self.event,
                                    endCallback=parentBlock.wxSynchronizeWidget)
                Calendar.EventStamp(proxy).summary = self.GetValue()

    def ResetFocus(self):
        if self.defocusCallback:
            self.defocusCallback()

    def HideAndResetFocus(self):
        self._unfocusing = True
        self.Hide()
        self.ResetFocus()
        self._unfocusing = False

        # If an event's title is empty and a user presses enter to begin 
        # editing, SetItem doesn't call SetValue, so empty the buffer
        self.SetValue('') 

    def SaveAndHide(self):
        self.SaveItem()
        self.HideAndResetFocus()

    def OnEnterPressed(self, event):
        """
        For now, no need to display.
        """
        self.SaveAndHide()

    def OnEscapePressed(self, event):
        self.HideAndResetFocus()

    def OnKillFocus(self, event):
        if self.IsBeingDeleted():
            return
        super(wxInPlaceEditor, self).OnKillFocus(event)
        if not self._unfocusing:
            self.SaveAndHide()

    def OnChar(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.OnEscapePressed(event)
        else:
            event.Skip()

    def SetItem(self, item, position, size, pointSize):
        self.event = Calendar.EventStamp(item)
        newKeyPressedItem = self.event.summary == ''
        if not newKeyPressedItem:
            self.SetValue(self.event.summary)

        newSize = wx.Size(size.width, size.height)

        if IS_GTK:
            # On GTK single-line lozenge text doesn't fit without scroll bars
            # but everything aligns nicely if the point size is reduced by 1
            pointSize -= 1

        font = wx.Font(pointSize, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.SetFont(font)

        # move the frame so that the default Mac Aqua focus "halo"
        # is aligned with the outer event frame
        if IS_MAC:
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
        # if summary is empty, a keyboard edit is likely in progress, don't
        # interrupt it.
        if not newKeyPressedItem:
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

    def InitializeStyles(self):

        # Map styles to fonts
        for stylename in ('monthLabel', 'eventLabel', 'eventTime', 'legend'):
            style = getattr(self, stylename + 'Style')
            setattr(self, stylename + 'Font', 
                    Styles.getFont(style))
            
        self.monthLabelColor = wx.Colour(64, 64, 64)

        self.eventLabelColor = wx.BLACK
        self.eventLabelMeasurements=Styles.getMeasurements(self.eventLabelFont)
        self.eventTimeMeasurements =Styles.getMeasurements(self.eventTimeFont)
        
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
        if IS_MAC:
            w.SetWindowStyle(wx.BORDER_SIMPLE)
        else:
            w.SetWindowStyle(wx.BORDER_STATIC)

        # minimum 45 pixels per column
        w.SetMinSize((8*45, -1))

        return w

    def onNewItemEvent(self, event):
        """
        Create a new event from the menu - try to use contextual
        information from the view to create it in a normal place.
        """
        classParameter = event.classParameter
        
        # if it's one of ours or None we'll handle it otherwise bubble it up
        if (classParameter is Calendar.EventStamp or
            classParameter is MissingClass):
            timedEventsCanvas = self.getTimedBlock().widget

            startTime, duration = timedEventsCanvas.GetNewEventTime()
            newEvent = timedEventsCanvas.CreateEmptyEvent(startTime=startTime,
                                                          duration=duration,
                                                          anyTime=False)

            timedEventsCanvas.SetPanelFocus()
            timedEventsCanvas.ScrollToEvent(newEvent)

            # return the list of items created
            return newEvent
        else:
            event.arguments['continueBubbleUp'] = True

    def getTimedBlock(self):
        # this is a little bit of a hack, because we know we want to get
        # to the timed events canvas        
        calendarSplitter = nth(self.childBlocks, 1)
        return nth(calendarSplitter.childBlocks, 1)

    def getAllDayBlock(self):
        # this is a little bit of a hack, because we know we want to get
        # to the timed events canvas        
        calendarSplitter = nth(self.childBlocks, 1)
        return nth(calendarSplitter.childBlocks, 0)

        
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
    dayMode = schema.One(schema.Boolean, initialValue=False)
    daysPerView = schema.One(schema.Integer, initialValue=7) #ready to phase out?
    tzCharacterStyle = schema.One(Styles.CharacterStyle)

    selectedDate = schema.One(schema.DateTime,
                              doc="The currently selected date for "
                              "day mode. We try to keep this up to "
                              "date even when we're in week mode")

    schema.addClouds(
        copying = schema.Cloud(byRef = [tzCharacterStyle])
    )

    def instantiateWidget(self):
        if not self.getHasBeenRendered():
            self.setRange( datetime.now().date() )
            self.setHasBeenRendered()
        w = wxCalendarControl(self.parentBlock.widget, -1, 
                              tzCharacterStyle=self.tzCharacterStyle)
        return w

    def getWatchList(self):
        tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        timezones = TimeZoneInfo.get(self.itsView)
        return [ (tzPrefs, 'showUI'), 
                 (timezones, 'wellKnownIDs') ]

    def onItemNotification(self, notificationType, data):
        if (notificationType == 'itemChange'):
            op, item, names = data
            tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
            itemUUID = getattr(item, 'itsUUID', item)
            if tzPrefs.itsUUID == itemUUID:
                # It's the timezone preference item
                if 'showUI' in names:
                    control = self.widget.tzChoice
                    control.Show(tzPrefs.showUI)
                    if (tzPrefs.showUI and
                        TimeZoneInfo.get(self.itsView).default != 
                        control.GetClientData(control.GetSelection())):
                        # the timezone chooser is out of sync, update it
                        TimeZoneList.buildTZChoiceList(self.itsView, control)
                        
                    self.widget.Layout()
            else:
                # It's the list-of-timezones preference item
                if 'wellKnownIDs' in names:
                    TimeZoneList.buildTZChoiceList(self.itsView, self.widget.tzChoice)
        
    def onSelectedDateChangedEvent(self, event):
        super(CalendarControl, self).onSelectedDateChangedEvent(event)

    # annoying: right now have to forward this to the widget, but
    # perhaps block dispatch could dispatch to the widget first, then
    # the block?
    def onGoToPrevEvent(self, event):
        self.widget.onGoToPrevEvent(event)

    def onGoToNextEvent(self, event):
        self.widget.onGoToNextEvent(event)

    def onGoToTodayEvent(self, event):
        self.widget.onGoToTodayEvent(event)

    def onGoToDateEvent(self, event):
        newDate = event.arguments.get('DateTime')
        dateString = event.arguments.get('DateString')
        if newDate is None and dateString is None:
            dateString = Util.promptUser(
                _(u"Go to date"),
                _(u"Enter a date in the form %(dateFormat)s") %
                                   dict(dateFormat=DateTimeUtil.sampleDate))
            if dateString is None:
                return

        if newDate is None:
            newDate = DateTimeUtil.shortDateFormat.parse(dateString)
        self.setRange(newDate)
        self.postDateChanged(self.selectedDate)
        self.synchronizeWidget()
        
    def initializeTree(self, hints):
        event = hints.get ("event", None)
        if event is not None:
            if event.dayMode:
                self.postDayMode(True, self.selectedDate)
            else:
                self.postDayMode(False)
            widget = getattr (self, "widget", None)
            if widget is not None:
                widget.UpdateHeader()

    def onViewEventUpdateUI (self, event):
        event.arguments ['Check'] = event.dayMode == self.dayMode

    def onGoToCalendarItemEvent(self, event):
        """
        Sets the selected date range to include the given calendar event's start
        time, selects the all collection if the item isn't in the currently
        overlaid collections, scrolls to put the calendar event in view,
        and selects the item.

        @param event: event sent on selected date changed event.
                      event.arguments['item']: item to move to
        @type event: osaf.framework.blocks.Block.BlockEvent.
                     event.arguments['item']: C{item}
        """
        eventItem = Calendar.EventStamp(event.arguments['item'])
        self.postDateChanged(eventItem.startTime)
        
        if eventItem.getMaster().itsItem not in self.contents:
            allCollection = schema.ns('osaf.pim', self.itsView).allCollection
            self.SelectCollectionInSidebar(allCollection)
            self.findBlockByName("DashboardSummaryView").postEventByName(
                "SelectItemsBroadcast", 
                {'items':[eventItem.itsItem]})
        else:                
            if not eventItem.allDay and not eventItem.anyTime:
                timeBlock = self.calendarContainer.getTimedBlock()
                timedEventsCanvas = getattr(timeBlock, 'widget', None)
                # if the dashboard is selected, the calendar won't be displayed
                if timedEventsCanvas is not None:
                    timedEventsCanvas.ScrollToEvent(eventItem)
                    timedEventsCanvas.SetPanelFocus()
            else:
                self.calendarContainer.getAllDayBlock().widget.SetPanelFocus()
                
            self.postEventByName("SelectItemsBroadcast",
                                 {'items':[eventItem.itsItem]})


    def setRange(self, date):
        """
        We need to override CalendarBlock's because the cal ctrl always
        has its range over an entire week, even if a specific day is
        selected (and dayMode is true).
        """
        assert self.daysPerView == 7, "daysPerView is a legacy variable, keep it at 7 plz"

        date = datetime.combine(date, time(tzinfo=ICUtzinfo.default))

        #Set rangeStart
        # start at the beginning of the week (Sunday midnight)
        calendar = GregorianCalendar()
        calendar.setTimeZone(ICUtzinfo.default.timezone)
        calendar.setTime(date)
        delta = timedelta(days=(calendar.get(calendar.DAY_OF_WEEK) -
                                calendar.getFirstDayOfWeek()))

        self.rangeStart = date - delta
        if self.dayMode:
            self.selectedDate = date.replace(tzinfo=ICUtzinfo.floating)
        else:
            # only reset selectedDate if its not in the current range
            if not hasattr(self, 'selectedDate'):
                self.selectedDate = self.rangeStart

            # now make sure the selectedDate stays more or less on the
            # same day of the week even if the week changed
            while self.selectedDate < self.rangeStart:
                self.selectedDate += self.rangeIncrement

            rangeEnd = self.rangeStart + self.rangeIncrement
            while self.selectedDate >= rangeEnd:
                self.selectedDate -= self.rangeIncrement

    def incrementRange(self):
        """
        Need to override block because what we really want to do is
        increment the selected date and reset the range.
        """
        self.setRange(self.selectedDate + self.rangeIncrement)

    def decrementRange(self):
        self.setRange(self.selectedDate - self.rangeIncrement)

    def onSelectItemsEvent(self, event):
        newSelection = event.arguments['items']

        # probably should account for the selection being identical to
        # the current selection

        contents = CalendarSelection(self.contents)
        contents.clearSelection()

        if newSelection:
            for item in newSelection:
                # Clicks in the preview area may result in selecting an item
                # not in contents, ignore such items
                if item in contents:
                    contents.selectItem(item)

        if hasattr(self, 'widget'):
            self.widget.Refresh()

class wxCalendarControl(wx.Panel, CalendarEventHandler):
    """
    This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons.
    """

    def __init__(self, parent, id, tzCharacterStyle, *arguments, **keywords):
        super(wxCalendarControl, self).__init__(parent, id, *arguments, **keywords)
    
        app = wx.GetApp()
        self.allDayCloseArrowImage = app.GetImage("AllDayCloseArrow_whitebg.png")
        self.allDayOpenArrowImage = app.GetImage("AllDayOpenArrow_whitebg.png")

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
        self.Bind(wx.EVT_BUTTON, self.onGoToPrevEvent, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.onGoToNextEvent, self.nextButton)

        self.tzChoice = self.MakeTimezoneChoice(tzCharacterStyle)
        registerStringForId (self.tzChoice.GetId(), "TimezoneChoice")

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
            weekColumnHeader.AppendItem(header, wx.ALIGN_CENTER, 0, bSortEnabled=False)
            
        expandoColumn = len(headerLabels) - 1
        self.Bind(wx.colheader.EVT_COLUMNHEADER_SELCHANGED,
                  self.OnDayColumnSelect, weekColumnHeader)

        # this should be the width of the word "Week" in the column
        # header, plus some padding
        dc = wx.ClientDC(self)
        width, height = dc.GetTextExtent(headerLabels[0])

        if '__WXGTK__' in wx.PlatformInfo:
            self.xOffset = width + 12
        else:
            self.xOffset = width + 6
        
        # set up initial selection
        weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_VisibleSelection,
                                      True)
        sizer.Add(weekColumnHeader, 0, wx.EXPAND)
        
        self.SetSizer(sizer)
        self.Layout()
        
    def __del__(self):
        unregisterStringForId ("TimezoneChoice")


    def OnInit(self):
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetBackgroundColour(self.blockItem.parentBlock.bgColor)
        
        styles = self.blockItem.calendarContainer
        self.monthText.SetFont(styles.monthLabelFont)
        self.monthText.SetForegroundColour(styles.monthLabelColor)
        
        self.weekColumnHeader.SetLabelBitmap(8, self.allDayCloseArrowImage)
        self.UpdateHeader()

        # onetime measurements
        self.scrollbarWidth = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X) + 1

        tzPrefs = schema.ns('osaf.pim', self.blockItem.itsView).TimezonePrefs
        self.tzChoice.Show(tzPrefs.showUI)

        self._doDrawingCalculations() #hopefully this is early enough

    def MakeTimezoneChoice(self, tzCharacterStyle):
        tzChoice = wx.Choice (self)
        font = Styles.getFont(tzCharacterStyle)
        if font is not None:
            tzChoice.SetFont(font)

        # self.blockItem hasn't been set yet, because
        # CalendarControl.instantiateWidget() hasn't returned.
        # So, we get the repo view from our parent's blockItem.
        TimeZoneList.buildTZChoiceList (self.GetParent().blockItem.itsView, tzChoice)

        tzChoice.Bind(wx.EVT_CHOICE, self.OnTZChoice)
        return tzChoice
        
    def UpdateHeader(self):
        if self.blockItem.dayMode:
            # ugly back-calculation of the previously selected day
            # [Bug 5577]: Do the calculation using date(), or else
            # things go awry near daylight/standard transitions
            reldate = self.blockItem.selectedDate.date() - \
                      self.blockItem.rangeStart.date()
            self.weekColumnHeader.SetSelectedItem(reldate.days+1)
        else:
            self.weekColumnHeader.SetSelectedItem(0)

    def ResizeHeader(self):
        drawInfo = self
        self.weekColumnHeader.Freeze()
        for (i,width) in enumerate(drawInfo.columnWidths):
            originPt = (0, 0)
            extentPt = self.weekColumnHeader.GetItemSize(i)
            extentPt.width = width
            self.weekColumnHeader.SetItemSize(i, extentPt)
        self.weekColumnHeader.Thaw()

    def OnSize(self, event):
        sizeChanged = getattr(self, 'size', None) != self.GetSize()
        self._doDrawingCalculations()
        if sizeChanged:
            # the event canvases base their geometry on the calendar control's
            # size.  On Win32, the calendar control receives OnSize before
            # the canvases do, but on Mac, the canvases calculate their geometry
            # inaccurately.  Refreshing twice is expensive, so it might be
            # preferable for canvases to be more independent about their
            # geometry calculations, but until resize speed is an issue, this
            # is an easy fix.
            self.blockItem.parentBlock.getTimedBlock().widget.RefreshCanvasItems()
            self.blockItem.parentBlock.getAllDayBlock().widget.RefreshCanvasItems()

        self.ResizeHeader()
        event.Skip()

    def wxSynchronizeWidget(self, useHints=False):
        selectedDate = self.blockItem.selectedDate
        startDate = self.blockItem.rangeStart

        # We're just synchronizing the control area,
        # so we only care if the visible range has changed
        if (selectedDate == self.currentSelectedDate and
            startDate == self.currentStartDate):
            return

        # update the calendar with the calender's color
        collection = self.blockItem.contentsCollection
        
        # force the creation of the .color attribute
        # XXX temporary - really this should somehow generate automatically
        colorInfo = ColorInfo(collection)

        # Update the month button given the selected date
        lastDate = startDate + timedelta(days=6)
        months = dateFormatSymbols.getMonths()
        year = lastDate.year
        if (startDate.month == lastDate.month):
            monthText = _(u'%(currentMonth)s %(currentYear)d') % \
                        dict( currentMonth= months[startDate.month - 1],
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

        self.Freeze()
        self.weekColumnHeader.Freeze()
        for day in xrange(7):
            actualDay = ((day + firstDay - 1) % 7)
            currentDate = startDate + timedelta(days=day)
            dayName = u"%s %d" %(shortWeekdays[actualDay + 1],
                                 currentDate.day)
            self.weekColumnHeader.SetLabelText(day + 1, dayName)

        self.weekColumnHeader.Thaw()
        self.Thaw()

        startOfDay = time(tzinfo=ICUtzinfo.floating)
        self.currentSelectedDate = datetime.combine(selectedDate, startOfDay)
        self.currentStartDate = datetime.combine(startDate, startOfDay)

        self.Layout()

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
        return self.OnDaySelect(colIndex - 1)

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
            wxAllDay.GetParent().AdjustAndSetSashPosition(wxAllDay.expandedHeight)
            wxAllDay.autoExpandMode = True
            self.ResetSashState()
        else:
            logger.debug("Collapse to %s" %wxAllDay.collapsedHeight)
            wxAllDay.autoExpandMode = False
            wxAllDay.GetParent().AdjustAndSetSashPosition(wxAllDay.collapsedHeight)
            self.ResetSashState()
        event.Skip()
    

    def GetAllDayBlock(self):
        # @@@ hack that depends on tree structure! would be better to have an
        # allDay reference in calcontainer or calctrl, but that causes
        # initialization order weirdness
        # ALTERNATIVE: findBlockByName?
        return list(list(self.blockItem.parentBlock.childBlocks)[1].childBlocks)[0]

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
            self.weekColumnHeader.SetLabelBitmap(8, self.allDayOpenArrowImage)
            
        elif position - sashsize > wxAllDay.collapsedHeight:
            wxAllDay.autoExpandMode = True
            self.weekColumnHeader.SetLabelBitmap(8, self.allDayCloseArrowImage)
        
    def OnDaySelect(self, day):
        """
        Callback when a specific day is selected from column header.

        @param day: is 0-6
        """
        startDate = self.blockItem.rangeStart
        selectedDate = startDate + timedelta(days=day)

        self.blockItem.postDayMode(True)
        self.blockItem.postDateChanged(selectedDate)

    def OnWeekSelect(self):
        """
        Callback when the 'week' button is clicked on column header.
        """
        self.blockItem.postDayMode(False)
        self.blockItem.postDateChanged(self.blockItem.rangeStart)

    ########## used to be in wxCalendarContainer, then CalendarContainer.  lets try putting here...
    def _doDrawingCalculations(self):
        """
        Sets a bunch of drawing variables.  Some more drawing
        variables are created lazily outside of this function.
        """

        self.size = self.GetSize()

        ### calculate column widths for the all-7-days week view case
        # column layout rules are funky (e.g. bug 3290 and bug 3521)
        # basically the day columns are almost all the same width but
        # when there are rounding errors we distribute the extra
        # pixels among the rightmost columns. When you're resizing,
        # you generalize resize from the right so it looks smoother
        # when you add the extra pixels there. When you resize from
        # the left, the whole screen is changing anyway so we can't
        # make that look any smoother.

        # the sum of all day widths
        allDayWidths = self.size.width - self.scrollbarWidth - self.xOffset

        # the starting point for day widths - an integer, rounded down
        baseDayWidth = allDayWidths / self.blockItem.daysPerView

        # due to rounding there may be up to 6 extra pixels to distribute
        leftover = allDayWidths - baseDayWidth*7
        
        assert leftover == self.size.width - (baseDayWidth*7) - \
                           self.scrollbarWidth - self.xOffset
        
        # evenly distribute the leftover into a tuple of the right length
        # for instance, leftover==4 gives us (0,0,0,1,1,1,1)
        leftoverWidths = (0,) * (7-leftover) + (1,) * leftover

        # now add the extra bits to the individual columns
        dayWidths = (baseDayWidth,) * 7 # like  (80,80,80,80,80,80,80)
        # with 5 leftover, this makes them like (80,80,81,81,81,81,81)
        dayWidths = tuple(map(add, dayWidths, leftoverWidths))
        self.middleWidth = sum(dayWidths)

        # make sure our calculations were correct - we shouldn't have
        # any more leftover pixels
        assert self.middleWidth == allDayWidths

        # finally bring all the lists together in one, and calculate
        # absolute column positions
        self.columnWidths = (self.xOffset,) +dayWidths+ (self.scrollbarWidth,)

        ## e.g. 10,40,40,40 => 0,10,50,90
        self.columnPositions = tuple(sum(self.columnWidths[:i])
                                     for i in range(len(self.columnWidths)))

        # make sure everything adds up - the right side of the last column
        # should be where all the columns added up would be
        assert self.columnPositions[-1]+self.columnWidths[-1] == \
               sum(self.columnWidths)
        

    def _getColumns(self):
        if self.blockItem.dayMode:
            return 1
        else:
            return self.blockItem.daysPerView

    columns = property(_getColumns)

class VisibleHoursEvent(BlockEvent):
    """
    The type of event that gets fired to change the number of visible
    hours. The code running the event should approprately set the
    global CalendarPreferences object as described there.
    """
    visibleHours = schema.One(schema.Integer)


class CalendarViewEvent (ViewEvent):
    """
    A variation of ViewEvent for the calendar that allows the tree of blocks to
    be set to day or week view.
    """
    dayMode = schema.One(schema.Boolean)

