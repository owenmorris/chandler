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
from osaf import sharing, usercollections
from util import task, viewpool
from application import schema, Globals
from i18n import ChandlerMessageFactory as _
import zanshin
from osaf.activity import *

logger = logging.getLogger(__name__)

MAX_UPDATE_MESSAGE_LENGTH = 55

class SubscribeDialog(wx.Dialog):

    def __init__(self, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None, url=None, name=None, modal=True,
         immediate=False, mine=None, publisher=None, color=None):

        # for bug #8387
        if "wxGTK" in wx.PlatformInfo:
            style |= wx.RESIZE_BORDER
            
        wx.Dialog.__init__(self, None, -1, title, pos, size, style)

        self.view = view
        self.resources = resources
        self.modal = modal
        self.name = name
        self.mine = mine
        self.publisher = publisher
        self.color = color

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "Subscribe")
        self.mySizer.Add(self.toolPanel, 0, wx.GROW|wx.ALL, 5)

        self.statusPanel = self.resources.LoadPanel(self, "StatusPanel")
        self.mySizer.Add(self.statusPanel, 0, wx.GROW, 5)
        self.statusPanel.Hide()
        self.accountPanel = self.resources.LoadPanel(self, "UsernamePasswordPanel")
        self.mySizer.Add(self.accountPanel, 0, wx.GROW, 5)
        self.accountPanel.Hide()

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.textUrl = wx.xrc.XRCCTRL(self, "TEXT_URL")
        if url is not None:
            self.textUrl.SetValue(url)
        else:
            account = sharing.schema.ns('osaf.sharing',
                self.view).currentSharingAccount.item
            if account:
                url = account.getLocation()
                self.textUrl.SetValue(url)

        self.Bind(wx.EVT_TEXT, self.OnTyping, self.textUrl)

        self.textStatus = wx.xrc.XRCCTRL(self, "TEXT_STATUS")
        self.gauge = wx.xrc.XRCCTRL(self, "GAUGE")
        self.gauge.SetRange(100)
        self.textUsername = wx.xrc.XRCCTRL(self, "TEXT_USERNAME")
        self.textPassword = wx.xrc.XRCCTRL(self, "TEXT_PASSWORD")
        self.checkboxKeepOut = wx.xrc.XRCCTRL(self, "CHECKBOX_KEEPOUT")
        if self.mine:
            self.checkboxKeepOut.SetValue(False)
        self.checkboxShareAlarms = wx.xrc.XRCCTRL(self, "CHECKBOX_ALARMS")
        self.checkboxShareStatus = wx.xrc.XRCCTRL(self, "CHECKBOX_STATUS")
        self.checkboxShareTriage = wx.xrc.XRCCTRL(self, "CHECKBOX_TRIAGE")
        self.checkboxShareReply = wx.xrc.XRCCTRL(self, "CHECKBOX_REPLY")
        self.checkboxShareBcc = wx.xrc.XRCCTRL(self, "CHECKBOX_BCC")

        self.subscribeButton = wx.xrc.XRCCTRL(self, "wxID_OK")

        self.Bind(wx.EVT_BUTTON, self.OnSubscribe, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

        self.textUrl.SetFocus()
        self.textUrl.SetSelection(-1, -1)

        self.subscribing = False

        if immediate:
            self.OnSubscribe(None)


    def getFilters(self):

        filters = set()

        if not self.checkboxShareAlarms.GetValue():
            filters.add('cid:reminders-filter@osaf.us')
        if not self.checkboxShareStatus.GetValue():
            filters.add('cid:event-status-filter@osaf.us')
        if not self.checkboxShareTriage.GetValue():
            filters.add('cid:triage-filter@osaf.us')
        if not self.checkboxShareReply.GetValue():
            filters.add('cid:needs-reply-filter@osaf.us')
        if not self.checkboxShareBcc.GetValue():
            filters.add('cid:bcc-filter@osaf.us')

        if filters:
            return filters
        else:
            return None


    def _updateCallback(self, activity, *args, **kwds):
        wx.GetApp().PostAsyncEvent(self.updateCallback, activity, *args, **kwds)

    def updateCallback(self, activity, *args, **kwds):

        if 'msg' in kwds:
            msg = kwds['msg'].replace('\n', ' ')
            # @@@MOR: This is unicode unsafe:
            if len(msg) > MAX_UPDATE_MESSAGE_LENGTH:
                msg = "%s..." % msg[:MAX_UPDATE_MESSAGE_LENGTH]
            self._showStatus(msg)
        if 'percent' in kwds:
            percent = kwds['percent']
            if percent is None:
                self.gauge.Pulse()
            else:
                self.gauge.SetValue(percent)



    def _finishedShare(self, uuid):

        viewpool.releaseView(self.taskView)

        # Pull in the changes from sharing view
        self.view.refresh(lambda code, item, attr, val: val)

        collection = self.view[uuid]

        if self.name:
            collection.displayName = self.name

        if self.publisher:
            me = schema.ns("osaf.pim", self.view).currentContact.item
            for share in sharing.SharedItem(collection).shares:
                share.sharer = me

        # Put this collection into "My items" if not checked:
        if not self.checkboxKeepOut.GetValue() or self.mine:
            logger.info(_(u'Moving collection into My Items'))
            schema.ns('osaf.pim', self.view).mine.addSource(collection)

        schema.ns("osaf.app", self.view).sidebarCollection.add(collection)

        if self.color:
            usercollections.UserCollection(collection).color = self.color

        # Commit now to prevent being in the state where the collection
        # has been subscribed to, but we don't remember adding it to the
        # sidebar.
        self.activity.update(msg="Saving...", totalWork=None)
        self.view.commit()
        self.activity.completed()
        self.listener.unregister()

        if self.modal:
            self.EndModal(True)
        self.Destroy()
        
        self.subscribing = False

    def _shareError(self, err):

        viewpool.releaseView(self.taskView)

        if not isinstance(err, ActivityAborted):
            self.activity.failed(exception=err)
        self.listener.unregister()

        self.subscribeButton.Enable(True)
        self.gauge.SetValue(0)

        if isinstance(err, sharing.NotAllowed):
            self._showAccountInfo()
        elif isinstance(err, sharing.NotFound):
            self._showStatus(_(u"Collection was not found"))
        elif isinstance(err, sharing.AlreadySubscribed):
            self._showStatus(_(u"You are already subscribed to this collection"))
        elif isinstance(err, sharing.OfflineError):
            self._showStatus(_(u"Application is in offline mode"))
        elif isinstance(err, zanshin.error.ConnectionError):
            logger.error("Connection error during subscribe")

            # Note: do not localize the 'startswith' strings -- these need to
            # match twisted error messages:
            if err.message.startswith("DNS lookup failed"):
                msg = _(u"Unable to look up server address via DNS")
            elif err.message.startswith("Connection was refused by other side"):
                msg = _(u"Connection refused by server")
            else:
                msg = err.message

            self._showStatus(_(u"Sharing Error:\n%(error)s") % {'error': msg})

        else:
            logger.error("Error during subscribe")
            self._showStatus(_(u"Sharing Error:\n%(error)s") % {'error': err})

        self.subscribing = False
        self._resize()

    def _shutdownInitiated(self):
        if self.modal:
            self.EndModal(False)
        self.Destroy()

    def OnSubscribe(self, evt):

        view = self.view
        url = self.textUrl.GetValue()
        url = url.strip()

        if " " in url:
            self._showStatus(_(u"Spaces are not allowed in URLs"))
            return

        # if url.startswith('webcal:'):
        #     url = 'http:' + url[7:]

        if self.accountPanel.IsShown():
            username = self.textUsername.GetValue()
            password = self.textPassword.GetValue()
        else:
            username = None
            password = None

        self.subscribeButton.Enable(False)
        self.gauge.SetValue(0)
        self.subscribing = True
        self._showStatus(_(u"In progress..."))
        wx.Yield()


        class ShareTask(task.Task):

            def __init__(task, view, url, username, password, activity,
                filters):
                super(ShareTask, task).__init__(view)
                task.url = url
                task.username = username
                task.password = password
                task.activity = activity
                task.filters = filters

            def error(task, err):
                self._shareError(err)

            def success(task, result):
                self._finishedShare(result)

            def shutdownInitiated(task, arg):
                self._shutdownInitiated()

            def run(task):
                collection = sharing.subscribe(task.view, task.url,
                    username=task.username, password=task.password,
                    activity=task.activity, filters=task.filters)

                return collection.itsUUID

        self.view.commit()
        self.taskView = viewpool.getView(self.view.repository)
        self.activity = Activity("Subscribe: %s" % url)
        self.currentTask = ShareTask(self.taskView, url, username, password,
                                     self.activity,
                                     self.getFilters())
        self.listener = Listener(activity=self.activity,
            callback=self._updateCallback)
        self.activity.started()
        self.currentTask.start(inOwnThread=True)



    def OnTyping(self, evt):
        self._hideStatus()
        self._hideAccountInfo()

    def _showAccountInfo(self):
        self._hideStatus()

        if not self.accountPanel.IsShown():
            self.accountPanel.Show()
            self.textUsername.SetFocus()

        self._resize()

    def _hideAccountInfo(self):

        if self.accountPanel.IsShown():
            self.accountPanel.Hide()
            self._resize()

    def _showStatus(self, text):
        self._hideAccountInfo()

        if not self.statusPanel.IsShown():
            self.statusPanel.Show()
            self._resize()

        self.textStatus.SetLabel(text)

    def _hideStatus(self):
        if self.statusPanel.IsShown():
            self.statusPanel.Hide()
            self._resize()

    def _resize(self):
        self.mySizer.Layout()
        self.mySizer.Fit(self)


    def OnCancel(self, evt):
        if self.subscribing:
            self.activity.abortRequested = True
        else:
            if self.modal:
                self.EndModal(False)
            self.Destroy()

def Show(view=None, url=None, name=None, modal=False, immediate=False,
         mine=None, publisher=None, color=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'SubscribeCollection.xrc')
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = SubscribeDialog(_(u"Subscribe"),
                          resources=resources, view=view, url=url, name=name,
                          modal=modal, immediate=immediate, mine=mine,
                          publisher=publisher, color=color)
    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
        return win
