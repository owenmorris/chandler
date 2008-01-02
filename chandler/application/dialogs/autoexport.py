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

import wx, threading, time
from i18n import ChandlerMessageFactory as _


class AutoExportDialog(wx.Dialog):
    """
    On shutdown we start automatically exporting to enable automatic updates.
    If the export is still going on after a while, we will ask the user if
    they would like to continue. The question dialog will also time out
    automatically and defaults to continuing export.
    
    ShowModal() returns with one of the following values::
        wx.ID_NO:     Never auto-export
        wx.ID_YES:    Always auto-export
        wx.ID_OK:     Continue auto-export
        wx.ID_CANCEL: Skip auto-export
    """
    # XXX Need to still modify dialog, see bug 11444

    COUNTDOWN = 30

    def __init__(self, parent):
        pre = wx.PreDialog()
        pre.Create(parent, -1, _(u"Skip Auto-Export"),
                   wx.DefaultPosition, wx.DefaultSize, wx.DEFAULT_DIALOG_STYLE)
        self.this = pre.this

        icon = wx.Icon('Chandler.egg-info/resources/icons/Chandler_32.ico',
                       wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self,
                              -1,
                              _("""Every time you quit, Chandler automatically exports your data in case you decide to upgrade to a new version. It's taking a long time to export your data. Would you like to:""")
                              )
        label.Wrap(400)
        sizer.Add(label,
                  flag=wx.ALL,
                  border=5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        
        button = wx.Button(self, wx.ID_NO, _(u'&Never Auto-Export'))
        button.Bind(wx.EVT_BUTTON, self.onNeverButton)
        box.Add(button, flag=wx.ALL, border=5)

        button = wx.Button(self, wx.ID_YES, _(u'&Always Auto-Export'))
        button.Bind(wx.EVT_BUTTON, self.onAlwaysButton)
        box.Add(button, flag=wx.ALL, border=5)
        button.SetDefault()

        button = wx.Button(self, wx.ID_CANCEL, _(u'&Skip Auto-Export'))
        button.Bind(wx.EVT_BUTTON, self.onSkipButton)
        box.Add(button, flag=wx.ALL, border=5)

        #button = wx.Button(self, wx.ID_OK, _(u'C&ontinue Auto-Export'))
        #button.Bind(wx.EVT_BUTTON, self.onContinueButton)
        #box.Add(button, flag=wx.ALL, border=5)

        sizer.Add(box, flag=wx.ALL, border=5)

        line = wx.StaticLine(self, -1)
        sizer.Add(line,
                  flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT,
                  border=5)

        label = wx.StaticText(self,
                              -1,
                              _("Note: You can also manually export from File>>Export Collections and Settings... menu."),
                              )
        label.Wrap(400)
        sizer.Add(label,
                  flag=wx.ALL,
                  border=5)

        self.auto = _(u"Export will continue automatically in %(numOf)d seconds.")
        self.status = wx.StaticText(self, -1,
                                    self.auto % {"numOf": self.COUNTDOWN})
        self.status.Wrap(400)
        sizer.Add(self.status, flag=wx.ALL, border=5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.end = None

    def onNeverButton(self, evt):
        self.end = wx.ID_NO

    def onAlwaysButton(self, evt):
        self.end = wx.ID_YES
        
    def onSkipButton(self, evt):
        self.end = wx.ID_CANCEL

    def autoContinue(self):
        countDown = self.COUNTDOWN
        while countDown:
            time.sleep(1)
            countDown -= 1
            if countDown > 0:
                if self.end is not None:
                    wx.CallAfter(self.EndModal, self.end)
                    break
                else:
                    wx.CallAfter(self.status.SetLabel,
                                 self.auto %{'numOf': countDown})
            else:
                wx.CallAfter(self.EndModal, wx.ID_OK)
                break

    def ShowModal(self):
        threading.Thread(target=self.autoContinue).start()

        return super(AutoExportDialog, self).ShowModal()
