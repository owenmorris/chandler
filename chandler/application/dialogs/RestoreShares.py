#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


import os, sys
import logging
import wx
import wx.xrc
from osaf import sharing
import application.Globals as Globals
from i18n import ChandlerMessageFactory as _
from application import schema
import SubscribeCollection

logger = logging.getLogger(__name__)

MAX_UPDATE_MESSAGE_LENGTH = 50

class RestoreSharesDialog(wx.Dialog):

    def __init__(self, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None):

        wx.Dialog.__init__(self, None, -1, title, pos, size, style)

        self.view = view
        self.resources = resources

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "Restore")
        self.mySizer.Add(self.toolPanel, 0, wx.GROW|wx.ALL, 5)

        self.statusPanel = self.resources.LoadPanel(self, "StatusPanel")
        self.statusPanel.Hide()

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.choiceAccounts = wx.xrc.XRCCTRL(self, "CHOICE_ACCOUNTS")
        self.listShares = wx.xrc.XRCCTRL(self, "LIST_SHARES")
        self.textStatus = wx.xrc.XRCCTRL(self, "TEXT_STATUS")
        self.restoreButton = wx.xrc.XRCCTRL(self, "wxID_OK")
        self.gauge = wx.xrc.XRCCTRL(self, "GAUGE")
        self.gauge.SetRange(100)

        self.currentAccount = sharing.getDefaultAccount(self.view)
        self.choiceAccounts.Clear()
        accounts = sorted(sharing.SharingAccount.iterItems(view),
                          key = lambda x: x.displayName.lower())

        for account in accounts:
            newIndex = self.choiceAccounts.Append(account.displayName)
            self.choiceAccounts.SetClientData(newIndex, account)
            if account is self.currentAccount:
                self.choiceAccounts.SetSelection(newIndex)

        self.PopulateSharesList()

        self.Bind(wx.EVT_CHOICE,
                  self.OnChangeAccount,
                  id=wx.xrc.XRCID("CHOICE_ACCOUNTS"))


        self.Bind(wx.EVT_BUTTON, self.OnRestore, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

        self.subscribing = False

    def OnChangeAccount(self, evt):
        self.hideStatus()
        accountIndex = self.choiceAccounts.GetSelection()
        account = self.choiceAccounts.GetClientData(accountIndex)
        self.currentAccount = account
        self.PopulateSharesList()


    def PopulateSharesList(self):
        self.listShares.Clear()
        try:
            self.showStatus(_(u"Getting list of shares..."))
            if isinstance(self.currentAccount, sharing.CosmoAccount):
                self.shares = self.currentAccount.getPublishedShares()
                self.hideStatus()
                for name, uuid, href, tickets in self.shares:
                    self.listShares.Append(name)

            else:
                existing = sharing.getExistingResources(self.currentAccount)
                self.hideStatus()
                for name in existing:
                    self.listShares.Append(name)

        except Exception, e:
            self.gauge.SetValue(0)
            logger.exception("Error during discovery of shares")
            self.showStatus(_(u"Sharing Error:\n%(error)s") % {'error': e})



    def OnRestore(self, evt):
        view = self.view

        me = schema.ns("osaf.pim", view).currentContact.item

        accountUrl = self.currentAccount.getLocation()
        if not accountUrl.endswith('/'):
            accountUrl += '/'

        self.subscribing = True

        indexes = self.listShares.GetSelections()

        for index in indexes:

            if isinstance(self.currentAccount, sharing.CosmoAccount):
                name, uuid, href, tickets = self.shares[index]
                url = "%smc/%s" % (self.currentAccount.getLocation( ), href)
            else:
                name =  self.listShares.GetString(index)
                url = accountUrl + name
                tickets = None

            share = sharing.findMatchingShare(view, url)
            if share is None:
                SubscribeCollection.Show(view=view, url=url, modal=True,
                    immediate=True, mine=True, publisher=True,
                    tickets=tickets)
                self.listShares.Deselect(index)



        self.subscribing = False
        view.commit()

        self.EndModal(True)


    def showStatus(self, text):

        if not self.statusPanel.IsShown():
            self.mySizer.Add(self.statusPanel, 0, wx.GROW, 5)
            self.statusPanel.Show()

        self.textStatus.SetLabel(text)
        self.resize()

    def hideStatus(self):
        if self.statusPanel.IsShown():
            self.statusPanel.Hide()
            self.mySizer.Detach(self.statusPanel)
            self.resize()

    def resize(self):
        self.mySizer.Layout()
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)


    def OnCancel(self, evt):
        if self.subscribing:
            self.cancelPressed = True
        else:
            self.EndModal(False)

def Show(view=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'RestoreShares.xrc')
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = RestoreSharesDialog(_(u"Restore shared collections"),
     resources=resources, view=view)
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()
