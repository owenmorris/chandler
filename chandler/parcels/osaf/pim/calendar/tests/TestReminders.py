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


import repository.tests.RepositoryTestCase as RepositoryTestCase
import unittest
from osaf.pim import *
from osaf.pim.calendar.Recurrence import *
import osaf.pim.tests.TestDomainModel as TestDomainModel
import repository.item
from datetime import datetime, timedelta, time

class AbsoluteReminderTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(AbsoluteReminderTestCase, self).setUp()
        self.reminderTime = datetime(2007,5,11,13,
                                     tzinfo=self.view.tzinfo.default)
        self.item = ContentItem(itsView=self.view)
        self.reminder = Reminder(itsView=self.view,
                            absoluteTime=self.reminderTime)


    def testInitReminder(self):
        
        self.failUnless(self.reminder.nextPoll is None)
        self.failUnlessEqual(self.reminder.absoluteTime, self.reminderTime)
        self.failIf(self.reminder.pendingEntries)
        
    def testUpdatePending(self):
        self.reminder.reminderItem = self.item

        self.reminder.updatePending(self.reminderTime)
        self.failUnlessEqual(self.reminder.nextPoll, Reminder.farFuture)
        self.failUnlessEqual(1, len(self.reminder.pendingEntries))
        
        pendingEntry = self.reminder.pendingEntries.first()
        self.failUnlessEqual(pendingEntry.when, self.reminderTime)
        self.failUnlessEqual(pendingEntry.item, self.reminder.reminderItem)
        self.failUnlessEqual(pendingEntry.reminder, self.reminder)

    def testDismissReminder(self):
        self.reminder.reminderItem = self.item
        self.reminder.updatePending(self.reminderTime - timedelta(hours=1))
        self.reminder.updatePending(self.reminder.nextPoll + timedelta(hours=2))
        
        self.reminder.dismissItem(self.item)
        
        self.failUnlessEqual(self.reminder.nextPoll, Reminder.farFuture)
        self.failUnlessEqual([], list(self.reminder.pendingEntries))


    def testSnoozeReminder(self):
        self.reminder.reminderItem = self.item
        self.reminder.updatePending(self.reminderTime)
        
        self.reminder.snoozeItem(self.item, timedelta(minutes=10))
        
        self.failUnless(self.reminder.nextPoll <=
                        datetime.now(self.view.tzinfo.default) + timedelta(minutes=10))
        self.failUnlessEqual(1, len(self.reminder.pendingEntries))
        
    def testDeleteItem(self):
        self.reminder.reminderItem = self.item
        self.reminder.updatePending(self.reminderTime)
        
        pending = list(self.reminder.pendingEntries)
        
        self.item.delete(recursive=True)

        self.failUnless(isDead(self.item))
        self.failUnless(isDead(self.reminder))
        for entry in pending:
            self.failUnless(isDead(entry))

    def testDeleteReminder(self):
        self.reminder.reminderItem = self.item
        self.reminder.updatePending(self.reminderTime)
        
        pending = list(self.reminder.pendingEntries)
        
        self.reminder.delete(recursive=True)
        self.failIf(isDead(self.item))
        self.failUnless(isDead(self.reminder))
        for entry in pending:
            self.failUnless(isDead(entry))

