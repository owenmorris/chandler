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


def Show(collection):
    win = InviteFrame(None, -1, _(u"Invite"), style=wx.DEFAULT_FRAME_STYLE,
        collection=collection)
    win.Show()



class InviteFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        self.collection = kwds['collection']
        del kwds['collection']
        super(InviteFrame, self).__init__(*args, **kwds)

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
            wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.panel = wx.Panel(self, -1)

        # Main sizer, vertical box
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        msg = _(u"Give out the URL(s) below to invite others to subscribe to "
            "'%(collection)s':") % {'collection' : self.collection.displayName}

        share = sharing.getShare(self.collection)
        urlString = (os.linesep * 2).join(sharing.getLabeledUrls(share))
        msg = "%s\n\n%s" % (msg, urlString)
        self.msgCtrl = wx.TextCtrl(self.panel, -1, msg,
            style=wx.TE_MULTILINE|wx.TE_READONLY)

        self.sizer.Add(self.msgCtrl, 1,
            wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)



        # Sizer to contain buttons at bottom, horizontal box
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.CancelButton = wx.Button(self.panel, wx.ID_CANCEL)
        self.CopyButton = wx.Button(self.panel, wx.ID_OK, _(u"&Copy URL(s)"))
        self.CopyButton.SetDefault()

        self.buttonSizer.Add(self.CancelButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.buttonSizer.Add(self.CopyButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.sizer.Add(self.buttonSizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)



        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.sizer)
        self.panel.Layout()
        self.sizer.Fit(self.panel)

        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnCopy, id=wx.ID_OK)

    def OnCancel(self, event):
        self.Destroy()

    def OnCopy(self, event):
        gotClipboard = wx.TheClipboard.Open()
        if gotClipboard:
            share = sharing.getShare(self.collection)
            urlString = (os.linesep * 2).join(sharing.getLabeledUrls(share))
            wx.TheClipboard.SetData(wx.TextDataObject(unicode(urlString)))
            wx.TheClipboard.Close()
