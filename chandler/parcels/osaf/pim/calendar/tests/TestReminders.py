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


