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

import application

from application import schema
from osaf.pim.contacts import Contact
from osaf.pim.items import ContentItem, cmpTimeAttribute, TriageEnum, isDead
from osaf.pim.stamping import Stamp, has_stamp
from osaf.pim.notes import Note
from osaf.pim.calendar import Recurrence
from osaf.pim.collections import FilteredCollection, IndexDefinition
from chandlerdb.util.c import isuuid

from TimeZone import formatTime
from osaf.pim.calendar.TimeZone import coerceTimeZone, TimeZoneInfo
from osaf.pim.calendar import DateTimeUtil
from PyICU import DateFormat, DateFormatSymbols, ICUtzinfo
from datetime import datetime, time, timedelta
import itertools
import StringIO
import logging
import operator
from chandlerdb.util.c import UUID

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
                t = IndexDefinition.findInheritedValues(view, uuid,
                                                        (fullName, None))
                return t[0]
            return getFn

    getStart = getGetFunction(startAttrName)
    getEnd = getGetFunction(endAttrName)
    
    # callbacks to use for searching the indexes
    def mStart(key, delta=None):
        # gets the last item starting before endVal, or before startVal - delta
        if delta is None:
            delta = zero_delta
        else:
            delta = delta + endVal - startVal
        testVal = getStart(key, view)
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
    tzprefs = schema.ns('osaf.pim', view).TimezonePrefs
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

    tzprefs = schema.ns('osaf.pim', view).TimezonePrefs
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
                    
