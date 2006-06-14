# The collection publishing dialog
# Invoke using the ShowPublishDialog( ) method.

import wx
import logging
import os, sys
from application import schema, Globals
from osaf import sharing
from util import task, viewpool
from i18n import OSAFMessageFactory as _
import SyncProgress

logger = logging.getLogger(__name__)

MAX_UPDATE_MESSAGE_LENGTH = 50

class PublishCollectionDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
                 resources=None, view=None, collection=None,
                 filterClassName=None, publishType='collection', modal=True):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)
        self.resources = resources
        self.view = view
        self.parent = parent
        self.collection = collection    # The collection to share
        self.modal = modal
        self.publishType = publishType

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

        self.updatePanel = self.resources.LoadPanel(self, "UpdatePanel")
        self.updatePanel.Hide()
        self.textUpdate = wx.xrc.XRCCTRL(self, "TEXT_UPDATE")
        self.gauge = wx.xrc.XRCCTRL(self, "GAUGE")
        self.gauge.SetRange(100)

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

        self.currentAccount = schema.ns('osaf.sharing',
            self.view).currentWebDAVAccount.item

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

        if self.publishType == 'collection': #freebusy doesn't need these
            wx.xrc.XRCCTRL(self, "TEXT_COLLNAME").SetLabel(collName)
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

        self.originalFilterClasses = self.filterClasses = share.filterClasses

        self._loadClassFilterState()
        self._loadAttributeFilterState(share)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

    def OnChangeAccount(self, evt):
        self._hideStatus()

        accountIndex = self.accountsControl.GetSelection()
        account = self.accountsControl.GetClientData(accountIndex)
        self.currentAccount = account



    def OnManageDone(self, evt):
        self._saveClassFilterState()

        # Commenting this out for now since they can't be changed in the
        # manage dialog anyway (the checkboxes are disabled), and it causes
        # CalDAV CloudXML shares to lose attribute filters that they need to
        # keep:
        # for share in self.collection.shares:
        #     self._saveAttributeFilterState(share)

        if self.modal:
            self.EndModal(False)
        self.Destroy()

        share = iter(self.collection.shares).next()
        if share.filterClasses != self.originalFilterClasses:
            SyncProgress.Show(wx.GetApp().mainFrame, rv=self.view,
                collection=share.contents)


    def _loadAttributeFilterState(self, share):
        # @@@ Jeffrey: Needs updating for new reminders?
        self.CheckboxShareAlarms.SetValue("reminders" not in \
                                          share.filterAttributes)
        self.CheckboxShareStatus.SetValue("transparency" not in \
                                          share.filterAttributes)


    def _getAttributeFilterState(self):
        attrs = []
        if self.publishType == 'collection':
            # @@@ Jeffrey: Needs updating for new reminders?
            if not self.CheckboxShareAlarms.GetValue():
                attrs.append('reminders')
                attrs.append('expiredReminders')
            if not self.CheckboxShareStatus.GetValue():
                attrs.append('transparency')
        return attrs


    def _saveAttributeFilterState(self, share):
        # @@@ Jeffrey: Needs updating for new reminders?
        if not self.CheckboxShareAlarms.GetValue():
            if "reminders" not in share.filterAttributes:
                share.filterAttributes.append("reminders")
                share.filterAttributes.append("expiredReminders")
        else:
            if "reminders" in share.filterAttributes:
                share.filterAttributes.remove("reminders")
                share.filterAttributes.remove("expiredReminders")

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

            if 'osaf.pim.tasks.TaskMixin' in self.filterClasses:
                self.CheckboxTasks.SetValue(True)
            else:
                self.CheckboxTasks.SetValue(False)

            if 'osaf.pim.calendar.Calendar.CalendarEventMixin' in self.filterClasses:
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
                self.filterClasses.append('osaf.pim.tasks.TaskMixin')

            if self.CheckboxEvents.GetValue():
                self.filterClasses.append('osaf.pim.calendar.Calendar.CalendarEventMixin')

        for share in self.collection.shares:
            share.filterClasses = self.filterClasses




    def OnAllItemsClicked(self, evt):
        # Clear the filter classes list

        self.filterClasses = []
        self._loadClassFilterState()


    def OnFilterClicked(self, evt):
        # If any individual class checkbox is clicked, unset "My items"

        self.RadioItems.SetValue(False)

    def updateCallback(self, msg=None, percent=None):
        if msg is not None:
            msg = msg.replace('\n', ' ')
            # @@@MOR: This is unicode unsafe:
            if len(msg) > MAX_UPDATE_MESSAGE_LENGTH:
                msg = "%s..." % msg[:MAX_UPDATE_MESSAGE_LENGTH]
            self._showUpdate(msg)
        if percent is not None:
            self.gauge.SetValue(percent)

    def OnPublish(self, evt):
        self.PublishCollection(blocking=False)

    def PublishCollection(self):
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
        self.Bind(wx.EVT_BUTTON, self.OnStopPublish, id=wx.ID_CANCEL)

        self._clearStatus()
        self._resize()
        wx.Yield()

        attrsToExclude = self._getAttributeFilterState()
        classesToInclude = self.filterClasses
        accountIndex = self.accountsControl.GetSelection()
        account = self.accountsControl.GetClientData(accountIndex)

        class ShareTask(task.Task):

            def __init__(task, view, account, collection):
                super(ShareTask, task).__init__(view)
                task.accountUUID = account.itsUUID
                task.collectionUUID = collection.itsUUID

            def error(task, err):
                self._shareError(err)
                self.done = True
                self.success = False

            def success(task, result):
                self._finishedShare(result)
                self.done = True
                self.success = True

            def _updateCallback(task, **kwds):
                cancel = task.cancelRequested
                task.callInMainThread(lambda _:self.updateCallback(**_), kwds)
                return cancel

            def run(task):
                task.cancelRequested = False

                account = task.view.find(task.accountUUID)
                collection = task.view.find(task.collectionUUID)

                msg = _(u"Publishing collection to server...")
                task.callInMainThread(self._showStatus, msg)

                if self.publishType == 'freebusy':
                    displayName = u"%s FreeBusy" % account.username
                elif self.collection is schema.ns('osaf.pim',
                    self.view).allCollection:

                    ext = _(u'items')
                    if classesToInclude:
                        classString = classesToInclude[0]
                        if classString == "osaf.pim.tasks.TaskMixin":
                            ext = _(u'tasks')
                        elif classString == "osaf.pim.mail.MailMessageMixin":
                            ext = _(u'mail')
                        elif classString == \
                            "osaf.pim.calendar.Calendar.CalendarEventMixin":
                            ext = _(u'calendar')

                    args = { 'username' : account.username, 'ext' : ext }

                    displayName = u"%(username)s's %(ext)s" % args
                else:
                    displayName = self.collection.displayName

                shares = sharing.publish(collection, account,
                                         classesToInclude=classesToInclude,
                                         attrsToExclude=attrsToExclude,
                                         displayName=displayName,
                                         publishType=self.publishType,
                                         updateCallback=task._updateCallback)

                shareUUIDs = [item.itsUUID for item in shares]
                return shareUUIDs

        # Run this in its own background thread
        self.view.commit()
        self.taskView = viewpool.getView(self.view.repository)
        self.currentTask = ShareTask(self.taskView, account, self.collection)
        self.done = False
        self.currentTask.start(inOwnThread=True)

    def _shareError(self, e):

        viewpool.releaseView(self.taskView)

        # Display the error
        self._hideUpdate()
        logger.exception("Failed to publish collection")
        try:
            #XXX: [i18n] Will need to capture and translate m2crypto and zanshin errors
            self._showStatus(_(u"\nSharing error:\n%(error)s\n") % {'error': e})
        except:
            self._showStatus(_(u"\nSharing error:\n(Can't display error message;\nSee chandler.log for more details)\n"))
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

        return False

    def _finishedShare(self, shareUUIDs):

        viewpool.releaseView(self.taskView)

        # Pull in the changes from sharing view
        self.view.refresh(lambda code, item, attr, val: val)

        self._showStatus(_(u" done.\n"))
        self._hideUpdate()

        if self.publishType == 'freebusy':
            share = sharing.getFreeBusyShare(self.collection)
        else:
            share = sharing.getShare(self.collection)

        urls = sharing.getUrls(share)
        if len(urls) == 1:
            self._showStatus(u"%s\n" % urls[0])
        else:
            if self.publishType != 'freebusy':
                self._showStatus(u"Read-write: %s\n" % urls[0])
            self._showStatus(u"Read-only: %s\n" % urls[1])

        self.buttonPanel.Hide()
        self.mySizer.Detach(self.buttonPanel)
        self.buttonPanel = self.resources.LoadPanel(self,
                                                    "PublishedButtonsPanel")
        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)

        self.Bind(wx.EVT_CLOSE,  self.OnPublishDone)
        self.Bind(wx.EVT_BUTTON, self.OnPublishDone, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCopy,
                  id=wx.xrc.XRCID("BUTTON_CLIPBOARD"))
        self._resize()

        return True

    def OnStopPublish(self, evt):
        self.currentTask.cancelRequested = True

    def OnCancel(self, evt):
        if self.modal:
            self.EndModal(False)
        self.Destroy()

    def OnPublishDone(self, evt):
        if self.modal:
            self.EndModal(False)
        self.Destroy()

    def OnUnPubSub(self, evt):
        share = sharing.getShare(self.collection)
        if sharing.isSharedByMe(share):
            sharing.unpublish(self.collection)
        else:
            sharing.unsubscribe(self.collection)
        if self.modal:
            self.EndModal(False)
        self.Destroy()

    def OnCopy(self, evt):
        gotClipboard = wx.TheClipboard.Open()
        if gotClipboard:
            if self.publishType == 'freebusy':
                share = sharing.getFreeBusyShare(self.collection)
            else:
                share = sharing.getShare(self.collection)
            urls = sharing.getUrls(share)
            if len(urls) == 1:
                urlString = urls[0]
            elif self.publishType == 'freebusy':
                urlString = urls[1]
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
        # @@@MOR wx.Yield()

    def _hideStatus(self):
        self._clearStatus()
        if self.statusPanel.IsShown():
            self.statusPanel.Hide()
            self.mySizer.Detach(self.statusPanel)
            self._resize()
            wx.Yield()
        pass

    def _showUpdate(self, text):
        if not self.updatePanel.IsShown():
            self.mySizer.Add(self.updatePanel, 0, wx.GROW, 5)
            self.updatePanel.Show()

        self.textUpdate.SetLabel(text)
        self._resize()

    def _hideUpdate(self):
        if self.updatePanel.IsShown():
            self.updatePanel.Hide()
            self.mySizer.Detach(self.updatePanel)
            self._resize()

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

type_to_xrc_map = {'collection' :
                   ('PublishCollection_wdr.xrc', _(u"Collection Sharing")),
                   'freebusy'   :
                   ('PublishFreeBusy.xrc', _(u"Publish Free/Busy Information"))}

def ShowPublishDialog(parent, view=None, collection=None, filterClassName=None,
                      publishType = 'collection', modal=False):
    filename, title = type_to_xrc_map[publishType]
    xrcFile = os.path.join(Globals.chandlerDirectory,
                           'application', 'dialogs', filename)
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = PublishCollectionDialog(parent, title, resources=resources, view=view,
                                  collection=collection,
                                  publishType=publishType,
                                  filterClassName=filterClassName, modal=modal)
    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
        return win
