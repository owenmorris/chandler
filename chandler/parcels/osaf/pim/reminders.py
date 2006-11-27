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
from osaf.pim.stamping import Stamp, has_stamp

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
    
    # These flags represent what kind of reminder this is:
    # userCreated promptUser
    #   True        True    a relative or absolute user reminder;
    #                       only one of these can exist on an item,
    #                       in its 'reminders' or 'expiredReminders'.
    #   False       True    A 'snooze' reminder.
    #   False       False   An internal reminder relative to the
    #                       the effectiveStartTime of an event, used
    #                       to update its triageStatus when it fires.
    
    userCreated = schema.One(
        schema.Boolean,
        defaultValue=True,
        doc="Is a user-created reminder?"
    )

    promptUser = schema.One(
        schema.Boolean,
        defaultValue=True,
        doc="Should we show this reminder to the user when it goes off?")
    
    reminderItems = schema.Sequence(
        initialValue=[]
    )

    expiredReminderItems = schema.Sequence(
        initialValue=[]
    )

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [absoluteTime, delta, relativeTo, 
                       userCreated, promptUser]
        )
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
        #logger.debug("next reminder time for %s on %s is %s",
                     #self, remindable, result)
        return result

    def __repr__(self):
        return "<%sReminder @ %s>" % (self.userCreated and "User" or 
                                      self.promptUser and "Snooze" or "Internal", 
                                      self.absoluteTime or self.delta)
    
    @classmethod
    def defaultTime(cls):
        """ 
        Something's creating a reminder and needs a default time.
        We'll return 5PM today if that's in the future; otherwise, 8AM tomorrow.
        """    
        # start with today at 5PM
        t = datetime.now(tz=ICUtzinfo.default)\
            .replace(hour=17, minute=0, second=0, microsecond=0)
        now = datetime.now(tz=ICUtzinfo.default)
        if t < now:
            # Make it tomorrow morning at 8AM (eg, 15 hours later)
            t += timedelta(hours=15)
        return t

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
        return cmpTimeAttribute(self, remindable, 'nextReminderTime')


    def getUserReminder(self, refListToo=False, expiredToo=True, skipThis=None):
        """
        Get the user reminder on this item. There's supposed to be only one; 
        it could be relative or absolute.
        
        We'll look in the 'reminders' reflist, and in the 'expiredReminders'
        reflist if expiredToo is set.
        
        instead of just returning the reminder, we can return a
        tuple containing (the reflist we found it in, and the reminder).
        """
        attrsToSearch = (expiredToo and (Remindable.reminders,
                                         Remindable.expiredReminders)
                                    or (Remindable.reminders,))
        for attr in attrsToSearch:
            if (self.itsItem.hasLocalAttributeValue(attr.name)):
                refList = getattr(self.itsItem, attr.name)
                for reminder in refList:
                    if reminder.userCreated and reminder is not skipThis:
                        return refListToo and (refList, reminder) or reminder
        return refListToo and (None, None) or None

    def makeReminder(self, checkExpired=False, replace=False, **kwds):
        """
        Create a new reminder on this item, and optionally:
        - put it in the 'expired' list if this new reminder is already in the 
          past, and/or
        - consider this new reminder a replacement of the existing one.
        (Other keyword options are passed to the Reminder constructor.)
        """        
        # Make the new reminder before we remove the old one, to avoid flicker
        # in the UI.
        if (kwds.get('delta') is not None) or \
           (kwds.get('absoluteTime') is not None):
            # We're creating a new reminder.
            newReminder = Reminder(None, itsView=self.itsItem.itsView, **kwds)
            logger.debug("Adding %s to %s", newReminder, self)

            addThisTo = self.reminders
            event = EventStamp(self)
            isMaster = event.isRecurrenceMaster()
            if checkExpired or isMaster:
                # If this is a recurrence master item, we want to stash the
                # event in its 'expired' list, no matter when it's due (to
                # avoid masters showing up in the itemsWithReminders collection,
                # alongside their occurrences).
                if isMaster:
                    addToExpired = True
                else:
                    # It's not a master -- when's it due?
                    nextTime = newReminder.getNextReminderTimeFor(self)
                    addToExpired = (nextTime < datetime.now(ICUtzinfo.default))
                    
                if addToExpired:
                    addThisTo = self.expiredReminders
    
            addThisTo.add(newReminder)
        else:
            # We don't need to create a new reminder, which means we're just
            # replacing an old one with None, right?
            assert replace
            newReminder = None

        # If we're supposed to, replace any old userReminder
        if replace:
            (refList, userReminder) = self.getUserReminder(refListToo=True, 
                                                           skipThis=newReminder)

            if userReminder is not None:
                logger.debug("Removing %s from %s", userReminder, self)
                refList.remove(userReminder)
                if not (len(userReminder.reminderItems) or \
                        len(userReminder.expiredReminderItems)):
                    userReminder.delete()

        return newReminder

    def dismissReminder(self, reminder, dontExpire=False):
        """ 
        Dismiss this reminder. Normally, we'll decide whether to keep it
        in 'expired' based on its userCreated attribute, but if dontExpire
        is True, we'll expire it anyway (we use this when unstamping and
        deleting relative reminders).
        """

        # If this is an occurrence, make sure the next one's around, so 
        # we'll prime the reminder-watching mechanism to alert us about it. 
        if has_stamp(self, EventStamp):
            event = EventStamp(self)
            assert not event.isRecurrenceMaster(), \
                   "Dismissing a reminder on a recurrence master"
            
            if reminder.userCreated or reminder.absoluteTime is None:
                # Get the next occurrence of this event. We
                # don't need to do anything with it; we just
                # want to make sure it's been instantiated
                # so that the next reminder will fire.
                event.getNextOccurrence(after=datetime.now(ICUtzinfo.default))

        # Remove the reminder from the pending list
        if reminder in self.reminders:
            self.reminders.remove(reminder)
            
        # If this was a user-created reminder, add it to the expired list,
        # unless we were told not to (because the user is deleting it)
        if dontExpire or not reminder.userCreated:
            # This is a triageStatus or "snooze" reminder, just toss it.
            assert dontExpire or len(reminder.reminderItems) == 0
            assert dontExpire or len(reminder.expiredReminderItems) == 0
            reminder.delete()
        elif not reminder in self.expiredReminders:
            self.expiredReminders.add(reminder)

    def snoozeReminder(self, reminder, delay):
        """ Snooze this reminder for this long. """
        # Make a new reminder for this event
        newReminder = Reminder(None, itsView=self.itsItem.itsView,
                               absoluteTime=(datetime.now(ICUtzinfo.default) +
                                             delay),
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
        attrName = EventStamp.effectiveStartTime.name
        assert hasattr(self.itsItem, attrName)
        return self.makeReminder(delta=delta, relativeTo=attrName,
                                 checkExpired=True, replace=True)


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
                                 checkExpired=True, replace=True)
    
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
    
    # @@@ (This Calculated attribute is used for indexing the itemsWithReminders
    # collection - it probably oughta be rewritten to avoid loading the items)
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
        self.itsItem.updateDisplayDate(op, attr)
    
    def addDisplayDates(self, dates):
        """
        Subclasses will override this to add relevant dates to this list;
        each should be a tuple, (dateTimeValue, 'attributeName').
        """
        # Add our reminder, if we have one
        reminder = self.getUserReminder(expiredToo=True)
        if reminder is not None:
            reminderTime = reminder.getNextReminderTimeFor(self)
            if reminderTime is not None:
                dates.append((reminderTime, 'reminder'))
