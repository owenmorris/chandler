#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

import os, wx
from application import styles
import logging
from osaf.framework.blocks import Styles
from osaf import pim

logger = logging.getLogger(__name__)

class TriageButtonImageNotFoundException(Exception): 
    pass

class TriageButtonImageProvider(object):
    """ 
    An "image provider", to be used with MultiStateButtonCache,
    that builds button images eg for the triage buttons.
    
    When an instance is called, it's given an image name that's in a
    particular format: "[status][.variation].png".
    
    We combine a left image (we prepend "Left." on the name given) that
    consists of the left side and wide background of a button image,
    with a right image (duh, "Right." prepended) that's just
    the right edge. On top of that, we draw a label.
    
    We're initialized with a sample image name, which we'll use to 
    load representative left and right images to determine 
    the height of the images we generate.
        
    Note that all the *.Left.* images should be the same size; likewise
    all the *.Left.* images.
    """
    def __init__(self, sampleImageName):
        self.sampleImageName = sampleImageName
    
    def __call__(self, name):
        leftImage, rightImage = self._getSideImages(name)
        imageSize = self.getImageSize(leftImage, rightImage)
        
        bitmap = wx.EmptyBitmap(imageSize[0], imageSize[1])
        dc = wx.MemoryDC(bitmap)
        
        # Ideally, our offscreen bitmaps would have transparent edges, and
        # composite when we draw them to the screen later. However,
        # I couldn't get transparency to work (partly due to bugs in GTK), 
        # so I'm going to hard-code the background for the markup bar buttons
        #
        # Also, the Markup buttons have some gray shadowing on the right and bottom;
        # offset the text a bit for this.
        if name.startswith("Markup"):
            backgroundColor = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
            backgroundBrush = wx.Brush(backgroundColor)
            textXOffset = 1
            textYOffset = 1
        else:
            backgroundBrush = wx.WHITE_BRUSH
            textXOffset = 0
            textYOffset = 1
        
        dc.SetBackground(backgroundBrush);
        dc.Clear()
        rightImageWidth = rightImage.GetWidth()
        leftImageWidth = imageSize[0] - rightImageWidth
            
        # Draw the left image
        dc.SetClippingRect(wx.Rect(0, 0, leftImageWidth, imageSize[1]))
        dc.DrawBitmap(leftImage, 0, 0, True)
        dc.DestroyClippingRegion()

        # Draw the right image
        dc.DrawBitmap(rightImage, imageSize[0] - rightImageWidth, 0, True)

        # Draw the label
        font = self.getTextFont()
        dc.SetFont(font)
        dc.SetTextForeground(wx.WHITE)
        label = self._getTriageButtonLabel(name)
        width, height, descent, leading = dc.GetFullTextExtent(label, font)
        textLeft = ((imageSize[0] - width) / 2) - textXOffset
        textTop = ((imageSize[1] - (height - descent)) / 2) - textYOffset
        dc.DrawText(label, textLeft, textTop)

        del dc
        return bitmap
    
    def getTextFont(self):
        font = getattr(self, 'font', None)
        if font is None:
            fontsize = styles.cfg.get('triagebuttons', 'FontSize.%s' % wx.Platform) or \
                           styles.cfg.get('triagebuttons', 'FontSize') or "10"
            fontweight = styles.cfg.get('triagebuttons', 'FontWeight.%s' % wx.Platform) or \
                           styles.cfg.get('triagebuttons', 'FontWeight') or wx.BOLD
            font = self.font = Styles.getFont(size=int(fontsize), weight=int(fontweight))
        return font

    def getImageSize(self, leftImage=None, rightImage=None):
        imageSize = getattr(self, 'imageSize', None)
        if imageSize is None:
            # Measure the triage values
            aWidget = wx.GetApp().mainFrame
            dc = wx.ClientDC(aWidget)
            oldWidgetFont = aWidget.GetFont()
            textWidth = 0
            textHeight = 0
            font = self.getTextFont()
            dc.SetFont(font)
            aWidget.SetFont(font)
            try:
                for label in self._getTriageButtonLabel(None):
                    width, height, descent, leading = dc.GetFullTextExtent(label, font)
                    if width > textWidth:
                        textWidth = width
                        textHeight = height - descent # ignore descenders when centering vertically
            finally:
                aWidget.SetFont(oldWidgetFont)

            # Measure our images to get the maximum dimension of our buttons.
            if leftImage is None or rightImage is None:
                leftImage, rightImage = self._getSideImages(self.sampleImageName)
            imageSize = leftImage.GetSize()
            imageSize[0] += rightImage.GetWidth()
            padding = int(styles.cfg.get('triagebuttons', 'Padding.%s' % wx.Platform) or \
                          styles.cfg.get('triagebuttons', 'Padding') or 6)
            maxTextWidth = imageSize[0] - padding
            if textWidth < maxTextWidth: # we're not past the limit
                imageSize[0] = textWidth + padding
            self.imageSize = imageSize

        return imageSize

    def _getSideImages(self, name):
        """ Load Left and Right images given the abstract name """
        def loadSideImage(side):
            basename, extension = os.path.splitext(name)
            sideImageName = "%s.%s%s" % (basename, side, extension)
            image = wx.GetApp().GetImage(sideImageName)
            if image is None:
                raise TriageButtonImageNotFoundException, sideImageName
            return image
        return [ loadSideImage(side) for side in "Left", "Right" ]
        
    def _getTriageButtonLabel(self, name):
        """
        Turn an image name (like "Triage.Now.png") into a localized label.
        If name is None, return a list of all possible values; the caller 
        will measure each to find the widest, which will determine the width 
        of the buttons.
        """
        if name is None:
            # it's looking for the widest label - return them all
            return [ pim.getTriageStatusButtonLabel(getattr(pim.TriageEnum, status))
                     for status in pim.TriageEnum.values ]
        else:
            # We were given an image name, like "Triage.Now.png"
            # extract the "Now", convert to lowercase, and get the 
            # localized label to use for it.
            status = getattr(pim.TriageEnum, name.split('.',2)[1].lower())
            return pim.getTriageStatusButtonLabel(status)

