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
from __future__ import with_statement

import application.schema as schema
from osaf import Preferences
from osaf.pim.stamping import has_stamp

import PyICU
import dateutil.tz
import vobject
import itertools

import datetime
from i18n import ChandlerMessageFactory


def reindexFloatingEvents(view, tzinfo):
    """
    When the user's default timezone changes, datetime values with a floating
    timezone may compare differently with non-floating datetimes than before.
    So, we need to resort some indexes if they did comparison of floating
    datetimes. At the moment, the only way we let floating datetimes creep into
    indexes is via C{EventStamp.startTime}, C{EventStamp.recurrenceEnd} and
    C{ContentItem.displayDate} (the latter being computed in some cases from
    the first).
    """
    pim_ns = schema.ns("osaf.pim", view)
    EventStamp = pim_ns.EventStamp

    attrs = (EventStamp.startTime.name, EventStamp.recurrenceEnd.name,
            'displayDate')

    # Ask the view to trigger reindexing for all the above attributes, for
    # all floating events. This should cover the cases above.
    floatingEvents = pim_ns.floatingEvents
    if view.isRefreshing():
        floatingEvents = [item for item in view.dirtyItems()
                          if item in floatingEvents]
    if floatingEvents:
        view.reindex(floatingEvents, *attrs)

    # [Bug 8688] Re-calculate until based on new (non-floating) timezone
    ruleClass = schema.ns("osaf.pim.calendar.Recurrence", view).RecurrenceRule
    for uuid in ruleClass.getKind(view).iterKeys():
        until = view.findValue(uuid, 'until', None)

        if until is not None:
            view[uuid].until = until.replace(tzinfo=tzinfo)


# The repository's view default timezone change callback
def ontzchange(view, tzinfo):

    view.logger.warning("%s: timezone changed to %s", view, tzinfo)

    defaultInfo = TimeZoneInfo.get(view)
    default = defaultInfo.canonicalTimeZone(tzinfo)
      
    if not view.isRefreshing():
        # only set defaultInfo's timezone if timezones are used
        if default is not None and defaultInfo.default != view.tzinfo.floating:
            defaultInfo.default = default

    reindexFloatingEvents(view, default)


def equivalentTZIDs(tzinfo):
    numEquivalents = PyICU.TimeZone.countEquivalentIDs(tzinfo.tzid)
    for index in xrange(numEquivalents):
        yield PyICU.TimeZone.getEquivalentID(tzinfo.tzid, index)


