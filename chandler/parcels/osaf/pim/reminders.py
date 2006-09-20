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
from osaf.pim.items import ContentItem, cmpTimeAttribute
from osaf.pim.calendar.Calendar import EventStamp

from datetime import datetime, time, timedelta
from PyICU import ICUtzinfo
import logging
logger = logging.getLogger(__name__)


class Reminder(schema.Item):
    # Make a value we can use for distant (or invalid) reminder times
    farFuture = datetime.max
    if getattr(farFuture, 'tzInfo', None) is None:
        farFuture = farFuture.replace(tzinfo=ICUtzinfo.default)

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
        initialValue=[]
    )

    expiredReminderItems = schema.Sequence(
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
        return self.absoluteTime or \
                getattr(remindable.itsItem, self.relativeTo) \
               or Reminder.farFuture

    def getNextReminderTimeFor(self, remindable):
        """ Get the time for this remindable's next reminder """
        result = self.getBaseTimeFor(remindable)
        if result != Reminder.farFuture:
            result += self.delta
        assert result.tzinfo is not None
        #if result.tzinfo is None:
            #result = result.replace(tzinfo=ICUtzinfo.default)
        logger.debug("next reminder time for %s on %s is %s",
                     self, remindable, result)
        return result

    def __repr__(self):
        return "<%sReminder @ %s>" % (self.userCreated and "User" or "Internal", 
                                      self.absoluteTime or self.delta)

class Remindable(schema.Annotation):
    schema.kindInfo(annotates=ContentItem)
    
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
        copying = schema.Cloud(reminders, expiredReminders),
        sharing = schema.Cloud(
            byCloud = [reminders, expiredReminders]
        )
    )

    @schema.Comparator
    def cmpReminderTime(self, remindable):
        return cmpTimeAttribute(self, remindable, 'reminderFireTime')


    def getUserReminder(self, collectionToo=False, expiredToo=True, skipThis=None):
        attrsToSearch = (expiredToo and (Remindable.reminders,
                                         Remindable.expiredReminders)
                                    or (Remindable.reminders,))
        for attr in attrsToSearch:
            if (self.itsItem.hasLocalAttributeValue(attr.name)):
                collection = getattr(self.itsItem, attr.name)
                for reminder in collection:
                    if reminder.userCreated and reminder is not skipThis:
                        return collectionToo and (collection, reminder) or reminder
        return collectionToo and (None, None) or None

    def makeReminder(self, checkExpired=False, replace=False, **kwds):
        # @@@ I think the proxy code should override calls to this method
        # add a separate reference to this reminder to each generated event,
        # (or something like that). (Remindable.snoozeReminder will call this
        # method; that operation should only affect the actual event, not the
        # series)
        
        # Make the new reminder before we remove the old one, to avoid flicker
        # in the UI.
        if kwds.get('delta') or kwds.get('absoluteTime'):
            # We're creating a new reminder.
            newReminder = Reminder(None, itsView=self.itsItem.itsView, **kwds)
            logger.debug("Adding %s to %s", newReminder, self)

            addThisTo = self.reminders
            if checkExpired:
                nextTime = newReminder.getNextReminderTimeFor(self)
    
                if (nextTime < datetime.now(ICUtzinfo.default)):
                    assert kwds['keepExpired'], "Creating an expired reminder that isn't marked 'keepExpired'?"
                    addThisTo = self.expiredReminders
    
            addThisTo.add(newReminder)
        else:
            # We don't need to create a new reminder, which means we're just
            # replacing an old one with None, right?
            assert replace
            newReminder = None

        # If we're supposed to, replace any old userReminder
        if replace:
            (collection, userReminder) = self.getUserReminder(collectionToo=True, 
                                                              skipThis=newReminder)

            if userReminder is not None:
                logger.debug("Removing %s from %s", userReminder, self)
                collection.remove(userReminder)
                if not (len(userReminder.reminderItems) or \
                        len(userReminder.expiredReminderItems)):
                    userReminder.delete()

        return newReminder

    def dismissReminder(self, reminder, dontExpire=False):
        """ 
        Dismiss this reminder. Normally, we'll decide whether to keep it
        in 'expired' based on its keepExpired attribute, but if dontExpire
        is True, we'll expire it anyway (we use this when unstamping and
        deleting relative reminders).
        """

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
        if dontExpire or not reminder.keepExpired:
            # This is a system or "snooze" reminder, just toss it.
            assert dontExpire or len(reminder.reminderItems) == 0
            assert dontExpire or len(reminder.expiredReminderItems) == 0
            reminder.delete()
        else:
            if not reminder in self.expiredReminders:
                self.expiredReminders.add(reminder)

    def snoozeReminder(self, reminder, delay):
        """ Snooze this reminder for this long. """
        # Make a new reminder for this event
        newReminder = Reminder(None, itsView=self.itsItem.itsView,
                               absoluteTime=(datetime.now(ICUtzinfo.default) +
                                             delay),
                               keepExpired=False,
                               userCreated=False)
        self.reminders.add(newReminder)

        # Dismiss the original reminder
        self.dismissReminder(reminder)

        return newReminder
    
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
        EventStamp = schema.ns("osaf.pim", self.itsItem.itsView).EventStamp
        attrName = EventStamp.effectiveStartTime.name
        assert hasattr(self.itsItem, attrName)
        return self.makeReminder(delta=delta, relativeTo=attrName,
                                 checkExpired=True, keepExpired=True, 
                                 replace=True)


    userReminderInterval = schema.Calculated(
        schema.TimeDelta,
        basedOn=(reminders,),
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
        return self.makeReminder(absoluteTime=absoluteTime, userCreated=True,
                                 checkExpired=True, keepExpired=True, 
                                 replace=True)
    
    userReminderTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(reminders,),
        fget=getUserReminderTime,
        fset=setUserReminderTime,
        doc="User-set absolute reminder time."
    )

    def _getNextReminderAndTime(self):
        """
        Get a tuple containing the time the next unexpired reminder (of any 
        kind) is supposed to fire, and the reminder itself.
        """
        try:
            return min((r.getNextReminderTimeFor(self), r)
                                   for r in self.reminders)
        except ValueError:
            return (Reminder.farFuture, None)
        
    def getNextReminderTuple(self):
        """
        Get a tuple containing (the next unexpired reminder's time, this
        item, and the reminder)
        """
        (when, reminder) = self._getNextReminderAndTime()
        assert not reminder.isDeleted()
        return (when, self, reminder)
        
    def getNextReminderTime(self):
        """
        Get the time the next unexpired reminder (of any kind) is due to fire
        """
        return self._getNextReminderAndTime()[0]
    
    nextReminderTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(EventStamp.startTime, EventStamp.allDay, EventStamp.anyTime,
                 reminders,),
        fget=getNextReminderTime,
        doc="Firing time of this item's next reminder, "
            "or None for no unexpired reminders")

    @schema.observer(reminders)
    def onRemindersChanged(self, op, attr):
        logger.debug("Hey, onRemindersChanged called!")
        self.itsItem.updateRelevantDate(op, attr)
    
    def addRelevantDates(self, dates):
        """
        Subclasses will override this to add relevant dates to this list;
        each should be a tuple, (dateTimeValue, 'attributeName').
        """
        # Add our reminder, if we have one
        reminder = self.getUserReminder(expiredToo=False)
        if reminder is not None:
            dates.append((reminder.getNextReminderTimeFor(self), 'reminder'))