class RelativeReminderTestCase(TestDomainModel.DomainModelTestCase):

    def setUp(self):
        super(RelativeReminderTestCase, self).setUp()
        self.event = CalendarEvent(itsView=self.view,
                startTime=datetime(2004,8,1,8,tzinfo=self.view.tzinfo.default),
                duration=timedelta(minutes=45), anyTime=False,
                summary=u"Meet with Very Important Person")
        self.event.itsItem.setTriageStatus(TriageEnum.later)

        self.reminder = RelativeReminder(itsView=self.view,
                            delta=-timedelta(minutes=20))


    def testInitReminder(self):
        
        self.failUnless(self.reminder.nextPoll is None)
        self.failUnlessEqual(self.reminder.absoluteTime, None)
        self.failIf(self.reminder.pendingEntries)
        
    def testUpdatePastPending(self):
        self.reminder.reminderItem = self.event.itsItem

        # We have an event whose reminder is in the past ...
        self.reminder.updatePending(self.event.startTime)
        
        # Make sure it has been shuffled off to the far future ...
        self.failUnlessEqual(self.reminder.nextPoll, Reminder.farFuture)
        # ... with no pending entries
        self.failIf(self.reminder.pendingEntries)
        
    def testUpdatePending(self):
        self.reminder.reminderItem = self.event.itsItem
        
        pollTime = self.reminder._getReminderTime(self.event.itsItem)
        self.reminder.updatePending(pollTime - timedelta(seconds=10))

        self.failUnlessEqual(self.reminder.nextPoll, pollTime)
        # ... with one pending entries
        self.failUnlessEqual(0, len(self.reminder.pendingEntries))
        
        self.reminder.updatePending(pollTime)
        # Make sure it has been shuffled off to the far future ...
        self.failUnlessEqual(self.reminder.nextPoll, Reminder.farFuture)
        self.failUnlessEqual(1, len(self.reminder.pendingEntries))

        pending = self.reminder.pendingEntries.first()
        self.failUnlessEqual(pending.item, self.event.itsItem)
        self.failUnlessEqual(pending.when,
                             self.reminder._getReminderTime(self.event.itsItem))
        self.failUnlessEqual(pending.reminder, self.reminder)
        self.failUnlessEqual(pending.item.triageStatus, TriageEnum.now)
        
    
    def testDismissReminder(self):
        self.reminder.reminderItem = self.event.itsItem

        pollTime = self.reminder._getReminderTime(self.event.itsItem)
        self.reminder.updatePending(pollTime)
        
        self.reminder.dismissItem(self.event.itsItem)
        self.reminder.updatePending(pollTime)
        
        self.failUnlessEqual(self.reminder.nextPoll, Reminder.farFuture)
        self.failUnlessEqual([], list(self.reminder.pendingEntries))

    def testSnoozeReminder(self):
        self.reminder.reminderItem = self.event.itsItem
        pollTime = self.reminder._getReminderTime(self.event.itsItem)
        self.reminder.updatePending(pollTime)
        
        self.reminder.snoozeItem(self.event.itsItem, timedelta(minutes=15))
        
        self.failUnless(self.reminder.nextPoll <=
                        datetime.now(self.view.tzinfo.default) + timedelta(minutes=15))
        self.failUnlessEqual(1, len(self.reminder.pendingEntries))
        
    def testChangeStartTime(self):
        self.reminder.reminderItem = self.event.itsItem
        
        self.event.startTime += timedelta(hours=1)
        pollTime = self.event.startTime + self.reminder.delta
        
        self.reminder.updatePending(pollTime)
        self.failUnlessEqual(1, len(self.reminder.pendingEntries))
        pending = self.reminder.pendingEntries.first()
        self.failUnlessEqual(pending.when, pollTime)
        
        self.failUnlessEqual(self.reminder.nextPoll, Reminder.farFuture)

    def testChangePendingStartTime(self):
        self.reminder.reminderItem = self.event.itsItem
        
        pollTime = self.event.startTime + self.reminder.delta
        
        self.reminder.updatePending(pollTime)

        self.event.startTime += timedelta(hours=1)
        
        # Make sure that we're no longer pending if the
        # event's startTime changes
        self.failUnlessEqual(0, len(self.reminder.pendingEntries))
        
    def testUnstamp(self):
        item = self.event.itsItem

        self.reminder.reminderItem = item
        
        self.event.remove()
        
        self.failUnless(isDead(self.reminder))
        self.failIf(item.reminders)
        
    def testAddRecurrence(self):
        ruleItem = RecurrenceRule(None, itsView=self.view, freq='daily')
        rruleset = RecurrenceRuleSet(None, itsView=self.view,
                                          rrules=[ruleItem])
                                          
        self.reminderTime = datetime(2004,11,1,12,22,3,tzinfo=self.view.tzinfo.default)
        self.reminder = Reminder(itsView=self.view,
                                 absoluteTime=self.reminderTime)

        self.event.itsItem.reminders = [self.reminder]
        absoluteTime = self.event.itsItem.userReminderTime
        
        self.failIf(absoluteTime is None)
        
        # Now, change the rruleset ...
        self.event.changeThisAndFuture(EventStamp.rruleset.name, rruleset)
        
        # That should delete the reminder ...
        self.failUnless(isDead(self.reminder))
        
        # ... and leave a relative reminder in its place
        self.failUnlessEqual(absoluteTime,
                             self.event.startTime +
                             self.event.userReminderInterval)

        
        
