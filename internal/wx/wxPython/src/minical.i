/////////////////////////////////////////////////////////////////////////////
// Name:        minical.i
// Purpose:     SWIG definitions for the wxMiniCalendar
//
// Author:      Jed Burgess
//
/////////////////////////////////////////////////////////////////////////////

%define DOCSTRING
"Classes for an interactive mini-Calendar control."
%enddef

%module(package="wx", docstring=DOCSTRING) minical


%{
#include "wx/wxPython/wxPython.h"
#include "wx/wxPython/pyclasses.h"

#include <wx/minical.h>
%}

//----------------------------------------------------------------------

%import misc.i
%pythoncode { wx = _core }
%pythoncode { __docfilter__ = wx.__DocFilter(globals()) }
%include _minical_rename.i

//---------------------------------------------------------------------------

enum {
    wxCAL_SUNDAY_FIRST,
    wxCAL_MONDAY_FIRST,
    wxCAL_SHOW_SURROUNDING_WEEKS,
    wxCAL_SHOW_PREVIEW,
    wxCAL_HIGHLIGHT_WEEK,
    wxCAL_SHOW_BUSY
};


enum wxCalendarHitTestResult
{
    wxCAL_HITTEST_NOWHERE,      // outside of anything
    wxCAL_HITTEST_HEADER,       // on the header (weekdays)
    wxCAL_HITTEST_DAY,          // on a day in the calendar
    wxCAL_HITTEST_TODAY,        // on the today button
    wxCAL_HITTEST_INCMONTH,
    wxCAL_HITTEST_DECMONTH,
    wxCAL_HITTEST_SURROUNDING_WEEK
};

//---------------------------------------------------------------------------

class wxMiniCalendarDateAttr
{
public:
    wxMiniCalendarDateAttr(double busyPercentage = 0);


    // setters
    void SetBusy(const double busyPercentage);

    // accessors
    const double GetBusy() const;
};

//---------------------------------------------------------------------------

class wxMiniCalendar;

class wxMiniCalendarEvent : public wxCommandEvent
{
public:
    wxMiniCalendarEvent(wxMiniCalendar *cal, wxEventType type);

    const wxDateTime GetDate() const;
    void SetDate(const wxDateTime &date);
    void SetWeekDay(const wxDateTime::WeekDay wd);
    wxDateTime::WeekDay GetWeekDay() const;

    %pythoncode {
    def PySetDate(self, date):
        """takes datetime.datetime or datetime.date object"""
        self.SetDate(_pydate2wxdate(date))

    def PyGetDate(self):
        """returns datetime.date object"""
        return _wxdate2pydate(self.GetDate())
    }
};


%constant wxEventType wxEVT_MINI_CALENDAR_DOUBLECLICKED;
%constant wxEventType wxEVT_MINI_CALENDAR_SEL_CHANGED;
%constant wxEventType wxEVT_MINI_CALENDAR_DAY_CHANGED;
%constant wxEventType wxEVT_MINI_CALENDAR_MONTH_CHANGED;
%constant wxEventType wxEVT_MINI_CALENDAR_YEAR_CHANGED;


%pythoncode {
EVT_MINI_CALENDAR_DOUBLECLICKED =   wx.PyEventBinder( wxEVT_MINI_CALENDAR_DOUBLECLICKED, 1)
EVT_MINI_CALENDAR_SEL_CHANGED =     wx.PyEventBinder( wxEVT_MINI_CALENDAR_SEL_CHANGED, 1)
EVT_MINI_CALENDAR_DAY =             wx.PyEventBinder( wxEVT_MINI_CALENDAR_DAY_CHANGED, 1)
EVT_MINI_CALENDAR_MONTH =           wx.PyEventBinder( wxEVT_MINI_CALENDAR_MONTH_CHANGED, 1)
EVT_MINI_CALENDAR_YEAR =            wx.PyEventBinder( wxEVT_MINI_CALENDAR_YEAR_CHANGED, 1)
}


//---------------------------------------------------------------------------
MustHaveApp(wxMiniCalendar);

class wxMiniCalendar : public wxControl
{
public:
        %pythonAppend wxMiniCalendar      "self._setOORInfo(self)"
        %pythonAppend wxMiniCalendar()    ""

        wxMiniCalendar(wxWindow *parent,
                       wxWindowID id=-1,
                       const wxDateTime& date = wxDefaultDateTime,
                       const wxPoint& pos = wxDefaultPosition,
                       const wxSize& size = wxDefaultSize,
                       long style = 0,
                       const wxString& name = wxCalendarNameStr);

        // NB: is this proper? What about the dtor?
        %RenameCtor(PreMiniCalendar, wxMiniCalendar());

        void SetDate(const wxDateTime& date);
        const wxDateTime& GetDate() const;
        bool SetLowerDateLimit(const wxDateTime& date = wxDefaultDateTime);
        bool SetUpperDateLimit(const wxDateTime& date = wxDefaultDateTime);
        const wxDateTime& GetLowerDateLimit() const;
        const wxDateTime& GetUpperDateLimit() const;
        bool SetDateRange(const wxDateTime& lowerdate = wxDefaultDateTime,
                           const wxDateTime& upperdate = wxDefaultDateTime);
        void SetHeaderColours(const wxColour& colFg, const wxColour& colBg);
        wxColour GetHeaderColourFg() const;
        wxColour GetHeaderColourBg() const;
        void SetHighlightColours(const wxColour& colFg, const wxColour& colBg);
        wxColour GetHighlightColourFg() const;
        wxColour GetHighlightColourBg() const;
        double GetBusy(int date) const;
        wxMiniCalendarDateAttr* GetAttr(size_t day) const;
        void SetAttr(size_t day, wxMiniCalendarDateAttr *attr);
};

//---------------------------------------------------------------------------

%init %{
%}

//---------------------------------------------------------------------------

