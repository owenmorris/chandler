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

import PyICU
import datetime
from i18n import OSAFMessageFactory

class TimeZoneInfo(schema.Item):
    """
    Item that persists:
     - A schema.TimeZone attribute that synchronizes
       itself with PyICU's default settings.
     - A list of "well-known" timezone names.
    """

    schema.kindInfo(
        displayName=u"TimeZone info"
    )

    default = schema.One(
        schema.TimeZone,
        displayName = u'User Default Time Zone',
    )

    # List of well-known time zones (for populating drop-downs).
    # [i18n] Since ICU doesn't suitably localize strings like 'US/Pacific',
    # we'll have to provide our own translations.
    wellKnownIDs = schema.Sequence(
        schema.Text,
        displayName = u'List of "well-known" time zones names',
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

                yield (OSAFMessageFactory(name), tzinfo)

        if withFloating:
            yield OSAFMessageFactory(u"Floating"), floating

    def onItemLoad(self, view):
        # This is overridden to ensure that storing the
        # default timezone in the repository overrides ICU's
        # settings.
        tz = self.default
        if tz is not None and view is not None:
            PyICU.TimeZone.setDefault(tz.timezone)

    def onValueChanged(self, name):
        # Repository hook for attribute changes.
        if name == 'default':
            default = self.default
            canonicalDefault = self.canonicalTimeZone(default)
            # Make sure that PyICU's default timezone is synched with
            # ours
            if (canonicalDefault is not None and
                canonicalDefault is not PyICU.ICUtzinfo.floating):
                PyICU.ICUtzinfo.default = canonicalDefault
            # This next if is required to avoid an infinite recursion!
            if canonicalDefault is not default:
                self.default = canonicalDefault
                
def installParcel(parcel, oldVersion = None):
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

def formatTime(dt, tzinfo=None):

    def __setTimeZoneInSubformats(msgFormat, tz):
        subformats = msgFormat.getFormats()
        for format in subformats:
                if hasattr(format, "setTimeZone"):
                    format.setTimeZone(tz)

        msgFormat.setFormats(subformats)

    
    if tzinfo is None: tzinfo = PyICU.ICUtzinfo.default
    
    useSameTimeZoneFormat = True

    if dt.tzinfo is None or dt.tzinfo is PyICU.ICUtzinfo.floating:
        dt = dt.replace(tzinfo=tzinfo)
    elif dt.tzinfo != tzinfo:
        useSameTimeZoneFormat = False
        
    if useSameTimeZoneFormat:
        format = PyICU.MessageFormat("{0,time,short}")
        __setTimeZoneInSubformats(format, tzinfo.timezone)
    else:
        # This string should be localizable
        format = PyICU.MessageFormat("{0,time,short} {0,time,z}")
        __setTimeZoneInSubformats(format, dt.tzinfo.timezone)
        
    formattable = PyICU.Formattable(dt, PyICU.Formattable.kIsDate)

    return unicode(format.format([formattable], PyICU.FieldPosition()))