class TimeZoneInfo(schema.Item):
    """
    Item that persists:
     - A schema.TimeZone attribute that synchronizes
       itself with PyICU's default settings.
     - A list of "well-known" timezone names.
    """

    default = schema.One(schema.TimeZone)

    # List of well-known time zones (for populating drop-downs).
    # [i18n] Since ICU doesn't suitably localize strings like 'US/Pacific',
    # we'll have to provide our own translations.
    wellKnownIDs = schema.Sequence(
        schema.Text,
    )

    schema.initialValues(
        default = lambda self: self.itsView.tzinfo.floating
    )

    # Observe changes to 'default'.
    # When the view's default timezone changes via another route such as
    # refresh(), ontzchange is invoked by the repository
    @schema.observer(default)
    def onDefaultChanged(self, op, name):

        # Make sure that the view's default timezone is synched with ours
        view = self.itsView
        default = self.default

        # only set the view's default timezone if timezones are used
        if default is not None and default != view.tzinfo.floating:
            assert view.tzinfo.ontzchange is ontzchange
            view.tzinfo.setDefault(default)  # --> ontzchange
        else:
            self.default = self.canonicalTimeZone(default)

    @classmethod
    def get(cls, view):
        """
        Return the default C{TimeZoneInfo} instance, which
        automatically syncs with the view's default; i.e. if you
        assign an ICUtzinfo to C{TimeZoneInfo.get().default},
        this will be stored as the view's default time zone.
        """

        return schema.ns(__name__, view).defaultInfo

    def canonicalTimeZone(self, tzinfo):
        """
        This returns an ICUtzinfo that's equivalent to the passed-in
        tzinfo, to prevent duplicates (like 'PST' and 'US/Pacific'
        from appearing in timezone pickers).

        A side-effect is that if a previously unseen tzinfo is
        passed in, it will be added to the receiver's wellKnownIDs.
        """
        view = self.itsView

        if tzinfo is None or tzinfo == view.tzinfo.floating:
            result = view.tzinfo.floating

        else:
            result = None

            if tzinfo.tzid in self.wellKnownIDs:
                result = tzinfo
            else:
                for equivName in equivalentTZIDs(tzinfo):
                    if equivName in self.wellKnownIDs:
                        result = view.tzinfo.getInstance(equivName)
                        break

            if result is None and tzinfo is not None:
                self.wellKnownIDs.append(unicode(tzinfo.tzid))
                result = tzinfo

        return result

    def iterTimeZones(self, withFloating=True):
        """
        A generator for all the well-known ICUtzinfo objects. Each
        generated value is a tuple of the form (display name, ICUtzinfo),
        where 'display name' is a suitably localized unicode string.
        """

        view = self.itsView
        floating = view.tzinfo.floating

        for name in self.wellKnownIDs:
            tzinfo = view.tzinfo.getInstance(name)

            if tzinfo != floating:
                yield (ChandlerMessageFactory(name), tzinfo)

        if withFloating:
            # L10N: Entry in the 'timezone' drop-down menu in the detail view
            # L10N: when an event has no time zone (also known as "Floating"
            # L10N: time). In English, this is translated as "None", but I
            # L10N: didn't want to use "None" in a msgid because that could
            # L10N: be used in other context (e.g. "alarm" dropdown).
            _ = ChandlerMessageFactory # we want this translated
            yield _(u"None (timezone)"), floating


class TZPrefs(Preferences):
    showUI = schema.One(schema.Boolean, initialValue = False)
    showPrompt = schema.One(schema.Boolean, initialValue = True,
                        doc="Show a prompt to turn on timezones when "
                            "timezone interactions happen")


    @schema.observer(showUI)
    def onShowUIChanged(self, op, attrName):
        timeZoneInfo = TimeZoneInfo.get(self.itsView)

        # Sync up the default timezone (i.e. the one used when
        # creating new events).
        view = self.itsView
        if self.showUI:
            timeZoneInfo.default = view.tzinfo.default
            convertFloatingEvents(view, view.tzinfo.default)
        else:
            timeZoneInfo.default = view.tzinfo.floating


def installParcel(parcel, oldVersion = None):
    TZPrefs.update(parcel, 'TimezonePrefs')

    # Get our parcel's namespace
    namespace = schema.ns(__name__, parcel.itsView)

    # This is a little cheesy...

    # We define _() here so that the wellKnownIDs
    # strings below are picked up for translation by
    # pygettext.py.
    #
    # By having _ return the original string, we store
    # (untranslated) TZIDs in the repository. This is
    # actually what we want, since ICU would have no idea
    # how to look up timezones based on the translated
    # names.
    from i18n import NoTranslationMessageFactory as _

    wellKnownIDs = [
        _(u'Pacific/Honolulu'),
        _(u'America/Anchorage'),
        _(u'America/Los_Angeles'),
        _(u'America/Denver'),
        _(u'America/Chicago'),
        _(u'America/New_York'),
        _(u'World/Floating'),
    ]

    # Set up our parcel's 'defaultInfo' attribute
    TimeZoneInfo.update(namespace.parcel, 'defaultInfo',
                        wellKnownIDs=wellKnownIDs)


def stripTimeZone(view, dt):
    """
    This method returns a naive C{datetime} (i.e. one with a
    C{tzinfo} of C{None}.

    @param dt: The input.
    @type dt: C{datetime}

    @return: If the input is naive, just returns dt. Otherwise, converts
             the input into the user's default timezone, and then strips
             that out.
    """

    if dt.tzinfo == None:
        return dt
    else:
        return dt.astimezone(view.tzinfo.default).replace(tzinfo=None)

