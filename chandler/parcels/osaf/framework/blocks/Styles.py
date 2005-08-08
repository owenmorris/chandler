__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks"

from repository.item.Item import Item
from osaf.pim.items import ContentItem
import application.Globals as Globals
from application import schema
import wx
import logging
from DocumentTypes import ColorType

logger = logging.getLogger(__name__)

class fontFamilyEnumType(schema.Enumeration):
    values = "DefaultUIFont", "SerifFont", "SansSerifFont", "FixedPitchFont"


class Style(schema.Item):
    pass

class CharacterStyle(Style):

    fontFamily = schema.One(
        fontFamilyEnumType, initialValue = 'DefaultUIFont',
    )

    # we default to 11 points, which'll get scaled to the platform's
    # default GUI font
    fontSize = schema.One(schema.Float, initialValue = 11.0)

    # Currently, fontStyle is a string containing any of the following words:
    # bold light italic underline, but others will be included in the future
    fontStyle = schema.One(schema.String, initialValue = '')

    fontName = schema.One(schema.String, initialValue = '')

    def __init__(self, *arguments, **keywords):
        super (CharacterStyle, self).__init__ ( *arguments, **keywords)

class ColorStyle(Style):
    """ 
    Class for Color Style
    Attributes for backgroundColor and foregroundColor
    """

    foregroundColor = schema.One(
        ColorType, initialValue = ColorType(0, 0, 0, 255),
    )

    backgroundColor = schema.One(
        ColorType, initialValue = ColorType(255, 255, 255, 255),
    )

    schema.addClouds(
        sharing = schema.Cloud(foregroundColor, backgroundColor)
    )

        
fontCache = {}
measurementsCache = {}

platformDefaultFaceName = None
platformDefaultFamily = None
platformSizeScalingFactor = 0.0

def getFont(characterStyle):
    # First time, get a couple of defaults
    global platformDefaultFaceName, platformDefaultFamily, platformSizeScalingFactor
    if platformDefaultFaceName is None:
        defaultGuiFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        platformDefaultFaceName = defaultGuiFont.GetFaceName()
        platformDefaultFamily = defaultGuiFont.GetFamily()
        platformSizeScalingFactor = defaultGuiFont.GetPointSize() / 11.0

    # We default to an 11-point font, which gets scaled by the size of the
    # platform's default GUI font (which we measured just above). It's 11
    # because that's the size of the Mac's default GUI font, which is what
    # Mimi thinks in terms of.
    family = platformDefaultFamily
    size = 11
    style = wx.NORMAL
    underline = False
    weight = wx.NORMAL
    name = ""
    
    if characterStyle is not None:
        size = characterStyle.fontSize
        name = characterStyle.fontName        

        if characterStyle.fontFamily == "SerifFont":
            family = wx.ROMAN
        elif characterStyle.fontFamily == "SanSerifFont":
            family = wx.SWISS
        elif characterStyle.fontFamily == "FixedPitchFont":
            family = wx.MODERN
                    
        for theStyle in characterStyle.fontStyle.split():
            lowerStyle = theStyle.lower()
            if lowerStyle == "bold":
                weight = wx.BOLD
            elif lowerStyle == "light":
                weight = wx.LIGHT
            elif lowerStyle == "italic":
                style = wx.ITALIC
            elif lowerStyle == "underline":
                underline = True
        
    if family == platformDefaultFamily:
        name = platformDefaultFaceName

    # Scale the requested size by the platform's scaling factor (then round to int)
    scaledSize = int((platformSizeScalingFactor * size) + 0.5)
    
    # Do we have this already?
    key = (scaledSize, family, style, weight, underline)
    try:
        font = fontCache[key]
    except KeyError:
        font = wx.Font(scaledSize, family, style, weight, underline, name)
        # Don't do this for now: it upsets Linux: assert key == getFontKey(font)
        fontCache[key] = font

    return font

def getFontKey(font):
    key = (font.GetPointSize(), font.GetFamily(), font.GetStyle(), 
           font.GetWeight(), font.GetUnderlined())
    return key
    
def getMeasurements(font):
    key = getFontKey(font)
    try:
        m = measurementsCache[key]
    except KeyError:
        m = FontMeasurements(font)
        measurementsCache[key] = m
    return m