class RecurringReminderTestCase(TestDomainModel.DomainModelTestCase):
    """Test behaviour of reminders with recurring events"""
    
    # @@@ [grant] Need to test anyTime
    def setUp(self):
        super(RecurringReminderTestCase, self).setUp()
        self.event = CalendarEvent(itsView=self.view,
                startTime=datetime(2007,1,4,12,5,tzinfo=self.view.tzinfo.default),
                duration=timedelta(minutes=55),
                anyTime=False,
                summary=u"Meet with Highly Unusual Person")

        self.reminder = RelativeReminder(itsView=self.view,
                            delta=-timedelta(minutes=20))
                            
        ruleItem = RecurrenceRule(None, itsView=self.view, freq='daily')
        ruleItem.until = datetime(2007,1,23,tzinfo=self.view.tzinfo.default)
        ruleItem.untilIsDate = False
        self.event.rruleset = RecurrenceRuleSet(None, itsView=self.view,
                                rrules=[ruleItem])


    def testInitReminder(self):
        
        self.failUnless(self.reminder.nextPoll is None)
        self.failUnlessEqual(self.reminder.absoluteTime, None)
        self.failIf(self.reminder.pendingEntries)

    def testUpdatePending(self):
        self.reminder.reminderItem = self.event.itsItem

        pollTime = self.event.startTime + self.reminder.delta

        self.reminder.updatePending(pollTime - timedelta(minutes=5))
        
        # Make sure it has been shuffled off to the first event's reminder time ...
        self.failUnlessEqual(pollTime, self.reminder.nextPoll)
        # ... with no pending entries
        self.failUnlessEqual(0, len(self.reminder.pendingEntries))
        
        # Now, try to get the first occurrence ...
        self.reminder.updatePending(pollTime)
        # ... make sure its nextPoll matches what we expect
        pollTime += timedelta(days=1)
        self.failUnlessEqual(self.reminder.nextPoll, pollTime)
        # ... and that we have one pending entry
        self.failUnlessEqual(1, len(self.reminder.pendingEntries))
        
        # Make sure that entry matches the event's first occurrence
        pending = self.reminder.pendingEntries.first()
        firstOccurrence = self.event.getFirstOccurrence()
        self.failUnlessEqual(pending.item, firstOccurrence.itsItem)
        self.failUnlessEqual(pending.when,
                             self.reminder._getReminderTime(self.event.itsItem))
        self.failUnlessEqual(pending.reminder, self.reminder)
        
        pollTime = self.reminder.nextPoll
        self.reminder.updatePending(pollTime)
        self.failUnlessEqual(2, len(self.reminder.pendingEntries))

    def testUpdatePendingFuture(self):
        self.reminder.reminderItem = self.event.itsItem

        # Let's leap 10 days into the future ....
        pollTime = self.event.startTime + timedelta(days=10) + self.reminder.delta

        # Tell the reminder to update just before a reminder is due to fire
        self.reminder.updatePending(pollTime - timedelta(minutes=5))
        # ... and make sure its nextPoll is set correctly, ...
        self.failUnlessEqual(self.reminder.nextPoll, pollTime)
        # ... with no pending reminders
        self.failIf(self.reminder.pendingEntries)
        
        # Now, update to its nextPoll
        self.reminder.updatePending(pollTime)
        self.failUnlessEqual(len(self.reminder.pendingEntries), 1)
        
        pendingEntry = self.reminder.pendingEntries.first()
        pendingEvent = EventStamp(pendingEntry.item)
        self.failUnless(has_stamp(pendingEvent, EventStamp))
        self.failUnlessEqual(pollTime - self.reminder.delta,
                             pendingEvent.startTime)

    def testMakeModification(self):
        self.reminder.reminderItem = self.event.itsItem

        # Make a THIS modification
        startTime = self.event.startTime + timedelta(days=4)
        occurrence = self.event.getNextOccurrence(after=startTime)
        
        occurrence.changeThis(EventStamp.startTime.name,
                              occurrence.startTime + timedelta(hours=2))
        
        # Check that it kepts the old copy of the reminder
        self.failUnless(self.event.itsItem.reminders is
                        occurrence.itsItem.reminders)

        self.failUnlessEqual(1, len(self.event.itsItem.reminders))
                
        self.failUnlessEqual(len(list(self.event.itsItem.reminders)), 1)
        modsReminder = self.event.itsItem.reminders.first()
        
        self.failUnlessEqual(modsReminder.delta, self.reminder.delta)
        
        # Make sure that the modification doesn't appear in the
        # pendingEntries of the master
        self.reminder.updatePending(startTime)
        self.failIf(self.reminder.pendingEntries)
        
        # Make sure the nextPoll for the reminder matches occurrence's
        # reminder time
        self.failUnlessEqual(self.reminder.nextPoll,
                             occurrence.startTime + self.reminder.delta)
                             
        # Now update again, and make sure we match the reminder time for
        # the following (non-modified) event.
        self.reminder.updatePending(self.reminder.nextPoll)
        self.failUnlessEqual(self.reminder.nextPoll,
                             startTime + self.reminder.delta + timedelta(days=1))
                             
    def testChangeThisReminderDelta(self):
        self.reminder.reminderItem = self.event.itsItem

        self.failUnlessEqual(self.event.userReminderInterval,
                             self.reminder.delta)

        # Make a THIS modification
        startTime = self.event.startTime
        occurrence = self.event.getNextOccurrence(after=startTime)
        
        occurrence.changeThis(EventStamp.userReminderInterval.name,
                              timedelta(minutes=-20))
        
        # Make sure the reminders reflist actually changed
        self.failIf(occurrence.itsItem.reminders is
                    self.event.itsItem.reminders)

        self.failUnlessEqual(occurrence.userReminderInterval,
                             timedelta(minutes=-20))
                    
        self.failUnlessEqual(self.event.userReminderInterval,
                             self.reminder.delta)
                             
        # Now, make sure our original reminder skips the modification
        # (which is taken care of by the THIS change)
        self.reminder.updatePending(self.event.startTime + self.reminder.delta)
        self.failIf(self.reminder.pendingEntries)

    def testChangeThisAbsoluteReminderTime(self):
        self.reminder.reminderItem = self.event.itsItem

        # Make a THIS modification of userReminderTime
        startTime = self.event.startTime + timedelta(days=12)
        occurrence = self.event.getNextOccurrence(after=startTime)
        
        occurrence.changeThis(Remindable.userReminderTime.name,
                              occurrence.startTime + timedelta(hours=6))
        
        # Check that it got a new copy of the reminders reflist
        self.failIf(self.event.itsItem.reminders is
                    occurrence.itsItem.reminders)
        
        self.failUnlessEqual(occurrence.itsItem.getUserReminder().absoluteTime,
                             occurrence.startTime + timedelta(hours=6))
                             
        # Check that there are no non-user-created reminders in the list
        nonUserReminders = list(rem for rem in occurrence.itsItem.reminders if
                               not rem.userCreated or not rem.promptUser)
        self.failUnlessEqual(nonUserReminders, [])


    def testThisAndFutureModification(self):
        self.reminder.reminderItem = self.event.itsItem

        # Make a THISANDFUTURE modification
        startTime = self.event.startTime + timedelta(days=1)
        occurrence = self.event.getNextOccurrence(after=startTime)
        
        occurrence.changeThisAndFuture(EventStamp.summary.name, u"New Series")
        detachedMaster = occurrence.getFirstInRule()
        
        self.failUnless(detachedMaster.itsItem.reminders)
        
        for reminder in detachedMaster.itsItem.reminders:        
            self.failIf(reminder in self.event.itsItem.reminders)


    def testModifyPendingOccurrence(self):
        self.reminder.reminderItem = self.event.itsItem

        # Make a THIS modification
        startTime = self.event.startTime + timedelta(days=12)
        occurrence = self.event.getNextOccurrence(after=startTime)

        # Let's get 3 entries into the reminder's pendingEntries
        self.reminder.updatePending(startTime + self.reminder.delta)
        self.failUnlessEqual(len(self.reminder.pendingEntries), 1)
        self.reminder.updatePending(startTime + timedelta(days=2) +
                                    self.reminder.delta)
        self.failUnlessEqual(len(self.reminder.pendingEntries), 3)

        # Now, make a THIS change
        occurrence.changeThis(Note.displayName.name,
                              u'I am a diaper. Change me')
        
        # Check that THIS doesn't modify reminders at all
        self.failUnless(self.event.itsItem.reminders is
                        occurrence.itsItem.reminders)
        
    def testEnableTimeZones(self):
        self.event.startTime = self.event.startTime.replace(tzinfo=self.view.tzinfo.floating)
    
        # This is not so lovely....
        from osaf.pim.calendar.TimeZone import ontzchange
        self.view.tzinfo.ontzchange = ontzchange

        # Set up the reminder
        self.reminder.reminderItem = self.event.itsItem
        
        # Simulate setting up the reminder 5 minutes after an
        # occurrence
        pending = self.event.startTime + timedelta(days=4, minutes=5)
        self.reminder.updatePending(pending)
        
        # That should result in 0 pending reminders
        self.failIf(self.reminder.pendingEntries)

        # Now, enable timezones ...
        schema.ns("osaf.pim", self.view).TimezonePrefs.showUI = True
        
        # ... 'tick' the clock a second
        self.reminder.updatePending(pending + timedelta(seconds=1))
        
        # ... and make sure we still have no pending reminders
        self.failIf(self.reminder.pendingEntries)


    def testChangeAllStartTimes(self):
        # Set up the reminder
        self.reminder.reminderItem = self.event.itsItem
        
        # Simulate setting up the reminder 5 minutes after an
        # occurrence
        pending = self.event.startTime - timedelta(days=1, minutes=5)
        self.reminder.updatePending(pending)
        
        # That should result in 0 pending reminders
        self.failIf(self.reminder.pendingEntries)

        # Now, do an ALL change of startTime ...
        CHANGE_ALL(self.event).startTime -= timedelta(days=2)
        
        self.reminder.updatePending(pending + timedelta(seconds=1))
        self.failIf(self.reminder.pendingEntries)
                        
    def DISABLED_testChangeUserReminderTime(self):
        self.reminder.reminderItem = self.event.itsItem
        
        # Get an occurrence 
        startTime = self.event.startTime + timedelta(days=15)
        occurrence = self.event.getNextOccurrence(after=startTime)
        
        # Make a "custom" reminder
        reminderTime = startTime.replace(hour=17, minute=0, second=0,
                                         microsecond=0)
        occurrence.itsItem.userReminderTime = reminderTime
        
        # Check that that made a THIS modification
        self.failUnless(occurrence.modificationFor)
        self.failUnless(occurrence.itsItem.hasLocalAttributeValue(Remindable.reminders.name))
        self.failUnlessEqual(occurrence.itsItem.userReminderTime, reminderTime)
        self.failUnlessEqual(occurrence.itsItem.displayDate, reminderTime)
        self.failUnlessEqual(occurrence.itsItem.displayDateSource, 'reminder')


