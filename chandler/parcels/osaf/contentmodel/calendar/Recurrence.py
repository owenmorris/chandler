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
        if struct.selector == 0: # dateutil's weekday doesn't like 0
            outlist.append(day)
        else:
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
        doc = "If True, calculate and export count instead of until",
        defaultValue = False
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
    rruleFor = schema.One('RecurrenceRuleSet', inverse='rrules')
    exruleFor = schema.One('RecurrenceRuleSet', inverse='exrules')
        

    normalNames = "interval", "until"
    listNames = "bysetpos", "bymonth", "bymonthday", "byyearday", "byweekno",\
                "byhour", "byminute", "bysecond"

    specialNames = "wkst", "byweekday", "freq"

    def createDateUtilFromRule(self, dtstart):
        """Return an appropriate dateutil.rrule.rrule."""
        kwargs = dict((k, getattr(self, k)) for k in 
                                            self.listNames + self.normalNames)
        for key in self.specialNames:
            if getattr(self, key) is not None:
                kwargs[key]=toDateUtil(getattr(self, key))
        rule = rrule(dtstart=dtstart, **kwargs)
        if not self.isCount or self.until is None:
            return rule
        else:
            # modifying in place may screw up cache, fix when we turn
            # on caching
            rule._count =  rule.count()
            rule._until = None
            return rule       

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
        for key in self.listNames:
            if getattr(rrule, '_' + key) is not None:
                # cast tuples to list, or will the repository do this for us?
                setattr(self, key, list(getattr(rrule, '_' + key)))

class RecurrenceRuleSet(ContentModel.ContentItem):
    rrules = schema.Sequence(
        RecurrenceRule,
        displayName="Recurrence rules",
        inverse = RecurrenceRule.rruleFor
    )
    exrules = schema.Sequence(
        RecurrenceRule,
        displayName="Exclusion rules",
        inverse = RecurrenceRule.exruleFor
    )
    rdates = schema.Sequence(
        schema.DateTime,
        displayName="Recurrence Dates"
    )
    exdates = schema.Sequence(
        schema.DateTime,
        displayName="Exclusion Dates"
    )
    events = schema.Sequence(
        "osaf.contentmodel.calendar.Calendar.CalendarEventMixin",
        displayName="Events",
        inverse="rruleset"
    )
    
    def addRule(self, rule, rruleorexrule='rrule'):
        """Add an rrule or exrule, defaults to rrule."""
        rulelist = getattr(self, rruleorexrule + 's', [])
        rulelist.append(rule)
        setattr(self, rruleorexrule + 's', rulelist)
        
    def createDateUtilFromRule(self, dtstart):
        """Return an appropriate dateutil.rrule.rruleset."""
        ruleset = rruleset()
        for rtype in 'rrule', 'exrule':
            for rule in getattr(self, rtype + 's', []):
                getattr(ruleset, rtype)(rule.createDateUtilFromRule(dtstart))
        for datetype in 'rdate', 'exdate':
            for date in getattr(self, datetype + 's', []):
                getattr(ruleset, datetype)(date)
        return ruleset

    def setRuleFromDateUtil(self, rruleset):
        """Extract rules and dates from rruleset, set them in self."""
        for rtype in 'rrule', 'exrule':
            rules = getattr(rruleset, '_' + rtype, [])
            if rules is None: rules = []
            itemlist = []
            for rule in rules:
                ruleItem=RecurrenceRule(parent=self)
                ruleItem.setRuleFromDateUtil(rule)
                itemlist.append(ruleItem)
            setattr(self, rtype + 's', itemlist)
        for datetype in 'rdate', 'exdate':
            setattr(self, datetype + 's', getattr(rruleset, '_' + datetype, []))

        
