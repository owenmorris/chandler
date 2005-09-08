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
        displayName="TimeZone info"
    )

    default = schema.One(
        schema.TimeZone,
        displayName = 'User Default Time Zone',
    )

    # List of well-known time zones (for populating drop-downs).
    # [i18n] Since ICU doesn't suitably localize strings like 'US/Pacific',
    # we'll have to provide our own translations.
    wellKnownIDs = schema.Sequence(
        schema.Text,
        displayName = 'List of "well-known" time zones names',
    )
    
    @classmethod
    def get(cls, view = None):
        """Return the default C{TimeZoneInfo} instance, which
           automatically syncs with PyICU's default; i.e.
           if you assign an ICUtzinfo to
           C{TimeZoneInfo.get().default},
           this will be stored as ICU's default time zone.
       """
       
        # Get our parcel's namespace
        namespace = schema.ns(__name__, view)
        
        # Make sure it has a 'default' attribute (alternatively
        # we could make the.update() call below inside installParcel()
        # in __init__.py).
        try:
            result = namespace.defaultInfo
        except AttributeError:
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
                _(u'US/Eastern'),
                _(u'US/Central'),
                _(u'US/Mountain'),
                _(u'US/Pacific'),
                _(u'US/Hawaii'),
                _(u'Europe/London'),
                _(u'Europe/Paris'),
                _(u'Asia/Shanghai'),
                _(u'Asia/Calcutta'),
                _(u'Australia/Sydney'),
            ]
            result = cls.update(namespace.parcel, 'defaultInfo',
                                wellKnownIDs=wellKnownIDs)
                                
    
        return result
        
    def __init__(self, *args, **keywds):
        
        super(TimeZoneInfo, self).__init__(*args, **keywds)
        
        self.default = PyICU.ICUtzinfo.getDefault()
        
    def canonicalTimeZone(self, tzinfo):
        """
        This returns an ICUtzinfo that's equivalent to the passed-in
        tzinfo, to prevent duplicates (like 'PST' and 'US/Pacific'
        from appearing in timezone pickers).
        
        A side-effect is that if a previously unseen tzinfo is
        passed in, it will be added to the receiver's wellKnownIDs
        """
        result = None
        
        if tzinfo is not None:
        
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
        
    def iterTimeZones(self):
        """
        A generator for all the well-known ICUtzinfo objects. Each
        generated value is a tuple of the form (display name, ICUtzinfo),
        where 'display name' is a suitably localized unicode string.
        """
        
        for name in self.wellKnownIDs:
            yield (OSAFMessageFactory(name), PyICU.ICUtzinfo.getInstance(name))
        
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
            tzinfo = self.canonicalTimeZone(self.default)
            if tzinfo is not None:
                PyICU.TimeZone.setDefault(tzinfo.timezone)

def stripTimeZone(dt):
    """
    This method returns a naive C{datetime} (i.e. one with a C{tzinfo}
    of C{None}.
    
    @param dt: The input.
    @type dt: C{datetime}
    
    @return: If the input is naive, just returns dt. Otherwise, converts
        the input into the user's default timezone, and then strips that out.
    """
    
    if dt.tzinfo == None:
        return dt
    else:
        return dt.astimezone(PyICU.ICUtzinfo.getDefault()).replace(tzinfo=None)


def coerceTimeZone(dt, tzinfo):
    """This method returns a C{datetime} with a specified C{tzinfo}.
    
    @param dt: The input.
    @type dt: C{datetime}
    
    @param tzinfo: The target tzinfo (may be None)
    @type tzinfo:  C{tzinfo}
    
    @return: A C{datetime} whose C{tzinfo} field is the same as the target.
    
    If the target tzinfo is C{None}, this returns C{stripTimeZone(dt)}.
    Otherwise, if C{dt} is naive, it's interpreted as being in the user's
    default timezone.
    """
    if tzinfo is None:
        return stripTimeZone(dt)
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=PyICU.ICUtzinfo.getDefault())
        return dt.astimezone(tzinfo)

def formatTime(dt, tzinfo=None):

    def __setTimeZoneInSubformats(msgFormat, tz):
        subformats = msgFormat.getFormats()
        for format in subformats:
                if hasattr(format, "setTimeZone"):
                    format.setTimeZone(tz)

        msgFormat.setFormats(subformats)

    
    if tzinfo is None: tzinfo = PyICU.ICUtzinfo.getDefault()
    
    useSameTimeZoneFormat = True

    if dt.tzinfo is None:
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
