__version__ = "$Revision: 10513 $"
__date__ = "$Date: 2006-05-01 10:30:00 -0700 (Mon, 01 May 2006) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, sys
import wx
from i18n import OSAFMessageFactory as _
from osaf import messages, sharing

"""
Note: need to migrate translation logic to a base wx dialog class that can handle all the work for sub classes
"""

def Show(view):

    win = AutoSyncPrefs(None, -1, "Sync Preferences", view)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
        # Assign the new values
        win.AssignNewValues()

    win.Destroy()
    return val == wx.ID_OK


class AutoSyncPrefs(wx.Dialog):
    def __init__(self, parent, ID, title, view, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Synchronize")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        choice = wx.Choice(self, -1, choices=[])

        interval = sharing.getAutoSyncInterval(view)

        choices = [
            ("Manually", None),
            ("Every 30 minutes", 30),
            ("Every hour", 60),
            ("Every 2 hours", 120),
            ("Every 6 hours", 360),
            ("Every day", 1440),
        ]
        for (text, minutes) in choices:
            newIndex = choice.Append(text)
            choice.SetClientData(newIndex, minutes)
            if interval == minutes:
                choice.SetSelection(newIndex)

        box.Add(choice, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK, u" " + messages.OK + u" ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL, u" " + messages.CANCEL + u" ")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.view = view
        self.choice = choice

    def AssignNewValues(self):
        index = self.choice.GetSelection()
        minutes = self.choice.GetClientData(index)
        sharing.setAutoSyncInterval(self.view, minutes)
