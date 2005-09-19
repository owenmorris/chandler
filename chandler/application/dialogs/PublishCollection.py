# The collection publishing dialog
# Invoke using the ShowPublishDialog( ) method.

import wx
import M2Crypto
import traceback, logging
import os, urlparse, urllib
import application.Globals as Globals
import application.Utility as Utility
from osaf import sharing
import zanshin.webdav
import zanshin.util
from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)

class PublishCollectionDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
                 resources=None, view=None, collection=None,
                 filterClassName=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)
        self.resources = resources
        self.view = view
        self.parent = parent
        self.collection = collection    # The collection to share

        # List of classes to share
        if filterClassName is None:
            self.filterClasses = []
        else:
            self.filterClasses = [filterClassName]

        self.mySizer = wx.BoxSizer(wx.VERTICAL)

        # Is this collection already shared?

        isShared = sharing.isShared(collection)

        if not isShared:       # Not yet shared, show "Publish"
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

        if not isShared:       # Not yet shared, show "Publish"
            self.ShowPublishPanel()
        else:                           # Already shared, show "Manage"
            self.ShowManagePanel()


    def ShowPublishPanel(self):
        # "Publish" mode -- i.e., the collection has not yet been shared

        self.Bind(wx.EVT_BUTTON, self.OnPublish, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        collName = sharing.getFilteredCollectionDisplayName(self.collection,
                                                            self.filterClasses)
        wx.xrc.XRCCTRL(self,
                       "TEXT_COLLNAME").SetLabel(collName)

        self.currentAccount = sharing.getWebDAVAccount(self.view)

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
        self.CheckboxShareAlarms.SetValue(False)
        self.CheckboxShareStatus = wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS")
        self.CheckboxShareStatus.SetValue(False)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))


    def ShowManagePanel(self):
        # "Manage" mode -- i.e., the collection has already been shared

        self.Bind(wx.EVT_BUTTON, self.OnManageDone, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnCopy,
                  id=wx.xrc.XRCID("BUTTON_CLIPBOARD"))
        self.Bind(wx.EVT_BUTTON, self.OnUnPubSub,
                  id=wx.xrc.XRCID("BUTTON_UNPUBLISH"))

        name = self.collection.displayName
        wx.xrc.XRCCTRL(self, "TEXT_MANAGE_COLLNAME").SetLabel(name)

        share = sharing.getShare(self.collection)
        if share.conduit.account:
            name = share.conduit.account.displayName
        else:
            name = u"(via ticket)"
        wx.xrc.XRCCTRL(self, "TEXT_ACCOUNT").SetLabel(name)

        self.UnPubSub = wx.xrc.XRCCTRL(self, "BUTTON_UNPUBLISH")

        share = sharing.getShare(self.collection)
        if sharing.isSharedByMe(share):
            self.UnPubSub.SetLabel("Unpublish")
        else:
            self.UnPubSub.SetLabel("Unsubscribe")

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
        self.CheckboxShareAlarms.Enable(False)
        self.CheckboxShareStatus = wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS")
        self.CheckboxShareStatus.Enable(False)

        self.filterClasses = share.filterClasses

        self._loadClassFilterState()
        self._loadAttributeFilterState(share)

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
        self._saveClassFilterState()
        for share in self.collection.shares:
            self._saveAttributeFilterState(share)
        self.EndModal(False)

    def _loadAttributeFilterState(self, share):
        self.CheckboxShareAlarms.SetValue("reminderTime" not in \
                                          share.filterAttributes)
        self.CheckboxShareStatus.SetValue("transparency" not in \
                                          share.filterAttributes)


    def _getAttributeFilterState(self):
        attrs = []
        if not self.CheckboxShareAlarms.GetValue():
            attrs.append('reminderTime')
        if not self.CheckboxShareStatus.GetValue():
            attrs.append('transparency')
        return attrs


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


    def _loadClassFilterState(self):
        # Based on which classes are listed in filterClasses, update the UI

        if len(self.filterClasses) == 0:      # No filtering

            self.RadioItems.SetValue(True)
            self.CheckboxMail.SetValue(False)
            self.CheckboxTasks.SetValue(False)
            self.CheckboxEvents.SetValue(False)

        else:                               # Filtering

            # Unset the "My items" radio button
            self.RadioItemsHidden.SetValue(True)

            # Conditionally set the individual class checkboxes:

            if 'osaf.pim.mail.MailMessageMixin' in self.filterClasses:
                self.CheckboxMail.SetValue(True)
            else:
                self.CheckboxMail.SetValue(False)

            if 'osaf.pim.TaskMixin' in self.filterClasses:
                self.CheckboxTasks.SetValue(True)
            else:
                self.CheckboxTasks.SetValue(False)

            if 'osaf.pim.CalendarEventMixin' in self.filterClasses:
                self.CheckboxEvents.SetValue(True)
            else:
                self.CheckboxEvents.SetValue(False)


    def _saveClassFilterState(self):
        # Examine the values in the UI and make the appropriate changes to the
        # Share's filter

        self.filterClasses = []

        if not self.RadioItems.GetValue():  # Filtering

            if self.CheckboxMail.GetValue():
                self.filterClasses.append('osaf.pim.mail.MailMessageMixin')

            if self.CheckboxTasks.GetValue():
                self.filterClasses.append('osaf.pim.TaskMixin')

            if self.CheckboxEvents.GetValue():
                self.filterClasses.append('osaf.pim.CalendarEventMixin')

        for share in self.collection.shares:
            share.filterClasses = self.filterClasses




    def OnAllItemsClicked(self, evt):
        # Clear the filter classes list

        self.filterClasses = []
        self._loadClassFilterState()


    def OnFilterClicked(self, evt):
        # If any individual class checkbox is clicked, unset "My items"

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


            attrs_to_exclude = self._getAttributeFilterState()
            classes_to_include = self.filterClasses
            accountIndex = self.accountsControl.GetSelection()
            account = self.accountsControl.GetClientData(accountIndex)

            self._showStatus(_(u"Wait for Sharing URLs...\n"))
            self._showStatus(_(u"Publishing collection to server..."))
            shares = sharing.publish(self.collection, account,
                                     classes_to_include, attrs_to_exclude)
            self._showStatus(_(u" done.\n"))

        except (sharing.SharingError, zanshin.error.Error,
                M2Crypto.SSL.Checker.WrongHost,
                Utility.CertificateVerificationError), e:

            # Display the error
            # self._clearStatus()
            try:
                #XXX: [i18n] Will need to capture and translate m2crypto and zanshin errors
                self._showStatus(_(u"\nSharing error:\n%(error)s\n") % {'error': e})
            except AttributeError:
                pass
            logger.exception("Failed to publish collection")
            # self._showStatus("Exception:\n%s" % traceback.format_exc(10))

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

        share = sharing.getShare(self.collection)
        urls = sharing.getUrls(share)
        if len(urls) == 1:
            self._showStatus(u"%s\n" % urls[0])
        else:
            self._showStatus(u"Read-write: %s\n" % urls[0])
            self._showStatus(u"Read-only: %s\n" % urls[1])

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

    def OnUnPubSub(self, evt):
        share = sharing.getShare(self.collection)
        if sharing.isSharedByMe(share):
            sharing.unpublish(self.collection)
        else:
            sharing.unsubscribe(self.collection)
        self.EndModal(True)


    def OnCopy(self, evt):
        gotClipboard = wx.TheClipboard.Open()
        if gotClipboard:
            share = sharing.getShare(self.collection)
            urls = sharing.getUrls(share)
            if len(urls) == 1:
                urlString = urls[0]
            else:
                urlString = "Read-write: %s\nRead-only: %s\n" % (urls[0],
                                                                 urls[1])
            wx.TheClipboard.SetData(wx.TextDataObject(unicode(urlString)))
            wx.TheClipboard.Close()

    def _clearStatus(self):
            self.textStatus.SetLabel(u"")

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
        #XXX [i18n] Should this be a localized PyICU sort?
        return sorted(
            sharing.WebDAVAccount.iterItems(self.view),
            key = lambda x: x.displayName.lower()
        )

def ShowPublishDialog(parent, view=None, collection=None, filterClassName=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'PublishCollection_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)
    win = PublishCollectionDialog(parent, _(u"Collection Sharing"),
     resources=resources, view=view, collection=collection,
     filterClassName=filterClassName)
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()
