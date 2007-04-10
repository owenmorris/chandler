#   Copyright (c) 2004-2007 Open Source Applications Foundation
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
from osaf.pim import calendar
from i18n import ChandlerMessageFactory as _

def formatDateTime(dt):
    syncDay = calendar.DateTimeUtil.shortDateFormat.format(dt)
    syncTime = calendar.formatTime(dt)
    text = "%s at %s" % (syncDay, syncTime)
    return text

class SharingDetailsFrame(wx.Frame):

    def __init__(self, parent, ID, title, text, *args, **kwds):
        super(SharingDetailsFrame, self).__init__(parent, ID, title,
            *args, **kwds)

        self.text = text

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        textCtrl = wx.TextCtrl(self, -1, text,
            style=wx.TE_MULTILINE|wx.TE_READONLY)
        sizer.Add(textCtrl, 1, wx.EXPAND|wx.ALL, 5)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        button = wx.Button(self, -1, _(u"Close"))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=button.GetId())
        buttonSizer.Add(button, 0, wx.ALL, 5)

        button = wx.Button(self, -1, _(u"Copy to Clipboard"))
        self.Bind(wx.EVT_BUTTON, self.OnCopy, id=button.GetId())
        buttonSizer.Add(button, 0, wx.ALL, 5)

        sizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 5)

    def OnClose(self, evt):
        self.Destroy()

    def OnCopy(self, evt):
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(wx.TextDataObject(self.text))
        wx.TheClipboard.Close()



def Show(parent, share):
    collection = share.contents
    title = _(u"Sharing Details: %s") % share.contents.displayName
    lines = []
    add = lines.append
    add(_(u"Collection name: ") + share.contents.displayName)
    add(_(u"URL: ") + share.getLocation())
    add(_(u"Last attempted sync: ") + formatDateTime(share.lastAttempt))
    add(_(u"Last successful sync: ") + formatDateTime(share.lastSuccess))
    if hasattr(share, "error"):
        add(_(u"Last error: ") + share.error)
    if hasattr(share, "errorDetails"):
        add(_(u"Last error details: "))
        add(share.errorDetails)
    add(_(u"Last statistics: "))
    add(str(share.lastStats))

    win = SharingDetailsFrame(parent, -1, title, u'\n\n'.join(lines))
    win.Show()



def ShowText(parent, text, title=_(u"Sharing Details")):
    win = SharingDetailsFrame(parent, -1, title, text)
    win.Show()