def forceToDateTime(view, dt, tzinfo=None):
    """
    If dt is a datetime, return dt, if a date, add time(0) and return.

    @param dt: The input.
    @type dt: C{datetime} or C{date}

    @return: A C{datetime}
    """
    if tzinfo is None:
        tzinfo = view.tzinfo.floating
    if type(dt) == datetime.datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tzinfo)
        else:
            return dt
    elif type(dt) == datetime.date:
        return datetime.datetime.combine(dt, datetime.time(0, tzinfo=tzinfo))

def coerceTimeZone(view, dt, tzinfo):
    """
    This method returns a C{datetime} with a specified C{tzinfo}.

    If the target tzinfo is C{None}, this returns C{stripTimeZone(dt)}.
    Otherwise, if C{dt} is naive, it's interpreted as being in the user's
    default timezone.

    @param dt: The input.
    @type dt: C{datetime}

    @param tzinfo: The target tzinfo (may be None)
    @type tzinfo:  C{tzinfo}

    @return: A C{datetime} whose C{tzinfo} field is the same as the target.
    """
    if tzinfo is None:
        return stripTimeZone(view, dt)
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=view.tzinfo.default)
        return dt.astimezone(tzinfo)


tzid_mapping = {}
dateutil_utc = dateutil.tz.tzutc()

def convertToICUtzinfo(view, dt):
    """
    This method returns a C{datetime} whose C{tzinfo} field
    (if any) is an instance of the ICUtzinfo class.

    @param dt: The C{datetime} whose C{tzinfo} field we want
               to convert to an ICUtzinfo instance.
    @type dt: C{datetime}
    """

    oldTzinfo = getattr(dt, 'tzinfo', None)
    if isinstance(oldTzinfo, (PyICU.ICUtzinfo, PyICU.FloatingTZ)):
        return dt
    elif oldTzinfo is None:
        icuTzinfo = None # Will patch to floating at the end
    else:

        def getICUInstance(name):
            result = None
            if name is not None:
                result = view.tzinfo.getInstance(name)
                if result is not None and \
                    result.tzid == 'GMT' and \
                    name != 'GMT':
                    result = None

            return result


        # First, for dateutil.tz._tzicalvtz, we check
        # _tzid, since that's the displayable timezone
        # we want to use. This is kind of cheesy, but
        # works for now. This means that we're preferring
        # a tz like 'America/Chicago' over 'CST' or 'CDT'.
        tzical_tzid = getattr(oldTzinfo, '_tzid', None)
        icuTzinfo = getICUInstance(tzical_tzid)

        if tzical_tzid is not None:
            if tzid_mapping.has_key(tzical_tzid):
                # we've already calculated a tzinfo for this tzid
                icuTzinfo = tzid_mapping[tzical_tzid]

        if icuTzinfo is None:
            # special case UTC, because dateutil.tz.tzutc() doesn't have a TZID
            # and a VTIMEZONE isn't used for UTC
            if vobject.icalendar.tzinfo_eq(dateutil_utc, oldTzinfo):
                icuTzinfo = view.tzinfo.UTC

        # iterate over all PyICU timezones, return the first one whose
        # offsets and DST transitions match oldTzinfo.  This is painfully
        # inefficient, but we should do it only once per unrecognized timezone,
        # so optimization seems premature.
        backup = None
        if icuTzinfo is None:
            if view is not None:
                info = TimeZoneInfo.get(view)
                well_known = (t[1].tzid for t in info.iterTimeZones())
            else:
                well_known = []

            # canonicalTimeZone doesn't help us here, because our matching
            # criteria aren't as strict as PyICU's, so iterate over well known
            # timezones first
            for tzid in itertools.chain(well_known,
                                        PyICU.TimeZone.createEnumeration()):
                test_tzinfo = getICUInstance(tzid)
                # only test for the DST transitions for the year of the event
                # being converted.  This could be very wrong, but sadly it's
                # legal (and common practice) to serialize VTIMEZONEs with only
                # one year's DST transitions in it.  Some clients (notably iCal)
                # won't even bother to get that year's offset transitions right,
                # but in that case, we really can't pin down a timezone
                # definitively anyway (fortunately iCal uses standard zoneinfo
                # tzid strings, so getICUInstance above should just work)
                if vobject.icalendar.tzinfo_eq(test_tzinfo, oldTzinfo,
                                               dt.year, dt.year + 1):
                    icuTzinfo = test_tzinfo
                    if tzical_tzid is not None:
                        tzid_mapping[tzical_tzid] = icuTzinfo
                    break
                # sadly, with the advent of the new US timezones, Exchange has
                # chosen to serialize US timezone DST transitions as if they
                # began in 1601, so we can't rely on dt.year.  So also try
                # 2007-2008, but treat any matches as a backup, they're
                # less reliable, since the VTIMEZONE may not define DST
                # transitions for 2007-2008.  Keep the first match, since we
                # process well known timezones first, and there's no way to
                # distinguish between, say, America/Detroit and America/New_York
                # in the 21st century.
                if backup is None:
                    if vobject.icalendar.tzinfo_eq(test_tzinfo, oldTzinfo,
                                                   2007, 2008):
                        backup = test_tzinfo
        if icuTzinfo is None and backup is not None:
            icuTzinfo = backup            
            if tzical_tzid is not None:
                tzid_mapping[tzical_tzid] = icuTzinfo

    # Here, if we have an unknown timezone, we'll turn
    # it into a floating datetime
    if icuTzinfo is None:
        icuTzinfo = view.tzinfo.floating

    if not hasattr(dt, 'hour'):
        dt = forceToDateTime(view, dt, icuTzinfo)
    else:
        dt = dt.replace(tzinfo=icuTzinfo)

    return dt

