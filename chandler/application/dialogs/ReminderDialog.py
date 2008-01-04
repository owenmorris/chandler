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


import sys, wx
from datetime import datetime, timedelta
from i18n import ChandlerMessageFactory as _
from osaf import pim

DAY    = 1440
HOUR   = 60
MINUTE = 1

# Message strings. Note that the singular ones don't need value interpolation.
singularPastMessages = { DAY: _(u'1 day ago'), 
                         HOUR: _(u'1 hour ago'), 
                         MINUTE: _(u'1 minute ago') }
singularFutureMessages = { DAY: _(u'1 day from now'), 
                           HOUR: _(u'1 hour from now'), 
                           MINUTE: _(u'1 minute from now') }
pluralPastMessages = { DAY: _(u'%(numOf)d days ago'), 
                       HOUR: _(u'%(numOf)d hours ago'), 
                       MINUTE: _(u'%(numOf)d minutes ago') }
pluralFutureMessages = { DAY: _(u'%(numOf)d days from now'), 
                         HOUR: _(u'%(numOf)d hours from now'), 
                         MINUTE: _(u'%(numOf)d minutes from now') }

# NOTE: We acutally use a wx.Frame here, instead of a wx.Dialog, so
# that activating the window will not cause the whole app to be
# activated.  (Windows and Linux only.  Mac will still activate the
# whole application...)

# NOTE #2: Using the wx.STAY_ON_TOP flag can be viewed as violating
# the various style guides because it causes the window to be raised
# above other apps if Chandler is not the active application.  It
# would be better to just rely on the RequestUserAttention call below
# to flash the taskbar icon, but there should probably also be a sound
# played to make sure the user notices it...  Leaving the STAY_ON_TOP
# until there is a sound to play.

