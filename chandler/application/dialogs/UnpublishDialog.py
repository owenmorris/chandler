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


import os, wx
from osaf import sharing
from i18n import ChandlerMessageFactory as _

def Show(share):
    win = UnpublishDialog(wx.GetApp().mainFrame, -1,
        _(u"Remove From Sharing Account"),
        style=wx.DEFAULT_DIALOG_STYLE, share=share)
    win.CenterOnParent()
    result = win.ShowModal()
    win.Destroy()
    return result

class UnpublishDialog(wx.Dialog):

    def __init__(self, *args, **kwds):

        self.share = kwds['share']
        del kwds['share']
        self.collection = self.share.contents
        account = self.share.conduit.account

        super(UnpublishDialog, self).__init__(*args, **kwds)
        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
            wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.panel = wx.Panel(self, -1)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.messageLabel = wx.StaticText(self.panel, -1,
            _(u"Do you also want to remove this collection from %(account)s?")
            % {'account':account.displayName})
        self.sizer.Add(self.messageLabel, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CancelButton = wx.Button(self.panel, wx.ID_CANCEL)
        self.RemoveButton = wx.Button(self.panel, wx.ID_OK, _(u"Remove"))
        self.DontButton = wx.Button(self.panel, -1, _(u"&Don't Remove"))
        self.RemoveButton.SetDefault()
        self.buttonSizer.Add(self.CancelButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.buttonSizer.Add(self.RemoveButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.buttonSizer.Add(self.DontButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.sizer.Add(self.buttonSizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.sizer)
        self._resize()

        self.Bind(wx.EVT_BUTTON, self.OnRemove, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnDont, id=self.DontButton.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

    def OnRemove(self, evt):
        try:
            sharing.unpublish(self.collection)
        except:
            logger.exception("Failed to unpublish.  Continuing...")
        self.EndModal(True)

    def OnDont(self, evt):
        sharing.CosmoAccount.ignoreCollection(self.collection)
        self.EndModal(True)

    def OnCancel(self, evt):
        self.EndModal(False)


    def _resize(self):
        self.SetMinSize((-1,-1))
        self.SetMaxSize((-1,-1))
        self.SetClientSize(self.sizer.CalcMin())
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
