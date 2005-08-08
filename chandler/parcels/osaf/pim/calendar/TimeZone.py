import application.schema as schema

import PyICU
import datetime

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
    #  (2) Elements in the list will be LocalizableStrings
    #  (3) List will probably become a schema.Sequence()
    #
    knownTimeZones = map(
        PyICU.ICUtzinfo.getInstance,
        ["US/Pacific", "US/Mountain", "US/Central", "US/Eastern",
         "Europe/Paris",
         "Africa/Johannesburg" # A long name to show how wide the popup can become
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
            PyICU.TimeZone.adoptDefault(tz.timezone)

    def onValueChanged(self, name):
        # Repository hook for attribute changes.
        if name == 'tzinfo':
            tzinfo = self.tzinfo
            if tzinfo is not None:
                PyICU.TimeZone.adoptDefault(tzinfo.timezone)
            
