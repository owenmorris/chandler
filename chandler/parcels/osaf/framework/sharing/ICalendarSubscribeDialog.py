import os
import traceback
import logging
import wx
import wx.xrc
import Sharing
import ICalendar
import application.Globals as Globals
from repository.item.Query import KindQuery
import application.dialogs.Util
import application.Parcel

logger = logging.getLogger('Sharing')
logger.setLevel(logging.INFO)

SHARING = "http://osafoundation.org/parcels/osaf/framework/sharing"
CONTENTMODEL = "http://osafoundation.org/parcels/osaf/contentmodel"

class ICalendarSubscribeDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
        self.resources = resources
        self.parent = parent

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.toolPanel = self.resources.LoadPanel(self, "ICalendarSubscribe")
        self.mySizer.Add(self.toolPanel, 0, wx.GROW|wx.ALL, 5)

        self.statusPanel = self.resources.LoadPanel(self, "StatusPanel")
        self.statusPanel.Hide()
        self.accountPanel = self.resources.LoadPanel(self, "UsernamePasswordPanel")
        self.accountPanel.Hide()

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.textUrl = wx.xrc.XRCCTRL(self, "TEXT_URL")
        wx.EVT_SET_FOCUS(self.textUrl, self.OnFocusGained)
        self.Bind(wx.EVT_TEXT, self.OnTyping, self.textUrl)

        self.textStatus = wx.xrc.XRCCTRL(self, "TEXT_STATUS")
        self.textUsername = wx.xrc.XRCCTRL(self, "TEXT_USERNAME")
        self.textPassword = wx.xrc.XRCCTRL(self, "TEXT_PASSWORD")

        self.Bind(wx.EVT_BUTTON, self.OnSubscribe, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

        self.textUrl.SetFocus()


    def OnSubscribe(self, evt):
        view = self.view
        url = self.textUrl.GetValue()
        if url.startswith('webcal:'):
            url = 'http:' + url[7:]
        share = Sharing.findMatchingShare(view, url)
        if share is not None:
            self.__showStatus("You are already subscribed to that calendar")
            return

        (useSSL, host, port, path, query, fragment) = Sharing.splitUrl(url)

        account = Sharing.findMatchingWebDAVAccount(view, url)
        if account is None:
            account = Sharing.WebDAVAccount(view=view)
            account.useSSL = useSSL
            account.host = host
            account.port = port
            # Get the parent directory of the given path:
            # '/dev1/foo/bar' becomes ['dev1', 'foo']
            parentPath = path.strip('/').split('/')[:-1]
            # ['dev1', 'foo'] becomes "dev1/foo"
            parentPath = "/".join(parentPath)
            account.path = parentPath
            account.displayName = "WebDAV account for %s" % host

        if self.accountPanel.IsShown():
            account.username = self.textUsername.GetValue()
            account.password = self.textPassword.GetValue()

        shareName = path.strip("/").split("/")[-1]
        conduit = Sharing.SimpleHTTPConduit(view=view, shareName=shareName,
                                            account=account)
        format = ICalendar.ICalendarFormat(view=view)
        share = Sharing.Share(view=view, conduit=conduit, format=format)
        share.mode = "get"
        try:
            self.__showStatus("In progress...")
            wx.Yield()
            share.get()
            collection = share.contents
            mainView = Globals.views[0]
            mainView.postEventByName("AddToSidebarWithoutCopying", {'items':[collection]})
            view.commit()
            mainView.postEventByName('RequestSelectSidebarItem', {'item':collection})
            mainView.postEventByName('SelectItemBroadcastInsideActiveView', {'item':collection})
            self.EndModal(True)

        except Sharing.NotAllowed, err:
            self.__showAccountInfo(account)
            conduit.delete()
            format.delete()
            share.delete()
        except Sharing.NotFound, err:
            self.__showStatus("That calendar was not found")
            conduit.delete()
            format.delete()
            share.delete()
        except Sharing.SharingError, err:
            self.__showStatus("Sharing Error:\n%s" % err.message)
            conduit.delete()
            format.delete()
            share.delete()
        except Exception, e:
            self.__showStatus("Exception:\n%s" % traceback.format_exc(10))
            logger.info("Sharing Exception: %s" % traceback.format_exc(10))
            conduit.delete()
            format.delete()
            share.delete()

    def OnTyping(self, evt):
        self.__hideStatus()
        self.__hideAccountInfo()


    def __showAccountInfo(self, account):
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
        self.EndModal(False)

    def OnFocusGained(self, evt):
        """ Select entire text field contents when focus is gained. """
        control = evt.GetEventObject()
        wx.CallAfter(control.SetSelection, -1, -1)


def Show(parent, view=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'parcels', 'osaf', 'framework', 'sharing',
     'ICalendarSubscribeDialog_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)
    win = ICalendarSubscribeDialog(parent, "Subscribe to Calendar",
     resources=resources, view=view)
    win.CenterOnScreen()
    win.ShowModal()
