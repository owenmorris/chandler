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


"""
Dialog box that implements the repository's password entry protocol.
"""

import wx
from i18n import ChandlerSafeTranslationMessageFactory as _

# see StartupOptionsDialog.py

class GetPasswordDialog(wx.Dialog):

    def __init__(self, create, msg):

        pre = wx.PreDialog()
        if create:
            title = _(u"Create Repository Password")
        else:
            title = _(u"Enter Repository Password")

        pre.Create(None, -1, title, wx.DefaultPosition, wx.DefaultSize,
                   wx.DEFAULT_DIALOG_STYLE)
        self.this = pre.this

        sizer = wx.BoxSizer(wx.VERTICAL)
        if create:
            grid = wx.GridSizer(2, 2)
        else:
            grid = wx.GridSizer(1, 2)

        # Enter Password (text control):
        label = wx.StaticText(self, -1, _(u"Enter password:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.passwordText = wx.TextCtrl(self, -1, u"",
                                        wx.DefaultPosition, [150, -1],
                                        wx.TE_PASSWORD)
        grid.Add(self.passwordText, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        if create:
            # Confirm Password (text control):
            label = wx.StaticText(self, -1, _(u"Confirm password:"))
            grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

            self.confirmText = wx.TextCtrl(self, -1, u"",
                                           wx.DefaultPosition, [150, -1],
                                           wx.TE_PASSWORD)
            grid.Add(self.confirmText, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        else:
            self.confirmText = None

        if msg:
            # Message (static text control):
            label = wx.StaticText(self, -1, msg)
            grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.Add(grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL), 0,
                  wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def getEntries(self):

        entries = { 'password': self.passwordText.GetValue() }
        if self.confirmText is not None:
            entries['confirmed'] = self.confirmText.GetValue()

        return entries


def getPassword(create=False, again=False):

    msg = None

    while True:
        if again:
            msg = _(u"Invalid password")

        dialog = GetPasswordDialog(create, msg)
        dialog.CenterOnScreen()

        try:
            if dialog.ShowModal() == wx.ID_OK:
                entries = dialog.getEntries()
            else:
                return ''

            if create and entries['password'] != entries['confirmed']:
                msg = _(u"Passwords did not match")
            else:
                return entries['password']

        finally:
            dialog.Destroy()
