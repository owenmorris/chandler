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


"""Classes used for Calendar parcel kinds.
   @group Main classes: EventStamp, CalendarEvent, Location,
   TimeTransparencyEnum
   @group Unused classes: Calendar, ModificationEnum, RecurrencePattern
"""

__parcel__ = "osaf.pim.calendar"

import application

from application import schema
from osaf.pim.contacts import Contact
from osaf.pim.items import ContentItem, cmpTimeAttribute
from osaf.pim.stamping import Stamp, has_stamp
from osaf.pim.notes import Note
from osaf.pim.calendar import Recurrence
from osaf.pim.collections import FilteredCollection

from TimeZone import formatTime
from osaf.pim.calendar.TimeZone import coerceTimeZone, TimeZoneInfo
from osaf.pim.calendar import DateTimeUtil
from PyICU import DateFormat, DateFormatSymbols, ICUtzinfo
from datetime import datetime, time, timedelta
import itertools
import StringIO
import logging
from util import indexes
import operator

from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)
DEBUG = logger.getEffectiveLevel() <= logging.DEBUG

class TimeTransparencyEnum(schema.Enumeration):
    """
    The iCalendar values for Time Transparency are slightly different, iCalendar
    has Cancelled, Chandler has fyi.

    """

    values="confirmed", "tentative", "fyi"

class ModificationEnum(schema.Enumeration):
    values="this", "thisandfuture"

def findUID(view, uid):
    """
    Return the master event whose icalUID matched uid, or None.
    """
    events = EventStamp.getCollection(view)
    eventItem = indexes.valueLookup(events, 'icalUID', EventStamp.icalUID.name, uid)
    if eventItem is None:
        return None
    else:
        return EventStamp(eventItem).getMaster()

def ensureIndexed(coll):
    if not coll.hasIndex('__adhoc__'):
        coll.addIndex('__adhoc__', 'numeric')


zero_delta = timedelta(0)
LONG_TIME  = timedelta(7)

def getKeysInRange(view, startVal, startAttrName, startIndex, startColl,
                         endVal,   endAttrName,   endIndex,   endColl,
                         filterColl = None, filterIndex = None, useTZ=True,
                         longDelta=None, longCollection=None):
    """
    Yield keys for events occurring between startVal and endVal.  Don't load
    items, just yield relevant keys, sorted according to startIndex.

    endIndex is needed to determine whether or not events starting before
    startVal also end before startVal.

    startIndex, endIndex, and filterIndex are the names (strings) of
    indexes on the relevant collections.

    If longDelta is present, the range checked will be constrained to look for
    events within longDelta of (startVal, endVal), supplemented as appropriate
    with any events in longCollection.  startIndex and endIndex must exist
    on longCollection.

    """
    # callbacks to use for searching the indexes
    def mStart(key, delta=None):
        # gets the last item starting before endVal, or before startVal - delta
        if delta is None:
            delta = zero_delta
        else:
            delta = delta + endVal - startVal
        testVal = getattr(EventStamp(view[key]), startAttrName)
        if testVal is None:
            return -1 # interpret None as negative infinity
        # note that we're NOT using >=, if we did, we'd include all day
        # events starting at the beginning of the next week
        if useTZ:
            if endVal - delta > testVal:
                return 0
        else:
            if endVal.replace(tzinfo=None) - delta > testVal.replace(tzinfo=None):
                return 0
        return -1

    def mEnd(key, delta=None):
        # gets the first item ending after startVal, or after endVal + delta
        if delta is None:
            delta = zero_delta
        else:
            delta = delta + endVal - startVal
        testVal = getattr(EventStamp(view[key]), endAttrName)

        if getattr(EventStamp(view[key]), startAttrName) == testVal:
            # zero duration events should be included, other events ending at
            # start time shouldn't be
            compare = operator.le
        else:
            compare = operator.lt

        if testVal is None:
            return 0 # interpret None as positive infinity, thus, a match
        if useTZ:
            if compare(startVal + delta, testVal):
                return 0
        else:
            if compare(startVal.replace(tzinfo=None) + delta,
                       testVal.replace(tzinfo=None)):
                return 0
        return 1

    lastStartKey = startColl.findInIndex(startIndex, 'last', mStart)
    if lastStartKey is None:
        return #there were no keys starting before end
    if longDelta is not None:
        firstStartKey = startColl.findInIndex(startIndex, 'last',
                                    lambda key: mStart(key, longDelta))
    else:
        firstStartKey = None

    firstEndKey = endColl.findInIndex(endIndex, 'first', mEnd)
    if firstEndKey is None:
        return #there were no keys ending after start
    if longDelta is not None:
        lastEndKey = endColl.findInIndex(endIndex, 'first',
                                         lambda key: mEnd(key, longDelta))
    else:
        lastEndKey = None

    if filterColl is not None:
        _filterIndex = filterColl.getIndex(filterIndex)

    keys = set(endColl.iterindexkeys(endIndex, firstEndKey, lastEndKey))
    ignores = []
    # first, yield long events, calculated by recursing, look at longCollection
    if longCollection is not None:
        for key in getKeysInRange(view, startVal, startAttrName, startIndex,
                         longCollection, endVal, endAttrName, endIndex,
                         longCollection, filterColl, filterIndex, useTZ):
            ignores.append(key)
            yield key

    # next, generate normal keys
    for key in startColl.iterindexkeys(startIndex, firstStartKey, lastStartKey):
        if key in keys and (filterColl is None or key in _filterIndex) \
           and key not in ignores:
            yield key

def isDayEvent(event):
    """
    Determines whether an event has "dayness"; i.e. whether you would want
    to display it at a specific start time or not.
    
    @param event: The event you're interested in
    @type event: C{EventStamp}
    """
    return getattr(event, 'anyTime', False) or getattr(event, 'allDay', False)

def eventsInRange(view, start, end, filterColl = None, dayItems=True,
                  timedItems=True):
    """
    An efficient generator to find all the items to be displayed
    between date and nextDate. This returns only actual events in the
    collection, and does not yield recurring event occurences, including
    masters.

    The trick here is to use indexes on startTime/endTime to make
    sure that we don't access (and thus load) items more than we
    have to.

    We're looking for the intersection of:
    [All items that end after date] and
    [All items that start after nextDate]

    We find these subsets by looking for the first/last occurrence
    in the index of the end/starttime, and taking the first/last
    items from that list. This gives us two lists, which we intersect.

    """
    tzprefs = schema.ns('osaf.app', view).TimezonePrefs
    if tzprefs.showUI:
        startIndex = 'effectiveStart'
        endIndex   = 'effectiveEnd'
    else:
        startIndex = 'effectiveStartNoTZ'
        endIndex   = 'effectiveEndNoTZ'

    allEvents  = EventStamp.getCollection(view)
    longEvents = schema.ns("osaf.pim", view).longEvents
    keys = getKeysInRange(view, start, 'effectiveStartTime', startIndex,
                          allEvents, end,'effectiveEndTime', endIndex,
                          allEvents, filterColl, '__adhoc__', tzprefs.showUI,
                          longDelta = LONG_TIME, longCollection=longEvents)
    for key in keys:
        event = EventStamp(view[key])
        # Should probably assert has_stamp(event, EventStamp)
        if (has_stamp(event, EventStamp) and
            event.rruleset is None and
            ((dayItems and timedItems) or isDayEvent(event) == dayItems)):
            yield event

