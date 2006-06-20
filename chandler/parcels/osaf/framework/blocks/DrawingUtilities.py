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


import wx, os, random

from colorsys import hsv_to_rgb, rgb_to_hsv
import Styles

def color2rgb(red, green, blue):
    return red/255.0, green/255.0, blue/255.0

def rgb2color(r, g, b):
    return int(r*255), int(g*255), int(b*255)

def SetTextColorsAndFont(grid, attr, dc, isSelected):
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

# used to be called "DrawWrappedText"
def DrawClippedTextWithDots(dc, string, rect):
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
        

def DrawWrappedText(dc, text, rect, measurements=None):
    """
    Simple wordwrap - draws the text into the current DC
    
    returns the height of the text that was written

    measurements is a FontMeasurements object as returned by
    Styles.getMeasurements()
    """

    if measurements is None:
        measurements = Styles.getMeasurements(dc.GetFont())

    lineHeight = measurements.height
    spaceWidth = measurements.spaceWidth
        
    (rectX, rectY, rectWidth, rectHeight) = rect
    y = rectY
    rectRight = rectX + rectWidth
    rectBottom = rectY + rectHeight

    # we hit this if if you narrow the main window enough:
    # assert rectHeight >= lineHeight, "Don't have enough room to write anything (have %d, need %d)" % (rectHeight, lineHeight)
    if rectHeight < lineHeight: return 0 # Can't draw anything    
    
    for line in text.splitlines():
        x = rectX
        # accumulate text to be written on a line
        thisLine = u''
        for word in line.split():
            width, ignored = dc.GetTextExtent(word)

            # if we wrapped but we still can't fit the word,
            # just truncate it    
            if (width > rectWidth and x == rectX):
                assert thisLine == u'', "Should be drawing first long word"
                DrawClippedText(dc, word, rectX, y, rectWidth, width)
                y += lineHeight
                continue

            # see if we want to jump to the next line
            if (x + width > rectRight):
                # wrapping, so draw the previous accumulated line if any
                if thisLine:
                    dc.DrawText(thisLine, rectX, y)
                    thisLine = u''
                y += lineHeight
                x = rectX
            
            # if we're out of vertical space, just return
            if (y + lineHeight > rectBottom):
                assert thisLine == u'', "shouldn't have any more to draw"
                return y - rectY # total height

            availableWidth = rectRight - x
            if width > availableWidth:
                assert x == rectX and thisLine == u'', "should be writing a long word at the beginning of a line"
                DrawClippedText(dc, word, rectX, y, availableWidth, width)
                x += width
                # x is now past rectRight, so this will force a wrap
            else:
                # rather than draw it, just accumulate it
                thisLine += word + u' '
                x += width + spaceWidth
        
        # draw the last words on this line, if any
        if thisLine:
            dc.DrawText(thisLine, rectX, y)        
        y += lineHeight
    return y - rectY # total height


