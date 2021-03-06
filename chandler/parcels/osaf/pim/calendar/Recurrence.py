#   Copyright (c) 2003-2008 Open Source Applications Foundation
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
from datetime import datetime
import dateutil.rrule
from dateutil.rrule import rrule, rruleset
from chandlerdb.item.PersistentCollections import PersistentList
from PyICU import DateFormat, DateFormatSymbols, Calendar
from TimeZone import coerceTimeZone, forceToDateTime
from i18n import ChandlerMessageFactory as _

class FrequencyEnum(schema.Enumeration):
    """The base frequency for a recurring event."""
    values="yearly","monthly","weekly","daily","hourly","minutely","secondly"

SHORT_FREQUENCIES = ("hourly", "minutely", "secondly")

# map FrequencyEnums to internationalized singular, plural and adverbial strings
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

adverbFrequencyMap = dict(yearly  = _(u"Yearly"),
                            monthly = _(u"Monthly"),
                            weekly  = _(u"Weekly"),
                            daily   = _(u"Daily"),
                            hourly  = _(u"Hourly"),
                            minutely = _(u"Minutely"),
                            secondly = _(u"Secondly"))

# Formatting strings dictionary: the code builds an index dynamically to pick the right one
descriptionFormat = {
                    # This entry does not require localization.
                    'fs' : u"%(frequencyadverb)s",

                    # L10N: %(frequencyplural)s can have
                    #       the following values:
                    #     1. years
                    #     2. months
                    #     3. weeks
                    #     4. days
                    #     5. hours
                    #     6. minutes
                    #     7. seconds
                    # %(interval)s will evaluate to an empty string or
                    # a number. As in 'every 2 weeks'.
                    'fp' : _(u"Every %(interval)s %(frequencyplural)s"),
                    # L10N: %(frequencyadverb)s can have
                    #       the following values:
                    #     1. Yearly
                    #     2. Monthly
                    #     3. Weekly
                    #     4. Daily
                    #     5. Hourly
                    #     6. Minutely
                    #     7. Secondly
                    'fxs' : _(u"Too frequent: %(frequencyadverb)s"),
                    # L10N: %(frequencyplural)s can have
                    #       the following values:
                    #     1. years
                    #     2. months
                    #     3. weeks
                    #     4. days
                    #     5. hours
                    #     6. minutes
                    #     7. seconds
                    # %(interval)s will evaluate to an empty string or
                    # a number. As in 'every 2 weeks'.
                    'fxp' : _(u"Too frequent: Every %(interval)s %(frequencyplural)s"),
                    # L10N: %(frequencysingular)s can have
                    #       the following values:
                    #     1. year
                    #     2. month
                    #     3. week
                    #     4. day
                    #     5. hour
                    #     6. minute
                    #     7. second
                    # %(days) evaluates to the short version of day names (Mon, Tue, Wed, etc)
                    'fds' : _(u"%(days)s every %(frequencysingular)s"),
                    # L10N: %(frequencyplural)s can have
                    #       the following values:
                    #     1. years
                    #     2. months
                    #     3. weeks
                    #     4. days
                    #     5. hours
                    #     6. minutes
                    #     7. seconds
                    # %(interval)s will evaluate to an empty string or
                    # a number. As in 'every 2 weeks'.
                    # %(days) evaluates to the short version of day names (Mon, Tue, Wed, etc)
                    'fdp' : _(u"%(days)s every %(interval)s %(frequencyplural)s"),
                    # L10N: The %(frequencyadverb)s can have
                    #       the following values:
                    #     1. Yearly
                    #     2. Monthly
                    #     3. Weekly
                    #     4. Daily
                    #     5. Hourly
                    #     6. Minutely
                    #     7. Secondly
                    'fus' : _(u"%(frequencyadverb)s until %(date)s"),
                    # L10N: %(frequencyplural)s can have
                    #       the following values:
                    #     1. years
                    #     2. months
                    #     3. weeks
                    #     4. days
                    #     5. hours
                    #     6. minutes
                    #     7. seconds
                    # %(interval)s will evaluate to an empty string or
                    # a number. As in 'every 2 weeks'.
                    'fup' : _(u"Every %(interval)s %(frequencyplural)s until %(date)s"),
                    # L10N: %(frequencysingular)s can have
                    #       the following values:
                    #     1. year
                    #     2. month
                    #     3. week
                    #     4. day
                    #     5. hour
                    #     6. minute
                    #     7. second
                    # %(days) evaluates to the short version of day names (Mon, Tue, Wed, etc)
                    'fdus' : _(u"%(days)s every %(frequencysingular)s until %(date)s"),
                    # L10N: %(frequencyplural)s can have
                    #       the following values:
                    #     1. years
                    #     2. months
                    #     3. weeks
                    #     4. days
                    #     5. hours
                    #     6. minutes
                    #     7. seconds
                    # %(interval)s will evaluate to an empty string or
                    # a number. As in 'every 2 weeks'.
                    # %(days) evaluates to the short version of day names (Mon, Tue, Wed, etc)
                    'fdup' : _(u"%(days)s every %(interval)s %(frequencyplural)s until %(date)s")}


