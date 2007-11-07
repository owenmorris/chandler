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

import webbrowser, os
import wx
from PyICU import DateFormat
from i18n import ChandlerSafeTranslationMessageFactory as _

MIGRATION_URL          = u'http://chandlerproject.org/migration'
MIGRATION_DIALOG_WIDTH = 450

class MigrationDialog(wx.Dialog):
    """
    If we think the user needs to run migration process we will show
    this dialog.
    """
    @classmethod
    def run(cls, backup=None):
        """
        Create and show the dialog.
        
        @param backup: If not None, should be the full path to backup.chex.
        @return: wx.YES means the user wants to reload backup.chex. 
                 wx.OK means the user wants to delete old data and start from
                 scratch.
                 In other cases just quit.
        """
        dialog = MigrationDialog(backup)

        result = dialog.ShowModal()

        dialog.Destroy()

        return result

    def __init__(self, backup=None):
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

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
                       wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        if backup is not None:
            lastMod = os.path.getctime(backup)
            format = DateFormat.createDateTimeInstance(DateFormat.kFull,
                                                       DateFormat.kFull)
            lastMod = format.format(lastMod)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((0, 3)) 

        self.msgText1 = wx.StaticText(self, -1, _(u'Your data was created by an incompatible version of Chandler. In order to proceed, all of your existing data must be deleted.'))
        self.msgText1.Wrap(MIGRATION_DIALOG_WIDTH)
        sizer.Add(self.msgText1, flag=wx.ALL, border=5)

        if backup is not None:
            text = wx.StaticText(self, -1, _(u'To reload your data from the automatically generated Collections and Settings file, which was last modified on %(datetime)s, select "Reload Data".') % {'datetime': lastMod})
            text.Wrap(MIGRATION_DIALOG_WIDTH)
            sizer.Add(text, flag=wx.ALL, border=5)
        
        self.msgText2 = wx.StaticText(self, -1, _(u'To manually preserve your data, select "Move Data" to follow instructions on how to move your data from one version of Chandler to another.'))
        self.msgText2.Wrap(MIGRATION_DIALOG_WIDTH)
        sizer.Add(self.msgText2, flag=wx.ALL, border=5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        cancelButton = wx.Button(self, wx.ID_CANCEL)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancelButton)
        box.Add(cancelButton, flag=wx.ALL, border=5)

        box.Add((0,0), proportion=1, flag=wx.ALL)

        if backup is not None:
            reloadButton = wx.Button(self, -1, _(u"&Reload Data"))
            reloadButton.Bind(wx.EVT_BUTTON, self.onReloadButton)
            box.Add(reloadButton, flag=wx.ALL, border=5)

        moveButton = wx.Button(self, -1, _(u"&Move Data"))
        moveButton.Bind(wx.EVT_BUTTON, self.onMoveDataButton)
        box.Add(moveButton, flag=wx.ALL, border=5)
        # Alternatively could maybe use a link
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

        if backup is not None:
            defaultButton = reloadButton
        else:
            defaultButton = moveButton

        defaultButton.SetDefault()
        defaultButton.SetFocus()

    def onCancelButton(self, event):
        self.EndModal(wx.CANCEL)

    def onReloadButton(self, event):
        self.EndModal(wx.YES)

    def onMoveDataButton(self, event):
        webbrowser.open(MIGRATION_URL)
        self.EndModal(wx.CANCEL)

    def onDeleteDataButton(self, event):
        self.EndModal(wx.OK)
