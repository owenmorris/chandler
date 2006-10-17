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
from osaf.pim import CalendarEvent, EventStamp, Reminder, Remindable
import osaf.pim.tests.TestDomainModel as TestDomainModel
from PyICU import ICUtzinfo
import repository.item
from datetime import datetime, timedelta

class ReminderTestCase(TestDomainModel.DomainModelTestCase):
    def testReminders(self):
        # Make an event in the past (so it won't have a startTime reminder)
        # and add an expired absolute reminder to it.
        pastTime = datetime(2005,3,8,12,00, tzinfo = ICUtzinfo.default)
        anEvent = CalendarEvent("calendarEventItem", itsView=self.rep.view,
                                startTime=pastTime,
                                duration=timedelta(hours=1),
                                allDay=False, anyTime=False)
        remindable = Remindable(anEvent)
        
        absoluteReminderTime = datetime(2005,3,8,11,00, tzinfo=ICUtzinfo.default)
        absoluteReminder = remindable.setUserReminderTime(absoluteReminderTime)
        
        # Make sure it got connected right: one expired absolute reminder.
        self.failIf(len(remindable.reminders))
        self.failUnless(len(remindable.expiredReminders) == 1 \
                        and remindable.expiredReminders.first() is absoluteReminder)
        self.failUnless(remindable.userReminderTime == absoluteReminderTime)
        self.failUnless(remindable.userReminderInterval is None)
        self.failUnless(remindable.nextReminderTime == Reminder.farFuture)
        
        # Replace the absoluteReminder with a relative one
        relativeReminderInterval = timedelta(minutes=-10)
        relativeReminder = remindable.setUserReminderInterval(relativeReminderInterval)

        # Make sure it all got reconnected correctly: one expired relative reminder
        self.failIf(len(remindable.reminders))
        self.failUnless(len(remindable.expiredReminders) == 1 \
                        and remindable.expiredReminders.first() is relativeReminder)
        self.failUnless(remindable.userReminderInterval == relativeReminderInterval)
        self.failUnless(remindable.userReminderTime is None)
        self.failUnless(remindable.nextReminderTime == Reminder.farFuture)

        # Change the start time to 'shortly'
        now = datetime.now(tz=ICUtzinfo.default) 
        shortly = now + timedelta(minutes=60)
        EventStamp(anEvent).startTime = shortly
        
        # Make sure it all got reconnected correctly: one pending startTime reminder, 
        # one expired relative reminder.
        self.failUnless(len(remindable.expiredReminders) == 1 \
                        and remindable.expiredReminders.first() is relativeReminder)
        self.failUnless(len(remindable.reminders) == 1)
        startTimeReminder = remindable.reminders.first()
        self.failUnless(startTimeReminder.getNextReminderTimeFor(remindable) == shortly)
        self.failUnless(remindable.userReminderInterval == relativeReminderInterval)
        self.failUnless(remindable.userReminderTime is None)
        self.failUnless(remindable.nextReminderTime == shortly)
        
        # Snooze the reminder for 5 minutes. (Snoozing causes any user reminder to be
        # expired, whether it's fired or not, and a new snooze reminder to be created.
        # This shouldn't affect the startTime reminder.)
        relativeReminder = remindable.expiredReminders.first()
        snoozeReminder = remindable.snoozeReminder(relativeReminder,
                                                   timedelta(minutes=5))
        
        # Check connections: the relative expired reminder remains, plus an
        # active absolute reminder that we won't keep when it fires, and the
        # startTime reminder.
        self.failUnless(len(remindable.expiredReminders) == 1)
        self.failUnless(remindable.expiredReminders.first() == relativeReminder)
        self.failUnless(snoozeReminder.userCreated == False)
        self.failUnless(startTimeReminder.userCreated == False)
        self.failUnlessEqual(set(remindable.reminders), set((snoozeReminder, startTimeReminder)))
        self.failUnlessEqual(snoozeReminder.reminderItems.first(),
                             remindable.itsItem)
        self.failIfEqual(remindable.nextReminderTime, Reminder.farFuture)

        # Dismiss the snoozed reminder
        remindable.dismissReminder(snoozeReminder)

        # (should destroy the snoozed reminder, leaving only the expired one and
        # the startTime reminder)
        self.failUnlessEqual(list(remindable.reminders), [startTimeReminder])
        self.failUnlessEqual(list(remindable.expiredReminders), [relativeReminder])
        self.failUnless(relativeReminder.reminderItems.first() is None)
        self.failUnless(relativeReminder.expiredReminderItems.first() is remindable.itsItem)
        
        # Change the startTime to the distant past
        EventStamp(anEvent).startTime = pastTime
        
        # (Just the expired one - no startTime reminder)
        self.failIf(len(remindable.reminders))
        self.failUnlessEqual(list(remindable.expiredReminders), [relativeReminder])
        self.failUnlessEqual(remindable.nextReminderTime, Reminder.farFuture)

if __name__ == "__main__":
    unittest.main()