class WeekdayEnum(schema.Enumeration):
    """The names of weekdays.  Values shouldn't be displayed directly."""
    values="monday","tuesday","wednesday","thursday","friday", \
           "saturday","sunday"

# map WeekdayEnums to an internationalized abbreviation for display
# [i18n] : use the week days returned by PyICU
shortWeekdays = DateFormatSymbols().getShortWeekdays()
weekdayAbbrevMap = dict(monday    = shortWeekdays[Calendar.MONDAY],
                        tuesday   = shortWeekdays[Calendar.TUESDAY],
                        wednesday = shortWeekdays[Calendar.WEDNESDAY],
                        thursday  = shortWeekdays[Calendar.THURSDAY],
                        friday    = shortWeekdays[Calendar.FRIDAY],
                        saturday  = shortWeekdays[Calendar.SATURDAY],
                        sunday    = shortWeekdays[Calendar.SUNDAY])


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
    rruleFor = schema.One() # inverse of RecurrenceRuleSet.rruleset
    exruleFor = schema.One()  # inverse of RecurrenceRuleSet.exrules

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [freq, isCount, until, untilIsDate, interval,
                       wkst, bysetpos, bymonth, bymonthday, byyearday, byweekno,
                       byweekday, byhour, byminute, bysecond]
        )
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

    WEEKDAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')

    def isWeekdayRule(self):
        if (self.freq == 'weekly' and
            self.interval == 1 and
            len(self.byweekday or []) == len(self.WEEKDAYS) and
            set(self.WEEKDAYS) == set(x.weekday for x in self.byweekday
                                         if x.selector == 0)):
            return True

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

        @param convertFloating: Whether or not to allow view.tzinfo.floating
                                in datetimes of the rruleset. If C{True},
                                naive datetimes are used instead. This is
                                needed for exporting floating events to
                                icalendar format.
        @type  convertFloating: C{bool}

        @rtype: C{dateutil.rrule.rrule}

        """

        tzinfo = dtstart.tzinfo
        view = self.itsView

        def coerceIfDatetime(value):
            if isinstance(value, datetime):
                if convertFloating and tzinfo == view.tzinfo.floating:
                    value = coerceTimeZone(view, value, tzinfo).replace(tzinfo=None)
                else:
                    value = coerceTimeZone(view, value, tzinfo)
            return value

        # TODO: more comments
        kwargs = dict((k, getattr(self, k, None)) for k in self.notSpecialNames)
        for key in self.specialNames:
            value = coerceIfDatetime(getattr(self, key))
            if value is not None:
                kwargs[key]=toDateUtil(value)
        if hasattr(self, 'until'):
            kwargs['until'] = coerceIfDatetime(self.calculatedUntil())
        rule = rrule(dtstart=coerceIfDatetime(dtstart), **kwargs)
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
        view = self.itsView
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
           len(rrule._byweekday or ()) != 1 or \
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
                self.until = until.replace(tzinfo=view.tzinfo.floating)
            else:
                self.until = coerceTimeZone(view, until, view.tzinfo.default)

        for key in self.listNames:
            # TODO: cache getattr(rrule, '_' + key)
            value = getattr(rrule, '_' + key)
            if key == 'bymonthday':
                if value is not None:
                    value += (rrule._bynmonthday or ())
            if value is not None and \
               (key not in self.interpretedNames or \
               len(value) > 1):
                # cast tuples to list
                setattr(self, key, list(value))
        # bymonthday and bymonth may be set automatically by dateutil, if so,
        # unset them
        if rrule._freq in (dateutil.rrule.MONTHLY, dateutil.rrule.YEARLY):
            if len(rrule._bymonthday) == 1 and len(rrule._bynmonthday) == 0:
                if rrule._bymonthday[0] == rrule._dtstart.day:
                    del self.bymonthday
        if rrule._freq == dateutil.rrule.YEARLY:
            if len(rrule._bymonth or ()) == 1 and \
                   rrule._byweekday is None and \
                   len(rrule._bynweekday or ()) == 0:
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
        return self.createDateUtilFromRule(dtstart).before(recurrenceID)

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
    ) # inverse of EventStamp.rruleset

    schema.addClouds(
        copying = schema.Cloud(rrules, exrules, rdates, exdates),
        sharing = schema.Cloud(
            literal = [exdates, rdates],
            byCloud = [exrules, rrules]
        )
    )

    @schema.observer(rrules, exrules, rdates, exdates)
    def onRuleSetChanged(self, op, name):
        """If the RuleSet changes, update the associated event."""
        if not getattr(self, '_ignoreValueChanges', False):
            if self.hasLocalAttributeValue('events'):
                pimNs = schema.ns("osaf.pim", self.itsView)
                for eventItem in self.events:
                    pimNs.EventStamp(eventItem).getFirstInRule().cleanRule()
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

    def createDateUtilFromRule(self, dtstart,
                               ignoreIsCount=True,
                               convertFloating=False,
                               ignoreShortFrequency=True):
        """Return an appropriate dateutil.rrule.rruleset.

        @param dtstart: The start time for the recurrence rule
        @type  dtstart: C{datetime}

        @param ignoreIsCount: Whether the isCount flag should be used to convert
                              until endtimes to a count. Converting to count
                              takes extra cycles and is only necessary when
                              the rule is going to be serialized
        @type  ignoreIsCount: C{bool}

        @param convertFloating: Whether or not to allow view.tzinfo.floating
                                in datetimes of the rruleset. If C{True},
                                naive datetimes are used instead. This is
                                needed for exporting floating events to
                                icalendar format.
        @type  convertFloating: C{bool}

        @param ignoreShortFrequency: If ignoreShortFrequency is True, replace
                                     hourly or more frequent rules with a single
                                     RDATE matching dtstart, so as to avoid 
                                     wasting millions of cycles on nonsensical
                                     recurrence rules.
        @type  ignoreShortFrequency: C{bool}

        @rtype: C{dateutil.rrule.rruleset}

        """
        view = self.itsView
        args = (ignoreIsCount, convertFloating)
        ruleset = rruleset()
        for rtype in 'rrule', 'exrule':
            for rule in getattr(self, rtype + 's', []):
                if ignoreShortFrequency and rule.freq in SHORT_FREQUENCIES:
                    # too-frequent rule, as Admiral Ackbar said, "IT'S A TRAP!"
                    ruleset.rdate(dtstart)
                    return ruleset
                rule_adder = getattr(ruleset, rtype)
                rule_adder(rule.createDateUtilFromRule(dtstart, *args))
        
        for datetype in 'rdate', 'exdate':
            for date in getattr(self, datetype + 's', []):
                if convertFloating and date.tzinfo == view.tzinfo.floating:
                    date = date.replace(tzinfo=None)
                else:
                    date = coerceTimeZone(view, date, dtstart.tzinfo)
                getattr(ruleset, datetype)(date)
        
        if (ignoreIsCount and 
            not getattr(self, 'rrules', []) and 
            getattr(self, 'rdates', [])):
            # no rrule, but there are RDATEs, create an RDATE for dtstart, or it
            # won't appear to be part of the rule
            ruleset.rdate(dtstart)
        
        return ruleset

    def setRuleFromDateUtil(self, ruleSetOrRule):
        """Extract rules and dates from ruleSetOrRule, set them in self.

        If a dateutil.rrule.rrule is passed in instead of an rruleset, treat
        it as the new rruleset.

        @param ruleSetOrRule: The rule to marshall into Chandler
        @type  ruleSetOrRule: C{dateutil.rrule.rrule} or C{dateutil.rrule.rruleset}

        """
        ignoreChanges = getattr(self, '_ignoreValueChanges', False)
        self._ignoreValueChanges = True
        try:
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
                datetimes = [forceToDateTime(self.itsView, d)
                             for d in getattr(ruleSetOrRule, '_' + typ, [])]
                setattr(self, typ + 's', datetimes)
        finally:
            self._ignoreValueChanges = ignoreChanges
        # only one rule cleaning is useful when setting a new rule
        self.onRuleSetChanged(None, None)

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
        elif rule.isWeekdayRule():
            return False
        elif rule.byweekday:
            return True
        else:
            return False

    def getCustomDescription(self):
        """Return a string describing custom rules.

        @rtype: C{str}

        """
        too_frequent = False
        if hasattr(self, 'rrules') and len(self.rrules) > 0:
            for rule in self.rrules:
                if rule.freq in SHORT_FREQUENCIES:
                    too_frequent = True
                    break
        
        if self.isComplex():
            if not too_frequent:
                return _(u"No description.")
            else:
                return _(u"Too frequent.")
        else:
            # Get the rule values we can interpret (so far...)
            rule = self.rrules.first()
            freq = rule.freq
            interval = rule.interval
            until = rule.calculatedUntil()
            days = rule.byweekday
            
            # Build the index and argument dictionary
            # The index must be built in the 'fxdus' order
            index = 'f'
            dct = {}
            
            if too_frequent:
                index += 'x'
            
            elif freq == 'weekly' and days is not None:
                index += 'd'
                daylist = [weekdayAbbrevMap[i.weekday] for i in days]
                dct['days'] = u" ".join(daylist)

            dct['frequencyplural'] = pluralFrequencyMap[freq]
            dct['frequencysingular'] = singularFrequencyMap[freq]
            dct['frequencyadverb'] = adverbFrequencyMap[freq]

            if not too_frequent and until is not None:
                index += 'u'
                formatter = DateFormat.createDateInstance(DateFormat.kShort)
                dct['date'] = unicode(formatter.format(until))
            
            if interval != 1:
                dct['interval'] = str(interval)
                index += 'p'
            else:
                index += 's'

            return descriptionFormat[index] % dct


    def transformDatesAfter(self, after, changeDate):
        """
        Transform dates (later than "after") in exdates, rdates and
        until, by applying the function C{changeDate}.

        @param after: Earliest date to move, or None for all occurrences
        @type  after: C{datetime} or None

        @param changeDate: Time difference
        @type  changeDate: C{callable}, taking a C{datetime} and
                           returning a C{datetime}


        """
        self._ignoreValueChanges = True
        for datetype in 'rdates', 'exdates':
            datelist = getattr(self, datetype, None)
            if datelist is not None:
                l = []
                for dt in datelist:
                    if after is None or dt >= after:
                        l.append(changeDate(dt))
                    else:
                        l.append(dt)
                setattr(self, datetype, l)
                
        for rule in self.rrules or []:
            if not rule.untilIsDate:
                try:
                    until = rule.until
                except AttributeError:
                    pass
                else:
                    if after is None or until >= after:
                        rule.until = changeDate(until)
                
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
                # need to start from the end, bug 11005
                for i in reversed(xrange(len(datelist))):
                    if cmpFn(datelist[i], endpoint):
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