class ReminderCollectionsTestCase(TestDomainModel.DomainModelTestCase):
    # Test behaviour of the 'reminders' collections in osaf.pim
    def setUp(self):
        super(ReminderCollectionsTestCase, self).setUp()
        self.note = Note(itsView=self.view,
                displayName=u"I am so very notable")

        
        self.firstDate = datetime(2004, 11, 3, 9, 25, tzinfo=self.view.tzinfo.default)
        self.reminder = Reminder(itsView=self.view,
                                 absoluteTime=self.firstDate)
        self.reminder.reminderItem = self.note
        
        pimNs = schema.ns("osaf.pim", self.view)
        self.tsReminder = pimNs.triageStatusReminder
        
        self.unexpired = pimNs.allFutureReminders
        
    def testFireAndDismissReminder(self):
        self.failUnlessEqual(set(self.unexpired),
                             set([self.reminder, self.tsReminder]))
        self.reminder.updatePending(self.reminder.absoluteTime)
        self.failUnlessEqual(list(self.unexpired), [self.tsReminder])
        
        self.reminder.dismissItem(self.note)
        self.failUnlessEqual(list(self.unexpired), [self.tsReminder])

    def testPendingEntries(self):
        def getPending():
            kind = PendingReminderEntry.getKind(self.view)
            
            return list(kind.iterItems())
            
        self.failUnlessEqual(set(self.unexpired),
                             set([self.tsReminder, self.reminder]))
        self.failUnlessEqual([], getPending())
        self.reminder.updatePending(self.reminder.absoluteTime)
        self.failUnlessEqual([self.reminder.pendingEntries.first()],
                             getPending())
        
        self.reminder.dismissItem(self.note)
        self.failUnlessEqual(list(self.unexpired), [self.tsReminder])
        self.failUnlessEqual([], getPending())
        
class TriageStatusReminderTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(TriageStatusReminderTestCase, self).setUp()
        self.event = CalendarEvent(itsView=self.view,
                startTime=datetime(2005,11,4,16,tzinfo=self.view.tzinfo.default),
                duration=timedelta(minutes=60),
                anyTime=False,
                summary=u"Hour-long event")
        self.tsReminder = schema.ns("osaf.pim", self.view).triageStatusReminder

    def testTriageChange(self):
        # Let's imagine we have a change to triage of later 2 hours before
        # the event
        self.event.itsItem.setTriageStatus(TriageEnum.later, 
                                           when=self.event.startTime -
                                               timedelta(hours=2))
                                          
        reminders = list(self.event.itsItem.reminders)
        self.failUnlessEqual([], reminders)
        
        self.tsReminder.updatePending(self.event.startTime - timedelta(hours=1))
        self.failUnlessEqual(self.event.startTime, self.tsReminder.nextPoll)
        self.failIf(self.tsReminder.pendingEntries)
        
        self.tsReminder.updatePending(self.tsReminder.nextPoll)
        self.failUnlessEqual(self.event.itsItem.triageStatus, TriageEnum.now)
        # @@@ [grant] No way to get triageStatusChanged. Tsk.
        
        # TriageStatusReminders never die ... they just wait for new events
        self.failIf(isDead(self.tsReminder))

    def testPastNoTriageChange(self):
        self.event.itsItem.setTriageStatus(TriageEnum.done, 
                                           when=self.event.startTime +
                                               timedelta(days=2))
                                                 
        self.failUnlessEqual(list(self.event.itsItem.reminders), [])
        
        self.failIf(self.tsReminder.delta)

        self.tsReminder.updatePending(self.event.startTime + timedelta(days=3))
        
        self.failUnlessEqual(self.event.itsItem.triageStatus, TriageEnum.done)

    def testRecurring(self):
        self.event.itsItem.setTriageStatus(TriageEnum.later,
                                           when=self.event.startTime +
                                               timedelta(days=3))

        # Make our event recurring
        ruleItem = RecurrenceRule(None, itsView=self.view, freq='daily')
        ruleItem.until = datetime.combine(
                    self.event.startTime + timedelta(days=6),
                    time(0, tzinfo=self.view.tzinfo.default))
        ruleItem.untilIsDate = True
        self.event.rruleset = RecurrenceRuleSet(None, itsView=self.view,
                                rrules=[ruleItem])
                                
        reminders = list(self.event.itsItem.reminders)
        self.failUnlessEqual([], reminders)

        # Trigger a triage status change that starts with the 5th occurrence
        fifthStart = self.event.startTime + timedelta(days=4)
        # @@@ [grant] explain
        self.tsReminder.updatePending(fifthStart - timedelta(minutes=10))
        self.tsReminder.updatePending(fifthStart)
        fifth = self.event.getRecurrenceID(fifthStart)
        
        self.failUnless(fifth.modificationFor)
        self.failUnlessEqual(fifth.itsItem.triageStatus, TriageEnum.now)
        
        self.failUnlessEqual(self.event.getFirstOccurrence().itsItem.triageStatus,
                             TriageEnum.done)

        self.failIfEqual(self.event.getFirstOccurrence().itsItem.triageStatusChanged,
                         fifth.itsItem.triageStatusChanged)

        
        # The occurrence after fifth has always been in the past, and
        # updatePending, hasn't passed over it, so its triage status has stayed
        # done.
        self.failUnlessEqual(fifth.getNextOccurrence().itsItem.triageStatus,
                             TriageEnum.done)
        
        self.failIf(self.tsReminder.pendingEntries)
        
        # Expire all the pending entries ...
        self.tsReminder.updatePending(fifthStart + timedelta(days=7))
        
        # ... make sure the triage status got set to done
        event = fifth
        while event is not None:
            self.failUnlessEqual(event.itsItem.triageStatus, TriageEnum.done)
            event = event.getNextOccurrence()

        # ... and make sure the reminder got deleted
        self.failIf(isDead(self.tsReminder))

        
