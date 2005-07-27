# The collection publishing dialog
# Invoke using the ShowPublishDialog( ) method.

import wx
import traceback, logging
import os, urlparse, urllib
import application.Globals as Globals
import Sharing, ICalendar
import WebDAV
import zanshin.webdav
import zanshin.util

logger = logging.getLogger('Sharing')
logger.setLevel(logging.INFO)

class PublishCollectionDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
                 resources=None, view=None, collection=None,
                 filterKindPath=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)
        self.resources = resources
        self.view = view
        self.parent = parent
        self.collection = collection    # The collection to share

        # List of kinds (paths) to share
        if filterKindPath is None:
            self.filterKinds = []
        else:
            self.filterKinds = [filterKindPath]

        self.mySizer = wx.BoxSizer(wx.VERTICAL)

        # Is this collection already shared?
        self.shareXML = Sharing.getShare(self.collection)

        if self.shareXML is None:       # Not yet shared, show "Publish"
            self.mainPanel = self.resources.LoadPanel(self,
                                                      "PublishCollection")
            self.buttonPanel = self.resources.LoadPanel(self,
                                                        "PublishButtonsPanel")
        else:                           # Already shared, show "Manage"
            self.mainPanel = self.resources.LoadPanel(self, "ManageCollection")
            self.buttonPanel = self.resources.LoadPanel(self,
                                                        "ManageButtonsPanel")


        # Create/Hide the status panel that appears when there is text to
        # display
        self.statusPanel = self.resources.LoadPanel(self, "StatusPanel")
        self.statusPanel.Hide()
        self.textStatus = wx.xrc.XRCCTRL(self, "TEXT_STATUS")

        # Fit all the pieces together
        self.mySizer.Add(self.mainPanel, 0, wx.GROW|wx.ALL, 5)
        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)
        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        if self.shareXML is None:       # Not yet shared, show "Publish"
            self.ShowPublishPanel()
        else:                           # Already shared, show "Manage"
            self.ShowManagePanel()


    def ShowPublishPanel(self):
        # "Publish" mode -- i.e., the collection has not yet been shared

        self.Bind(wx.EVT_BUTTON, self.OnPublish, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        collName = Sharing.getFilteredCollectionDisplayName(self.collection,
                                                            self.filterKinds)
        wx.xrc.XRCCTRL(self,
                       "TEXT_COLLNAME").SetLabel(collName)

        self.currentAccount = Sharing.getWebDAVAccount(self.view)

        # Populate the listbox of sharing accounts
        self.accounts = self._getSharingAccounts()
        self.accountsControl = wx.xrc.XRCCTRL(self, "CHOICE_ACCOUNT")
        self.accountsControl.Clear()

        for account in self.accounts:
            newIndex = self.accountsControl.Append(account.displayName)
            self.accountsControl.SetClientData(newIndex, account)
            if account is self.currentAccount:
                self.accountsControl.SetSelection(newIndex)

        self.Bind(wx.EVT_CHOICE,
                  self.OnChangeAccount,
                  id=wx.xrc.XRCID("CHOICE_ACCOUNT"))

        self.CheckboxShareAlarms = wx.xrc.XRCCTRL(self, "CHECKBOX_ALARMS")
        self.CheckboxShareAlarms.SetValue(True)
        self.CheckboxShareStatus = wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS")
        self.CheckboxShareStatus.SetValue(True)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))


    def ShowManagePanel(self):
        # "Manage" mode -- i.e., the collection has already been shared

        self.Bind(wx.EVT_BUTTON, self.OnManageDone, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnCopy,
                  id=wx.xrc.XRCID("BUTTON_CLIPBOARD"))

        name = self.collection.displayName
        wx.xrc.XRCCTRL(self, "TEXT_MANAGE_COLLNAME").SetLabel(name)

        name = self.shareXML.conduit.account.displayName
        wx.xrc.XRCCTRL(self, "TEXT_ACCOUNT").SetLabel(name)

        url = self.shareXML.conduit.getLocation()
        wx.xrc.XRCCTRL(self, "TEXT_URL").SetLabel(url)

        # Not yet supported
        wx.xrc.XRCCTRL(self, "BUTTON_UNPUBLISH").Enable(False)

        # Controls for managing filtered shares:

        self.RadioItems = wx.xrc.XRCCTRL(self, "RADIO_ITEMS")
        self.RadioItemsHidden = wx.xrc.XRCCTRL(self, "RADIO_ITEMS_HIDDEN")
        self.RadioItemsHidden.Hide()
        wx.EVT_RADIOBUTTON(self.RadioItems,
                           self.RadioItems.GetId(),
                           self.OnAllItemsClicked)

        self.CheckboxMail = wx.xrc.XRCCTRL(self, "CHECK_MAIL")
        wx.EVT_CHECKBOX(self.CheckboxMail,
                        self.CheckboxMail.GetId(),
                        self.OnFilterClicked)

        self.CheckboxTasks = wx.xrc.XRCCTRL(self, "CHECK_TASKS")
        wx.EVT_CHECKBOX(self.CheckboxTasks,
                        self.CheckboxTasks.GetId(),
                        self.OnFilterClicked)

        self.CheckboxEvents = wx.xrc.XRCCTRL(self, "CHECK_EVENTS")
        wx.EVT_CHECKBOX(self.CheckboxEvents,
                        self.CheckboxEvents.GetId(),
                        self.OnFilterClicked)

        self.CheckboxShareAlarms = wx.xrc.XRCCTRL(self, "CHECKBOX_ALARMS")
        self.CheckboxShareAlarms.Enable(True)
        self.CheckboxShareStatus = wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS")
        self.CheckboxShareStatus.Enable(True)

        self.filterKinds = self.shareXML.filterKinds

        self._loadKindFilterState()
        self._loadAttributeFilterState(self.shareXML)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

    def OnChangeAccount(self, evt):
        self._hideStatus()

        accountIndex = self.accountsControl.GetSelection()
        account = self.accountsControl.GetClientData(accountIndex)
        self.currentAccount = account


    def _suggestName(self):
        # Figure out a name that doesn't already exist, by appending a hyphen
        # and a number

        basename = self.collection.displayName
        name = basename

        counter = 1
        while name in self.existing:
            name = "%s-%d" % (basename, counter)
            counter += 1

        return name


    def OnManageDone(self, evt):
        self._saveKindFilterState()
        for share in self.collection.shares:
            self._saveAttributeFilterState(share)
        self.EndModal(False)

    def _loadAttributeFilterState(self, share):
        self.CheckboxShareAlarms.SetValue("reminderTime" not in \
                                          share.filterAttributes)
        self.CheckboxShareStatus.SetValue("transparency" not in \
                                          share.filterAttributes)


    def _saveAttributeFilterState(self, share):
        if not self.CheckboxShareAlarms.GetValue():
            if "reminderTime" not in share.filterAttributes:
                share.filterAttributes.append("reminderTime")
        else:
            if "reminderTime" in share.filterAttributes:
                share.filterAttributes.remove("reminderTime")

        if not self.CheckboxShareStatus.GetValue():
            if "transparency" not in share.filterAttributes:
                share.filterAttributes.append("transparency")
        else:
            if "transparency" in share.filterAttributes:
                share.filterAttributes.remove("transparency")


    def _loadKindFilterState(self):
        # Based on which kinds are listed in filterKinds, update the UI

        if len(self.filterKinds) == 0:      # No filtering

            self.RadioItems.SetValue(True)
            self.CheckboxMail.SetValue(False)
            self.CheckboxTasks.SetValue(False)
            self.CheckboxEvents.SetValue(False)

        else:                               # Filtering

            # Unset the "My items" radio button
            self.RadioItemsHidden.SetValue(True)

            # Conditionally set the individual kind checkboxes:

            path = "//parcels/osaf/contentmodel/mail/MailMessageMixin"
            if path in self.filterKinds:
                self.CheckboxMail.SetValue(True)
            else:
                self.CheckboxMail.SetValue(False)

            path = "//parcels/osaf/contentmodel/tasks/TaskMixin"
            if path in self.filterKinds:
                self.CheckboxTasks.SetValue(True)
            else:
                self.CheckboxTasks.SetValue(False)

            path = "//parcels/osaf/contentmodel/calendar/CalendarEventMixin"
            if path in self.filterKinds:
                self.CheckboxEvents.SetValue(True)
            else:
                self.CheckboxEvents.SetValue(False)


    def _saveKindFilterState(self):
        # Examine the values in the UI and make the appropriate changes to the
        # Share's filter

        self.filterKinds = []

        if not self.RadioItems.GetValue():  # Filtering

            if self.CheckboxMail.GetValue():
                path = "//parcels/osaf/contentmodel/mail/MailMessageMixin"
                self.filterKinds.append(path)

            if self.CheckboxTasks.GetValue():
                path = "//parcels/osaf/contentmodel/tasks/TaskMixin"
                self.filterKinds.append(path)

            if self.CheckboxEvents.GetValue():
                path = "//parcels/osaf/contentmodel/calendar/CalendarEventMixin"
                self.filterKinds.append(path)

        self.shareXML.filterKinds = self.filterKinds




    def OnAllItemsClicked(self, evt):
        # Clear the filter kinds list

        self.filterKinds = []
        self._loadKindFilterState()


    def OnFilterClicked(self, evt):
        # If any individual kind checkbox is clicked, unset "My items"

        self.RadioItems.SetValue(False)

    def OnPublish(self, evt):
        # Publish the collection


        # Update the UI by disabling/hiding various panels, and swapping in a
        # new set of buttons
        self.mainPanel.Enable(False)
        self.buttonPanel.Hide()
        self.mySizer.Detach(self.buttonPanel)
        self.buttonPanel = self.resources.LoadPanel(self,
                                                    "PublishingButtonsPanel")
        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)
        publishingButton = wx.xrc.XRCCTRL(self, "BUTTON_PUBLISHING")
        publishingButton.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnPublishDone, id=wx.ID_CANCEL)

        self._clearStatus()
        self._resize()
        wx.Yield()

        try:

            # Populate the list of existing shares on the selected webdav server
            self.existing = self._getExistingFiles()
            suggestedName = self._suggestName()
            shareName = suggestedName
            shareNameSafe = urllib.quote_plus(shareName.encode('utf-8'))
            accountIndex = self.accountsControl.GetSelection()
            account = self.accountsControl.GetClientData(accountIndex)

            # Create the main share object
            shareXML = Sharing.newOutboundShare(self.view,
                                                self.collection,
                                                kinds=self.filterKinds,
                                                shareName=shareNameSafe,
                                                account=account)
            self.shareXML = shareXML
            shareXML.displayName = shareName
            self._saveAttributeFilterState(shareXML)

            # Create the secondary (.ics) share object
            iCalName = "%s.ics" % shareNameSafe
            shareICal = Sharing.newOutboundShare(self.view,
                                                 self.collection,
                                                 kinds=self.filterKinds,
                                                 shareName=iCalName,
                                                 account=account)
            self.shareICal = shareICal
            shareICal.displayName = "%s.ics" % shareName
            self._saveAttributeFilterState(shareICal)

            # For the .ics share, use ICalendarFormat instead
            format = ICalendar.ICalendarFormat(view=self.view)
            shareICal.mode = "put"
            shareICal.format = format
            shareICal.hidden = True

            self._showStatus("Wait for Sharing URLs...\n")
            if shareXML.exists():
                raise Sharing.SharingError("Share already exists")
            else:
                self._showStatus("Creating collection on server...")
                shareXML.create()
                self._showStatus(" done.\n")

            self._showStatus("Publishing collection to server...")
            shareXML.put()
            self._showStatus(" done.\n")

            self._showStatus("Publishing calendar file to server...")
            shareICal.put()
            self._showStatus(" done.\n")

        except (Sharing.SharingError, zanshin.error.Error), e:

            # Display the error
            # self._clearStatus()
            self._showStatus("\nSharing error:\n%s\n" % e.message)
            logger.exception("Failed to publish collection")
            # self._showStatus("Exception:\n%s" % traceback.format_exc(10))

            # Clean up all share objects we created
            try:
                shareXML.delete(True)
                shareICal.delete(True)
            except:
                pass

            # Re-enable the main panel and switch back to the "Share" button
            self.mainPanel.Enable(True)
            self.buttonPanel.Hide()
            self.mySizer.Detach(self.buttonPanel)
            self.buttonPanel = self.resources.LoadPanel(self,
                                                        "PublishButtonsPanel")
            self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnPublish, id=wx.ID_OK)
            self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
            self._resize()

            return

        self._showStatus("%s\n" % shareXML.getLocation())
        self._showStatus("%s\n" % shareICal.getLocation())

        self.buttonPanel.Hide()
        self.mySizer.Detach(self.buttonPanel)
        self.buttonPanel = self.resources.LoadPanel(self,
                                                    "PublishedButtonsPanel")
        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)

        self.Bind(wx.EVT_BUTTON, self.OnPublishDone, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCopy,
                  id=wx.xrc.XRCID("BUTTON_CLIPBOARD"))
        self._resize()

    def OnCancel(self, evt):
        self.EndModal(False)

    def OnPublishDone(self, evt):
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
        self._clearStatus()
        if self.statusPanel.IsShown():
            self.statusPanel.Hide()
            self.mySizer.Detach(self.statusPanel)
            self._resize()
            wx.Yield()
        pass

    def _resize(self):
        self.mySizer.Layout()
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

    def _getSharingAccounts(self):
        return sorted(
            Sharing.WebDAVAccount.iterItems(self.view),
            key = lambda x: str(x.displayName).lower()
        )

    def _getExistingFiles(self):
        account = self.currentAccount
        host = account.host
        port = account.port
        username = account.username
        password = account.password
        useSSL = account.useSSL
        sharePath = account.path.strip("/")

        handle = WebDAV.ChandlerServerHandle(host, port=port, username=username,
                   password=password, useSSL=useSSL, repositoryView=self.view)

        if len(sharePath) > 0:
            sharePath = "/%s/" % (sharePath)
        else:
            sharePath = "/"
            
        existing = []

        parent = handle.getResource(sharePath)
        skipLen = len(sharePath)
        for resource in zanshin.util.blockUntil(parent.getAllChildren):
            path = resource.path[skipLen:]
            path = path.strip("/")
            if path:
                path = urllib.unquote_plus(path).decode('utf-8')
                existing.append(path)
        
        # @@@ [grant] Localized sort?
        existing.sort()
        return existing

def ShowPublishDialog(parent, view=None, collection=None, filterKindPath=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'parcels', 'osaf', 'framework', 'sharing',
     'PublishCollection_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)
    win = PublishCollectionDialog(parent, "Collection Sharing",
     resources=resources, view=view, collection=collection,
     filterKindPath=filterKindPath)
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()
