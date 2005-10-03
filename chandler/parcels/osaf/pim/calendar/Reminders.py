
from application import schema
from osaf.pim.items import Calculated, ContentItem
from datetime import datetime, time, timedelta
from DateTimeUtil import datetimeOp


class Reminder(schema.Item):
    schema.kindInfo(
        displayName=u"A Reminder for one or more RemindableMixin items"
    )

    delta = schema.One(
        schema.TimeDelta, 
        displayName=u"Delta",
        doc="The amount in advance this reminder should occur (usually negative!)",
    )

    relativeTo = schema.One(
        schema.String,
        displayName=u"Relative to",
        initialValue='effectiveStartTime',
    )

    reminderItems = schema.Sequence(
        "RemindableMixin", 
        displayName=u"Pending Reminder Items",
        inverse="reminders",
        initialValue=[]
    )

    expiredReminderItems = schema.Sequence(
        "RemindableMixin", 
        displayName=u"Expired Reminder Items",
        inverse="expiredReminders",
        initialValue=[]
    )
    
    snoozedUntil = schema.One(
        schema.DateTime,
        displayName=u"SnoozedUntil",
        defaultValue=None
    )
    
    schema.addClouds(
        sharing = schema.Cloud(delta, relativeTo, snoozedUntil,
            byCloud = [reminderItems, expiredReminderItems]
        )
    )
    
    def getBaseTimeFor(self, remindable):
        """ Get the relative-to time for this reminderable's next reminder
        
        so that the UI can generate a message relative to it.
        """
        return getattr(remindable, self.relativeTo, datetime.max)
    
    def getNextReminderTimeFor(self, remindable):
        """ Get the time for this reminderable's next reminder """
        return self.snoozedUntil or \
               (self.getBaseTimeFor(remindable) + self.delta)
    
    def getNextFiring(self):
        """ Get a tuple describing this reminder's next firing, or None.
        
        The tuple contains (firingTime, remindable, self); returns None if 
        no reminders are pending.
        """
        pending = [ (self.getNextReminderTimeFor(r), r, self ) \
                          for r in self.reminderItems ]
        try:
            return sorted(pending, Reminder.TupleComparer)[0]
        except IndexError:
            return None

    @staticmethod
    def TupleComparer(tuple1, tuple2):
        """ Compare reminder tuples as returned by getNextFiring """
        return datetimeOp(tuple1[0], 'cmp', tuple2[0]) \
               or cmp(tuple1[1], tuple2[1]) \
               or cmp(tuple1[2], tuple2[2])

class RemindableMixin(ContentItem):
    schema.kindInfo(
        displayName=u"RemindableMixin",
    )

    reminders = schema.Sequence(
        Reminder,
        displayName=u"Reminders",
        inverse=Reminder.reminderItems,
        initialValue=[]
    )
    
    expiredReminders = schema.Sequence(
        Reminder,
        displayName=u"Expired Reminders",
        inverse=Reminder.expiredReminderItems,
        initialValue=[]
    )
    
    schema.addClouds(
        copying = schema.Cloud(reminders,expiredReminders),
        sharing = schema.Cloud(
            byCloud = [reminders, expiredReminders]
        )
    )
    def makeReminder(self, delta):
        # @@@ I think the proxy code should override calls to this method
        # add a separate reference to this reminder to each generated event,
        # (or something like that). (Remindable.snoozeReminder will call this
        # method; that operation should only affect the actual event, not the 
        # series)
        newReminder = Reminder(None, delta=delta, view=self.itsView)
        self.reminders.add(newReminder)
        return newReminder

    def dismissReminder(self, reminder):
        """ Dismiss this reminder. """
        self.reminders.remove(reminder)
        if hasattr(reminder, 'snoozedUntil') \
           and reminder.snoozedUntil is not None:
            # This is a "snooze" reminder, just toss it.
            assert len(reminder.reminderItems) == 0
            assert len(reminder.expiredReminderItems) == 0
            reminder.delete()
        else:
            self.expiredReminders.add(reminder)
            # Make sure the next one's around, so we'll prime the reminder-
            # watching mechanism to alert us about it.
            try:
                getNextOccurrenceMethod = self.getNextOccurrence
            except AttributeError:
                pass
            else:
                getNextOccurrenceMethod()
        
    def snoozeReminder(self, reminder, delay):
        """ Snooze this reminder for this long. """
        # Dismiss the original reminder
        originalTime = reminder.getNextReminderTimeFor(self)
        self.dismissReminder(reminder)
        
        # Make a new reminder for this event
        newReminder = Reminder(None, view=self.itsView,
                               snoozedUntil=(datetime.now() + delay))
        self.reminders.add(newReminder)
        return newReminder
