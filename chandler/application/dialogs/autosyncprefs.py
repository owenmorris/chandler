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


import wx
from i18n import ChandlerMessageFactory as _
from osaf import sharing

"""
Note: need to migrate translation logic to a base wx dialog class that can handle all the work for sub classes
"""

def Show(view):

    win = AutoSyncPrefs(_(u"Sync Preferences"), view)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
        # Assign the new values
        win.AssignNewValues()

    win.Destroy()
    return val == wx.ID_OK


class AutoSyncPrefs(wx.Dialog):
    def __init__(self, title, view, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(None, -1, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _(u"&Synchronize"))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        choice = wx.Choice(self, -1, choices=[])

        interval = sharing.getAutoSyncInterval(view)

        choices = [
            (_(u"Manually"), None),
            (_(u"Every 30 minutes"), 30),
            (_(u"Every hour"), 60),
            (_(u"Every 2 hours"), 120),
            (_(u"Every 6 hours"), 360),
            (_(u"Every day"), 1440),
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

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL)
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
        self.view.commit()
        