def recurringEventsInRange(view, start, end, filterColl = None,
                           dayItems = True, timedItems = True):
    """
    Yield all recurring events between start and end that appear in filterColl.
    """

    tzprefs = schema.ns('osaf.app', view).TimezonePrefs
    if tzprefs.showUI:
        startIndex = 'effectiveStart'
        endIndex   = 'recurrenceEnd'
    else:
        startIndex = 'effectiveStartNoTZ'
        endIndex   = 'recurrenceEndNoTZ'

    pim_ns = schema.ns("osaf.pim", view)
    masterEvents = pim_ns.masterEvents
    keys = getKeysInRange(view, start, 'effectiveStartTime', startIndex,
                          masterEvents, end, 'recurrenceEnd', endIndex,
                          masterEvents, filterColl, '__adhoc__')
    for key in keys:
        masterEvent = EventStamp(view[key])
        for event in masterEvent.getOccurrencesBetween(start, end):
            # One or both of dayItems and timedItems must be
            # True. If both, then there's no need to test the
            # item's day-ness.  If only one is True, then
            # dayItems' value must match the return of
            # isDayEvent.
            if ((event.occurrenceFor is not None) and
                ((dayItems and timedItems) or
                 isDayEvent(event) == dayItems)):
                    yield event

class Location(ContentItem):
    """Stub Kind for Location."""


    eventsAtLocation = schema.Sequence(
    ) # inverse of EventStamp.location


    @classmethod
    def getLocation (cls, view, locationName):
        """
        Factory Method for getting a Location.

        Lookup or create a Location based on the supplied name string.

        If a matching Location object is found in the repository, it
        is returned.  If there is no match, then a new item is created
        and returned.

        @param locationName: name of the Location
        @type locationName: C{String}
        @return: C{Location} created or found
        """
        # make sure the locationName looks reasonable
        assert locationName, "Invalid locationName passed to getLocation factory"
        locations = schema.ns('osaf.pim', view).locations

        def callback(key):
            return cmp(locationName, view[key].displayName)

        existing = locations.findInIndex('locationName', 'exact', callback)
        if existing is not None:
            return view[existing]
        else:
            # make a new Location
            newLocation = Location(itsView=view)
            newLocation.displayName = locationName
            return newLocation