def DrawClippedText(dc, word, x, y, maxWidth, wordWidth = -1):
    """
    Draw the text, clipping at letter boundaries. This is optimized to
    reduce the number of calls to GetTextExtent by first estimating
    the length of the word that will fit in the given width.

    Note that I did consider some sort of complex quicksearch
    algorithm to find the right fit, but generally you're dealing with
    less than 20 or so characters at a time and you can actually guess
    reasonably accurately even with proportional fonts. This means its
    probably cheaper to just start walking up or down from the guess,
    rather than trying to do a quicksearch -alecf
    """
    if wordWidth < 0:
        # do some initial measurements
        wordWidth, wordHeight = dc.GetTextExtent(word)

    # this is easy, so catch this early
    if wordWidth <= maxWidth:
        dc.DrawText(word, x, y)
        return

    # take a guess at how long the word should be
    testLength = (maxWidth*100/wordWidth)*len(word)/100
    wordWidth, wordHeight = dc.GetTextExtent(word[0:testLength])

    # now check if the guessed length actually fits
    if wordWidth < maxWidth:
        # yep, it fit!
        # keep increasing word until it won't fit
        for newLen in range(testLength, len(word)+1, 1):
            wordWidth, wordHeight = dc.GetTextExtent(word[0:newLen])
            if wordWidth > maxWidth:
                dc.DrawText(word[0:newLen-1], x, y)
                return
        #assert False, "Didn't draw any text!"
    else:
        # no, it didn't fit
        # keep shrinking word until it fits
        for newLen in range(testLength, 0, -1):
            wordWidth,wordHeight = dc.GetTextExtent(word[0:newLen])
            if wordWidth <= maxWidth:
                dc.DrawText(word[0:newLen], x,y)
                return
        #assert False, "Didn't draw any text!"


        
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
        self.hits = 0
        self.misses = 0
    
    def ClearCache(self):
        """
        Clears the gradient cache - used if you just don't need gradients of
        that particular width of height
        """
        self._gradientCache = {}
    
    def MakeGradientBrush(self, offset, bitmapWidth, leftColor, rightColor,
                          orientation):
        """
        Creates a gradient brush from leftColor to rightColor, specified
        as color tuples (r,g,b)
        The brush is a bitmap, width of self.dayWidth, height 1. The color 
        gradient is made by varying the color saturation from leftColor to 
        rightColor. This means that the Hue and Value should be the same, 
        or the resulting color on the right won't match rightColor
        """
        
        # There is probably a nicer way to do this, without:
        # - going through wxImage
        # - individually setting each RGB pixel
        if orientation == "Horizontal":
            image = wx.EmptyImage(bitmapWidth, 1)
        else:
            image = wx.EmptyImage(1, bitmapWidth)
        leftHSV = rgb_to_hsv(*color2rgb(*leftColor))
        rightHSV = rgb_to_hsv(*color2rgb(*rightColor))

        # make sure they are the same hue and brightness
        # XXX: this doesn't quite work, because sometimes division issues
        # cause numbers to be very close, but not quite the same
        # (i.e. 0.4 != 0.40000001 etc)
        #assert leftHSV.hue == rightHSV.hue
        #assert leftHSV.value == rightHSV.value
        
        hue = leftHSV[0]
        value = leftHSV[2]
        satStart = leftHSV[1]
        satDelta = rightHSV[1] - leftHSV[1]
        if bitmapWidth == 0: bitmapWidth = 1
        satStep = satDelta / bitmapWidth
        
        # assign a sliding scale of floating point values from left to right
        # in the bitmap
        offset %= bitmapWidth

        from struct import pack
        bufferX = 0
        imageBuffer = image.GetDataBuffer()
        
        for x in xrange(bitmapWidth):
            
            # first offset the gradient within the bitmap
            # gradientIndex is the index of the color, i.e. the nth
            # color between leftColor and rightColor
            
            # First offset within the bitmap. The + bitmapWidth % bitmapWidth
            # ensures we're dealing with x<offset correctly
            gradientIndex = (x - offset + bitmapWidth) % bitmapWidth
            
            # now offset within the gradient range
            gradientIndex %= bitmapWidth
            
            # now calculate the actual color from the gradient index
            sat = satStart + satStep * gradientIndex
            color = rgb2color(*hsv_to_rgb(hue, sat, value))

            # use the image buffer to write values directly
            # amazingly, this %c techinque to convert
            # is actually faster than either of:
            # chr(color[0]) + chr(color[1]) + chr(color[2])
            # ''.join(map(chr,color))
            imageBuffer[bufferX:bufferX+3] = pack('BBB', *color)

            bufferX += 3
            
        # and now we have to go from Image -> Bitmap. Yuck.
        brush = wx.Brush(wx.WHITE, wx.STIPPLE)
        brush.SetStipple(wx.BitmapFromImage(image))
        return brush
        
    def GetGradientBrush(self, offset, width, leftColor, rightColor,
                         orientation="Horizontal"):
        """
        Gets an appropriately sized gradient brush from the cache, 
        or creates one if necessary
        """
        assert orientation in ("Horizontal", "Vertical")
        key = (offset, width, leftColor, rightColor, orientation)
        brush = self._gradientCache.get(key, None)
        if brush is None:
            self.misses += 1
            brush = self.MakeGradientBrush(*key)
            self._gradientCache[key] = brush
        else:
            self.hits += 1
        return brush

if __name__ == '__main__':
    
    # Test/example of DrawWrappedText
    
    class TestFrame(wx.Frame):
        def __init__(self, *args, **kwds):
            super(TestFrame, self).__init__(*args, **kwds)
            self.Bind(wx.EVT_PAINT, self.OnPaint)
        def OnPaint(self, event):
            dc = wx.PaintDC(self)
            dc.Clear()
            
            padding = 10
            r = wx.Rect(padding, padding, self.GetRect().width - padding*2, self.GetRect().height-padding*2)
            
            dc.DrawRectangle(*iter(r))
            DrawWrappedText(dc, "Resize this window!\n\n  Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.", r)
            
        
    class TestApp(wx.App):
        def OnInit(self):
            frame = TestFrame(None, -1, "Test frame -- resize me!")
            frame.Show(True)
            self.SetTopWindow(frame)
            return True
     
    app = TestApp(0)
    app.MainLoop()
