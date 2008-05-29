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

import os
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
        if backup is not None:
            lastMod = os.path.getmtime(backup)
            format = DateFormat.createDateTimeInstance(DateFormat.kFull,
                                                       DateFormat.kFull)
            lastMod = format.format(lastMod)
            title = _(u"Reload Your Data")
            text = _(u"Congratulations on upgrading to a new version of "
                     "Chandler. Would you like to reload your data from the "
                     "backup that was automatically created on %(datetime)s?"
                     "\n\n"
                     "Warning: Before reloading into this version of Chandler, "
                     "make sure you quit the previous version of Chandler "
                     "completely without any problems, as otherwise you may "
                     "lose important edits.") % { 'datetime' : lastMod }
        else:
            title = _(u"Incompatible Data")
            text = _(u"Your data was created by an incompatible version of "
                     "Chandler. You can either proceed and delete all of your "
                     "existing data, or click the Help button for instructions "
                     "on how to manually move your data into this version of "
                     "Chandler.")

        pre = wx.PreDialog()
        style = wx.CAPTION
        pre.Create(None, -1, title, wx.DefaultPosition, wx.DefaultSize, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
                       wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((0, 3))
        
        logo = wx.GetApp().GetImage("Chandler_128.png")
        bitmap = wx.StaticBitmap(self, -1, logo)
        sizer.Add(bitmap, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 15)

        self.msgText = wx.StaticText(self, -1, text)
        self.msgText.Wrap(MIGRATION_DIALOG_WIDTH)
        sizer.Add(self.msgText, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border=15)

        buttonSizer = wx.StdDialogButtonSizer()

        cancelButton = wx.Button(self, wx.ID_CANCEL)
        cancelButton.Bind(wx.EVT_BUTTON, self.onCancelButton)
        buttonSizer.AddButton(cancelButton)

        if backup is not None:
            reloadButton = wx.Button(self, wx.ID_OK, _(u"&Reload Data"), name="Reload Data")
            reloadButton.Bind(wx.EVT_BUTTON, self.onReloadButton)
            buttonSizer.AddButton(reloadButton)
            deleteButton = wx.Button(self, wx.ID_NO, _(u"&Start Fresh"), name="Start Fresh")
        else:
            helpButton = wx.Button(self, wx.ID_NO, _(u"&Help"), name="Help")
            helpButton.Bind(wx.EVT_BUTTON, self.onMoveDataButton)
            buttonSizer.AddButton(helpButton)
            deleteButton = wx.Button(self, wx.ID_OK, _(u"&Start Fresh"), name="Start Fresh")

        deleteButton.Bind(wx.EVT_BUTTON, self.onDeleteDataButton)
        buttonSizer.AddButton(deleteButton)
        buttonSizer.Realize()

        sizer.Add(buttonSizer, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.EXPAND, border=15)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.CenterOnScreen()

        if backup is not None:
            defaultButton = focusButton = reloadButton
        else:
            defaultButton = cancelButton
            focusButton = deleteButton

        defaultButton.SetDefault()
        focusButton.SetFocus()

    def onCancelButton(self, event):
        self.EndModal(wx.CANCEL)

    def onReloadButton(self, event):
        self.EndModal(wx.YES)

    def onMoveDataButton(self, event):
        # webbrowser.open() is known to be unreliable on Linux so using wx instead
        wx.LaunchDefaultBrowser(MIGRATION_URL, wx.BROWSER_NEW_WINDOW)
        self.EndModal(wx.CANCEL)

    def onDeleteDataButton(self, event):
        self.EndModal(wx.OK)
