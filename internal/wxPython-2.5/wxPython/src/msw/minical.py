# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

"""
Classes for an interactive mini-Calendar control.
"""

import _minical

import _misc
import _core
wx = _core 
__docfilter__ = wx.__DocFilter(globals()) 
CAL_SUNDAY_FIRST = _minical.CAL_SUNDAY_FIRST
CAL_MONDAY_FIRST = _minical.CAL_MONDAY_FIRST
CAL_SHOW_SURROUNDING_WEEKS = _minical.CAL_SHOW_SURROUNDING_WEEKS
CAL_SHOW_PREVIEW = _minical.CAL_SHOW_PREVIEW
CAL_HITTEST_NOWHERE = _minical.CAL_HITTEST_NOWHERE
CAL_HITTEST_HEADER = _minical.CAL_HITTEST_HEADER
CAL_HITTEST_DAY = _minical.CAL_HITTEST_DAY
CAL_HITTEST_TODAY = _minical.CAL_HITTEST_TODAY
CAL_HITTEST_INCMONTH = _minical.CAL_HITTEST_INCMONTH
CAL_HITTEST_DECMONTH = _minical.CAL_HITTEST_DECMONTH
CAL_HITTEST_SURROUNDING_WEEK = _minical.CAL_HITTEST_SURROUNDING_WEEK
class MiniCalendarDateAttr(object):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxMiniCalendarDateAttr instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args, **kwargs):
        """__init__(self, double busyPercentage=0) -> MiniCalendarDateAttr"""
        newobj = _minical.new_MiniCalendarDateAttr(*args, **kwargs)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def SetBusy(*args, **kwargs):
        """SetBusy(self, double busyPercentage)"""
        return _minical.MiniCalendarDateAttr_SetBusy(*args, **kwargs)

    def GetBusy(*args, **kwargs):
        """GetBusy(self) -> double"""
        return _minical.MiniCalendarDateAttr_GetBusy(*args, **kwargs)


class MiniCalendarDateAttrPtr(MiniCalendarDateAttr):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = MiniCalendarDateAttr
_minical.MiniCalendarDateAttr_swigregister(MiniCalendarDateAttrPtr)

class MiniCalendarEvent(_core.CommandEvent):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxMiniCalendarEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args, **kwargs):
        """__init__(self, MiniCalendar cal, wxEventType type) -> MiniCalendarEvent"""
        newobj = _minical.new_MiniCalendarEvent(*args, **kwargs)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def GetDate(*args, **kwargs):
        """GetDate(self) -> DateTime"""
        return _minical.MiniCalendarEvent_GetDate(*args, **kwargs)

    def SetDate(*args, **kwargs):
        """SetDate(self, DateTime date)"""
        return _minical.MiniCalendarEvent_SetDate(*args, **kwargs)

    def SetWeekDay(*args, **kwargs):
        """SetWeekDay(self, int wd)"""
        return _minical.MiniCalendarEvent_SetWeekDay(*args, **kwargs)

    def GetWeekDay(*args, **kwargs):
        """GetWeekDay(self) -> int"""
        return _minical.MiniCalendarEvent_GetWeekDay(*args, **kwargs)

    def PySetDate(self, date):
        """takes datetime.datetime or datetime.date object"""
        self.SetDate(_pydate2wxdate(date))

    def PyGetDate(self):
        """returns datetime.date object"""
        return _wxdate2pydate(self.GetDate())


class MiniCalendarEventPtr(MiniCalendarEvent):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = MiniCalendarEvent
_minical.MiniCalendarEvent_swigregister(MiniCalendarEventPtr)

wxEVT_MINI_CALENDAR_DOUBLECLICKED = _minical.wxEVT_MINI_CALENDAR_DOUBLECLICKED
wxEVT_MINI_CALENDAR_SEL_CHANGED = _minical.wxEVT_MINI_CALENDAR_SEL_CHANGED
wxEVT_MINI_CALENDAR_DAY_CHANGED = _minical.wxEVT_MINI_CALENDAR_DAY_CHANGED
wxEVT_MINI_CALENDAR_MONTH_CHANGED = _minical.wxEVT_MINI_CALENDAR_MONTH_CHANGED
wxEVT_MINI_CALENDAR_YEAR_CHANGED = _minical.wxEVT_MINI_CALENDAR_YEAR_CHANGED
EVT_MINI_CALENDAR_DOUBLECLICKED =   wx.PyEventBinder( wxEVT_MINI_CALENDAR_DOUBLECLICKED, 1)
EVT_MINI_CALENDAR_SEL_CHANGED =     wx.PyEventBinder( wxEVT_MINI_CALENDAR_SEL_CHANGED, 1)
EVT_MINI_CALENDAR_DAY =             wx.PyEventBinder( wxEVT_MINI_CALENDAR_DAY_CHANGED, 1)
EVT_MINI_CALENDAR_MONTH =           wx.PyEventBinder( wxEVT_MINI_CALENDAR_MONTH_CHANGED, 1)
EVT_MINI_CALENDAR_YEAR =            wx.PyEventBinder( wxEVT_MINI_CALENDAR_YEAR_CHANGED, 1)

