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

import wx
from osaf.framework.blocks import (BlockEvent, NewBlockWindowEvent, MenuItem,
    Menu)
from osaf.framework.blocks.Block import Block

from osaf import pim, sharing
from application import schema, dialogs
from classes import *

from i18n import MessageFactory
_ = MessageFactory("Chandler-gdataPlugin")

import logging
logger = logging.getLogger(__name__)

__all__ = [
    'ShowCalendarListWindow',
    'makeGdataMenu',
]



def ShowCalendarListWindow(rv):
    win = CalendarListFrame(None, -1, _("Google Calendars"),
        size=(300,100), style=wx.DEFAULT_FRAME_STYLE, rv=rv)
    win.Show()



class CalendarListFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        self.rv = kwds['rv']
        del kwds['rv']
        super(CalendarListFrame, self).__init__(*args, **kwds)

        self.panel = wx.Panel(self, -1)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.accountControl = wx.Choice(self.panel, -1) #, size=(300,10))
        self.sizer.Add(self.accountControl, 0,
            wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.calendarControl = wx.ListBox(self.panel, -1, size=(400,300))
        self.sizer.Add(self.calendarControl, 0,
            wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.okControl = wx.Button(self.panel, wx.ID_OK, _(u"Subscribe"))
        self.sizer.Add(self.okControl, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.cancelControl = wx.Button(self.panel, wx.ID_CANCEL)
        self.sizer.Add(self.cancelControl, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnSubscribe, id=wx.ID_OK)


        self.panel.SetSizer(self.sizer)
        self.panel.Layout()
        self.sizer.Fit(self)

        self.PopulateAccounts()
        self.PopulateCalendars()

        self.Bind(wx.EVT_CHOICE, self.OnChangeAccount,
                  id=self.accountControl.GetId())


    def OnCloseWindow(self, event):
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()


    def PopulateAccounts(self):

        self.currentAccount = None

        accounts = sorted(GDataAccount.iterItems(self.rv),
                          key = lambda x: x.displayName.lower())

        for account in accounts:
            newIndex = self.accountControl.Append(account.displayName)
            self.accountControl.SetClientData(newIndex, account)

        self.accountControl.SetSelection(0)
        account = self.accountControl.GetClientData(0)
        self.currentAccount = account


    def PopulateCalendars(self):
        self.calendarControl.Clear()
        if self.currentAccount is not None:
            for title, url, access, color in self.currentAccount.getCalendars():
                if access == "read":
                    title = "%s (view only)" % title
                newIndex = self.calendarControl.Append(title)
                self.calendarControl.SetClientData(newIndex, url)


    def OnChangeAccount(self, evt):
        accountIndex = self.accountControl.GetSelection()
        account = self.accountControl.GetClientData(accountIndex)
        self.currentAccount = account
        self.PopulateCalendars()


    def OnSubscribe(self, evt):
        calendarIndex = self.calendarControl.GetSelection()
        url = self.calendarControl.GetClientData(calendarIndex)
        collection = self.currentAccount.subscribe(url)
        schema.ns('osaf.app', self.rv).sidebarCollection.add(collection)
        self.OnCloseWindow(None)



def ensureGoogleAccountSetUp(rv):
    while True:
        if len(list(GDataAccount.iterItems(rv))) > 0:
            return True

        msg = _("No Google account set up yet.  Would you like to set an account up now?")
        response = wx.MessageBox(msg, _("Google Account"),
            style=wx.YES_NO) == wx.YES
        if response == False:
            return False
        response = dialogs.AccountPreferences.ShowAccountPreferencesDialog(
                rv=rv, create="SHARING_GDATA")
        if response == False:
            return False



class GdataMenuHandler(Block):

    def on_gdata_ShowCalendarListEvent(self, event):
        rv = self.itsView

        msg = _("Syncing Google calendars is still experimental. Sync only with test calendars.\n\nNote: recurring events are not supported.\n\nProceed?")
        response = wx.MessageBox(msg, _("Caution!"),
            style=wx.YES_NO|wx.ICON_EXCLAMATION) == wx.YES
        if response:
            if ensureGoogleAccountSetUp(rv):
                ShowCalendarListWindow(rv)


def makeGdataMenu(parcel, parentMenu):

    handler = GdataMenuHandler.update(parcel, None,
        blockName='_gdata_GdataMenuHandler')

    showCalendarListEvent = BlockEvent.update(parcel, None,
        blockName='_gdata_ShowCalendarList',
        dispatchEnum='SendToBlockByReference',
        destinationBlockReference=handler)

    gdataMenu = Menu.update(parcel, None, blockName='_gdata_gdataMenu',
        title="Google",
        parentBlock=parentMenu)

    MenuItem.update(parcel, None, blockName='_gdata_ShowCalendarListItem',
        title=_(u"Subscribe to Google Calendar..."),
        helpString=_(u"Brings up a list of Google calendars to sync with"),
        event=showCalendarListEvent,
        parentBlock=gdataMenu)
