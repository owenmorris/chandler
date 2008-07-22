#   Copyright (c) 2003-2008 Open Source Applications Foundation
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
from chandlerdb.item.c import isitemref
from chandlerdb.util.c import Empty
from PyICU import ICUtzinfo

from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)

DEAD_FLAGS = (schema.Item.STALE | schema.Item.DELETING | schema.Item.DEFERRING |
              schema.Item.DEFERRED)

def isDead(item):
    """
    Return True if the item is None, an itemref, stale, or deferred.
    
    """
    return (item is None or isitemref(item) or
            (item.itsStatus & DEAD_FLAGS) != 0
           )


class PendingReminderEntry(schema.Item):
    """
    A C{PendingReminderEntry} represents a reminder that has fired for some
    item, but has not yet been dismissed by the user. (In other words, for
    user-visible reminders, this what would be shown in some kind of dialog).
    
    This class is also used to implement "snooze": when the user snoozes a
    reminder, the 'when' of the corresponding PendingReminderEntry is
    updated to the new 'wakeup' time; it's up to client code to avoid
    displaying the entry till that time rolls around.
    """

    item = schema.One(
        schema.Item,
        doc="The Item this reminder entry pertains to",
    )
    
    when = schema.One(
        schema.DateTimeTZ,
        doc="When the reminder should fire for this Item",
    )
    
    reminder = schema.One()
    
    snoozed = schema.One(
        schema.Boolean,
        doc="Has this item ever been snoooooozed?",
        defaultValue=False,
    )