class FontMeasurements(object):
    """ Measurements that we cache with each font """    
    def __init__(self, font):
        aWidget = Globals.mainViewRoot.widget
        dc = wx.ClientDC(aWidget)
        oldWidgetFont = aWidget.GetFont()
        try:
            dc.SetFont(font)
            aWidget.SetFont(font)

            self.height = self.descent = self.leading = 0
            (ignored, self.height, self.descent, self.leading) = \
             dc.GetFullTextExtent("M", font)

            # @@@ These result in too-big boxes - so fake it.
            if False:
                # How big is an instance of each of these controls with this font?
                for (fieldName, ctrl) in {
                    'textCtrlHeight': wx.TextCtrl(aWidget, -1, '', wx.DefaultPosition,
                                                  wx.DefaultSize, wx.STATIC_BORDER),
                    'choiceCtrlHeight': wx.Choice(aWidget, -1, wx.DefaultPosition,
                                                  wx.DefaultSize, ['M']),
                    'checkboxCtrlHeight': wx.CheckBox(aWidget, -1, 'M')
                    }.items():
                    setattr(self, fieldName, ctrl.GetSize()[1])
                    ctrl.Destroy()
                
                # We end up just getting the size of the box if we ask a checkbox,
                # so make sure we're at least as big as the text
                self.checkboxCtrlHeight += self.descent
            else:
                self.textCtrlHeight = self.height + 6
                self.choiceCtrlHeight = self.height + 8
                self.checkboxCtrlHeight  = self.height + 6

        finally:
            aWidget.SetFont(oldWidgetFont)
            
if False:    
    # To try to work out font differences between the platforms, I wrote the
    # following: 
    # 
    # Gather info about each of wx's "specified" defaults:
    for fam in wx.SYS_DEFAULT_GUI_FONT, wx.SYS_OEM_FIXED_FONT, \
        wx.SYS_ANSI_FIXED_FONT, wx.SYS_ANSI_VAR_FONT, wx.SYS_SYSTEM_FONT, \
        wx.SYS_DEVICE_DEFAULT_FONT, wx.SYS_SYSTEM_FONT:
        f = wx.SystemSettings_GetFont(fam)
        logger.debug("%d -> %s, %s %s (%s)" % (fam, f.GetFamily(), f.GetFaceName(), f.GetPointSize(), f.GetFamilyString()))
        
    # Also see what a completely-default Font looks like
    f = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, "")
    logger.debug("default -> %s, %s %s (%s)" % (f.GetFamily(), f.GetFaceName(), f.GetPointSize(), f.GetFamilyString()))
    # On Mac, where the grid uses Lucida Grande 13 when no font is specified, this says:
    #2005-05-09 13:53:43,536 styles DEBUG: 17 -> 70, Lucida Grande 11 (wxDEFAULT)
    #2005-05-09 13:53:43,548 styles DEBUG: 10 -> 70, Lucida Grande 13 (wxDEFAULT)
    #2005-05-09 13:53:43,550 styles DEBUG: 11 -> 70, Lucida Grande 13 (wxDEFAULT)
    #2005-05-09 13:53:43,552 styles DEBUG: 12 -> 70, Lucida Grande 11 (wxDEFAULT)
    #2005-05-09 13:53:43,553 styles DEBUG: 13 -> 70, Lucida Grande 11 (wxDEFAULT)
    #2005-05-09 13:53:43,555 styles DEBUG: 14 -> 70, Lucida Grande 11 (wxDEFAULT)
    #2005-05-09 13:53:43,557 styles DEBUG: 13 -> 70, Lucida Grande 11 (wxDEFAULT)
    #2005-05-09 13:53:43,559 styles DEBUG: default -> 70, Geneva 12 (wxDEFAULT)
    #
    # and this on PC, where the grid uses MS Shell Dlg 8 by default
    #2005-05-09 13:53:24,812 styles DEBUG: 17 -> 74, MS Shell Dlg 8 (wxSWISS)
    #2005-05-09 13:53:24,812 styles DEBUG: 10 -> 74, Terminal 9 (wxSWISS)
    #2005-05-09 13:53:24,812 styles DEBUG: 11 -> 74, Courier 9 (wxSWISS)
    #2005-05-09 13:53:24,812 styles DEBUG: 12 -> 74, MS Sans Serif 9 (wxSWISS)
    #2005-05-09 13:53:24,812 styles DEBUG: 13 -> 74, System 12 (wxSWISS)
    #2005-05-09 13:53:24,812 styles DEBUG: 14 -> 74, System 12 (wxSWISS)
    #2005-05-09 13:53:24,812 styles DEBUG: 13 -> 74, System 12 (wxSWISS)
    #2005-05-09 13:53:24,812 styles DEBUG: default -> 70, MS Sans Serif 12 (wxDEFAULT)
    #2005-05-09 13:53:24,812 styles DEBUG: got font: 70 12.0 -> MS Shell Dlg 8 (wxDEFAULT)    
    #
    # This is interesting because you'd expect the grid to be using one of the
    # selectors above, but it's not: you only get Lucida Grande 13 if you specify
    # SYS_OEM_FIXED_FONT or SYS_ANSI_FIXED_FONT on Mac, and you only get MS Shell
    # Dlg 8 on the PC if you specify DEFAULT_GUI_FONT or use a "completely-default"
    # font.
    # 
    # Anyway, it turns out that Mimi wants the summary view to use Lucida Grande
    # 11 for the grid anyway, so I've modified the Table block to always tell
    # the grid to use something, and that mechanism defaults to DEFAULT_GUI_FONT,
    # so the right thing is now happening.
    # 
    # This means that we don't need to do anything explicitly platform-specific,
    # other than the mechanism above that uses the DEFAULT_GUI_FONT's size as
    # a scaling factor.
