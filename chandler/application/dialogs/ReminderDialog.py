__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, sys, wx
from datetime import datetime, timedelta

class ReminderDialog(wx.Dialog):
    def __init__(self, parent, ID, size=wx.DefaultSize,
     pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, _("Reminders"), pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Note that we're not in the process of closing; we'll set this
        # when the widget gets destroyed, letting UpdateList know it can NOP.
        self.reminderClosing = False

        # Now continue with the normal construction of the dialog
        # contents: a list, then a row of buttons
        sizer = wx.BoxSizer(wx.VERTICAL)
        listCtrl = wx.ListCtrl(self, -1, size=(400,80), style=wx.LC_REPORT|wx.LC_NO_HEADER)
        listCtrl.InsertColumn(0, "title")
        listCtrl.InsertColumn(1, "event time")
        listCtrl.SetColumnWidth(0, 250)
        listCtrl.SetColumnWidth(1, 140)
        listCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectionChanged)
        listCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onSelectionChanged)
        self.reminders = {}
        sizer.Add(listCtrl, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        snoozeButton = wx.Button(self, -1, _("Snooze 5 minutes"))
        snoozeButton.Enable(False)
        snoozeButton.Bind(wx.EVT_BUTTON, self.onSnooze)
        box.Add(snoozeButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        dismissButton = wx.Button(self, wx.ID_OK, _("Dismiss"))
        dismissButton.Enable(False)
        dismissButton.Bind(wx.EVT_BUTTON, self.onDismiss)
        box.Add(dismissButton, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        dismissAllButton = wx.Button(self, wx.ID_OK, _("Dismiss All"))
        dismissAllButton.Bind(wx.EVT_BUTTON, self.onDismiss)
        box.Add(dismissAllButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        # Do "dismiss all" on close
        self.Bind(wx.EVT_CLOSE, self.onClose)
        
        # Note when we're being destroyed, so we can ignore subsequent events
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)

        # Save controls using attribute names that hopefully wont collide with
        # any wx attributes
        self.reminderControls = { 'list': listCtrl, 'snooze': snoozeButton, 'dismiss': dismissButton, 'dismissAll': dismissAllButton }

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.CenterOnScreen()
        self.Show()
    
    def onDestroy(self, event):
        # print "*** destroying"
        self.reminderClosing = True
        
    def onClose(self, event):
        # @@@BJS For now, treat "close" as "dismiss all"
        listCtrl = self.reminderControls['list']
        if listCtrl.GetItemCount() > 0:
            self.onDismiss(event)
        
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
    
    def UpdateList (self, reminders):
        """ 
        Update our list of reminders, and return the time we next want to fire.
        If we've still got reminders displayed, this'll be a minute from now, so we can 
        update their "when" column
        """

        # Don't do anything if we're responding to an update after our widget's been destroyed
        if self.reminderClosing:
            return (None, False)
        
        selectedReminders = list(self.getListItems(True))
        listCtrl = self.reminderControls['list']
        listCtrl.DeleteAllItems()
        self.remindersInList = {}
        nextReminder = None
        now = datetime.now()
        for reminder in reminders:
            if reminder.reminderTime < datetime.now():
                # Another pending reminder add it to the list.
                index = listCtrl.InsertStringItem(sys.maxint, reminder.displayName)
                self.remindersInList[index] = reminder

                # Make a relative expression of its time ("3 minutes from now")
                deltaMessage = self.RelativeDateTimeMessage(now - reminder.startTime)
                listCtrl.SetStringItem(index, 1, deltaMessage)
                
                # Select it if it was selected before
                try:
                    selectedReminders.index(reminder)
                except ValueError:
                    pass
                else:
                    listCtrl.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            else:
                # This reminder is still in the future.
                nextReminder = reminder
                break

        self.UpdateControlEnabling()
                
        # When do we want to be called again?
        # If we have anything in the list, call us in a minute so we can update
        # the event times; otherwise, update us at the first future reminder time;
        # otherwise, no reminder needed.
        closeIt = listCtrl.GetItemCount() == 0
        if not closeIt:
            now = datetime.now()
            nextReminderTime = now + timedelta(seconds=(60-now.second))
        elif nextReminder is not None:
            nextReminderTime = reminder.reminderTime
        else:
            nextReminderTime = None
        return (nextReminderTime, closeIt)
    
    def RelativeDateTimeMessage(self, delta):
        deltaMinutes = delta.minutes
        if 1 > deltaMinutes >= 0:
            return _("Now")
        
        absDeltaMinutes = abs(deltaMinutes)
        if (absDeltaMinutes >= 2880): # Use "days" only if it's more than two
            format = _("%d day%s %s")
            scale = 1440
        elif (absDeltaMinutes >= 120): # Use "hours" only if it's more than two
            format = _("%d hour%s %s")
            scale = 60
        else:
            format = _("%d minute%s %s")
            scale = 1
        
        value = round((absDeltaMinutes / scale) + 0.49999)
        return format % (value, value != 1 and "s" or "", absDeltaMinutes == deltaMinutes and _("ago") or _("from now"))

    def onDismiss(self, event):
        """ 
        Dismiss reminders, either limited to the selection, or not: the event
        can come from the dismiss or dismissAll buttons, or from the window's close box.
        """
        dismissSelection = event.GetEventObject() is self.reminderControls['dismiss']
        for reminder in self.getListItems(dismissSelection):
            del reminder.reminderTime
        wx.GetApp().repository.view.commit()

    def onSnooze(self, event):
        """ Snooze the selected reminders for five minutes """
        for reminder in self.getListItems(True):
            reminder.reminderTime = datetime.now() + timedelta(minutes=5)
        wx.GetApp().repository.view.commit()
    
    def getListItems(self, selectedOnly):
        """ Provide iteration over ListCtrl items """
        listCtrl = self.reminderControls['list']
        for index in range(listCtrl.GetItemCount()):
            if not selectedOnly or listCtrl.GetItemState(index, wx.LIST_STATE_SELECTED):
                yield self.remindersInList[index]
       
