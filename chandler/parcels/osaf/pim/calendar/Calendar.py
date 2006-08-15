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
   @group Main classes: CalendarEventMixin, CalendarEvent, Location,
   TimeTransparencyEnum
   @group Unused classes: Calendar, ModificationEnum, RecurrencePattern
"""

__parcel__ = "osaf.pim.calendar"

import application

from application import schema
from osaf.pim.contacts import Contact
from osaf.pim.calculated import Calculated
from osaf.pim.items import ContentItem
from osaf.pim.notes import Note
from osaf.pim.calendar import Recurrence
from application.dialogs import RecurrenceDialog
import wx

from TimeZone import formatTime
from osaf.pim.calendar.TimeZone import coerceTimeZone, TimeZoneInfo
from osaf.pim.calendar import DateTimeUtil
from osaf.pim.reminders import Remindable, Reminder
from PyICU import DateFormat, DateFormatSymbols, ICUtzinfo
from datetime import datetime, time, timedelta
import itertools
import StringIO
import logging
from util import indexes

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

def _sortEvents(eventlist, reverse=False):
    """Helper function for working with events."""
    def cmpEventStarts(event1, event2):
        return cmp(event1.effectiveStartTime, event2.effectiveStartTime)
    eventlist = list(eventlist)
    eventlist.sort(cmp=cmpEventStarts)
    if reverse: eventlist.reverse()
    return eventlist

def findUID(view, uid):
    """
    Return the master event whose icalUID matched uid, or None.
    """
    events = schema.ns('osaf.pim', view).events
    event = indexes.valueLookup(events, 'icalUID', 'icalUID', uid)
    if event is None:
        return None
    else:
        return event.getMaster()

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
        testVal = getattr(view[key], startAttrName)
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
        testVal = getattr(view[key], endAttrName)
        if testVal is None:
            return 0 # interpret None as positive infinity, thus, a match
        if useTZ:
            if startVal + delta < testVal:
                return 0
        else:
            if startVal.replace(tzinfo=None) + delta < testVal.replace(tzinfo=None):
                return 0
        return 1

    lastStartKey = startColl.findInIndex(startIndex, 'last', mStart)
    if lastStartKey is None:
        return #there were no keys starting after end
    if longDelta is not None:
        firstStartKey = startColl.findInIndex(startIndex, 'last',
                                    lambda key: mStart(key, longDelta))
    else:
        firstStartKey = None

    firstEndKey = endColl.findInIndex(endIndex, 'first', mEnd)
    if firstEndKey is None:
        return #there were no keys ending before start
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

def isDayItem(item):
    anyTime = False
    try:
        anyTime = item.anyTime
    except AttributeError:
        pass

    allDay = False
    try:
        allDay = item.allDay
    except AttributeError:
        pass

    return allDay or anyTime

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

    allEvents  = schema.ns("osaf.pim", view).events
    longEvents = schema.ns("osaf.pim", view).longEvents
    keys = getKeysInRange(view, start, 'effectiveStartTime', startIndex,
                          allEvents, end,'effectiveEndTime', endIndex,
                          allEvents, filterColl, '__adhoc__', tzprefs.showUI,
                          longDelta = LONG_TIME, longCollection=longEvents)
    for key in keys:
        if (view[key].rruleset is None and
            ((dayItems and timedItems) or isDayItem(view[key]) == dayItems)):
            yield view[key]

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
        masterEvent = view[key]
        for event in masterEvent.getOccurrencesBetween(start, end):
            # One or both of dayItems and timedItems must be
            # True. If both, then there's no need to test the
            # item's day-ness.  If only one is True, then
            # dayItems' value must match the return of
            # isDayItem.
            if ((event.occurrenceFor is not None) and
                ((dayItems and timedItems) or
                 isDayItem(event) == dayItems)):
                    yield event



class CalendarEventMixin(ContentItem):
    """
    This is the set of CalendarEvent-specific attributes. This Kind is 'mixed
    in' to others kinds to create Kinds that can be instantiated.

    Calendar Event Mixin is the bag of Event-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".

    @group Main Public Methods: changeThis, changeThisAndFuture, setRuleFromDateUtil,
    getLastUntil, getRecurrenceEnd, getMaster, createDateUtilFromRule,
    getNextOccurrence, getOccurrencesBetween, getExistingOccurrence,
    getRecurrenceID, deleteThis, deleteThisAndFuture, deleteAll,
    removeRecurrence, isCustomRule, getCustomDescription, isAttributeModifiable

    @group Comparison Methods for Indexing: cmpTimeAttribute, cmpStartTime,
    cmpEndTime, cmpRecurEnd, cmpReminderTime

    @group Semi-Private Methods: addToCollection, changeNoModification,
    cleanRule, copyCollections, getEffectiveEndTime, getEffectiveStartTime,
    getEndTime, getFirstInRule, InitOutgoingAttributes, isBetween, isProxy,
    moveCollections, moveRuleEndBefore, onValueChanged, removeFutureOccurrences,
    setEndTime, StampKind, updateRecurrenceEnd, __init__, removeFromCollection

    """

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
        "Location",
        doc="We might want to think about having Location be just a 'String', "
            "rather than a reference to a 'Location' item.",
        indexed=True
     )

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

    icalUIDMap = schema.One(
        otherName = "items",
        doc = "For performance we maintain a ref collection mapping iCalendar "
              "UIDs to events, making lookup by UID quick."
    )

    modifies = schema.One(
        ModificationEnum,
        defaultValue=None,
        doc = "Describes whether a modification applies to future events, or "
              "just one event"
    )

    modifications = schema.Sequence(
        "CalendarEventMixin",
        doc = "A list of occurrences that have been modified",
        defaultValue=None,
        inverse="modificationFor"
    )

    modificationFor = schema.One(
        "CalendarEventMixin",
        defaultValue=None,
        inverse="modifications"
    )

    modificationRecurrenceID = schema.One(
        schema.DateTimeTZ,
        defaultValue=None,
        doc="If a modification's startTime is changed, none of its generated"
            "occurrences will backup startTime, so modifications must persist"
            "a backup for startTime"
    )

    occurrences = schema.Sequence(
        "CalendarEventMixin",
        defaultValue=None,
        inverse="occurrenceFor"
    )

    occurrenceFor = schema.One(
        "CalendarEventMixin",
        defaultValue=None,
        inverse="occurrences"
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
            "onValueChanged.  Note that this attribute is only meaningful "
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

    # Redirections

    whoFrom = schema.One(redirectTo="organizer")
    about = schema.One(redirectTo="displayName")
    date = schema.One(redirectTo="startTime")

    def __init__(self, *args, **kw):
        super(CalendarEventMixin, self).__init__(*args, **kw)
        self.occurrenceFor = self
        if not kw.has_key('icalUID'):
            self.icalUID = unicode(self.itsUUID)

    def InitOutgoingAttributes(self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(CalendarEventMixin, self).InitOutgoingAttributes()
        except AttributeError:
            pass

        CalendarEventMixin._initMixin(self) # call our init, not the method of a subclass

        # New item initialization
        self.displayName = _(u"New Event")

    def _initMixin(self):
        """
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        if not self.hasLocalAttributeValue('startTime'):
            # start at the nearest half hour, duration of an hour
            defaultTz = TimeZoneInfo.get(self.itsView).default
            now = datetime.now(defaultTz)
            roundedTime = time(hour=now.hour, minute=(now.minute/30)*30,
                               tzinfo = defaultTz)
            self.startTime = datetime.combine(now, roundedTime)
        if not self.hasLocalAttributeValue('duration'):
            self.duration = timedelta(hours=1)

        # set the organizer to "me"
        self.organizer = schema.ns("osaf.pim", self.itsView).currentContact.item

        # give a starting display name
        try:
            self.displayName = self.getAnyAbout ()
        except AttributeError:
            pass

        self.occurrenceFor = self

        if not hasattr(self, 'icalUID'):
            self.icalUID = unicode(self.itsUUID)

        # TBD - set participants to any existing "who"
        # participants are currently not implemented.

    def StampKind (self, operation, mixinKind):
        """
        Override StampKind to deal with unstamping CalendarEventMixin on
        recurring events.

        When unstamping CalendarEventMixin, first add the item's recurrenceID
        to the exclusion list, so the item doesn't reappear after unstamping.

        """
        if operation == 'remove' and self.rruleset is not None and \
           not self._findStampedKind(operation, mixinKind).isKindOf(CalendarEventMixin.getKind(self.itsView)):
            self._ignoreValueChanges = True
            rruleset = self.rruleset
            self.occurrenceFor = None
            self.rruleset = None
            if getattr(rruleset, 'exdates', None) is None:
                rruleset.exdates=[]
            rruleset.exdates.append(self.recurrenceID)
            del self._ignoreValueChanges

        super(CalendarEventMixin, self).StampKind(operation, mixinKind)

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

    timeDescription = Calculated(
        schema.Text,
        basedOn=('startTime', 'duration', 'recurrence'),
        fget=getTimeDescription,
        doc="A human-readable description of the time-related attributes.",
    )

    def getEndTime(self):
        if (self.hasLocalAttributeValue("startTime") and
            self.hasLocalAttributeValue("duration")):
            return self.startTime + self.duration
        else:
            return None

    def setEndTime(self, dateTime):
        if self.hasLocalAttributeValue("startTime"):
            duration = dateTime - self.startTime
            if duration < timedelta(0):
                raise ValueError, "End time must not be earlier than start time"
            self.duration = duration

    endTime = Calculated(
        schema.DateTimeTZ,
        basedOn=('startTime', 'duration'),
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
        # If startTime's time is invalid, ignore it.
        if not self.hasLocalAttributeValue('startTime'):
            return None
        elif self.anyTime or self.allDay:
            startOfDay = time(0, tzinfo=ICUtzinfo.floating)
            return datetime.combine(self.startTime, startOfDay)
        else:
            return self.startTime

    effectiveStartTime = Calculated(
        schema.DateTimeTZ,
        basedOn=('startTime', 'allDay', 'anyTime'),
        fget=getEffectiveStartTime,
        doc="Start time, without time if allDay/anyTime")

    def getEffectiveEndTime(self):
        """
        Get the effective end time of this event: ignore the time
        component of the endTime attribute if this is an allDay
        or anyTime event.
        """
        endTime = self.endTime
        if endTime is None:
            return self.effectiveStartTime
        elif self.anyTime or self.allDay:
            # all day events include their endtime, so they end at midnight
            # one day later than their normal end date.
            return datetime.combine(endTime + timedelta(1),
                                    time(0, tzinfo=endTime.tzinfo))
        else:
            return endTime

    effectiveEndTime = Calculated(
        schema.DateTimeTZ,
        basedOn=('startTime', 'allDay', 'anyTime', 'duration'),
        fget=getEffectiveEndTime,
        doc="End time, without time if allDay/anyTime")


    # begin recurrence related methods

    def getFirstInRule(self):
        """Return the rule's master, equivalent to getMaster, different only
        when THISANDFUTURE modifications stay connected to masters.

        @rtype: C{CalendarEventMixin}

        """
        first = self.modificationFor
        if first is not None:
            return first

        first = self.occurrenceFor
        if first is self or first is None:
            # could be None if a master's first date has a "this" modification
            return self

        return first

    def getLastUntil(self):
        """Find the last modification's rruleset, return it's until value.

        @rtype: C{datetime} or C{None}

        """
        # for no-THISANDFUTURE, this is just return until
        if self.rruleset is None:
            return None
        last = None
        for rule in self.rruleset.rrules:
            until = getattr(rule, 'until', None)
            if until is not None:
                if last is None or last < until:
                    last = until
        return last

    def getRecurrenceEnd(self):
        """Return (last until or RDATE) + duration, or None.

        @rtype: C{datetime} or C{None}

        """
        if self.rruleset is None:
            return self.endTime
        last = self.getLastUntil()
        rdates = getattr(self.rruleset, 'rdates', [])
        for dt in rdates:
            if last < dt:
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

        @rtype: C{CalendarEventMixin}

        """
        if self.modificationFor is not None:
            return self.modificationFor.getMaster()
        elif self.occurrenceFor in (self, None):
            return self
        else:
            return self.occurrenceFor.getMaster()

    def __getDatetimePrepFunction(self):
        """
        This method returns a function that prepares datetimes for comparisons
        according to the user's global timezone preference settings. This
        is important because "naive timezone mode" can re-order events; e.g.
        in US timezones, an event that falls at 2AM GMT Sunday will be treated
        as occurring on Sunday in naive mode, but Saturday in non-naive.
        [cf Bug 5598].
        """

        if schema.ns('osaf.app', self.itsView).TimezonePrefs.showUI:
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

        if inclusive:
            def compare(dt1, dt2):
                return prepDatetime(dt1) <= prepDatetime(dt2)
        else:
            def compare(dt1, dt2):
                return prepDatetime(dt1) < prepDatetime(dt2)

        return ((before is None or compare(self.startTime, before)) and
               (after is None or (prepDatetime(self.endTime) >= prepDatetime(after))))

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
            ruleItem=Recurrence.RecurrenceRuleSet(None, itsView=self.itsView)
            ruleItem.setRuleFromDateUtil(rule)
            self.rruleset = ruleItem
        else:
            if self.getFirstInRule() != self:
                rruleset = Recurrence.RecurrenceRuleSet(None, itsView=self.itsView)
                rruleset.setRuleFromDateUtil(rule)
                self.changeThisAndFuture('rruleset', rruleset)
            else:
                self.rruleset.setRuleFromDateUtil(rule)

    def delete(self, *args, **kwargs):
        """If self is the master of a recurring event, call deleteAll."""
        if self.hasLocalAttributeValue('rruleset') and self.getMaster() == self:
            self.deleteAll()
        else:
            self._ignoreValueChanges = True
            super(CalendarEventMixin, self).delete(*args, **kwargs)

    def _cloneEvent(self):

        clone = self.clone(None, None, ('collections',))
        clone.updateRecurrenceEnd()

        return clone

    def _createOccurrence(self, recurrenceID):
        """
        Generate an occurrence for recurrenceID, return it.
        """

        first = self.getFirstInRule()
        if first is not self:
            return first._createOccurrence(recurrenceID)

        item = self.clone(None, None, ('collections', 'recurrenceEnd'), False,
                          isGenerated=True,
                          recurrenceID=recurrenceID,
                          startTime=recurrenceID,
                          occurrenceFor=first,
                          modificationFor=None)
        item._fixReminders()
        return item

    def getNextOccurrence(self, after=None, before=None):
        """Return the next occurrence for the recurring event self is part of.

        If self is the only occurrence, or the last occurrence, return None.

        @param after: Earliest end time allowed
        @type  after: C{datetime} or C{None}

        @param before: Latest start time allowed
        @type  before: C{datetime} or C{None}

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
                    return ((self.startTime < mod.startTime) and
                           (before is None or (mod.startTime < before)))
            else:
                def test(mod):
                    return mod.isBetween(after, before)
            withMaster = []
            if first.occurrenceFor is not None:
                withMaster.append(first)
            for mod in itertools.chain(withMaster, first.modifications or []):
                if test(mod):
                    if nextEvent is None:
                        nextEvent = mod
                    # sort by recurrenceID if startTimes are equal
                    elif ((mod.startTime < nextEvent.startTime) or
                         ((mod.startTime == nextEvent.startTime)
                          and (mod.recurrenceID  < nextEvent.recurrenceID))):
                        nextEvent = mod
            return nextEvent

        # main getNextOccurrence logic
        if self.rruleset is None:
            return None

        first = self.getMaster()
        exact = after is not None and after == before

        # take duration into account if after is set
        if not exact and after is not None:
            start = prepDatetime(after) - first.duration
        else:
            start = prepDatetime(self.startTime)

        if before is not None:
            before = prepDatetime(before)

        ruleset = self.createDateUtilFromRule()


        for recurrenceID in ruleset:

            preparedRID = prepDatetime(recurrenceID)

            if (preparedRID < start or (not exact and preparedRID == start)):
                continue

            if before is not None and preparedRID > before:
                return checkModifications(first, before)

            calculated = self.getExistingOccurrence(recurrenceID)
            if calculated is None:
                return checkModifications(first, before,
                                          self._createOccurrence(recurrenceID))
            elif calculated.isGenerated or exact:
                return checkModifications(first, before, calculated)

        return checkModifications(first, before)

    def _fixReminders(self):
        # When creating generated events, this function is
        # called so that all reminders in the past are marked
        # expired, and the rest are not. This helps avoid a
        # mass of reminders if an event in the past is changed.
        #
        now = datetime.now(ICUtzinfo.default)

        def expired(reminder):
            nextTime = reminder.getNextReminderTimeFor(self)
            return (nextTime is not None and nextTime <= now)


        # We really don't want to touch self.reminders
        # or self.expiredReminders if they haven't really
        # changed. The reason is that that will trigger a
        # change notification on app idle, which in turn causes
        # the UI to re-generate all these occurrences, which puts
        # us back in this # method, etc, etc.

        # Figure out what (if anything) has changed ...
        nowExpired = [r for r in self.reminders
                        if expired(r)]

        nowNotExpired = [r for r in self.expiredReminders
                           if not expired(r)]

        # ... and update the collections accordingly
        for reminder in nowExpired:
            self.expiredReminders.add(reminder)
            self.reminders.remove(reminder)

        for reminder in nowNotExpired:
            self.reminders.add(reminder)
            self.expiredReminders.remove(reminder)


    def _generateRule(self, after=None, before=None, inclusive=False):
        """Yield all occurrences in this rule."""
        event = first = self.getFirstInRule()
        # check for modifications taking place before first, but only if
        # if we're actually interested in dates before first (i.e., the
        # after argument is None or less than first.startTime)

        prepDatetime = self.__getDatetimePrepFunction()

        if (first.modifications is not None and
            (after is None or prepDatetime(after) < prepDatetime(first.startTime))):
            for mod in first.modifications:
                if prepDatetime(mod.startTime) <= prepDatetime(event.startTime):
                    event = mod

        if not event.isBetween(after, before):
            event = first.getNextOccurrence(after, before)
        else:
            # [Bug 5482], [Bug 5627], [Bug 6174]
            # We need to make sure event is actually
            # included in our recurrence rule.
            rruleset = self.createDateUtilFromRule()

            recurrenceID = event.recurrenceID
            if isDayItem(event):
                recurrenceID = datetime.combine(
                                    recurrenceID.date(),
                                    time(0, tzinfo=recurrenceID.tzinfo))

            if not recurrenceID in rruleset:
                event = event.getNextOccurrence()

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
        if self.rruleset == None: return None

        first = self.getFirstInRule()
        if first != self: return first._getFirstGeneratedOccurrence(create)

        # make sure recurrenceID gets set for all masters
        if self.recurrenceID is None:
            self.recurrenceID = self.startTime

        if create:
            iter = self._generateRule()
        else:
            if self.occurrences == None:
                return None
            iter = _sortEvents(self.occurrences)
        for occurrence in iter:
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

        @rtype: C{list} containing 0 or more C{CalendarEventMixin}s

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

        @rtype: C{datetime} or C{None}

        """
        first = self.getFirstInRule()

        # When an event is imported via sharing, the constructor is bypassed
        # and we need to make sure occurrences has a value
        if first.occurrences is not None:
            for occurrence in first.occurrences:
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

    def _makeGeneralChange(self):
        """Do everything that should happen for any change call."""
        self.isGenerated = False

    def changeNoModification(self, attr, value):
        """Set _ignoreValueChanges flag, set the attribute, then unset flag."""
        flagStart = getattr(self, '_ignoreValueChanges', None)
        self._ignoreValueChanges = True
        setattr(self, attr, value)
        if flagStart is None:
            del self._ignoreValueChanges

    def _propagateChange(self, modification):
        """Move later modifications to self."""
        # [@@@] grant != or is not?
        if (modification.occurrenceFor != self and
            modification.recurrenceID > self.startTime):
            # future 'this' modifications in master should move to self
            modification.modificationFor = self
            modification.occurrenceFor = self
            modification.rruleset = self.rruleset
            modification.icalUID = self.icalUID

    def changeThisAndFuture(self, attr=None, value=None):
        """Modify this and all future events."""
        master = self.getMaster()
        first = master # Changed for no-THISANDFUTURE-style
        if self.recurrenceID is None:
            self.recurrenceID = self.startTime
        recurrenceID = self.recurrenceID
        # we can't use master.effectiveStartTime because the event timezone and
        # the current timezone may not match
        isFirst = (((master.allDay or master.anyTime) and
                    recurrenceID.date() == master.startTime.date()) or
                   (recurrenceID == master.startTime))
        self._ignoreValueChanges = True

        # all day events' startTime is at midnight
        startMidnight = datetime.combine(self.startTime.date(),
                                         time(0, tzinfo=self.startTime.tzinfo))

        if attr in ('startTime', 'allDay', 'anyTime'):
            # if startTime changes (and an allDay/anyTime change changes
            # effective startTime), all future occurrences need to be shifted
            # appropriately
            startTimeDelta = zero_delta
            if attr == 'startTime':
                startTimeDelta = (value - self.startTime)
            # don't move future occurrences unless allDayness (anyTime or
            # allDay) changes
            else:
                if attr == 'allDay':
                    otherAllDayness = self.anyTime
                else:
                    otherAllDayness = self.allDay
                if (value or otherAllDayness) != (getattr(self, attr) or
                                                  otherAllDayness):
                    if value == False:
                        startTimeDelta = self.startTime - startMidnight
                    else:
                        startTimeDelta = startMidnight - self.startTime

            if startTimeDelta != zero_delta:
                self.rruleset.moveDatesAfter(recurrenceID, startTimeDelta)

        setattr(self, attr, value)

        def makeThisAndFutureMod():
            # Changing occurrenceFor before changing rruleset is important, it
            # keeps the rruleset change from propagating inappropriately
            self.occurrenceFor = self
            if attr != 'rruleset':
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
            self.icalUID = unicode(self.itsUUID)
            self.copyCollections(master, self)

        # determine what type of change to make
        if attr == 'rruleset': # rule change, thus a destructive change
            self.removeFutureOccurrences()
            if self.recurrenceID == master.startTime and self.modificationFor == master:
                # A THIS modification to master, make it the new master
                self.moveCollections(master, self)
                del self.modificationFor
                self.occurrenceFor = self
                self.recurrenceID = self.startTime
                master.deleteAll()
            elif self == master: # self is master, nothing to do
                pass
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
                    newfirst._ignoreValueChanges = True
                    newfirst.rruleset = self.rruleset.copy(cloudAlias='copying')
                    # There are two events in play, self (which has been
                    # changed), and newfirst, a non-displayed item used to
                    # define generated events.  Make sure the current change
                    # is applied to both items, and that both items have the
                    # same rruleset.
                    setattr(newfirst, attr, value)
                    self.rruleset = newfirst.rruleset
                    newfirst.startTime = self.recurrenceID
                    newfirst.occurrenceFor = None #self overrides newfirst
                    newfirst.icalUID = self.icalUID = str(newfirst.itsUUID)
                    newfirst._makeGeneralChange()
                    self.occurrenceFor = self.modificationFor = newfirst
                    self.copyCollections(master, newfirst)
                    # move THIS modifications after self to newfirst
                    if first.hasLocalAttributeValue('modifications'):
                        for mod in first.modifications:
                            if mod.recurrenceID > newfirst.startTime:
                                mod.occurrenceFor = newfirst
                                mod.modificationFor = newfirst
                                mod.icalUID = newfirst.icalUID
                                mod.rruleset = newfirst.rruleset
                                #rruleset needs to change, so does icalUID
                    del newfirst._ignoreValueChanges
                else:
                    # self was a THIS modification to the master, setattr needs
                    # to be called on master
                    if attr == 'startTime':
                        newStart = master.startTime + startTimeDelta
                        master.changeNoModification('startTime', newStart)
                        master.changeNoModification('recurrenceID', newStart)
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

            if master.modifications:
                for mod in master.modifications:
                    self.occurrenceFor._propagateChange(mod)
                    # change recurrenceIDs for modifications if startTime change
                    if attr == 'startTime' and mod.modificationFor == self:
                        mod.changeNoModification('recurrenceID',
                            mod.recurrenceID + startTimeDelta)
            if not isFirst:
                master.moveRuleEndBefore(recurrenceID)

            # if modifications were moved from master to self, they may have the
            # same recurrenceID as a (spurious) generated event, so delete
            # generated occurrences.

            self._deleteGeneratedOccurrences()
            self._getFirstGeneratedOccurrence(True)

        del self._ignoreValueChanges

    def moveCollections(self, fromItem, toItem):
        """Move all collection references from one item to another."""
        for collection in getattr(fromItem, 'collections', []):
            collection.add(toItem)
            collection.remove(fromItem)

    def copyCollections(self, fromItem, toItem):
        """Copy all collection references from one item to another."""
        for collection in getattr(fromItem, 'collections', []):
            collection.add(toItem)

    def changeThis(self, attr=None, value=None):
        """Make this event a modification, don't modify future events.

        Without arguments, change self appropriately to make it a THIS
        modification.

        """
        if self.modificationFor is not None:
            pass
        elif self.rruleset is not None:
            first = self.getFirstInRule()
            master = self.getMaster()
            if first == self:
                # self may have already been changed, find a backup to copy
                backup = self._getFirstGeneratedOccurrence()
                if backup is not None:
                    newfirst = backup._cloneEvent()
                    newfirst._ignoreValueChanges = True
                    self.moveCollections(master, newfirst)
                    newfirst.startTime = self.modificationRecurrenceID or \
                                         self.recurrenceID
                    if self.hasLocalAttributeValue('modifications'):
                        for mod in self.modifications:
                            mod.modificationFor = newfirst
                    if self.hasLocalAttributeValue('occurrences'):
                        for occ in self.occurrences:
                            occ.occurrenceFor = newfirst
                    newfirst.occurrenceFor = None #self overrides newfirst
                    newfirst.modificationFor = self.modificationFor
                    # Unnecessary when we switch endTime->duration
                    newfirst.duration = backup.duration
                    self.occurrenceFor = self.modificationFor = newfirst
                    newfirst._makeGeneralChange()
                    self.recurrenceID = newfirst.startTime
                    # for 0.6, to diminish sharing problems, change the icalUID
                    # of the recurrence set when master is changed
                    newfirst.icalUID = unicode(newfirst.itsUUID)
                    for occurrence in newfirst.occurrences:
                        occurrence.changeNoModification('icalUID', newfirst.icalUID)
                    if self.hasLocalAttributeValue('modificationRecurrenceID'):
                        del self.modificationRecurrenceID
                    del newfirst._ignoreValueChanges
                # if backup is None, allow the change to stand, applying just
                # to self.  This relies on _getFirstGeneratedOccurrence() always
                # being called.  Still, make sure changes to startTime change
                # modificationRecurrenceID, and recurrenceID if self is master.
                else:
                    self.modificationRecurrenceID = self.startTime
                    if master == self:
                        self.recurrenceID = self.startTime

            else:
                self.modificationFor = first
                self._makeGeneralChange()
                self._getFirstGeneratedOccurrence(True)
        if attr is not None:
            setattr(self, attr, value)

    def addToCollection(self, collection):
        """
        If recurring, create a proxy and use its addToCollection().

        This method should be used by UI related code, when user feedback is
        appropriate.  To add to collections unrelated to UI, use
        collection.add().

        """
        if self.rruleset is None:
            super(CalendarEventMixin, self).addToCollection(collection)
        else:
            RecurrenceDialog.getProxy(u'ui', self).addToCollection(collection)


    def removeFromCollection(self, collection, cutting=False):
        """
        If recurring, create a proxy and use its removeFromCollection().

        This method should be used by UI related code, when user feedback is
        appropriate.  To remove from collections unrelated to UI, use
        collection.remove().

        @param cutting: Whether this removal is associated with a cut, or just
                        a removal.
        @type  cutting: C{bool}

        """
        if self.rruleset is None:
            super(CalendarEventMixin, self).removeFromCollection(collection, cutting)
        else:
            RecurrenceDialog.getProxy(u'ui', self).removeFromCollection(collection, cutting)

    changeNames = ('displayName', 'startTime', 'duration', 'location', 'body',
                   'lastModified', 'allDay')

    def onValueChanged(self, name):
        """
        Maintain coherence of the various recurring items associated with self
        after an attribute has been changed.

        """
        # allow initialization code to avoid triggering onValueChanged
        rruleset = name == 'rruleset'
        changeName = not rruleset and name in CalendarEventMixin.changeNames

        if (not (rruleset or changeName) or
            self.rruleset is None or
            getattr(self, '_share_importing', False) or
            getattr(self, '_ignoreValueChanges', False)):
            return
        # avoid infinite loops
        if rruleset:
            logger.debug("just set rruleset")
            gen = self._getFirstGeneratedOccurrence(True)
            if DEBUG and gen:
                logger.debug("got first generated occurrence, %s", gen.serializeMods().getvalue())

            # make sure masters get modificationRecurrenceID set
            if self == self.getFirstInRule():
                self.modificationRecurrenceID = self.startTime
                self.recurrenceID = self.startTime
                self.updateRecurrenceEnd()

        # the changeName kludge should be replaced with the new domain attribute
        # aspect, just using a fixed list of attributes which should trigger
        # changeThis won't work with stamping
        elif changeName:
            if DEBUG:
                logger.debug("about to changeThis in onValueChanged(name=%s) for %s", name, str(self))
                logger.debug("value is: %s", getattr(self, name))
            if name == 'duration' and self == self.getFirstInRule():
                self.updateRecurrenceEnd()
            self.changeThis()

    def _deleteGeneratedOccurrences(self):
        first = self.getFirstInRule()
        for event in first.occurrences:
            if event.isGenerated:
                # don't let deletion result in spurious onValueChanged calls
                event._ignoreValueChanges = True
                event.delete()

    def cleanRule(self):
        """Delete generated occurrences in the current rule, create a backup."""
        first = self.getFirstInRule()
        self._deleteGeneratedOccurrences()
        if first.hasLocalAttributeValue('modifications'):
            until = first.rruleset.rrules.first().calculatedUntil()
            for mod in first.modifications:
                # this won't work for complicated rrulesets
                if until != None and (mod.recurrenceID > until):
                    mod._ignoreValueChanges = True
                    mod.delete()

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
        rruleset = self.rruleset
        recurrenceID = self.recurrenceID
        if getattr(rruleset, 'exdates', None) is None:
            rruleset.exdates=[]
        rruleset.exdates.append(recurrenceID)
        if getattr(self, 'occurrenceFor', None) == self:
            self.occurrenceFor = None
        else:
            self.delete()

    def deleteAll(self):
        """Delete master, all its modifications, occurrences, and rules."""
        master = self.getMaster()
        for event in master.occurrences:
            if event in (master, self): #don't delete master or self quite yet
                continue
            event._ignoreValueChanges = True
            event.delete(recursive=True)

        rruleset = self.rruleset
        rruleset._ignoreValueChanges = True
        # we don't want rruleset's recursive delete to get self yet
        del self.rruleset
        rruleset._ignoreValueChanges = True
        rruleset.delete(recursive=True)
        self._ignoreValueChanges = True
        master.delete(recursive=True)
        self.delete(recursive=True)

    def removeFutureOccurrences(self):
        """Delete all future occurrences and modifications."""
        master = self.getMaster()
        for event in master.occurrences:
            if event.startTime >  self.startTime:
                event._ignoreValueChanges = True
                event.delete()

        self._getFirstGeneratedOccurrence(True)

    def removeRecurrence(self):
        """
        Remove modifications, rruleset, and all occurrences except master.

        The resulting event will occur exactly once.
        """
        master = self.getMaster()
        if not master.recurrenceID in (None, master.startTime):
            master.changeNoModification('recurrenceID', master.startTime)
        rruleset = master.rruleset
        if rruleset is not None:
            rruleset._ignoreValueChanges = True
            masterHadModification = False
            for event in master.occurrences:

                if event.recurrenceID != master.startTime:
                    # Since we're possibly doing delayed deleting (if we're
                    # in the background sharing mode) let's remove the events
                    # from occurrences:
                    master.occurrences.remove(event)
                    # now that we've disconnected this event from the master,
                    # event.delete() will erroneously dispatch to deleteAll() if
                    # event.rruleset exists, so disconnect from the rruleset
                    del event.rruleset
                    event.delete()

                elif event != master:
                    # A THIS modification to master, make it the new master
                    self.moveCollections(master, event)
                    del event.rruleset
                    del event.recurrenceID
                    del event.modificationFor
                    event.occurrenceFor = event
                    # events with the same icalUID but different UUID drive
                    # sharing crazy, so change icalUID of master
                    event.icalUID = unicode(event.itsUUID)
                    masterHadModification = True

            rruleset._ignoreValueChanges = True
            rruleset.delete()

            if masterHadModification:
                master.delete()
            else:
                del master.recurrenceID
                del master.rruleset
                master.occurrenceFor = master



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
        return super(CalendarEventMixin, self).isAttributeModifiable(attribute)

    def cmpTimeAttribute(self, item, attr, useTZ=True):
        """Compare item and self.attr, ignore timezones if useTZ is False."""
        itemTime = getattr(item, attr, None)
        selfTime = getattr(self, attr, None)

        if itemTime is None:
            if selfTime is None:
                # both attributes are None, so item and self compare as equal
                return 0
            else:
                return -1
        elif not useTZ:
            itemTime = itemTime.replace(tzinfo = None)

        if selfTime is None:
            return 1
        elif not useTZ:
            selfTime = selfTime.replace(tzinfo = None)

        return cmp(selfTime, itemTime)

    # for use in indexing CalendarEventMixins
    def cmpStartTime(self, item):
        return self.cmpTimeAttribute(item, 'effectiveStartTime')

    def cmpEndTime(self, item):
        return self.cmpTimeAttribute(item, 'effectiveEndTime')

    def cmpRecurEnd(self, item):
        return self.cmpTimeAttribute(item, 'recurrenceEnd')

    def cmpReminderTime(self, item):
        return self.cmpTimeAttribute(item, 'reminderFireTime')

    # comparisons which strip timezones
    def cmpStartTimeNoTZ(self, item):
        return self.cmpTimeAttribute(item, 'effectiveStartTime', False)

    def cmpEndTimeNoTZ(self, item):
        return self.cmpTimeAttribute(item, 'effectiveEndTime', False)

    def cmpRecurEndNoTZ(self, item):
        return self.cmpTimeAttribute(item, 'recurrenceEnd', False)

class CalendarEvent(CalendarEventMixin, Note):
    """An unstamped event."""

    def __init__(self, *args, **kw):
        kw.setdefault('participants',[])
        super (CalendarEvent, self).__init__(*args, **kw)


class Calendar(ContentItem):
    """Unused, should be removed."""



class Location(ContentItem):
    """Stub Kind for Location."""


    eventsAtLocation = schema.Sequence(
        CalendarEventMixin,
        inverse=CalendarEventMixin.location
    )


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


class RecurrencePattern(ContentItem):
    """Unused, should be removed."""

