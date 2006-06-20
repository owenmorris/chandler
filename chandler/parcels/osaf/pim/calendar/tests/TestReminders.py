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
        # Make an event and add a reminder to it.
        anEvent = CalendarEvent("calendarEventItem", itsView=self.rep.view,
                                startTime=datetime(2005,3,8,12,00,
                                                   tzinfo = ICUtzinfo.default),
                                duration=timedelta(hours=1),
                                allDay=False, anyTime=False)
        regularReminder = anEvent.makeReminder(timedelta(minutes=-10))

        # Make sure it all got connected correctly
        self.failUnless(len(anEvent.reminders) == 1 \
                        and anEvent.reminders.first() is regularReminder)
        self.failIf(len(anEvent.expiredReminders))
        self.failUnless(anEvent.reminderFireTime == datetime(2005,3,8,11,50,
                                 tzinfo = ICUtzinfo.default))

        # Snooze the reminder for 5 minutes.
        snoozeReminder = anEvent.snoozeReminder(regularReminder,
                                                timedelta(minutes=5))
        # (should move the old reminder to expired)
        self.failUnless(list(anEvent.expiredReminders) == [ regularReminder ])
        self.failUnless(list(anEvent.reminders) == [ snoozeReminder ])
        self.failUnless(snoozeReminder.reminderItems.first() is not None)

        # Dismiss the snoozed reminder
        anEvent.dismissReminder(snoozeReminder)
        # (should destroy the snoozed reminder, leaving only the expired one)
        self.failIf(len(anEvent.reminders))
        self.failUnless(list(anEvent.expiredReminders) == [ regularReminder ])
        self.failUnless(regularReminder.reminderItems.first() is None)

if __name__ == "__main__":
    unittest.main()


