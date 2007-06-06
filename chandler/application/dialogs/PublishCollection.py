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


# The collection publishing dialog
# Invoke using the ShowPublishDialog( ) method.

import wx
import logging
import os, sys
from application import schema, Globals
from osaf import sharing
from util import task
from i18n import ChandlerMessageFactory as _
from osaf.pim import Remindable, EventStamp
from TurnOnTimezones import ShowTurnOnTimezonesDialog, PUBLISH
import zanshin
from osaf.activity import *
import SharingDetails
import SubscribeCollection

logger = logging.getLogger(__name__)

MAX_UPDATE_MESSAGE_LENGTH = 55

MSG_ALREADY_EXISTS = _("""Collection already exists on the server.  You may:

- Sync your collection with the one on the server, or...
- Replace the collection on the server with your local copy
""")

class PublishCollectionDialog(wx.Dialog):

    def __init__(self, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
                 resources=None, view=None, collection=None,
                 publishType='collection', modal=True,
                 name=None, account=None):

        wx.Dialog.__init__(self, None, -1, title, pos, size, style)
        self.resources = resources
        self.view = view
        self.collection = collection    # The collection to share
        self.modal = modal
        self.publishType = publishType
        self.name = name
        self.account = account # use this account, overriding the default

        self.mySizer = wx.BoxSizer(wx.VERTICAL)

        # Turn on timezones
        notCancelled = ShowTurnOnTimezonesDialog(view,
                                                 modal=True,
                                                 state=PUBLISH,
                                                 parent=self)
        if notCancelled == False:
            self.OnCancel(None)
            return

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

        self.errorPanel = self.resources.LoadPanel(self, "ErrorPanel")
        self.errorPanel.Hide()
        self.Bind(wx.EVT_BUTTON, self.OnErrorDetails,
                  id=wx.xrc.XRCID("BUTTON_ERROR"))

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

        collName = self.collection.displayName

        # Populate the listbox of sharing accounts
        self.accounts = self._getSharingAccounts()
        self.accountsControl = wx.xrc.XRCCTRL(self, "CHOICE_ACCOUNT")
        self.accountsControl.Clear()

        if self.account:
            self.currentAccount = self.account
        else:
            self.currentAccount = self.accounts[0]

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
            self.CheckboxShareStatus.SetValue(True)
            self.CheckboxShareTriage = wx.xrc.XRCCTRL(self, "CHECKBOX_TRIAGE")
            self.CheckboxShareTriage.SetValue(True)
            self.CheckboxShareReply = wx.xrc.XRCCTRL(self, "CHECKBOX_REPLY")
            self.CheckboxShareReply.SetValue(False)
            self.CheckboxShareBcc = wx.xrc.XRCCTRL(self, "CHECKBOX_BCC")
            self.CheckboxShareBcc.SetValue(False)

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
        self.share = share
        if share.conduit.account:
            name = share.conduit.account.displayName
        else:
            name = u"(via ticket)"
        wx.xrc.XRCCTRL(self, "TEXT_ACCOUNT").SetLabel(name)

        if hasattr(share, 'lastSuccess'):
            lastSync = SharingDetails.formatDateTime(share.lastSuccess)
        else:
            lastSync = _(u"Unknown")
        wx.xrc.XRCCTRL(self, "TEXT_SUCCESS").SetLabel(lastSync)

        self.UnPubSub = wx.xrc.XRCCTRL(self, "BUTTON_UNPUBLISH")

        share = sharing.getShare(self.collection)
        if sharing.isSharedByMe(share):
            self.UnPubSub.SetLabel("Unpublish")
        else:
            self.UnPubSub.SetLabel("Unsubscribe")


        self.CheckboxShareAlarms = wx.xrc.XRCCTRL(self, "CHECKBOX_ALARMS")
        self.CheckboxShareAlarms.Enable(True)
        self.CheckboxShareStatus = wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS")
        self.CheckboxShareStatus.Enable(True)
        self.CheckboxShareTriage = wx.xrc.XRCCTRL(self, "CHECKBOX_TRIAGE")
        self.CheckboxShareTriage.Enable(True)
        self.CheckboxShareReply = wx.xrc.XRCCTRL(self, "CHECKBOX_REPLY")
        self.CheckboxShareReply.Enable(True)
        self.CheckboxShareBcc = wx.xrc.XRCCTRL(self, "CHECKBOX_BCC")
        self.CheckboxShareBcc.Enable(True)

        if isinstance(share.conduit, sharing.RecordSetConduit):
            self.originalFilters = set(share.conduit.filters)

        else:
            self.originalFilterAttributes = list(share.filterAttributes)

        self._loadAttributeFilterState(share)


        if getattr(share, "error", None):
            self._showErrorPanel()


        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

    def OnChangeAccount(self, evt):
        self._hideStatus()

        accountIndex = self.accountsControl.GetSelection()
        account = self.accountsControl.GetClientData(accountIndex)
        self.currentAccount = account


    def OnErrorDetails(self, evt):
        SharingDetails.Show(None, self.share)


    def OnManageDone(self, evt):

        for share in sharing.SharedItem(self.collection).shares:
            self._saveAttributeFilterState(share)

        if self.modal:
            self.EndModal(False)
        self.Destroy()

        share = sharing.getShare(self.collection)
        needsSync = False
        if isinstance(share.conduit, sharing.RecordSetConduit):
            for filter in self.originalFilters:
                if filter not in share.conduit.filters:
                    # A filter has been removed so we need to re-synchronize
                    needsSync = True
                    break
        else:
            if share.filterAttributes != self.originalFilterAttributes:
                needsSync = True

        if needsSync:
            self.view.commit()
            sharing.scheduleNow(self.view, collection=share.contents,
                                forceUpdate=True)


    def _loadAttributeFilterState(self, share):

        if isinstance(share.conduit, sharing.RecordSetConduit):

            self.CheckboxShareAlarms.SetValue('cid:reminders-filter@osaf.us'
                not in share.conduit.filters)
            self.CheckboxShareStatus.SetValue('cid:event-status-filter@osaf.us'
                not in share.conduit.filters)
            self.CheckboxShareTriage.SetValue('cid:triage-filter@osaf.us'
                not in share.conduit.filters)
            self.CheckboxShareReply.SetValue('cid:needs-reply-filter@osaf.us'
                not in share.conduit.filters)
            self.CheckboxShareBcc.SetValue('cid:bcc-filter@osaf.us'
                not in share.conduit.filters)

        else:
            # @@@ Jeffrey: Needs updating for new reminders?
            self.CheckboxShareAlarms.SetValue(Remindable.reminders.name
                not in share.filterAttributes)
            self.CheckboxShareStatus.SetValue(EventStamp.transparency.name
                not in share.filterAttributes)
            self.CheckboxShareTriage.SetValue('_triageStatus'
                not in share.filterAttributes)


    def _getAttributeFilterState(self):
        attrs = []
        if self.publishType == 'collection':

            attrs = set()
            if not self.CheckboxShareAlarms.GetValue():
                attrs.add('cid:reminders-filter@osaf.us')
            if not self.CheckboxShareStatus.GetValue():
                attrs.add('cid:event-status-filter@osaf.us')
            if not self.CheckboxShareTriage.GetValue():
                attrs.add('cid:triage-filter@osaf.us')
            if not self.CheckboxShareReply.GetValue():
                attrs.add('cid:needs-reply-filter@osaf.us')
            if not self.CheckboxShareBcc.GetValue():
                attrs.add('cid:bcc-filter@osaf.us')

        return attrs


    def _saveAttributeFilterState(self, share):

        if not self.CheckboxShareAlarms.GetValue():
            if 'cid:reminders-filter@osaf.us' not in share.conduit.filters:
                share.conduit.filters.add('cid:reminders-filter@osaf.us')
        else:
            if 'cid:reminders-filter@osaf.us' in share.conduit.filters:
                share.conduit.filters.remove('cid:reminders-filter@osaf.us')

        if not self.CheckboxShareStatus.GetValue():
            if 'cid:event-status-filter@osaf.us' not in share.conduit.filters:
                share.conduit.filters.add('cid:event-status-filter@osaf.us')
        else:
            if 'cid:event-status-filter@osaf.us' in share.conduit.filters:
                share.conduit.filters.remove('cid:event-status-filter@osaf.us')

        if not self.CheckboxShareTriage.GetValue():
            if 'cid:triage-filter@osaf.us' not in share.conduit.filters:
                share.conduit.filters.add('cid:triage-filter@osaf.us')
        else:
            if 'cid:triage-filter@osaf.us' in share.conduit.filters:
                share.conduit.filters.remove('cid:triage-filter@osaf.us')

        if not self.CheckboxShareReply.GetValue():
            if 'cid:needs-reply-filter@osaf.us' not in share.conduit.filters:
                share.conduit.filters.add('cid:needs-reply-filter@osaf.us')
        else:
            if 'cid:needs-reply-filter@osaf.us' in share.conduit.filters:
                share.conduit.filters.remove('cid:needs-reply-filter@osaf.us')

        if not self.CheckboxShareBcc.GetValue():
            if 'cid:bcc-filter@osaf.us' not in share.conduit.filters:
                share.conduit.filters.add('cid:bcc-filter@osaf.us')
        else:
            if 'cid:bcc-filter@osaf.us' in share.conduit.filters:
                share.conduit.filters.remove('cid:bcc-filter@osaf.us')



    def _updateCallback(self, activity, *args, **kwds):
        wx.GetApp().PostAsyncEvent(self.updateCallback, activity, *args, **kwds)

    def updateCallback(self, activity, *args, **kwds):

        if 'msg' in kwds:
            msg = kwds['msg'].replace('\n', ' ')
            # @@@MOR: This is unicode unsafe:
            if len(msg) > MAX_UPDATE_MESSAGE_LENGTH:
                msg = "%s..." % msg[:MAX_UPDATE_MESSAGE_LENGTH]
            self._showUpdate(msg)
        if 'percent' in kwds:
            percent = kwds['percent']
            if percent is None:
                self.gauge.Pulse()
            else:
                self.gauge.SetValue(percent)

    def _shutdownInitiated(self):
        if self.modal:
            self.EndModal(False)
        self.Destroy()

    def OnPublish(self, evt):
        self.PublishCollection()

    def PublishCollection(self, overwrite=False):
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

        accountIndex = self.accountsControl.GetSelection()
        account = self.accountsControl.GetClientData(accountIndex)
        self.pubAccount = account

        class ShareTask(task.Task):

            def __init__(task, view, account, collection, activity, overwrite):
                super(ShareTask, task).__init__(view)
                task.accountUUID = account.itsUUID
                task.collectionUUID = collection.itsUUID
                task.activity = activity
                task.overwrite = overwrite

            def error(task, err):
                self._shareError(err)
                self.done = True
                self.success = False

            def success(task, result):
                self._finishedShare(result)
                self.done = True
                self.success = True

            def shutdownInitiated(task, arg):
                self._shutdownInitiated()

            def run(task):

                account = task.view.find(task.accountUUID)
                collection = task.view.find(task.collectionUUID)

                msg = _(u"Publishing collection to server...")
                task.callInMainThread(self._showStatus, msg)

                if self.publishType == 'freebusy':
                    displayName = u"%s FreeBusy" % account.username
                else:
                    displayName = self.collection.displayName

                if self.name:
                    displayName = self.name

                shares = sharing.publish(collection, account,
                                         attrsToExclude=attrsToExclude,
                                         displayName=displayName,
                                         publishType=self.publishType,
                                         activity=task.activity,
                                         overwrite=task.overwrite)

                shareUUIDs = [item.itsUUID for item in shares]
                return shareUUIDs

        # Run this in its own background thread
        self.view.commit()
        self.taskView = sharing.getView(self.view.repository)
        self.activity = Activity("Publish: %s" % self.collection.displayName)
        self.currentTask = ShareTask(self.taskView, account, self.collection,
            self.activity, overwrite)
        self.listener = Listener(activity=self.activity,
            callback=self._updateCallback)
        self.activity.started()
        self.done = False
        self.currentTask.start(inOwnThread=True)

    def _shareError(self, (err, summary, extended)):

        sharing.releaseView(self.taskView)

        if not isinstance(err, ActivityAborted):
            self.activity.failed(exception=err)
        self.listener.unregister()

        # Display the error
        self._hideUpdate()
        logger.error("Failed to publish collection.")
        try:
            if isinstance(err, sharing.OfflineError):
                self._showStatus(_(u"Application is in offline mode"))
            elif isinstance(err, zanshin.error.ConnectionError):
                logger.error("Connection error during publish")

                # Note: do not localize the 'startswith' strings -- these need
                # to match twisted error messages:
                if err.message.startswith("DNS lookup failed"):
                    msg = _(u"Unable to look up server address via DNS")
                elif err.message.startswith("Connection was refused"):
                    msg = _(u"Connection refused by server")
                else:
                    msg = err.message
            elif isinstance(err, sharing.AlreadyExists):
                if hasattr(err, "mine"):
                    # This is a morsecode publish
                    if err.mine:
                        self._clearStatus()
                        self._showStatus(MSG_ALREADY_EXISTS)
                        # Enable the "already exists" panel
                        self.buttonPanel.Hide()
                        self.mySizer.Detach(self.buttonPanel)
                        self.buttonPanel = self.resources.LoadPanel(self,
                            "AlreadyExistsButtonsPanel")
                        self.mySizer.Add(self.buttonPanel, 0, wx.GROW|wx.ALL, 5)
                        self.Bind(wx.EVT_BUTTON, self.OnSync, id=wx.ID_OK)
                        self.Bind(wx.EVT_BUTTON, self.OnReplace,
                                  id=wx.xrc.XRCID("BUTTON_REPLACE"))
                        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
                        self._resize()

                        return False

                    else:
                        # This was one someone else published
                        msg = _(u"Collection was already published from a different account")
                else:
                    msg = _(u"Collection already exists on server")
            else:
                msg = err

                if Globals.options.catch != 'tests':
                    text = "%s\n\n%s" % (summary, extended)
                    SharingDetails.ShowText(None, text,
                        title=_(u"Publish Error"))


            self._showStatus(_(u"\nSharing error:\n%(error)s\n") %
                {'error': msg})

        except Exception, e:
            logger.exception("Error displaying exception")
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

        sharing.releaseView(self.taskView)

        self.activity.completed()
        self.listener.unregister()

        # Pull in the changes from sharing view
        self.view.refresh(lambda code, item, attr, val: val)


        self._showStatus(_(u" Done\n"))
        self._hideUpdate()

        if self.publishType == 'freebusy':
            share = sharing.getFreeBusyShare(self.collection)
        else:
            share = sharing.getShare(self.collection)

        urlString = "\n".join(sharing.getLabeledUrls(share))
        self._showStatus("%s\n" % urlString)

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
        self.activity.abortRequested = True

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

    def OnSync(self, evt):
        if self.modal:
            self.EndModal(False)
        self.Destroy()

        url = "%smc/collection/%s" % (
            self.pubAccount.getLocation(),
            self.collection.itsUUID.str16())
        SubscribeCollection.Show(view=self.view,
            url=url, modal=True, immediate=True,
            mine=True, publisher=True)

    def OnReplace(self, evt):
        self.PublishCollection(overwrite=True)

    def OnCopy(self, evt):
        gotClipboard = wx.TheClipboard.Open()
        if gotClipboard:
            share = sharing.getShare(self.collection)
            urlString = "\n".join(sharing.getLabeledUrls(share))
            wx.TheClipboard.SetData(wx.TextDataObject(unicode(urlString)))
            wx.TheClipboard.Close()

    def _showErrorPanel(self):
        if not self.errorPanel.IsShown():
            self.mySizer.Add(self.errorPanel, 0, wx.GROW, 5)
            self.errorPanel.Show()
        self._resize()

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
            sharing.SharingAccount.iterItems(self.view),
            key = lambda x: x.displayName.lower()
        )

type_to_xrc_map = {'collection' :
                   ('PublishCollection.xrc', _(u"Publish")),
                   'freebusy'   :
                   ('PublishFreeBusy.xrc', _(u"Publish Free/Busy Calendar"))}

def ShowPublishDialog(view=None, collection=None,
                      publishType = 'collection', modal=False, name=None,
                      account=None):
    filename, title = type_to_xrc_map[publishType]

    isShared = sharing.isShared(collection)
    title = _(u"Manage Shared Collection") if isShared else _(u"Publish")

    xrcFile = os.path.join(Globals.chandlerDirectory,
                           'application', 'dialogs', filename)
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = PublishCollectionDialog(title,
                                  resources=resources,
                                  view=view,
                                  collection=collection,
                                  publishType=publishType,
                                  modal=modal,
                                  name=name,
                                  account=account)
    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
        return win
