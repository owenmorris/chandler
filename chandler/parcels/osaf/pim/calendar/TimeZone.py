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


import application.schema as schema
from osaf import Preferences

import PyICU
import dateutil.tz
import vobject
import itertools

import datetime
from i18n import ChandlerMessageFactory


def reindexFloatingEvents(view):
    """
    When floating timezone changes, floating events need to be reindexed in the
    events collection.
    """
    pim_ns = schema.ns("osaf.pim", view)
    events = pim_ns.EventStamp.getCollection(view)
    
    floatingKeys = list(pim_ns.floatingEvents.iterkeys())
    events.reindexKeys(floatingKeys, 'effectiveStart', 'effectiveEnd')
    
    keys = pim_ns.masterEvents.getIndex('recurrenceEnd')
    
    masterFloatingKeys = [i for i in floatingKeys if i in keys]
    pim_ns.masterEvents.reindexKeys(masterFloatingKeys, 'recurrenceEnd')
                              
    UTCKeys = list(pim_ns.UTCEvents.iterkeys())
    events.reindexKeys(UTCKeys, 'effectiveStartNoTZ', 'effectiveEndNoTZ')
    
    masterUTCKeys = [i for i in UTCKeys if i in keys]
    pim_ns.masterEvents.reindexKeys(masterUTCKeys, 'recurrenceEndNoTZ')

class TimeZoneInfo(schema.Item):
    """
    Item that persists:
     - A schema.TimeZone attribute that synchronizes
       itself with PyICU's default settings.
     - A list of "well-known" timezone names.
    """

    default = schema.One(
        schema.TimeZone,
    )

    @schema.observer(default)
    def onDefaultChanged(self, op, name):
        # Repository hook for attribute changes.
        default = self.default
        canonicalDefault = self.canonicalTimeZone(default)
        # Make sure that PyICU's default timezone is synched with
        # ours
        if (canonicalDefault is not None and
            canonicalDefault is not PyICU.ICUtzinfo.floating):
            PyICU.ICUtzinfo.default = canonicalDefault
            reindexFloatingEvents(self.itsView)
        # This next if is required to avoid an infinite recursion!
        if canonicalDefault is not default:
            self.default = canonicalDefault

    # List of well-known time zones (for populating drop-downs).
    # [i18n] Since ICU doesn't suitably localize strings like 'US/Pacific',
    # we'll have to provide our own translations.
    wellKnownIDs = schema.Sequence(
        schema.Text,
    )

    @classmethod
    def get(cls, view):
        """
        Return the default C{TimeZoneInfo} instance, which
        automatically syncs with PyICU's default; i.e. if you
        assign an ICUtzinfo to C{TimeZoneInfo.get().default},
        this will be stored as ICU's default time zone.
        """

        return schema.ns(__name__, view).defaultInfo

    def __init__(self, *args, **keywds):

        super(TimeZoneInfo, self).__init__(*args, **keywds)

        self.default = PyICU.ICUtzinfo.floating


    def canonicalTimeZone(self, tzinfo):
        """
        This returns an ICUtzinfo that's equivalent to the passed-in
        tzinfo, to prevent duplicates (like 'PST' and 'US/Pacific'
        from appearing in timezone pickers).

        A side-effect is that if a previously unseen tzinfo is
        passed in, it will be added to the receiver's wellKnownIDs.
        """

        if tzinfo is None or tzinfo == PyICU.ICUtzinfo.floating:

            result = PyICU.ICUtzinfo.floating

        else:
            result = None

            if tzinfo.tzid in self.wellKnownIDs:
                result = tzinfo
            else:
                numEquivalents = PyICU.TimeZone.countEquivalentIDs(tzinfo.tzid)

                for index in xrange(numEquivalents):
                    equivName = PyICU.TimeZone.getEquivalentID(tzinfo.tzid, index)

                    if equivName in self.wellKnownIDs:
                        result = PyICU.ICUtzinfo.getInstance(equivName)
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

        floating = PyICU.ICUtzinfo.floating

        for name in self.wellKnownIDs:
            tzinfo = PyICU.ICUtzinfo.getInstance(name)

            if tzinfo != floating:

                yield (ChandlerMessageFactory(name), tzinfo)

        if withFloating:
            yield ChandlerMessageFactory(u"Floating"), floating

    def onItemLoad(self, view):
        # This is overridden to ensure that storing the
        # default timezone in the repository overrides ICU's
        # settings.
        tz = self.default
        if tz is not None and view is not None:
            PyICU.TimeZone.setDefault(tz.timezone)


