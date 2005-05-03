__version__ = "$Revision: 1.104 $"
__date__ = "$Date: 2005/04/07 01:01:02 $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx, os, random

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