class ReminderDialog(wx.Frame):
    def __init__(self, size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=(wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER) | wx.STAY_ON_TOP):

        wx.Frame.__init__(self, None, -1, name=u'ReminderDialog', pos=pos, 
                          size=size, style=style, title=_(u"Reminders"))
        panel = wx.Panel(self)
        
        # Note that we're not in the process of closing; we'll set this
        # when the widget gets destroyed, letting UpdateList know it can NOP.
        self.reminderClosing = False

        # Note that we don't have anyone to notify when a reminder is dismissed.
        self.dismissCallback = None
        
        # Now continue with the normal construction of the dialog
        # contents: a list, then a row of buttons
        sizer = wx.BoxSizer(wx.VERTICAL)
        listCtrl = wx.ListCtrl(panel, -1, size=(400,80), style=wx.LC_REPORT|wx.LC_NO_HEADER)
        listCtrl.InsertColumn(0, _(u"Title"))
        listCtrl.InsertColumn(1, _(u"Date"))
        listCtrl.SetColumnWidth(0, 250)
        listCtrl.SetColumnWidth(1, 140)
        listCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectionChanged)
        listCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onSelectionChanged)
        self.reminders = {}
        sizer.Add(listCtrl, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        snoozeButton = wx.Button(panel, -1, _(u"&Snooze for 5 minutes"), name="Snooze for 5 minutes")
        snoozeButton.Enable(False)
        snoozeButton.Bind(wx.EVT_BUTTON, self.onSnooze)
        box.Add(snoozeButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        dismissButton = wx.Button(panel, wx.ID_OK, _(u"&Dismiss"))
        dismissButton.Enable(False)
        dismissButton.Bind(wx.EVT_BUTTON, self.onDismiss)
        box.Add(dismissButton, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        dismissAllButton = wx.Button(panel, wx.ID_OK, _(u"Dismiss &All"))
        dismissAllButton.SetDefault()
        dismissAllButton.Bind(wx.EVT_BUTTON, self.onDismiss)
        box.Add(dismissAllButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        # Do "dismiss all" on close
        self.Bind(wx.EVT_CLOSE, self.onClose)
        
        # Clean up when the app quits
        mainFrame = wx.GetApp().mainFrame
        mainFrame.Bind(wx.EVT_CLOSE, self.onAppQuit)
        
        # Note when we're being destroyed, so we can ignore subsequent events
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)

        # Save controls using an attribute name that hopefully won't collide with
        # any wx attributes
        self.reminderControls = { 'list': listCtrl, 'snooze': snoozeButton, 'dismiss': dismissButton, 'dismissAll': dismissAllButton }

        panel.SetSizer(sizer)
        sizer.Fit(self)
        self.CenterOnScreen()
        self.Show()
        self.RequestUserAttention()

    def onAppQuit(self, event):
        if self:
            self.Unbind(wx.EVT_CLOSE, self)
            self.reminderClosing = True
            self.Close(force=True)
        event.Skip()
   
    
    def onDestroy(self, event):
        # print "*** destroying"
        self.reminderClosing = True
        
    def onClose(self, event):
        # If we have been asked to close directly (i.e. not as a result of the
        # main frame closing and the app quitting),  treat "close" as
        # "dismiss all"
        if self and not self.reminderClosing:
            listCtrl = self.reminderControls['list']
            if listCtrl.GetItemCount() > 0:
                self.onDismiss(event)
        event.Skip()
        
    def onSelectionChanged(self, event):
        self.UpdateControlEnabling()
    
    def UpdateControlEnabling(self):
        listCtrl = self.reminderControls['list']
        haveSelection = listCtrl.GetSelectedItemCount() > 0
        haveAnyItems = listCtrl.GetItemCount() > 0
        self.reminderControls['snooze'].Enable(haveSelection)
        self.reminderControls['dismiss'].Enable(haveSelection)
        self.reminderControls['dismissAll'].Enable(haveAnyItems)
        return haveAnyItems
    
    def UpdateList(self, reminderTuples):
        """ Update our reminder list; return info about our next firing.
        
        We return a tuple containing a time (or None), an item (or None), and 
        a flag that indicates whether this dialog should stay open. If we've 
        still got reminders displayed, this'll be a minute from now (so we can 
        update their "when" column) and the flag will be True; if not, it'll 
        be when the next reminder is due.
        """

        # Don't do anything if we're responding to an update after our 
        # widget's been destroyed.
        if self.reminderClosing:
            return (None, None, False)
        
        selectedReminders = list(self.getListItems(True))
        listCtrl = self.reminderControls['list']
        listCtrl.DeleteAllItems()
        self.remindersInList = {}
        nextReminderTime = pim.Reminder.farFuture
        nextReminderItem = None
        tzinfo = wx.GetApp().UIRepositoryView.tzinfo.default

        for t in reminderTuples:
            (reminderTime, remindable, reminder) = t
            if reminderTime < datetime.now(tzinfo):
                # Another pending reminder; add it to the list.
                index = listCtrl.InsertStringItem(sys.maxint, 
                                                  remindable.displayName)
                self.remindersInList[index] = t

                # Make a relative expression of its time ("3 minutes from now").
                eventTime = reminder.getItemBaseTime(remindable)
                deltaMessage = self.RelativeDateTimeMessage(eventTime)
                listCtrl.SetStringItem(index, 1, deltaMessage)

                # Select it if it was selected before
                try:
                    selectedReminders.index(t)
                except ValueError:
                    pass
                else:
                    listCtrl.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            else:
                # This reminder is still in the future.
                nextReminderTime = reminderTime
                nextReminderItem = remindable
                break

        # If we have stuff, but nothing selected, select the first thing
        closeIt = listCtrl.GetItemCount() == 0
        if not closeIt and listCtrl.GetSelectedItemCount() == 0:
            listCtrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            
        self.UpdateControlEnabling()

        # When do we want to be called again?
        # If we have anything in the list, call us in a minute so we can update
        # the event times; otherwise, update us at the first future reminder time;
        # otherwise, no reminder needed.
        if not closeIt:
            now = datetime.now(tzinfo)
            nextReminderTime = now + timedelta(seconds=(60-now.second))
        return (nextReminderTime, nextReminderItem, closeIt)

    def RelativeDateTimeMessage(self, eventTime):
        """ Build a message expressing relative time to this time, 
        like '12 minutes from now', 'Now', or '1 day ago'. """
        tzinfo = wx.GetApp().UIRepositoryView.tzinfo.default
        now = datetime.now(tzinfo)
        delta = now - eventTime
        deltaMinutes = (delta.days * 1440L) + (delta.seconds / 60)
        if 0 <= deltaMinutes < 1:
            return _(u"Now")
        
        # Pick a friendly scale factor
        absDeltaMinutes = abs(deltaMinutes)        
        ago = absDeltaMinutes == deltaMinutes
        if absDeltaMinutes < 120: # Use "minutes" if it's less than 2 hrs
            scale = MINUTE
        elif absDeltaMinutes < 2880: # Use "hours" if it's less than 2 days
            scale = HOUR
        else:
            scale = DAY

        # Scale the value to the units.
        value = round((absDeltaMinutes / scale) + 0.49999)
        
        # Make the message.
        if value == 1:
            # Singular strings don't need the "1" substituted into them
            msg = (ago and singularPastMessages or singularFutureMessages)[scale]
        else:
            # Get a string and stick the value in it.
            msg = (ago and pluralPastMessages or pluralFutureMessages)[scale] \
                % { 'numOf' : value }
        return msg

    def onDismiss(self, event):
        """ 
        Dismiss reminders, either limited to the selection, or not: the event
        can come from the dismiss or dismissAll buttons, or from the window's close box.
        """
        dismissSelection = event.GetEventObject() is self.reminderControls['dismiss']
        for (reminderTime, remindable, reminder) in self.getListItems(dismissSelection):
            reminder.dismissItem(remindable)
        wx.GetApp().UIRepositoryView.commit()
        if self.dismissCallback is not None:
            self.dismissCallback()

    def onSnooze(self, event):
        """ Snooze the selected reminders for five minutes """
        for (reminderTime, remindable, reminder) in self.getListItems(True):
            reminder.snoozeItem(remindable, timedelta(minutes=5))
        wx.GetApp().UIRepositoryView.commit()
        if self.dismissCallback is not None:
            self.dismissCallback()

    def getListItems(self, selectedOnly):
        """ Provide iteration over ListCtrl items """
        listCtrl = self.reminderControls['list']
        # Note: because our caller may be updating the list, we don't act
        # like a generator; return the whole list at once.
        results = []
        for index in range(listCtrl.GetItemCount()):
            if not selectedOnly or listCtrl.GetItemState(index, wx.LIST_STATE_SELECTED):
                entryTuple = self.remindersInList[index]
                if (not pim.isDead(entryTuple[1]) and
                    not pim.isDead(entryTuple[2])):
                    results.append(entryTuple)
        return results

