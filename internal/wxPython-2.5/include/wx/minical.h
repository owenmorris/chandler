#ifndef _WX_MINICAL_H_
#define _WX_MINICAL_H_

#include "wx/defs.h"

#if wxUSE_CALENDARCTRL

#include "wx/datetime.h"
#include "wx/colour.h"
#include "wx/font.h"

// ----------------------------------------------------------------------------
// wxMiniCalendar flags
// ----------------------------------------------------------------------------

enum
{
    // show Sunday as the first day of the week (default)
    wxCAL_SUNDAY_FIRST               = 0x0000,

    // show Monder as the first day of the week
    wxCAL_MONDAY_FIRST               = 0x0001,

    // show the neighbouring weeks in the previous and next month
    wxCAL_SHOW_SURROUNDING_WEEKS     = 0x0002,

    // show a preview of events on the selected day
    wxCAL_SHOW_PREVIEW               = 0x0004
};

// ----------------------------------------------------------------------------
// constants
// ----------------------------------------------------------------------------

// return values for the HitTest() method
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

// ----------------------------------------------------------------------------
// wxMiniCalendarData: class to be overridden to provide calendar data
// ----------------------------------------------------------------------------

class WXDLLIMPEXP_ADV wxMiniCalendarData
{
public:
    // ctors
    wxMiniCalendarData() { }

    // setters
    void SetBusy(const double busyPercentage) { m_busy = busyPercentage; }

    // accessors
    const double GetBusy() const { return m_busy; }

private:
    double    m_busy;
};

// ----------------------------------------------------------------------------
// wxMiniCalendarDateAttr: custom attributes for a calendar date
// ----------------------------------------------------------------------------

class WXDLLIMPEXP_ADV wxMiniCalendarDateAttr
{
public:
    // ctors
    wxMiniCalendarDateAttr(double busyPercentage = 0)
    {
        Init(busyPercentage);
    }

    // setters
    void SetBusy(const double busyPercentage) { m_busy = busyPercentage; }

    // accessors
    const double GetBusy() const { return m_busy; }

protected:
    void Init(double busyPercentage = 0)
    {
        m_busy = busyPercentage;
    }

private:
    double    m_busy;
};

// ----------------------------------------------------------------------------
// wxMiniCalendar events
// ----------------------------------------------------------------------------

class WXDLLIMPEXP_ADV wxMiniCalendar;

class WXDLLIMPEXP_ADV wxMiniCalendarEvent : public wxCommandEvent
{
friend class wxMiniCalendar;
public:
    wxMiniCalendarEvent() { Init(); }
    wxMiniCalendarEvent(wxMiniCalendar *cal, wxEventType type);

    const wxDateTime& GetDate() const { return m_date; }
    void SetDate(const wxDateTime &date) { m_date = date; }
    void SetWeekDay(const wxDateTime::WeekDay wd) { m_wday = wd; }
    wxDateTime::WeekDay GetWeekDay() const { return m_wday; }

protected:
    void Init();

private:
    wxDateTime m_date;
    wxDateTime::WeekDay m_wday;

    DECLARE_DYNAMIC_CLASS_NO_COPY(wxMiniCalendarEvent)
};

// ----------------------------------------------------------------------------
// wxMiniCalendar
// ----------------------------------------------------------------------------

// so far we only have a generic version, so keep it simple
#include "wx/generic/minical.h"

// ----------------------------------------------------------------------------
// calendar event types and macros for handling them
// ----------------------------------------------------------------------------

BEGIN_DECLARE_EVENT_TYPES()
    DECLARE_EXPORTED_EVENT_TYPE(WXDLLIMPEXP_ADV, wxEVT_MINI_CALENDAR_SEL_CHANGED, 950)
    DECLARE_EXPORTED_EVENT_TYPE(WXDLLIMPEXP_ADV, wxEVT_MINI_CALENDAR_DAY_CHANGED, 951)
    DECLARE_EXPORTED_EVENT_TYPE(WXDLLIMPEXP_ADV, wxEVT_MINI_CALENDAR_MONTH_CHANGED, 952)
    DECLARE_EXPORTED_EVENT_TYPE(WXDLLIMPEXP_ADV, wxEVT_MINI_CALENDAR_YEAR_CHANGED, 953)
    DECLARE_EXPORTED_EVENT_TYPE(WXDLLIMPEXP_ADV, wxEVT_MINI_CALENDAR_DOUBLECLICKED, 954)
END_DECLARE_EVENT_TYPES()

typedef void (wxEvtHandler::*wxMiniCalendarEventFunction)(wxMiniCalendarEvent&);

#define EVT_MINI_CALENDAR_DOUBLECLICKED(id, fn) DECLARE_EVENT_TABLE_ENTRY(wxEVT_MINI_CALENDAR_DOUBLECLICKED, id, wxID_ANY, (wxObjectEventFunction) (wxEventFunction) (wxCommandEventFunction)  wxStaticCastEvent( wxMiniCalendarEventFunction, & fn ), (wxObject *) NULL),
#define EVT_MINI_CALENDAR_SEL_CHANGED(id, fn) DECLARE_EVENT_TABLE_ENTRY(wxEVT_MINI_CALENDAR_SEL_CHANGED, id, wxID_ANY, (wxObjectEventFunction) (wxEventFunction) (wxCommandEventFunction)  wxStaticCastEvent( wxMiniCalendarEventFunction, & fn ), (wxObject *) NULL),
#define EVT_MINI_CALENDAR_DAY(id, fn) DECLARE_EVENT_TABLE_ENTRY(wxEVT_MINI_CALENDAR_DAY_CHANGED, id, wxID_ANY, (wxObjectEventFunction) (wxEventFunction) (wxCommandEventFunction)  wxStaticCastEvent( wxMiniCalendarEventFunction, & fn ), (wxObject *) NULL),
#define EVT_MINI_CALENDAR_MONTH(id, fn) DECLARE_EVENT_TABLE_ENTRY(wxEVT_MINI_CALENDAR_MONTH_CHANGED, id, wxID_ANY, (wxObjectEventFunction) (wxEventFunction) (wxCommandEventFunction)  wxStaticCastEvent( wxMiniCalendarEventFunction, & fn ), (wxObject *) NULL),
#define EVT_MINI_CALENDAR_YEAR(id, fn) DECLARE_EVENT_TABLE_ENTRY(wxEVT_MINI_CALENDAR_YEAR_CHANGED, id, wxID_ANY, (wxObjectEventFunction) (wxEventFunction) (wxCommandEventFunction)  wxStaticCastEvent( wxMiniCalendarEventFunction, & fn ), (wxObject *) NULL),

#endif // wxUSE_CALENDARCTRL

#endif // _WX_MINICAL_H_

