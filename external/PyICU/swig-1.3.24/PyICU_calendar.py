# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_calendar

def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "this"):
        if isinstance(value, class_type):
            self.__dict__[name] = value.this
            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
            del value.thisown
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static) or hasattr(self,name) or (name == "thisown"):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0
del types


def _swig_setattr_nondynamic_method(set):
    def set_attr(self,name,value):
        if hasattr(self,name) or (name in ("this", "thisown")):
            set(self,name,value)
        else:
            raise AttributeError("You cannot add attributes to %s" % self)
    return set_attr


import PyICU_bases
import PyICU_iterators
import PyICU_locale
UCAL_ERA = _PyICU_calendar.UCAL_ERA
UCAL_YEAR = _PyICU_calendar.UCAL_YEAR
UCAL_MONTH = _PyICU_calendar.UCAL_MONTH
UCAL_WEEK_OF_YEAR = _PyICU_calendar.UCAL_WEEK_OF_YEAR
UCAL_WEEK_OF_MONTH = _PyICU_calendar.UCAL_WEEK_OF_MONTH
UCAL_DATE = _PyICU_calendar.UCAL_DATE
UCAL_DAY_OF_YEAR = _PyICU_calendar.UCAL_DAY_OF_YEAR
UCAL_DAY_OF_WEEK = _PyICU_calendar.UCAL_DAY_OF_WEEK
UCAL_DAY_OF_WEEK_IN_MONTH = _PyICU_calendar.UCAL_DAY_OF_WEEK_IN_MONTH
UCAL_AM_PM = _PyICU_calendar.UCAL_AM_PM
UCAL_HOUR = _PyICU_calendar.UCAL_HOUR
UCAL_HOUR_OF_DAY = _PyICU_calendar.UCAL_HOUR_OF_DAY
UCAL_MINUTE = _PyICU_calendar.UCAL_MINUTE
UCAL_SECOND = _PyICU_calendar.UCAL_SECOND
UCAL_MILLISECOND = _PyICU_calendar.UCAL_MILLISECOND
UCAL_ZONE_OFFSET = _PyICU_calendar.UCAL_ZONE_OFFSET
UCAL_DST_OFFSET = _PyICU_calendar.UCAL_DST_OFFSET
UCAL_YEAR_WOY = _PyICU_calendar.UCAL_YEAR_WOY
UCAL_DOW_LOCAL = _PyICU_calendar.UCAL_DOW_LOCAL
UCAL_EXTENDED_YEAR = _PyICU_calendar.UCAL_EXTENDED_YEAR
UCAL_JULIAN_DAY = _PyICU_calendar.UCAL_JULIAN_DAY
UCAL_MILLISECONDS_IN_DAY = _PyICU_calendar.UCAL_MILLISECONDS_IN_DAY
UCAL_DAY_OF_MONTH = _PyICU_calendar.UCAL_DAY_OF_MONTH
UCAL_SUNDAY = _PyICU_calendar.UCAL_SUNDAY
UCAL_MONDAY = _PyICU_calendar.UCAL_MONDAY
UCAL_TUESDAY = _PyICU_calendar.UCAL_TUESDAY
UCAL_WEDNESDAY = _PyICU_calendar.UCAL_WEDNESDAY
UCAL_THURSDAY = _PyICU_calendar.UCAL_THURSDAY
UCAL_FRIDAY = _PyICU_calendar.UCAL_FRIDAY
UCAL_SATURDAY = _PyICU_calendar.UCAL_SATURDAY
UCAL_JANUARY = _PyICU_calendar.UCAL_JANUARY
UCAL_FEBRUARY = _PyICU_calendar.UCAL_FEBRUARY
UCAL_MARCH = _PyICU_calendar.UCAL_MARCH
UCAL_APRIL = _PyICU_calendar.UCAL_APRIL
UCAL_MAY = _PyICU_calendar.UCAL_MAY
UCAL_JUNE = _PyICU_calendar.UCAL_JUNE
UCAL_JULY = _PyICU_calendar.UCAL_JULY
UCAL_AUGUST = _PyICU_calendar.UCAL_AUGUST
UCAL_SEPTEMBER = _PyICU_calendar.UCAL_SEPTEMBER
UCAL_OCTOBER = _PyICU_calendar.UCAL_OCTOBER
UCAL_NOVEMBER = _PyICU_calendar.UCAL_NOVEMBER
UCAL_DECEMBER = _PyICU_calendar.UCAL_DECEMBER
UCAL_UNDECIMBER = _PyICU_calendar.UCAL_UNDECIMBER
UCAL_AM = _PyICU_calendar.UCAL_AM
UCAL_PM = _PyICU_calendar.UCAL_PM
class TimeZone(PyICU_bases.UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    SHORT = _PyICU_calendar.TimeZone_SHORT
    LONG = _PyICU_calendar.TimeZone_LONG
    def __eq__(*args): return _PyICU_calendar.TimeZone___eq__(*args)
    def __ne__(*args): return _PyICU_calendar.TimeZone___ne__(*args)
    def setRawOffset(*args): return _PyICU_calendar.TimeZone_setRawOffset(*args)
    def getRawOffset(*args): return _PyICU_calendar.TimeZone_getRawOffset(*args)
    def getID(*args): return _PyICU_calendar.TimeZone_getID(*args)
    def setID(*args): return _PyICU_calendar.TimeZone_setID(*args)
    def getDisplayName(*args): return _PyICU_calendar.TimeZone_getDisplayName(*args)
    def useDaylightTime(*args): return _PyICU_calendar.TimeZone_useDaylightTime(*args)
    def inDaylightTime(*args): return _PyICU_calendar.TimeZone_inDaylightTime(*args)
    def hasSameRules(*args): return _PyICU_calendar.TimeZone_hasSameRules(*args)
    getGMT = staticmethod(_PyICU_calendar.TimeZone_getGMT)
    createTimeZone = staticmethod(_PyICU_calendar.TimeZone_createTimeZone)
    createEnumeration = staticmethod(_PyICU_calendar.TimeZone_createEnumeration)
    countEquivalentIDs = staticmethod(_PyICU_calendar.TimeZone_countEquivalentIDs)
    getEquivalentID = staticmethod(_PyICU_calendar.TimeZone_getEquivalentID)
    createDefault = staticmethod(_PyICU_calendar.TimeZone_createDefault)
    def __repr__(*args): return _PyICU_calendar.TimeZone___repr__(*args)
    def getOffset(*args): return _PyICU_calendar.TimeZone_getOffset(*args)
    setDefault = staticmethod(_PyICU_calendar.TimeZone_setDefault)

class TimeZonePtr(TimeZone):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = TimeZone
_PyICU_calendar.TimeZone_swigregister(TimeZonePtr)

TimeZone_getGMT = _PyICU_calendar.TimeZone_getGMT

TimeZone_createTimeZone = _PyICU_calendar.TimeZone_createTimeZone

TimeZone_createEnumeration = _PyICU_calendar.TimeZone_createEnumeration

TimeZone_countEquivalentIDs = _PyICU_calendar.TimeZone_countEquivalentIDs

TimeZone_getEquivalentID = _PyICU_calendar.TimeZone_getEquivalentID

TimeZone_createDefault = _PyICU_calendar.TimeZone_createDefault

TimeZone_setDefault = _PyICU_calendar.TimeZone_setDefault

class SimpleTimeZone(TimeZone):
    WALL_TIME = _PyICU_calendar.SimpleTimeZone_WALL_TIME
    STANDARD_TIME = _PyICU_calendar.SimpleTimeZone_STANDARD_TIME
    UTC_TIME = _PyICU_calendar.SimpleTimeZone_UTC_TIME
    def __init__(self, *args):
        newobj = _PyICU_calendar.new_SimpleTimeZone(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def setStartYear(*args): return _PyICU_calendar.SimpleTimeZone_setStartYear(*args)
    def setStartRule(*args): return _PyICU_calendar.SimpleTimeZone_setStartRule(*args)
    def setEndRule(*args): return _PyICU_calendar.SimpleTimeZone_setEndRule(*args)
    def getRawOffset(*args): return _PyICU_calendar.SimpleTimeZone_getRawOffset(*args)
    def setRawOffset(*args): return _PyICU_calendar.SimpleTimeZone_setRawOffset(*args)
    def setDSTSavings(*args): return _PyICU_calendar.SimpleTimeZone_setDSTSavings(*args)
    def getDSTSavings(*args): return _PyICU_calendar.SimpleTimeZone_getDSTSavings(*args)
    def __repr__(*args): return _PyICU_calendar.SimpleTimeZone___repr__(*args)
    def getOffset(*args): return _PyICU_calendar.SimpleTimeZone_getOffset(*args)

class SimpleTimeZonePtr(SimpleTimeZone):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = SimpleTimeZone
_PyICU_calendar.SimpleTimeZone_swigregister(SimpleTimeZonePtr)

class Calendar(PyICU_bases.UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    ERA = _PyICU_calendar.Calendar_ERA
    YEAR = _PyICU_calendar.Calendar_YEAR
    MONTH = _PyICU_calendar.Calendar_MONTH
    WEEK_OF_YEAR = _PyICU_calendar.Calendar_WEEK_OF_YEAR
    WEEK_OF_MONTH = _PyICU_calendar.Calendar_WEEK_OF_MONTH
    DATE = _PyICU_calendar.Calendar_DATE
    DAY_OF_YEAR = _PyICU_calendar.Calendar_DAY_OF_YEAR
    DAY_OF_WEEK = _PyICU_calendar.Calendar_DAY_OF_WEEK
    DAY_OF_WEEK_IN_MONTH = _PyICU_calendar.Calendar_DAY_OF_WEEK_IN_MONTH
    AM_PM = _PyICU_calendar.Calendar_AM_PM
    HOUR = _PyICU_calendar.Calendar_HOUR
    HOUR_OF_DAY = _PyICU_calendar.Calendar_HOUR_OF_DAY
    MINUTE = _PyICU_calendar.Calendar_MINUTE
    SECOND = _PyICU_calendar.Calendar_SECOND
    MILLISECOND = _PyICU_calendar.Calendar_MILLISECOND
    ZONE_OFFSET = _PyICU_calendar.Calendar_ZONE_OFFSET
    DST_OFFSET = _PyICU_calendar.Calendar_DST_OFFSET
    YEAR_WOY = _PyICU_calendar.Calendar_YEAR_WOY
    DOW_LOCAL = _PyICU_calendar.Calendar_DOW_LOCAL
    SUNDAY = _PyICU_calendar.Calendar_SUNDAY
    MONDAY = _PyICU_calendar.Calendar_MONDAY
    TUESDAY = _PyICU_calendar.Calendar_TUESDAY
    WEDNESDAY = _PyICU_calendar.Calendar_WEDNESDAY
    THURSDAY = _PyICU_calendar.Calendar_THURSDAY
    FRIDAY = _PyICU_calendar.Calendar_FRIDAY
    SATURDAY = _PyICU_calendar.Calendar_SATURDAY
    JANUARY = _PyICU_calendar.Calendar_JANUARY
    FEBRUARY = _PyICU_calendar.Calendar_FEBRUARY
    MARCH = _PyICU_calendar.Calendar_MARCH
    APRIL = _PyICU_calendar.Calendar_APRIL
    MAY = _PyICU_calendar.Calendar_MAY
    JUNE = _PyICU_calendar.Calendar_JUNE
    JULY = _PyICU_calendar.Calendar_JULY
    AUGUST = _PyICU_calendar.Calendar_AUGUST
    SEPTEMBER = _PyICU_calendar.Calendar_SEPTEMBER
    OCTOBER = _PyICU_calendar.Calendar_OCTOBER
    NOVEMBER = _PyICU_calendar.Calendar_NOVEMBER
    DECEMBER = _PyICU_calendar.Calendar_DECEMBER
    UNDECIMBER = _PyICU_calendar.Calendar_UNDECIMBER
    AM = _PyICU_calendar.Calendar_AM
    PM = _PyICU_calendar.Calendar_PM
    def __eq__(*args): return _PyICU_calendar.Calendar___eq__(*args)
    def __ne__(*args): return _PyICU_calendar.Calendar___ne__(*args)
    def getTime(*args): return _PyICU_calendar.Calendar_getTime(*args)
    def setTime(*args): return _PyICU_calendar.Calendar_setTime(*args)
    def isEquivalentTo(*args): return _PyICU_calendar.Calendar_isEquivalentTo(*args)
    def getType(*args): return _PyICU_calendar.Calendar_getType(*args)
    def equals(*args): return _PyICU_calendar.Calendar_equals(*args)
    def before(*args): return _PyICU_calendar.Calendar_before(*args)
    def after(*args): return _PyICU_calendar.Calendar_after(*args)
    def add(*args): return _PyICU_calendar.Calendar_add(*args)
    def roll(*args): return _PyICU_calendar.Calendar_roll(*args)
    def fieldDifference(*args): return _PyICU_calendar.Calendar_fieldDifference(*args)
    def setTimeZone(*args): return _PyICU_calendar.Calendar_setTimeZone(*args)
    def getTimeZone(*args): return _PyICU_calendar.Calendar_getTimeZone(*args)
    def inDaylightTime(*args): return _PyICU_calendar.Calendar_inDaylightTime(*args)
    def setLenient(*args): return _PyICU_calendar.Calendar_setLenient(*args)
    def isLenient(*args): return _PyICU_calendar.Calendar_isLenient(*args)
    def setFirstDayOfWeek(*args): return _PyICU_calendar.Calendar_setFirstDayOfWeek(*args)
    def getFirstDayOfWeek(*args): return _PyICU_calendar.Calendar_getFirstDayOfWeek(*args)
    def setMinimalDaysInFirstWeek(*args): return _PyICU_calendar.Calendar_setMinimalDaysInFirstWeek(*args)
    def getMinimum(*args): return _PyICU_calendar.Calendar_getMinimum(*args)
    def getMaximum(*args): return _PyICU_calendar.Calendar_getMaximum(*args)
    def getGreatestMinimum(*args): return _PyICU_calendar.Calendar_getGreatestMinimum(*args)
    def getLeastMaximum(*args): return _PyICU_calendar.Calendar_getLeastMaximum(*args)
    def getActualMinimum(*args): return _PyICU_calendar.Calendar_getActualMinimum(*args)
    def getActualMaximum(*args): return _PyICU_calendar.Calendar_getActualMaximum(*args)
    def get(*args): return _PyICU_calendar.Calendar_get(*args)
    def isSet(*args): return _PyICU_calendar.Calendar_isSet(*args)
    def set(*args): return _PyICU_calendar.Calendar_set(*args)
    def clear(*args): return _PyICU_calendar.Calendar_clear(*args)
    def haveDefaultCentury(*args): return _PyICU_calendar.Calendar_haveDefaultCentury(*args)
    def defaultCenturyStart(*args): return _PyICU_calendar.Calendar_defaultCenturyStart(*args)
    def defaultCenturyStartYear(*args): return _PyICU_calendar.Calendar_defaultCenturyStartYear(*args)
    createInstance = staticmethod(_PyICU_calendar.Calendar_createInstance)
    getAvailableLocales = staticmethod(_PyICU_calendar.Calendar_getAvailableLocales)
    getNow = staticmethod(_PyICU_calendar.Calendar_getNow)
    def getLocale(*args): return _PyICU_calendar.Calendar_getLocale(*args)
    def getLocaleID(*args): return _PyICU_calendar.Calendar_getLocaleID(*args)
    def __repr__(*args): return _PyICU_calendar.Calendar___repr__(*args)

class CalendarPtr(Calendar):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Calendar
_PyICU_calendar.Calendar_swigregister(CalendarPtr)

Calendar_createInstance = _PyICU_calendar.Calendar_createInstance

Calendar_getAvailableLocales = _PyICU_calendar.Calendar_getAvailableLocales

Calendar_getNow = _PyICU_calendar.Calendar_getNow

class GregorianCalendar(Calendar):
    BC = _PyICU_calendar.GregorianCalendar_BC
    AD = _PyICU_calendar.GregorianCalendar_AD
    def __init__(self, *args):
        newobj = _PyICU_calendar.new_GregorianCalendar(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def setGregorianChange(*args): return _PyICU_calendar.GregorianCalendar_setGregorianChange(*args)
    def getGregorianChange(*args): return _PyICU_calendar.GregorianCalendar_getGregorianChange(*args)
    def isLeapYear(*args): return _PyICU_calendar.GregorianCalendar_isLeapYear(*args)
    def isEquivalentTo(*args): return _PyICU_calendar.GregorianCalendar_isEquivalentTo(*args)
    def __repr__(*args): return _PyICU_calendar.GregorianCalendar___repr__(*args)

class GregorianCalendarPtr(GregorianCalendar):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = GregorianCalendar
_PyICU_calendar.GregorianCalendar_swigregister(GregorianCalendarPtr)

from datetime import tzinfo, timedelta
FLOATING_TZNAME = "World/Floating"

class ICUtzinfo(tzinfo):

    instances = {}

    def _resetDefault(cls):
        cls.default = ICUtzinfo(TimeZone.createDefault())
    _resetDefault = classmethod(_resetDefault)

    def getInstance(cls, id):
        try:
            return cls.instances[id]
        except KeyError:
            if id == FLOATING_TZNAME:
                instance = cls.floating
            else:
                instance = cls(TimeZone.createTimeZone(id))
            cls.instances[id] = instance
            return instance
    getInstance = classmethod(getInstance)

    def getDefault(cls):
        return cls.default
    getDefault = classmethod(getDefault)

    def getFloating(cls):
        return cls.floating
    getFloating = classmethod(getFloating)

    def __init__(self, timezone):
        if not isinstance(timezone, TimeZone):
            raise TypeError, timezone
        super(ICUtzinfo, self).__init__()
        self._timezone = timezone

    def __repr__(self):
        return "<ICUtzinfo: %s>" %(self._timezone.getID())

    def __str__(self):
        return str(self._timezone.getID())

    def __eq__(self, other):
        if isinstance(other, ICUtzinfo):
            return str(self) == str(other)
        return False

    def __ne__(self, other):
        if isinstance(other, ICUtzinfo):
            return str(self) != str(other)
        return True

    def __hash__(self):
        return hash(self.tzid)

    def _notzsecs(self, dt):
        return ((dt.toordinal() - 719163) * 86400.0 +
                dt.hour * 3600.0 + dt.minute * 60.0 +
                float(dt.second) + dt.microsecond / 1e6)

    def utcoffset(self, dt):
        raw, dst = self._timezone.getOffset(self._notzsecs(dt), True)
        return timedelta(seconds = (raw + dst) / 1000)

    def dst(self, dt):
        raw, dst = self._timezone.getOffset(self._notzsecs(dt), True)
        return timedelta(seconds = dst / 1000)

    def tzname(self, dt):
        return str(self._timezone.getID())

    def _getTimezone(self):
        return TimeZone.createTimeZone(self._timezone.getID())

    tzid = property(__str__)
    timezone = property(_getTimezone)


class FloatingTZ(ICUtzinfo):

    def __init__(self):
        pass

    def __repr__(self):
        return "<FloatingTZ: %s>" %(ICUtzinfo.default._timezone.getID())

    def __str__(self):
        return FLOATING_TZNAME

    def __hash__(self):
        return hash(FLOATING_TZNAME)

    def utcoffset(self, dt):
        tz = ICUtzinfo.default._timezone
        raw, dst = tz.getOffset(self._notzsecs(dt), True)
        return timedelta(seconds = (raw + dst) / 1000)

    def dst(self, dt):
        tz = ICUtzinfo.default._timezone
        raw, dst = tz.getOffset(self._notzsecs(dt), True)
        return timedelta(seconds = dst / 1000)

    def _getTimezone(self):
        return TimeZone.createTimeZone(ICUtzinfo.default._timezone.getID())

    def __getTimezone(self):
        return ICUtzinfo.default._timezone

    def tzname(self, dt):
        return FLOATING_TZNAME

    tzid = FLOATING_TZNAME
    _timezone = property(__getTimezone)


ICUtzinfo.default = ICUtzinfo(TimeZone.createDefault())
ICUtzinfo.floating = FloatingTZ()


