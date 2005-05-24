import wx
import os, urlparse, urllib
import application.Globals as Globals
import Sharing, ICalendar
import WebDAV
from repository.item.Query import KindQuery

class PublishCollectionDialog(wx.Dialog):
    
    def __init__(self, parent, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
                 resources=None, view=None, collection=None):
        
        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)
        self.resources = resources
        self.view = view
        self.parent = parent
        self.collection = collection
        
        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        
        self.shareXML = Sharing.getShare(self.collection)
        
        if self.shareXML is None:
            self.ShowPublishPanel()
        else:
            self.ShowManagePanel()

        self.statusPanel = self.resources.LoadPanel(self, "StatusPanel")
        self.statusPanel.Hide()
        self.textStatus = wx.xrc.XRCCTRL(self, "TEXT_STATUS")
       
        self.mySizer.Add(self.mainPanel, 0, wx.GROW|wx.ALL, 5)
        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)        
        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)
        
       
    def ShowPublishPanel(self):
        self.mainPanel = self.resources.LoadPanel(self, "PublishCollection")
        self.buttonPanel = self.resources.LoadPanel(self, 
                                                    "PublishButtonsPanel")       
        self.Bind(wx.EVT_BUTTON, self.OnPublish, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        wx.xrc.XRCCTRL(self,
                       "TEXT_COLLNAME").SetLabel(self.collection.displayName)

        self.currentAccount = Sharing.getWebDAVAccount(self.view)
        self.accounts = self._getSharingAccounts()
        self.accountsControl = wx.xrc.XRCCTRL(self, "CHOICE_ACCOUNT")
        self.accountsControl.Clear()
        for account in self.accounts:
            newIndex = self.accountsControl.Append(account.displayName)
            self.accountsControl.SetClientData(newIndex, account)
            if account is self.currentAccount:
                self.accountsControl.SetSelection(newIndex)
        self.Bind(wx.EVT_CHOICE, self.OnChangeAccount,
                  id=wx.xrc.XRCID("CHOICE_ACCOUNT"))    
                  
        self.existingControl = wx.xrc.XRCCTRL(self, "LISTBOX_EXISTING")
        self._refreshExisting()
        self._suggestName()

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))
        wx.xrc.XRCCTRL(self, "CHECKBOX_ALARMS").Enable(False)
        wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS").Enable(False)        
    
    def OnChangeAccount(self, evt):
        accountIndex = self.accountsControl.GetSelection()
        account = self.accountsControl.GetClientData(accountIndex)
        self.currentAccount = account
        self._refreshExisting()
        self._suggestName()
        
    def _suggestName(self):
        collectionName = self.collection.displayName
        try:
            username = self.currentAccount.username
        except:
            username = ""
        if not username:
            username = "User"
        basename = "%s's %s" % (username, collectionName)
        name = basename
        
        counter = 1
        while name in self.existing:
            name = "%s-%d" % (basename, counter)
            counter += 1
        
        self.publishNameControl = wx.xrc.XRCCTRL(self, "TEXTCTRL_NAME")
            
        self.publishNameControl.SetValue(name)
        self.publishNameControl.SetFocus()
        self.publishNameControl.SetSelection(-1, -1)            
        
        
    def ShowManagePanel(self):
        self.mainPanel = self.resources.LoadPanel(self, "ManageCollection")
        self.buttonPanel = self.resources.LoadPanel(self, 
                                                    "ManageButtonsPanel")
        # self.buttonClipboard = wx.xrc.XRCCTRL(self, "BUTTON_CLIPBOARD")
        # self.buttonDone = wx.xrc.XRCCTRL(self, "BUTTON_DONE")
        self.Bind(wx.EVT_BUTTON, self.OnDone, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnCopy,
                  id=wx.xrc.XRCID("BUTTON_CLIPBOARD"))
        wx.xrc.XRCCTRL(self, "TEXT_MANAGE_COLLNAME").SetLabel(self.collection.displayName)
        wx.xrc.XRCCTRL(self, "TEXT_ACCOUNT").SetLabel(self.shareXML.conduit.account.displayName)
        wx.xrc.XRCCTRL(self, "TEXT_URL").SetLabel(self.shareXML.conduit.getLocation())
        wx.xrc.XRCCTRL(self, "TEXT_SHARINGNAME").SetLabel(self.shareXML.displayName)
        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))
        wx.xrc.XRCCTRL(self, "BUTTON_UNPUBLISH").Enable(False)
        wx.xrc.XRCCTRL(self, "CHECKBOX_ALARMS").Enable(False)
        wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS").Enable(False)
    
    def OnPublish(self, evt):
        self.mainPanel.Enable(False)
        self.buttonPanel.Hide()
        self.mySizer.Detach(self.buttonPanel)
        self.buttonPanel = self.resources.LoadPanel(self, 
                                                    "PublishingButtonsPanel")
        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)
        publishingButton = wx.xrc.XRCCTRL(self, "BUTTON_PUBLISHING")
        publishingButton.Enable(False)
        
        self._clearStatus()
        self._resize()
        wx.Yield()
        
        shareName = self.publishNameControl.GetValue()
        shareNameSafe = urllib.quote_plus(shareName)
        
        accountIndex = self.accountsControl.GetSelection()
        account = self.accountsControl.GetClientData(accountIndex)
        
        shareXML = Sharing.newOutboundShare(self.view, self.collection,
                                            shareName=shareNameSafe,
                                            account=account)
        self.shareXML = shareXML
        shareXML.displayName = shareName
        
        iCalName = "%s.ics" % shareNameSafe
        shareICal = Sharing.newOutboundShare(self.view, self.collection,
                                             shareName=iCalName,
                                             account=account)
        self.shareICal = shareICal
        shareICal.displayName = "%s.ics" % shareName
        
        format = ICalendar.ICalendarFormat(view=self.view)
        shareICal.mode = "put"
        shareICal.format = format
        shareICal.hidden = True
        
        self._showStatus("Wait for Sharing URL...\n")
        if not shareXML.exists():
            self._showStatus("Creating collection on server...")
            shareXML.create()
            self._showStatus(" done.\n")
            
        self._showStatus("Publishing collection to server...")
        shareXML.put()
        self._showStatus(" done.\n")

        self._showStatus("Publishing calendar file to server...")
        shareICal.put()
        self._showStatus(" done.\n")
        
        self._showStatus("%s" % shareXML.getLocation())

        self.buttonPanel.Hide()
        self.mySizer.Detach(self.buttonPanel)
        self.buttonPanel = self.resources.LoadPanel(self, 
                                                    "PublishedButtonsPanel")
        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)  
        
        self.Bind(wx.EVT_BUTTON, self.OnDone, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCopy, 
                  id=wx.xrc.XRCID("BUTTON_CLIPBOARD"))
        self._resize()        
                
    def OnCancel(self, evt):
        self.EndModal(False)
    
    def OnDone(self, evt):
        self.EndModal(True)
        
    def OnCopy(self, evt):
        gotClipboard = wx.TheClipboard.Open()        
        if gotClipboard:
            wx.TheClipboard.SetData(wx.TextDataObject(str(self.shareXML.getLocation())))
            wx.TheClipboard.Close()
                
    def _clearStatus(self):
            self.textStatus.SetLabel("")
            
    def _showStatus(self, msg):
        if not self.statusPanel.IsShown():
            self.mySizer.Insert(1, self.statusPanel, 0, wx.GROW, 5)
            self.statusPanel.Show()
        self.textStatus.SetLabel("%s%s" % (self.textStatus.GetLabel(), msg))
        # self.textStatus.ShowPosition(self.textStatus.GetLastPosition())
        self._resize()
        wx.Yield()

    def _hideStatus(self):
        if self.statusPanel.IsShown():
            self.statusPanel.Hide()
            # self.mySizer.Detach(self.statusPanel)
            self._resize()
        pass
            
    def _resize(self):
        self.mySizer.Layout()
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)
        
    def _getSharingAccounts(self):
        accounts = []
        webDAVAccountKind = self.view.findPath("//parcels/osaf/framework/sharing/WebDAVAccount")
        for account in KindQuery().run([webDAVAccountKind]):
            accounts.append(account)
        accounts.sort(lambda x, y: cmp(str(x.displayName).lower(),
                                       str(y.displayName).lower()))
        return accounts

    def _refreshExisting(self):
        self.existing = self._getExistingFiles()
        self.existingControl.Clear()
        for file in self.existing:
            self.existingControl.Append(file)
                
    def _getExistingFiles(self):
        account = self.currentAccount
        host = account.host
        port = account.port
        username = account.username
        password = account.password
        useSSL = account.useSSL
        sharePath = account.path.strip("/")
       
        client = WebDAV.Client(host, port=port, username=username,
                               password=password, useSSL=useSSL,
                               repositoryView=self.view)
        
 
        scheme = "http"
        if account.useSSL:
            scheme = "https"

        if account.port == 80:
            url = "%s://%s" % (scheme, account.host)
        else:
            url = "%s://%s:%d" % (scheme, account.host, account.port)
        url = urlparse.urljoin(url, sharePath + "/")
        
        existing = []
        skipLen = 1
        if sharePath:
            skipLen += len(sharePath) + 1
        for (resource, etag) in client.ls(url, ignoreCollections=False):
            resource = resource[skipLen:]
            resource = resource.strip("/")
            if resource:
                resource = urllib.unquote_plus(resource)
                existing.append(resource)
        existing.sort()
        return existing

def ShowPublishDialog(parent, view=None, collection=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'parcels', 'osaf', 'framework', 'sharing',
     'PublishCollection_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)
    win = PublishCollectionDialog(parent, "Collection Sharing",
     resources=resources, view=view, collection=collection)
    win.CenterOnScreen()
    win.ShowModal()