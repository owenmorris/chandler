import os
import wx
import wx.xrc
import osaf.framework.sharing.Sharing as Sharing
import application.Globals as Globals
from repository.item.Query import KindQuery
import application.dialogs.Util


class ShareToolDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
        self.resources = resources
        self.parent = parent

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "ShareTool")
        self.mySizer.Add(self.toolPanel, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.sharesList = wx.xrc.XRCCTRL(self, "LIST_SHARES")

        # self.currentIndex = None # the list index of account in detail panel

        # self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        # self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.Bind(wx.EVT_BUTTON, self.OnRefresh,
         id=wx.xrc.XRCID("BUTTON_REFRESH"))

        self.Bind(wx.EVT_BUTTON, self.OnCreateShare,
         id=wx.xrc.XRCID("BUTTON_CREATE"))

        self.Bind(wx.EVT_BUTTON, self.OnJoinShare,
         id=wx.xrc.XRCID("BUTTON_JOIN"))

        self.Bind(wx.EVT_BUTTON, self.OnEditShare,
         id=wx.xrc.XRCID("BUTTON_EDIT"))

        self.Bind(wx.EVT_BUTTON, self.OnItems,
         id=wx.xrc.XRCID("BUTTON_ITEMS"))

        self.Bind(wx.EVT_BUTTON, self.OnSyncShare,
         id=wx.xrc.XRCID("BUTTON_SYNC"))

        # self.Bind(wx.EVT_BUTTON, self.OnPutShare,
        #  id=wx.xrc.XRCID("BUTTON_PUT"))

        # self.Bind(wx.EVT_BUTTON, self.OnGetShare,
        #  id=wx.xrc.XRCID("BUTTON_GET"))

        # self.Bind(wx.EVT_LISTBOX, self.OnAccountSel,
        #  id=wx.xrc.XRCID("ACCOUNTS_LIST"))

        # self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

        # Setting focus to the accounts list let's us "tab" to the first
        # text field (without this, on the mac, tabbing doesn't work)
        # self.accountsList.SetFocus()

        self._populateSharesList()

    def _populateSharesList(self):
        # get all share items
        self.sharesList.Clear()
        self.shares = []
        shareKind = self.view.findPath("//parcels/osaf/framework/sharing/Share")
        for item in KindQuery().run([shareKind]):
            self.shares.append(item)
            display = "'%s' -- %s" % (item.getItemDisplayName(),
             item.conduit.getLocation())
            self.sharesList.Append(display)

    def OnRefresh(self, evt):
        self._populateSharesList()

    def OnCreateShare(self, evt):
        share = ShowShareEditorDialog(self.parent, share=None,
         resources=self.resources, view=self.view)
        if share is not None:
            share.create()
            share.put()
        self._populateSharesList()

    def OnJoinShare(self, evt):
        share = ShowShareEditorDialog(self.parent, share=None,
         resources=self.resources, view=self.view, join=True)
        if share is not None:
            share.get()

            # @@@MOR apparently the sidebar code has changed.  the following
            # doesn't work:
            """
            # Add the collection to the sidebar by...
            event = self.view.findPath("//parcels/osaf/views/main/NewItemCollection")
            args = { 'collection' : share.contents }
            # ...creating a new view (which gets returned as args['view'])...
            event.Post(args)
            self.view.commit()
            # ...and selecting that view in the sidebar
            Globals.mainView.selectView(args['view'], showInDetailView=share.contents)
            """
        self._populateSharesList()

    def OnEditShare(self, evt):
        selection = self.sharesList.GetSelection()
        if selection > -1:
            share = self.shares[selection]
            share = ShowShareEditorDialog(self.parent, share=share,
             resources=self.resources, view=self.view)
        self._populateSharesList()

    def OnItems(self, evt):
        selection = self.sharesList.GetSelection()
        if selection > -1:
            share = self.shares[selection]
            ShowCollectionEditorDialog(self.parent, collection=share.contents,
             resources=self.resources, view=self.view)

    def OnSyncShare(self, evt):
        selection = self.sharesList.GetSelection()
        if selection > -1:
            share = self.shares[selection]
            share.sync()  #@@@MOR

    def OnPutShare(self, evt):
        selection = self.sharesList.GetSelection()
        if selection > -1:
            share = self.shares[selection]
            try:
                share.create()  #@@@MOR
            except:
                pass #@@@MOR
            try:
                share.put()
            except Exception, e:
                raise #@@@MOR

    def OnGetShare(self, evt):
        selection = self.sharesList.GetSelection()
        if selection > -1:
            share = self.shares[selection]
            share.get()

    def OnOk(self, evt):
        if self.__Validate():
            self.__ApplyChanges()
            self.EndModal(True)
            # repo.commit()

    def OnCancel(self, evt):
        self.EndModal(False)

    def OnAccountSel(self, evt):
        # Huh? This is always False!
        # if not evt.IsSelection(): return

        sel = evt.GetSelection()
        self.__SwapDetailPanel(sel)

    def OnFocusGained(self, evt):
        """ Select entire text field contents when focus is gained. """
        control = evt.GetEventObject()
        wx.CallAfter(control.SetSelection, -1, -1)


