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
from osaf.pim import CalendarEvent, Reminder
import osaf.pim.tests.TestDomainModel as TestDomainModel
from PyICU import ICUtzinfo
import repository.item
from datetime import datetime, timedelta

class ReminderTestCase(TestDomainModel.DomainModelTestCase):
    def testReminders(self):
        # Make an event and add an expired absolute reminder to it.
        anEvent = CalendarEvent("calendarEventItem", itsView=self.rep.view,
                                startTime=datetime(2005,3,8,12,00,
                                                   tzinfo = ICUtzinfo.default),
                                duration=timedelta(hours=1),
                                allDay=False, anyTime=False)
        
        absoluteReminderTime = datetime(2005,3,8,11,00, tzinfo=ICUtzinfo.default)
        absoluteReminder = anEvent.setUserReminderTime(absoluteReminderTime)
        
        # Make sure it got connected right: one expired absolute reminder.
        self.failIf(len(anEvent.reminders))
        self.failUnless(len(anEvent.expiredReminders) == 1 \
                        and anEvent.expiredReminders.first() is absoluteReminder)
        self.failUnless(anEvent.userReminderTime == absoluteReminderTime)
        self.failUnless(anEvent.userReminderInterval is None)
        self.failUnless(anEvent.reminderFireTime == None)
        
        # Replace the absoluteReminder with a relative one
        relativeReminderInterval = timedelta(minutes=-10)
        relativeReminder = anEvent.setUserReminderInterval(relativeReminderInterval)

        # Make sure it all got reconnected correctly: one expired relative reminder
        self.failIf(len(anEvent.reminders))
        self.failUnless(len(anEvent.expiredReminders) == 1 \
                        and anEvent.expiredReminders.first() is relativeReminder)
        self.failUnless(anEvent.userReminderInterval == relativeReminderInterval)
        self.failUnless(anEvent.userReminderTime is None)
        self.failUnless(anEvent.reminderFireTime == None)

        # Snooze the reminder for 5 minutes.
        snoozeReminder = anEvent.snoozeReminder(relativeReminder,
                                                timedelta(minutes=5))
        # Check connections: the relative expired reminder remains, plus an
        # active absolute reminder that we won't keep when it fires.
        self.failUnless(list(anEvent.expiredReminders) == [ relativeReminder ])
        self.failUnless(list(anEvent.reminders) == [ snoozeReminder ])
        self.failUnless(snoozeReminder.keepExpired == False)
        self.failUnless(snoozeReminder.reminderItems.first() is anEvent)

        # Dismiss the snoozed reminder
        anEvent.dismissReminder(snoozeReminder)
        # (should destroy the snoozed reminder, leaving only the expired one)
        self.failIf(len(anEvent.reminders))
        self.failUnless(list(anEvent.expiredReminders) == [ relativeReminder ])
        self.failUnless(relativeReminder.reminderItems.first() is None)

if __name__ == "__main__":
    unittest.main()


