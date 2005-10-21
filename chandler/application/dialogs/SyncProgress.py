import os, sys
import traceback
import logging
import wx
import wx.xrc
from osaf import sharing
from application import Globals, schema
from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)

SHARING = "osaf.sharing"
CONTENTMODEL = "osaf.pim"

class SyncDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None, collection=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
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
                self.addMessage("Syncing all shares\n")
                stats = sharing.syncAll(view, updateCallback=self.updateCallback)
            else:
                self.addMessage("Syncing one collection\n")
                stats = sharing.sync(self.collection,
                    updateCallback=self.updateCallback)
            
            for stat in stats:
                self.addMessage("%s (%s) added:%d modified:%d removed:%d\n" %
                    (view.findUUID(stat['share']).getLocation(), stat['op'],
                    len(stat['added']),
                    len(stat['modified']),
                    len(stat['removed'])))

        except sharing.SharingError, err:
            logger.exception("Error during sync")
            self.addMessage(_(u"Sharing Error:\n%(error)s\n") % {'error': err})
        except Exception, e:
            logger.exception("Error during sync")
            self.addMessage(_(u"Error:\n%(error)s\n") % {'error': e})

        self.btnOk.Enable(True)
        self.btnCancel.Enable(False)
        self.addMessage("\nDone\n")

    def OnOk(self, evt):
        self.EndModal(False)

    def OnCancel(self, evt):
        self.cancelPressed = True

    def updateCallback(self, msg=None):
        if msg is not None:
            self.addMessage(msg + "\n")

        wx.Yield()
        return self.cancelPressed

    def addMessage(self, message):
        self.textStatus.AppendText(message)
        wx.Yield()

def Show(parent, view=None, collection=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'SyncProgress_wdr.xrc')
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = SyncDialog(parent, _(u"Synchronization Progress"),
     resources=resources, view=view, collection=collection)
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()