def shortTZ(view, dt, tzinfo=None):
    """
    Return an empty string or the short timezone string for dt if dt.tzinfo
    doesn't match tzinfo (tzinfo defaults to PyICU.ICUtzinfo.default)

    """
    if tzinfo is None:
        tzinfo = view.tzinfo.default

    if dt.tzinfo is None or dt.tzinfo == view.tzinfo.floating:
        return u''
    elif dt.tzinfo != tzinfo:
        # make sure they aren't equivalent
        if (dt.tzinfo.timezone.getRawOffset() ==
               tzinfo.timezone.getRawOffset()):
            for tzid in equivalentTZIDs(tzinfo):
                if dt.tzinfo.tzid == tzid:
                    return u''

        name = dt.tzinfo.timezone.getDisplayName(dt.dst(),
                                          dt.tzinfo.timezone.SHORT)
        if not name:
            return u''
        else:
            return name
    return u''


class DateAndNoDateFormats(object):
    __slots__ = 'date', 'nodate', 'hour'

FormatDictParent = {True:{}, False:{}}

def _setTimeZoneInSubformats(msgFormat, tz):
    subformats = msgFormat.getFormats()

    for format in subformats:
            if hasattr(format, "setTimeZone"):
                format.setTimeZone(tz)

    msgFormat.setFormats(subformats)

