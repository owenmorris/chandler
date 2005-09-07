import application.schema as schema

import PyICU
import datetime
from i18n import OSAFMessageFactory as _

class DefaultTimeZone(schema.Item):
    """
    Item that stores for a schema.TimeZone attribute that synchronizes
    itself with PyICU's default settings.
    """
    
    schema.kindInfo(
        displayName="TimeZone info"
    )

    tzinfo = schema.One(
        schema.TimeZone,
        displayName = 'Time Zone',
    )

    # List of known time zones (for populating drop-downs).
    # Future expansions:
    #
    #  (1) List will become larger (not quite 400 or so)
    #  (2) Elements in the list will be Text
    #  (3) List will probably become a schema.Sequence()
    #
    # XXX: [i18n] Are these names translated in ICU or do we need to do this manually?
    knownTimeZones = map(
        PyICU.ICUtzinfo.getInstance,
        [_("US/Pacific"), _("US/Mountain"), _("US/Central"), _("US/Eastern"),
         _("Europe/Paris"),
         _("Africa/Johannesburg") # A long name to show how wide the popup can become
        ])
    
    
    @classmethod
    def get(cls, view = None):
        """Return the default C{DefaultTimeZoneItem} instance, which
           automatically syncs with PyICU's default; i.e.
           if you assign an ICUtzinfo to
           C{DefaultTimeZoneItem.get().tzinfo},
           this will be stored as ICU's default time zone.
       """
       
        # Get our parcel's namespace
        namespace = schema.ns(__name__, view)
        
        # Make sure it has a 'default' attribute (alternatively
        # we could make the.update() call below inside installParcel()
        # in __init__.py).
        try:
            result = namespace.default
        except AttributeError:
            cls.update(namespace.parcel, 'default')
            result = namespace.default
    
        return result
        
    def __init__(self, *args, **keywds):
        super(DefaultTimeZone, self).__init__(*args, **keywds)
        
        self.tzinfo = PyICU.ICUtzinfo.getDefault()
        
    def onItemLoad(self, view):
        # This is overridden to ensure that storing the
        # default timezone in the repository overrides ICU's
        # settings.
        tz = self.tzinfo
        if tz is not None and view is not None:
            PyICU.TimeZone.setDefault(tz.timezone)

    def onValueChanged(self, name):
        # Repository hook for attribute changes.
        if name == 'tzinfo':
            tzinfo = self.tzinfo
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
