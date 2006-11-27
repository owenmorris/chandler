#   Copyright (c) 2006-2006 Open Source Applications Foundation
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
MultiStateButton class
"""


import os
import sys
import wx
from wx.lib.buttons import GenBitmapButton

# Variations we support
allVariations = ["normal", "rollover", "selected", "rolloverselected", "mousedown", "mousedownselected", "disabled", "focus"]

class BitmapInfo(object):
    __slots__ = (['stateName'] + allVariations +
                 [ x+"Bitmap" for x in allVariations ])
    def __init__(self, **kwds):
        for (k, v) in kwds.items():
            setattr(self, k, v)

class MultiStateBitmapCache(dict):
    """
    A cache of bitmap sets
    """
    def AddStates(self, multibitmaps, bitmapProvider=wx.Image):
        """
        Add more state bitmaps.
        
        @param multibitmaps: a list of strings/tuples/BitmapInfo's. See
        MultiStateButton.__init__ for a description of this list. More bitmap 
        states can be added at any time.
        """
        firstFoundState = None
        found = False
        for entry in multibitmaps:
            stateName = None
            paths = {}
            bitmaps = {}

            if isinstance(entry, tuple):
                # a tuple with normal and rollover bitmap names
                paths["normal"] = entry[0]
                paths["rollover"] = entry[1]
            elif isinstance(entry, basestring):
                paths["normal"] = entry
                paths["rollover"] = None
            elif isinstance(entry, BitmapInfo):
                stateName = getattr(entry, "stateName", None)
                for variation in allVariations:
                    bitmaps[variation] = getattr(entry, variation + "Bitmap", None)
                    paths[variation] = getattr(entry, variation, None)
            else:
                raise TypeError, "Unknown bitmap entry type"

            if stateName is None:
                assert paths["normal"] is not None
                # The name of the state is the same as the base name of the
                # bitmap
                stateName = os.path.basename(paths["normal"])
                assert len(stateName) > 0

            if not self.has_key(stateName):
                self[stateName] = BitmapInfo()
                for variation in allVariations:
                    if bitmaps.get(variation) is not None:
                        setattr(self[stateName], variation, bitmaps[variation])
                    elif paths.get(variation) is not None:
                        setattr(self[stateName], variation,
                                self._GetBitmapFor(paths[variation], bitmapProvider))
    
                assert self[stateName].normal is not None

            if firstFoundState is None:
                firstFoundState = stateName
        assert firstFoundState is not None
        return firstFoundState

    def _GetBitmapFor(self, bitmapName, bitmapProvider):
        """
        Find the named bitmap, checking various file type extensions (are
        these available inside wx.Image somewhere?)
        
        The design decision here is that the specific type of the image
        is not as important as its name. Indeed, the type of the image can
        change over time to accomodate new technologies. By leaving the
        type unspecified, code does not have to change whenever the file
        format changes.
        """
        bitmap = None
        ##rae
        # is there a more robust list of image types? I made this list up myself..
        for ext in ("png", "gif", "jpg", "tiff", "psd"):
            try:
                img = bitmapProvider("%s.%s" % (bitmapName, ext))
                convert = getattr(img, "ConvertToBitmap", None)
                if convert is not None:
                    bitmap = convert(img)
                else:
                    bitmap = img
                if bitmap is not None:
                    # stop when the bitmap is found
                    break
            except IOError:
                # file was not found
                pass
        if bitmap is not None:
            assert bitmap.GetWidth() > 0
        return bitmap
 
    
class MultiStateButton(GenBitmapButton):
    """
    A MultiStateButton can have multiple bitmaps in its default state. These
    bitmaps are passed in as a list of names, which are also the names of the
    PNG/GIF/JPG/TIFF/PSD bitmaps.
    
    The name of a "state" is the same as the base name of the image. So for
    "/var/image/foo.png", the state name would be "foo"

        mailButton = MultiStateButton(parent_view, 100,
            multibitmaps=["/var/image/NoMail", "/var/image/Mail"])

    will create a button with the two bitmaps Mail.png and
    NoMail.png. The default initial value will be the first named state;
    in this case "NoMail". When desired (presumably when mail comes in),
    the state of the button can be changed thusly:

        mailButton.SetState("/var/image/Mail")

    and the button's bitmap will change to Mail.png. Later, after all the
    mail has been read, the button can be changed back:

        mailButton.SetState("/var/image/NoMail")

    Roll-over bitmaps can be passed in through the use of tuples:

        mailButton = MultiStateButton(parent_view, 100,
            multibitmaps=[("/var/image/NoMail", "/var/image/NoMailRollover"),
                          ("/var/image/Mail",   "/var/image/MailRollover")])

    When the mouse rolls over the button in a particular state, it will
    display the named rollover bitmap.

    Even more control can be exercised through the use of the BitmapInfo
    class. You can specify the normally auto-generated bitmaps for disabled,
    selected and focus states, as well as a separate state name not derived
    from the bitmap name(s).

        no_mail_bitmaps = MultiStateButton.BitmapInfo()
        no_mail_bitmaps.normal      = "/var/image/NoMail"
        no_mail_bitmaps.rollover    = "/var/image/NoMailRollover"
        no_mail_bitmaps.disabled    = "/var/image/NoMailDisabled"
        no_mail_bitmaps.focus       = "/var/image/NoMailFocus"
        no_mail_bitmaps.selected    = "/var/image/NoMailSelected"
        no_mail_bitmaps.stateName   = "ThereIsNoMail"

        mail_bitmaps = MultiStateButton.BitmapInfo()
        mail_bitmaps.normal      = "/var/image/Mail"
        mail_bitmaps.rollover    = "/var/image/MailRollover"
        mail_bitmaps.disabled    = "/var/image/MailDisabled"
        mail_bitmaps.focus       = "/var/image/MailFocus"
        mail_bitmaps.selected    = "/var/image/MailSelected"
        mail_bitmaps.stateName   = "ThereIsSomeMail"

        mailButton = MultiStateButton(parent_view, 100,
            multibitmaps=[no_mail_bitmaps, mail_bitmaps])
        mailButton.SetState("ThereIsSomeMail")

    Obviously this latter method is a lot more verbose

    """
    bitmapCache = MultiStateBitmapCache()
    
    def __init__(self, parent, ID, pos, size, style, multibitmaps=(),
                bitmapProvider=wx.Image, *args, **kwds):
        """
        Initialize the button to the usual button states, plus a list of
        button bitmap filenames and their optional rollover bitmap filenames
        
        @param multibitmaps: a list containing strings/tuples/BitmapInfo's.
        Each item in the list represents a button state, the name of which is
        the base root name of the "normal" bitmap file.

        e.g. /var/share/NoMail.png would become the state "NoMail", and could
        thus be passed in to SetState() as SetState("NoMail").

        If an item in the list is a tuple of two strings, the first string is
        the normal button bitmap filename, while the second is the rollover
        button bitmap filename. The rollover bitmap is displayed when the
        mouse just moves over the button.

        If a BitmapInfo is passed in, it can specify separate bitmaps for each
        possible situation (pressed, rollover, selected, etc) as well as the
        name of the state itself

        """
        self.currentState = None
        self.bitmapProvider = bitmapProvider

        # check to see if there is a tooltip
        help = kwds.get("helpString")
        if help is not None:
            del kwds["helpString"]

        super(MultiStateButton, self).__init__(parent, ID, None, pos, size, style, *args, **kwds)
        firstStateName = self.AddStates(multibitmaps)
        assert firstStateName is not None
        self.SetState(firstStateName)

        # calls to Bind must come after call to super's  __init__
        self.Bind(wx.EVT_ENTER_WINDOW, self._RolloverStart)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._RolloverFinish)

        # add the button's tooltip
        if help is not None:
            self.SetToolTipString(help)

    def AddStates(self, multibitmaps):
        """
        Add more state bitmaps to the button.
        
        @param multibitmaps: a list of strings/tuples/BitmapInfo's. See
        __init__ for a description of this list. More bitmap states can be
        added at any time to the button.
        """
        return self.bitmapCache.AddStates(multibitmaps, 
                                          self.bitmapProvider)

    def SetState(self, inStateName):
        """
        Set the current state name of the button. The appropriate bitmap will
        be used.
        
        @param multibitmaps: a list of strings or tuples of two strings. See
        __init__ for a description of this list. More bitmap states can be
        added at any time to the button.
        """
        enabled = self.IsEnabled()
        self.UpdateWindowUI()
        refresh = (self.IsEnabled() != enabled)
        if inStateName != self.currentState:
            variationMap = (('normal',      self.SetBitmapLabel),
                            ('disabled',    self.SetBitmapDisabled),
                            ('focus',       self.SetBitmapFocus), 
                            ('selected',    self.SetBitmapSelected))

            stateBitmaps = self.bitmapCache.get(inStateName)
            assert stateBitmaps is not None, "invalid state name '" + inStateName + "'"
            assert getattr(stateBitmaps, "normal", None) is not None, "invalid state '" + inStateName + "' is missing 'normal' bitmap"
 
            for variation, method in variationMap:
                bitmap = getattr(stateBitmaps, variation, None)
                if bitmap is not None:
                    method(bitmap)
 
            self.currentState = inStateName
            refresh = True
        if refresh:
            self.Refresh()
            self.Update()

    def _RolloverStart(self, event):
        """
        Change the state of the button to its possible rollover state.
        """
        if self.IsEnabled():
            stateBitmaps = self.bitmapCache[self.currentState]
            assert stateBitmaps is not None
            rolloverBitmap = getattr(stateBitmaps, "rollover", None)
            if rolloverBitmap is not None:
                self.SetBitmapLabel(rolloverBitmap)
                self.Refresh()
                # will the app need this call to Update?
                self.Update()

    def _RolloverFinish(self, event):
        """
        Return the button to its non-rollover state.
        """
        if self.IsEnabled():
            stateBitmaps = self.bitmapCache[self.currentState]
            # only do all this if there was actually a rollover
            if getattr(stateBitmaps, "rollover", None) is not None:
                assert getattr(stateBitmaps, "normal", None) is not None, "invalid state '" + inStateName + "' is missing 'normal' bitmap"
                self.SetBitmapLabel(stateBitmaps.normal)
                self.Refresh()
                # will the app need this call to Update?
                self.Update()

    def GetBackgroundBrush(self, dc):
        # override the GenBitmapButton GetBackgroundBrush(), which assumes you
        # want a white background when a transparent button is pressed
        colBg = self.GetBackgroundColour()
        brush = wx.Brush(colBg, wx.SOLID)
        if self.style & wx.BORDER_NONE:
            myAttr = self.GetDefaultAttributes()
            parAttr = self.GetParent().GetDefaultAttributes()
            myDef = colBg == myAttr.colBg
            parDef = self.GetParent().GetBackgroundColour() == parAttr.colBg
            if myDef and parDef:
                if wx.Platform == "__WXMAC__":
                    brush.MacSetTheme(1) # 1 == kThemeBrushDialogBackgroundActive
                elif wx.Platform == "__WXMSW__":
                    if self.DoEraseBackground(dc):
                        brush = None
            elif myDef and not parDef:
                if self.up:
                    colBg = self.GetParent().GetBackgroundColour()
                    brush = wx.Brush(colBg, wx.SOLID)
                else:
                    brush = wx.Brush(self.faceDnClr, wx.SOLID)
        return brush

# execute with execfile("/Users/rae/work/osaf/rae-button/MultiStateButton.py", { "__name__" :"__main__" })
# or similar
if __name__ == "__main__":
    # for debugging, uncomment the next line
    # import pdb;pdb.set_trace()

    # Change this to where you keep your bitmaps; remember the
    # trailing path separator - it prevents needing os.path code
    dir = "/Users/rae/work/rae-button/"

	# these lines assume you have bitmaps available; you will need to
	# change the absolute paths to bitmaps you have.
    theWindow = wx.Frame(parent=None, id=-1, title="MultiButton testing")
    b = MultiStateButton(theWindow, style=wx.BORDER_NONE,
        multibitmaps = ((dir + "button1", dir + "button4"), 
                        (dir + "button2", dir + "button3")))
    b2 = MultiStateButton(theWindow, style=wx.BORDER_NONE,
        multibitmaps=((dir + "button5", dir + "button4"),
                        (dir + "button2", dir + "button3")))
    b3 = MultiStateButton(theWindow, style=wx.BORDER_NONE,
        multibitmaps=((dir + "button1", dir + "button4"),
                        (dir + "button2", dir + "button3"),
        ))
    box = wx.BoxSizer(wx.HORIZONTAL)
    box.Add(b)
    box.Add(b2)
    box.Add(b3)

    sb = MultiStateButton(theWindow, 1010, style=wx.BORDER_NONE,
         multibitmaps=( (dir + "button1-small", dir + "button4-small"),
                        (dir + "button2-small", dir + "button3-small")))
    sb2 = MultiStateButton(theWindow, 1011, style=wx.BORDER_NONE,
         multibitmaps=((dir + "button5-small", dir + "button4-small"),
                        (dir + "button2-small", dir + "button3-small")))
    sb3 = MultiStateButton(theWindow, 1010, style=wx.BORDER_NONE,
         multibitmaps=((dir + "button1-small", dir + "button4-small"),
                        (dir + "button2-small", dir + "button3-small")))
    box2 = wx.BoxSizer(wx.HORIZONTAL)
    box2.Add(sb)
    box2.Add(sb2)
    box2.Add(sb3)
    box.Add(box2)

    bmi = BitmapInfo()
    bmi.normal = dir + "button1"
    bmi.rollover = dir + "button2"
    # Note: the focus state seems to hang around a bit long
    bmi.focus =    dir + "button3"
    bmi.disabled = dir + "button4"
    bmi.selected = dir + "button5"
    bmi.stateName = "zimbabwe"
    mmb = MultiStateButton(theWindow, 1010, style=wx.BORDER_NONE, multibitmaps=(bmi,))
    box3 = wx.BoxSizer(wx.HORIZONTAL)
    box3.Add(mmb)
    box.Add(box3)

    theWindow.SetSizer(box)
    theWindow.Show()
