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
wxCAL_SUNDAY_FIRST = _minical.wxCAL_SUNDAY_FIRST
wxCAL_MONDAY_FIRST = _minical.wxCAL_MONDAY_FIRST
wxCAL_SHOW_SURROUNDING_WEEKS = _minical.wxCAL_SHOW_SURROUNDING_WEEKS
wxCAL_SHOW_PREVIEW = _minical.wxCAL_SHOW_PREVIEW
wxCAL_HITTEST_NOWHERE = _minical.wxCAL_HITTEST_NOWHERE
wxCAL_HITTEST_HEADER = _minical.wxCAL_HITTEST_HEADER
wxCAL_HITTEST_DAY = _minical.wxCAL_HITTEST_DAY
wxCAL_HITTEST_TODAY = _minical.wxCAL_HITTEST_TODAY
wxCAL_HITTEST_INCMONTH = _minical.wxCAL_HITTEST_INCMONTH
wxCAL_HITTEST_DECMONTH = _minical.wxCAL_HITTEST_DECMONTH
wxCAL_HITTEST_SURROUNDING_WEEK = _minical.wxCAL_HITTEST_SURROUNDING_WEEK
class wxMiniCalendarDateAttr(object):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxMiniCalendarDateAttr instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args, **kwargs):
        """__init__(self, double busyPercentage=0) -> wxMiniCalendarDateAttr"""
        newobj = _minical.new_wxMiniCalendarDateAttr(*args, **kwargs)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def SetBusy(*args, **kwargs):
        """SetBusy(self, double busyPercentage)"""
        return _minical.wxMiniCalendarDateAttr_SetBusy(*args, **kwargs)

    def GetBusy(*args, **kwargs):
        """GetBusy(self) -> double"""
        return _minical.wxMiniCalendarDateAttr_GetBusy(*args, **kwargs)


class wxMiniCalendarDateAttrPtr(wxMiniCalendarDateAttr):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = wxMiniCalendarDateAttr
_minical.wxMiniCalendarDateAttr_swigregister(wxMiniCalendarDateAttrPtr)

class wxMiniCalendarEvent(_core.CommandEvent):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxMiniCalendarEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args, **kwargs):
        """__init__(self, wxMiniCalendar cal, wxEventType type) -> wxMiniCalendarEvent"""
        newobj = _minical.new_wxMiniCalendarEvent(*args, **kwargs)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def GetDate(*args, **kwargs):
        """GetDate(self) -> DateTime"""
        return _minical.wxMiniCalendarEvent_GetDate(*args, **kwargs)

    def SetDate(*args, **kwargs):
        """SetDate(self, DateTime date)"""
        return _minical.wxMiniCalendarEvent_SetDate(*args, **kwargs)

    def SetWeekDay(*args, **kwargs):
        """SetWeekDay(self, int wd)"""
        return _minical.wxMiniCalendarEvent_SetWeekDay(*args, **kwargs)

    def GetWeekDay(*args, **kwargs):
        """GetWeekDay(self) -> int"""
        return _minical.wxMiniCalendarEvent_GetWeekDay(*args, **kwargs)

    def PySetDate(self, date):
        """takes datetime.datetime or datetime.date object"""
        self.SetDate(_pydate2wxdate(date))

    def PyGetDate(self):
        """returns datetime.date object"""
        return _wxdate2pydate(self.GetDate())


class wxMiniCalendarEventPtr(wxMiniCalendarEvent):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = wxMiniCalendarEvent
_minical.wxMiniCalendarEvent_swigregister(wxMiniCalendarEventPtr)

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

class wxMiniCalendar(_core.Control):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxMiniCalendar instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        """
        __init__(self, Window parent, int id=-1, DateTime date=DefaultDateTime, 
            Point pos=DefaultPosition, Size size=DefaultSize, 
            long style=0, String name=wxCalendarNameStr) -> wxMiniCalendar
        __init__(self) -> wxMiniCalendar
        """
        newobj = _minical.new_wxMiniCalendar(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def SetDate(*args, **kwargs):
        """SetDate(self, DateTime date)"""
        return _minical.wxMiniCalendar_SetDate(*args, **kwargs)

    def GetDate(*args, **kwargs):
        """GetDate(self) -> DateTime"""
        return _minical.wxMiniCalendar_GetDate(*args, **kwargs)

    def SetLowerDateLimit(*args, **kwargs):
        """SetLowerDateLimit(self, DateTime date=DefaultDateTime) -> bool"""
        return _minical.wxMiniCalendar_SetLowerDateLimit(*args, **kwargs)

    def SetUpperDateLimit(*args, **kwargs):
        """SetUpperDateLimit(self, DateTime date=DefaultDateTime) -> bool"""
        return _minical.wxMiniCalendar_SetUpperDateLimit(*args, **kwargs)

    def GetLowerDateLimit(*args, **kwargs):
        """GetLowerDateLimit(self) -> DateTime"""
        return _minical.wxMiniCalendar_GetLowerDateLimit(*args, **kwargs)

    def GetUpperDateLimit(*args, **kwargs):
        """GetUpperDateLimit(self) -> DateTime"""
        return _minical.wxMiniCalendar_GetUpperDateLimit(*args, **kwargs)

    def SetDateRange(*args, **kwargs):
        """SetDateRange(self, DateTime lowerdate=DefaultDateTime, DateTime upperdate=DefaultDateTime) -> bool"""
        return _minical.wxMiniCalendar_SetDateRange(*args, **kwargs)

    def SetHeaderColours(*args, **kwargs):
        """SetHeaderColours(self, Colour colFg, Colour colBg)"""
        return _minical.wxMiniCalendar_SetHeaderColours(*args, **kwargs)

    def GetHeaderColourFg(*args, **kwargs):
        """GetHeaderColourFg(self) -> Colour"""
        return _minical.wxMiniCalendar_GetHeaderColourFg(*args, **kwargs)

    def GetHeaderColourBg(*args, **kwargs):
        """GetHeaderColourBg(self) -> Colour"""
        return _minical.wxMiniCalendar_GetHeaderColourBg(*args, **kwargs)

    def SetHighlightColours(*args, **kwargs):
        """SetHighlightColours(self, Colour colFg, Colour colBg)"""
        return _minical.wxMiniCalendar_SetHighlightColours(*args, **kwargs)

    def GetHighlightColourFg(*args, **kwargs):
        """GetHighlightColourFg(self) -> Colour"""
        return _minical.wxMiniCalendar_GetHighlightColourFg(*args, **kwargs)

    def GetHighlightColourBg(*args, **kwargs):
        """GetHighlightColourBg(self) -> Colour"""
        return _minical.wxMiniCalendar_GetHighlightColourBg(*args, **kwargs)

    def GetAttr(*args, **kwargs):
        """GetAttr(self, size_t day) -> wxMiniCalendarDateAttr"""
        return _minical.wxMiniCalendar_GetAttr(*args, **kwargs)

    def SetAttr(*args, **kwargs):
        """SetAttr(self, size_t day, wxMiniCalendarDateAttr attr)"""
        return _minical.wxMiniCalendar_SetAttr(*args, **kwargs)


class wxMiniCalendarPtr(wxMiniCalendar):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = wxMiniCalendar
_minical.wxMiniCalendar_swigregister(wxMiniCalendarPtr)