class MiniCalendar(_core.Control):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxMiniCalendar instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        """
        __init__(self, Window parent, int id=-1, DateTime date=DefaultDateTime, 
            Point pos=DefaultPosition, Size size=DefaultSize, 
            long style=0, String name=wxCalendarNameStr) -> MiniCalendar
        __init__(self) -> MiniCalendar
        """
        newobj = _minical.new_MiniCalendar(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def SetDate(*args, **kwargs):
        """SetDate(self, DateTime date)"""
        return _minical.MiniCalendar_SetDate(*args, **kwargs)

    def GetDate(*args, **kwargs):
        """GetDate(self) -> DateTime"""
        return _minical.MiniCalendar_GetDate(*args, **kwargs)

    def SetLowerDateLimit(*args, **kwargs):
        """SetLowerDateLimit(self, DateTime date=DefaultDateTime) -> bool"""
        return _minical.MiniCalendar_SetLowerDateLimit(*args, **kwargs)

    def SetUpperDateLimit(*args, **kwargs):
        """SetUpperDateLimit(self, DateTime date=DefaultDateTime) -> bool"""
        return _minical.MiniCalendar_SetUpperDateLimit(*args, **kwargs)

    def GetLowerDateLimit(*args, **kwargs):
        """GetLowerDateLimit(self) -> DateTime"""
        return _minical.MiniCalendar_GetLowerDateLimit(*args, **kwargs)

    def GetUpperDateLimit(*args, **kwargs):
        """GetUpperDateLimit(self) -> DateTime"""
        return _minical.MiniCalendar_GetUpperDateLimit(*args, **kwargs)

    def SetDateRange(*args, **kwargs):
        """SetDateRange(self, DateTime lowerdate=DefaultDateTime, DateTime upperdate=DefaultDateTime) -> bool"""
        return _minical.MiniCalendar_SetDateRange(*args, **kwargs)

    def SetHeaderColours(*args, **kwargs):
        """SetHeaderColours(self, Colour colFg, Colour colBg)"""
        return _minical.MiniCalendar_SetHeaderColours(*args, **kwargs)

    def GetHeaderColourFg(*args, **kwargs):
        """GetHeaderColourFg(self) -> Colour"""
        return _minical.MiniCalendar_GetHeaderColourFg(*args, **kwargs)

    def GetHeaderColourBg(*args, **kwargs):
        """GetHeaderColourBg(self) -> Colour"""
        return _minical.MiniCalendar_GetHeaderColourBg(*args, **kwargs)

    def SetHighlightColours(*args, **kwargs):
        """SetHighlightColours(self, Colour colFg, Colour colBg)"""
        return _minical.MiniCalendar_SetHighlightColours(*args, **kwargs)

    def GetHighlightColourFg(*args, **kwargs):
        """GetHighlightColourFg(self) -> Colour"""
        return _minical.MiniCalendar_GetHighlightColourFg(*args, **kwargs)

    def GetHighlightColourBg(*args, **kwargs):
        """GetHighlightColourBg(self) -> Colour"""
        return _minical.MiniCalendar_GetHighlightColourBg(*args, **kwargs)

    def GetAttr(*args, **kwargs):
        """GetAttr(self, size_t day) -> MiniCalendarDateAttr"""
        return _minical.MiniCalendar_GetAttr(*args, **kwargs)

    def SetAttr(*args, **kwargs):
        """SetAttr(self, size_t day, MiniCalendarDateAttr attr)"""
        return _minical.MiniCalendar_SetAttr(*args, **kwargs)


class MiniCalendarPtr(MiniCalendar):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = MiniCalendar
_minical.MiniCalendar_swigregister(MiniCalendarPtr)


