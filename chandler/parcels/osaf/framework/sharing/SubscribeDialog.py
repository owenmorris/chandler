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

class SubscribeDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, view=None, url=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.view = view
        self.resources = resources
        self.parent = parent

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
            self.__showStatus("You are already subscribed")
            return

        share = Sharing.newInboundShare(view, url)

        if share is None:
            return

        if self.accountPanel.IsShown():
            share.conduit.account.username = self.textUsername.GetValue()
            share.conduit.account.password = self.textPassword.GetValue()

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
            self.__showAccountInfo(share.conduit.account)
            share.conduit.delete(True)
            share.format.delete(True)
            share.delete(True)
        except Sharing.NotFound, err:
            self.__showStatus("That collection was not found")
            share.conduit.delete(True)
            share.format.delete(True)
            share.delete(True)
        except Sharing.SharingError, err:
            self.__showStatus("Sharing Error:\n%s" % err.message)
            self.__showStatus("Exception:\n%s" % traceback.format_exc(10))
            share.conduit.delete(True)
            share.format.delete(True)
            share.delete(True)
        except Exception, e:
            self.__showStatus("Exception:\n%s" % traceback.format_exc(10))
            logger.info("Sharing Exception: %s" % traceback.format_exc(10))
            share.conduit.delete(True)
            share.format.delete(True)
            share.delete(True)

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


def Show(parent, view=None, url=None):
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'parcels', 'osaf', 'framework', 'sharing',
     'SubscribeDialog_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)
    win = SubscribeDialog(parent, "Subscribe to Shared Collection",
     resources=resources, view=view, url=url)
    win.CenterOnScreen()
    win.ShowModal()
