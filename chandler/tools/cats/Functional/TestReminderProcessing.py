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

import time
from datetime import datetime, timedelta
import wx
from PyICU import ICUtzinfo
from application import schema
import osaf.framework.scripting as scripting
import osaf.pim as pim
from i18n.tests import uw
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import logging, traceback

logger = logging.getLogger(__name__)
def getstack():
    stack = traceback.extract_stack(limit=5)[:-2]
    return "".join(traceback.format_list(stack))
    
# Under normal circumstances, we'll create events to fire
# shortly, so the tests aren't slowed much by waiting.
# (Note: this used to be 3 seconds, which failed on slow machines or when
# indexing or other background processing happened to fire after we started
# but before we got to the 'waiting' phase of the test)
nearFutureSeconds=15

# If I'm debugging, set up events farther in the future
#nearFutureSeconds=120

# While we're debugging this test, I set reallyFail to False so failures will
# just get logged.
reallyFail = True

class TestReminderProcessing(ChandlerTestCase):

    def failif(self, x, msg):
        if x:
            logger.critical("%s...\n%s", msg, getstack())
            if reallyFail:
                raise AssertionError(msg)                    
    def failunless(self, x, msg):
        if not x:
            logger.critical("%s...\n%s", msg, getstack())
            if reallyFail:
                raise AssertionError(msg)                    
    def failunlessequal(self, a, b, msg):
        if not a == b:
            logger.critical("%s: %r != %r...\n%s", msg, a, b, getstack())
            if reallyFail: 
                raise AssertionError("%s: %r != %r" % (msg, a, b))
    def failifequal(self, a, b, msg):
        if a == b:
            logger.critical("%s: %r == %r...\n%s", msg, a, b, getstack())
            if reallyFail: 
                raise AssertionError("%s: %r == %r" % (msg, a, b))

    def _checkRemindersOn(self, anEvent, userTime=None, userExpired=False,
                          triageStatusTime=None, snoozeTime=None,
                          triageStatus=None):
        """ 
        Verify that these are the only reminders on this remindable. userTime
        can be datetime or timedelta, or None; triageStatusTime and snoozeTime
        must be datetime or None.
        """
        logger.critical("Checking reminders on %s at %s", anEvent,
                        anEvent.startTime)
        
        remindable = anEvent.itsItem
        
        # Make sure we have exactly 1 user reminder.
        userReminders = [r for r in remindable.reminders if r.userCreated]
        self.failunlessequal(len(userReminders), 1, "Wrong number of reminders")
        
        # ... and make sure it has expired if the user expired it.
        if userExpired:
            self.failunlessequal(userReminders[0].nextPoll,
                                 userReminders[0].farFuture, 
                                 "Reminder hasn't expired")
            self.failunlessequal(len(userReminders[0].pendingEntries or []), 0, 
                                 "Reminder has visible items")
        else:
            pass
        
        
        # If we have a user reminder, make sure it has the right time
        if isinstance(userTime, timedelta):
            self.failunlessequal(
                pim.EventStamp(remindable).userReminderInterval, userTime,
                "Wrong user reminder interval")
        elif isinstance(userTime, datetime):
            self.failunlessequal(remindable.userReminderTime, userTime,
                                 "Wrong user reminder time")
                
        # Make sure we have the right number of triageStatus reminders
        existingTS = [ r for r in remindable.reminders 
                       if not r.promptUser and not r.userCreated ]
        if triageStatusTime is None:
            self.failunlessequal(existingTS, [], "Shouldn't have triageStatus reminder")
        elif False: # @@@ [grant] Re-enable this test!
            self.failif(len(existingTS) != 1 or 
                        existingTS[0].absoluteTime != triageStatusTime,
                        "Wrong triageStatus reminder")
            
        # Make sure we have the right number of snooze reminders (0 or 1)
        existingSnooze = []
        for r in remindable.reminders:
            existingSnooze.extend(e for e in r.pendingEntries or []
                                  if e.snoozed)
        if snoozeTime is None:
            self.failunlessequal(existingSnooze, [],
                                 "Shouldn't have snooze reminder")
        else:
            self.failif(len(existingSnooze) != 1 or 
                        existingSnooze[0].when != snoozeTime,
                        "Wrong snooze reminder")
            
        # Make sure the item's triage status is what we expect
        # @@@ [grant] Re-enable this test (remove the or False below) !
        if triageStatus is not None or False: # if not specified, we won't check it.
            self.failunlessequal(anEvent.itsItem.triageStatus, triageStatus,
                                 "Wrong triageStatus value")
            

    def _makeEvent(self, displayName, startTime):
        note = pim.Note(itsView=self.app_ns.itsView)
        note.displayName = displayName
        note.setTriageStatus(pim.TriageEnum.later)
        
        self.collection.item.add(note)
        evt = pim.EventStamp(note)
        evt.add()
        evt.allDay = False
        evt.anyTime = False
        evt.startTime = startTime
        return evt

    def _makeRecur(self, anEvent, now):
        """ Make this event recur, and return the next occurrence """
        view = anEvent.itsItem.itsView
        rule = pim.calendar.Recurrence.RecurrenceRule(None, itsView=view) # 'weekly' by default
        rruleset = pim.calendar.Recurrence.RecurrenceRuleSet(None, itsView=view)
        rruleset.addRule(rule)
        anEvent.rruleset = rruleset
        return anEvent.getNextOccurrence(after=now)
        

    def startTest(self):
        view = QAUITestAppLib.UITestView(self.logger)
        view.SwitchToAllView()
        
        self.logger.startAction("Testing reminder processing")
    
        repoView = self.app_ns.itsView

        reminderDialog = wx.FindWindowByName(u'ReminderDialog')
        if reminderDialog is not None:
            self.logger.endAction(False, "Reminder dialog presented too soon?!")
            return

        self.collection = QAUITestAppLib.UITestItem("Collection", self.logger)
        colName = uw("TestReminderProcessing")
        self.collection.SetDisplayName(colName)
        self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, colName)


        # We'll create a few items with interesting times coming up
        testTime = datetime.now(tz=ICUtzinfo.default).replace(microsecond=0) \
                   + timedelta(seconds=1)
        nearFutureDelta = timedelta(seconds=nearFutureSeconds)
        nearFutureReminderDelta = timedelta(seconds=nearFutureSeconds/-2)
        nearFuture = testTime + nearFutureDelta
        nearFutureReminder = nearFuture + nearFutureReminderDelta
        logger.critical("testTime=%s, nearFutureReminder=%s, nearFuture=%s", 
                        testTime, nearFutureReminder, nearFuture)

        # An ordinary event with relative and triageStatus reminders
        simpleEvent = self._makeEvent("Simple Event", nearFuture)
        simpleEvent.userReminderInterval = nearFutureReminderDelta
        self._checkRemindersOn(simpleEvent, userTime=nearFutureReminderDelta,
                               userExpired=False, triageStatusTime=nearFuture,
                               triageStatus=pim.TriageEnum.later)

        # A recurring event that hasn't started yet. We start with
        # an event with an absolute reminder just before its startTime.
        futureRecurrerNormal = self._makeEvent("Recurrer: Future", nearFuture)
        futureRecurrerNormal.itsItem.userReminderTime = nearFutureReminder
        self._checkRemindersOn(futureRecurrerNormal, userTime=nearFutureReminder,
                               userExpired=False, triageStatusTime=nearFuture)
        
        # Making it recur should: convert the absolute reminder to a relative 
        # one, leaving the relative reminder on the master's 'expired' list
        # but pending on the first occurrence. It should also get rid of the
        # triageStatus reminder.
        nextOccurrence = self._makeRecur(futureRecurrerNormal, testTime)
        
        # Let the app pick up any reminder firing changes
        scripting.User.idle()
        # Individual occurrences don't get their own reminders (unless you
        # make a change).
        self.failunless(futureRecurrerNormal.itsItem.reminders is
                        nextOccurrence.itsItem.reminders,
                        "occurrence shouldn't have its own reminders reflist")
        
        self._checkRemindersOn(futureRecurrerNormal, userTime=nearFutureReminderDelta,
                               userExpired=False, triageStatusTime=nearFuture)

        # A recurring event that started in the past, so the second occurrence
        # is in the near future
        pastTime = testTime - (timedelta(days=7) - nearFutureDelta)
        pastRecurrerNormal = self._makeEvent("Recurrer: Past", pastTime)
        pastRecurrerNormal.userReminderInterval = timedelta(0)
        
        scripting.User.idle()
        self._checkRemindersOn(pastRecurrerNormal, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
                               
        secondOccurrence = self._makeRecur(pastRecurrerNormal, testTime)
        firstOccurrence = pastRecurrerNormal.getFirstOccurrence()
        self.failunlessequal(firstOccurrence.getNextOccurrence(),
                         secondOccurrence, 
                        "2nd occurrence isn't the one after first")
        self._checkRemindersOn(firstOccurrence, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
        self._checkRemindersOn(secondOccurrence, userTime=timedelta(0), 
                               userExpired=False, triageStatusTime=None)

        # Iterate until all the processing is complete, or we hit our timeout
        timeOut = nearFuture + timedelta(seconds=nearFutureSeconds*2)
        state = "Waiting for reminder dialog"
        # @@@ [grant] Is this actually right ... ?
        allFutureReminders = schema.ns('osaf.pim',
                                       repoView).allFutureReminders
        
        testReminderItems = list(event.itsItem for event in
            (simpleEvent, futureRecurrerNormal, nextOccurrence,
             pastRecurrerNormal, firstOccurrence, 
             secondOccurrence))
        logger.critical(state)
        
        clicked = False
        
        
        while True:
            now = datetime.now(tz=ICUtzinfo.default)

            repoView.dispatchQueuedNotifications()
            scripting.User.idle()

            
            if now > timeOut:
                self.logger.endAction(False, "Reminder processing didn't complete (%s)" % state)
                return

            reminderDialog = wx.FindWindowByName(u'ReminderDialog')
            
            if state == "Waiting for reminder dialog":
                if reminderDialog is not None:
                    state = "Dismissing reminders"
                    logger.critical(state)
                continue

            if reminderDialog is not None:
                # The reminder dialog is up. Hit its dismiss button.
                dismissWidget = reminderDialog.reminderControls['dismiss']
                self.failunless(dismissWidget.IsEnabled(), "Reminder dialog up, but dismiss button disabled? That's just wrong.")
                scripting.User.emulate_click(dismissWidget)
                clicked = True
                continue
            
            # The reminder dialog isn't up. Skip out when none of our items have
            # pending reminders
            if clicked and now > nearFuture + timedelta(seconds=1):
                foundPending = False
                for pending in pim.PendingReminderEntry.getKind(repoView).iterItems():
                    if pending.item in testReminderItems:
                        break
                else:
                    state = "Reminders done"
                    logger.critical(state)
                    break
        
        self.failunlessequal(state, "Reminders done", "Reminder-processing timeout")

        # Check each reminder
        logger.critical("Checking reminders, post-dismissal")
        self._checkRemindersOn(simpleEvent, userTime=nearFutureReminderDelta,
                               userExpired=True, triageStatusTime=None,
                               triageStatus=pim.TriageEnum.now)
        self._checkRemindersOn(firstOccurrence, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
        self._checkRemindersOn(secondOccurrence, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
        thirdOccurrence = secondOccurrence.getNextOccurrence()
        self._checkRemindersOn(thirdOccurrence, userTime=timedelta(0),
                               userExpired=False, triageStatusTime=None)
        self.logger.endAction(True)
