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


def Show(rv):
    win = ProxiesDialog(wx.GetApp().mainFrame, -1, _(u"Configure Proxy"),
        style=wx.DEFAULT_DIALOG_STYLE, rv=rv)
    win.CenterOnParent()
    win.ShowModal()



class ProxiesDialog(wx.Dialog):

    def __init__(self, *args, **kwds):
        self.rv = kwds.pop('rv')
        super(ProxiesDialog, self).__init__(*args, **kwds)

        self.proxy = sharing.getProxy(self.rv)

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
            wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.panel = wx.Panel(self, -1)

        # Main sizer, vertical box
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddSpacer((280, 8))

        self.proxyCheckbox = wx.CheckBox(self.panel, -1, _(u"Use HTTP Proxy"))
        self.sizer.Add(self.proxyCheckbox, 0,
            wx.ALIGN_LEFT|wx.ALL, 5)



        self.flexHost = wx.FlexGridSizer(2, 2, 2, 2) # rows, cols, hgap, vgap

        self.hostLabel = wx.StaticText(self.panel, -1, _(u"Proxy server:"))
        self.flexHost.Add(self.hostLabel, 1,
            wx.EXPAND|wx.ALIGN_LEFT|wx.ALL, 1)

        self.portLabel = wx.StaticText(self.panel, -1, _(u"Port:"))
        self.flexHost.Add(self.portLabel, 0,
            wx.ALIGN_LEFT|wx.ALL, 1)

        self.hostField = wx.TextCtrl(self.panel, -1, "",
            wx.DefaultPosition, size=(300, -1))
        self.flexHost.Add(self.hostField, 1,
            wx.EXPAND|wx.ALIGN_LEFT|wx.ALL, 3)
        self.hostField.SetValue(self.proxy.host)

        self.portField = wx.TextCtrl(self.panel, -1, "",
            wx.DefaultPosition, size=(50, -1))
        self.flexHost.Add(self.portField, 0,
            wx.ALIGN_LEFT|wx.ALL, 3)
        self.portField.SetValue(str(self.proxy.port))

        self.bypassLabel = wx.StaticText(self.panel, -1, _(u"No proxy for:"))
        self.bypassField = wx.TextCtrl(self.panel, -1, "",
            wx.DefaultPosition) #, size=(300, -1))
        self.bypassField.SetValue(self.proxy.bypass)
        self.bypassExample = wx.StaticText(self.panel, -1,
            _(u"Example: example.com, 192.168.1."))
        self.bypassExample.Enable(False)

        self.authCheckbox = wx.CheckBox(self.panel, -1,
            _(u"Proxy requires authentication"))

        self.flexAuth = wx.FlexGridSizer(2, 2, 2, 2) # rows, cols, hgap, vgap

        self.usernameLabel = wx.StaticText(self.panel, -1, _(u"Username:"))
        self.flexAuth.Add(self.usernameLabel, 1,
            wx.EXPAND|wx.ALIGN_LEFT|wx.ALL, 1)

        self.passwordLabel = wx.StaticText(self.panel, -1, _(u"Password:"))
        self.flexAuth.Add(self.passwordLabel, 0,
            wx.ALIGN_LEFT|wx.ALL, 1)

        self.usernameField = wx.TextCtrl(self.panel, -1, "",
            wx.DefaultPosition, size=(200, -1))
        self.flexAuth.Add(self.usernameField, 1,
            wx.EXPAND|wx.ALIGN_LEFT|wx.ALL, 3)
        self.usernameField.SetValue(self.proxy.username)

        self.passwordField = wx.TextCtrl(self.panel, -1, "",
            wx.DefaultPosition, size=(200, -1), style=wx.TE_PASSWORD)
        self.flexAuth.Add(self.passwordField, 0,
            wx.ALIGN_LEFT|wx.ALL, 3)
        self.passwordField.SetValue(self.proxy.passwd)

        self.proxySizer = wx.BoxSizer(wx.VERTICAL)
        self.proxySizer.Add(self.flexHost, 1, wx.EXPAND|wx.ALL, 1)
        self.proxySizer.Add(self.bypassLabel, 0, wx.EXPAND|wx.ALL, 4)
        self.proxySizer.Add(self.bypassField, 0, wx.EXPAND|wx.ALL, 4)
        self.proxySizer.Add(self.bypassExample, 0, wx.EXPAND|wx.ALL, 4)
        self.proxySizer.Add(self.authCheckbox, 0, wx.EXPAND|wx.ALL, 1)
        self.proxySizer.Add(self.flexAuth, 1, wx.EXPAND|wx.ALL, 1)

        self.sizer.Add(self.proxySizer, 1, wx.EXPAND|wx.ALL, 10)





        # Sizer to contain buttons at bottom, horizontal box
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.CancelButton = wx.Button(self.panel, wx.ID_CANCEL)
        self.OKButton = wx.Button(self.panel, wx.ID_OK)
        self.OKButton.SetDefault()

        self.buttonSizer.Add(self.CancelButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.buttonSizer.Add(self.OKButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.sizer.Add(self.buttonSizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.sizer)



        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
        self.Bind(wx.EVT_CHECKBOX, self.OnProxyCheck,
            id=self.proxyCheckbox.GetId())
        self.Bind(wx.EVT_CHECKBOX, self.OnAuthCheck,
            id=self.authCheckbox.GetId())

        if self.proxy.active:
            self.proxyCheckbox.SetValue(True)

        if self.proxy.useAuth:
            self.authCheckbox.SetValue(True)


        self.OnProxyCheck(None)


    def OnCancel(self, event):
        self.Destroy()

    def OnOK(self, event):
        try:
            self.proxy.port = int(self.portField.GetValue())
        except ValueError:
            dialog = wx.MessageDialog(None,
                _(u"Port number must be an integer"),
                _(u"Invalid Entry"),
                wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()
            return
        self.proxy.host = self.hostField.GetValue()
        self.proxy.username = self.usernameField.GetValue()
        self.proxy.passwd = self.passwordField.GetValue()
        self.proxy.active = bool(self.proxyCheckbox.GetValue() and
            self.proxy.host and self.proxy.port)
        self.proxy.useAuth = bool(self.authCheckbox.GetValue())
        self.proxy.bypass = self.bypassField.GetValue()
        self.rv.commit()
        self.Destroy()

    def OnProxyCheck(self, event):
        self.sizer.Show(self.proxySizer, self.proxyCheckbox.GetValue(),
            recursive=True)
        self.OnAuthCheck(None,
            override=(None if self.proxyCheckbox.GetValue() else False))
        self._resize()

    def OnAuthCheck(self, event, override=None):
        self.proxySizer.Show(self.flexAuth,
            (self.authCheckbox.GetValue() if override is None else override),
            recursive=True)
        self._resize()

    def _resize(self):
        self.SetMinSize((-1,-1))
        self.SetMaxSize((-1,-1))
        self.SetClientSize(self.sizer.CalcMin())
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
