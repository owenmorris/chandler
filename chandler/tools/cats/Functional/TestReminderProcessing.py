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
    
# Under normal circumstances, we'll create events to fire very
# shortly, so the tests aren't slowed much by waiting. (at least 2!)
# If I'm debugging, set up events farther in the future
nearFutureSeconds=2
#nearFutureSeconds=120

class TestReminderProcessing(ChandlerTestCase):

    if False:
        # Really fail
        def failif(self, x, msg):
            if x:
                raise AssertionError(msg)
        def failunless(self, x, msg):
            if not x:
                raise AssertionError(msg)
        def failunlessequal(self, a, b, msg):
            if not a == b:
                raise AssertionError("%s: %r != %r" % (msg, a, b))
        def failifequal(self, a, b, msg):
            if a == b:
                raise AssertionError("%s: %r == %r" % (msg, a, b))
    else:
        # Just log CRITICAL warnings
        def failif(self, x, msg):
            if x:
                logger.critical("%s...\n%s", msg, getstack())
        def failunless(self, x, msg):
            if not x:
                logger.critical("%s...\n%s", msg, getstack())
        def failunlessequal(self, a, b, msg):
            if not a == b:
                logger.critical("%s: %r != %r...\n%s", msg, a, b, getstack())
        def failifequal(self, a, b, msg):
            if a == b:
                logger.critical("%s: %r == %r...\n%s", msg, a, b, getstack())

    def _checkRemindersOn(self, anItem, userTime=None, userExpired=False,
                          triageStatusTime=None, snoozeTime=None,
                          triageStatus=None):
        """ 
        Verify that these are the only reminders on this remindable. userTime
        can be datetime or timedelta, or None; triageStatusTime and snoozeTime
        must be datetime or None.
        """
        logger.critical("Checking reminders on %s at %s", anItem.displayName,
                        pim.EventStamp(anItem).startTime)
        
        remindable = pim.Remindable(anItem)
        
        # Make sure we have 0 or 1 user reminders, on the right reflist.
        (refList, otherList, msg, otherMsg) = userExpired \
            and (remindable.expiredReminders, remindable.reminders, "Wrong expired count", "Wrong unexpired count") \
            or (remindable.reminders, remindable.expiredReminders, "Wrong unexpired count", "Wrong expired count")
        self.failunlessequal(len([r for r in refList if r.userCreated]), 
                             userTime is not None and 1 or 0, msg)
        self.failunlessequal([r for r in otherList if r.userCreated], [],
                             otherMsg)

        # If we have a user reminder, make sure it has the right time
        if isinstance(userTime, timedelta):
            self.failunlessequal(remindable.userReminderInterval, userTime,
                                 "Wrong user reminder interval")
        elif isinstance(userTime, datetime):
            self.failunlessequal(remindable.userReminderTime, userTime,
                                 "Wrong user reminder time")
                
        # Make sure we have the right number of triageStatus reminders (0 or 1)
        existingTS = [ r for r in remindable.reminders 
                       if not r.promptUser and not r.userCreated ]
        if triageStatusTime is None:
            self.failunlessequal(existingTS, [], "Shouldn't have triageStatus reminder")
        else:
            self.failif(len(existingTS) != 1 or 
                        existingTS[0].absoluteTime != triageStatusTime,
                        "Wrong triageStatus reminder")
            
        # Make sure we have the right number of snooze reminders (0 or 1)
        existingSnooze = [ r for r in remindable.reminders 
                           if r.promptUser and not r.userCreated ]
        if snoozeTime is None:
            self.failunlessequal(existingSnooze, [],
                                 "Shouldn't have snooze reminder")
        else:
            self.failif(len(existingSnooze) != 1 or 
                        existingSnooze[0].absoluteTime != snoozeTime,
                        "Wrong snooze reminder")
            
        # Make sure the item's triage status is what we expect
        if triageStatus is not None: # if not specified, we won't check it.
            self.failunlessequal(anItem.triageStatus, triageStatus,
                                 "Wrong triageStatus value")
            

    def _makeEvent(self, displayName, startTime):
        note = pim.Note(itsView=self.app_ns.itsView,
                     displayName=displayName,
                     triageStatus=pim.TriageEnum.later)
        self.collection.item.add(note)
        evt = pim.EventStamp(note)
        evt.add()
        evt.allDay = False
        evt.anyTime = False
        evt.startTime = startTime
        return note

    def _makeRecur(self, anEvent, now):
        """ Make this event recur, and return the next occurrence """
        rule = pim.calendar.Recurrence.RecurrenceRule(None, itsView=anEvent.itsView) # 'weekly' by default
        rruleset = pim.calendar.Recurrence.RecurrenceRuleSet(None, itsView=anEvent.itsView)
        rruleset.addRule(rule)
        evtStamp = pim.EventStamp(anEvent)
        evtStamp.rruleset = rruleset
        return evtStamp.getNextOccurrence(after=now).itsItem
        

    def startTest(self):
        view = QAUITestAppLib.UITestView(self.logger)
        view.SwitchToAllView()
    
        repoView = self.app_ns.itsView

        reminderDialog = wx.FindWindowByName(u'ReminderDialog')
        if reminderDialog is not None:
            self.logger.endAction(False, "Reminder dialog presented too soon?!")

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
        pim.Remindable(simpleEvent).userReminderInterval = nearFutureReminderDelta
        self._checkRemindersOn(simpleEvent, userTime=nearFutureReminderDelta,
                               userExpired=False, triageStatusTime=nearFuture,
                               triageStatus=pim.TriageEnum.later)

        # A recurring event that hasn't started yet. We start with
        # an event with an absolute reminder just before its startTime.
        futureRecurrerNormal = self._makeEvent("Recurrer: Future", nearFuture)
        pim.Remindable(futureRecurrerNormal).userReminderTime = nearFutureReminder
        self._checkRemindersOn(futureRecurrerNormal, userTime=nearFutureReminder,
                               userExpired=False, triageStatusTime=nearFuture)
        # Making it recur should: convert the absolute reminder to a relative 
        # one, leaving the relative reminder on the master's 'exipred' list
        # but pending on the first occurrence. It should also get rid of the
        # triageStatus reminder.
        nextOccurrence = self._makeRecur(futureRecurrerNormal, testTime)
        self._checkRemindersOn(futureRecurrerNormal, userTime=nearFutureReminderDelta,
                               userExpired=True, triageStatusTime=None)
        self._checkRemindersOn(nextOccurrence, userTime=nearFutureReminderDelta, 
                               userExpired=False, triageStatusTime=None)

        # A recurring event that started in the past, so the second occurrence
        # is in the near future
        pastTime = testTime - (timedelta(days=7) - nearFutureDelta)
        pastRecurrerNormal = self._makeEvent("Recurrer: Past", pastTime)
        pim.Remindable(pastRecurrerNormal).userReminderInterval = timedelta(0)
        self._checkRemindersOn(pastRecurrerNormal, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
        secondOccurrence = self._makeRecur(pastRecurrerNormal, testTime)
        firstOccurrence = pim.EventStamp(pastRecurrerNormal).getFirstOccurrence().itsItem
        self.failunless(pim.EventStamp(firstOccurrence).getNextOccurrence().itsItem \
                        is secondOccurrence, 
                        "2nd occurrence isn't the one after first")
        self._checkRemindersOn(firstOccurrence, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
        self._checkRemindersOn(secondOccurrence, userTime=timedelta(0), 
                               userExpired=False, triageStatusTime=None)

        # Sleep until after the events' start time, then fire all the collection 
        # notifications
        while True:
            sleepDelta = (nearFuture + timedelta(seconds=1)) \
                         - datetime.now(tz=ICUtzinfo.default)
            sleepDeltaSeconds = (sleepDelta.days * 86400) + sleepDelta.seconds
            if sleepDeltaSeconds < 0:
                break
            # If we're not there yet, sleep at least a second more.
            sleepDeltaSeconds = sleepDeltaSeconds >= 1 and sleepDeltaSeconds or 1
            logger.critical("Sleeping %d seconds", sleepDeltaSeconds)
            time.sleep(sleepDeltaSeconds)
            repoView.dispatchNotifications()
            scripting.User.idle()
        
        # Make sure the reminder alert popped up
        logger.critical("Done waiting - looking for reminder dialog")
        reminderDialog = wx.FindWindowByName(u'ReminderDialog')
        if reminderDialog is None:
            self.logger.endAction(False, "Didn't see the reminder dialog")

        # Dismiss reminders until the box goes away
        logger.critical("Dismissing reminders")
        timeout = datetime.now(tz=ICUtzinfo.default) + timedelta(seconds=2)
        while datetime.now(tz=ICUtzinfo.default) < timeout:
            reminderDialog = wx.FindWindowByName(u'ReminderDialog')
            if reminderDialog is None:
                break

            scripting.User.emulate_click(reminderDialog.reminderControls['dismiss'])
            repoView.dispatchNotifications()
            scripting.User.idle()
                    
        if reminderDialog is not None:
            self.logger.endAction(False, "Didn't dismiss all reminders")

        # Check each reminder
        logger.critical("Checking reminders, post-dismissal")
        self._checkRemindersOn(simpleEvent, userTime=nearFutureReminderDelta,
                               userExpired=True, triageStatusTime=None,
                               triageStatus=pim.TriageEnum.now)
        self._checkRemindersOn(firstOccurrence, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
        self._checkRemindersOn(secondOccurrence, userTime=timedelta(0), 
                               userExpired=True, triageStatusTime=None)
        thirdOccurrence = pim.EventStamp(secondOccurrence).getNextOccurrence().itsItem
        self._checkRemindersOn(thirdOccurrence, userTime=timedelta(0),
                               userExpired=False, triageStatusTime=None)
