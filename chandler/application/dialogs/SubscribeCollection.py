import os, sys
import logging
import wx
import wx.xrc
from osaf import sharing
import application.Globals as Globals
import application.dialogs.Util
from i18n import OSAFMessageFactory as _
from application import schema
from AccountInfoPrompt import PromptForNewAccountInfo
from osaf.framework.blocks.Block import Block

logger = logging.getLogger(__name__)

MAX_UPDATE_MESSAGE_LENGTH = 50

class SubscribeDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None, url=None, modal=True):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
        self.resources = resources
        self.parent = parent
        self.modal = modal

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
        self.subscribeButton = wx.xrc.XRCCTRL(self, "wxID_OK")

        self.Bind(wx.EVT_BUTTON, self.OnSubscribe, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))


        self.textUrl.SetFocus()
        self.textUrl.SetInsertionPointEnd()
        self.subscribing = False


    def accountInfoCallback(self, host, path):
        return PromptForNewAccountInfo(self, host=host, path=path)

    def updateCallback(self, msg=None, percent=None):
        if msg is not None:
            msg = msg.replace('\n', ' ')
            # @@@MOR: This is unicode unsafe:
            if len(msg) > MAX_UPDATE_MESSAGE_LENGTH:
                msg = "%s..." % msg[:MAX_UPDATE_MESSAGE_LENGTH]
            self.__showStatus(msg)
        if percent is not None:
            self.gauge.SetValue(percent)
        wx.Yield()
        return self.cancelPressed

    def OnSubscribe(self, evt):
        view = self.view
        url = self.textUrl.GetValue()
        url = url.strip()
        if url.startswith('webcal:'):
            url = 'http:' + url[7:]

        try:

            if self.accountPanel.IsShown():
                username = self.textUsername.GetValue()
                password = self.textPassword.GetValue()
            else:
                username = None
                password = None

            self.subscribeButton.Enable(False)
            self.gauge.SetValue(0)
            self.subscribing = True
            self.cancelPressed = False
            self.__showStatus(_(u"In progress..."))
            wx.Yield()

            collection = sharing.subscribe(view, url,
                accountInfoCallback=self.accountInfoCallback,
                updateCallback=self.updateCallback,
                username=username, password=password)

            if collection is None:
                # user cancelled out of account dialog
                self.subscribing = False
                if self.modal:
                    self.EndModal(True)
                self.Destroy()
                return

            # Keep this collection out of "My items" if checked:
            if not self.checkboxKeepOut.GetValue():
                logger.info(_(u'Moving collection out of My Items'))
                schema.ns('osaf.pim', view).mine.addSource(collection)

            schema.ns("osaf.app", view).sidebarCollection.add (collection)
            # Need to SelectFirstItem -- DJA
            share = sharing.getShare(collection)

            if share.filterClasses and len(share.filterClasses) == 1:
                parts = share.filterClasses[0].split (".")
                className = parts.pop ()
                module = __import__ ('.'.join(parts), globals(), locals(), ['__name__'])
                filterClass = module.__dict__[className].getKind (view)
            else:
                filterClass = None
            Block.findBlockByName ("Sidebar").setPreferredKind(filterClass)

            if self.modal:
                self.EndModal(True)
            self.Destroy()

        except Exception, e:
            self.subscribeButton.Enable(True)
            self.gauge.SetValue(0)

            if isinstance(e, sharing.NotAllowed):
                self.__showAccountInfo()
            elif isinstance(e, sharing.NotFound):
                self.__showStatus(_(u"That collection was not found"))
            elif isinstance(e, sharing.AlreadySubscribed):
                self.__showStatus(_(u"You are already subscribed"))
            else:
                logger.exception("Error during subscribe for %s" % url)
                self.__showStatus(_(u"Sharing Error:\n%(error)s") % {'error': e})

        self.subscribing = False


    def OnTyping(self, evt):
        self.__hideStatus()
        self.__hideAccountInfo()

    def __showAccountInfo(self):
        self.__hideStatus()

        if not self.accountPanel.IsShown():
            self.mySizer.Add(self.accountPanel, 0, wx.GROW, 5)
            self.accountPanel.Show()
            self.textUsername.SetFocus()

        self.__resize()

    def __hideAccountInfo(self):

        if self.accountPanel.IsShown():
            self.accountPanel.Hide()
            self.mySizer.Detach(self.accountPanel)
            self.__resize()

    def __showStatus(self, text):
        self.__hideAccountInfo()

        if not self.statusPanel.IsShown():
            self.mySizer.Add(self.statusPanel, 0, wx.GROW, 5)
            self.statusPanel.Show()

        self.textStatus.SetLabel(text)
        self.__resize()

    def __hideStatus(self):
        if self.statusPanel.IsShown():
            self.statusPanel.Hide()
            self.mySizer.Detach(self.statusPanel)
            self.__resize()

    def __resize(self):
        self.mySizer.Layout()
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)


    def OnCancel(self, evt):
        if self.subscribing:
            self.cancelPressed = True
        else:
            if self.modal:
                self.EndModal(False)
            self.Destroy()

def Show(parent, view=None, url=None, modal=True):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'SubscribeCollection_wdr.xrc')
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = SubscribeDialog(parent, _(u"Subscribe to Shared Collection"),
     resources=resources, view=view, url=url, modal=modal)
    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
        return win
