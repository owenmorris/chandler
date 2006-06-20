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
from application import Globals
from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)

class SyncDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, rv=None, collection=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = rv
        self.resources = resources
        self.parent = parent
        self.collection = collection

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "SyncProgress")
        self.mySizer.Add(self.toolPanel, 0, wx.GROW|wx.ALL, 5)

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.textStatus = wx.xrc.XRCCTRL(self, "TEXT_STATUS")
        self.btnOk = wx.xrc.XRCCTRL(self, "wxID_OK")
        self.btnCancel = wx.xrc.XRCCTRL(self, "wxID_CANCEL")
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

        wx.CallAfter(self.OnSync)


    def OnSync(self, evt=None):
        view = self.view

        self.btnOk.Enable(False)
        self.btnCancel.Enable(True)
        self.cancelPressed = False

        try:
            if self.collection is None:
                # self.addMessage("Synchronizing all shares\n")
                stats = sharing.syncAll(view, updateCallback=self.updateCallback)
            else:
                # self.addMessage("Synchoronizing collection\n")
                stats = sharing.sync(self.collection,
                    updateCallback=self.updateCallback)

            uploaded = 0
            downloaded = 0
            removedLocally = 0
            removedRemotely = 0

            for stat in stats:
                if stat['op'] == 'put':
                    uploaded += len(stat['added'])
                    uploaded += len(stat['modified'])
                    removedRemotely += len(stat['removed'])
                elif stat['op'] == 'get':
                    downloaded += len(stat['added'])
                    downloaded += len(stat['modified'])
                    removedLocally += len(stat['removed'])

            if uploaded:
                self.addMessage(_(u"%d items that were modified by you have been uploaded\n") % uploaded)
            if downloaded:
                self.addMessage(_(u"%d items that were modified by others have been downloaded\n") % downloaded)

        except sharing.SharingError, err:
            logger.exception("Error during sync")
            self.addMessage(_(u"Sharing Error:\n%(error)s\n") % {'error': err})
        except Exception, e:
            logger.exception("Error during sync")
            self.addMessage(_(u"Error:\n%(error)s\n") % {'error': e})

        self.btnOk.Enable(True)
        self.btnCancel.Enable(False)
        self.addMessage(_(u"Done\n"))

    def OnOk(self, evt):
        self.EndModal(False)

    def OnCancel(self, evt):
        self.cancelPressed = True

    def updateCallback(self, msg=None, work=None, totalWork=None):
        if msg is not None:
            self.addMessage(msg + "\n")

        wx.Yield()
        return self.cancelPressed

    def addMessage(self, message):
        self.textStatus.AppendText(message)
        wx.Yield()

def Show(parent, rv=None, collection=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'SyncProgress_wdr.xrc')
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = SyncDialog(parent, _(u"Synchronization Progress"),
     resources=resources, rv=rv, collection=collection)
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()
