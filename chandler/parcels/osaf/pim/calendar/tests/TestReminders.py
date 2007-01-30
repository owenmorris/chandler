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


import repository.tests.RepositoryTestCase as RepositoryTestCase
import unittest
from osaf.pim import *
from osaf.pim.calendar.Recurrence import *
import osaf.pim.tests.TestDomainModel as TestDomainModel
from PyICU import ICUtzinfo
import repository.item
from datetime import datetime, timedelta, time

class AbsoluteReminderTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(AbsoluteReminderTestCase, self).setUp()
        self.reminderTime = datetime(2007,5,11,13,tzinfo=ICUtzinfo.default)
        self.item = ContentItem(itsView=self.rep.view)
        self.reminder = Reminder(itsView=self.rep.view,
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
                        datetime.now(ICUtzinfo.default) + timedelta(minutes=10))
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
        self.event = CalendarEvent(itsView=self.rep.view,
                startTime=datetime(2004,8,1,8,tzinfo=ICUtzinfo.default),
                duration=timedelta(minutes=45), anyTime=False,
                summary=u"Meet with Very Important Person",
                triageStatus=TriageEnum.later)

        self.reminder = RelativeReminder(itsView=self.rep.view,
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
                        datetime.now(ICUtzinfo.default) + timedelta(minutes=15))
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
        ruleItem = RecurrenceRule(None, itsView=self.rep.view, freq='daily')
        rruleset = RecurrenceRuleSet(None, itsView=self.rep.view,
                                          rrules=[ruleItem])
                                          
        self.reminderTime = datetime(2004,11,1,12,22,3,tzinfo=ICUtzinfo.default)
        self.reminder = Reminder(itsView=self.rep.view,
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
        self.event = CalendarEvent(itsView=self.rep.view,
                startTime=datetime(2007,1,4,12,5,tzinfo=ICUtzinfo.default),
                duration=timedelta(minutes=55),
                anyTime=False,
                summary=u"Meet with Highly Unusual Person")

        self.reminder = RelativeReminder(itsView=self.rep.view,
                            delta=-timedelta(minutes=20))
                            
        ruleItem = RecurrenceRule(None, itsView=self.rep.view, freq='daily')
        ruleItem.until = datetime(2007,1,23,tzinfo=ICUtzinfo.default)
        ruleItem.untilIsDate = False
        self.event.rruleset = RecurrenceRuleSet(None, itsView=self.rep.view,
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

        self.failUnlessEqual(2, len(self.event.itsItem.reminders))
        
        # @@@ [grant] Need to redo this for changing absolute or
        # relative reminders
        tsReminder = modsReminder = None
        for rem in self.event.itsItem.reminders:
            if rem.delta:
                modsReminder = rem
            else:
                tsReminder = rem
                
        self.failIf(modsReminder is None)
        self.failIf(tsReminder is None)
        
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
                             
        # Check that it has exactly one triage status reminder
        tsReminders = list(rem for rem in occurrence.itsItem.reminders if
                           not rem.userCreated and not rem.promptUser)
        self.failUnlessEqual(len(tsReminders), 1)


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

class ReminderCollectionsTestCase(TestDomainModel.DomainModelTestCase):
    # Test behaviour of the 'reminders' collections in osaf.pim
    def setUp(self):
        super(ReminderCollectionsTestCase, self).setUp()
        self.note = Note(itsView=self.rep.view,
                displayName=u"I am so very notable")

        
        self.firstDate = datetime(2004, 11, 3, 9, 25, tzinfo=ICUtzinfo.default)
        self.reminder = Reminder(itsView=self.rep.view,
                                 absoluteTime=self.firstDate)
        self.reminder.reminderItem = self.note
        
        self.unexpired = schema.ns("osaf.pim", self.rep.view).allFutureReminders
        
    def testFireAndDismissReminder(self):
        self.failUnlessEqual(list(self.unexpired), [self.reminder])
        self.reminder.updatePending(self.reminder.absoluteTime)
        self.failUnlessEqual(list(self.unexpired), [])
        
        self.reminder.dismissItem(self.note)
        self.failUnlessEqual(list(self.unexpired), [])

    def testPendingEntries(self):
        def getPending():
            kind = PendingReminderEntry.getKind(self.rep.view)
            
            return list(kind.iterItems())
            
        self.failUnlessEqual(list(self.unexpired), [self.reminder])
        self.failUnlessEqual([], getPending())
        self.reminder.updatePending(self.reminder.absoluteTime)
        self.failUnlessEqual([self.reminder.pendingEntries.first()],
                             getPending())
        
        self.reminder.dismissItem(self.note)
        self.failUnlessEqual(list(self.unexpired), [])
        self.failUnlessEqual([], getPending())
        
class TriageStatusReminderTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(TriageStatusReminderTestCase, self).setUp()
        self.event = CalendarEvent(itsView=self.rep.view,
                startTime=datetime(2005,11,4,16,tzinfo=ICUtzinfo.default),
                duration=timedelta(minutes=60),
                anyTime=False,
                summary=u"Hour-long event")

    def testTriageChange(self):
        # Let's imagine we have a change to triage of later 2 hours before
        # the event
        self.event.itsItem.triageStatus = TriageEnum.later
        self.event.itsItem.setTriageStatusChanged(when=self.event.startTime -
                                                 timedelta(hours=2))
                                          
        reminders = list(self.event.itsItem.reminders)
        self.failUnlessEqual(1, len(reminders))
        
        self.failIf(reminders[0].delta)
        
        reminders[0].updatePending(self.event.startTime - timedelta(hours=1))
        self.failUnlessEqual(self.event.startTime, reminders[0].nextPoll)
        self.failIf(reminders[0].pendingEntries)
        
        reminders[0].updatePending(reminders[0].nextPoll)
        self.failUnlessEqual(self.event.itsItem.triageStatus, TriageEnum.now)
        # @@@ [grant] No way to get triageStatusChanged. Tsk.
        
        # Now that the reminder has been fired, it should have deleted itself,
        # since it's not user-generated.
        self.failUnless(isDead(reminders[0]))

    def testPastNoTriageChange(self):
        self.event.itsItem.triageStatus = TriageEnum.done
        self.event.itsItem.setTriageStatusChanged(when=self.event.startTime +
                                                 timedelta(days=2))
                                                 
        reminders = list(self.event.itsItem.reminders)
        self.failUnlessEqual(1, len(reminders))
        
        self.failIf(reminders[0].delta)

        reminders[0].updatePending(self.event.startTime + timedelta(days=3))
        
        self.failUnlessEqual(self.event.itsItem.triageStatus, TriageEnum.done)

        self.failUnless(isDead(reminders[0]))

    def testRecurring(self):
        self.event.itsItem.triageStatus = TriageEnum.later
        self.event.itsItem.setTriageStatusChanged(when=self.event.startTime +
                                                 timedelta(days=3))

        # Make our event recurring
        ruleItem = RecurrenceRule(None, itsView=self.rep.view, freq='daily')
        ruleItem.until = datetime.combine(
                    self.event.startTime + timedelta(days=6),
                    time(0, tzinfo=ICUtzinfo.default))
        ruleItem.untilIsDate = True
        self.event.rruleset = RecurrenceRuleSet(None, itsView=self.rep.view,
                                rrules=[ruleItem])
                                
        reminders = list(self.event.itsItem.reminders)
        self.failUnlessEqual(1, len(reminders))
        
        self.failIf(reminders[0].delta)

        # Trigger a triage status change that starts with the 5th occurrence
        fifthStart = self.event.startTime + timedelta(days=4)
        reminders[0].updatePending(fifthStart)
        fifth = self.event.getRecurrenceID(fifthStart)
        
        self.failUnless(fifth.modificationFor)
        self.failUnlessEqual(fifth.itsItem.triageStatus, TriageEnum.now)
        
        self.failUnlessEqual(self.event.getFirstOccurrence().itsItem.triageStatus,
                             TriageEnum.later)

        self.failIfEqual(self.event.getFirstOccurrence().itsItem.triageStatusChanged,
                         fifth.itsItem.triageStatusChanged)

                             
        self.failUnlessEqual(fifth.getNextOccurrence().itsItem.triageStatus,
                             TriageEnum.later)
        
        self.failIf(reminders[0].pendingEntries)
        
        # Expire all the pending entries ...
        reminders[0].updatePending(fifthStart + timedelta(days=7))
        
        # ... make sure the triage status got set to now
        event = fifth
        while event is not None:
            self.failUnlessEqual(event.itsItem.triageStatus, TriageEnum.now)
            event = event.getNextOccurrence()

        # ... and make sure the reminder got deleted
        self.failUnless(isDead(reminders[0]))

        
class ReminderTestCase(TestDomainModel.DomainModelTestCase):
    def testReminders(self):
        # Make an event in the past (so it won't have a startTime reminder)
        # and add an expired absolute reminder to it.
        pastTime = datetime(2005,3,8,12,00, tzinfo = ICUtzinfo.default)
        anEvent = CalendarEvent("calendarEventItem", itsView=self.rep.view,
                                startTime=pastTime,
                                duration=timedelta(hours=1),
                                allDay=False, anyTime=False)
        remindable = anEvent.itsItem
        
        absoluteReminderTime = datetime(2005,3,8,11,00, tzinfo=ICUtzinfo.default)
        absoluteReminder = remindable.setUserReminderTime(absoluteReminderTime)
        
        # Make sure it got connected right: one expired absolute reminder.
        # Er, we're assuming now > 2005/03/08, of course :o
        for rem in remindable.reminders:
            rem.updatePending(datetime.now(ICUtzinfo.default))
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
            rem.updatePending(datetime.now(ICUtzinfo.default))
        self.failUnlessEqual(len(remindable.reminders), 1)
        self.failUnless(remindable.reminders.first() is relativeReminder)
        self.failUnless(anEvent.userReminderInterval == relativeReminderInterval)
        self.failUnless(remindable.userReminderTime is None)
        self.failUnlessEqual(relativeReminder.nextPoll, Reminder.farFuture)

        # Change the start time to 'shortly'
        now = datetime.now(tz=ICUtzinfo.default) 
        shortly = now + timedelta(minutes=60)
        EventStamp(anEvent).startTime = shortly
        
        # Make sure it all got updated correctly: one pending startTime
        # reminder, one expired relative reminder.
        self.failUnlessEqual(len(remindable.reminders), 2)
        self.failUnless(remindable.getUserReminder() is relativeReminder)
        
        for rem in remindable.reminders:
            if not rem.userCreated:
                startTimeReminder = rem
                break
        else:
            self.fail("No start time reminder found!")
            
        self.failIf(startTimeReminder.delta)
        startTimeReminder.updatePending(now)
        self.failUnlessEqual(startTimeReminder.nextPoll, shortly)
        
        # Check that the relative reminder is still expired
        self.failUnless(relativeReminder.isExpired())
        
        # Now, let's set a new reminder interval, so we can bring up
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

        self.failUnlessEqual(set(remindable.reminders),
                             set([newReminder, startTimeReminder]))
        self.failUnless(newReminder.userCreated)
        self.failIf(startTimeReminder.userCreated)

        # Dismiss the snoozed reminder
        newReminder.dismissItem(remindable)

        # (should destroy the snoozed reminder, leaving only the expired one and
        # the startTime reminder)
        self.failUnless(newReminder.isExpired())
        
        self.failUnlessEqual(set(remindable.reminders),
                             set([newReminder, startTimeReminder]))
                             
        self.failIf(startTimeReminder.pendingEntries)
        self.failUnlessEqual(startTimeReminder.nextPoll, shortly)
        
        # Change the startTime to the distant past
        EventStamp(anEvent).startTime = pastTime
        
        for rem in remindable.reminders:
            rem.updatePending(now)
        
        # (Just the expired one - no startTime reminder)
        self.failUnlessEqual(1, len(remindable.reminders))
        self.failUnless(isDead(startTimeReminder))
        self.failUnlessEqual(newReminder.nextPoll, Reminder.farFuture)

if __name__ == "__main__":
    unittest.main()