class EventStamp(Stamp):
    """
    EventStamp is the bag of Event-specific attributes. Like other Stamp
    subclasses, an Item can have values for these attributes without
    "having" the stamp; you have to call the add() method to make the
    stamp be present.

    @group Main Public Methods: changeThis, changeThisAndFuture, setRuleFromDateUtil,
    getLastUntil, getRecurrenceEnd, getMaster, createDateUtilFromRule,
    getNextOccurrence, getOccurrencesBetween, getExistingOccurrence, getFirstOccurrence
    getRecurrenceID, deleteThis, deleteThisAndFuture, deleteAll,
    removeRecurrence, isCustomRule, getCustomDescription, isAttributeModifiable

    @group Comparison Methods for Indexing: cmpStartTime,
    cmpEndTime, cmpRecurEnd

    @group Semi-Private Methods: changeNoModification,
    cleanRule, copyCollections, getEffectiveEndTime, getEffectiveStartTime,
    getEndTime, getFirstInRule, InitOutgoingAttributes, isBetween, isProxy,
    moveCollections, moveRuleEndBefore, onEventChanged, removeFutureOccurrences,
    setEndTime, updateRecurrenceEnd, __init__

    """

    schema.kindInfo(annotates=Note)
    
    __use_collection__ = True
    
    @classmethod
    def getCollection(cls, view):
        coll = super(EventStamp, cls).getCollection(view)
        
        try:
            # See if we created a child filter already ...
            return coll['filtered']
        except KeyError:
            # OK, so go ahead and create one
            filterExpression="not view.findValue(uuid, '%s', False)" % (
                                EventStamp.isGenerated.name)
            result = FilteredCollection('filtered', coll,
                        source=coll,
                        filterExpression=filterExpression,
                        filterAttributes=[EventStamp.isGenerated.name])
        return result

    startTime = schema.One(
        schema.DateTimeTZ,
        indexed=True,
        doc="For items that represent *only* Tasks, this attribute serves as "
            "the 'Do-on' attribute. For items that represent only Calendar "
            "Events, this attribute serves as the 'Start-time' attribute. "
            "I think this unified attribute may match the way iCalendar "
            "models these attributes, but we should check to make sure. "
            "- Brian"
    )

    duration = schema.One(
        schema.TimeDelta,
        doc="Duration.")

    recurrenceID = schema.One(
        schema.DateTimeTZ,
        defaultValue=None,
        doc="Date time this occurrence was originally scheduled. startTime and "
            "recurrenceID match for everything but modifications"
    )

    allDay = schema.One(
        schema.Boolean,
        initialValue=False
    )

    anyTime = schema.One(
        schema.Boolean,
        initialValue=True
    )

    transparency = schema.One(
        TimeTransparencyEnum,
        initialValue="confirmed"
    )

    location = schema.One(
        Location,
        inverse=Location.eventsAtLocation,
        doc="We might want to think about having Location be just a 'String', "
            "rather than a reference to a 'Location' item.",
        indexed=True
     ) # inverse of Location.eventsAtLocation

    rruleset = schema.One(
        Recurrence.RecurrenceRuleSet,
        doc="Rule or rules for when future occurrences take place",
        inverse=Recurrence.RecurrenceRuleSet.events,
        defaultValue=None
    )

    organizer = schema.One(
        Contact,
        inverse=Contact.organizedEvents
    )

    participants = schema.Sequence(
        Contact,
        inverse=Contact.participatingEvents
    )

    icalUID = schema.One(
        schema.Text,
        doc="iCalendar uses arbitrary strings for UIDs, not UUIDs.  We can "
            "set UID to a string representation of UUID, but we need to be "
            "able to import iCalendar events with arbitrary UIDs."
    )

    modifies = schema.One(
        ModificationEnum,
        defaultValue=None,
        doc = "Describes whether a modification applies to future events, or "
              "just one event"
    )

    modifications = schema.Sequence(
        doc = "A list of occurrences that have been modified",
        defaultValue=None,
    ) # inverse of modificationFor

    modificationFor = schema.One(
        defaultValue=None,
        inverse=modifications
    )

    occurrences = schema.Sequence(
        defaultValue=None,
    ) # inverse = occurrenceFor

    occurrenceFor = schema.One(
        defaultValue=None,
        inverse=occurrences
    )

    isGenerated = schema.One(
        schema.Boolean,
        defaultValue=False
    )

    isFreeBusy = schema.One(
        schema.Boolean,
        defaultValue=False
    )

    recurrenceEnd = schema.One(
        schema.DateTimeTZ,
        defaultValue = None,
        doc="End time for recurrence, or None, kept up to date by "
            "onEventChanged.  Note that this attribute is only meaningful "
            "on master events")

    schema.addClouds(
        copying = schema.Cloud(organizer,location,rruleset,participants),
        sharing = schema.Cloud(
            startTime, duration, allDay, location, anyTime, modifies,
            transparency, isGenerated, recurrenceID, icalUID,
            byCloud = [organizer, participants, modifications, rruleset,
                occurrenceFor]
        )
    )
    
    IGNORE_CHANGE_ATTR = "%s.EventStamp.__ignoreValueChange" % (__module__,)

    # Redirections

    #whoFrom = schema.One(redirectTo="organizer")
    summary = schema.One(redirectTo="displayName")

    def __disableRecurrenceChanges(self):
        item = self.itsItem
        disable = not getattr(item, EventStamp.IGNORE_CHANGE_ATTR, False)
        if disable:
            setattr(item, EventStamp.IGNORE_CHANGE_ATTR, True)
        return disable
        
    def __enableRecurrenceChanges(self):
        item = self.itsItem
        delattr(item, EventStamp.IGNORE_CHANGE_ATTR)
            
                        

    def InitOutgoingAttributes(self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        self.itsItem.InitOutgoingAttributes()
        self.summary = _(u"New Event")



    def add(self):
        """
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        disabled = self.__disableRecurrenceChanges()
        super(EventStamp, self).add()
        if disabled: self.__enableRecurrenceChanges()
        
        if not hasattr(self, 'startTime'):
            # start at the nearest half hour, duration of an hour
            defaultTz = TimeZoneInfo.get(self.itsItem.itsView).default
            now = datetime.now(defaultTz)
            roundedTime = time(hour=now.hour, minute=(now.minute/30)*30,
                               tzinfo = defaultTz)
            self.startTime = datetime.combine(now, roundedTime)
        if not hasattr(self, 'duration'):
            self.duration = timedelta(hours=1)

        # set the organizer to "me"
        if not hasattr(self, 'organizer'):
            self.organizer = schema.ns("osaf.pim", self.itsItem.itsView).currentContact.item

        if not hasattr(self, 'icalUID'):
            self.icalUID = unicode(self.itsItem.itsUUID)

        # TBD - set participants to any existing "who"
        # participants are currently not implemented.

    def remove(self):
        """
        Override remove to deal with unstamping EventStamp on
        recurring events.

        When removing EventStamp, first add the item's recurrenceID
        to the exclusion list, so the item doesn't reappear after unstamping.

        """
        didDisable = self.__disableRecurrenceChanges()

        rruleset = self.rruleset
        self.occurrenceFor = None
        self.rruleset = None
        
        if rruleset is not None:
            if getattr(rruleset, 'exdates', None) is None:
                rruleset.exdates=[]
            rruleset.exdates.append(self.recurrenceID)
            
        if didDisable:
            self.__enableRecurrenceChanges()

            # Delete any relative user reminders, as well as any startTime
            # triageStatus transition reminders
            from osaf.pim.reminders import Remindable
            remindable = Remindable(self)
            doomed = iter(r for r in remindable.reminders
                          if ((r.userCreated and r.absoluteTime is None) or 
                              (not r.userCreated and r.keepExpired)))
            moreDoomed = iter(r for r in remindable.expiredReminders
                              if r.absoluteTime is None)
            for r in itertools.chain(doomed, moreDoomed):
                logger.debug("Destroying obsolete %s on %s", r, self)
                remindable.dismissReminder(r, dontExpire=True)

        super(EventStamp, self).remove()

    def getTimeDescription(self):
        """
        Get a description of the time components of this event; it'll be
        used in the static presentation in the detail view, and maybe in
        our initial cut at invitations.
        """
        if self.duration == timedelta(0): # @time
            fmt = _(u'%(startDay)s, %(startDate)s at %(startTimeTz)s%(recurrenceSeparator)s%(recurrence)s')
        else:
            sameDate = self.endTime.date() == self.startTime.date()
            if self.anyTime:
                fmt = (sameDate and _(u'%(startDay)s, %(startDate)s any time%(recurrenceSeparator)s%(recurrence)s')
                       or _(u'%(startDate)s - %(endDate)s, any time%(recurrenceSeparator)s%(recurrence)s'))
            elif self.allDay:
                fmt = (sameDate and _(u'%(startDay)s, %(startDate)s all day%(recurrenceSeparator)s%(recurrence)s')
                       or _(u'%(startDate)s - %(endDate)s all day%(recurrenceSeparator)s%(recurrence)s'))
            else:
                fmt = (sameDate and _(u'%(startDay)s, %(startDate)s %(startTime)s - %(endTimeTz)s%(recurrenceSeparator)s%(recurrence)s')
                       or _(u'%(startDay)s, %(startDate)s %(startTime)s - %(endDay)s, %(endDate)s %(endTimeTz)s%(recurrenceSeparator)s%(recurrence)s'))

        recurrenceDescription = self.getCustomDescription()
        # @@@ this could probably be made 'lazy', to only format the values we need...
        return fmt % {
            'startDay': DateTimeUtil.weekdayName(self.startTime),
            'startDate': DateTimeUtil.mediumDateFormat.format(self.startTime),
            'startTime': DateTimeUtil.shortTimeFormat.format(self.startTime),
            'startTimeTz': formatTime(self.startTime),
            'endDay': DateTimeUtil.weekdayName(self.endTime),
            'endDate': DateTimeUtil.mediumDateFormat.format(self.endTime),
            'endTime': DateTimeUtil.shortTimeFormat.format(self.endTime),
            'endTimeTz': formatTime(self.endTime),
            'recurrenceSeparator': recurrenceDescription and _(u', ') or u'',
            'recurrence': recurrenceDescription,
        }

    timeDescription = schema.Calculated(
        schema.Text,
        basedOn=(startTime, duration, rruleset),
        fget=getTimeDescription,
        doc="A human-readable description of the time-related attributes.",
    )

    def getEndTime(self):
        if (self.itsItem.hasLocalAttributeValue(EventStamp.startTime.name) and
            self.itsItem.hasLocalAttributeValue(EventStamp.duration.name)):
            return self.startTime + self.duration
        else:
            return None

    def setEndTime(self, dateTime):
        if self.itsItem.hasLocalAttributeValue(EventStamp.startTime.name):
            duration = dateTime - self.startTime
            if duration < timedelta(0):
                raise ValueError, "End time must not be earlier than start time"
            self.duration = duration

    endTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(startTime, duration),
        fget=getEndTime,
        fset=setEndTime,
        doc="End time, computed from startTime + duration."
    )


    def getEffectiveStartTime(self):
        """
        Get the effective start time of this event: ignore the time
        component of the startTime attribute if this is an allDay
        or anyTime event.
        """
        # Return None if we're not valid (eg, during stamping)
        startTime = getattr(self, 'startTime', None)
        anyTime = getattr(self, 'anyTime', None)
        allDay = getattr(self, 'allDay', None)        
        if None in (startTime, anyTime, allDay):
            return None
        
        if anyTime or allDay:
            startOfDay = time(0, tzinfo=ICUtzinfo.floating)
            return datetime.combine(startTime, startOfDay)
        else:
            return startTime

    effectiveStartTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(startTime, allDay, anyTime),
        fget=getEffectiveStartTime,
        doc="Start time, without time if allDay/anyTime")

    def getEffectiveEndTime(self):
        """
        Get the effective end time of this event: ignore the time
        component of the endTime attribute if this is an allDay
        or anyTime event.
        """
        allDay = self.anyTime or self.allDay
        endTime = self.endTime
        if endTime is None:
            start = self.effectiveStartTime
            if allDay and start is not None:
                return start + timedelta(1)
            else:
                return start
        elif allDay:
            # all day events include their endtime, so they end at midnight
            # one day later than their normal end date.
            return datetime.combine(endTime + timedelta(1),
                                    time(0, tzinfo=endTime.tzinfo))
        else:
            return endTime

    effectiveEndTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(startTime, allDay, anyTime, duration),
        fget=getEffectiveEndTime,
        doc="End time, without time if allDay/anyTime")

    @schema.observer(startTime, allDay, anyTime)
    def onStartTimeChanged(self, op, name):
        from osaf.pim.reminders import Remindable
        # Update the reminder we use to update triageStatus at startTime, 
        # if it's in the future. First, find any existing startTime reminder.
        existing = [r for r in getattr(Remindable(self), 'reminders', [])
                      if not r.userCreated]
        assert len(existing) <= 1
        existing = len(existing) and existing[0] or None
        assert not existing or existing.absoluteTime is not None
        
        try:
            newStartTime = self.effectiveStartTime
        except AttributeError:
            pass
        else:
            # @@@ For now, occurrences don't handle individual values right,
            # so don't do this if the event is a member of a recurrence set.
            # (see bug 6701)
            if not self.isRecurring() and \
               newStartTime is not None and \
               newStartTime >= datetime.now(tz=ICUtzinfo.default):
                # It's due, or in the future.
                if existing is not None and newStartTime == existing.absoluteTime:
                    return # the effective time didn't change - leave it alone.
                
                # Create a new reminder for the new time. (We don't just update 
                # the old because we want notifications to fire on this change)
                Remindable(self).makeReminder(absoluteTime=newStartTime,
                                     userCreated=False, checkExpired=True,
                                     keepExpired=False, promptUser=False)
                    
        # If we had an existing startTime reminder, dismiss it.
        if existing:
            Remindable(self).dismissReminder(existing)
            
        # Update our relevant-date attribute, too
        self.itsItem.updateRelevantDate(op, name)

    def addRelevantDates(self, dates):
        effectiveStartTime = getattr(self, 'effectiveStartTime', None)
        if effectiveStartTime is not None:
            dates.append((effectiveStartTime, 'startTime'))

    # begin recurrence related methods

    def getFirstInRule(self):
        """Return the rule's master, equivalent to getMaster, different only
        when THISANDFUTURE modifications stay connected to masters.

        @rtype: C{EventStamp}

        """
        first = self.modificationFor
        if first is not None:
            return type(self)(first)

        first = self.occurrenceFor
        if first is None or first is self.itsItem:
            # could be None if a master's first date has a "this" modification
            return self

        return type(self)(first)

    def getLastUntil(self):
        """Find the last modification's rruleset, return it's until value.

        @rtype: C{datetime} or C{None}

        """
        lastRule = self.getLastUntilRule()
        
        if lastRule is None:
            return None
        else:
            return lastRule.until

    def getLastUntilRule(self):
        """Find the rruleset containing the latest until value.

        @rtype: C{RecurrenceRule} or C{None}

        """
        # for no-THISANDFUTURE, this is just return until
        if self.rruleset is None:
            return None
        lastRule = None
        lastUntil = None
        for rule in self.rruleset.rrules:
            until = getattr(rule, 'until', None)
            if until is not None:
                if lastUntil is None or lastUntil < until:
                    lastUntil = until
                    lastRule = rule
        return lastRule
        

    def getRecurrenceEnd(self):
        """Return (last until or RDATE) + duration, or None.

        @rtype: C{datetime} or C{None}

        """
        if self.rruleset is None:
            return self.endTime
        last = self.getLastUntil()
        rdates = getattr(self.rruleset, 'rdates', [])
        for dt in rdates:
            if last is None or last < dt:
                last = dt
        # @@@ we're not doing anything with anyTime or allDay
        if last is None:
            return None
        duration = getattr(self, 'duration', None) or timedelta(0)
        return last + duration

    def updateRecurrenceEnd(self):
        """
        Calculate what recurrenceEnd should be and set it or delete it if it's
        None.
        """
        if self is not self.getMaster():
            end = None
        else:
            end = self.getRecurrenceEnd()

        if end is None:
            if self.recurrenceEnd is not None:
                del self.recurrenceEnd
        else:
            self.recurrenceEnd = end

    def getMaster(self):
        """Return the master event in modifications or occurrences.

        @rtype: C{EventStamp}

        """
        if self.modificationFor is not None:
            masterEvent = type(self)(self.modificationFor).getMaster()
        elif self.occurrenceFor in (self.itsItem, None):
            return self
        else:
            masterEvent = type(self)(self.occurrenceFor).getMaster()
        return masterEvent

    def __getDatetimePrepFunction(self):
        """
        This method returns a function that prepares datetimes for comparisons
        according to the user's global timezone preference settings. This
        is important because "naive timezone mode" can re-order events; e.g.
        in US timezones, an event that falls at 2AM GMT Sunday will be treated
        as occurring on Sunday in naive mode, but Saturday in non-naive.
        [cf Bug 5598].
        """

        if schema.ns('osaf.app', self.itsItem.itsView).TimezonePrefs.showUI:
            # If timezones are enabled, just return the original
            # datetime.
            def prepare(dt):
                return dt
        else:
            # If timezones are disabled, convert all timezones to
            # floating.
            def prepare(dt):
                return dt.replace(tzinfo=ICUtzinfo.floating)

        return prepare


    def isBetween(self, after=None, before=None, inclusive = True):
        """Whether self is between after and before.

        @param after: Earliest end time allowed
        @type  after: C{datetime} or C{None}

        @param before: Latest start time allowed
        @type  before: C{datetime} or C{None}

        @param inclusive: Whether events starting exactly at before should be
                          allowed
        @type  inclusive: C{bool}

        @rtype: C{bool}

        """
        prepDatetime = self.__getDatetimePrepFunction()
        def lte(dt1, dt2):
            return prepDatetime(dt1) <= prepDatetime(dt2)
        def lt(dt1, dt2):
            return prepDatetime(dt1) < prepDatetime(dt2)
        
        if inclusive:
            beforecompare = lte
        else:
            beforecompare = lt

        if self.effectiveStartTime == self.effectiveEndTime:
            aftercompare = lte
        else:
            aftercompare = lt
            
        return ((before is None or beforecompare(self.effectiveStartTime, 
                                                 before)) and
                (after  is None or  aftercompare(after, self.effectiveEndTime)))

    def createDateUtilFromRule(self, ignoreIsCount = True, convertFloating=False):
        """Construct a dateutil.rrule.rruleset from self.rruleset.

        @see: L{Recurrence.RecurrenceRuleSet.createDateUtilFromRule}
        @return: C{dateutil.rrule.rruleset}

        """
        if self.getFirstInRule() != self:
            return self.getFirstInRule().createDateUtilFromRule(ignoreIsCount, convertFloating)
        else:
            dtstart = self.getEffectiveStartTime()
            return self.rruleset.createDateUtilFromRule(dtstart, ignoreIsCount, convertFloating)

    def setRuleFromDateUtil(self, rule):
        """Set self.rruleset from rule.  Rule may be an rrule or rruleset.

        @see: L{Recurrence.RecurrenceRuleSet.setRuleFromDateUtil}

        """
        if self.rruleset is None:
            ruleItem=Recurrence.RecurrenceRuleSet(None, itsView=self.itsItem.itsView)
            ruleItem.setRuleFromDateUtil(rule)
            self.rruleset = ruleItem
        else:
            if self.getFirstInRule() != self:
                rruleset = Recurrence.RecurrenceRuleSet(None, itsView=self.itsItem.itsView)
                rruleset.setRuleFromDateUtil(rule)
                self.changeThisAndFuture(type(self).rruleset.name, rruleset)
            else:
                self.rruleset.setRuleFromDateUtil(rule)

    def onItemDelete(self, view, deferring):
        """If self is the master of a recurring event, call removeRecurrence."""
        if self.getFirstInRule() == self:
            self.removeRecurrence()
        else:
            self.__disableRecurrenceChanges()


    def _restoreStamps(self, clonedEvent):
        disabledChanges = clonedEvent.__disableRecurrenceChanges()
        for stampClass in Stamp(self).stamp_types:
            stampClass(clonedEvent).add()
        if disabledChanges:
            clonedEvent.__enableRecurrenceChanges()

    def _cloneEvent(self):
         # Exclude stamps, since add() does something good here
        clonedItem = self.itsItem.clone(None, None, ('collections', Stamp.stamp_types.name))
        clone = EventStamp(clonedItem)
        self._restoreStamps(clone)
        
        clone.updateRecurrenceEnd()

        return clone

    def _createOccurrence(self, recurrenceID):
        """
        Generate an occurrence for recurrenceID, return it.
        """

        first = self.getFirstInRule()
        if first != self:
            return first._createOccurrence(recurrenceID)
            
        item = first.itsItem
        # It's possible this method has been called on a proxy; in that
        # case, we should make sure we're dealing with the "real"
        # item.
        item = getattr(first.itsItem, 'proxiedItem', item)
        
        values = {
            EventStamp.isGenerated.name: True,
            EventStamp.recurrenceID.name: recurrenceID,
            EventStamp.startTime.name: recurrenceID,
            EventStamp.occurrenceFor.name: item,
            EventStamp.modificationFor.name: None,
        }

        item = self.itsItem.clone(None, None,
                          ('collections', EventStamp.recurrenceEnd.name, Stamp.stamp_types.name),
                          False, **values)
        event = EventStamp(item)
        self._restoreStamps(event)
        event._fixReminders()
        return event

    def getNextOccurrence(self, after=None, before=None):
        """Return the next occurrence for the recurring event self is part of.

        If self is the only occurrence, or the last occurrence, return None.
        
        If self is a master event, raise ValueError, as it's proved error prone
        to figure out what getNextOccurrence on a master means.  To get the
        first occurrence, use the getFirstOccurrence method.

        @param after: Earliest end time allowed
        @type  after: C{datetime} or C{None}

        @param before: Latest start time allowed
        @type  before: C{datetime} or C{None}
        
        @rtype: C{EventStamp}

        """

        prepDatetime = self.__getDatetimePrepFunction()

        # helper function
        def checkModifications(first, before, nextEvent = None):
            """Look for modifications or a master event before nextEvent,
            before "before", and after "after".
            """
            if after is None:
                # isBetween isn't quite what we want if after is None
                def test(mod):
                    return ((self is first or
                        self.effectiveStartTime < mod.effectiveStartTime) and
                       (before is None or (mod.effectiveStartTime < before)))
            else:
                def test(mod):
                    return mod.isBetween(after, before)
            for mod in itertools.imap(EventStamp, first.modifications or []):
                if test(mod):
                    if nextEvent is None:
                        nextEvent = mod
                    # sort by recurrenceID if startTimes are equal
                    elif ((mod.effectiveStartTime < nextEvent.effectiveStartTime) or
                         ((mod.effectiveStartTime == nextEvent.effectiveStartTime)
                          and (mod.recurrenceID  < nextEvent.recurrenceID))):
                        nextEvent = mod
            return nextEvent

        # main getNextOccurrence logic
        if self.rruleset is None:
            return None

        first = self.getMaster()
        if first == self:
            raise ValueError, "getNextOccurrence cannot be called on a master."
        
        # exact means this is a search for a specific recurrenceID
        exact = after is not None and after == before
        
        # inclusive means events starting at exactly after should be allowed.        
        inclusive = after is not None and (after == before or 
                                           self.duration == timedelta(0))
            

        # take duration into account if after is set
        if not exact and after is not None:
            start = prepDatetime(after) - first.duration
        else:
            start = prepDatetime(self.effectiveStartTime)

        if before is not None:
            before = prepDatetime(before)

        ruleset = self.createDateUtilFromRule()


        for recurrenceID in ruleset:

            preparedRID = prepDatetime(recurrenceID)

            if preparedRID < start or (not inclusive and preparedRID == start):
                continue

            if before is not None and preparedRID > before:
                return checkModifications(first, before)

            calculated = self.getExistingOccurrence(recurrenceID)
            if calculated is None:
                return checkModifications(first, before,
                                          self._createOccurrence(recurrenceID))
            # don't bother with modifications (isGenerated == False) unless
            # we're looking for this exact recurrenceID, because
            # checkModifications will find earlier modifications for us, and the
            # modification may have been moved later than a future occurrence
            elif calculated.isGenerated or exact:
                return checkModifications(first, before, calculated)

        return checkModifications(first, before)

    def _fixReminders(self):
        from osaf.pim.reminders import Remindable
        # When creating generated events, this function is
        # called so that all reminders in the past are marked
        # expired, and the rest are not. This helps avoid a
        # mass of reminders if an event in the past is changed.
        #
        now = datetime.now(ICUtzinfo.default)

        def expired(reminder):
            nextTime = reminder.getNextReminderTimeFor(self)
            return nextTime <= now


        # We really don't want to touch self.reminders
        # or self.expiredReminders if they haven't really
        # changed. The reason is that that will trigger a
        # change notification on app idle, which in turn causes
        # the UI to re-generate all these occurrences, which puts
        # us back in this # method, etc, etc.

        # Figure out what (if anything) has changed ...
        remindable = Remindable(self)
        nowExpired = [r for r in remindable.reminders
                         if expired(r)]

        nowNotExpired = [r for r in remindable.expiredReminders
                           if not expired(r)]

        # ... and update the collections accordingly
        for reminder in nowExpired:
            self.reminders.remove(reminder)
            if reminder.keepExpired:
                self.expiredReminders.add(reminder)
            else:
                assert len(reminder.reminderItems) == 0
                assert len(reminder.expiredReminderItems) == 0
                reminder.delete()

        for reminder in nowNotExpired:
            remindable.reminders.add(reminder)
            remindable.expiredReminders.remove(reminder)


    def _generateRule(self, after=None, before=None, inclusive=False):
        """Yield all occurrences in this rule."""
        first = self.getMaster()
        event = self.getFirstOccurrence()
        if event is None:
            raise StopIteration
        # check for modifications taking place before first, but only if
        # if we're actually interested in dates before first (i.e., the
        # after argument is None or less than first.startTime)

        prepDatetime = self.__getDatetimePrepFunction()

        if (first.modifications is not None and
            (after is None or prepDatetime(after) < prepDatetime(first.startTime))):
            for mod in itertools.imap(EventStamp, first.modifications):
                if prepDatetime(mod.startTime) <= prepDatetime(event.startTime):
                    event = mod

        if not event.isBetween(after, before):
            event = event.getNextOccurrence(after, before)
        else:
            # [Bug 5482], [Bug 5627], [Bug 6174]
            # We need to make sure event is actually
            # included in our recurrence rule.
            rruleset = self.createDateUtilFromRule()

            recurrenceID = event.recurrenceID
            if isDayEvent(event):
                recurrenceID = datetime.combine(
                                    recurrenceID.date(),
                                    time(0, tzinfo=recurrenceID.tzinfo))

            if not recurrenceID in rruleset:
                event = event.getNextOccurrence()

        lastUntilRule = self.getLastUntilRule()
        if lastUntilRule is not None:
            lastUntil = lastUntilRule.until
            
            lastUntil += getattr(self, 'duration', timedelta(0))
            
            if lastUntilRule.untilIsDate:
                lastUntil += timedelta(days=1)

            if before is None:
                before = lastUntil
            else:
                before = min(before, lastUntil)

        while event is not None:
            if event.isBetween(after, before, inclusive):
                if event.occurrenceFor is not None:
                    yield event

            # if event takes place after the before parameter, we're done.
            elif event.isBetween(after=before):
                break

            event = event.getNextOccurrence()

    def _getFirstGeneratedOccurrence(self, create=False):
        """Return the first generated occurrence or None.

        If create is True, create an occurrence if possible.

        """
        if self.rruleset is None: return None

        first = self.getFirstInRule()
        if first != self: return first._getFirstGeneratedOccurrence(create)

        # make sure recurrenceID gets set for all masters
        if self.recurrenceID is None:
            self.recurrenceID = self.startTime

        if create:
            iter = self._generateRule()
        else:
            if self.occurrences is None:
                return None
            iter = _sortEvents(self.occurrences)
        for occurrence in iter:
            occurrence = EventStamp(occurrence)
            if occurrence.isGenerated:
                return occurrence
        # no generated occurrences
        return None

    def getOccurrencesBetween(self, after, before, inclusive = False):
        """Return a list of events ordered by startTime.

        Get events starting on or before "before", ending on or after "after".
        Generate any events needing generating.

        @param after: Earliest end time allowed
        @type  after: C{datetime} or C{None}

        @param before: Latest start time allowed
        @type  before: C{datetime} or C{None}

        @param inclusive: Whether events starting exactly at before should be
                          allowed
        @type  inclusive: C{bool}

        @rtype: C{list} containing 0 or more C{EventStamp}s

        """
        master = self.getMaster()

        if not master.hasLocalAttributeValue('rruleset'):
            if master.isBetween(after, before, inclusive):
                return [master]
            else: return []

        return list(master._generateRule(after, before, inclusive))

    def getExistingOccurrence(self, recurrenceID):
        """Get event associated with recurrenceID if it already exists.

        @param recurrenceID:
        @type  recurrenceID: C{datetime}

        @rtype: C{EventStamp}, or C{NoneType}

        """
        first = self.getFirstInRule()

        # When an event is imported via sharing, the constructor is bypassed
        # and we need to make sure occurrences has a value
        for occurrence in itertools.imap(EventStamp, first.occurrences or []):
            if occurrence.recurrenceID == recurrenceID:
                return occurrence
        return None

    def getRecurrenceID(self, recurrenceID):
        """Get or create the item matching recurrenceID, or None.

        @param recurrenceID:
        @type  recurrenceID: C{datetime}

        @rtype: C{datetime} or C{None}

        """
        # look through master's occurrences
        existing = self.getExistingOccurrence(recurrenceID)
        if existing is not None:
            return existing

        # no existing matches, see if one can be generated:
        for occurrence in self.getOccurrencesBetween(recurrenceID,recurrenceID,True):
            if occurrence.recurrenceID == recurrenceID:
                return occurrence

        # no match
        return None
    
    def getFirstOccurrence(self):
        """
        Generally, return the occurrence with the same recurrenceID as the
        master.
        
        In various edge cases, return the *first* occurrence (if the master's
        recurrenceID has been excluded, or a modification moved earlier than the
        first), or if there are no occurrences, return None.
        
        """
        if self.rruleset is None:
            return None
        
        master = self.getMaster()
        recurrenceID = master.startTime
        occurrence = self.getExistingOccurrence(recurrenceID)

        def checkModifications(event):
            """Return the earliest modification coming before event, or event"""
            earliest = event
            for mod in itertools.imap(EventStamp, master.modifications or []):
                if (mod.effectiveStartTime < earliest.effectiveStartTime or
                    (mod.effectiveStartTime == earliest.effectiveStartTime and
                     mod.recurrenceID  < earliest.recurrenceID)):
                    earliest = mod
            return earliest       
        
        if occurrence is None:
            rruleset = self.createDateUtilFromRule()
            try:
                earliestTime = iter(rruleset).next()
                occurrence = self._createOccurrence(earliestTime)
            except StopIteration:
                pass
        
        if occurrence is None:
            return None
        else:
            return checkModifications(occurrence)
            
    def _makeGeneralChange(self):
        """Do everything that should happen for any change call."""
        self.isGenerated = False

    def changeNoModification(self, attr, value):
        """Set _ignoreValueChanges flag, set the attribute, then unset flag."""
        flagStart = self.__disableRecurrenceChanges()
        setattr(self.itsItem, attr, value)
        if flagStart:
            self.__enableRecurrenceChanges()

    def _propagateChange(self, modEvent):
        """Move later modifications to self."""
        if (self != modEvent and modEvent.occurrenceFor is not self.itsItem and
            modEvent.recurrenceID > self.startTime):
            # future 'this' modifications in master should move to self
            modEvent.modificationFor = self.itsItem
            modEvent.occurrenceFor = self.itsItem
            modEvent.rruleset = self.rruleset
            modEvent.icalUID = self.icalUID

    def changeThisAndFuture(self, attr=None, value=None):
        """Modify this and all future events."""
        master = self.getMaster()
        first = master # Changed for no-THISANDFUTURE-style
        if self.recurrenceID is None:
            self.recurrenceID = self.startTime
        recurrenceID = self.recurrenceID
        # we can't use master.effectiveStartTime because the event timezone and
        # the current timezone may not match
        isFirst = (self == first) or (((master.allDay or master.anyTime) and
                    recurrenceID.date() == master.startTime.date()) or
                   (recurrenceID == master.startTime))
                   
        if isFirst and self != first and self.modificationFor is None:
            # We're the unmodified occurrence for the master (but not
            # the master itself). Just let the master handle
            # everything.
            return first.changeThisAndFuture(attr, value)
            
        
        disabledSelf = self.__disableRecurrenceChanges()

        # all day events' startTime is at midnight
        startMidnight = datetime.combine(self.startTime.date(),
                                         time(0, tzinfo=self.startTime.tzinfo))

        if attr in (EventStamp.startTime.name, EventStamp.allDay.name,
                    EventStamp.anyTime.name):
            # if startTime changes (and an allDay/anyTime change changes
            # effective startTime), all future occurrences need to be shifted
            # appropriately
            startTimeDelta = zero_delta
            if attr == EventStamp.startTime.name:
                startTimeDelta = (value - self.startTime)
            # don't move future occurrences unless allDayness (anyTime or
            # allDay) changes
            else:
                if attr == EventStamp.allDay.name:
                    otherAllDayness = self.anyTime
                else:
                    otherAllDayness = self.allDay
                if (value or otherAllDayness) != (getattr(self.itsItem, attr) or
                                                  otherAllDayness):
                    if value == False:
                        startTimeDelta = self.startTime - startMidnight
                    else:
                        startTimeDelta = startMidnight - self.startTime

            if startTimeDelta != zero_delta:
                self.rruleset.moveDatesAfter(recurrenceID, startTimeDelta)
                self.recurrenceID += startTimeDelta

        setattr(self.itsItem, attr, value)

        def makeThisAndFutureMod():
            # Changing occurrenceFor before changing rruleset is important, it
            # keeps the rruleset change from propagating inappropriately
            del self.occurrenceFor
            if attr != EventStamp.rruleset.name:
                self.rruleset = self.rruleset.copy(cloudAlias='copying')
                self.rruleset.removeDates(datetime.__lt__, self.startTime)
            # We have to pass in master because occurrenceFor has been changed
            self._makeGeneralChange()
            # Make this event a separate event from the original rule
            del self.modificationFor
            if self.allDay:
                self.recurrenceID = startMidnight
            else:
                self.recurrenceID = self.startTime
            self.icalUID = unicode(self.itsItem.itsUUID)
            self.copyCollections(master, self)

        # determine what type of change to make
        if attr == EventStamp.rruleset.name: # rule change, thus a destructive change
            if self == master:
                rruleset = master.createDateUtilFromRule()
                for occurrence in itertools.imap(EventStamp,
                                                 self.occurrences or []):
                    disabled = occurrence.__disableRecurrenceChanges()
                    if occurrence.recurrenceID in rruleset:
                        # Make sure each occurrence has our rruleset
                        setattr(occurrence.itsItem, attr, value)
                        if disabled:
                            occurrence.__enableRecurrenceChanges()
                    else:
                        del occurrence.rruleset
                        del occurrence.occurrenceFor
                        del occurrence.modificationFor
                        occurrence.itsItem.delete()
                if self.occurrences is None:
                    # Make sure we have at least one occurrence
                    self.getRecurrenceID(self.startTime)
            else:
                self.removeFutureOccurrences()
                if self.recurrenceID == master.startTime and self.modificationFor == master:
                    # A THIS modification to master, make it the new master
                    self.moveCollections(master, self)
                    del self.modificationFor
                    del self.occurrenceFor
                    self.recurrenceID = self.startTime
                    master.deleteAll()
                elif self.isGenerated or self.modificationFor is not None:
                    makeThisAndFutureMod()
                    master.moveRuleEndBefore(recurrenceID)
        else: #propagate changes forward
            if self.modificationFor is not None:
                #preserve self as a THIS modification
                if self.recurrenceID != first.startTime:
                    # create a new event, cloned from first, make it a
                    # thisandfuture modification with self overriding it
                    newfirst = first._cloneEvent()
                    disabled = newfirst.__disableRecurrenceChanges()
                    newfirstItem = newfirst.itsItem
                    newfirst.rruleset = self.rruleset.copy(cloudAlias='copying')
                    # There are two events in play, self (which has been
                    # changed), and newfirst, a non-displayed item used to
                    # define generated events.  Make sure the current change
                    # is applied to both items, and that both items have the
                    # same rruleset.
                    setattr(newfirst.itsItem, attr, value)
                    self.rruleset = newfirst.rruleset
                    newfirst.startTime = self.recurrenceID
                    newfirst.occurrenceFor = None #self overrides newfirst
                    newfirst.icalUID = self.icalUID = str(
                                                   newfirst.itsItem.itsUUID)
                    newfirst._makeGeneralChange()
                    self.occurrenceFor = self.modificationFor = newfirstItem
                    self.copyCollections(master, newfirst)
                    # move THIS modifications after self to newfirst
                    for mod in itertools.imap(EventStamp,
                                              first.modifications or []):
                        if mod.recurrenceID > newfirst.startTime:
                            mod.occurrenceFor = newfirstItem
                            mod.modificationFor = newfirstItem
                            mod.icalUID = newfirst.icalUID
                            mod.rruleset = newfirst.rruleset
                            #rruleset needs to change, so does icalUID
                    if disabled:
                        newfirst.__enableRecurrenceChanges()
                else:
                    # self was a THIS modification to the master, setattr needs
                    # to be called on master
                    if attr == EventStamp.startTime.name:
                        newStart = master.startTime + startTimeDelta
                        master.changeNoModification(EventStamp.startTime.name, newStart)
                        master.changeNoModification(EventStamp.recurrenceID.name, newStart)
                        self.recurrenceID = newStart
                    else:
                        master.changeNoModification(attr, value)

            else: # change applies to an event which isn't a modification
                if self.isGenerated:
                    makeThisAndFutureMod()
                else:
                    # Change applied to a master, make sure it gets its
                    # recurrenceID updated
                    self.recurrenceID = self.startTime
            master._deleteGeneratedOccurrences()

            for mod in itertools.imap(EventStamp, master.modifications or []):
                self._propagateChange(mod)
                # change recurrenceIDs for modifications if startTime change
                if attr == EventStamp.startTime.name and mod.modificationFor == self.itsItem:
                    mod.changeNoModification(EventStamp.recurrenceID.name,
                        mod.recurrenceID + startTimeDelta)
            if not isFirst:
                master.moveRuleEndBefore(recurrenceID)

            # if modifications were moved from master to self, they may have the
            # same recurrenceID as a (spurious) generated event, so delete
            # generated occurrences.

            self._deleteGeneratedOccurrences()
            self._getFirstGeneratedOccurrence(True)

        if disabledSelf: self.__enableRecurrenceChanges()

    def moveCollections(self, fromEvent, toEvent):
        """Move all collection references from one event to another."""
        fromItem = fromEvent.itsItem.getMembershipItem()
        toItem = fromEvent.itsItem.getMembershipItem()

        for collection in getattr(fromItem, 'collections', []):
            collection.add(toItem)
            collection.remove(fromItem)

    def copyCollections(self, fromEvent, toEvent):
        """Copy all collection references from one item to another."""
        fromItem = EventStamp(fromEvent).itsItem.getMembershipItem()
        toItem = EventStamp(toEvent).itsItem.getMembershipItem()
        
        for collection in getattr(fromItem, 'collections', []):
            collection.add(toItem)

    def changeThis(self, attr=None, value=None):
        """Make this event a modification, don't modify future events.

        Without arguments, change self appropriately to make it a THIS
        modification.

        """
        if self.modificationFor is not None:
            # We're already a modification, fall through to
            # the setattr() at the end of this method.
            pass
        elif self.rruleset is not None:
            first = self.getFirstInRule()
            master = self.getMaster()
            if first == self:
                # Here, we're trying to make a THIS change to
                # a master. That means making a change to the
                # corresponding occurrence.
                backup = self.getRecurrenceID(self.startTime)
                if backup is not None:
                    return backup.changeThis(attr, value)
                else:
                    # if backup is None, that means that the master's
                    # occurrence isn't included in the rule. Hmm, that's
                    # confusing. Maybe we should raise?
                    if master.itsItem == self.itsItem:
                        self.recurrenceID = self.startTime
            else:
                self.modificationFor = first.itsItem
                self._makeGeneralChange()
                self._getFirstGeneratedOccurrence(True)
        if attr is not None:
            setattr(self.itsItem, attr, value)

    @schema.observer(
        ContentItem.displayName, ContentItem.body, ContentItem.lastModified,
        startTime, duration, location, allDay, rruleset, Stamp.stamp_types
    )
    def onEventChanged(self, op, name):
        """
        Maintain coherence of the various recurring items associated with self
        after an attribute has been changed.

        """
        
        # allow initialization code to avoid triggering onEventChanged
        rruleset = (name == EventStamp.rruleset.name)
        
        if (self.rruleset is None or
            getattr(self.itsItem, type(self).IGNORE_CHANGE_ATTR, False) or
            getattr(self.itsItem, '_share_importing', False)):
            return
        # avoid infinite loops
        if rruleset:
            logger.debug("just set rruleset")
            gen = self._getFirstGeneratedOccurrence(True)
            if DEBUG and gen:
                logger.debug("got first generated occurrence, %s", gen.serializeMods().getvalue())

            if self == self.getFirstInRule():
                self.recurrenceID = self.startTime
                self.updateRecurrenceEnd()

        else:
            if DEBUG:
                logger.debug("about to changeThis in onEventChanged(name=%s) for %s", name, str(self))
                logger.debug("value is: %s", getattr(self, name))
            if self == self.getFirstInRule():
                if name == EventStamp.duration.name:
                    self.updateRecurrenceEnd()
                # A direct change to a master's attribute becomes
                # a THISANDFUTURE change.
                makeChange = self.changeThisAndFuture
            else:
                makeChange = self.changeThis

            if name and op == 'set':
                makeChange(name, getattr(self.itsItem, name))
            else:
                makeChange()

    def _deleteGeneratedOccurrences(self):
        for event in itertools.imap(EventStamp,
                                    self.getFirstInRule().occurrences or []):
            if event.isGenerated:
                # don't let deletion result in spurious onEventChanged calls
                event.__disableRecurrenceChanges()
                event.itsItem.delete()

    def cleanRule(self):
        """Delete generated occurrences in the current rule, create a backup."""
        first = self.getFirstInRule()
        self._deleteGeneratedOccurrences()
        if first.itsItem.hasLocalAttributeValue(EventStamp.modifications.name):
            until = first.rruleset.rrules.first().calculatedUntil()
            for mod in itertools.imap(EventStamp, first.modifications):
                # this won't work for complicated rrulesets
                if until is not None and (mod.recurrenceID > until):
                    mod.__disableRecurrenceChanges()
                    mod.itsItem.delete()

        # create a backup
        first._getFirstGeneratedOccurrence(True)
        first.updateRecurrenceEnd()

    def moveRuleEndBefore(self, recurrenceID):
        master = self.getMaster()
        master.rruleset.moveRuleEndBefore(master.startTime, recurrenceID)

    def deleteThisAndFuture(self):
        """Delete self and all future occurrences and modifications."""
        # changing the rule will delete self unless self is the master
        master = self.getMaster()
        if self.recurrenceID == master.startTime:
            self.deleteAll()
        else:
            self.moveRuleEndBefore(self.recurrenceID)

    def deleteThis(self):
        """Exclude this occurrence from the recurrence rule."""
        master = self.getMaster()
        
        # If we're a master, delete the occurrence
        # that corresponds to self
        if master == self:
            event = self.getRecurrenceID(self.startTime)
            if event is not None:
                return event.deleteThis()
        
        rruleset = self.rruleset
        recurrenceID = self.recurrenceID
        if getattr(rruleset, 'exdates', None) is None:
            rruleset.exdates=[]
        rruleset.exdates.append(recurrenceID)
        if getattr(self, 'occurrenceFor', None) is self.itsItem:
            self.occurrenceFor = None
        else:
            self.itsItem.delete(recursive=True)

    def deleteAll(self):
        """Delete master, all its modifications, occurrences, and rules."""
        master = self.getMaster()
        itemsToSkip = (master.itsItem, self.itsItem)
        for event in itertools.imap(EventStamp, master.occurrences):
            if event.itsItem in itemsToSkip: #don't delete master or self quite yet
                continue
            event.__disableRecurrenceChanges()
            event.itsItem.delete(recursive=True)

        rruleset = self.rruleset
        rruleset._ignoreValueChanges = True
        # we don't want rruleset's recursive delete to get self yet
        del self.rruleset
        rruleset._ignoreValueChanges = True
        rruleset.delete(recursive=True)
        self.__disableRecurrenceChanges()
        master.itsItem.delete(recursive=True)
        self.itsItem.delete(recursive=True)

    def removeFutureOccurrences(self):
        """Delete all future occurrences and modifications."""
        master = self.getMaster()
        for event in itertools.imap(EventStamp, master.occurrences):
            if event.startTime >  self.startTime:
                event.__disableRecurrenceChanges()
                event.itsItem.delete()

        self._getFirstGeneratedOccurrence(True)

    def removeRecurrence(self):
        """
        Remove modifications, rruleset, and all occurrences except master.

        The resulting event will occur exactly once.
        """
        master = self.getMaster()
        if not master.recurrenceID in (None, master.startTime):
            master.changeNoModification(EventStamp.recurrenceID.name, master.startTime)
        rruleset = master.rruleset
        if rruleset is not None:
            rruleset._ignoreValueChanges = True
            masterHadModification = False
            
            for event in itertools.imap(EventStamp, master.occurrences or []):

                if (event.recurrenceID == master.startTime and
                    event.itsItem in (master.modifications or [])):
                    
                    # A THIS modification to master, make it the new master
                    self.moveCollections(master, event)
                    del event.rruleset
                    del event.recurrenceID
                    del event.modificationFor
                    # events with the same icalUID but different UUID drive
                    # sharing crazy, so change icalUID of master
                    event.icalUID = unicode(event.itsItem.itsUUID)
                    masterHadModification = True
                else:
                    # Since we're possibly doing delayed deleting (if we're
                    # in the background sharing mode) let's remove the events
                    # from occurrences:
                    master.occurrences.remove(event.itsItem)
                    # now that we've disconnected this event from the master,
                    # event.delete() will erroneously dispatch to deleteAll() if
                    # event.rruleset exists, so disconnect from the rruleset
                    del event.rruleset
                    event.itsItem.delete()

            rruleset._ignoreValueChanges = True
            rruleset.delete()

            if masterHadModification:
                master.itsItem.delete()
            else:
                del master.recurrenceID
                del master.rruleset
                del master.occurrences



    def isCustomRule(self):
        """Determine if self.rruleset represents a custom rule.

        @see: L{Recurrence.RecurrenceRuleSet.isCustomRule}
        @rtype: C{bool}

        """
        rruleset = getattr(self, 'rruleset', None)
        if rruleset is not None:
            return self.rruleset.isCustomRule()
        else: return False

    def getCustomDescription(self):
        """Return a string describing custom rules.

        @see: L{Recurrence.RecurrenceRuleSet.getCustomDescription}
        @rtype: C{str}

        """
        rruleset = getattr(self, 'rruleset', None)
        if rruleset is not None:
            return rruleset.getCustomDescription()
        else: return ''

    def isProxy(self):
        """Is this a proxy of an event?

        @rtype: C{bool}

        """
        return False

    def isAttributeModifiable(self, attribute):
        """Is this attribute modifiable?

        @rtype: C{bool}

        """
        master = self.getMaster()
        if self is not master:
            # This is a recurring event that isn't the master;
            # go ask the master.
            return master.isAttributeModifiable(attribute)
        # Otherwise, just do it the normal way.
        return super(EventStamp, self).isAttributeModifiable(attribute)

    # for use in indexing EventStamps
    @schema.Comparator
    def cmpStartTime(self, event):
        return cmpTimeAttribute(self, event, 'effectiveStartTime')

    @schema.Comparator
    def cmpEndTime(self, event):
        return cmpTimeAttribute(self, event, 'effectiveEndTime')

    @schema.Comparator
    def cmpRecurEnd(self, event):
        return cmpTimeAttribute(self, event, 'recurrenceEnd')

    # comparisons which strip timezones
    @schema.Comparator
    def cmpStartTimeNoTZ(self, event):
        return cmpTimeAttribute(self, event, 'effectiveStartTime', False)

    @schema.Comparator
    def cmpEndTimeNoTZ(self, event):
        return cmpTimeAttribute(self, event, 'effectiveEndTime', False)

    @schema.Comparator
    def cmpRecurEndNoTZ(self, event):
        return cmpTimeAttribute(self, event, 'recurrenceEnd', False)

    def isRecurring(self):
        """ Is this Event a recurring event? """
        return self.rruleset is not None
    
def isRecurring(item):
    """ Is this item a recurring event? """
    return (has_stamp(item, EventStamp) and 
            EventStamp(item).isRecurring())
    
def CalendarEvent(*args, **kw):
    """An unstamped event."""

    # This seems wonky.... which attributes belong to Note, and
    # which belong to Event? Maybe the code that calls this should
    # operate on a Note instead?
    kw.setdefault('participants', [])
    
    for key in kw.keys():
        attr = getattr(EventStamp, key, None)
        if isinstance(attr, schema.Descriptor):
            kw[attr.name] = kw[key]
            del kw[key]
            
    
    note = Note(*args, **kw)
    result = EventStamp(note)
    result.add()
        
    return result

def _sortEvents(itemlist, reverse=False, attrName=EventStamp.effectiveStartTime.name):
    """Helper function for working with events."""
    def key(item):
         return getattr(item, attrName)
    return sorted(itemlist, key=key, reverse=reverse)

class RecurrencePattern(ContentItem):
    """Unused, should be removed."""

