#   Copyright (c) 2006 Open Source Applications Foundation
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

from application import schema
from osaf.framework.blocks.Block import Block
from i18n import MessageFactory

from p2p.account import findDefaultAccounts, findLoggedInAccounts
from repository.item.Access import ACL, ACE, Permissions


_m_ = MessageFactory("Chandler-p2pPlugin")
PROTOCOLS = ['jabber']
PROTOCOL_NAMES = [_m_(u"Jabber")]


def setStatusMessage(msg):
    wx.GetApp().CallItemMethodAsync("MainView", 'setStatusMessage', msg)


class SubscribeDialog(wx.Dialog):

    def __init__(self, parent, ID):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, _m_(u"Subscribe to peer collection"),
                   wx.DefaultPosition, wx.DefaultSize, wx.DEFAULT_DIALOG_STYLE)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Collection name (text control)....
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _m_(u"Collection:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.nameText = wx.TextCtrl(self, -1, u"",
                                    wx.DefaultPosition, [150, -1])
        box.Add(self.nameText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
                
        # RemoteId (text control):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _m_(u"From:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.remoteIdText = wx.TextCtrl(self, -1, u"",
                                    wx.DefaultPosition, [150, -1])
        box.Add(self.remoteIdText, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL), 0,
                  wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def getParameters(self):

        return { 
            'name': self.nameText.GetValue(),
            'remoteId': self.remoteIdText.GetValue(),
        }


class LoginDialog(wx.Dialog):

    def __init__(self, parent, ID, defaultAccounts):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, _m_(u"Login to a peer network"),
                   wx.DefaultPosition, wx.DefaultSize, wx.DEFAULT_DIALOG_STYLE)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        protocol = PROTOCOLS[0]
        for account in defaultAccounts:
            if account.protocol == protocol:
                self.userid = account.userid
                self.server = account.server
                self.password = account.password
                self.useSSL = account.useSSL
                break
        else:
            self.userid = ""
            self.server = ""
            self.password = ""
            self.useSSL = False
        
        # Userid (text control)....
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _m_(u"Userid:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.useridText = wx.TextCtrl(self, -1, self.userid,
                                      wx.DefaultPosition, [150, -1])
        box.Add(self.useridText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
                
        # Password (text control):
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _m_(u"Password:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.passwordText = wx.TextCtrl(self, -1, self.password,
                                        wx.DefaultPosition, [150, -1],
                                        wx.TE_PASSWORD)
        box.Add(self.passwordText, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Server (text control)....
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _m_(u"Server:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.serverText = wx.TextCtrl(self, -1, self.server,
                                      wx.DefaultPosition, [150, -1])
        box.Add(self.serverText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
                
        # SSL (checkbox)....
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _m_(u"Secure connection:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sslCheck = wx.CheckBox(self, -1, "SSL",
                                    wx.DefaultPosition, [150, -1])
        self.sslCheck.SetValue(self.useSSL)
        box.Add(self.sslCheck, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
                
        # Protocol (choice)....
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _m_(u"Over:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.protocolsChoice = wx.Choice(self, -1, choices=PROTOCOL_NAMES)
        box.Add(self.protocolsChoice, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.protocolsChoice.SetSelection(0)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL), 0,
                  wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def getParameters(self):

        return {
            'userid': self.useridText.GetValue(),
            'server': self.serverText.GetValue(),
            'password': self.passwordText.GetValue(),
            'protocol': PROTOCOLS[(self.protocolsChoice.GetSelection())],
            'ssl': self.sslCheck.IsChecked()
        }


def login(view):

    dialog = LoginDialog(wx.GetApp().mainFrame, -1,
                         findDefaultAccounts(view))
    dialog.CenterOnScreen()

    if dialog.ShowModal() == wx.ID_OK:
        params = dialog.getParameters()
    else:
        params = None

    dialog.Destroy()

    if params is not None:
        protocol = params.pop('protocol')
        module = getattr(__import__("p2p.%s" %(protocol)), protocol)
        module.login(view, setStatusMessage,
                     params['userid'], params['server'],
                     params['password'], params['ssl'])


def subscribe(view):

    protocol = PROTOCOLS[0]
    for account in findLoggedInAccounts(view):
        if account.protocol == protocol:
            break
    else:
        login(view)
        return

    dialog = SubscribeDialog(wx.GetApp().mainFrame, -1)
    dialog.CenterOnScreen()

    if dialog.ShowModal() == wx.ID_OK:
        params = dialog.getParameters()
    else:
        params = None

    dialog.Destroy()

    if params is not None:
        account.subscribe(params['name'], params['remoteId'])


class p2pHandler(Block):

    def onSubscribeEvent(self, event):
        subscribe(self.itsView)

    def onAccessEvent(self, event):

        sidebar = Block.findBlockByName("Sidebar")
        collection = sidebar.contents.getFirstSelectedItem()
        view = self.itsView

        # for now, grant READ to everyone
        acl = ACL()
        acl.append(ACE(schema.ns('p2p', view).all.itsUUID, Permissions.READ))
        collection.setACL(acl, 'p2p')

        view.commit()

    def onAccessEventUpdateUI(self, event):

        sidebar = Block.findBlockByName("Sidebar")

        collection = sidebar.contents.getFirstSelectedItem()
        if collection is not None:
            menuTitle = 'Grant peer access to "%s"' %(collection.displayName)
            event.arguments['Enable'] = True
        else:
            event.arguments['Enable'] = False
            menuTitle = 'Grant peer access to ...'

        event.arguments ['Text'] = menuTitle

    def onLoginEvent(self, event):
        login(self.itsView)
