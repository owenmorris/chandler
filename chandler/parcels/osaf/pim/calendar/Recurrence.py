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


"""Classes used for recurrence.

@group Main Recurrence Kinds: RecurrenceRule, RecurrenceRuleSet
@group Recurrence Enumerations: FrequencyEnum, WeekdayEnum, WeekdayAndPositionStruct

"""

__parcel__ = "osaf.pim.calendar"

from application import schema
from osaf.pim import items
from datetime import datetime, timedelta
import dateutil.rrule
from dateutil.rrule import rrule, rruleset
from repository.item.PersistentCollections import PersistentList
from PyICU import ICUtzinfo, DateFormat
from TimeZone import coerceTimeZone, forceToDateTime
from i18n import ChandlerMessageFactory as _

class FrequencyEnum(schema.Enumeration):
    """The base frequency for a recurring event."""
    values="yearly","monthly","weekly","daily","hourly","minutely","secondly"


# map FrequencyEnums to internationalized singular and plural strings
singularFrequencyMap = dict(yearly  = _(u"year"),
                            monthly = _(u"month"),
                            weekly  = _(u"week"),
                            daily   = _(u"day"),
                            hourly  = _(u"hour"),
                            minutely = _(u"minute"),
                            secondly = _(u"second"))

pluralFrequencyMap =   dict(yearly  = _(u"years"),
                            monthly = _(u"months"),
                            weekly  = _(u"weeks"),
                            daily   = _(u"days"),
                            hourly  = _(u"hours"),
                            minutely = _(u"minutes"),
                            secondly = _(u"seconds"))


class WeekdayEnum(schema.Enumeration):
    """The names of weekdays.  Values shouldn't be displayed directly."""
    values="monday","tuesday","wednesday","thursday","friday", \
           "saturday","sunday"

# map WeekdayEnums to an internationalized abbreviation for display
weekdayAbbrevMap = dict(monday    = _(u"Mo"),
                        tuesday   = _(u"Tu"),
                        wednesday = _(u"We"),
                        thursday  = _(u"Th"),
                        friday    = _(u"Fr"),
                        saturday  = _(u"Sa"),
                        sunday    = _(u"Su"))


class WeekdayAndPositionStruct(schema.Struct):
    """
    Composition of a WeekdayEnum and an integer selecting first (1), last (-1),
    or n-th occurrence of that weekday in the month.

    selector=0 represents all days in the month equal to the given weekday.

    """
    __slots__ = "weekday", "selector"

def toDateUtilWeekday(enum):
    """
    Convert the English string for a weekday in WeekdayEnum to dateutil's
    special weekday class associated with that day.

    """
    return getattr(dateutil.rrule, enum[0:2].upper())

def toDateUtilFrequency(enum):
    """Return the dateutil constant associated with the given frequency."""
    return getattr(dateutil.rrule, enum.upper())

def toDateUtilStruct(structlist):
    """
    Convert a WeekdayAndPositionStruct to the associated dateutil byweekday
    class.

    """
    outlist = []
    for struct in structlist:
        day=toDateUtilWeekday(struct.weekday)
        if struct.selector == 0: # dateutil's weekday doesn't like 0
            outlist.append(day)
        else:
            outlist.append(day(struct.selector))
    return outlist

def toDateUtil(val):
    """
    Convert a Chandler frequency, weekday, or byweekday selector to the
    associated dateutil value.

    """
    if type(val) == PersistentList: return toDateUtilStruct(val)
    elif val in FrequencyEnum.values: return toDateUtilFrequency(val)
    elif val in WeekdayEnum.values: return toDateUtilWeekday(val)

def fromDateUtilWeekday(val):
    """Convert a dateutil weekday constant to its associated WeekdayEnum."""
    return WeekdayEnum.values[val]

def fromDateUtilFrequency(val):
    """Convert a dateutil frequency constant to its associated FrequencyEnum."""
    return FrequencyEnum.values[val]