class ReminderTestCase(TestDomainModel.DomainModelTestCase):
    def testReminders(self):
        # Make an event in the past (so it won't have a startTime reminder)
        # and add an expired absolute reminder to it.
        pastTime = datetime(2005,3,8,12,00, tzinfo = self.view.tzinfo.default)
        anEvent = CalendarEvent("calendarEventItem", itsView=self.view,
                                startTime=pastTime,
                                duration=timedelta(hours=1),
                                allDay=False, anyTime=False)
        remindable = anEvent.itsItem
        
        absoluteReminderTime = datetime(2005,3,8,11,00, tzinfo=self.view.tzinfo.default)
        absoluteReminder = remindable.setUserReminderTime(absoluteReminderTime)
        
        # Make sure it got connected right: one expired absolute reminder.
        # Er, we're assuming now > 2005/03/08, of course :o
        for rem in remindable.reminders:
            rem.updatePending(datetime.now(self.view.tzinfo.default))
        self.failUnless(len(remindable.reminders), 1)
        self.failUnless(remindable.reminders.first() is absoluteReminder)

        self.failUnless(remindable.userReminderTime == absoluteReminderTime)
        self.failUnless(anEvent.userReminderInterval is None)
        self.failUnless(absoluteReminder.isExpired())

        self.failUnlessEqual(absoluteReminder.nextPoll, Reminder.farFuture)
        self.failIf(absoluteReminder.pendingEntries)
                
        # Replace the absoluteReminder with a relative one
        relativeReminderInterval = timedelta(minutes=10)
        relativeReminder = anEvent.setUserReminderInterval(relativeReminderInterval)

        # Make sure it all got reconnected correctly: one expired relative reminder
        for rem in remindable.reminders:
            rem.updatePending(datetime.now(self.view.tzinfo.default))
        self.failUnlessEqual(len(remindable.reminders), 1)
        self.failUnless(remindable.reminders.first() is relativeReminder)
        self.failUnlessEqual(anEvent.userReminderInterval,
                             relativeReminderInterval)
        self.failUnless(remindable.userReminderTime is None)
        self.failUnlessEqual(relativeReminder.nextPoll, Reminder.farFuture)

        # Change the start time to 'shortly'
        now = datetime.now(tz=self.view.tzinfo.default) 
        shortly = now + timedelta(minutes=60)
        EventStamp(anEvent).startTime = shortly
        
        # Make sure it all got updated correctly: one pending startTime
        # reminder, one now unexpired relative reminder.
        self.failUnlessEqual(len(remindable.reminders), 1)
        self.failUnless(remindable.reminders.first() is relativeReminder)
        self.failUnless(remindable.reminders.first() is
                        remindable.getUserReminder())
        
        startTimeReminder = schema.ns("osaf.pim", self.view).triageStatusReminder
        self.failIf(startTimeReminder.delta)
        startTimeReminder.updatePending(now)
        self.failUnlessEqual(startTimeReminder.nextPoll, shortly)
        
        # Check that the relative reminder is no longer expired, since
        # the event moved into the future.
        self.failIf(relativeReminder.isExpired())
        
        # Now, let's set a new reminder interval, so we can "bring up"
        # a new reminder and snooze it.
        relativeReminderInterval = -timedelta(minutes=15)
        newReminder = anEvent.setUserReminderInterval(relativeReminderInterval)
        
        # Make sure the old one got deleted
        self.failUnless(isDead(relativeReminder))
        self.failUnless(newReminder in remindable.reminders)
        
        #self.failUnless(startTimeReminder.getNextReminderTimeFor(remindable) == shortly)
        self.failUnlessEqual(anEvent.userReminderInterval,
                             relativeReminderInterval)
        self.failUnless(remindable.userReminderTime is None)
        #self.failUnless(remindable.nextReminderTime == shortly)

        newReminder.updatePending(now)
        self.failUnlessEqual(newReminder.nextPoll,
                             shortly + relativeReminderInterval)
                             
        # Snooze the reminder for 5 minutes. (Snoozing causes any user reminder
        # to be expired, whether it's fired or not, and a new snooze reminder
        # to be created. This shouldn't affect the startTime reminder.)
        newReminder.updatePending(newReminder.nextPoll)
        
        self.failUnlessEqual(1, len(newReminder.pendingEntries))
        self.failUnlessEqual(newReminder.pendingEntries.first().item,
                             remindable)
                             
        self.failUnlessEqual(newReminder.pendingEntries.first().when,
                             shortly + relativeReminderInterval)
        
        newReminder.snoozeItem(remindable, timedelta(minutes=5))
        
        # Check connections: the relative reminder remains, with a pending
        # entry in
        # active absolute reminder that we won't keep when it fires, and the
        # startTime reminder.
        self.failUnlessEqual(1, len(newReminder.pendingEntries))
        
        # >= b/c some time elapsed in between our calling datetime.now() and
        # snoozeItem().
        self.failUnless(newReminder.pendingEntries.first().when >=
                        now + timedelta(minutes=5))
        self.failUnlessEqual(newReminder.pendingEntries.first().when,
                             newReminder.nextPoll)
        self.failUnlessEqual(newReminder.pendingEntries.first().item,
                             remindable)

        self.failUnlessEqual(list(remindable.reminders), [newReminder])
        self.failUnless(newReminder.userCreated)
        self.failIf(startTimeReminder.userCreated)

        # Dismiss the snoozed reminder
        newReminder.dismissItem(remindable)

        # (should destroy the snoozed reminder, leaving only the expired one and
        # the startTime reminder)
        self.failUnless(newReminder.isExpired())
        
        self.failUnlessEqual(list(remindable.reminders), [newReminder])
                             
        self.failIf(startTimeReminder.pendingEntries)
        self.failUnlessEqual(startTimeReminder.nextPoll, shortly)
        
        # Change the startTime to the distant past
        EventStamp(anEvent).startTime = pastTime
        
        for rem in remindable.reminders:
            rem.updatePending(now)
        
        # (Just the expired one - no startTime reminder)
        self.failUnlessEqual(1, len(remindable.reminders))
        self.failUnlessEqual(newReminder.nextPoll, Reminder.farFuture)

        # The triage status reminder never dies ... ?
        self.failIf(isDead(startTimeReminder))
        self.failIfEqual(startTimeReminder.nextPoll, Reminder.farFuture)


class PendingTuplesTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(PendingTuplesTestCase, self).setUp()
        self.eventTime = datetime.combine(datetime.now().date() +
                                           timedelta(days=3),
                                          time(13, 0, tzinfo=self.view.tzinfo.default))
        self.event = CalendarEvent("calendarEventItem", itsView=self.view,
                              startTime=self.eventTime,
                              duration=timedelta(hours=1), allDay=False,
                              anyTime=False)
        
    def runNonRecurringTest(self, deltaMinutes):
        pollTime = self.eventTime.replace(hour=12, minute=15,
                                          microsecond=213985)
                              
        self.event.userReminderInterval = timedelta(minutes=deltaMinutes)
        
        # Should have no reminders before the fireDate
        self.failIf(Reminder.getPendingTuples(self.view, pollTime))

        # Still no reminders just before....
        pollTime = self.eventTime + timedelta(minutes=deltaMinutes-1,
                                              microseconds=642202)
        self.failIf(Reminder.getPendingTuples(self.view, pollTime))
        
        # But should have 1 right after!
        pollTime += timedelta(minutes=1)
        tuples = Reminder.getPendingTuples(self.view, pollTime)
        
        self.failUnlessEqual(len(tuples), 1)

        reminder = self.event.itsItem.getUserReminder()

        self.failUnlessEqual(
            tuples,
            [(self.eventTime + timedelta(minutes=deltaMinutes),
              self.event.itsItem,
              reminder),]
        )
        
        reminder.dismissItem(self.event.itsItem)
        
        self.failIf(Reminder.getPendingTuples(self.view, pollTime))


    def testBeforeReminder(self):
        self.runNonRecurringTest(-15)

    def testAfterReminder(self):
        self.runNonRecurringTest(+20)

    def runRecurringTest(self, deltaMinutes):
        pollTime = self.eventTime.replace(hour=12, minute=15,
                                          microsecond=213985)


        # Move the event back in time; we'll make it recur and
        # check the reminder on the occurrence that corresponds to
        # self.eventTime.
        self.event.startTime -= timedelta(days=10)
        self.event.userReminderInterval = timedelta(minutes=deltaMinutes)
        
        ruleItem = RecurrenceRule(None, itsView=self.view, freq='daily')
        rruleset = RecurrenceRuleSet(None, itsView=self.view,
                                          rrules=[ruleItem])                                          
        self.event.rruleset = rruleset

        # Should have no reminders before the fireDate
        self.failIf(Reminder.getPendingTuples(self.view, pollTime))

        # ... even a fraction of a second before
        pollTime = self.eventTime + timedelta(minutes=deltaMinutes-1,
                                              microseconds=653507)

        # But should have 1 right after
        pollTime += timedelta(minutes=1)
        tuples = Reminder.getPendingTuples(self.view, pollTime)
        
        self.failUnlessEqual(len(tuples), 1)
        self.failUnlessEqual(tuples[0][0],
                             self.eventTime + timedelta(minutes=deltaMinutes))
        self.failUnlessEqual(tuples[0][2], self.event.itsItem.getUserReminder())
        
        occurrence = EventStamp(tuples[0][1])
        self.failUnlessEqual(occurrence.occurrenceFor, self.event.itsItem)
        self.failUnlessEqual(occurrence.startTime, self.eventTime)
        
    def testRecurringBeforeReminder(self):
        self.runRecurringTest(-10)

    def testRecurringAfterReminder(self):
        self.runRecurringTest(+60)

if __name__ == "__main__":
    unittest.main()


