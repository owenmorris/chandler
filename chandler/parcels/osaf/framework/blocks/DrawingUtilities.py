__version__ = "$Revision: 1.104 $"
__date__ = "$Date: 2005/04/07 01:01:02 $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx, os, random
import math
from colorsys import *

def SetTextColorsAndFont (grid, attr, dc, isSelected):
    """
      Set the text foreground, text background, brush and font into the dc
      for grids
    """
    if grid.IsEnabled():
        if isSelected:
            background = grid.GetSelectionBackground()
            foreground = grid.GetSelectionForeground()
        else:
            background = attr.GetBackgroundColour()
            foreground = attr.GetTextColour()
    else:
        background = wx.SystemSettings.GetColour (wx.SYS_COLOUR_BTNFACE)
        foreground = wx.SystemSettings.GetColour (wx.SYS_COLOUR_GRAYTEXT)
    dc.SetTextBackground (background)
    dc.SetTextForeground (foreground)
    dc.SetBrush (wx.Brush (background, wx.SOLID))

    dc.SetFont (attr.GetFont())


def DrawWrappedText (dc, string, rect):
    x = rect.x + 1
    y = rect.y + 1
    for line in unicode(string).split (os.linesep):
        # test for flicker by drawing a random character first each time we draw
        # line = chr(ord('a') + random.randint(0,25)) + line
        
        dc.DrawText (line, x, y)
        lineWidth, lineHeight = dc.GetTextExtent (line)
        # If the text doesn't fit within the box we want to clip it and
        # put '...' at the end.  This method may chop a character in half,
        # but is a lot faster than doing the proper calculation of where
        # to cut off the text.  Eventually we will want a solution that
        # doesn't chop chars, but that will come along with multiline 
        # wrapping and hopefully won't be done at the python level.
        if lineWidth > rect.width - 2:
            width, height = dc.GetTextExtent('...')
            x = rect.x + 1 + rect.width - 2 - width
            dc.DrawRectangle(x, rect.y + 1, width + 1, height)
            dc.DrawText('...', x, rect.y + 1)
        y += lineHeight


# 'color' is 0..255 based
# 'rgb' is 0..1.0 based
def color2rgb(r,g,b):
    return (r*1.0)/255, (g*1.0)/255, (b*1.0)/255
    
def rgb2color(r,g,b):
    return r*255,g*255,b*255

class Gradients(object):
    """
    Gradient cache. 
    Creates and caches gradient bitmaps of size n x 1, going from one color
    to another. It does this by varying the HSV-based saturation so the
    assumption is that the incoming colors are of the same hue.
    
    Note that the brush also requires an offset, which is the offset from the
    VIEWPORT that the brush will be used. Thus if you'll be painting
    something whose left edge is really at x=100, you need to pass in 100
    for the offset. This is because wxWidgets does not have a (working) way
    to offset brushes on all 3 platforms.
    
    TODO: abstract this out to let the user choose left/right or top/bottom
    style gradient cache.
    """
    def __init__(self):
        self.ClearCache()
    
    def ClearCache(self):
        """
        Clears the gradient cache - used if you just don't need gradients of
        that particular width of height
        """
        self._gradientCache = {}
    
    def MakeGradientBitmap(self, offset, width, leftColor, rightColor):
        """
        Creates a gradient brush from leftColor to rightColor, specified
        as color tuples (r,g,b)
        The brush is a bitmap, width of self.dayWidth, height 1. The color 
        gradient is made by varying the color saturation from leftColor to 
        rightColor. This means that the Hue and Value should be the same, 
        or the resulting color on the right won't match rightColor
        """
        # mac requires bitmaps to have a height and width that are powers of 2
        # use frexp to round up to the nearest power of 2
        # (frexp(x) returns (m,e) where x = m * 2**e, and we just want e)
        bitmapWidth = 2**math.frexp(width-1)[1]
        
        # There is probably a nicer way to do this, without:
        # - going through wxImage
        # - individually setting each RGB pixel
        image = wx.EmptyImage(bitmapWidth, 1)
        leftHSV = rgb_to_hsv(*color2rgb(*leftColor))
        rightHSV = rgb_to_hsv(*color2rgb(*rightColor))
        
        # make sure they are the same hue and brightness
        # XXX: this doesn't quite work, because sometimes division issues
        # cause numbers to be very close, but not quite the same
        # (i.e. 0.4 != 0.40000001 etc)
        #assert leftHSV[0] == rightHSV[0]
        #assert leftHSV[2] == rightHSV[2]
        
        hue = leftHSV[0]
        value = leftHSV[2]
        satStart = leftHSV[1]
        satDelta = rightHSV[1] - leftHSV[1]
        if width == 0: width == 1
        satStep = satDelta / width
        
        # assign a sliding scale of floating point values from left to right
        # in the bitmap
        offset %= bitmapWidth
        for x in xrange(bitmapWidth):
            
            # first offset the gradient within the bitmap
            # gradientIndex is the index of the color, i.e. the nth
            # color between leftColor and rightColor
            
            # First offset within the bitmap. The + bitmapWidth % bitmapWidth
            # ensures we're dealing with x<offset correctly
            gradientIndex = (x - offset + bitmapWidth) % bitmapWidth
            
            # now offset within the gradient range
            gradientIndex %= width
            
            # now calculate the actual color from the gradient index
            sat = satStart + satStep*gradientIndex
            newColor = rgb2color(*hsv_to_rgb(hue, sat, value))
            image.SetRGB(x,0,*newColor)
            
        # and now we have to go from Image -> Bitmap. Yuck.
        return wx.BitmapFromImage(image)
        
    def GetGradientBrush(self, offset, width, leftColor, rightColor):
        """
        Gets an appropriately sized gradient brush from the cache, 
        or creates one if necessary
        """
        key = (offset, width, leftColor, rightColor)
        bitmap = self._gradientCache.get(key, None)
        if not bitmap:
            bitmap = self.MakeGradientBitmap(*key)
            self._gradientCache[key] = bitmap
        brush = wx.Brush(wx.WHITE, wx.STIPPLE)
        brush.SetStipple(bitmap)
        return brush
            