def iterBusyInfo(view, start, end, filterColl=None):
    tzprefs = schema.ns('osaf.pim', view).TimezonePrefs
    if tzprefs.showUI:
        startIndex = 'effectiveStart'
        endIndex   = 'effectiveEnd'
        recurEndIndex   = 'recurrenceEnd'
    else:
        startIndex = 'effectiveStartNoTZ'
        endIndex   = 'effectiveEndNoTZ'
        recurEndIndex   = 'recurrenceEndNoTZ'


    allEvents  = EventStamp.getCollection(view)
    longEvents = schema.ns("osaf.pim", view).longEvents
    keys = getKeysInRange(view, start, 'effectiveStartTime', startIndex,
                          allEvents, end, 'effectiveEndTime', endIndex,
                          allEvents, filterColl, '__adhoc__', tzprefs.showUI,
                          longDelta = LONG_TIME, longCollection=longEvents)
    for key in keys:
        event = EventStamp(view[key])
        assert has_stamp(event, EventStamp)
        if event.rruleset is None:
            for fb in event.iterBusyInfo(start, end):
                yield fb

    masterEvents = schema.ns("osaf.pim", view).masterEvents
    keys = getKeysInRange(view, start, 'effectiveStartTime', startIndex,
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

    @group Semi-Private Methods: changeNoModification,
    cleanRule, _copyCollections, getEffectiveEndTime, getEffectiveStartTime,
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
        defaultValue=False
    )

    anyTime = schema.One(
        schema.Boolean,
        defaultValue=True
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
    
    icalendarProperties = schema.Mapping(
        schema.Text,
        defaultValue = None,
        doc="Original icalendar property name/value pairs not understood "
            "by Chandler.  Subcomponents (notably VALARMS) aren't stored."
    )

    icalendarParameters = schema.Mapping(
        schema.Text,
        defaultValue = None,
        doc="property name/parameter pairs for parameters not understood by "
            "Chandler.  The parameter value is the concatenation of "
            "paramater key/value pairs, separated by semi-colons, like the "
            "iCalendar serialization of those parameters"
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
        try:
            super(EventStamp, self).add()
        finally:
            if disabled: self.__enableRecurrenceChanges()
        
        if not hasattr(self, 'startTime'):
            # start at the nearest half hour, duration of an hour
            defaultTz = TimeZoneInfo.get(self.itsItem.itsView).default
            now = datetime.now(defaultTz)
            roundedTime = time(hour=now.hour, minute=(now.minute/30)*30,
                               tzinfo = defaultTz)
            self.startTime = datetime.combine(now, roundedTime)
        else:
            # Give the startTime-observer a chance to create a triageStatus
            # reminder
            self.onStartTimeChanged('set', EventStamp.startTime.name)
        if not hasattr(self, 'duration'):
            self.duration = timedelta(hours=1)

        # set the organizer to "me"
        if not hasattr(self, 'organizer'):
            self.organizer = schema.ns("osaf.pim", self.itsItem.itsView).currentContact.item

        if not hasattr(self.itsItem, 'icalUID'):
            self.itsItem.icalUID = unicode(self.itsItem.itsUUID)

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
        try:
            rruleset = self.rruleset
            
            if rruleset is not None:
                del self.rruleset
                del self.occurrenceFor
                if getattr(rruleset, 'exdates', None) is None:
                    rruleset.exdates=[]
                rruleset.exdates.append(self.recurrenceID)
        finally:
            if didDisable:
                self.__enableRecurrenceChanges()

        # Delete any relative user reminders, as well as any
        # triageStatus reminders
        from osaf.pim.reminders import Remindable
        remindable = Remindable(self)
        doomed = (r for r in remindable.reminders
                  if (r.userCreated and r.absoluteTime is None) or
                     not r.promptUser)
        moreDoomed = (r for r in remindable.expiredReminders
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
            allDay, anyTime, startTime = IndexDefinition.findInheritedValues(
                    view, uuidOrEvent,
                    (EventStamp.allDay.name, False),
                    (EventStamp.anyTime.name, False),
                    (EventStamp.startTime.name, None))
        else:
            allDay = getattr(uuidOrEvent, 'allDay', False)
            anyTime = getattr(uuidOrEvent, 'anyTime', False)
            startTime = getattr(uuidOrEvent, 'startTime', None)
        
        if startTime is None:
            return None
        
        if anyTime or allDay:
            startOfDay = time(0, tzinfo=ICUtzinfo.floating)
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
            allDay, anyTime, startTime, duration = IndexDefinition.findInheritedValues(
                    view, uuidOrEvent,
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
        from osaf.pim.reminders import Remindable
        remindable = Remindable(self)
        # Update the reminder we use to update triageStatus at startTime, 
        # if it's in the future. First, find any existing startTime reminder.
        existing = [r for r in getattr(remindable, 'reminders', [])
                      if not (r.userCreated or r.promptUser)]
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
                remindable.makeReminder(absoluteTime=newStartTime,
                                     userCreated=False, checkExpired=True,
                                     promptUser=False)
                    
        # If we had an existing startTime reminder, dismiss it.
        if existing:
            remindable.dismissReminder(existing)
            
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

    def __getDatetimePrepFunction(self):
        """
        This method returns a function that prepares datetimes for comparisons
        according to the user's global timezone preference settings. This
        is important because "naive timezone mode" can re-order events; e.g.
        in US timezones, an event that falls at 2AM GMT Sunday will be treated
        as occurring on Sunday in naive mode, but Saturday in non-naive.
        [cf Bug 5598].
        """

        if schema.ns('osaf.pim', self.itsItem.itsView).TimezonePrefs.showUI:
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
        if self.occurrenceFor is None:
            self.removeRecurrence()
        else:
            self.__disableRecurrenceChanges()


    def _restoreStamps(self, clonedEvent):
        disabledChanges = clonedEvent.__disableRecurrenceChanges()
        try:
            for stampClass in Stamp(self).stamp_types:
                stampClass(clonedEvent).add()
        finally:
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
            
        # It's possible this method has been called on a proxy; in that
        # case, we should make sure we're dealing with the "real"
        # item.
        item = first.itsItem.getMembershipItem()
        
        from osaf.pim.reminders import Remindable
        
        values = {
            EventStamp.isGenerated.name: True,
            EventStamp.recurrenceID.name: recurrenceID,
            EventStamp.startTime.name: recurrenceID,
            EventStamp.occurrenceFor.name: item,
            Remindable.reminders.name: list(Remindable(item).reminders),
            Remindable.expiredReminders.name:
                  list(Remindable(item).expiredReminders),
        }

        item = Occurrence.getKind(item.itsView).instantiateItem(
                None,
                item.itsParent,
                UUID(),
                withInitialValues=False)
        
        event = EventStamp(item)
        event.__disableRecurrenceChanges()
        for key, value in values.iteritems():
            setattr(item, key, value)
        event._fixReminders()
        event.__enableRecurrenceChanges()

        return event

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
                         if (not r.userCreated) or expired(r)]

        nowNotExpired = [r for r in remindable.expiredReminders
                           if not expired(r)]

        # ... and update the collections accordingly
        for reminder in nowExpired:
            remindable.reminders.remove(reminder)
            if reminder.userCreated:
                remindable.expiredReminders.add(reminder)
            elif len(reminder.reminderItems) == 0 and \
                 len(reminder.expiredReminderItems) == 0:
                reminder.delete()

        for reminder in nowNotExpired:
            remindable.reminders.add(reminder)
            remindable.expiredReminders.remove(reminder)

    def _generateRule(self, after=None, before=None, inclusive=False,
                      occurrenceCreator=_createOccurrence):
        """Yield all occurrences in this rule."""
        first = self.getMaster()
        prepDatetime = self.__getDatetimePrepFunction()
        
        #if after is None:
        #    event = first.getFirstOccurrence()
        #
        #    if event is None:
        #        return # No occurrences
        
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

        prepStart = prepDatetime(start)
        
        if (self.effectiveStartTime.tzinfo != prepDatetime(self.effectiveStartTime).tzinfo):
            if after is not None:
                after = after.replace(tzinfo=self.effectiveStartTime.tzinfo)
            start = start.replace(tzinfo=self.effectiveStartTime.tzinfo)

        def iterRecurrenceIDs():
            if after is not None:
                if (exact or (inclusive and (prepDatetime(after) <= prepStart))):
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
                       ((before is None) or
                        (prepDatetime(current) < prepDatetime(before)))):
                    #print '*** yielding current=%s' % (current,)
                    yield current
                    current = ruleset.after(current)

                if inclusive and (before is not None) and (before in ruleset):
                    yield before

        for recurrenceID in iterRecurrenceIDs():
            #print '*** recurrenceID=%s' % (recurrenceID,)

            knownOccurrence = self.getExistingOccurrence(recurrenceID)

            # yield all the matching modifications
            while mods and (prepDatetime(mods[0].effectiveStartTime)
                            < prepDatetime(recurrenceID)):
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
            
        if not inclusive and not master.duration:
            inclusive = True

        return list(master._generateRule(after, before, inclusive))
        
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
        try:
            return master._generateRule().next()
        except StopIteration:
            return None

        recurrenceID = master.effectiveStartTime
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

    def changeNoModification(self, attr, value):
        """Set _ignoreValueChanges flag, set the attribute, then unset flag."""
        flagStart = self.__disableRecurrenceChanges()
        try:
            setattr(self.itsItem, attr, value)
        finally:
            if flagStart:
                self.__enableRecurrenceChanges()

    def _grabOccurrences(self, occurrences, attrName, deleteIfNotMatching):
        """
        An internal method called when occurrences are being reassigned
        from one master to another, or when recurrence has changed and
        a master has to filter out the occurrences that no longer match.
        
        @param occurrences: The Occurrences whose master should become self
        @type occurrences: iterable or None
        
        @param deleteIfNotMatching: If set to True, objects in occurrences that
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
            disabled = False
            
            try:
                if occurrence.recurrenceID in rruleset:
                    if occurrence.occurrenceFor is not selfItem:
                        
                        disabled = occurrence.__disableRecurrenceChanges()
                        
                        occurrence.occurrenceFor = selfItem
                        
                        if occurrence.modificationFor is not None:
                            occurrence.modificationFor = selfItem
                            
                    if (attrName is not None and 
                        occurrence.itsItem.hasLocalAttributeValue(attrName)):
                        delattr(occurrence.itsItem, attrName)
                        
                elif deleteIfNotMatching:
                    occurrence.__disableRecurrenceChanges()
                    del occurrence.rruleset
                    del occurrence.occurrenceFor
                    del occurrence.modificationFor
                    for coll in list(getattr(occurrence.itsItem, 'appearsIn', ())):
                        if occurrence.itsItem in getattr(coll, 'inclusions', ()):
                            coll.inclusions.remove(occurrence.itsItem)
                    occurrence.itsItem.delete()
            finally:
                if disabled:
                    occurrence.__enableRecurrenceChanges()
        if not self.occurrences: # None or empty
            self.getFirstOccurrence()

        self.updateTriageStatus()

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
                        disabled = self.__disableRecurrenceChanges()
                        try:
                            setattr(self.itsItem, attr, value)
                        finally:
                            if not disabled: self.__enableRecurrenceChanges()
                        break

            return first.changeThisAndFuture(attr, value)
            
        
        # So, from now on, either self is a master, or it's an occurrence that
        # doesn't correspond to the master.
        
        startChanging = attr in (EventStamp.startTime.name,
                                 )
        disabledSelf = self.__disableRecurrenceChanges()
        try:
            if attr == EventStamp.startTime.name:
                startTimeDelta = (value - self.startTime)
                if first.allDay or first.anyTime:
                    recurrenceIDDelta = value.date() - self.startTime.date()
                else:
                    recurrenceIDDelta = startTimeDelta
                if startTimeDelta:
                    self.rruleset.moveDatesAfter(recurrenceID, startTimeDelta)
                    
                    for occurrence in itertools.imap(EventStamp,
                                                     first.occurrences or []):
                        if occurrence.recurrenceID >= recurrenceID:
                            occurrence.startTime += startTimeDelta
                            occurrence.recurrenceID += recurrenceIDDelta
                
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
                        recurrenceTime = time(0, tzinfo=first.startTime.tzinfo)
                    else:
                        recurrenceTime = first.startTime.timetz()
    
                    for occurrence in itertools.imap(EventStamp,
                                                     first.occurrences or []):
                        occurrence.recurrenceID = datetime.combine(
                            occurrence.startTime.date(), recurrenceTime)
    
                    
            setattr(self.itsItem, attr, value)
            
            if isFirst:
                # Make sure master's recurrenceID matches its effectiveStartTime
                self.recurrenceID = self.effectiveStartTime
                if attr == EventStamp.rruleset.name: # rule change, thus a destructive change
                    self._fixMasterReminders()
            else:
                # If we're not first, we're an occurrence (and not the master's
                # occurrence). So, we generate a new master, truncate the old
                # master before our recurrenceID, and move the occurrences over
                # accordingly.
                newMaster = first._cloneEvent()
                disabled = newMaster.__disableRecurrenceChanges()
                
                try:
                    newMasterItem = newMaster.itsItem
                    if attr != EventStamp.rruleset.name:
                        newMaster.rruleset = first.rruleset.copy(cloudAlias='copying')
                        newMaster.rruleset.removeDates(datetime.__lt__, recurrenceID)
                
                    # There are two events in play, self (which has been
                    # changed), and newMaster, a non-displayed item used to
                    # define generated events.  Make sure the current change
                    # is applied to both items. Note that Occurrences get
                    # their rruleset from their masters, so there's no
                    # need to reassign
                    setattr(newMasterItem, attr, value)
                    newMaster.startTime = newMaster.recurrenceID = self.recurrenceID
                    if newMaster.occurrenceFor:
                        del newMaster.occurrenceFor #self overrides newMaster
                    newMaster.itsItem.icalUID = str(newMasterItem.itsUUID)
                    newMaster._makeGeneralChange()
                    
                    self._copyCollections(master, newMaster)
                    
                    if startChanging:
                        attrToDrop = None
                    else:
                        attrToDrop = attr
                    newMaster._grabOccurrences(master.occurrences, attrToDrop,
                                               False)

                    # We want to do this after _grabOccurrences, so
                    # that master doesn't go remove the occurrences itself.
                    master.moveRuleEndBefore(recurrenceID)

                finally:
                    if disabled: newMaster.__enableRecurrenceChanges()
            
            master._grabOccurrences(master.occurrences, None, True)
            
        finally:
            if disabledSelf: self.__enableRecurrenceChanges()

    def moveCollections(self, fromEvent, toEvent):
        """Move all collection references from one event to another."""
        fromItem = fromEvent.itsItem.getMembershipItem()
        toItem = toEvent.itsItem.getMembershipItem()

        for collection in getattr(fromItem, 'collections', []):
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
            
        fromCollections = getattr(fromItem, 'collections', [])
        
        # We really, really want modifications to get their
        # own copy of collections, so that the biref doesn't
        # get all messed up
        if not toItem.hasLocalAttributeValue('collections'):
            toItem.collections = []
            
        if removeOld:
            for collection in getattr(toItem, 'collections', []):
                if collection not in fromCollections:
                    collection.remove(toItem)
        
        for collection in fromCollections:
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
                disabled = self.__disableRecurrenceChanges()
                if not self.itsItem.hasLocalAttributeValue(Stamp.stamp_types.name):
                    Stamp(self).stamp_types = set()
                for stamp in list(Stamp(first).stamp_types):
                    if not stamp in iter(Stamp(self).stamp_types):
                        stamp(self).add()
                for stamp in list(Stamp(self).stamp_types):
                    if not stamp in Stamp(first).stamp_types:
                        stamp(self).remove()
                self._copyCollections(first, self)
                if disabled:
                    self.__enableRecurrenceChanges()
        if attr is not None:
            setattr(self.itsItem, attr, value)

    def updateTriageStatus(self):
        """
        If appropriate, make sure there's at least one LATER modification in the
        future and at least one DONE modification in the past.
        
        Also collapse DONE modifications whose only change is to triageStatus so
        only the most recent triage-only modification is kept.
        
        When auto-triage is distinguished from user-triage, the algorithm may
        get more complicated.
        
        """
        defaultTz = TimeZoneInfo.get(self.itsItem.itsView).default
        now = datetime.now(defaultTz)
        master = self.getMaster()
        firstOccurrence = master.getRecurrenceID(master.recurrenceID)
        if firstOccurrence is None:
            firstOccurrence = master.getFirstOccurrence()
        if firstOccurrence is None:
            # an empty rule, nothing to do
            return
        if firstOccurrence.modificationFor is None:
            # touch the first occurrence, it should always be a modification
            firstOccurrence.changeThis()

        # run backwards through recurrenceIDs till a DONE occurrence is found
        lastPastDone = None
        rruleset = master.rruleset.createDateUtilFromRule(master.effectiveStartTime)
        earlierRecurrenceID = rruleset.before(now)
        while earlierRecurrenceID is not None:
            pastOccurrence = master.getRecurrenceID(earlierRecurrenceID)
            if pastOccurrence is None:
                print earlierRecurrenceID, master.recurrenceID
            if pastOccurrence.modificationFor is None:
                pastOccurrence.changeThis('triageStatus', TriageEnum.done)
                # changeThis won't set up modificationFor if the triageStatus
                # is already DONE, so explicitly set modificationFor
                pastOccurrence.modificationFor = master.itsItem
                lastPastDone = pastOccurrence.recurrenceID
                break
            elif pastOccurrence.itsItem.triageStatus == TriageEnum.done:
                lastPastDone = pastOccurrence.recurrenceID
                break
            else:
                earlierRecurrenceID = rruleset.before(earlierRecurrenceID)

        # run through old modifications and unmodify them if only triageStatus
        # is changed on them
        if lastPastDone is not None and master.modifications is not None:
            for mod in itertools.imap(EventStamp, master.modifications):
                if (mod.startTime < lastPastDone and 
                    mod.itsItem.triageStatus == TriageEnum.done and
                    mod != firstOccurrence):

                    if mod.isTriageOnlyModification():
                        mod.unmodify()

        # run through future occurrences to find a LATER
        for occurrence in master._generateRule(after=now):
            if occurrence.modificationFor is not None:
                if occurrence.itsItem.triageStatus == TriageEnum.later:
                    break
            else:
                occurrence.changeThis('triageStatus', TriageEnum.later)
                break

    def isTriageOnlyModification(self):
        if self.modificationFor is None:
            return False
        for attr, value in self.itsItem.iterModifiedAttributes():
            if attr not in (ContentItem.triageStatus.name, 
                            ContentItem.triageStatusChanged.name):
                return False
        
        return True
                        
    def unmodify(self):
        """Turn a modification into a normal occurrence."""
        # turning the modification into an occurrence doesn't
        # remove the item from the master's collections.  For
        # now just empty collections.  Are there circumstances
        # where plain occurrences *should* be in a collection?    
        self.itsItem.collections = []
        # @@@ [jeffrey] need to remove triageStatus from mod's
        # attributes once there's a mechanism for it to inherit
        # triageStatus based on time        
        del self.modificationFor


    def _fixMasterReminders(self):
        """
        When we turn recurrence on or off, deal with existing reminders.
        """
        from osaf.pim.reminders import Remindable
        remindable = Remindable(self)
        
        if self.rruleset is not None:
            if not self.isRecurrenceMaster():
                return

            # We're adding recurrence, and this is a master.
            # Tweak the reminders.
            disabled = self.__disableRecurrenceChanges()
            try:
                # Convert any absolute user reminder to relative.
                absTime = remindable.userReminderTime
                if absTime is not None:
                    remindable.userReminderInterval = \
                        (absTime - self.effectiveStartTime)
                else:
                    # No absolute reminder. If we have a relative one, move it
                    # to 'expired' (so the master won't show up in the 
                    # itemsWithReminders list).                    
                    reminder = remindable.getUserReminder(expiredToo=False)
                    if reminder is not None:
                        # We've got a relative reminder that isn't expired - move
                        # it to 'expired' now that we're a master.
                        remindable.reminders.remove(reminder)
                        remindable.expiredReminders.add(reminder)
                    
                # Any remaining reminders in the pending list are triageStatus
                # or snooze reminders; discard them -- it'd be messy to have 
                # them on the master.
                if remindable.reminders:
                    for r in list(remindable.reminders):
                        r.delete()
                    # delete() is sometimes deferred until commit
                    # therefore remindable.reminders won't clear until then
                    # unless it's explicitely done here.
                    remindable.reminders.clear()
                assert len(remindable.reminders) == 0
            finally:
                if disabled: self.__enableRecurrenceChanges()
        else:
            # When we remove recurrence, we might need to move the user
            # reminder from 'expired' to 'reminders' if it's still in the future.
            (refList, reminder) = remindable.getUserReminder(refListToo=True)
            now = datetime.now(tz=ICUtzinfo.default)
            if reminder is not None and refList is remindable.expiredReminders \
               and reminder.getNextReminderTimeFor(remindable) >= now:
                remindable.expiredReminders.remove(reminder)
                remindable.reminders.add(reminder)
            
    @schema.observer(
        ContentItem.displayName, ContentItem.body, ContentItem.lastModified,
        startTime, duration, location, allDay, rruleset, Stamp.stamp_types,
        ContentItem.triageStatus
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
            logger.debug("just set rruleset")
            self._fixMasterReminders()
            if self == self.getFirstInRule():
                self.recurrenceID = self.effectiveStartTime
                self.cleanRule()
        elif name == ContentItem.triageStatus.name:
            # just in case this isn't already a modification, make it one
            self.changeThis()
            # go and create a later modification if this change got rid of our
            # current token later
            self.updateTriageStatus()
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

    @schema.observer(ContentItem.collections)
    def onCollectionChange(self, op, name):
        if self.itsItem.hasLocalAttributeValue(EventStamp.occurrenceFor.name):
            # code that removes items from collections should generally try
            # getMaster first.  Ignoring collection membership changes for
            # non-masters prevents painful perpetual loops
            return
        for event in self.modifications or []:
            # @@@FIXME really slow hack, we could use op to be much more
            # precise about this.
            self._copyCollections(self, event, removeOld=True)
        

    def cleanRule(self):
        """
        Delete generated occurrences in the current rule and any out of date
        modifications.
        
        """
        
        rrulesetItem = getattr(self, 'rruleset', None)
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
            self.itsItem.delete(recursive=True)

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

    def removeRecurrence(self, deleteOccurrences=True):
        """
        Remove modifications, rruleset, and all occurrences except master.

        The resulting event will occur exactly once.
        
        @type deleteOccurrences: C{bool}
        @param deleteOccurrences: If C{True} (the default), the C{occurrences}
            attribute will be deleted, while otherwise it will only be cleared.
            The latter is needed while merging changes during sharing.
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
                master.__disableRecurrenceChanges()
                for attr, value in event.itsItem.iterModifiedAttributes():
                    setattr(master.itsItem, attr, value)
                master.__enableRecurrenceChanges()
            
            event.__disableRecurrenceChanges()
            event.itsItem.delete(recursive=True)
            
        if rruleset is not None:
            rruleset._ignoreValueChanges = True
            rruleset.delete()

        if hasattr(master, 'rruleset'):
            del master.rruleset

        if deleteOccurrences and master.occurrences is not None:
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

    def isRecurring(self):
        """ Is this Event a recurring event? """
        return self.rruleset is not None
    
    def isRecurrenceMaster(self):
        """ Is this Event a master of a recurrence set? """
        return self.rruleset is not None and self.getMaster() == self
    
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
    
def parseText(text):
    """
    Parses the given text and returns the start date/time and the end date/time and
    a countFlag  and a typeFlag.
    
    countFlag indicates the number of date/times present in the text. It is an enum.
    0 indicates no date/time, 1 indicates only one date/time, 2 indicates more than one date/time.
    
    typeFlag indicates the type of date/time information present. It is an ennum too.
    0 indicates no date/time, 1 indicates only date, 2 indicates only time
    and 3 indicates both date and time
    """
    
    import parsedatetime.parsedatetime as parsedatetime
    import parsedatetime.parsedatetime_consts as ptc
    from i18n import getLocaleSet
    import time
    import string
    
    cal = parsedatetime.Calendar(ptc.Constants(str(getLocaleSet()[0])))
    countFlag = 0   #counts the number of date/times in the text
    for line in (text.split('.')):
        line = string.strip(line)
        if  countFlag > 1:
            #More than one date time exists.
            break
        else:
            if line is not '' and line is not None:
                (dt1, dt2, typeFlag) = cal.evalRanges(line)
                if typeFlag != 0:
                    countFlag += 1
                    # Date/time range exists
                    (yr1, mth1, dy1, hr1, mn1, sec1, wd1, yd1, isdst1) = dt1
                    (yr2, mth2, dy2, hr2, mn2, sec2, wd2, yd2, isdst2) = dt2
                    
                    if typeFlag == 1:
                        #only date exists
                        startTime = datetime(yr1, mth1, dy1, tzinfo=ICUtzinfo.default)
                        endTime = datetime(yr2, mth2, dy2, tzinfo=ICUtzinfo.default)
                    else:
                        #time exists
                        startTime = datetime(yr1, mth1, dy1, hr1, mn1, tzinfo=ICUtzinfo.default)
                        endTime = datetime(yr2, mth2, dy2, hr2, mn2, tzinfo=ICUtzinfo.default)
                else:
                    # Check whether there is a single date/time
                    (dt, typeFlag) = cal.parse(line)
                    if typeFlag != 0:
                        # Date/time exists
                        countFlag += 1
                        (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = dt
                        
                        if typeFlag == 1:
                            #only date exists
                            startTime = endTime = datetime(yr, mth, dy, tzinfo=ICUtzinfo.default)
                        else:
                            #time exists
                            startTime = endTime = datetime(yr, mth, dy, hr, mn, tzinfo=ICUtzinfo.default)
                            
    #If no date/time exists or more than one date/time exists,
    #set the date as today's date and time as Anytime                                   
    if (countFlag == 2) or (countFlag == 0):
        (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = time.localtime()
        startTime = endTime = datetime(yr, mth, dy, tzinfo=ICUtzinfo.default)
        typeFlag = 0
        
    return startTime, endTime, countFlag, typeFlag

def makeCompareMethod(attr=None, getFn=None, useTZ=True):
    if getFn is None:
        attrName = attr.name
        def getFn(uuid, view):
            t = IndexDefinition.findInheritedValues(view, uuid,
                                                    (attrName, None))
            return t[0]
    def compare(self, u1, u2):
        view = self.itsView
        v1 = getFn(u1, view)
        v2 = getFn(u2, view)
        return cmpTimeAttribute(v1, v2, useTZ=useTZ)
    return compare
        
class EventComparator(schema.Item):
    cmpStartTime = makeCompareMethod(getFn=EventStamp._getEffectiveStartTime)
    cmpEndTime = makeCompareMethod(getFn=EventStamp._getEffectiveEndTime)
    cmpRecurEnd = makeCompareMethod(attr=EventStamp.recurrenceEnd)
    # comparisons which strip timezones
    cmpStartTimeNoTZ = makeCompareMethod(getFn=EventStamp._getEffectiveStartTime, useTZ=False)
    cmpEndTimeNoTZ = makeCompareMethod(getFn=EventStamp._getEffectiveEndTime, useTZ=False)
    cmpRecurEndNoTZ = makeCompareMethod(attr=EventStamp.recurrenceEnd, useTZ=False)

def setEventDateTime(item, startTime, endTime, typeFlag):
    """
    Sets the startTime and the endTime of the item (CalendarEvent) depending on the typeFlag.
    typeFlag = 0 indicates no date/time, 1 indicates only date, 2 indicates only time
    and 3 indicates both date and time
    """
    from osaf import pim
    
    if (typeFlag == 1) or (typeFlag == 0):
        # No time is present
        pim.EventStamp(item).anyTime = True
    else:
        pim.EventStamp(item).anyTime = False
        
    pim.EventStamp(item).startTime = startTime
    pim.EventStamp(item).endTime = endTime
    
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
            'osaf.pim.reminders.Remindable.reminders',
            'osaf.pim.reminders.Remindable.expiredReminders',
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
        
        if (not attr in cls.LOCAL_ATTRIBUTES and
            not isDead(self) and
            cls._kind.__get__(self) and
            not hasattr(self, EventStamp.IGNORE_CHANGE_ATTR) and
            getattr(self, EventStamp.modificationFor.name) is None and
            cls.itsKind.__get__(self).hasAttribute(attr)):
            
            s.__setattr__(EventStamp.modificationFor.name,
                          self.inheritFrom)
            s.__setattr__(EventStamp.isGenerated.name, False)
            
           
        s.__setattr__(attr, value)
        
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
        ContentItem._unpurgedTriageStatusChanged.name,
        ContentItem.excludedBy.name,
    )
    
    IGNORE_ATTRIBUTE_PREFIX = 'osaf.framework'
    
    def iterModifiedAttributes(self):
        """
        Yields all attribute changed on this occurrence, with certain 
        exclusions:
        
        1) Excluding all attributes in the DONT_PUSH class variable
        2) Excluding startTime and reminders/expiredReminders if they match
           recurrenceID
        3) Excluding any attribute that starts with IGNORE_ATTRIBUTE_PREFIX.
           This is a total hack which will break if we ever refactor, but it's a
           stand in for a way to define attributes as "not user facing"

        """
        event = EventStamp(self)
        master = event.modificationFor
        
        if master is not None:
            cls = type(self)
            masterEvent = EventStamp(master)
            from osaf.pim.reminders import Remindable
            masterReminder = Remindable(master).getUserReminder()
            eventReminder  = Remindable(self).getUserReminder()
                        
            for attr, value in self.iterAttributeValues():
                if (attr not in cls.DONT_PUSH and
                    not attr.startswith(cls.IGNORE_ATTRIBUTE_PREFIX)):
                    if attr == EventStamp.startTime.name:
                        if event.startTime == event.recurrenceID:
                            # startTime matches recurrenceID, ignore it
                            continue
                    elif attr in (Remindable.reminders.name, 
                                  Remindable.expiredReminders.name):
                        if masterReminder == eventReminder:
                            continue
                    elif attr == Stamp.stamp_types.name:
                        if set(Stamp(self).stamp_types) == set(Stamp(masterEvent).stamp_types):
                            continue

                    yield attr, value

# Make sure iCalUID and rruleset are read-only attributes; i.e. they always
# get inherited from the master event.
def _makeReadonlyAccessor(attr):
    attrName = attr.name
    def fget(self):
        return getattr(self.inheritFrom, attr)
    setattr(Occurrence, attrName, fget)

_makeReadonlyAccessor(Note.icalUID)
_makeReadonlyAccessor(EventStamp.rruleset)