class RecurrenceRule(items.ContentItem):
    """One rule defining recurrence for an item."""
    freq = schema.One(
        FrequencyEnum,
        defaultValue="weekly"
    )
    isCount = schema.One(
        schema.Boolean,
        doc = "If True, calculate and export count instead of until",
        defaultValue = False
    )
    until = schema.One(
        schema.DateTimeTZ,
    )
    untilIsDate = schema.One(
        schema.Boolean,
        doc = "If True, treat until as an inclusive date, use until + 23:59 "
              "for until",
        defaultValue = True
    )
    interval = schema.One(
        schema.Integer,
        defaultValue=1
    )
    wkst = schema.One(
        WeekdayEnum,
        defaultValue=None
    )
    bysetpos = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    bymonth = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    bymonthday = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    byyearday = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    byweekno = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    byweekday = schema.Sequence(
         WeekdayAndPositionStruct,
        defaultValue=None
    )
    byhour = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    byminute = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    bysecond = schema.Sequence(
        schema.Integer,
        defaultValue=None
    )
    rruleFor = schema.One('RecurrenceRuleSet', inverse='rrules')
    exruleFor = schema.One('RecurrenceRuleSet', inverse='exrules')

    schema.addClouds(
        sharing = schema.Cloud(freq, isCount, until, untilIsDate, interval,
            wkst, bysetpos, bymonth, bymonthday, byyearday, byweekno,
            byweekday, byhour, byminute, bysecond)
    )

    normalNames = "interval", "until"
    listNames = ("bysetpos", "bymonth", "bymonthday", "byyearday", "byweekno",
                 "byhour", "byminute", "bysecond")
    specialNames = "wkst", "byweekday", "freq"

    notSpecialNames = ("interval", "until", "bysetpos", "bymonth", "bymonthday",
                       "byyearday","byweekno", "byhour", "byminute", "bysecond")

    @schema.observer(
        interval, until, bysetpos, bymonth, bymonthday, byyearday, byweekno,
        byhour, byminute, bysecond, wkst, byweekday, freq
    )
    def onRecurrenceChanged(self, op, name):
        """If the rule changes, update any associated events."""
        for ruletype in ('rruleFor', 'exruleFor'):
            if self.hasLocalAttributeValue(ruletype):
                getattr(self, ruletype).onRuleSetChanged(op, 'rrules')


    # dateutil automatically sets these from dtstart, we don't want these
    # unless their length is greater than 1.
    interpretedNames = "byhour", "byminute", "bysecond"

    def calculatedUntil(self):
        """
        Return until or until + 23:59, depending on untilIsDate.
        Will return None if there's no 'until' (so don't assume you can
        compare this value with a datetime directly!)

        @rtype: C{datetime} or C{None}

        """
        try:
            until = self.until
        except AttributeError:
            return None

        if self.untilIsDate:
            return until.replace(hour=23, minute=59)
        else:
            return until


    def createDateUtilFromRule(self, dtstart, ignoreIsCount=True,
                               convertFloating=False):
        """Return an appropriate dateutil.rrule.rrule.

        @param dtstart: The start time for the recurrence rule
        @type  dtstart: C{datetime}

        @param ignoreIsCount: Whether the isCount flag should be used to convert
                              until endtimes to a count. Converting to count
                              takes extra cycles and is only necessary when
                              the rule is going to be serialized
        @type  ignoreIsCount: C{bool}

        @param convertFloating: Whether or not to allow ICUtzinfo.floating
                                in datetimes of the rruleset. If C{True},
                                naive datetimes are used instead. This is
                                needed for exporting floating events to
                                icalendar format.
        @type  convertFloating: C{bool}

        @rtype: C{dateutil.rrule.rrule}

        """

        tzinfo = dtstart.tzinfo

        def coerceIfDatetime(value):
            if isinstance(value, datetime):
                if convertFloating and value.tzinfo is ICUtzinfo.floating:
                    value = value.replace(tzinfo=None)
                else:
                    value = coerceTimeZone(value, tzinfo)
            return value

        # TODO: more comments
        kwargs = dict((k, getattr(self, k, None)) for k in self.notSpecialNames)
        for key in self.specialNames:
            value = coerceIfDatetime(getattr(self, key))
            if value is not None:
                kwargs[key]=toDateUtil(value)
        if hasattr(self, 'until'):
            kwargs['until'] = coerceIfDatetime(self.calculatedUntil())
        rule = rrule(dtstart=dtstart, **kwargs)
        if ignoreIsCount or not self.isCount or not hasattr(self, 'until'):
            return rule
        else:
            # modifying in place may screw up cache, fix when we turn
            # on caching
            rule._count =  rule.count()
            rule._until = None
            return rule

    def setRuleFromDateUtil(self, rrule):
        """Extract attributes from rrule, set them in self.

        @param rrule: The rule to marshall into Chandler
        @type  rrule: C{dateutil.rrule.rrule}

        """
        self.untilIsDate = False
        until = None # assume no limit
        if rrule._count is not None:
            self.isCount = True
            until = rrule[-1]
        self.wkst = fromDateUtilWeekday(rrule._wkst)
        self.freq = fromDateUtilFrequency(rrule._freq)

        # ignore byweekday if freq is WEEKLY and day correlates with dtstart
        # because it was automatically set by dateutil
        if rrule._freq != dateutil.rrule.WEEKLY or \
           len(rrule._byweekday) != 1 or \
           rrule._dtstart.weekday() != rrule._byweekday[0]:
            listOfDayTuples = []
            if rrule._byweekday:
                # Day tuples are (dayOrdinal, n-th week of the month),
                # 0 means all weeks
                listOfDayTuples=[(day, 0) for day in rrule._byweekday]
            if rrule._bynweekday is not None:
                listOfDayTuples.extend(rrule._bynweekday)
            if len(listOfDayTuples) > 0:
                self.byweekday = []
                for day, n in listOfDayTuples:
                    day = fromDateUtilWeekday(day)
                    self.byweekday.append(WeekdayAndPositionStruct(day, n))
        if rrule._until is not None:
            until = rrule._until
        if rrule._interval != 1:
            self.interval = rrule._interval
        if until is None:
            if self.hasLocalAttributeValue('until'):
                del self.until
        else:
            if until.tzinfo is None:
                self.until = until.replace(tzinfo=ICUtzinfo.floating)
            else:
                self.until = coerceTimeZone(until, ICUtzinfo.default)

        for key in self.listNames:
            # TODO: cache getattr(rrule, '_' + key)
            if getattr(rrule, '_' + key) is not None and \
                                        (key not in self.interpretedNames or \
                                         len(getattr(rrule, '_' + key)) > 1):
                # cast tuples to list
                setattr(self, key, list(getattr(rrule, '_' + key)))
        # bymonthday and bymonth may be set automatically by dateutil, if so,
        # unset them
        if rrule._freq in (dateutil.rrule.MONTHLY, dateutil.rrule.YEARLY):
            if len(rrule._bymonthday) == 1:
                if rrule._bymonthday[0] == rrule._dtstart.day:
                    del self.bymonthday
        if rrule._freq == dateutil.rrule.YEARLY:
            if len(rrule._bymonth) == 1:
                if rrule._bymonth[0] == rrule._dtstart.month:
                    del self.bymonth

    def getPreviousRecurrenceID(self, dtstart, recurrenceID):
        """Return the date of the previous recurrenceID, or None.

        @param dtstart: The start time for the recurrence rule
        @type  dtstart: C{datetime}

        @param recurrenceID: The current recurrenceID
        @type  recurrenceID: C{datetime}

        @rtype: C{datetime} or C{None}
        """
        previous = None
        for dt in self.createDateUtilFromRule(dtstart):
            if dt < recurrenceID:
                previous = dt
            else:
                break
        return previous

    def moveUntilBefore(self, dtstart, recurrenceID):
        """Find the previous recurrenceID, set UNTIL to match it.

        @param dtstart: The start time for the recurrence rule
        @type  dtstart: C{datetime}

        @param recurrenceID: The current recurrenceID
        @type  recurrenceID: C{datetime}

        """
        previous = self.getPreviousRecurrenceID(dtstart, recurrenceID)
        assert previous is not None
        self.until = previous
        self.untilIsDate = False


