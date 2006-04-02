# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_dateformat

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
import PyICU_format
import PyICU_calendar
import PyICU_numberformat
class DateFormatSymbols(PyICU_bases.UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::DateFormatSymbols instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    FORMAT = _PyICU_dateformat.DateFormatSymbols_FORMAT
    STANDALONE = _PyICU_dateformat.DateFormatSymbols_STANDALONE
    WIDE = _PyICU_dateformat.DateFormatSymbols_WIDE
    ABBREVIATED = _PyICU_dateformat.DateFormatSymbols_ABBREVIATED
    NARROW = _PyICU_dateformat.DateFormatSymbols_NARROW
    def __init__(self, *args):
        newobj = _PyICU_dateformat.new_DateFormatSymbols(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __eq__(*args): return _PyICU_dateformat.DateFormatSymbols___eq__(*args)
    def __ne__(*args): return _PyICU_dateformat.DateFormatSymbols___ne__(*args)
    def getEras(*args): return _PyICU_dateformat.DateFormatSymbols_getEras(*args)
    def setEras(*args): return _PyICU_dateformat.DateFormatSymbols_setEras(*args)
    def getMonths(*args): return _PyICU_dateformat.DateFormatSymbols_getMonths(*args)
    def setMonths(*args): return _PyICU_dateformat.DateFormatSymbols_setMonths(*args)
    def getShortMonths(*args): return _PyICU_dateformat.DateFormatSymbols_getShortMonths(*args)
    def setShortMonths(*args): return _PyICU_dateformat.DateFormatSymbols_setShortMonths(*args)
    def getWeekdays(*args): return _PyICU_dateformat.DateFormatSymbols_getWeekdays(*args)
    def setWeekdays(*args): return _PyICU_dateformat.DateFormatSymbols_setWeekdays(*args)
    def getShortWeekdays(*args): return _PyICU_dateformat.DateFormatSymbols_getShortWeekdays(*args)
    def setShortWeekdays(*args): return _PyICU_dateformat.DateFormatSymbols_setShortWeekdays(*args)
    def getAmPmStrings(*args): return _PyICU_dateformat.DateFormatSymbols_getAmPmStrings(*args)
    def setAmPmStrings(*args): return _PyICU_dateformat.DateFormatSymbols_setAmPmStrings(*args)
    def getLocalPatternChars(*args): return _PyICU_dateformat.DateFormatSymbols_getLocalPatternChars(*args)
    def setLocalPatternChars(*args): return _PyICU_dateformat.DateFormatSymbols_setLocalPatternChars(*args)
    def getLocale(*args): return _PyICU_dateformat.DateFormatSymbols_getLocale(*args)

class DateFormatSymbolsPtr(DateFormatSymbols):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = DateFormatSymbols
_PyICU_dateformat.DateFormatSymbols_swigregister(DateFormatSymbolsPtr)

class DateFormat(PyICU_format.Format):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::DateFormat instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    kNone = _PyICU_dateformat.DateFormat_kNone
    kFull = _PyICU_dateformat.DateFormat_kFull
    kLong = _PyICU_dateformat.DateFormat_kLong
    kMedium = _PyICU_dateformat.DateFormat_kMedium
    kShort = _PyICU_dateformat.DateFormat_kShort
    kDateOffset = _PyICU_dateformat.DateFormat_kDateOffset
    kDateTime = _PyICU_dateformat.DateFormat_kDateTime
    kDefault = _PyICU_dateformat.DateFormat_kDefault
    FULL = _PyICU_dateformat.DateFormat_FULL
    LONG = _PyICU_dateformat.DateFormat_LONG
    MEDIUM = _PyICU_dateformat.DateFormat_MEDIUM
    SHORT = _PyICU_dateformat.DateFormat_SHORT
    DEFAULT = _PyICU_dateformat.DateFormat_DEFAULT
    DATE_OFFSET = _PyICU_dateformat.DateFormat_DATE_OFFSET
    NONE = _PyICU_dateformat.DateFormat_NONE
    DATE_TIME = _PyICU_dateformat.DateFormat_DATE_TIME
    kEraField = _PyICU_dateformat.DateFormat_kEraField
    kYearField = _PyICU_dateformat.DateFormat_kYearField
    kMonthField = _PyICU_dateformat.DateFormat_kMonthField
    kDateField = _PyICU_dateformat.DateFormat_kDateField
    kHourOfDay1Field = _PyICU_dateformat.DateFormat_kHourOfDay1Field
    kHourOfDay0Field = _PyICU_dateformat.DateFormat_kHourOfDay0Field
    kMinuteField = _PyICU_dateformat.DateFormat_kMinuteField
    kSecondField = _PyICU_dateformat.DateFormat_kSecondField
    kMillisecondField = _PyICU_dateformat.DateFormat_kMillisecondField
    kDayOfWeekField = _PyICU_dateformat.DateFormat_kDayOfWeekField
    kDayOfYearField = _PyICU_dateformat.DateFormat_kDayOfYearField
    kDayOfWeekInMonthField = _PyICU_dateformat.DateFormat_kDayOfWeekInMonthField
    kWeekOfYearField = _PyICU_dateformat.DateFormat_kWeekOfYearField
    kWeekOfMonthField = _PyICU_dateformat.DateFormat_kWeekOfMonthField
    kAmPmField = _PyICU_dateformat.DateFormat_kAmPmField
    kHour1Field = _PyICU_dateformat.DateFormat_kHour1Field
    kHour0Field = _PyICU_dateformat.DateFormat_kHour0Field
    kTimezoneField = _PyICU_dateformat.DateFormat_kTimezoneField
    kYearWOYField = _PyICU_dateformat.DateFormat_kYearWOYField
    kDOWLocalField = _PyICU_dateformat.DateFormat_kDOWLocalField
    kExtendedYearField = _PyICU_dateformat.DateFormat_kExtendedYearField
    kJulianDayField = _PyICU_dateformat.DateFormat_kJulianDayField
    kMillisecondsInDayField = _PyICU_dateformat.DateFormat_kMillisecondsInDayField
    ERA_FIELD = _PyICU_dateformat.DateFormat_ERA_FIELD
    YEAR_FIELD = _PyICU_dateformat.DateFormat_YEAR_FIELD
    MONTH_FIELD = _PyICU_dateformat.DateFormat_MONTH_FIELD
    DATE_FIELD = _PyICU_dateformat.DateFormat_DATE_FIELD
    HOUR_OF_DAY1_FIELD = _PyICU_dateformat.DateFormat_HOUR_OF_DAY1_FIELD
    HOUR_OF_DAY0_FIELD = _PyICU_dateformat.DateFormat_HOUR_OF_DAY0_FIELD
    MINUTE_FIELD = _PyICU_dateformat.DateFormat_MINUTE_FIELD
    SECOND_FIELD = _PyICU_dateformat.DateFormat_SECOND_FIELD
    MILLISECOND_FIELD = _PyICU_dateformat.DateFormat_MILLISECOND_FIELD
    DAY_OF_WEEK_FIELD = _PyICU_dateformat.DateFormat_DAY_OF_WEEK_FIELD
    DAY_OF_YEAR_FIELD = _PyICU_dateformat.DateFormat_DAY_OF_YEAR_FIELD
    DAY_OF_WEEK_IN_MONTH_FIELD = _PyICU_dateformat.DateFormat_DAY_OF_WEEK_IN_MONTH_FIELD
    WEEK_OF_YEAR_FIELD = _PyICU_dateformat.DateFormat_WEEK_OF_YEAR_FIELD
    WEEK_OF_MONTH_FIELD = _PyICU_dateformat.DateFormat_WEEK_OF_MONTH_FIELD
    AM_PM_FIELD = _PyICU_dateformat.DateFormat_AM_PM_FIELD
    HOUR1_FIELD = _PyICU_dateformat.DateFormat_HOUR1_FIELD
    HOUR0_FIELD = _PyICU_dateformat.DateFormat_HOUR0_FIELD
    TIMEZONE_FIELD = _PyICU_dateformat.DateFormat_TIMEZONE_FIELD
    def isLenient(*args): return _PyICU_dateformat.DateFormat_isLenient(*args)
    def setLenient(*args): return _PyICU_dateformat.DateFormat_setLenient(*args)
    def format(*args): return _PyICU_dateformat.DateFormat_format(*args)
    def parse(*args): return _PyICU_dateformat.DateFormat_parse(*args)
    def getCalendar(*args): return _PyICU_dateformat.DateFormat_getCalendar(*args)
    def setCalendar(*args): return _PyICU_dateformat.DateFormat_setCalendar(*args)
    def getNumberFormat(*args): return _PyICU_dateformat.DateFormat_getNumberFormat(*args)
    def setNumberFormat(*args): return _PyICU_dateformat.DateFormat_setNumberFormat(*args)
    def getTimeZone(*args): return _PyICU_dateformat.DateFormat_getTimeZone(*args)
    def setTimeZone(*args): return _PyICU_dateformat.DateFormat_setTimeZone(*args)
    createInstance = staticmethod(_PyICU_dateformat.DateFormat_createInstance)
    createTimeInstance = staticmethod(_PyICU_dateformat.DateFormat_createTimeInstance)
    createDateInstance = staticmethod(_PyICU_dateformat.DateFormat_createDateInstance)
    createDateTimeInstance = staticmethod(_PyICU_dateformat.DateFormat_createDateTimeInstance)
    getAvailableLocales = staticmethod(_PyICU_dateformat.DateFormat_getAvailableLocales)

class DateFormatPtr(DateFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = DateFormat
_PyICU_dateformat.DateFormat_swigregister(DateFormatPtr)

DateFormat_createInstance = _PyICU_dateformat.DateFormat_createInstance

DateFormat_createTimeInstance = _PyICU_dateformat.DateFormat_createTimeInstance

DateFormat_createDateInstance = _PyICU_dateformat.DateFormat_createDateInstance

DateFormat_createDateTimeInstance = _PyICU_dateformat.DateFormat_createDateTimeInstance

DateFormat_getAvailableLocales = _PyICU_dateformat.DateFormat_getAvailableLocales

class SimpleDateFormat(DateFormat):
    def __init__(self, *args):
        newobj = _PyICU_dateformat.new_SimpleDateFormat(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def toPattern(*args): return _PyICU_dateformat.SimpleDateFormat_toPattern(*args)
    def toLocalizedPattern(*args): return _PyICU_dateformat.SimpleDateFormat_toLocalizedPattern(*args)
    def applyPattern(*args): return _PyICU_dateformat.SimpleDateFormat_applyPattern(*args)
    def applyLocalizedPattern(*args): return _PyICU_dateformat.SimpleDateFormat_applyLocalizedPattern(*args)
    def set2DigitYearStart(*args): return _PyICU_dateformat.SimpleDateFormat_set2DigitYearStart(*args)
    def get2DigitYearStart(*args): return _PyICU_dateformat.SimpleDateFormat_get2DigitYearStart(*args)
    def getDateFormatSymbols(*args): return _PyICU_dateformat.SimpleDateFormat_getDateFormatSymbols(*args)
    def setDateFormatSymbols(*args): return _PyICU_dateformat.SimpleDateFormat_setDateFormatSymbols(*args)
    def __repr__(*args): return _PyICU_dateformat.SimpleDateFormat___repr__(*args)

class SimpleDateFormatPtr(SimpleDateFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = SimpleDateFormat
_PyICU_dateformat.SimpleDateFormat_swigregister(SimpleDateFormatPtr)


