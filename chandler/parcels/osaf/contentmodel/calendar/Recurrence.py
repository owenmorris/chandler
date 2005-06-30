""" Classes used for recurrence"""

__revision__  = "$Revision: 5771 $"
__date__      = "$Date: 2005-06-24 19:13:27 -0700 (Fri, 24 Jun 2005) $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel.calendar"

from application import schema
from osaf.contentmodel import ContentModel
import dateutil.rrule
from dateutil.rrule import rrule, rruleset
from repository.item.PersistentCollections import PersistentList

class FrequencyEnum(schema.Enumeration):
    """The base frequency for a recurring event."""
    schema.kindInfo(
        displayName="Frequency"
    )
    values="yearly","monthly","weekly","daily","hourly","minutely","secondly"


class WeekdayEnum(schema.Enumeration):
    """The names of weekdays."""
    schema.kindInfo(
        displayName="Weekdays"
    )
    values="monday","tuesday","wednesday","thursday","friday","saturday","sunday"

class WeekdayAndPositionStruct(schema.Struct):
    """Weekday and an integer selecting the first, last, etc. day.

    Use selector=0 for all days equal to weekday.

    """
    __slots__ = "weekday", "selector"
    # schema.kindInfo(
#         displayName="Weekday and position"
#     )

def toDateUtilWeekday(enum):
    return getattr(dateutil.rrule, enum[0:2].upper())

def toDateUtilFrequency(enum):
    return getattr(dateutil.rrule, enum.upper())

def toDateUtilStruct(structlist):
    outlist = []
    for struct in structlist:
        day=toDateUtilWeekday(struct.weekday)
        outlist.append(day(struct.selector))
    return outlist

def toDateUtil(val):
    #what's the proper way to dispatch, particularly for the struct?
    if type(val) == PersistentList: return toDateUtilStruct(val)
    elif val in FrequencyEnum.values: return toDateUtilFrequency(val)
    elif val in WeekdayEnum.values: return toDateUtilWeekday(val)

def fromDateUtilWeekday(val):
    #hack!
    return WeekdayEnum.values[val]

def fromDateUtilFrequency(val):
    #hack!
    return FrequencyEnum.values[val]

class RecurrenceRuleSet(ContentModel.ContentItem):
    pass

class RecurrenceRule(ContentModel.ContentItem):
    """One rule defining recurrence for an item."""
    freq = schema.One(
        FrequencyEnum,
        displayName="Frequency possibilities",
        defaultValue="weekly"
    )
    isCount = schema.One(
        schema.Boolean,
        displayName = "isCount",
        doc = "If True, calculate and export count instead of until"
    )
    until = schema.One(
        schema.DateTime,
        displayName="Until",
        defaultValue=None
    )
    interval = schema.One(
        schema.Integer,
        displayName="Interval",
        defaultValue=1
    )
    wkst = schema.One(
        WeekdayEnum,
        displayName="Week Start Day",
        defaultValue=None
    )
    bysetpos = schema.Sequence(
        schema.Integer,
        displayName="Position selector",
        defaultValue=None
    )
    bymonth = schema.Sequence(
        schema.Integer,
        displayName="Month selector",
        defaultValue=None
    )
    bymonthday = schema.Sequence(
        schema.Integer,
        displayName="Ordinal day of month selector",
        defaultValue=None
    )
    byyearday = schema.Sequence(
        schema.Integer,
        displayName="Ordinal day of year selector",
        defaultValue=None
    )
    byweekno = schema.Sequence(
        schema.Integer,
        displayName="Week number selector",
        defaultValue=None
    )
    byweekday = schema.Sequence(
         WeekdayAndPositionStruct,
         displayName="Weekday selector",
        defaultValue=None
    )
    byhour = schema.Sequence(
        schema.Integer,
        displayName="Hour selector",
        defaultValue=None
    )
    byminute = schema.Sequence(
        schema.Integer,
        displayName="Minute selector",
        defaultValue=None
    )
    bysecond = schema.Sequence(
        schema.Integer,
        displayName="Second selector",
        defaultValue=None
    )

    normalNames = "interval", "until", "bysetpos", "bymonth", "bymonthday", "byyearday", "byweekno", "byhour", "byminute", "bysecond"

    specialNames = "wkst", "byweekday", "freq"

    def createDateUtilFromRule(self, dtstart):
        """Return an appropriate dateutil.rrule.rrule."""
        kwargs = dict((k, getattr(self, k)) for k in self.normalNames if getattr(self, k) is not None)
        for key in self.specialNames:
            if getattr(self, key) is not None:
                kwargs[key]=toDateUtil(getattr(self, key))
        return rrule(dtstart=dtstart, **kwargs)

    def setRuleFromDateUtil(self, rrule):
        """Extract attributes from rrule, set them in self."""
        if rrule._count is not None:
            self.isCount = True
            self.until = rrule[-1]
        self.wkst = fromDateUtilWeekday(rrule._wkst)
        self.freq = fromDateUtilFrequency(rrule._freq)
        
        temp = []
        if rrule._byweekday:
            temp=[(day, 0) for day in rrule._byweekday]
        if rrule._bynweekday:
            temp.extend(tup for tup in rrule._bynweekday)
        if len(temp) > 0: self.byweekday = []
        for day, n in temp:
            day = fromDateUtilWeekday(day)
            self.byweekday.append(WeekdayAndPositionStruct(day, n))
        for key in self.normalNames:
            if getattr(rrule, '_' + key) is not None:
                setattr(self, key, getattr(rrule, '_' + key))

