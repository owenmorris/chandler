#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from __future__ import with_statement

__parcel__ = "osaf.pim.calendar"

class redirector(property):
    """
    A property that redirects from an Annotation class to its
    target item. This is only used right now to avoid a giant
    search/replace of occurrenceFor <-> inheritFrom and
    occurrences <-> inheritTo.
    
    The differences between this and a schema.Calculated are:
    
    1) No basedOn attribute.
    2) This doesn't install a property on the target class.
    3) redirector.name returns the name of the target class attribute. This
       is so that existing usages like EventStamp.occurrences.name will still
       work.
    """
    name = None
    
    def __init__(self, attrName):
        self.name = attrName
        
        def fset(self, value):
            setattr(self.itsItem, attrName, value)

        def fget(self):
            return getattr(self.itsItem, attrName, None)

        def fdel(self):
            delattr(self.itsItem, attrName)

        property.__init__(self, fset=fset, fget=fget, fdel=fdel,
                          doc="Redirect to '%s'" % (attrName,))

from application import schema
from osaf.pim.contacts import Contact
from osaf.pim.triage import Triageable, TriageEnum
from osaf.pim.items import ContentItem, isDead
from osaf.pim.stamping import Stamp, has_stamp
from osaf.pim.notes import Note
from osaf.pim.calendar import Recurrence
from osaf.pim.collections import FilteredCollection
from chandlerdb.util.c import isuuid, UUID, Empty, Nil
from osaf.pim.reminders import Remindable, Reminder

