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


import os, sys
import logging
import wx
from i18n import ChandlerMessageFactory as _
from osaf.framework.twisted import runInUIThread
from osaf import sharing
from util import task
from osaf.activity import *
from application import Globals
import SharingDetails

logger = logging.getLogger(__name__)



restoreDialog = None

def Show():
    d = _Show()
    d.addCallback(lambda dummy: True)

@runInUIThread
def _Show():
    global restoreDialog

    if restoreDialog is None:
        restoreDialog = UnsubscribedCollectionsDialog(wx.GetApp().mainFrame,
            -1, _("Sync Manager"))
        restoreDialog.CenterOnParent()
        restoreDialog.Show()
    else:
        restoreDialog.Raise()


class UnsubscribedCollectionsDialog(wx.Dialog):

    def __init__(self, *args, **kwds):

        super(UnsubscribedCollectionsDialog, self).__init__(*args, **kwds)
        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
            wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.restoring = False

        self.rv = wx.GetApp().UIRepositoryView

        self.checkListBoxes = []
        self.checkBoxes = []
        self.populateLists()

        self.panel = wx.Panel(self, -1)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.messageLabel = wx.StaticText(self.panel, -1,
            _("Accessing server accounts..."))
        self.sizer.Add(self.messageLabel, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.messageLabel2 = wx.StaticText(self.panel, -1,
            _("Please wait..."))
        self.sizer.Add(self.messageLabel2, 0, wx.ALIGN_LEFT|wx.ALL, 5)


        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.sizer)
        self._resize()




    def _resize(self):
        self.panel.Layout()
        self.sizer.Fit(self)



    def populateLists(self):
        self.data = []
        self.listControls = []

        self.accounts = []
        for account in sharing.CosmoAccount.iterAccounts(self.rv):
            if account.isSetUp():
                self.accounts.append(account)

        for account in self.accounts:
            account.getPublishedShares(callback=self.OnRetrieveList,
                blocking=False)


    def OnCompleteLists(self):
        firstAccountName = ""
        for accountUUID, info in self.data:
            if type(info) is Exception:
                # render the error somehow?
                pass
            elif info:
                # info is a list of (uuid, name, tickets) tuples
                account = self.rv.findUUID(accountUUID)
                if account is not None:
                    names = []
                    for uuid, name, tickets in info:
                        names.append(name)

                    cb = wx.CheckBox(self.panel, -1,
                        _(u"&All collections in %(account)s") %
                        { 'account' : account.displayName})
                    self.Bind(wx.EVT_CHECKBOX, self.OnAccountCheck,
                        id=cb.GetId())
                    self.checkBoxes.append(cb)
                    self.sizer.Add(cb, 0, wx.EXPAND|wx.ALL, 5)

                    lb = wx.CheckListBox(self.panel, -1, size=(400,100),
                        choices=names)
                    self.Bind(wx.EVT_CHECKLISTBOX,
                        self.OnCollectionCheck, id=lb.GetId())
                    self.checkListBoxes.append(lb)
                    self.sizer.Add(lb, 1, wx.EXPAND|wx.ALL, 5)

                    if not firstAccountName:
                        firstAccountName = account.displayName



        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        if len(self.checkBoxes) == 0:
            self.messageLabel.SetLabel(_(u"You are already syncing all collections in your accounts"))
            self.messageLabel2.Destroy()
            # Yes, I really do want ID_CANCEL but labeled "OK" (so hitting ESC
            # will work):
            self.DismissButton = wx.Button(self.panel, wx.ID_CANCEL, _(u"OK"))
            self.Bind(wx.EVT_BUTTON, self.OnDismiss, id=wx.ID_CANCEL)
            self.buttonSizer.Add(self.DismissButton, 0, wx.ALIGN_RIGHT|wx.ALL,
                5)

        else:
            self.noteLabel = wx.StaticText(self.panel, -1, _("Note: This list does not include subscriptions."))
            self.sizer.Add(self.noteLabel, 0, wx.ALIGN_LEFT|wx.ALL, 5)

            self.NoButton = wx.Button(self.panel, wx.ID_CANCEL,
                _(u"&Don't Sync"))
            self.LaterButton = wx.Button(self.panel, -1,
                _(u"Sync &Later"))
            self.SyncButton = wx.Button(self.panel, wx.ID_OK,
                _(u"&Sync Now"))

            self.Bind(wx.EVT_BUTTON, self.OnNo, id=wx.ID_CANCEL)
            self.Bind(wx.EVT_BUTTON, self.OnLater, id=self.LaterButton.GetId())
            self.Bind(wx.EVT_BUTTON, self.OnYes, id=wx.ID_OK)

            self.SyncButton.SetDefault()
            self.UpdateSyncButton()

            self.buttonSizer.Add(self.NoButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
            self.buttonSizer.Add(self.LaterButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
            self.buttonSizer.Add(self.SyncButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

            if len(self.checkBoxes) == 1:
                self.messageLabel.SetLabel(_(u"You have collections in a sharing account which aren't being synced."))

            else:
                self.messageLabel.SetLabel(_(u"You have collections in sharing accounts which aren't being synced."))

            self.messageLabel2.SetLabel(
                _(u"Which of them would you like to sync?"))

        self.sizer.Add(self.buttonSizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        for cb in self.checkBoxes:
            # Check account-wide checkbox by default
            cb.SetValue(True)
            self.OnAccountCheck(None, control=cb)

        self._resize()
        self.CenterOnParent()



    def OnCollectionCheck(self, evt):
        self.UpdateSyncButton()


    def OnAccountCheck(self, evt, control=None):
        if control is None:
            checkbox = evt.GetEventObject()
        else:
            checkbox = control
        index = self.checkBoxes.index(checkbox)
        if checkbox.GetValue():
            for i in range(len(self.checkListBoxes[index].GetItems())):
                self.checkListBoxes[index].Check(i, False)
            for i in range(len(self.checkListBoxes[index].GetItems())):
                self.checkListBoxes[index].Check(i, True)
            self.checkListBoxes[index].Enable(False)
        else:
            self.checkListBoxes[index].Enable(True)
            for i in range(len(self.checkListBoxes[index].GetItems())):
                self.checkListBoxes[index].Check(i, False)

        self.UpdateSyncButton()



    def OnRetrieveList(self, results):
        if not restoreDialog:
            # we're closed already
            return

        exc, accountUUID, items = results
        if exc is None:
            account = self.rv.findUUID(accountUUID)

            unsubscribedCollections = list()
            for name, uuid, href, tickets, subscribed in items:
                if not subscribed:
                    unsubscribedCollections.append( (uuid, name, tickets) )
            self.data.append( (accountUUID, unsubscribedCollections) )

        else:
            # error
            logger.error("Got an error trying to get list of unsubscribed: %s",
                exc)
            self.data.append( (accountUUID, exc) )

        if len(self.data) == len(self.accounts):
            self.OnCompleteLists()


    def UpdateSyncButton(self):
        for clb in self.checkListBoxes:
            for i in range(len(clb.GetItems())):
                if clb.IsChecked(i):
                    self.SyncButton.Enable(True)
                    return

        self.SyncButton.Enable(False)


    def OnYes(self, evt):
        global restoreDialog

        index = 0
        totalWork = 0
        for accountUUID, info in self.data:
            if not type(info) is Exception and info:
                # info is a list of (uuid, name, tickets) tuples
                account = self.rv.findUUID(accountUUID)
                if account is not None:
                    account.requested = set()
                    if self.checkBoxes[index].GetValue(): # restore all
                        for uuid, name, tickets in info:
                            account.requested.add(uuid)
                            totalWork += 1
                    else:
                        clb = self.checkListBoxes[index]
                        for i in range(len(clb.GetItems())):
                            uuid = info[i][0]
                            if clb.IsChecked(i):
                                account.requested.add(uuid)
                                totalWork += 1
                            else:
                                account.ignored.add(uuid)


                index += 1

        for cb in self.checkBoxes:
            cb.Enable(False)
        for cbl in self.checkListBoxes:
            cbl.Enable(False)

        self.SyncButton.Destroy()
        self.LaterButton.Destroy()
        self.NoButton.Destroy()

        self.CancelButton = wx.Button(self.panel, wx.ID_CANCEL)
        self.CancelButton.SetDefault()
        self.buttonSizer.Add(self.CancelButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)


        self.gaugeCtrl = wx.Gauge(self.panel, -1, size=(300,10))
        self.sizer.Add(self.gaugeCtrl, 0,
            wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self.gaugeCtrl.Pulse()

        self.statusCtrl = wx.StaticText(self.panel, -1, "")
        self.sizer.Add(self.statusCtrl, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self._resize()


        class RestoreTask(task.Task):

            def __init__(task, view, activity):
                super(RestoreTask, task).__init__(view)
                task.activity = activity

            def error(task, err):
                if restoreDialog:
                    sharing.releaseView(self.taskView)
                    self.restoring = False
                    self._restoreError(err)

            def success(task, result):
                if restoreDialog:
                    sharing.releaseView(self.taskView)
                    self.restoring = False
                    self._restoreSuccess(result)

            def shutdownInitiated(task):
                if restoreDialog:
                    self.restoring = False
                    self._shutdownInitiated()

            def run(task):
                for account in sharing.CosmoAccount.iterAccounts(task.view):
                    if account.isSetUp():
                        account.restoreCollections(activity=task.activity)

        self.rv.commit(sharing.mergeFunction)
        self.taskView = sharing.getView(self.rv.repository)
        self.activity = Activity(_(u"Restoring collections"))
        self.currentTask = RestoreTask(self.taskView, self.activity)
        self.listener = Listener(activity=self.activity,
            callback=self._updateCallback)
        self.activity.started()
        self.activity.update(totalWork=totalWork+1)
        self.restoring = True
        self.currentTask.start(inOwnThread=True)


    def OnDismiss(self, evt):
        global restoreDialog
        restoreDialog = None
        self.Destroy()


    def OnLater(self, evt):
        global restoreDialog
        restoreDialog = None
        self.Destroy()


    def OnNo(self, evt):
        global restoreDialog

        if self.restoring:
            self.activity.requestAbort()
            restoreDialog = None
            self.Destroy()

        else:

            # Ignore all unsubscribed collections

            for accountUUID, info in self.data:
                if not type(info) is Exception and info:
                    # info is a list of (uuid, name, tickets) tuples
                    account = self.rv.findUUID(accountUUID)
                    if account is not None:
                        account.requested = set()
                        for uuid, name, tickets in info:
                            account.ignored.add(uuid)

            self.rv.commit(sharing.mergeFunction)
            restoreDialog = None
            self.Destroy()

    def _updateCallback(self, activity, *args, **kwds):
        if restoreDialog:
            wx.GetApp().PostAsyncEvent(self.updateCallback, activity,
                *args, **kwds)

    def updateCallback(self, activity, *args, **kwds):

        if 'msg' in kwds:
            msg = kwds['msg'].replace('\n', ' ')
            self.statusCtrl.SetLabel(msg)

        if 'percent' in kwds:
            percent = kwds['percent']
            if percent is None:
                self.gaugeCtrl.Pulse()
            else:
                self.gaugeCtrl.SetValue(percent)


    def _restoreError(self, (err, summary, extended)):
        self.activity.failed(err)
        global restoreDialog
        restoreDialog = None
        self.Destroy()

        if Globals.options.catch != 'tests':
            text = "%s\n\n%s" % (summary, extended)
            SharingDetails.ShowText(wx.GetApp().mainFrame, text,
                title=_(u"Collection Restore Error"))

    def _restoreSuccess(self, result):
        self.activity.completed()
        global restoreDialog
        restoreDialog = None
        self.Destroy()

    def _shutdownInitiated(self):
        self.activity.requestAbort()