def ShowShareToolDialog(parent, view=None):
        xrcFile = os.path.join(Globals.chandlerDirectory,
         'parcels', 'osaf', 'framework', 'sharing', 'ShareTool_wdr.xrc')
        resources = wx.xrc.XmlResource(xrcFile)
        win = ShareToolDialog(parent, "Share Tool",
         resources=resources, view=view)
        win.CenterOnScreen()
        win.Show(True)






class ShareEditorDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None, share=None, join=False):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
        self.join = join
        self.share = share
        self.resources = resources

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "ShareEditor")
        self.mySizer.Add(self.toolPanel, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.textTitle = wx.xrc.XRCCTRL(self, "TEXT_TITLE")
        wx.EVT_SET_FOCUS(self.textTitle, self.OnFocusGained)
        self.choiceColl = wx.xrc.XRCCTRL(self, "CHOICE_COLL")
        self.textServer = wx.xrc.XRCCTRL(self, "TEXT_SERVER")
        wx.EVT_SET_FOCUS(self.textServer, self.OnFocusGained)
        self.textUsername = wx.xrc.XRCCTRL(self, "TEXT_USERNAME")
        wx.EVT_SET_FOCUS(self.textUsername, self.OnFocusGained)
        self.textPassword = wx.xrc.XRCCTRL(self, "TEXT_PASSWORD")
        wx.EVT_SET_FOCUS(self.textPassword, self.OnFocusGained)
        self.textSharePath = wx.xrc.XRCCTRL(self, "TEXT_SHAREPATH")
        wx.EVT_SET_FOCUS(self.textSharePath, self.OnFocusGained)
        self.textShareName = wx.xrc.XRCCTRL(self, "TEXT_SHARENAME")
        wx.EVT_SET_FOCUS(self.textShareName, self.OnFocusGained)

        if join:
            self.choiceColl.Disable()

        if share is not None:
            self.textTitle.SetValue(share.getItemDisplayName())
            self.textServer.SetValue(share.conduit.host)
            self.textUsername.SetValue(share.conduit.username)
            self.textPassword.SetValue(share.conduit.password)
            self.textSharePath.SetValue(share.conduit.sharePath)
            self.textShareName.SetValue(share.conduit.shareName)

            # self.textServer.Disable()
            # self.textSharePath.Disable()
            # self.textShareName.Disable()
        else:
            self.textTitle.SetValue("Enter a descriptive title")
            account = Sharing.getWebDavAccount()
            if account is not None:
                self.textServer.SetValue(account.host)
                self.textUsername.SetValue(account.username)
                self.textPassword.SetValue(account.password)
                self.textSharePath.SetValue(account.path)
            self.textShareName.SetValue("Enter directory name to use")

        if not join:
            collKind = self.view.findPath("//parcels/osaf/contentmodel/ItemCollection")
            self.collections = []
            i = 1
            for item in KindQuery().run([collKind]):
                self.collections.append(item)
                self.choiceColl.Append(item.getItemDisplayName())
                if item.getItemDisplayName() == "Calendar Demo":
                    defaultChoice = i
                if share is not None and share.contents is not None:
                    if item is share.contents:
                        self.choiceColl.SetSelection(i)
                i += 1
            if share is None or share.contents is None:
                self.choiceColl.SetSelection(defaultChoice)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))
        self.textTitle.SetFocus()

    def OnFocusGained(self, evt):
        """ Select entire text field contents when focus is gained. """
        control = evt.GetEventObject()
        wx.CallAfter(control.SetSelection, -1, -1)


    def OnOk(self, evt):
        title = self.textTitle.GetValue()
        server = self.textServer.GetValue()
        username = self.textUsername.GetValue()
        password = self.textPassword.GetValue()
        sharePath = self.textSharePath.GetValue()
        shareName = self.textShareName.GetValue()

        if not self.join:
            collIndex = self.choiceColl.GetSelection() - 1
            collection = self.collections[collIndex]

        if self.share is None:
            conduit = Sharing.WebDAVConduit(
             host=server,
             sharePath=sharePath,
             shareName=shareName,
             username=username,
             password=password
            )
            if shareName.endswith('.ics'):
                format = Sharing.ICalendarFormat()
            else:
                format = Sharing.CloudXMLFormat()
            if self.join:
                self.share = Sharing.Share(conduit=conduit, format=format)
            else:
                self.share = Sharing.Share(contents=collection, conduit=conduit,
                 format=format)
            self.share.displayName = title
        else:
            self.share.displayName = title
            self.share.conduit.host = server
            self.share.conduit.username = username
            self.share.conduit.password = password
            self.share.conduit.sharePath = sharePath
            self.share.conduit.shareName = shareName
            self.share.contents = collection

        self.EndModal(True)

    def OnCancel(self, evt):
        self.EndModal(False)

    def GetShare(self):
        return self.share

