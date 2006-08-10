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


import wx
from i18n import ChandlerMessageFactory as _
import i18n

_SITE_CODES = ['us', 'gb', 'de', 'jp']
_SITE_LIST = [
             _(u"Amazon USA"),
             _(u"Amazon UK"),
             _(u"Amazon Germany"),
             _(u"Amazon Japan")
            ]

_CAT_CODES = ['books', 'dvd', 'music']
_CAT_LIST = [
            _(u"Books"),
            _(u"DVD"),
            _(u"Music")
           ]


def promptEmail():
    """
    Displays an Amazon Email Wishlist dialog. The dialog allows the user to choose the
    Amazon site (Amazon US, Amazon UK, Amazon Germany, Amazon Japan) which the Email wishlist is on.

    @rtype: tuple
    @return: tuple containing the Email Address to use and the country code for the Amazon Site
             or a tuple containing (None, None) if no results found.
    """

    return _showDialog(_(u"New Amazon Wish List"),
                       _(u"What is the Amazon email address of the wish list?"),
                         u"", False)

def promptKeywords():
    """
    Displays an Amazon Keyword search dialog. The dialog allows the user to choose the
    Amazon site (Amazon US, Amazon UK, Amazon Germany, Amazon Japan) and the category (Books, DVD, Music)
    which the keyword search is on.

    @rtype: tuple
    @return: tuple containing the search keywords to use, the country code for the Amazon Site, and
             the category to search on or a tuple containing (None, None, None) if no results found.
    """

    return _showDialog(_(u"New Amazon Collection"),
                       _(u"Enter your Amazon search keywords:"),
                         u"Theodore Leung")


def _showDialog(title, message, value, showCategories=True):
    win = _promptAmazonDialog(wx.GetApp().mainFrame, -1, title, message, value, showCategories)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
       # Assign the new values
       value = win.GetValue()

    elif showCategories:
       value = (None, None, None)
    else:
       value = (None, None)

    win.Destroy()

    return value


class _promptAmazonDialog(wx.Dialog):
    def __init__(self, parent, ID, title, message, value, showCategories):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, wx.DefaultPosition, wx.DefaultSize, wx.DEFAULT_DIALOG_STYLE)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this
        self.showCategories = showCategories

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, message)
        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        text = wx.TextCtrl(self, -1, value, wx.DefaultPosition, [350,-1])
        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        if self.showCategories:
            box = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, _(u"Browse by category"))
            box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
            catChoice = wx.Choice(self, -1, choices=_CAT_LIST)
            box.Add(catChoice, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
            sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            catChoice.SetSelection(0)
            self.catChoiceControl = catChoice

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _(u"Select a site to search"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        siteChoice = wx.Choice(self, -1, choices=_SITE_LIST)
        box.Add(siteChoice, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.textControl = text
        self.siteChoiceControl = siteChoice

        siteChoice.SetSelection(self.GetSelectionPosition())

    def GetValue(self):
        if self.showCategories:
            return (
                     self.textControl.GetValue(),
                     _SITE_CODES[self.siteChoiceControl.GetSelection()],
                     _CAT_CODES[self.catChoiceControl.GetSelection()]
                    )

        return (self.textControl.GetValue(), _SITE_CODES[self.siteChoiceControl.GetSelection()])


    def GetSelectionPosition(self):
        localeSet = i18n.getLocaleSet()

        for loc in localeSet:
            try:
                #raises a ValueError if the string does not contain a '_'
                loc.index("_")
                #Strip the country code from the locale string
                loc = loc.split("_")[1]
            except ValueError:
                pass

            for i in xrange(len(_SITE_CODES)):
                if _SITE_CODES[i] == loc.lower():
                    return i
        return 0