def formatTime(view, dt, tzinfo=None, noTZ=False, includeDate=False,
               justHour=False):
    if tzinfo is None:
        tzinfo = view.tzinfo.default

    useSameTimeZoneFormat = True

    if dt.tzinfo is None or dt.tzinfo == view.tzinfo.floating or noTZ:
        dt = dt.replace(tzinfo=tzinfo)
    elif dt.tzinfo != tzinfo:
        useSameTimeZoneFormat = False
        
    formattable = PyICU.Formattable(dt, PyICU.Formattable.kIsDate)
    FormatDict = FormatDictParent[useSameTimeZoneFormat or noTZ]
    formats = FormatDict.get((dt.tzinfo, tzinfo))
    if formats is None:
        formats = DateAndNoDateFormats()
        if useSameTimeZoneFormat or noTZ:
            formats.date = PyICU.MessageFormat("{0,date,medium} {0,time,short}")
            formats.nodate = PyICU.MessageFormat("{0,time,short}")        
        else:
            formats.date = PyICU.MessageFormat(
                                 "{0,date,medium} {0,time,short} {0,time,z}")
            formats.nodate = PyICU.MessageFormat("{0,time,short} {0,time,z}")

        # this is cheating, there's got to be an API to expand short, but I
        # don't know it.  Calling the format method does it, though.
        formats.nodate.format([formattable], PyICU.FieldPosition())
        short = formats.nodate.toPattern().split(',')[2]
        localeHour = 'h' if short.find('h') >= 0 else 'H'
        formats.hour = PyICU.MessageFormat("{0,time,%s}" % localeHour)

        _setTimeZoneInSubformats(formats.nodate, dt.tzinfo.timezone)
        _setTimeZoneInSubformats(formats.date, dt.tzinfo.timezone)
        FormatDict[(dt.tzinfo, tzinfo)] = formats

    if justHour:
        format = formats.hour
    else:
        format = (formats.date if includeDate else formats.nodate)

    return unicode(format.format([formattable], PyICU.FieldPosition()))

def getTimeZoneCode(view, dt):
    tzinfo = view.tzinfo.default

    if dt.tzinfo is None or dt.tzinfo == view.tzinfo.floating:
        dt = dt.replace(tzinfo=tzinfo)

    format = PyICU.MessageFormat("{0,time,z}")

    _setTimeZoneInSubformats(format, dt.tzinfo.timezone)
    formattable = PyICU.Formattable(dt, PyICU.Formattable.kIsDate)

    return unicode(format.format([formattable], PyICU.FieldPosition()))

def serializeTimeZone(tzinfo):
    """Given a tzinfo class, return a VTIMEZONE in an iCalendar object."""
    cal = vobject.iCalendar()
    cal.add(vobject.icalendar.TimezoneComponent(tzinfo=tzinfo))
    return cal.serialize()

def convertFloatingEvents(view, newTZ):
    """Convert existing floating events to the default timezone.

    Don't convert events that are in shared collections, because they may be
    someone else's events and are intended to be floating. 

    """
    pim_ns = schema.ns("osaf.pim", view)
    sharing_ns = schema.ns("osaf.sharing", view)

    EventStamp = pim_ns.EventStamp
    def replaceTZ(dt):
        return dt.replace(tzinfo=newTZ)
    # put all floating events in a list, because we can't iterate over 
    # floatingEvents while we remove items from it
    # XXX - This should probably be replaced with a CHANGE_ALL to timezones,
    # applied only to non-Allday masters/non-recurring events.  That ought to be
    # faster and would more reliably handle recurrence issues like bug 10223
    # which were fixed in changeThisAndFuture but not here.  But that doesn't
    # seem like the safest course for 1.0, since the present code is mostly
    # working ---jeffrey
    for item in list(pim_ns.floatingEvents):
        event = EventStamp(item)
        if not sharing_ns.isShared(event):
            with event.noRecurrenceChanges():
                event.startTime = replaceTZ(event.startTime)
            # not all items are actually floating, some will be all day, don't
            # change the timezone for such item's, bug 9622
            if not event.anyTime and not event.allDay:
                if (getattr(event, 'rruleset', False) and
                    not getattr(item, 'inheritFrom', False)):
                    # fix bug 10223, convert EXDATEs from floating
                    event.rruleset.transformDatesAfter(None, replaceTZ)
                for occurrence in event.occurrences or []:
                    ev = EventStamp(occurrence)
                    with ev.noRecurrenceChanges():
                        ev.recurrenceID = replaceTZ(ev.recurrenceID)
                        if ev.startTime.tzinfo == view.tzinfo.floating:
                            ev.startTime = replaceTZ(ev.startTime)
