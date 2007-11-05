#   Copyright (c) 2007 Open Source Applications Foundation
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
Dialog box that conditionally runs at startup.
Provides the user with the option of starting Chandler with reload options
"""

# borrowed almost verbatim from StartupOptionsDialog - any mistakes are mine (bear)

import webbrowser
import os, sys, wx, glob
from application.Utility import locateProfileDir
from i18n import ChandlerSafeTranslationMessageFactory as _

MIGRATION_URL          = u'http://chandlerproject.org/migration'
MIGRATION_DIALOG_WIDTH = 450

class UpgradeDialog(wx.Dialog):
    @classmethod
    def run(cls, exception=None):
        dialog = UpgradeDialog(exception)

        result = dialog.ShowModal()

        dialog.Destroy()

        return result

    def __init__(self, exception=None):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        style = wx.CAPTION
        pre.Create(None, -1, _(u"Reload options for Chandler"), 
                   wx.DefaultPosition, wx.DefaultSize, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Construct the controls and lay them out; their member names match 
        # the options they set in Globals.options below.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((0, 3)) 

        staticText    = _(u"Your data repository was created by an incompatible version of Chandler.")
        normalCaption = _(u"Would you like to remove all data and start with a fresh repository?")

        self.msgText = wx.StaticText(self, -1, staticText)
        sizer.Add(self.msgText, flag=wx.ALL, border=5)

        self.normalStartup = wx.RadioButton(self, -1, normalCaption)
        sizer.Add(self.normalStartup, flag=wx.ALL, border=5)
        self.normalStartup.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

        self.exitReload = wx.RadioButton(self, -1, _(u"Click on the link below to learn how to migrate your data and quit Chandler."))
        self.exitReload.SetValue(True)
        sizer.Add(self.exitReload, flag=wx.ALL, border=5)
        self.exitReload.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

        self.linkText = wx.HyperlinkCtrl(self, -1, _(u'Migration Directions'), MIGRATION_URL)
        sizer.Add(self.linkText, flag=wx.ALL, border=5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, -1, _(u"OK"))
        okButton.Bind(wx.EVT_BUTTON, self.onButton)
        box.Add(okButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        sizer.Add(box, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.CenterOnScreen()

    def onButton(self, event):
        if self.exitReload.GetValue():
            result = wx.CANCEL
        else:
            result = wx.OK

        self.EndModal(result)


class MigrationDialog(wx.Dialog):
    @classmethod
    def run(cls, exception=None):
        dialog = MigrationDialog(exception)

        result = dialog.ShowModal()

        dialog.Destroy()

        return result

    def __init__(self, exception=None):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        style = wx.CAPTION
        pre.Create(None, -1, _(u"Incompatible Data"),
                   wx.DefaultPosition, wx.DefaultSize, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((0, 3)) 

        self.msgText1 = wx.StaticText(self, -1, _(u'Your data was created by an incompatible version of Chandler. In order to proceed, all of your existing data must be deleted.'))
        self.msgText1.Wrap(MIGRATION_DIALOG_WIDTH)
        sizer.Add(self.msgText1, flag=wx.ALL, border=5)

        self.msgText2 = wx.StaticText(self, -1, _(u'To preserve your data, select "Move Data" to follow instructions on how to move your data from one version of Chandler to another.'))
        self.msgText2.Wrap(MIGRATION_DIALOG_WIDTH)
        sizer.Add(self.msgText2, flag=wx.ALL, border=5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        cancelButton = wx.Button(self, wx.ID_CANCEL)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancelButton)
        box.Add(cancelButton, flag=wx.ALL, border=5)

        box.Add((0,0), proportion=1, flag=wx.ALL)

        moveButton = wx.Button(self, -1, _(u"&Move Data"))
        moveButton.Bind(wx.EVT_BUTTON, self.onMoveDataButton)
        box.Add(moveButton, flag=wx.ALL, border=5)

        #self.linkText = wx.HyperlinkCtrl(self, -1, _(u'Move Data'), MIGRATION_URL)
        #box.Add(self.linkText, flag=wx.ALL, border=5)

        deleteButton = wx.Button(self, -1, _(u"&Delete Data"))
        deleteButton.Bind(wx.EVT_BUTTON, self.onDeleteDataButton)
        box.Add(deleteButton, flag=wx.ALL, border=5)

        sizer.Add(box, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, border=5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.CenterOnScreen()

        moveButton.SetDefault()
        moveButton.SetFocus()

    def onCancelButton(self, event):
        self.EndModal(wx.CANCEL)

    def onMoveDataButton(self, event):
        webbrowser.open(MIGRATION_URL)
        self.EndModal(wx.CANCEL)

    def onDeleteDataButton(self, event):
        self.EndModal(wx.OK)

