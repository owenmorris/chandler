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
from calculated import Calculated
from datetime import datetime, time, timedelta
from PyICU import ICUtzinfo

# Make a value we can use for distant (or invalid) reminder times
farFuture = datetime.max
if getattr(farFuture, 'tzInfo', None) is None:
    farFuture = farFuture.replace(tzinfo=ICUtzinfo.default)

class Reminder(schema.Item):
    absoluteTime = schema.One(
        schema.DateTimeTZ,
        defaultValue=None,
        doc="If set, overrides relativeTo as the base time for this reminder"
    )

    relativeTo = schema.One(
        schema.Text,
        defaultValue=None,
        doc="The Remindable attribute that we're relative to",
    )

    delta = schema.One(
        schema.TimeDelta,
        defaultValue=timedelta(0),
        doc="Offset relative to 'relativeTo' that this reminder should occur",
    )
    
    userCreated = schema.One(
        schema.Boolean,
        defaultValue=True,
        doc="Is a user-created reminder?"
    )
        
    keepExpired = schema.One(
        schema.Boolean,
        defaultValue=True,
        doc="Should we keep this around (in the Remindable's expiredReminders) "
            "after it fires?")
    
    reminderItems = schema.Sequence(
        "Remindable",
        inverse="reminders",
        initialValue=[]
    )

    expiredReminderItems = schema.Sequence(
        "Remindable",
        inverse="expiredReminders",
        initialValue=[]
    )

    schema.addClouds(
        sharing = schema.Cloud(absoluteTime, delta, relativeTo, 
                               userCreated, keepExpired)
    )

    def getBaseTimeFor(self, remindable):
        """
        Get the base time for this remindable's next reminder:
        - it's our absolute time if we have one; 
        - otherwise, get the relative-to time from our remindable
        - otherwise, use a time in the far future.
        """
        return self.absoluteTime or getattr(remindable, self.relativeTo) \
               or farFuture

    def getNextReminderTimeFor(self, remindable):
        """ Get the time for this remindable's next reminder """
        result = self.getBaseTimeFor(remindable)
        if result != farFuture:
            result += self.delta
        assert result.tzinfo is not None
        #if result.tzinfo is None:
            #result = result.replace(tzinfo=ICUtzinfo.default)
        return result

class Remindable(schema.Item):
    reminders = schema.Sequence(
        Reminder,
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

    def getUserReminder(self, collectionToo=False):
        for attr in ("reminders", "expiredReminders"):
            if (self.hasLocalAttributeValue(attr)):
                collection = getattr(self, attr)
                for reminder in collection:
                    if reminder.userCreated:
                        return collectionToo and (collection, reminder) or reminder
        return collectionToo and (None, None) or None

    def replaceUserReminder(self, **kwds):
        (collection, userReminder) = self.getUserReminder(True)

        if userReminder is not None:
            collection.remove(userReminder)
            if not (len(userReminder.reminderItems) or \
                    len(userReminder.expiredReminderItems)):
                userReminder.delete()

        if kwds.get('delta') is None and kwds.get('absoluteTime') is None:
            return None
        
        return self.makeReminder(userCreated=True, keepExpired=True,
                                 checkExpired=True, **kwds)
    
    # @@@ Note: 'Calculated' APIs are provided for both relative and absolute
    # user-set reminders, even though only one reminder (which can be of either
    # flavor) can be set right now. The 'set' functions can replace an existing
    # reminder of either flavor, but the 'get' functions ignore (that is, return
    # 'None' for) reminders of the wrong flavor.
    
    def getUserReminderInterval(self):
        userReminder = self.getUserReminder()
        if userReminder is None or userReminder.absoluteTime is not None:
            return None
        return userReminder.delta

    def setUserReminderInterval(self, delta):
        assert hasattr(self, 'effectiveStartTime')
        return self.replaceUserReminder(delta=delta, relativeTo='effectiveStartTime')

    userReminderInterval = Calculated(
        schema.TimeDelta,
        basedOn=('reminders',),
        fget=getUserReminderInterval,
        fset=setUserReminderInterval,
        doc="User-set reminder interval, computed from the first unexpired reminder."
    )

    def getUserReminderTime(self):
        userReminder = self.getUserReminder()
        if userReminder is None or userReminder.absoluteTime is None:
            return None
        return userReminder.absoluteTime

    def setUserReminderTime(self, absoluteTime):
        return self.replaceUserReminder(absoluteTime=absoluteTime)
    
    userReminderTime = Calculated(
        schema.DateTimeTZ,
        basedOn=('reminders',),
        fget=getUserReminderTime,
        fset=setUserReminderTime,
        doc="User-set absolute reminder time."
    )

    def getReminderFireTime(self):
        """
        Get the next reminder (of any kind) due to fire, or None if there aren't
        any.
        """
        for reminder in self.reminders:
            nextTime = reminder.getNextReminderTimeFor(self)
            if nextTime is not None:
                return nextTime
        return None
    
    # @@@ For now, this is used to set absolute user reminders
    # @@@ This is used for the next reminder of any kind (user or not), which is
    # what the reminder-firing mechanism wants
    reminderFireTime = Calculated(
        schema.DateTimeTZ,
        basedOn=('startTime', 'allDay', 'anyTime', 'reminders'),
        fget=getReminderFireTime,
        doc="Reminder fire time, or None for no unexpired reminders")

    def makeReminder(self, checkExpired=False, **kwds):
        # @@@ I think the proxy code should override calls to this method
        # add a separate reference to this reminder to each generated event,
        # (or something like that). (Remindable.snoozeReminder will call this
        # method; that operation should only affect the actual event, not the
        # series)
        
        newReminder = Reminder(None, itsView=self.itsView, **kwds)

        addThisTo = self.reminders
        if checkExpired:
            nextTime = newReminder.getNextReminderTimeFor(self)

            if (nextTime is not None and
                nextTime < datetime.now(ICUtzinfo.default)):
                assert kwds['keepExpired'], "Creating an expired reminder that isn't marked 'keepExpired'?"
                addThisTo = self.expiredReminders

        addThisTo.add(newReminder)
        return newReminder

    def dismissReminder(self, reminder):
        """ Dismiss this reminder. """

        # Make sure the next one's around, so we'll prime the reminder-
        # watching mechanism to alert us about it. We also check that
        # reminders for past events don't trigger this one.
        try:
            getNextOccurrenceMethod = self.getNextOccurrence
        except AttributeError:
            pass
        else:
            # Get the next occurrence of this event. We
            # don't need to do anything with it; we just
            # want to make sure it's been instantiated
            # so that the next reminder will fire.
            getNextOccurrenceMethod(after=datetime.now(ICUtzinfo.default))

        # In the case of generated occurrences, the reminder
        # may already have fired (cf fixReminders() in
        # CalendarEventMixin.getNextOccurrence
        if reminder in self.reminders:
            self.reminders.remove(reminder)
        if not reminder.keepExpired:
            # This is a system or "snooze" reminder, just toss it.
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
                               absoluteTime=(datetime.now(ICUtzinfo.default) +
                                             delay),
                               keepExpired=False,
                               userCreated=False)
        self.reminders.add(newReminder)
        return newReminder
