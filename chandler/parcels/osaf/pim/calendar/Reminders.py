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


from application import schema
from osaf.pim.items import Calculated, ContentItem
from datetime import datetime, time, timedelta
from PyICU import ICUtzinfo


class Reminder(schema.Item):
    delta = schema.One(
        schema.TimeDelta,
        doc="The amount in advance this reminder should occur (usually negative!)",
    )

    relativeTo = schema.One(
        schema.Text,
        initialValue='effectiveStartTime',
    )

    reminderItems = schema.Sequence(
        "RemindableMixin",
        inverse="reminders",
        initialValue=[]
    )

    expiredReminderItems = schema.Sequence(
        "RemindableMixin",
        inverse="expiredReminders",
        initialValue=[]
    )

    snoozedUntil = schema.One(
        schema.DateTimeTZ,
        defaultValue=None
    )

    schema.addClouds(
        sharing = schema.Cloud(delta, relativeTo, snoozedUntil)
    )

    def getBaseTimeFor(self, remindable):
        """
        Get the relative-to time for this remindable's next reminder
        so that the UI can generate a message relative to it.
        """
        return getattr(remindable, self.relativeTo, datetime.max)

    def getNextReminderTimeFor(self, remindable):
        """ Get the time for this remindable's next reminder """
        result = self.snoozedUntil or \
               (self.getBaseTimeFor(remindable) + self.delta)
        if result.tzinfo is None:
            result = result.replace(tzinfo=ICUtzinfo.default)
        return result

class RemindableMixin(ContentItem):
    reminders = schema.Sequence(
        Reminder,
        displayName=u"Reminders",
        inverse=Reminder.reminderItems,
        initialValue=[]
    )

    expiredReminders = schema.Sequence(
        Reminder,
        inverse=Reminder.expiredReminderItems,
        initialValue=[]
    )

    schema.addClouds(
        copying = schema.Cloud(reminders,expiredReminders),
        sharing = schema.Cloud(
            byCloud = [reminders, expiredReminders]
        )
    )

    def getReminderInterval(self):
        for attr in ("reminders", "expiredReminders"):
            if (self.hasLocalAttributeValue(attr)):
                #@@@ This assumes we've only got 0 or 1 reminders.
                first = getattr(self, attr).first()
                try:
                    return first.delta
                except AttributeError:
                    pass

        return None

    def setReminderInterval(self, delta):
        reminderCollection = self.reminders
        firstReminder = reminderCollection.first()

        if firstReminder is None:
            reminderCollection = self.expiredReminders
            firstReminder = reminderCollection.first()

        if firstReminder is not None:
            reminderCollection.remove(firstReminder)
            if not (len(firstReminder.reminderItems) or \
                    len(firstReminder.expiredReminderItems)):
                firstReminder.delete()

        if delta is not None:
            self.makeReminder(delta, checkExpired=True)

    reminderInterval = Calculated(
        schema.TimeDelta,
        basedOn=('reminders',),
        fget=getReminderInterval,
        fset=setReminderInterval,
        doc="Reminder interval, computed from the first unexpired reminder."
    )

    def getReminderFireTime(self):
        """
        A simplification of the possible complexity of reminder, assumes one
        or zero reminders.  Returns a datetime or None.
        """
        reminder = self.reminders.first()
        if reminder is None:
            return None
        else:
            return reminder.getNextReminderTimeFor(self)

    reminderFireTime = Calculated(
        schema.DateTimeTZ,
        basedOn=('startTime', 'allDay', 'anyTime', 'reminders'),
        fget=getReminderFireTime,
        doc="Reminder fire time, or None for no unexpired reminders")

    def makeReminder(self, delta, checkExpired=False):
        # @@@ I think the proxy code should override calls to this method
        # add a separate reference to this reminder to each generated event,
        # (or something like that). (Remindable.snoozeReminder will call this
        # method; that operation should only affect the actual event, not the
        # series)
        newReminder = Reminder(None, delta=delta, itsView=self.itsView)

        addThisTo = self.reminders

        if checkExpired:
            nextTime = newReminder.getNextReminderTimeFor(self)

            if (nextTime is not None and
                nextTime < datetime.now(ICUtzinfo.default)):
                addThisTo = self.expiredReminders

        addThisTo.add(newReminder)
        return newReminder

    def dismissReminder(self, reminder):
        """ Dismiss this reminder. """

        # Make sure the next one's around, so we'll prime the reminder-
        # watching mechanism to alert us about it. We also check that
        # reminders for past events don't trigger this one.
        now = datetime.now(ICUtzinfo.default)

        try:
            getNextOccurrenceMethod = self.getNextOccurrence
        except AttributeError:
            pass
        else:
            # Get the next occurrence of this event. We
            # don't need to do anything with it; we just
            # want to make sure it's been instantiated
            # so that the next reminder will fire.
            getNextOccurrenceMethod(after=now)

        # In the case of generated occurrences, the reminder
        # may already have fired (cf fixReminders() in
        # CalendarEventMixin.getNextOccurrence
        if reminder in self.reminders:
            self.reminders.remove(reminder)
        if getattr(reminder, 'snoozedUntil', None) is not None:
            # This is a "snooze" reminder, just toss it.
            assert len(reminder.reminderItems) == 0
            assert len(reminder.expiredReminderItems) == 0
            reminder.delete()
        else:
            if not reminder in self.expiredReminders:
                self.expiredReminders.add(reminder)



    def snoozeReminder(self, reminder, delay):
        """ Snooze this reminder for this long. """
        # Dismiss the original reminder
        originalTime = reminder.getNextReminderTimeFor(self)
        self.dismissReminder(reminder)

        # Make a new reminder for this event
        newReminder = Reminder(None, itsView=self.itsView,
                               snoozedUntil=(datetime.now(ICUtzinfo.default) +
                                             delay))
        self.reminders.add(newReminder)
        return newReminder