class RecurrenceRuleSet(items.ContentItem):
    """
    A collection of recurrence and exclusion rules, dates, and exclusion dates.
    """
    rrules = schema.Sequence(
        RecurrenceRule,
        inverse = RecurrenceRule.rruleFor,
        deletePolicy = 'cascade'
    )
    exrules = schema.Sequence(
        RecurrenceRule,
        inverse = RecurrenceRule.exruleFor,
        deletePolicy = 'cascade'
    )
    rdates = schema.Sequence(
        schema.DateTimeTZ,
    )
    exdates = schema.Sequence(
        schema.DateTimeTZ,
    )
    events = schema.Sequence(
        "osaf.pim.calendar.Calendar.CalendarEventMixin",
        inverse="rruleset"
    )

    schema.addClouds(
        copying = schema.Cloud(rrules, exrules, rdates, exdates),
        sharing = schema.Cloud(exdates, rdates, byCloud = [exrules, rrules])
    )

    @schema.observer(rrules, exrules, rdates, exdates)
    def onRuleSetChanged(self, op, name):
        """If the RuleSet changes, update the associated event."""
        if not getattr(self, '_ignoreValueChanges', False):
            if self.hasLocalAttributeValue('events'):
                for event in self.events:
                    event.getFirstInRule().cleanRule()
                    # assume we have only one conceptual event per rrule
                    break

    def addRule(self, rule, rrulesorexrules='rrules'):
        """Add an rrule or exrule, defaults to rrule.

        @param rule: Rule to be added
        @type  rule: L{RecurrenceRule}

        @param rrulesorexrules: Whether the rule is an rrule or exrule
        @type  rrulesorexrules: 'rrules' or 'exrules'

        """
        try:
            getattr(self, rrulesorexrules).append(rule)
        except AttributeError:
            setattr(self, rrulesorexrules, [rule])

    def createDateUtilFromRule(self, dtstart, ignoreIsCount=True,
                               convertFloating=False):
        """Return an appropriate dateutil.rrule.rruleset.

        @param dtstart: The start time for the recurrence rule
        @type  dtstart: C{datetime}

        @param ignoreIsCount: Whether the isCount flag should be used to convert
                              until endtimes to a count. Converting to count
                              takes extra cycles and is only necessary when
                              the rule is going to be serialized
        @type  ignoreIsCount: C{bool}

        @param convertFloating: Whether or not to allow ICUtzinfo.floating
                                in datetimes of the rruleset. If C{True},
                                naive datetimes are used instead. This is
                                needed for exporting floating events to
                                icalendar format.
        @type  convertFloating: C{bool}

        @rtype: C{dateutil.rrule.rruleset}

        """
        ruleset = rruleset()
        for rtype in 'rrule', 'exrule':
            for rule in getattr(self, rtype + 's', []):
                getattr(ruleset, rtype)(rule.createDateUtilFromRule(dtstart, ignoreIsCount, convertFloating))
        for datetype in 'rdate', 'exdate':
            for date in getattr(self, datetype + 's', []):
                if convertFloating and date.tzinfo is ICUtzinfo.floating:
                    date = date.replace(tzinfo=None)
                else:
                    date = coerceTimeZone(date, dtstart.tzinfo)
                getattr(ruleset, datetype)(date)
        return ruleset

    def setRuleFromDateUtil(self, ruleSetOrRule):
        """Extract rules and dates from ruleSetOrRule, set them in self.

        If a dateutil.rrule.rrule is passed in instead of an rruleset, treat
        it as the new rruleset.

        @param ruleSetOrRule: The rule to marshall into Chandler
        @type  ruleSetOrRule: C{dateutil.rrule.rrule} or C{dateutil.rrule.rruleset}

        """
        if isinstance(ruleSetOrRule, rrule):
            set = rruleset()
            set.rrule(ruleSetOrRule)
            ruleSetOrRule = set
        elif not isinstance(ruleSetOrRule, rruleset):
            raise TypeError, "ruleSetOrRule must be an rrule or rruleset"
        for rtype in 'rrule', 'exrule':
            rules = getattr(ruleSetOrRule, '_' + rtype, [])
            if rules is None: rules = []
            itemlist = []
            for rule in rules:
                ruleItem=RecurrenceRule(None, None, None, self.itsView)
                ruleItem.setRuleFromDateUtil(rule)
                itemlist.append(ruleItem)
            setattr(self, rtype + 's', itemlist)
        for typ in 'rdate', 'exdate':
            datetimes = [forceToDateTime(d) for d in getattr(ruleSetOrRule, '_' + typ, [])]
            setattr(self, typ + 's', datetimes)

    def isComplex(self):
        """Determine if the rule is too complex to display a meaningful
        description about it.

        @rtype: C{bool}

        """
        if hasattr(self, 'rrules'):
            if len(self.rrules) != 1:
                return True # multiple rules
            for recurtype in 'exrules', 'rdates':
                if self.hasLocalAttributeValue(recurtype) and \
                       len(getattr(self, recurtype)) != 0:
                    return True # more complicated rules
            rule = self.rrules.first()
            for attr in RecurrenceRule.listNames:
                if getattr(rule, attr) not in (None, []):
                    return True
            if rule.byweekday is not None:
                # treat nth weekday of the month as complex
                for daystruct in rule.byweekday:
                    if daystruct.selector != 0:
                        return True
            return False
        else:
            return True


    def isCustomRule(self):
        """Determine if this is a custom rule.

        For the moment, simple daily, weekly, or monthly repeating events,
        optionally with an UNTIL date, or the abscence of a rule, are the only
        rules which are not custom.

        @rtype: C{bool}

        """
        if self.isComplex():
            return True
        # isComplex has already tested for most custom things, but
        # not intervals greater than 1 and multiple weekdays
        rule = self.rrules.first()
        if not (rule.interval == 1 or (rule.interval == 2 and
                                       rule.freq == 'weekly')):
            return True
        elif rule.byweekday:
            return True
        else:
            return False

    def getCustomDescription(self):
        """Return a string describing custom rules.

        @rtype: C{str}

        """
        if self.isComplex():
            return _(u"complex rule - no description available")
        else:
            rule = self.rrules.first()
            freq = rule.freq
            interval = rule.interval

            #@@@ This would be tricky to internationalize, bug 4464
            dct = {}
            dct['weekdays'] = u""
            if freq == 'weekly' and rule.byweekday is not None:
                daylist = [weekdayAbbrevMap[i.weekday] for i in rule.byweekday]
                if len(daylist) > 0:
                    daylist.append(u" ")
                    dct['weekdays'] = u"".join(daylist)

            if rule.interval != 1:
                dct['interval'] = str(rule.interval)
                dct['freq'] = pluralFrequencyMap[freq]
            else:
                dct['interval'] = u""
                dct['freq'] = singularFrequencyMap[freq]

            until = rule.calculatedUntil()
            if until is None:
                dct['until'] = u""
            else:
                formatter = DateFormat.createDateInstance(DateFormat.kShort)
                dct['until'] = _(u"until ") + unicode(formatter.format(until))

            return "%(weekdays)severy %(interval)s %(freq)s %(until)s" % dct


    def moveDatesAfter(self, after, delta):
        """Move dates (later than "after") in exdates and rdates by delta.

        @param after: Earliest date to move
        @type  after: C{datetime}

        @param delta: Time difference
        @type  delta: C{timedelta}


        """
        self._ignoreValueChanges = True
        for datetype in 'rdates', 'exdates':
            datelist = getattr(self, datetype, None)
            if datelist is not None:
                l = []
                for dt in datelist:
                    if dt >= after:
                        l.append(dt + delta)
                    else:
                        l.append(dt)
                setattr(self, datetype, l)
        del self._ignoreValueChanges

    def removeDates(self, cmpFn, endpoint):
        """Remove dates in exdates and rdates before or after endpoint.

        @param cmpFn: Comparison function (will be called with two
                      C{datetime} objects as arguments).
        @type  cmpFn: callable

        @param endpoint: Start or end point for comparisons
        @type  endpoint: C{datetime}

        """
        for datetype in 'rdates', 'exdates':
            datelist = getattr(self, datetype, None)
            if datelist is not None:
                for i, dt in enumerate(datelist):
                    if cmpFn(dt, endpoint):
                        self._ignoreValueChanges = True
                        del datelist[i]
                        self._ignoreValueChanges = False

    def moveRuleEndBefore(self, dtstart, end):
        """Make self's rules end before end.

        @param dtstart: Start time for the recurrence rule
        @type  dtstart: C{datetime}

        @param end: Date not to include in the rule's new end
        @type  end: C{datetime}

        """
        #change the rule, onRuleSetChanged will trigger cleanRule for master
        for rule in getattr(self, 'rrules', []):
            if (not rule.hasLocalAttributeValue('until') or
               (rule.calculatedUntil() >= end)):
                rule.moveUntilBefore(dtstart, end)
        self.removeDates(datetime.__ge__, end)


