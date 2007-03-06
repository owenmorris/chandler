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
from osaf.pim.mail import SMTPAccount, IMAPAccount
from i18n import MessageFactory

from p2p.account import findAccounts, findDefaultAccounts, findLoggedInAccounts
from p2p.mail import MailAccount
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
        grid = wx.GridSizer(2, 2)

        # Collection name (text control)....
        label = wx.StaticText(self, -1, _m_(u"Collection:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.nameText = wx.TextCtrl(self, -1, u"",
                                    wx.DefaultPosition, [150, -1])
        grid.Add(self.nameText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
                
        # RemoteId (text control):
        label = wx.StaticText(self, -1, _m_(u"From:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.remoteIdText = wx.TextCtrl(self, -1, u"",
                                        wx.DefaultPosition, [150, -1])
        grid.Add(self.remoteIdText, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
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
        grid = wx.GridSizer(5, 2)

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
        label = wx.StaticText(self, -1, _m_(u"Userid:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.useridText = wx.TextCtrl(self, -1, self.userid,
                                      wx.DefaultPosition, [150, -1])
        grid.Add(self.useridText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
                
        # Password (text control):
        label = wx.StaticText(self, -1, _m_(u"Password:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.passwordText = wx.TextCtrl(self, -1, self.password,
                                        wx.DefaultPosition, [150, -1],
                                        wx.TE_PASSWORD)
        grid.Add(self.passwordText, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        # Server (text control)....
        label = wx.StaticText(self, -1, _m_(u"Server:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.serverText = wx.TextCtrl(self, -1, self.server,
                                      wx.DefaultPosition, [150, -1])
        grid.Add(self.serverText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
                
        # SSL (checkbox)....
        label = wx.StaticText(self, -1, _m_(u"Secure connection:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sslCheck = wx.CheckBox(self, -1, "SSL",
                                    wx.DefaultPosition, [150, -1])
        self.sslCheck.SetValue(self.useSSL)
        grid.Add(self.sslCheck, 0, wx.ALIGN_LEFT|wx.ALL, 5)
                
        # Protocol (choice)....
        label = wx.StaticText(self, -1, _m_(u"Over:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.protocolsChoice = wx.Choice(self, -1, choices=PROTOCOL_NAMES)
        grid.Add(self.protocolsChoice, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        self.protocolsChoice.SetSelection(0)

        sizer.Add(grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

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


class MailDialog(wx.Dialog):

    def __init__(self, parent, ID, title):

        pre = wx.PreDialog()
        pre.Create(parent, ID, title, wx.DefaultPosition, wx.DefaultSize,
                   wx.DEFAULT_DIALOG_STYLE)
        self.this = pre.this

    def getAccounts(self, view):

        for account in findDefaultAccounts(view):
            if account.protocol == 'mail':
                self.account = account
                imapAccount = account.imap
                smtpAccount = account.smtp
                break
        else:
            self.account = None
            current = schema.ns('osaf.pim', view).currentSMTPAccount
            smtpAccount = getattr(current, 'item', None)
            current = schema.ns('osaf.pim', view).currentMailAccount
            mailAccount = getattr(current, 'item', None)
            if isinstance(mailAccount, IMAPAccount):
                imapAccount = mailAccount
            else:
                imapAccount = None

        smtpAccounts = [account for account in SMTPAccount.iterItems(view)]
        self.smtpIDs = [account.itsUUID for account in smtpAccounts]
        smtpChoices = [account.displayName for account in smtpAccounts]
        if smtpAccount is not None:
            smtpSelection = smtpChoices.index(smtpAccount.displayName)
        else:
            smtpSelection = 0

        imapAccounts = [account for account in IMAPAccount.iterItems(view)
                        if (account.replyToAddress and
                            account.replyToAddress.emailAddress)]
        self.imapIDs = [account.itsUUID for account in imapAccounts]
        imapChoices = [account.displayName for account in imapAccounts]
        if imapAccount is not None:
            imapSelection = imapChoices.index(imapAccount.displayName)
        else:
            imapSelection = 0

        return (smtpChoices, smtpSelection), (imapChoices, imapSelection)

class SendMailDialog(MailDialog):

    def __init__(self, parent, ID, name, view):

        title = _m_(u'Send "%s" via p2p email' %(name))
        super(MailDialog, self).__init__(parent, ID, title)

        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridSizer(3, 2)

        (smtpChoices, smtpSelection), (imapChoices, imapSelection) = \
            self.getAccounts(view)

        # To (text control)....
        label = wx.StaticText(self, -1, _m_(u"to:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.toText = wx.TextCtrl(self, -1, u'',
                                  wx.DefaultPosition, [200, -1])
        grid.Add(self.toText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
                
        # From (choice)....
        label = wx.StaticText(self, -1, _m_(u"from:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.fromChoice = wx.Choice(self, -1, choices=imapChoices)
        grid.Add(self.fromChoice, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        self.fromChoice.SetSelection(imapSelection)
                
        # Via (choice)....
        label = wx.StaticText(self, -1, _m_(u"via:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.viaChoice = wx.Choice(self, -1, choices=smtpChoices)
        grid.Add(self.viaChoice, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        self.viaChoice.SetSelection(smtpSelection)

        sizer.Add(grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL), 0,
                  wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def getParameters(self, view):

        return {
            'to': self.toText.GetValue(),
            'account': self.account,
            'smtp': view.find(self.smtpIDs[self.viaChoice.GetSelection()]),
            'imap': view.find(self.imapIDs[self.fromChoice.GetSelection()]),
        }

class CheckMailDialog(MailDialog):

    def __init__(self, parent, ID, view):

        super(MailDialog, self).__init__(parent, ID, _m_(u'Check p2p email'))

        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridSizer(3, 2)

        (smtpChoices, smtpSelection), (imapChoices, imapSelection) = \
            self.getAccounts(view)

        # From (text control)....
        label = wx.StaticText(self, -1, _m_(u"from:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.fromText = wx.TextCtrl(self, -1, u'',
                                  wx.DefaultPosition, [200, -1])
        grid.Add(self.fromText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
                
        # In (choice)....
        label = wx.StaticText(self, -1, _m_(u"in:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.inChoice = wx.Choice(self, -1, choices=imapChoices)
        grid.Add(self.inChoice, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        self.inChoice.SetSelection(imapSelection)
                
        # Reply Via (choice)....
        label = wx.StaticText(self, -1, _m_(u"reply via:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.viaChoice = wx.Choice(self, -1, choices=smtpChoices)
        grid.Add(self.viaChoice, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        self.viaChoice.SetSelection(smtpSelection)

        sizer.Add(grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL), 0,
                  wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def getParameters(self, view):

        return {
            'from': self.fromText.GetValue(),
            'account': self.account,
            'smtp': view.find(self.smtpIDs[self.viaChoice.GetSelection()]),
            'imap': view.find(self.imapIDs[self.inChoice.GetSelection()]),
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
        account.subscribe(params['remoteId'], params['name'])


def sendmail(collection):

    view = collection.itsView
    name = collection.displayName
    dialog = SendMailDialog(wx.GetApp().mainFrame, -1, name, view)
    dialog.CenterOnScreen()

    if dialog.ShowModal() == wx.ID_OK:
        params = dialog.getParameters(view)
    else:
        params = None

    dialog.Destroy()

    if params is not None:
        account = params['account']
        commit = False
        if account is None:
            userid, server = params['to'].rsplit('@', 1)
            account = MailAccount(itsView=view, userid=userid, server=server,
                                  smtp=params['smtp'], imap=params['imap'])
            commit = True

        if collection.getACL('p2p', None) is None:
            acl = ACL()
            acl.append(ACE(schema.ns('p2p', view).all.itsUUID,
                           Permissions.READ))
            collection.setACL(acl, 'p2p')
            commit = True

        if commit:
            view.commit()
        account.login(setStatusMessage)
        account.send(params['to'], name)


def checkmail(view):

    dialog = CheckMailDialog(wx.GetApp().mainFrame, -1, view)
    dialog.CenterOnScreen()

    if dialog.ShowModal() == wx.ID_OK:
        params = dialog.getParameters(view)
    else:
        params = None

    dialog.Destroy()

    if params is not None:
        account = params['account']
        commit = False
        if account is None:
            userid, server = params['from'].rsplit('@', 1)
            account = MailAccount(itsView=view, userid=userid, server=server,
                                  smtp=params['smtp'], imap=params['imap'])
            view.commit()

        account.login(setStatusMessage)
        account.check(params['from'], None)


class p2pHandler(Block):

    def on_p2p_SubscribeEvent(self, event):
        subscribe(self.itsView)

    def on_p2p_AccessEvent(self, event):

        sidebar = Block.findBlockByName("Sidebar")
        collection = sidebar.contents.getFirstSelectedItem()
        view = self.itsView

        acl = collection.getACL('p2p', None)
        if acl is None:
            # for now, grant READ to everyone
            acl = ACL()
            acl.append(ACE(schema.ns('p2p', view).all.itsUUID,
                           Permissions.READ))
            collection.setACL(acl, 'p2p')
        else:
            collection.removeACL('p2p')

        view.commit()

    def on_p2p_AccessEventUpdateUI(self, event):

        sidebar = Block.findBlockByName("Sidebar")
        collection = sidebar.contents.getFirstSelectedItem()

        if collection is not None:
            acl = collection.getACL('p2p', None)
            if acl is None:
                op = 'Grant'
            else:
                op = 'Revoke'
            menuTitle = '%s peer access to "%s"' %(op, collection.displayName)
            event.arguments['Enable'] = True
        else:
            event.arguments['Enable'] = False
            menuTitle = 'Grant peer access to ...'

        event.arguments['Text'] = menuTitle

    def on_p2p_LoginEvent(self, event):
        login(self.itsView)

    def on_p2p_SendMailEventUpdateUI(self, event):

        sidebar = Block.findBlockByName("Sidebar")
        collection = sidebar.contents.getFirstSelectedItem()

        if collection is not None:
            menuTitle = 'Send "%s" via p2p email' %(collection.displayName)
            event.arguments['Enable'] = True
        else:
            event.arguments['Enable'] = False
            menuTitle = 'Send ... via p2p email'

        event.arguments['Text'] = menuTitle

    def on_p2p_SendMailEvent(self, event):

        sidebar = Block.findBlockByName("Sidebar")
        collection = sidebar.contents.getFirstSelectedItem()
        
        sendmail(collection)

    def on_p2p_CheckMailEvent(self, event):
        checkmail(self.itsView)
