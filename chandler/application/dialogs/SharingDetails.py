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

def formatDateTime(view, dt):
    syncDay = calendar.DateTimeUtil.shortDateFormat.format(view, dt)
    syncTime = calendar.formatTime(view, dt)
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
    view = share.itsView
    collection = share.contents
    title = _(u"Sharing details: %(collectionName)s") % {'collectionName': collection.displayName}
    lines = []
    add = lines.append
    add(_(u"Collection name: ") + collection.displayName)
    add(_(u"URL: ") + share.getLocation())
    add(_(u"Last attempted sync: ") + formatDateTime(view, share.lastAttempt))
    add(_(u"Last successful sync: ") + formatDateTime(view, share.lastSuccess))
    if hasattr(share, "error"):
        add(_(u"Last Error: ") + share.error)
    if hasattr(share, "errorDetails"):
        add(_(u"Last Error details: "))
        add(share.errorDetails)

    win = SharingDetailsFrame(parent, -1, title, u'\n\n'.join(lines))
    win.Show()



def ShowText(parent, text, title=_(u"Sharing Details")):
    win = SharingDetailsFrame(parent, -1, title, text)
    win.Show()
    win.CenterOnParent()