class Reminder(schema.Item):
    """
    The base class for reminders. Note that this only supports 'custom'
    (fixed-time) reminders; the more familiar relative reminders are
    defined in Calendar.py on as RelativeReminder. This resolves some
    unfortunate circular import dependency issues we had in the past.
    """
    # Make values we can use for distant (or invalid) reminder times
    farFuture = datetime.max
    if farFuture.tzinfo is None:
        farFuture = farFuture.replace(tzinfo=ICUtzinfo.getInstance('UTC'))
    distantPast = datetime.min
    if distantPast.tzinfo is None:
        distantPast = distantPast.replace(tzinfo=ICUtzinfo.getInstance('UTC'))
    
    absoluteTime = schema.One(
        schema.DateTimeTZ,
        defaultValue=None,
        doc="If set, overrides relativeTo as the base time for this reminder"
    )

    # These flags represent what kind of reminder this is:
    # userCreated promptUser
    #   True        True    a relative or absolute user reminder, usually
    #                       created in the detail view (or possibly, imported
    #                       as ICalendar)
    #   False       False   An internal reminder relative to the
    #                       the effectiveStartTime of an event, used
    #                       to update its triageStatus when it fires.
    #
    # @@@ [grant] For now, userCreated and promptUser are identical... It's
    # not so clear to me whether we need both.
    #
    
    userCreated = schema.One(
        schema.Boolean,
        defaultValue=True,
        doc="Is a user-created reminder?"
    )

    promptUser = schema.One(
        schema.Boolean,
        defaultValue=True,
        doc="Should we show this reminder to the user when it goes off?")
    
    reminderItem = schema.One(
        defaultValue=None,
    )

    pendingEntries = schema.Sequence(
        PendingReminderEntry,
        defaultValue=Empty,
        inverse=PendingReminderEntry.reminder,
        doc="What user-created reminders have fired, and not been " \
            "dismissed or snoozed?"
    )
    
    nextPoll = schema.One(
        schema.DateTimeTZ,
        doc="When next will something interesting happen with this reminder?" \
            "Set to reminder.farFuture if this reminder has expired.",
        defaultValue=None,
    )
    
    description = schema.One(
        schema.Text,
        doc="End-user text description of this reminder. Currently unused by "
            "Chandler.",
    )

    duration = schema.One(
        schema.TimeDelta,
        doc="Reminder DURATION (a la ICalendar VALARM); unused by Chandler.",
        defaultValue=timedelta(0),
    )
    repeat = schema.One(
        schema.Integer,
        doc="Reminder REPEAT (a la ICalendar VALARM); unused by Chandler.",
        defaultValue=0,
    )

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [absoluteTime, userCreated, promptUser]
        ),
        copying = schema.Cloud(
            literal = [absoluteTime, userCreated, promptUser, nextPoll]
        )
    )

    def onItemDelete(self, view, deferring):
        if self.pendingEntries:
            pending = list(self.pendingEntries)
            self.pendingEntries.clear()
            for entry in pending:
                entry.delete(recursive=True)

    def updatePending(self, when=None):
        """
        The method makes sure that the Reminder's list of
        PendingReminderEntries is up-to-date. This involves adding new
        entries to the list, via the Remindable.reminderFired() method.
        Also, the C{nextPoll} attribute is updated to the next time
        something interesting will happen (i.e. another item should be
        reminded); this may be C{Reminder.farFuture} if the C{Reminder}
        has no more items to process.
        
        @param when: The time to update to. You can pass C{None}, in which
                     case C{datetime.now()} is used.
        @type when: C{datetime}.
        """
        if when is None:
            when = datetime.now(self.itsView.tzinfo.default)

        if self.nextPoll is None:
            # No value for nextPoll means we've just been initialized.
            # If we're in the past, we treat ourselves as expired.
                
            if self.absoluteTime >= when:
                self.nextPoll = self.absoluteTime
            else:
                self.nextPoll = self.farFuture
                
        if self.nextPoll != self.farFuture and when >= self.absoluteTime:
            self.reminderItem.reminderFired(self, self.absoluteTime)
            self.nextPoll = self.farFuture
            
        self._checkExpired()

    def _checkExpired(self):
        if self.isExpired() and not self.userCreated:
            self.delete(True)

    def dismissItem(self, item):
        pendingEntries = self.pendingEntries
        toDismiss = list(p for p in pendingEntries if p.item is item)
        assert len(toDismiss), "Attempt to dismiss item non-pending item %r" % (
                               item)

        for item in toDismiss:
            item.delete(recursive=True)
            
        if not self.pendingEntries:
            self.nextPoll = self.farFuture

        self._checkExpired()
                

    def snoozeItem(self, item, delta):
        nextPoll = self.nextPoll
        pendingEntries = self.pendingEntries
        toSnooze = list(p for p in pendingEntries if p.item is item)
        assert len(toSnooze), "Attempt to snooze item non-pending item %r" % (
                               item)

        when = datetime.now(self.itsView.tzinfo.default) + delta
        for item in toSnooze:
            item.when = when
            item.snoozed = True
            nextPoll = min(nextPoll, item.when)
            
        self.nextPoll = nextPoll
        
    def getItemBaseTime(self, item):
        """
        Return the time we would fire for this item (independent of
        if it has been snoozed?)
        """
        return self.absoluteTime or Reminder.farFuture
        
    getReminderTime = getItemBaseTime
        
    def isExpired(self):
        return (not self.pendingEntries and
                self.nextPoll is not None
                and self.nextPoll >= Reminder.farFuture)
        
        
    @schema.observer(reminderItem)
    def reminderItemChanged(self, op, attr):
        if op == 'remove':
            if self.pendingEntries:
                # @@@ [grant] Check this!
                toRemove = list(p for p in self.pendingEntries
                                if isDead(p.item))
            
                for pending in toRemove:
                    self.pendingEntries.remove(pending)
                    
            if not self.pendingEntries:
                self.delete(True)

    @classmethod
    def defaultTime(cls, view):
        """ 
        Something's creating a reminder and needs a default time.
        We'll return 5PM today if that's in the future; otherwise, 8AM tomorrow.
        """    
        # start with today at 5PM
        t = datetime.now(tz=view.tzinfo.default)\
            .replace(hour=17, minute=0, second=0, microsecond=0)
        now = datetime.now(tz=view.tzinfo.default)
        if t < now:
            # Make it tomorrow morning at 8AM (eg, 15 hours later)
            t += timedelta(hours=15)
        return t

    @classmethod
    def getPendingTuples(cls, view, when):
        """
        Return a list of all reminder tuples with fire times in the past, 
        sorted by reminder time.

        Each tuple contains (reminderTime, remindable, reminder).
        """

        allFutureReminders = schema.ns('osaf.pim', view).allFutureReminders
        
        remindersToPoll = []
        for reminder in allFutureReminders.iterindexvalues('reminderPoll'):
            if reminder.nextPoll is None or reminder.nextPoll <= when:
                remindersToPoll.append(reminder)
            else:
                break

        for reminder in remindersToPoll:
            reminder.updatePending(when)

        pendingKind = PendingReminderEntry.getKind(view)
        trash = schema.ns("osaf.pim", view).trashCollection
        resultTuples = []
        
        for entry in pendingKind.iterItems():
            thisTuple = tuple(getattr(entry, attr, None)
                               for attr in ('when', 'item', 'reminder'))
            # Show everything except reminders in the trash, and
            # reminders that have been snoozed into the future. Also,
            # don't return any "dead" items in the tuple, and check
            # for missing attributes (bug 11415).
            if (thisTuple[0] is not None and
                not isDead(thisTuple[1]) and
                not isDead(thisTuple[2]) and
                not thisTuple[1] in trash and
                not (entry.snoozed and thisTuple[0] > when)):

                resultTuples.append(thisTuple)
                                
        resultTuples.sort(key=lambda t: t[0])
        return resultTuples


