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
from util import task, viewpool
from application import schema, Globals
from i18n import ChandlerMessageFactory as _
from AccountInfoPrompt import PromptForNewAccountInfo

logger = logging.getLogger(__name__)

MAX_UPDATE_MESSAGE_LENGTH = 50

class SubscribeDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None, url=None, name=None, modal=True,
         immediate=False, mine=None, publisher=None, freebusy=False):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
        self.resources = resources
        self.parent = parent
        self.modal = modal
        self.name = name
        self.mine = mine
        self.publisher = publisher
        self.freebusy = freebusy

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "Subscribe")
        self.mySizer.Add(self.toolPanel, 0, wx.GROW|wx.ALL, 5)

        self.statusPanel = self.resources.LoadPanel(self, "StatusPanel")
        self.statusPanel.Hide()
        self.accountPanel = self.resources.LoadPanel(self, "UsernamePasswordPanel")
        self.accountPanel.Hide()

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.textUrl = wx.xrc.XRCCTRL(self, "TEXT_URL")
        if url is not None:
            self.textUrl.SetValue(url)
        else:
            account = sharing.schema.ns('osaf.sharing',
                self.view).currentWebDAVAccount.item
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
        self.forceFreeBusy = wx.xrc.XRCCTRL(self, "CHECKBOX_FORCEFREEBUSY")
        if self.freebusy:
            self.forceFreeBusy.SetValue(True)

        self.subscribeButton = wx.xrc.XRCCTRL(self, "wxID_OK")

        self.Bind(wx.EVT_BUTTON, self.OnSubscribe, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

        self.textUrl.SetFocus()
        self.textUrl.SetSelection(-1, -1)

        self.subscribing = False

        if immediate:
            self.OnSubscribe(None)


    def accountInfoCallback(self, host, path):
        return PromptForNewAccountInfo(self, host=host, path=path)

    def updateCallback(self, msg=None, percent=None):
        if msg is not None:
            msg = msg.replace('\n', ' ')
            # @@@MOR: This is unicode unsafe:
            if len(msg) > MAX_UPDATE_MESSAGE_LENGTH:
                msg = "%s..." % msg[:MAX_UPDATE_MESSAGE_LENGTH]
            self._showStatus(msg)
        if percent is not None:
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
            for share in collection.shares:
                share.sharer = me

        # Put this collection into "My items" if not checked:
        if not self.checkboxKeepOut.GetValue() or self.mine:
            logger.info(_(u'Moving collection into My Items'))
            schema.ns('osaf.pim', self.view).mine.addSource(collection)

        schema.ns("osaf.app", self.view).sidebarCollection.add(collection)

        if self.modal:
            self.EndModal(True)
        self.Destroy()
        
        self.subscribing = False

    def _shareError(self, err):

        viewpool.releaseView(self.taskView)

        self.subscribeButton.Enable(True)
        self.gauge.SetValue(0)

        if isinstance(err, sharing.NotAllowed):
            self._showAccountInfo()
        elif isinstance(err, sharing.NotFound):
            self._showStatus(_(u"That collection was not found"))
        elif isinstance(err, sharing.AlreadySubscribed):
            self._showStatus(_(u"You are already subscribed"))
        else:
            logger.exception("Error during subscribe")
            self._showStatus(_(u"Sharing Error:\n%(error)s") % {'error': err})

        self.subscribing = False


    def OnSubscribe(self, evt):

        view = self.view
        url = self.textUrl.GetValue()
        url = url.strip()
        if url.startswith('webcal:'):
            url = 'http:' + url[7:]

        if self.accountPanel.IsShown():
            username = self.textUsername.GetValue()
            password = self.textPassword.GetValue()
        else:
            username = None
            password = None

        forceFreeBusy = self.forceFreeBusy.GetValue()

        self.subscribeButton.Enable(False)
        self.gauge.SetValue(0)
        self.subscribing = True
        self._showStatus(_(u"In progress..."))
        wx.Yield()


        class ShareTask(task.Task):

            def __init__(task, view, url, username, password, forceFreeBusy):
                super(ShareTask, task).__init__(view)
                task.url = url
                task.username = username
                task.password = password
                task.forceFreeBusy = forceFreeBusy

            def error(task, err):
                self._shareError(err)

            def success(task, result):
                self._finishedShare(result)

            def _updateCallback(task, **kwds):
                cancel = task.cancelRequested
                task.callInMainThread(lambda _:self.updateCallback(**_), kwds)
                return cancel

            def run(task):
                task.cancelRequested = False

                collection = sharing.subscribe(task.view, task.url,
                    updateCallback=task._updateCallback,
                    username=task.username, password=task.password,
                    forceFreeBusy=task.forceFreeBusy)

                return collection.itsUUID

        self.view.commit()
        self.taskView = viewpool.getView(self.view.repository)
        self.currentTask = ShareTask(self.taskView, url, username, password,
                                     forceFreeBusy)
        self.currentTask.start(inOwnThread=True)



    def OnTyping(self, evt):
        self._hideStatus()
        self._hideAccountInfo()

    def _showAccountInfo(self):
        self._hideStatus()

        if not self.accountPanel.IsShown():
            self.mySizer.Add(self.accountPanel, 0, wx.GROW, 5)
            self.accountPanel.Show()
            self.textUsername.SetFocus()

        self._resize()

    def _hideAccountInfo(self):

        if self.accountPanel.IsShown():
            self.accountPanel.Hide()
            self.mySizer.Detach(self.accountPanel)
            self._resize()

    def _showStatus(self, text):
        self._hideAccountInfo()

        if not self.statusPanel.IsShown():
            self.mySizer.Add(self.statusPanel, 0, wx.GROW, 5)
            self.statusPanel.Show()

        self.textStatus.SetLabel(text)
        self._resize()

    def _hideStatus(self):
        if self.statusPanel.IsShown():
            self.statusPanel.Hide()
            self.mySizer.Detach(self.statusPanel)
            self._resize()

    def _resize(self):
        self.mySizer.Layout()
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)


    def OnCancel(self, evt):
        if self.subscribing:
            self.currentTask.cancelRequested = True
        else:
            if self.modal:
                self.EndModal(False)
            self.Destroy()

def Show(parent, view=None, url=None, name=None, modal=False, immediate=False,
         mine=None, publisher=None, freebusy=False):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'SubscribeCollection.xrc')
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = SubscribeDialog(parent, _(u"Subscribe to Shared Collection"),
                          resources=resources, view=view, url=url, name=name,
                          modal=modal, immediate=immediate, mine=mine,
                          publisher=publisher, freebusy=freebusy)
    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
        return win