from TimeZone import formatTime
from osaf.pim.calendar.TimeZone import TimeZoneInfo
from osaf.pim.calendar import DateTimeUtil
from time import localtime
from datetime import datetime, time, timedelta
import itertools
import logging
from util import tokenizer
import operator
import parsedatetime.parsedatetime as parsedatetime
import parsedatetime.parsedatetime_consts as ptc
from i18n import getLocale

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

    def getGetFunction(attrName):
        if attrName == 'effectiveStartTime':
            return EventStamp._getEffectiveStartTime
        elif attrName == 'effectiveEndTime':
            return EventStamp._getEffectiveEndTime
        else:
            fullName = getattr(EventStamp, attrName).name
            def getFn(uuid, view):
                return view.findInheritedValues(uuid, (fullName, None))[0]
            return getFn

    getStart = getGetFunction(startAttrName)
    getEnd = getGetFunction(endAttrName)
    endSubStartVal = endVal - startVal
    if not useTZ:
        endValNoTZ = endVal.replace(tzinfo=None)
        startValNoTZ = startVal.replace(tzinfo=None)
    
    # callbacks to use for searching the indexes
    def mStart(key, delta=None):
        # gets the last item starting before endVal, or before startVal - delta
        if delta is None:
            delta = zero_delta
        else:
            delta = delta + endSubStartVal
        testVal = getStart(key, view)
        if testVal is None:
            return -1 # interpret None as negative infinity
        # note that we're NOT using >=, if we did, we'd include all day
        # events starting at the beginning of the next week
        if useTZ:
            if endVal - delta > testVal:
                return 0
        else:
            if endValNoTZ - delta > testVal.replace(tzinfo=None):
                return 0
        return -1

    def mEnd(key, delta=None):
        # gets the first item ending after startVal, or after endVal + delta
        if delta is None:
            delta = zero_delta
        else:
            delta = delta + endSubStartVal

        testVal = getEnd(key, view)

        if (getStart(key, view) == testVal):
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
            if compare(startValNoTZ + delta,
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
    
def adjustSearchTimes(start, end, showTZUI):
    """
    In many cases, we want to find all events within a range of C{datetime}
    values, This includes API like L{eventsInRange}, L{recurringEventsInRange},
    L{iterBusyInfo} and L{EventStamp.getOccurrencesBetween}.
    
    However, the set of events we return depends on how we are
    comparing event start- and end-times. (When timezones have been disabled
    in the Chandler UI, we're supposed to compare them without regard to
    timezone (or, by stripping out the C{tzinfo}), while otherwise we just
    do normal C{datetime} comparison).

    So, in the case where timezones have been disabled in the UI, we cope
    with this by expanding the range of our searches, and making sure we
    only return events that fall within the original requested range. This
    function does that adjustment.
    
    @param start: Lower bound of search range, or C{None}
    @type start: C{datetime}
    
    @param end: Upper bound of search range, or C{None}
    @type end: C{datetime}
    
    @param showTZUI: Whether the user has enabled display of timezones in the UI
    @type showTZUI: C{bool}
    
    @return: If C{showTZUI} is C{True}, the adjusted C{start} and C{end}
             are returned. ((C{None} values are not adjusted).
             
             In the case where C{showTZUI} is C{False}, the input values
             are returned.
             
    @rtype: C{tuple}
    """
    if not showTZUI:
        if start is not None:
            start -= timedelta(days=1)
        if end is not None:
            end += timedelta(days=1)
    return start, end

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
    
    pim_ns = schema.ns('osaf.pim', view)
    tzprefs = pim_ns.TimezonePrefs

    startIndex = 'effectiveStart'
    endIndex   = 'effectiveEnd'
    
    searchStart, searchEnd = adjustSearchTimes(start, end, tzprefs.showUI)
    
    allEvents  = EventStamp.getCollection(view)
    longEvents = pim_ns.longEvents
    keys = getKeysInRange(view, start, 'effectiveStartTime', startIndex,
                          allEvents, end,'effectiveEndTime', endIndex,
                          allEvents, filterColl, '__adhoc__', tzprefs.showUI,
                          longDelta = LONG_TIME, longCollection=longEvents)
    for key in keys:
        item = view[key]
        event = EventStamp(item)
        # Should probably assert has_stamp(event, EventStamp)
        if (has_stamp(event, EventStamp) and
            event.rruleset is None and not isDead(item) and
            event.isBetween(start, end) and
            ((dayItems and timedItems) or isDayEvent(event) == dayItems)):
            yield event

def recurringEventsInRange(view, start, end, filterColl=None,
                           dayItems=True, timedItems=True):
    """
    Yield all recurring events between start and end that appear in filterColl.
    """

    pim_ns = schema.ns("osaf.pim", view)
    tzprefs = pim_ns.TimezonePrefs

    searchStart, searchEnd = adjustSearchTimes(start, end, tzprefs.showUI)

    startIndex = 'effectiveStart'
    endIndex   = 'recurrenceEnd'

    masterEvents = pim_ns.masterEvents
    keys = getKeysInRange(view, searchStart, 'effectiveStartTime', startIndex,
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
                    
def iterBusyInfo(view, start, end, filterColl=None):
    pim_ns = schema.ns('osaf.pim', view)
    tzprefs = pim_ns.TimezonePrefs
    searchStart, searchEnd = adjustSearchTimes(start, end, tzprefs.showUI)

    startIndex = 'effectiveStart'
    endIndex   = 'effectiveEnd'
    recurEndIndex   = 'recurrenceEnd'

    allEvents  = EventStamp.getCollection(view)
    longEvents = pim_ns.longEvents
    keys = getKeysInRange(view, searchStart, 'effectiveStartTime', startIndex,
                          allEvents, searchEnd, 'effectiveEndTime', endIndex,
                          allEvents, filterColl, '__adhoc__', tzprefs.showUI,
                          longDelta = LONG_TIME, longCollection=longEvents)
    for key in keys:
        event = EventStamp(view[key])
        assert has_stamp(event, EventStamp)
        if event.rruleset is None:
            for fb in event.iterBusyInfo(start, end):
                yield fb

    masterEvents = pim_ns.masterEvents
    keys = getKeysInRange(view, searchStart, 'effectiveStartTime', startIndex,
                          masterEvents, end, 'recurrenceEnd', recurEndIndex,
                          masterEvents, filterColl, '__adhoc__')

    for key in keys:
        masterEvent = EventStamp(view[key])
        for fb in masterEvent.iterBusyInfo(start, end):
            yield fb

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

    @group Semi-Private Methods: noRecurrenceChanges,
    cleanRule, _copyCollections, getEffectiveEndTime, getEffectiveStartTime,
    getEndTime, getFirstInRule, InitOutgoingAttributes, isBetween,
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
        defaultValue=False
    )

    anyTime = schema.One(
        schema.Boolean,
        defaultValue=True
    )

    transparency = schema.One(
        TimeTransparencyEnum,
        defaultValue="confirmed"
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

    modifies = schema.One(
        ModificationEnum,
        defaultValue=None,
        doc = "Describes whether a modification applies to future events, or "
              "just one event"
    )

    modifications = schema.Sequence(
        doc = "A list of occurrences that have been modified",
        defaultValue=Empty,
    ) # inverse of modificationFor

    modificationFor = schema.One(
        defaultValue=None,
        inverse=modifications
    )
        
    occurrences = redirector('inheritTo')
    occurrenceFor = redirector('inheritFrom')
    
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
            literal = [startTime, duration, allDay, anyTime, modifies,
                       transparency, isGenerated, recurrenceID],
            byValue = [location], 
            byCloud = [modifications, rruleset, occurrenceFor]
        )
    )
    
    IGNORE_CHANGE_ATTR = "%s.EventStamp.__ignoreValueChange" % (__module__,)

    def __cmp__(self, other):
        """
        Compare events based on their effectiveStartTime.  Fall back to
        comparing UUIDs if the times match.
        """
        selfTime = self.effectiveStartTime
        otherTime = other.effectiveStartTime
        
        if otherTime == selfTime:
            return cmp(self.itsItem.itsUUID, other.itsItem.itsUUID)
        elif otherTime is None:
            return 1
        elif selfTime is None:
            return -1
        else:
            #datetime.__cmp__ isn't forgiving of None
            return cmp(selfTime, otherTime)

    @apply
    def summary():
        def fget(self):
            return self.itsItem.displayName
        def fset(self, value):
            self.itsItem.displayName = value
        return schema.Calculated(schema.Text, (ContentItem.displayName,),
                                 fget, fset)

    def __disableRecurrenceChanges(self):
        item = self.itsItem
        disable = not getattr(item, EventStamp.IGNORE_CHANGE_ATTR, False)
        if disable:
            setattr(item, EventStamp.IGNORE_CHANGE_ATTR, True)
        return disable
        
    def noRecurrenceChanges(self):
        """
        For use in a Python 2.5 'with' statement. Usage:
        
        >>> with event.noRecurrenceChanges():
        ...    # change event attributes without triggering
        ...    # automatic THIS/THISANDFUTURE changes
        
        """
        disable = self.__disableRecurrenceChanges()
        
        class NoModContextMgr(object):
            def __enter__(self):
                pass

        result = NoModContextMgr()
                
        if disable:
            def exit(exc_type, exc_val, exc_tb):
                delattr(self.itsItem, EventStamp.IGNORE_CHANGE_ATTR)
                return False
        else:
            def exit(exc_type, exc_val, exc_tb):
                return False
                
        result.__exit__ = exit
        return result
        

    def InitOutgoingAttributes(self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        self.itsItem.InitOutgoingAttributes()
        self.summary = _(u"New Event")

    def initialStartTime(self):
        defaultTz = TimeZoneInfo.get(self.itsItem.itsView).default
        now = datetime.now(defaultTz)
        roundedTime = time(hour=now.hour, minute=(now.minute/30)*30,
                           tzinfo=defaultTz)
        return datetime.combine(now, roundedTime)
        
    def initialOrganizer(self):
        return schema.ns("osaf.pim", self.itsItem.itsView).currentContact.item

    schema.initialValues(
        startTime=initialStartTime,
        duration=lambda self: timedelta(hours=1),
        organizer=initialOrganizer,
    )

    def add(self):
        """
        Init only the attributes specific to this mixin.
        """
        with self.noRecurrenceChanges():
            super(EventStamp, self).add()

        # TBD - set participants to any existing "who"
        # participants are currently not implemented.

    def remove(self):
        """
        Override remove to deal with unstamping EventStamp on
        recurring events.

        When removing EventStamp, first add the item's recurrenceID
        to the exclusion list, so the item doesn't reappear after unstamping.

        """
        if not self.itsItem.isProxy:
            if self.occurrenceFor is not None:
                with self.noRecurrenceChanges():
                    del self.occurrenceFor
            elif self.rruleset is not None:
                self.removeRecurrence()
                
            # Delete any relative user reminders, as well as any
            # triageStatus reminders
            toDelete = list(r for r in self.itsItem.reminders
                            if hasattr(r, 'delta'))
                  
            for rem in toDelete:
                logger.debug("Destroying obsolete %s on %s", rem)
                rem.delete(recursive=True)

        super(EventStamp, self).remove()
        
        if self.itsItem.displayName == _("New Event"):
            self.itsItem.displayName = _("Untitled")

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
            # allDay should be first, because it takes precedence over anyTime
            if self.allDay: 
                fmt = (sameDate and _(u'%(startDay)s, %(startDate)s all day%(recurrenceSeparator)s%(recurrence)s')
                       or _(u'%(startDate)s - %(endDate)s all day%(recurrenceSeparator)s%(recurrence)s'))
            elif self.anyTime:
                fmt = (sameDate and _(u'%(startDay)s, %(startDate)s any time%(recurrenceSeparator)s%(recurrence)s')
                       or _(u'%(startDate)s - %(endDate)s, any time%(recurrenceSeparator)s%(recurrence)s'))
            else:
                fmt = (sameDate and _(u'%(startDay)s, %(startDate)s %(startTime)s - %(endTimeTz)s%(recurrenceSeparator)s%(recurrence)s')
                       or _(u'%(startDay)s, %(startDate)s %(startTime)s - %(endDay)s, %(endDate)s %(endTimeTz)s%(recurrenceSeparator)s%(recurrence)s'))

        recurrenceDescription = self.getCustomDescription()
        # @@@ this could probably be made 'lazy', to only format the values we need...
        view = self.itsItem.itsView
        return fmt % {
            'startDay': DateTimeUtil.weekdayName(self.startTime),
            'startDate': DateTimeUtil.mediumDateFormat.format(view, self.startTime),
            'startTime': DateTimeUtil.shortTimeFormat.format(view, self.startTime),
            'startTimeTz': formatTime(view, self.startTime),
            'endDay': DateTimeUtil.weekdayName(self.endTime),
            'endDate': DateTimeUtil.mediumDateFormat.format(view, self.endTime),
            'endTime': DateTimeUtil.shortTimeFormat.format(view, self.endTime),
            'endTimeTz': formatTime(view, self.endTime),
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
        try:
            start, duration = self.startTime, self.duration
        except AttributeError:
            return None
        else:
            return start + duration

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


    @staticmethod
    def _getEffectiveStartTime(uuidOrEvent, view=None):
    
        if isuuid(uuidOrEvent):
            allDay, anyTime, startTime = view.findInheritedValues(
                    uuidOrEvent,
                    (EventStamp.allDay.name, False),
                    (EventStamp.anyTime.name, False),
                    (EventStamp.startTime.name, None))
        else:
            allDay = getattr(uuidOrEvent, 'allDay', False)
            anyTime = getattr(uuidOrEvent, 'anyTime', False)
            startTime = getattr(uuidOrEvent, 'startTime', None)
            view = uuidOrEvent.itsItem.itsView
        
        if startTime is None:
            return None
        
        if anyTime or allDay:
            startOfDay = time(0, tzinfo=view.tzinfo.floating)
            return datetime.combine(startTime, startOfDay)
        else:
            return startTime

    def getEffectiveStartTime(self):
        """
        Get the effective start time of this event: ignore the time
        component of the startTime attribute if this is an allDay
        or anyTime event.
        """
        return self._getEffectiveStartTime(self)

    effectiveStartTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(startTime, allDay, anyTime),
        fget=getEffectiveStartTime,
        doc="Start time, without time if allDay/anyTime")
        
    @staticmethod
    def _getEffectiveEndTime(uuidOrEvent, view=None):
        if isuuid(uuidOrEvent):
            allDay, anyTime, startTime, duration = view.findInheritedValues(
                    uuidOrEvent,
                    (EventStamp.allDay.name, None),
                    (EventStamp.anyTime.name, None),
                    (EventStamp.startTime.name, None),
                    (EventStamp.duration.name, None))
        else:
            allDay = getattr(uuidOrEvent, 'allDay', False)
            anyTime = getattr(uuidOrEvent, 'anyTime', False)
            startTime = getattr(uuidOrEvent, 'startTime', None)
            duration = getattr(uuidOrEvent, 'duration', None)
        
                    
        if startTime is None:
            return None
        elif duration is None:
            duration = timedelta(0)

        endTime = startTime + duration
        if anyTime or allDay:
            # all day events include their endtime, so they end at midnight
            # one day later than their normal end date.
            return datetime.combine(endTime + timedelta(1),
                                    time(0, tzinfo=endTime.tzinfo))
        else:
            return endTime

    def getEffectiveEndTime(self):
        """
        Get the effective end time of this event: ignore the time
        component of the endTime attribute if this is an allDay
        or anyTime event.
        """
        return self._getEffectiveEndTime(self)

    effectiveEndTime = schema.Calculated(
        schema.DateTimeTZ,
        basedOn=(startTime, allDay, anyTime, duration),
        fget=getEffectiveEndTime,
        doc="End time, without time if allDay/anyTime")

    @schema.observer(startTime, allDay, anyTime)
    def onStartTimeChanged(self, op, name):
        # Update our relative reminders. If necessary, add a relative reminder
        # to fire at our effectiveStartTime and update triageStatus.
        
        try:
            newStartTime = self.effectiveStartTime
        except AttributeError:
            pass
        else:
            onlyReminder = (self.rruleset is None or
                            self.itsItem.hasLocalAttributeValue('reminders'))
            isMaster = (self.occurrenceFor is None and self.rruleset is not None)
            
            for reminder in self.itsItem.reminders:
            
                # Absolute-time reminders don't need to change
                if not hasattr(reminder, 'delta'):
                    continue
                
                if isMaster or onlyReminder:
                    reminder.itemChanged(self.itsItem)
                    
        # Update our display-date attribute, too
        self.itsItem.updateDisplayDate(op, name)

    def addDisplayDates(self, dates, now):
        effectiveStartTime = getattr(self, 'effectiveStartTime', None)
        if effectiveStartTime is not None:
            dates.append((effectiveStartTime < now and 20 or 10,
                          effectiveStartTime, 'startTime'))

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
        """Find the last modification's rruleset, return its until value.

        @rtype: C{datetime} or C{None}

        """
        # for no-THISANDFUTURE, this is just return until
        if self.rruleset is None:
            return None
        lastUntil = None
        for rule in getattr(self.rruleset, 'rrules', None) or []:
            until = getattr(rule, 'until', None)
            if until is not None:
                if lastUntil is None or lastUntil < until:
                    lastUntil = until
        return lastUntil
        

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
        if self != self.getMaster():
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
        
    @staticmethod
    def _isBetween(self, after, before, inclusive, showUI):
        # Broken out into a staticmethod to avoid recalculating showUI
        if showUI:
            lte = datetime.__le__
            lt = datetime.__lt__
        else:
            def lte(dt1, dt2):
                return dt1.replace(tzinfo=None) <= dt2.replace(tzinfo=None)
            def lt(dt1, dt2):
                return dt1.replace(tzinfo=None) < dt2.replace(tzinfo=None)
        
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

    def isBetween(self, after=None, before=None, inclusive=True):
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
        showUI = schema.ns('osaf.pim', self.itsItem.itsView).TimezonePrefs.showUI
        
        return self._isBetween(self, after, before, inclusive, showUI)
                               

    def createDateUtilFromRule(self, *args, **kw):
        """Construct a dateutil.rrule.rruleset from self.rruleset.

        @see: L{Recurrence.RecurrenceRuleSet.createDateUtilFromRule}
        @return: C{dateutil.rrule.rruleset}

        """
        first = self.getFirstInRule()
        if first != self:
            return first.createDateUtilFromRule(*args, **kw)
        else:
            dtstart = self.getEffectiveStartTime()
            return self.rruleset.createDateUtilFromRule(dtstart, *args, **kw)

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
        if self.rruleset is not None:
            self.removeRecurrence()
        else:
            self.__disableRecurrenceChanges()

    def _changeAllStamps(self, change):
        master = self.getMaster()
        for obj in itertools.chain([master], master.modifications):
            change(obj)

    def addStampToAll(self, stampClass):
        def addIt(obj):
            if not has_stamp(obj, stampClass):
                stampClass(obj).add()
        self._changeAllStamps(addIt)

    def removeStampFromAll(self, stampClass):
        def removeIt(obj):
            if has_stamp(obj, stampClass):
                stampClass(obj).remove()
        self._changeAllStamps(removeIt)


    def _restoreStamps(self, clonedEvent):
        with self.noRecurrenceChanges():
            for stampClass in Stamp(self).stamp_types:
                stampClass(clonedEvent).add()

    def _createOccurrence(self, recurrenceID):
        """
        Generate an occurrence for recurrenceID, return it.
        """

        first = self.getFirstInRule()
        if first != self:
            return first._createOccurrence(recurrenceID)
            
        # It's possible this method has been called on a proxy; in that
        # case, we should make sure we're dealing with the "real"
        # item.
        item = first.itsItem.getMembershipItem()
        
        
        values = {
            EventStamp.isGenerated.name: True,
            EventStamp.recurrenceID.name: recurrenceID,
            EventStamp.startTime.name: recurrenceID,
            EventStamp.occurrenceFor.name: item,
        }

        item = Occurrence.getKind(item.itsView).instantiateItem(
                None,
                item.itsParent,
                UUID(),
                withInitialValues=False)
        
        event = EventStamp(item)
        with event.noRecurrenceChanges():
            for key, value in values.iteritems():
                setattr(item, key, value)

            # set the item's triageStatus explicitly, but don't create a
            # modification
            item.setTriageStatus(event.autoTriage())

            # occurrences should all start with a local True value for
            # doAutoTriageOnDateChange, regardless of what this was set to on the
            # master
            item.doAutoTriageOnDateChange = True

        return event

    def makeOrphan(self):
        """
        Take an existing recurrence modification, copy its attributes into a new
        item, then delete the original modification.  Return the new orphan.
        
        """
        master = getattr(self, 'occurrenceFor', None)

        if master is None:
            return None
        
        orphan = master.copy(cloudAlias='copying')
        
        # we just copied the master's rruleset, get rid of it
        EventStamp(orphan).removeRecurrence()
        
        orphanEvent = EventStamp(orphan)
        orphanEvent.startTime = self.startTime

        for key, value in self.itsItem.iterModifiedAttributes():
            setattr(orphan, key, value)

        self._copyCollections(master, orphan)

        self._safeDelete()
        return orphan

    def getNextOccurrence(self, after=None, before=None):
        """Return the next occurrence for the recurring event self is part of.

        If self is the only occurrence, or the last occurrence, return None.
        
        If self is a master event and after is None, raise ValueError, as it's
        proved error prone to figure out what getNextOccurrence on a master
        means.  To get the first occurrence, use the getFirstOccurrence method.

        @param after: Earliest end time allowed
        @type  after: C{datetime} or C{None}

        @param before: Latest start time allowed
        @type  before: C{datetime} or C{None}
        
        @rtype: C{EventStamp}

        """
        
        if self.rruleset is None:
            return None
        
        if self.getMaster() == self and after is None:
            raise ValueError, "getNextOccurrence cannot be called on a master "\
                              "if after is None. Use getFirstOccurrence instead"
        
        
        if after is None:
            after = self.effectiveStartTime
            
        iterEvents = self._generateRule(after, before, inclusive=True)
        
        try:
            if self != self.getFirstInRule():
                while True:
                    q = iterEvents.next()
                    if q == self:
                        break
                    else:
                        pass
                        #print '*** skipping %s (startTime=%s)' % (q, q.startTime)
            result = iterEvents.next()
            #print '*** result is %s (startTime=%s)' % (result, result.startTime)
        except StopIteration:
            return None
        else:
            return result # @@@ [grant] not right if we did an inclusive match
                          # on before

    def _generateRule(self, after=None, before=None, inclusive=False,
                      occurrenceCreator=_createOccurrence):
        """Yield occurrences in this rule."""
        
        #
        # Timezone behaviour: This method does not pay any attention to
        # the user's TimeZone preferences; i.e. all comparisons use
        # tzinfo, regardless of that setting. If you need to call
        # _generateRule() with after or before, call adjustSearchTimes()
        # first.
        
        first = self.getMaster()

        if self.rruleset is None:
            return

        ruleset = first.createDateUtilFromRule()
        
        # exact means this is a search for a specific recurrenceID
        exact = after is not None and after == before
        
        # inclusive means events starting at exactly after should be allowed.
         
        # check for modifications taking place before first, but only if
        # if we're actually interested in dates before first (i.e., the
        # after argument is None or less than first.startTime)
 
        if exact or not first.modifications:
            mods = []
        else:
            iterMods = itertools.imap(EventStamp, first.modifications)
            mods = sorted((mod for mod in iterMods
                            if mod.isBetween(after, before, inclusive)),
                          key=EventStamp.getEffectiveStartTime)

        # take duration into account if after is set
        if not exact and after is not None:
            # @@@ [grant] use self.duration here??
            start = after - (self.effectiveEndTime - self.effectiveStartTime)
        else:
            start = self.effectiveStartTime

        def iterRecurrenceIDs():
            if after is not None:
                if (exact or (inclusive and (after <= start))):
                    if after in ruleset:
                        yield after

            if not exact:
                if after is not None:
                    current = ruleset.after(start)
                    #print '*** ruleset.after() --> setting current=%s' % (current,)
                else:
                    try:
                        current = iter(ruleset).next()
                        #print '*** iter(ruleset).next() setting current=%s' % (current,)
                    except StopIteration:
                        current = None

                while ((current is not None) and
                       (before is None or current < before)):
                    #print '*** yielding current=%s' % (current,)
                    yield current
                    current = ruleset.after(current)

                if inclusive and (before is not None) and (before in ruleset):
                    yield before

        for recurrenceID in iterRecurrenceIDs():
            #print '*** recurrenceID=%s' % (recurrenceID,)

            knownOccurrence = self.getExistingOccurrence(recurrenceID)

            # yield all the matching modifications
            while mods and (mods[0].effectiveStartTime < recurrenceID):
                yield mods.pop(0)

            if knownOccurrence is None:
                yield occurrenceCreator(self, recurrenceID)
            elif exact or knownOccurrence.modificationFor is None:
                yield knownOccurrence
  
        # Finally, yield any remaining mods
        for m in mods:
            yield m


    def _getFirstGeneratedOccurrence(self, create=False):
        """Return the first generated occurrence or None.

        If create is True, create an occurrence if possible.

        """
        if self.rruleset is None: return None

        first = self.getFirstInRule()
        if first != self: return first._getFirstGeneratedOccurrence(create)

        # make sure recurrenceID gets set for all masters
        if self.recurrenceID is None:
            self.recurrenceID = self.effectiveStartTime

        if create:
            i = iter(event.itsItem for event in self._generateRule())
        else:
            if self.occurrences is None:
                return None
            i = _sortEvents(self.occurrences)
        isGeneratedAttrName = EventStamp.isGenerated.name 
        for item in i:
            if getattr(item, isGeneratedAttrName):
                return EventStamp(item)
        # no generated occurrences
        return None

    def getOccurrencesBetween(self, after, before, inclusive=False):
        """Return a list of events ordered by startTime.

        Get events starting on or before "after", ending on or after "before".
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
        showUI = schema.ns('osaf.pim', self.itsItem.itsView).TimezonePrefs.showUI
        master = self.getMaster()
        result = []
        
        if not master.hasLocalAttributeValue('rruleset'):
            if EventStamp._isBetween(master, after, before, inclusive, showUI):
                result.append(master)
        else:
            if not inclusive and not master.duration and not isDayEvent(master):
                # zero-duration events at midnight aren't found if inclusive is
                # False and the event's startTime matches start.
                inclusive = True
            
            searchAfter, searchBefore = adjustSearchTimes(after, before, showUI)
            for event in master._generateRule(searchAfter, searchBefore,
                                              inclusive):
                if EventStamp._isBetween(event, after, before, inclusive, showUI):
                    result.append(event)
        

        return result
        
    def iterBusyInfo(self, after, before):

        master = self.getMaster()
            
        if (not master.hasLocalAttributeValue('rruleset')
            and master.isBetween(after, before, True)):
                yield master, master.effectiveStartTime
        else:
            def makeOccurrence(master, recurrenceID):
                return (master, recurrenceID)
                
            for result in master._generateRule(after, before, True,
                                               makeOccurrence):
               if isinstance(result, tuple):
                   yield result
               else:
                   yield result, result.effectiveStartTime

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

        # no existing matches, see if this occurrence matches the rruleset:
        rruleset = self.createDateUtilFromRule()
        recurrenceID = recurrenceID.astimezone(self.effectiveStartTime.tzinfo)
        if recurrenceID in rruleset:
            return self._createOccurrence(recurrenceID)

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
        try:
            return master._generateRule().next()
        except StopIteration:
            return None

        recurrenceID = master.effectiveStartTime
        occurrence = self.getExistingOccurrence(recurrenceID)

        def checkModifications(event):
            """Return the earliest modification coming before event, or event"""
            earliest = event
            for mod in itertools.imap(EventStamp, master.modifications):
                if (mod.effectiveStartTime < earliest.effectiveStartTime or
                    (mod.effectiveStartTime == earliest.effectiveStartTime and
                     mod.recurrenceID  < earliest.recurrenceID)):
                    earliest = mod
            return earliest       
        
        if occurrence is None:
            rruleset = self.createDateUtilFromRule()
            try:
                earliestTime = iter(rruleset).next()
            except StopIteration:
                pass
            else:
                occurrence = self.getExistingOccurrence(earliestTime)
                
                if occurrence is None:
                    occurrence = self._createOccurrence(earliestTime)

        
        if occurrence is None:
            return None
        else:
            return checkModifications(occurrence)
            
    def _makeGeneralChange(self):
        """Do everything that should happen for any change call."""
        self.isGenerated = False

    def _safeDelete(self):
        """
        Handle the finicky order of attribute deletion for deleting individual
        recurring events.
        """
        if not isDead(self.itsItem):
            self.__disableRecurrenceChanges()
            del self.rruleset
            del self.occurrenceFor
            del self.modificationFor
            # I'm not sure why we need to do explicitly delve into collections,
            # but keeping it for stability's sake - jeffrey
            for coll in list(getattr(self.itsItem, 'appearsIn', ())):
                if self.itsItem in getattr(coll, 'inclusions', ()):
                    coll.inclusions.remove(self.itsItem)
            self.itsItem.delete()

    def _grabOccurrences(self, occurrences, attrName, deleteIfNotMatching):
        """
        An internal method called when occurrences are being reassigned
        from one master to another, or when recurrence has changed and
        a master has to filter out the occurrences that no longer match.
        
        @param occurrences: The Occurrences whose master should become self
        @type occurrences: iterable or None
        
        @param deleteIfNotMatching: If set to True, non-modifications and
                                    triage-only modifications that
                                    don't match the self's rruleset are
                                    deleted. (This is for the changed recurrence
                                    case).
        @type deleteIfNotMatching: bool

        @param attrName: An attribute to delete from occurrences if they
                         match. This is for a THISANDFUTURE change when some
                         modifications already changed an attribute.
        @type attrName: str or None
        """
        rruleset = self.createDateUtilFromRule()
        selfItem = self.itsItem
        
        for occurrence in itertools.imap(EventStamp, occurrences or []):
            with occurrence.noRecurrenceChanges():
                if occurrence.recurrenceID in rruleset:
                    if occurrence.occurrenceFor is not selfItem:
                        occurrence.occurrenceFor = selfItem
                        
                        if occurrence.modificationFor is not None:
                            occurrence.modificationFor = selfItem
                            
                    if (attrName is not None and 
                        occurrence.itsItem.hasLocalAttributeValue(attrName)):
                        delattr(occurrence.itsItem, attrName)
                        
                elif deleteIfNotMatching and (
                                occurrence.modificationFor is None or 
                                (occurrence.isTriageOnlyModification() and
                                 occurrence.itsItem.doAutoTriageOnDateChange)):
                    occurrence._safeDelete()

        if not self.occurrences: # None or empty
            self.getFirstOccurrence()

        self.updateTriageStatus(True)
        self.triageForRecurrenceAddition()

    def deleteOffRuleModifications(self):
        """
        Delete all modifications that don't match the current recurrence rule.
        
        Changes to recurrence will call _grabOccurrences, which will delete
        triage-only modifications and occurrences that are off rule, but not
        all off-rule modifications.
        """
        rruleset = self.createDateUtilFromRule()
        selfItem = self.itsItem
        
        for modification in itertools.imap(EventStamp,
                                           self.modifications or Nil):
            if modification.recurrenceID not in rruleset:
                modification._safeDelete()

    def changeThisAndFuture(self, attr=None, value=None):
        """Modify this and all future events."""
        master = self.getMaster()
        first = master # Changed for no-THISANDFUTURE-style
        if self.recurrenceID is None:
            self.recurrenceID = self.effectiveStartTime
        recurrenceID = self.recurrenceID
        # we can't use master.effectiveStartTime because the event timezone and
        # the current timezone may not match
        isFirst = (self == first) or (((master.allDay or master.anyTime) and
                    recurrenceID.date() == master.effectiveStartTime.date()) or
                   (recurrenceID == master.effectiveStartTime))
                   
        if isFirst and self != first:
            # We're the occurrence for the master (but not
            # the master itself). Just let the master handle
            # everything.
            if self.modificationFor is not None and attr is not None:
                # if the modification already had a change to this attribute,
                # just changing the master isn't enough, the change won't be
                # reflected in the modification.  In that case, make sure the
                # change happens to this item, not just the master
                for modattr, modvalue in self.itsItem.iterModifiedAttributes():
                    if attr == modattr:
                        with self.noRecurrenceChanges():
                            delattr(self.itsItem, attr)
                        break

            return first.changeThisAndFuture(attr, value)
            
        
        # So, from now on, either self is a master, or it's an occurrence that
        # doesn't correspond to the master.
        
        #startChanging = attr in (EventStamp.startTime.name,
        #                         )
        with self.noRecurrenceChanges():
            if attr == EventStamp.startTime.name:
                startTimeDelta = (value.replace(tzinfo=None) -
                                  self.startTime.replace(tzinfo=None))
                tzChanged = value.tzinfo != self.startTime.tzinfo

                if startTimeDelta or tzChanged:
                    if first.allDay or first.anyTime:
                        recurrenceIDDelta = value.date() - self.startTime.date()
                    else:
                        recurrenceIDDelta = startTimeDelta
                
                    def makeChangeFn(delta, tzChanged):
                        def change(dt):
                            if delta:
                                dt = dt + delta
                            if tzChanged:
                                dt = dt.replace(tzinfo=value.tzinfo)
                            return dt
                        return change
                    
                    changeStart = makeChangeFn(startTimeDelta, tzChanged)
                    changeRecurrenceID = makeChangeFn(recurrenceIDDelta,
                                                      tzChanged)
                    
                    self.rruleset.transformDatesAfter(recurrenceID, changeStart)
                
                    
                    for occurrence in itertools.imap(EventStamp,
                                                     first.occurrences or []):
                        occurrenceID = occurrence.recurrenceID
                        if occurrenceID >= recurrenceID:
                            occurrenceStart = occurrence.effectiveStartTime
                            with occurrence.noRecurrenceChanges():
                                if (occurrenceID == occurrenceStart and
                                    occurrenceID.tzinfo == occurrenceStart.tzinfo):
                                    # don't change start time if its a startTime
                                    # modification
                                    occurrence.startTime = changeStart(
                                                        occurrence.startTime)
                                occurrence.recurrenceID = changeRecurrenceID(
                                                                occurrenceID)
                
            elif attr in (EventStamp.allDay.name, EventStamp.anyTime.name):
                # if startTime changes (and an allDay/anyTime change changes
                # effective startTime), all future occurrences's recurrenceIDs
                # need to be adjusted appropriately
                if attr == EventStamp.allDay.name:
                    otherAllDayness = self.anyTime
                else:
                    otherAllDayness = self.allDay
                if (value or otherAllDayness) != (getattr(self.itsItem, attr) or
                                                      otherAllDayness):
                # We update all the recurrenceIDs so that they either start
                # @ midnight (anyTime/allDay), or @ first's startTime
                # (including timezone). There's no need to update the
                # startTimes of the occurrences, since their effectiveStartTime
                # will still be calculated correctly.
                    if value:
                        recurrenceTime = time(0, tzinfo=self.itsItem.itsView.tzinfo.floating)
                    else:
                        recurrenceTime = first.startTime.timetz()
    
                    for occurrence in itertools.imap(EventStamp,
                                                     first.occurrences or []):
                        with occurrence.noRecurrenceChanges():
                            occurrence.recurrenceID =  datetime.combine(
                                                occurrence.startTime.date(),
                                                recurrenceTime)
                    
            if attr is not None:
                setattr(self.itsItem, attr, value)
            
            if isFirst:
                # Make sure master's recurrenceID matches its effectiveStartTime
                self.recurrenceID = self.effectiveStartTime
                if attr == EventStamp.rruleset.name: # rule change, thus a destructive change
                    oldReminders = list(self.itsItem.reminders)
                    newReminders = []
                    for rem in oldReminders:
                        # Convert absolute-time reminders to delta-time ones
                        if hasattr(rem, 'delta'):
                            newReminder = rem.copy(cloudAlias="copying")
                        else:
                            newReminder = RelativeReminder(
                                itsView=self.itsItem.itsView,
                                userCreated=rem.userCreated,
                                promptUser=rem.promptUser,
                                delta=rem.absoluteTime - self.effectiveStartTime  
                            )
                        newReminders.append(newReminder)
                        rem.delete(recursive=True)
                        
                    self.itsItem.reminders = newReminders

                    # _grabOccurrence isn't needed after most changes to all
                    # occurrences, but since rruleset was changed, it needs to
                    # be called here
                    master._grabOccurrences(master.occurrences, None, True)

                elif attr in (EventStamp.allDay.name, EventStamp.anyTime.name,
                        EventStamp.startTime.name):
                    # update triage status for an effectiveStartTime change
                    self.updateTriageStatus(True)
            else:
                # If we're not first, we're an occurrence (and not the master's
                # occurrence). So, we generate a new master, truncate the old
                # master before our recurrenceID, and move the occurrences over
                # accordingly.
                 # Exclude stamps, since add() does something good here
                newMasterItem = first.itsItem.clone(None, None,
                                     ('collections', Stamp.stamp_types.name, 'reminders'))
                newMaster = EventStamp(newMasterItem)
                
                with newMaster.noRecurrenceChanges():
                    first._restoreStamps(newMaster)
                
                    newMaster.updateRecurrenceEnd()
                    
                    for rem in first.itsItem.reminders:
                        newReminder = rem.copy(cloudAlias="copying")
                        newReminder.reminderItem = newMasterItem
        
                    if attr != EventStamp.rruleset.name:
                        newMaster.rruleset = first.rruleset.copy(cloudAlias='copying')
                        newMaster.rruleset.removeDates(datetime.__lt__, recurrenceID)
                
                    # There are two events in play, self (which has been
                    # changed), and newMaster, a non-displayed item used to
                    # define generated events.  Make sure the current change
                    # is applied to both items. Note that Occurrences get
                    # their rruleset from their masters, so there's no
                    # need to reassign
                    if attr is not None:
                        setattr(newMasterItem, attr, value)
                    newMaster.startTime = newMaster.recurrenceID = self.recurrenceID
                    if newMaster.occurrenceFor:
                        del newMaster.occurrenceFor #self overrides newMaster
                    newMaster.itsItem.icalUID = str(newMasterItem.itsUUID)
                    newMaster._makeGeneralChange()
                    
                    self._copyCollections(master, newMaster)
                    
                    #if startChanging:
                        #attrToDrop = None
                    #else:
                        #attrToDrop = attr
                    attrToDrop = None ## Not clear if this is needed
                    newMaster._grabOccurrences(master.occurrences, attrToDrop,
                                               False)

                    # We want to do this after _grabOccurrences, so
                    # that master doesn't go remove the occurrences itself.
                    master.moveRuleEndBefore(recurrenceID)

            if not isFirst:
                master._grabOccurrences(master.occurrences, None, True)
            
    def changeAll(self, attr=None, value=None):
        master = self.getMaster()
        isStartTime = (attr == EventStamp.startTime.name)
        if attr is not None:
            with self.noRecurrenceChanges():
                # For startTime, treat the changeAll as a request to
                # change the delta of all events, so adjust startTime
                # to be relative to the master.
                if isStartTime:
                    delta = (value.replace(tzinfo=None) -
                             self.startTime.replace(tzinfo=None))
                    value = (master.startTime + delta).replace(
                                tzinfo=value.tzinfo)
                    # Revert self's startTime change (if any)
                    self.startTime = self.recurrenceID
                else:
                    # If self is a modification that has a change to
                    # this event, delete the attribute, since we're
                    # going to pick up the master's value
                    if (self.modificationFor is not None and
                        self.itsItem.hasLocalAttributeValue(attr)):
                        delattr(self.itsItem, attr)
        master.changeThisAndFuture(attr, value)

    def moveCollections(self, fromEvent, toEvent):
        """Move all collection references from one event to another."""
        fromItem = fromEvent.itsItem.getMembershipItem()
        toItem = toEvent.itsItem.getMembershipItem()

        for collection in getattr(fromItem, 'collections', Nil):
            collection.add(toItem)
            collection.remove(fromItem)

    def _copyCollections(self, fromEvent, toEvent, removeOld=False):
        """Copy all collection references from one item to another."""
        fromEvent = EventStamp(fromEvent)
        toEvent = EventStamp(toEvent)
        fromItem = fromEvent.itsItem.getMembershipItem()
        toItem = toEvent.itsItem

        if toEvent.occurrenceFor is None or toEvent.modificationFor is None:
            toItem = toItem.getMembershipItem()
            
        fromCollections = getattr(fromItem, 'collections', Nil)

        # We really, really want modifications to get their
        # own copy of collections, so that the biref doesn't
        # get all messed up
        if not toItem.hasLocalAttributeValue('collections'):
            toItem.collections = []
            
        if removeOld:
            for collection in getattr(toItem, 'collections', Nil):
                if collection not in fromCollections:
                    collection.remove(toItem)
        
        for collection in fromCollections:
            collection.add(toItem)

    def changeThis(self, attr=None, value=None, setWithHandlerDisabled=False):
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
                backup = self.getRecurrenceID(self.effectiveStartTime)
                if backup is not None:
                    return backup.changeThis(attr, value)
                else:
                    # if backup is None, that means that the master's
                    # occurrence isn't included in the rule. Hmm, that's
                    # confusing. Maybe we should raise?
                    if master == self:
                        self.recurrenceID = self.effectiveStartTime
            else:
                self.modificationFor = first.itsItem
                self._makeGeneralChange()
                # Need to copy over the master's stamps ... ew
                with self.noRecurrenceChanges():

                    if not self.itsItem.hasLocalAttributeValue(Stamp.stamp_types.name):
                        Stamp(self).stamp_types = set()
                    stamp_types = Stamp(first).stamp_types
                    if stamp_types is not None:
                        for stamp in list(stamp_types):
                            if not stamp in iter(Stamp(self).stamp_types):
                                stamp(self).add()
                    stamp_types = Stamp(first).stamp_types
                    if stamp_types is not None:
                        for stamp in list(Stamp(self).stamp_types):
                            if not stamp in Stamp(first).stamp_types:
                                stamp(self).remove()
                    self._copyCollections(first, self)

                        
        if attr is not None:
            if setWithHandlerDisabled:
                disabled = self.__disableRecurrenceChanges()
            setattr(self.itsItem, attr, value)
            if attr is EventStamp.rruleset.name:
                self.updateRecurrenceEnd()
            elif attr in (EventStamp.startTime.name, EventStamp.anyTime.name,
                          EventStamp.allDay.name):
                if self.modificationFor is not None:
                    # only do autoTriage for changes to recurring events,
                    # setTriageStatus should always be called explicitly for
                    # non-recurring events somewhere else
                    newTriage = self.autoTriage()
                    if (self.itsItem._triageStatus != newTriage and
                        self.itsItem.doAutoTriageOnDateChange):
                        self.itsItem.setTriageStatus(newTriage, pin=True)
            if setWithHandlerDisabled and disabled:
                disabled = self.__enableRecurrenceChanges()               
                
    def getLastPastDone(self):
        """
        Return the recurrence-id of the last occurrence triaged DONE that's in
        the past, if one exists (or can be created).  Otherwise return None.
        """
        defaultTz = TimeZoneInfo.get(self.itsItem.itsView).default
        now = datetime.now(defaultTz)
        master = self.getMaster()
        if master.rruleset is None:
            # this isn't useful on a non-recurring event
            return None

        # run backwards through recurrenceIDs till a DONE occurrence is found
        rruleset = master.rruleset.createDateUtilFromRule(master.effectiveStartTime)
        earlierRecurrenceID = rruleset.before(now)
        while earlierRecurrenceID is not None:
            pastOccurrence = master.getRecurrenceID(earlierRecurrenceID)
            assert pastOccurrence is not None, "Invalid recurrence-id"
            if pastOccurrence.effectiveEndTime > now:
                # it's happening now, it's not done yet
                pass
            elif pastOccurrence.modificationFor is None:
                pastOccurrence.itsItem.setTriageStatus(TriageEnum.done)
                pastOccurrence.changeThis()
                return pastOccurrence.recurrenceID
            elif pastOccurrence.itsItem._triageStatus == TriageEnum.done:
                return pastOccurrence.recurrenceID

            earlierRecurrenceID = rruleset.before(earlierRecurrenceID)

    def getFirstFutureLater(self):
        """
        Return the recurrenceID of the first future LATER event, or None.
        
        A side effect is to turn any in progress occurrences into modifications.
        
        """
        defaultTz = TimeZoneInfo.get(self.itsItem.itsView).default
        now = datetime.now(defaultTz)        
        master = self.getMaster()
        # run through future occurrences to find a LATER
        for occurrence in master._generateRule(after=now):
            if occurrence.effectiveStartTime < now:
                # _generateRule includes events that start in the past but are
                # ongoing.  Make sure such events are modifications
                occurrence.changeThis()
                continue
            if occurrence.modificationFor is not None:
                if occurrence.itsItem.triageStatus == TriageEnum.later:
                    return occurrence.recurrenceID
            else:
                occurrence.itsItem.setTriageStatus(TriageEnum.later)
                # setTriageStatus won't set up modificationFor, so explicitly
                # set modificationFor and copy collections
                return occurrence.recurrenceID

    def autoTriage(self):
        """
        What triage status should this item have?
        """
        if not has_stamp(self, EventStamp):
            return TriageEnum.now
        item = self.itsItem
        now = datetime.now(tz=item.itsView.tzinfo.default)
        if self.effectiveStartTime > now:
            # Hasn't started yet? it's Later.
            status = TriageEnum.later
        else:
            reminder = item.getUserReminder()
            reminderTime = (reminder is not None
                            and reminder.getReminderTime(item)
                            or Reminder.distantPast)
            if reminderTime > now:
                # Doesn't start in the future, but has a reminder there: Later.
                status = TriageEnum.later
            elif self.effectiveEndTime < now:
                # It already ended - it's done.
                status = TriageEnum.done
            else: # It's ongoing: now.
                status = TriageEnum.now

        return status

    def triageForRecurrenceAddition(self):
        """
        When initially adding recurrence, the first occurrence is treated
        specially, for more info see bug 7904.
        
        This method should be called after an initial updateTriageStatus,
        because subsequent updates may cause the first occurrence to be
        unmodified.
        
        """
        master = self.getMaster()
        firstOccurrence = master.getRecurrenceID(master.effectiveStartTime)
        if firstOccurrence is None:
            # This can happen if there's an EXDATE deleting the first occurrence
            return
        firstItem = firstOccurrence.itsItem
        wasModification = firstOccurrence.modificationFor is not None
        oldTriageStatus = firstItem._triageStatus
        if not firstItem.hasLocalAttributeValue('_sectionTriageStatus'):
            firstItem.copyTriageStatusFrom(master.itsItem)
        # don't let masters keep their _sectionTriageStatus, if they do it'll
        # be inherited inappropriately by modifications
        master.itsItem.purgeSectionTriageStatus()
        
        # if the master's triage status was NOW because it was just created, 
        # don't leave it that way, it's enough to pin it in the NOW section.
        # Because force isn't set, this will preserve _sectionTriageStatus
        # if the master happened to be pinned already
        firstItem.setTriageStatus('auto', pin=True)
        
        if wasModification and oldTriageStatus == TriageEnum.later:
            # this occurrence was the token Later occurrence, make sure there's
            # a new token later
            if firstItem._triageStatus != TriageEnum.later:
                self.getFirstFutureLater()


    def updateTriageStatus(self, checkOccurrences=False):
        """
        If appropriate, make sure there's at least one LATER modification in the
        future and at least one DONE modification in the past.
        
        Also collapse DONE and LATER modifications whose only change is to
        triageStatus so only one DONE before now and one LATER after now
        is kept.

        If checkOccurrences is True, change triage status for all occurrences,
        this is used when the effectiveStartTime changes.
        
        """
        master = self.getMaster()

        if checkOccurrences:
            for occurrence in master.occurrences or []:
                if occurrence.doAutoTriageOnDateChange:
                    event = EventStamp(occurrence)
                    status = event.autoTriage()
                    with event.noRecurrenceChanges():
                        event.itsItem._triageStatus = status

        firstFutureLater = self.getFirstFutureLater()
        lastPastDone = self.getLastPastDone()
        # run through modifications and unmodify them if their only changes
        # are from autoTriage
        for mod in map(EventStamp, master.modifications):
            item = mod.itsItem
            if ((item._triageStatus == TriageEnum.done and
                 lastPastDone is not None and
                 mod.startTime < lastPastDone) or
                (item._triageStatus == TriageEnum.later and
                 firstFutureLater is not None and 
                 mod.startTime > firstFutureLater)):

                if mod.isTriageOnlyModification():
                    mod.unmodify()

    def isTriageOnlyModification(self):
        if self.modificationFor is None:
            return False
        names = (Triageable._triageStatus.name, 
                 Triageable._triageStatusChanged.name,
                 Triageable.doAutoTriageOnDateChange.name,
                 Triageable._sectionTriageStatus.name,
                 Triageable._sectionTriageStatusChanged.name)
        item = self.itsItem
        for attr, value in item.iterModifiedAttributes():
            if attr in names:
                continue

            return False
        
        return True
                        
    def unmodify(self, partial=False):
        """
        Turn a modification into a normal occurrence.
        
        If partial is True, remove all modified attributes, but leave the item
        as a triage-only modification.
        """
        # turning the modification into an occurrence doesn't
        # remove the item from the master's collections.  For
        # now just empty collections.  Are there circumstances
        # where plain occurrences *should* be in a collection?

        with self.noRecurrenceChanges():
            if not partial:
                self.itsItem.collections = []
            for attr, value in list(self.itsItem.iterModifiedAttributes()):
                # sharing may send an unmodify at times when triage status
                # doesn't match its date, so we need to explicitly change it
                if attr == '_triageStatus':
                    triage = self.autoTriage()
                    if value != triage:
                        self.itsItem.setTriageStatus(triage)
                elif attr == Stamp.stamp_types.name and partial:
                    # don't delete the local set of stamps
                    pass
                elif self.itsItem.hasLocalAttributeValue(attr):
                    delattr(self.itsItem, attr)

            if partial:
                master = EventStamp(self.modificationFor)
                for stampClass in Stamp(master).stamp_types:
                    if not has_stamp(self, stampClass):
                        stampClass(self).add()
                for stampClass in list(Stamp(self).stamp_types):
                    if stampClass not in Stamp(master).stamp_types:
                        stampClass(self).remove()

                assert self.isTriageOnlyModification()
            else:
                self.isGenerated = True
                del self.modificationFor


    @schema.observer(
        ContentItem.displayName, ContentItem.body, ContentItem.lastModified,
        startTime, duration, location, allDay, rruleset, Stamp.stamp_types,
    )
    def onEventChanged(self, op, name):
        """
        Maintain coherence of the various recurring items associated with self
        after an attribute has been changed.

        """
        
        # allow initialization code to avoid triggering onEventChanged
        if (self.rruleset is None or
            getattr(self.itsItem, type(self).IGNORE_CHANGE_ATTR, False) or
            getattr(self.itsItem, '_share_importing', False)):
            return
        # avoid infinite loops
        if name == EventStamp.rruleset.name:
            # A rruleset change is always a THISANDFUTURE change ... 
            # Note that there's currently no way to set it on an Occurrence,
            # so really this code path only happens if there are changes
            # on a recurrence master, or on a non-recurring event.
            self.changeThisAndFuture(name, self.rruleset)
        elif name == Triageable._triageStatus.name:
            # just in case this isn't already a modification, make it one
            self.changeThis()
            # go and create a later modification if this change got rid of our
            # current token later
            self.updateTriageStatus()
        else:
            if DEBUG:
                logger.debug("about to changeThis in onEventChanged(name=%s) for %s", name, str(self))
                logger.debug("value is: %s", getattr(self, name, Nil))
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

    @schema.observer(ContentItem.collections)
    def onCollectionChange(self, op, name):
        if self.itsItem.hasLocalAttributeValue(EventStamp.occurrenceFor.name):
            # code that removes items from collections should generally try
            # getMaster first.  Ignoring collection membership changes for
            # non-masters prevents painful perpetual loops
            return
        for event in self.modifications:
            # @@@FIXME really slow hack, we could use op to be much more
            # precise about this.
            self._copyCollections(self, event, removeOld=True)
        

    def cleanRule(self):
        """
        Do bookkeeping triggered by changes to the recurrence rule.
        
        Delete generated occurrences in the current rule and any out of date
        triage-only modifications.  To delete all off-rule modifications, use
        deleteOffRuleModifications.
        
        """
        # when an attribute on master.rruleset changes, an observer on 
        # RecurrenceRuleSet calls cleanRule (or, in sharing, cleanRule is
        # called explicitly).  master.rruleset doesn't change, but conceptually
        # its changed.  The calendar and minicalendar are watching for
        # master.rruleset changes, queue asynchronous notifications as if
        # master.rruleset changed
        view = self.itsItem.itsView
        for collection in getattr(self.itsItem, 'appearsIn', Nil):
            view.queueNotification(
                collection, 'changed', 'notification', 
                collection.__collection__, self.itsItem.itsUUID,
                (EventStamp.rruleset.name,)
            )

        first = self.getFirstInRule()
        first._grabOccurrences(first.occurrences, None, True)
        first.updateRecurrenceEnd()
        first.updateTriageStatus()

    def moveRuleEndBefore(self, recurrenceID):
        master = self.getMaster()
        master.rruleset.moveRuleEndBefore(master.startTime, recurrenceID)

    def deleteThisAndFuture(self):
        """Delete self and all future occurrences and modifications."""
        # changing the rule will delete self unless self is the master
        master = self.getMaster()
        if self.recurrenceID == master.effectiveStartTime:
            self.deleteAll()
        else:
            self.moveRuleEndBefore(self.recurrenceID)
            master.deleteOffRuleModifications()

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
            del self.occurrenceFor
        else:
            self._safeDelete()

    def deleteAll(self):
        """Delete master, all its modifications, occurrences, and rules."""
        master = self.getMaster()
        rruleset = master.rruleset
        
        for event in map(EventStamp, master.occurrences or []):
            event.__disableRecurrenceChanges()
            event.itsItem.delete(recursive=True)

        # we don't want rruleset's recursive delete to get self yet
        rruleset._ignoreValueChanges = True
        rruleset.delete(recursive=True)

        master.__disableRecurrenceChanges()
        master.itsItem.delete(recursive=True)

    def removeFutureOccurrences(self):
        """Delete all future occurrences and modifications."""
        master = self.getMaster()
        for event in itertools.imap(EventStamp, master.occurrences):
            if event.startTime > self.startTime:
                event.__disableRecurrenceChanges()
                event.itsItem.delete()

    def removeRecurrence(self):
        """
        Remove modifications, rruleset, and all occurrences except master.

        The resulting event will occur exactly once.
        """
        master = self.getMaster()
        rruleset = self.rruleset
        if rruleset is not None:
            rruleset._ignoreValueChanges = True
        
        masterRecurrenceID = master.effectiveStartTime
        masterItem = master.itsItem
        for event in map(EventStamp, master.occurrences or []):
            if (event.recurrenceID == masterRecurrenceID and
                event.modificationFor is masterItem):
                # A THIS modification to master, make sure all its
                # local attributes make their way back over to the
                # master
                with master.noRecurrenceChanges():
                    for attr, value in event.itsItem.iterModifiedAttributes():
                        setattr(master.itsItem, attr, value)
            
            event.__disableRecurrenceChanges()
            event.itsItem.delete(recursive=True)
            
        if rruleset is not None:
            rruleset._ignoreValueChanges = True
            rruleset.delete()

        if hasattr(master, 'rruleset'):
            del master.rruleset

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

    def isRecurring(self):
        """ Is this Event a recurring event? """
        return self.rruleset is not None
    
    def isRecurrenceMaster(self):
        """ Is this Event a master of a recurrence set? """
        return self.rruleset is not None and self.getMaster() == self
    
            
    # @@@ Note: 'Calculated' APIs are provided for both relative and absolute
    # user-set reminders, even though only one reminder (which can be of either
    # flavor) can be set right now. The 'set' functions can replace an existing
    # reminder of either flavor, but the 'get' functions ignore (that is, return
    # 'None' for) reminders of the wrong flavor.
    
    def getUserReminderInterval(self):
        userReminder = self.itsItem.getUserReminder()
        if userReminder is None or userReminder.absoluteTime is not None:
            return None
        return userReminder.delta

    def _removeThisUserReminder(self):
        # Prepares for a THIS change of user reminder interval/time, by
        # making a copy of all non-user reminders from the master, and
        # installing that in self.itsItem.reminders
        item = self.itsItem
        if not item.hasLocalAttributeValue('reminders'):
            userReminder = item.getUserReminder()
            newReminders = list(rem.copy(cloudAlias='copying')
                                     for rem in item.reminders
                                  if rem is not userReminder)
            self.changeThis('reminders', newReminders)

    def setUserReminderInterval(self, delta):
        if self != self.getMaster():
            self._removeThisUserReminder()

        existing = self.itsItem.getUserReminder()
        if delta is not None:
            # Make a new reminder (See bug 8181 for why we set reminderItem
            # separately)
            retval = RelativeReminder(itsView=self.itsItem.itsView, delta=delta)
            if self.itsItem.reminders:
                self.itsItem.reminders.add(retval)
            else:
                self.itsItem.reminders = [retval]
        else:
            retval = None

        if existing is not None:
            existing.delete(recursive=True)
            
        return retval

    userReminderInterval = schema.Calculated(
        schema.TimeDelta,
        basedOn=(Remindable.reminders,),
        fget=getUserReminderInterval,
        fset=setUserReminderInterval,
        doc="User-set reminder interval, computed from the first unexpired reminder."
    )


    
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

def parseText(view, text, locale=None):
    """
    Parses the given text and returns the start date/time and the end date/time and
    a countFlag  and a typeFlag.

    countFlag indicates the number of date/times present in the text. It is an enum.
    0 indicates no date/time, 1 indicates only one date/time, 2 indicates more than one date/time.

    typeFlag indicates the type of date/time information present. It is an ennum too.
    0 indicates no date/time, 1 indicates only date, 2 indicates only time
    and 3 indicates both date and time
    """
    loc = str(locale is not None and locale or getLocale())

    cal = parsedatetime.Calendar(ptc.Constants(loc))
    countFlag = 0   #counts the number of date/times in the text

    # The tokenizer will split large
    # bodies of text in to locale aware sentences.
    st = tokenizer.SentenceTokenizer(text, loc)
    for line in st.nextToken():
        if  countFlag > 1:
            #More than one date time exists.
            break
        else:
            (dt1, dt2, typeFlag) = cal.evalRanges(line)
            if typeFlag != 0:
                countFlag += 1
                # Date/time range exists
                (yr1, mth1, dy1, hr1, mn1, sec1, wd1, yd1, isdst1) = dt1
                (yr2, mth2, dy2, hr2, mn2, sec2, wd2, yd2, isdst2) = dt2

                if typeFlag == 1:
                    #only date exists
                    startTime = datetime(yr1, mth1, dy1, tzinfo=view.tzinfo.default)
                    endTime = datetime(yr2, mth2, dy2, tzinfo=view.tzinfo.default)
                else:
                    #time exists
                    startTime = datetime(yr1, mth1, dy1, hr1, mn1, tzinfo=view.tzinfo.default)
                    endTime = datetime(yr2, mth2, dy2, hr2, mn2, tzinfo=view.tzinfo.default)
            else:
                # Check whether there is a single date/time
                (dt, typeFlag) = cal.parse(line)
                if typeFlag != 0:
                    # Date/time exists
                    countFlag += 1
                    (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = dt

                    if typeFlag == 1:
                    #only date exists
                        startTime = endTime = datetime(yr, mth, dy, tzinfo=view.tzinfo.default)
                    else:
                        #time exists
                        startTime = endTime = datetime(yr, mth, dy, hr, mn, tzinfo=view.tzinfo.default)

    #If no date/time exists or more than one date/time exists,
    #set the date as today's date and time as Anytime
    if (countFlag == 2) or (countFlag == 0):
        (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = localtime()
        startTime = endTime = datetime(yr, mth, dy, tzinfo=view.tzinfo.default)
        typeFlag = 0

    return startTime, endTime, countFlag, typeFlag

def makeCompareMethod(attr=None, getFn=None):
    if getFn is None:
        attrName = attr.name
        def getFn(uuid, view):
            return view.findInheritedValues(uuid, (attrName, None))[0]
    def compare(self, index, u1, u2, vals):
        view = self.itsView
        if u1 in vals:
            v1 = vals[u1]
        else:
            v1 = getFn(u1, view)
        if u2 in vals:
            v2 = vals[u2]
        else:
            v2 = getFn(u2, view)

        if v2 is None:
            if v1 is None:
                # both attributes are None, so item and other compare as equal
                return 0
            else:
                return -1
        if v1 is None:
            return 1

        return cmp(v1, v2)

    def compare_init(self, index, u, vals):
        return getFn(u, self.itsView)
    return compare, compare_init
        
class EventComparator(schema.Item):
    cmpStartTime, cmpStartTime_init = makeCompareMethod(getFn=EventStamp._getEffectiveStartTime)
    cmpEndTime, cmpEndTime_init = makeCompareMethod(getFn=EventStamp._getEffectiveEndTime)
    cmpRecurEnd, cmpRecurEnd_init = makeCompareMethod(attr=EventStamp.recurrenceEnd)

def setEventDateTime(item, startTime, endTime, typeFlag):
    """
    Sets the startTime and the endTime of the item (CalendarEvent) depending on the typeFlag.
    typeFlag = 0 indicates no date/time, 1 indicates only date, 2 indicates only time
    and 3 indicates both date and time
    """
    event = EventStamp(item)
    if (typeFlag == 1) or (typeFlag == 0):
        # No time is present
        event.anyTime = True
    else:
        event.anyTime = False
        
    event.startTime = startTime
    event.endTime = endTime
    item.setTriageStatus('auto', pin=True)
    
class Occurrence(Note):
    """
    An C{Occurrence} is used to represent a single occurrence in a series
    of recurring events. It uses the chandlerdb C{inheritFrom} mechanism
    to store only the attributes that it has actually changed compared to
    the master events. If you do a getattr() (or access via ".") for other
    attributes, the repository will automatically redirect the call to
    the master event, which we've cleverly set as the occurrence's inheritFrom.
    
    This can potentially lead to some interesting problems, especially with
    assigning to the 'other' side of a biref. For example, if you do
    aCollection.add(occurrence), the repository will faithfully go and
    add aCollection to occurrence.collections. Unfortunately, if that is
    identical to the master, we end up with unexpected results. For now,
    the 'solution' to this is to avoid doing this without explicitly creating
    a fresh new attribute value on the Occurrence in question, but hopefully
    we'll come up with something more streamlined in the future.
    
    @cvar LOCAL_ATTRIBUTES: Usually, if you set a value on an Ocurrence, you
                            this will result in a THIS modification.
                            LOCAL_ATTRIBUTES specify attributes for which this
                            doesn't happen, i.e. attributes which are expected
                            to be different for each Occurrence.
    @type LOCAL_ATTRIBUTES: C{tuple} of C{str}
    """

    LOCAL_ATTRIBUTES = (
            'triageStatusChanged',
            EventStamp.isGenerated.name,
            EventStamp.recurrenceID.name,
            EventStamp.startTime.name,
            EventStamp.occurrenceFor.name,
            EventStamp.modificationFor.name,
    )

    NONE_ATTRIBUTES = (EventStamp.modifications.name, EventStamp.occurrences.name)
    
    def getMembershipItem(self):
        return self.inheritFrom
    
    def __setattr__(self, attr, value):
        cls = type(self)
        s = super(Occurrence, self)
        if self.isLive():
            if getattr(self, EventStamp.isGenerated.name, True):
                if (not attr in cls.LOCAL_ATTRIBUTES and
                    not hasattr(self, EventStamp.IGNORE_CHANGE_ATTR) and
                    self.itsKind.hasAttribute(attr)):
                    # changeThis does various domain model things, sets
                    # modificationFor, moves collections, and makes sure
                    # stamp_types isn't inherited
                    EventStamp(self).changeThis()
        s.__setattr__(attr, value)
    
    @apply
    def triageStatus():
        """
        Override item's triageStatus attribute, to allow us to calculate
        it for occurrences that don't have it set locally (eg, a triageStatus
        modification).
        """
        def fget(self):
            return self._triageStatus
        return property(fget)

    
    def onItemDelete(self, view, deferring):
        attrName = EventStamp.occurrenceFor.name
        if self.hasLocalAttributeValue(attrName):
            delattr(self, attrName)
        super(Occurrence, self).onItemDelete(view, deferring)

    DONT_PUSH = (EventStamp.recurrenceID.name, EventStamp.isGenerated.name,
        EventStamp.occurrenceFor.name, EventStamp.modificationFor.name,
        ContentItem.displayDate.name, ContentItem.displayDateSource.name,
        ContentItem.displayWho.name, ContentItem.displayWhoSource.name,
        ContentItem.appearsIn.name, ContentItem.collections.name,
        Triageable._sectionTriageStatusChanged.name,
        ContentItem.excludedBy.name, ContentItem.lastModifiedBy.name,
        ContentItem.lastModification.name, ContentItem.lastModified.name,
        ContentItem.createdOn.name, ContentItem.modifiedFlags.name,
        Stamp._stampCollections.name,
    )
    
    IGNORE_ATTRIBUTE_PREFIXES = ('osaf.framework',
                                 'osaf.sharing.shares.SharedItem')

    def hasModifiedAttribute(self, attr):
        cls = type(self)
        if (attr in cls.DONT_PUSH or
            [p for p in cls.IGNORE_ATTRIBUTE_PREFIXES if attr.startswith(p)]):
            return False
            
        event = EventStamp(self)
        masterItem = self.inheritFrom
    
        if attr == EventStamp.startTime.name:
            return event.effectiveStartTime != event.recurrenceID
        
        if attr == Remindable.reminders.name:
            return masterItem.getUserReminder() is not self.getUserReminder()
        
        if attr == Stamp.stamp_types.name:
            # Ignore SharedItem stamp
            my_stamps = set(Stamp(self).stamp_types)
            master_stamps = set(Stamp(masterItem).stamp_types)
            changes = my_stamps.symmetric_difference(master_stamps)
            real_stamp_change = False
            for stamp in changes:
                if stamp.__name__ != 'SharedItem':
                    return True
            return False

        return self.hasLocalAttributeValue(attr)
        
    
    def iterModifiedAttributes(self):
        """
        Yields all attribute changed on this occurrence, with certain 
        exclusions:
        
        1) Excluding all attributes in the DONT_PUSH class variable
        2) Excluding any attribute that starts with IGNORE_ATTRIBUTE_PREFIXES.
           This is a total hack which will break if we ever refactor, but it's a
           stand in for a way to define attributes as "not user facing"

        """
        event = EventStamp(self)
        if event.modificationFor is not None:
            for attr, value in self.iterAttributeValues():
                if self.hasModifiedAttribute(attr):
                    yield attr, value
                    
    def setUserReminderTime(self, reminderTime):
        EventStamp(self)._removeThisUserReminder()
        return super(Occurrence, self).setUserReminderTime(reminderTime)
        
    def _updateCommonAttribute(self, *args, **kw):
        event = EventStamp(self)
        if event.modificationFor is not None:
            with event.noRecurrenceChanges():
                super(Occurrence, self)._updateCommonAttribute(*args, **kw)
                    
    userReminderTime = schema.Calculated(
        Remindable.userReminderTime.type,
        basedOn=Remindable.userReminderTime.basedOn,
        fget=Remindable.userReminderTime.fget,
        fset=setUserReminderTime,
        doc="User-set absolute reminder time."
    )

                    
# Make sure iCalUID and rruleset are read-only attributes; i.e. they always
# get inherited from the master event.
def _makeReadonlyAccessor(attr):
    attrName = attr.name
    def fget(self):
        return getattr(self.inheritFrom, attr)
    setattr(Occurrence, attrName, property(fget))

_makeReadonlyAccessor(Note.icalUID)

    

class RelativeReminder(Reminder):
    relativeTo = EventStamp.effectiveStartTime.name

    delta = schema.One(
        schema.TimeDelta,
        defaultValue=zero_delta,
    )
    schema.addClouds(
        sharing = schema.Cloud(
            literal = [delta]
        ),
        copying = schema.Cloud(
            literal = [delta]
        )
    )
    
    # @@@ [grant] Seem to have lost relativeTo from the clouds. Do we
    # need it?
    def _getReminderTime(self, item, includePending=True):
        if includePending:
            for entry in self.pendingEntries:
                if entry.item is item:
                    return entry.when
                
        when = self.getItemBaseTime(item)
        
        if when is None or not self.hasLocalAttributeValue('delta'):
            return None
        else:
            return when + self.delta
            

    def updatePending(self, dt=None):
        if dt is None:
            dt = datetime.now(self.itsView.tzinfo.default)
            
        reminderItem = self.reminderItem
        reminderTime = self._getReminderTime(reminderItem)

        if reminderTime is None:
            self.nextPoll = self.farFuture
            return
        
        # Find the earliest "invisible" (snoozed into the future) reminder.
        # The idea is to make sure that self.nextPoll doesn't skip over some
        # snoozed reminder.
        firstSnoozedDate = None
        for pending in self.pendingEntries:
            if pending.when > dt:
                if firstSnoozedDate is None:
                    firstSnoozedDate = pending.when
                else:
                    firstSnoozedDate = min(firstSnoozedDate, pending.when)
            
        if self.nextPoll is None:
            # No value for nextPoll means we've just been initialized, and want
            # to find the first occurrence after dt, and set self.nextPoll to
            # be the reminder time for the event after that.
            
            start = dt - self.delta

        elif self.nextPoll != self.farFuture:
            start = self.nextPoll - self.delta
            
        else:
            return
        
        event = EventStamp(reminderItem)
        
        def _isModReminder(event):
            # Is self part of a modification's changed reminders?
            if (event.modificationFor is not None and
                event.itsItem.hasLocalAttributeValue('reminders') and
                self in event.itsItem.reminders):
                return True
            else:
                return False


        if not has_stamp(event, EventStamp):
            interestingEvents = []
        elif event.rruleset is None or _isModReminder(event):
            if event.effectiveStartTime >= start:
                interestingEvents = [event]
            else:
                interestingEvents = []
        else:
            master = event.getMaster()
            # skip mods, since they get their own copy of reminders for now
            # note that _generateRule returns items before start if their end
            # time is after start, but reminders don't want those, so explicitly
            # filter out such occurrences
            interestingEvents = iter(
                e for e in master._generateRule(start, None, True)
                       if self in e.itsItem.reminders and
                       e.effectiveStartTime >= start
            )
            
        for event in interestingEvents:
            reminderItem = event.itsItem
            reminderTime = self._getReminderTime(reminderItem)
            
            if dt < reminderTime:
                self.nextPoll = reminderTime
                break
                
            reminderItem.reminderFired(self, reminderTime)
        else:
            # We reached the end of the recurring series without
            # finding any new and "interesting" events. So, set
            # nextPoll to be the farFuture
            self.nextPoll = self.farFuture
            
        if firstSnoozedDate is not None and firstSnoozedDate < self.nextPoll:
            self.nextPoll = firstSnoozedDate
        else:
            self._checkExpired()
            
    def getItemBaseTime(self, item):
        return getattr(item, self.relativeTo, None)
        
    def getReminderTime(self, item):
        """
        When will we fire (or would we have fired) for item; taking
        snooze into account
        """
        return self._getReminderTime(item) or Reminder.farFuture
        
    def itemChanged(self, item):
        if self.nextPoll is None:
            return # We'll get updated later as necessary
            
        reminderTime = self._getReminderTime(item)
        if reminderTime is None:
            return # Er ....
            
        for entry in self.pendingEntries:
            if not entry.snoozed:
                entryReminder = self._getReminderTime(entry.item, False)
                # If the reminder has moved off into the future, but is before
                # our nextPoll, make sure that we remove it, and update
                # self.nextPoll accordingly.
                if entryReminder > entry.when:
                    self.pendingEntries.remove(entry)
                    if entryReminder <= self.nextPoll:
                        self.nextPoll = entryReminder
        # If the reminder is expired (i.e. nextPoll is far future), we
        # reset its nextPoll ... that way, it'll be marked as current
        # if necessary (Bug 9659).
        if self.nextPoll >= Reminder.farFuture:
            del self.nextPoll
        elif reminderTime < self.nextPoll:
            self.nextPoll = reminderTime
                        
    def reminderFired(self, reminder, when):
        """
        Override of C{ContentItem.reminderFired}: performs a THIS change
        of triageStatus to Now.
        """
        self.setTriageStatus(TriageEnum.now, when=when)
        
        # bypass ContentItem, because we want to do a THIS change here
        # always
        return super(ContentItem, self).reminderFired(reminder, when)

class TriageStatusReminder(RelativeReminder):
    """
    Singleton instance that updates triage status on events when their
    startTime passes.
    """
    
    QUERY_INTERVAL = timedelta(minutes=60)

    schema.initialValues(
        userCreated = lambda self: False,
        promptUser = lambda self: False
    )
    
    prevPoll = schema.One(
        schema.DateTimeTZ,
        doc="When was this reminder last polled?",
        defaultValue=None,
    )
    
    def installWatcher(self):
        """
        Install a watcher on the collection of all events. This is used
        to make sure that when events' (effective) startTimes change, we
        will change their triage status to NOW at the right time.
        """
        view = self.itsView
        
        # @@@ [grant]: Kludge for Bug 9944: watch all Notes rather than
        # EventStamp.getCollection(view).
        allNotes = schema.ns("osaf.pim", view).noteCollection
        view.watchCollectionQueue(self, allNotes, 'onCollectionNotification')
                                          
    def onCollectionNotification(self, op, collection, name, other, dirties):
        if op in ('changed', 'add'):
            item = self.itsView[other]
            if has_stamp(item, EventStamp):
                self.itemChanged(item)
        

    def itemChanged(self, item):
        if self.nextPoll is not None:
            event = EventStamp(item)
            possibleNewNextPoll = None
            if event.rruleset is None:
                # an ordinary event ... see if we need to reschedule
                possibleNewNextPoll = event.effectiveStartTime
            elif event.occurrenceFor is None:
                # a master
                occurrence = event.getNextOccurrence(after=self.prevPoll)
                if occurrence is not None:
                    possibleNewNextPoll = occurrence.effectiveStartTime
                
            if (possibleNewNextPoll is not None and
                possibleNewNextPoll >= self.prevPoll and
                possibleNewNextPoll < self.nextPoll):
                
                self.nextPoll = possibleNewNextPoll
                

    
    def updatePending(self, when=None):
        view = self.itsView

        if when is None:
            when = datetime.now(view.tzinfo.default)
            
        # getKeysInRange() isn't quite what we want, because
        # it cares about events overlapping range, whereas we
        # only want events whose effectiveStartTime lies within
        # range

        def yieldEvents(start, end):
            pimNs = schema.ns("osaf.pim", view)
            useTZ = pimNs.TimezonePrefs.showUI
            
            startIndex = 'effectiveStart'
            recurEndIndex ='recurrenceEnd'

            allEvents = EventStamp.getCollection(view)
            
            searchStart, searchEnd = adjustSearchTimes(start, end, useTZ)
            
            if not useTZ:
                start = start.replace(tzinfo=None)
                end = end.replace(tzinfo=None)
            
            def cmpStart(key):
                testVal = EventStamp._getEffectiveStartTime(key, view)
                if testVal is None:
                    return -1 # interpret None as negative infinity
                # note that we're NOT using >=, if we did, we'd include all day
                # events starting at the beginning of the next week
                return cmp(testVal, searchStart)

            firstKey = allEvents.findInIndex(startIndex, 'first', cmpStart)
            for key, item in allEvents.iterindexitems(startIndex, firstKey):
                event = EventStamp(item)
                if event.rruleset is None:
                    if useTZ or start <= event.effectiveStartTime.replace(tzinfo=None) <= end:
                        yield event

            masterEvents = pimNs.masterEvents
            for key in getKeysInRange(view, searchStart, 'effectiveStartTime',
                      startIndex, masterEvents, searchEnd, 'recurrenceEnd',
                      recurEndIndex, masterEvents, None, '__adhoc__'):

                master = EventStamp(view[key])
                
                for event in master._generateRule(after=searchStart,
                                                  before=searchEnd):
                    if useTZ or start <= event.effectiveStartTime.replace(tzinfo=None) <= end:
                        yield event

        if self.nextPoll is not None:
            start = self.nextPoll
        else:
            start = when
            
        # Now, find all the events in the hour (say) after when
        oneHourHence = when + self.QUERY_INTERVAL
        nextPoll = oneHourHence
        
        for event in yieldEvents(start, oneHourHence):
            effectiveStart = event.effectiveStartTime
            
            if effectiveStart <= when:
                if self.prevPoll is not None and effectiveStart >= self.prevPoll:
                    event.changeThis()
                    event.itsItem.setTriageStatus(TriageEnum.now,
                                                  when=effectiveStart)
                    event.getFirstFutureLater()
            elif effectiveStart < nextPoll:
                nextPoll = effectiveStart
                
        self.nextPoll = nextPoll
        self.prevPoll = when
            
def setTriageStatus(item, *args, **kwds):
    """
    Set triage status on this item, which might be a recurring event: if
    it is, we'll need to triage its modifications individually.
    """
    if has_stamp(item, EventStamp):
        event = EventStamp(item)
        if event.isRecurrenceMaster():
            # if the item that has changed is a master, DON'T set
            # triage status on the master, particularly
            # _sectionTriageStatus, as that will be inherited by
            # occurrences; instead, just pop all modifications to NOW
            for mod in event.modifications or []:
                mod.setTriageStatus(None, **kwds)
            return
        
    # Not an event, or not a master - do it normally.
    item.setTriageStatus(*args, **kwds)

