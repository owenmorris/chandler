
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
        schema.Bytes,
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
        """
        Get the relative-to time for this remindable's next reminder
        so that the UI can generate a message relative to it.
        """
        return getattr(remindable, self.relativeTo, datetime.max)
    
    def getNextReminderTimeFor(self, remindable):
        """ Get the time for this remindable's next reminder """
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
        displayName=u"Reminder Interval",
        basedOn=('reminders'),
        fget=getReminderInterval,
        fset=setReminderInterval,
        doc="Reminder interval, computed from the first unexpired reminder."
    )

    def makeReminder(self, delta, checkExpired=False):
        # @@@ I think the proxy code should override calls to this method
        # add a separate reference to this reminder to each generated event,
        # (or something like that). (Remindable.snoozeReminder will call this
        # method; that operation should only affect the actual event, not the 
        # series)
        newReminder = Reminder(None, delta=delta, view=self.itsView)
        
        addThisTo = self.reminders
        
        if checkExpired:
            nextTime = newReminder.getNextReminderTimeFor(self)
            
            if (nextTime is not None and
                datetimeOp(nextTime, '<', datetime.now())):
                addThisTo = self.expiredReminders
            
        addThisTo.add(newReminder)
        return newReminder

    def dismissReminder(self, reminder):
        """ Dismiss this reminder. """
        
        # Make sure the next one's around, so we'll prime the reminder-
        # watching mechanism to alert us about it. We also check that
        # reminders for past events don't trigger this one.
        now = datetime.now()

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
        newReminder = Reminder(None, view=self.itsView,
                               snoozedUntil=(datetime.now() + delay))
        self.reminders.add(newReminder)
        return newReminder