def ShowShareEditorDialog(parent, share=None, join=False, resources=None,
 view=None):
        win = ShareEditorDialog(parent, "Share Editor", share=share, join=join,
         resources=resources, view=view)
        win.CenterOnScreen()
        val = win.ShowModal()
        if val:
            share = win.GetShare()
        else:
            share = None
        win.Destroy()
        return share





class CollectionEditorDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None, collection=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
        self.collection = collection
        self.resources = resources

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "CollectionEditor")
        self.mySizer.Add(self.toolPanel, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.textName = wx.xrc.XRCCTRL(self, "TEXT_COLLNAME")
        self.listItems = wx.xrc.XRCCTRL(self, "LIST_ITEMS")

        self.textName.SetValue(self.collection.getItemDisplayName())
        self._populateList()

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)

        self.Bind(wx.EVT_BUTTON, self.OnRemove,
         id=wx.xrc.XRCID("BUTTON_REMOVE"))

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

    def _populateList(self):
        self.items = []
        self.listItems.Clear()
        i = 0
        for item in self.collection:
            self.items.append(item)
            self.listItems.Append(item.getItemDisplayName())
            i += 1

    def OnOk(self, evt):
        self.EndModal(True)

    def OnRemove(self, evt):
        selection = self.listItems.GetSelection()
        if selection > -1:
            item = self.items[selection]
            self.collection.remove(item)
        self._populateList()


def ShowCollectionEditorDialog(parent, collection=None, resources=None,
 view=None):
        win = CollectionEditorDialog(parent, "Collection Editor",
         collection=collection, resources=resources, view=view)
        win.CenterOnScreen()
        win.ShowModal()
        win.Destroy()