class Remindable(schema.Item):
    reminders = schema.Sequence(
        Reminder,
        inverse=Reminder.reminderItem,
        defaultValue=Empty,
    )

    schema.addClouds(
        copying = schema.Cloud(reminders),
        sharing = schema.Cloud(
            byCloud = [reminders]
        )
    )

    def InitOutgoingAttributes(self):
        pass

    def onItemDelete(self, view, deferring):
        for rem in self.reminders:
            rem.delete(recursive=True)
    
    def getUserReminder(self, expiredToo=True):
        """
        Get the user reminder on this item. There's supposed to be only one; 
        it could be relative or absolute.
        
        We'll look in the 'reminders' reflist, and allow expired reminders
        only if expiredToo is set to False.
        """
        # @@@ Note: This code is reimplemented in the index for the dashboard
        # calendar column: be sure to change that if you change this!
        for reminder in self.reminders:
            if reminder.userCreated:
                if expiredToo or not reminder.isExpired():
                    return reminder

    # @@@ Note: 'Calculated' APIs are provided for only absolute user-set
    # reminders. Relative reminders, which currently can only apply to
    # EventStamp instances, can be set via similar APIs on EventStamp.
    # Currently only one reminder (which can be of either
    # flavor) can be set right now. The 'set' functions can replace an existing
    # reminder of either flavor, but the 'get' functions ignore (that is, return
    # 'None' for) reminders of the wrong flavor.
    
    def getUserReminderTime(self):
        userReminder = self.getUserReminder()
        if userReminder is None or userReminder.absoluteTime is None:
            return None
        return userReminder.absoluteTime

    def setUserReminderTime(self, absoluteTime):
        existing = self.getUserReminder()
        if absoluteTime is not None:
            retval = Reminder(itsView=self.itsView, absoluteTime=absoluteTime,
                              reminderItem=self)
        else:
            retval = None

        if existing is not None:
            existing.delete(recursive=True)
            
        return retval
    
    userReminderTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(reminders,),
        fget=getUserReminderTime,
        fset=setUserReminderTime,
        doc="User-set absolute reminder time."
    )

    @schema.observer(reminders)
    def onRemindersChanged(self, op, attr):
        logger.debug("Hey, onRemindersChanged called!")
        self.updateDisplayDate(op, attr)
    
    def addDisplayDates(self, dates, now):
        """
        Subclasses will override this to add relevant dates to this list;
        each should be a tuple, (priority, dateTimeValue, 'attributeName').
        """
        # Add our reminder, if we have one
        reminder = self.getUserReminder()
        if reminder is not None:
            reminderTime = reminder.getReminderTime(self)
            # displayDate should be base time for RelativeReminder, bug 12246
            # for absolute reminders, getItemBaseTime matches reminderTime
            displayDate = reminder.getItemBaseTime(self)
            if reminderTime not in (None, Reminder.farFuture):
                dates.append((30 if reminderTime < now else 10, displayDate,
                              'reminder'))
                              
    def reminderFired(self, reminder, when):
        """
        Called when a reminder's fire date (whether snoozed or not)
        rolls around. This is overridden by subclasses; e.g. ContentItem
        uses it to set triage status, whereas Occurrence makes sure that
        the triage status change is a THIS change.
        
        The Remindable implementation makes sure that a
        PendingReminderEntry is created, if necessary, if reminder is
        userCreated.
        """
        for pending in reminder.pendingEntries:
            if pending.item is self:
                break
        else:
            if reminder.userCreated:
                # No matching item, so add one
                pending = PendingReminderEntry(itsView=self.itsView, item=self,
                                               reminder=reminder, when=when)
            else:
                pending = None

        return pending
    