class TZPrefs(Preferences):
    showUI = schema.One(schema.Boolean, initialValue = False)

    @schema.observer(showUI)
    def onShowUIChanged(self, op, attrName):
        from osaf.pim.calendar.TimeZone import TimeZoneInfo
        timeZoneInfo = TimeZoneInfo.get(self.itsView)

        # Sync up the default timezone (i.e. the one used when
        # creating new events).
        if self.showUI:
            timeZoneInfo.default = PyICU.ICUtzinfo.default
        else:
            timeZoneInfo.default = PyICU.ICUtzinfo.floating

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
    _ = lambda x: x

    wellKnownIDs = [
        _(u'US/Hawaii'),
        _(u'US/Alaska'),
        _(u'US/Pacific'),
        _(u'US/Mountain'),
        _(u'US/Central'),
        _(u'US/Eastern'),
        _(u'World/Floating'),
    ]

    # Set up our parcel's 'defaultInfo' attribute
    TimeZoneInfo.update(namespace.parcel, 'defaultInfo',
                        wellKnownIDs=wellKnownIDs)


def stripTimeZone(dt):
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
        return dt.astimezone(PyICU.ICUtzinfo.default).replace(tzinfo=None)

def forceToDateTime(dt):
    """
    If dt is a datetime, return dt, if a date, add time(0) and return.

    @param dt: The input.
    @type dt: C{datetime} or C{date}

    @return: A C{datetime}
    """
    floating = PyICU.ICUtzinfo.floating
    if type(dt) == datetime.datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=floating)
        else:
            return dt
    elif type(dt) == datetime.date:
        return datetime.datetime.combine(dt, datetime.time(0, tzinfo=floating))

def coerceTimeZone(dt, tzinfo):
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
        return stripTimeZone(dt)
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=PyICU.ICUtzinfo.default)
        return dt.astimezone(tzinfo)


utc = PyICU.ICUtzinfo.getInstance('UTC')
tzid_mapping = {}
dateutil_utc = dateutil.tz.tzutc()

def convertToICUtzinfo(dt, view=None):
    """
    This method returns a C{datetime} whose C{tzinfo} field
    (if any) is an instance of the ICUtzinfo class.
    
    @param dt: The C{datetime} whose C{tzinfo} field we want
               to convert to an ICUtzinfo instance.
    @type dt: C{datetime}
    """
    oldTzinfo = dt.tzinfo
    if isinstance(oldTzinfo, PyICU.ICUtzinfo):
        return dt
    elif oldTzinfo is None:
        icuTzinfo = None # Will patch to floating at the end
    else:
        
        def getICUInstance(name):
            result = None
            if name is not None:
                result = PyICU.ICUtzinfo.getInstance(name)
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
                icuTzinfo = utc
        
        # iterate over all PyICU timezones, return the first one whose
        # offsets and DST transitions match oldTzinfo.  This is painfully
        # inefficient, but we should do it only once per unrecognized timezone,
        # so optimization seems premature.
        
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
        
    # Here, if we have an unknown timezone, we'll turn
    # it into a floating datetime
    if icuTzinfo is None:
        icuTzinfo = PyICU.ICUtzinfo.floating

    dt = dt.replace(tzinfo=icuTzinfo)
        
    return dt

def shortTZ(dt, tzinfo=None):
    """
    Return an empty string or the short timezone string for dt if dt.tzinfo
    doesn't match tzinfo (tzinfo defaults to PyICU.ICUtzinfo.default)

    """
    if tzinfo is None: tzinfo = PyICU.ICUtzinfo.default

    if dt.tzinfo is None or dt.tzinfo is PyICU.ICUtzinfo.floating:
        return u''
    elif dt.tzinfo != tzinfo:
        name = dt.tzinfo.timezone.getDisplayName(dt.dst(),
                                          dt.tzinfo.timezone.SHORT)
        if not name:
            return u''
        else:
            return name
    return u''

def formatTime(dt, tzinfo=None, noTZ=False):

    def __setTimeZoneInSubformats(msgFormat, tz):
        subformats = msgFormat.getFormats()
        for format in subformats:
                if hasattr(format, "setTimeZone"):
                    format.setTimeZone(tz)

        msgFormat.setFormats(subformats)


    if tzinfo is None: tzinfo = PyICU.ICUtzinfo.default

    useSameTimeZoneFormat = True

    if dt.tzinfo is None or dt.tzinfo is PyICU.ICUtzinfo.floating or noTZ:
        dt = dt.replace(tzinfo=tzinfo)
    elif dt.tzinfo != tzinfo:
        useSameTimeZoneFormat = False

    if useSameTimeZoneFormat or noTZ:
        format = PyICU.MessageFormat("{0,time,short}")
        __setTimeZoneInSubformats(format, tzinfo.timezone)
    else:
        # This string should be localizable
        format = PyICU.MessageFormat("{0,time,short} {0,time,z}")
        __setTimeZoneInSubformats(format, dt.tzinfo.timezone)

    formattable = PyICU.Formattable(dt, PyICU.Formattable.kIsDate)

    return unicode(format.format([formattable], PyICU.FieldPosition()))
