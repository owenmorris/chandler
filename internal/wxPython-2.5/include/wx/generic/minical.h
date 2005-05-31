#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
    #pragma interface "minical.h"
#endif

#ifndef _WX_GENERIC_MINICAL_H
#define _WX_GENERIC_MINICAL_H

#include "wx/control.h"         // the base class
#include "wx/dcclient.h"        // for wxPaintDC

class WXDLLEXPORT wxStaticText;

#define wxCalendarNameStr _T("MiniCalendar")
#define DAYS_PER_WEEK 7
#define WEEKS_TO_DISPLAY 6
#define NUMBER_TO_PREVIEW 5

// ----------------------------------------------------------------------------
// wxMiniCalendar: a control allowing the user to pick a date interactively
// ----------------------------------------------------------------------------

class WXDLLIMPEXP_ADV wxMiniCalendar : public wxControl
{
public:
    // construction
    wxMiniCalendar() { Init(); }
    wxMiniCalendar(wxWindow *parent,
                   wxWindowID id,
                   const wxDateTime& date = wxDefaultDateTime,
                   const wxPoint& pos = wxDefaultPosition,
                   const wxSize& size = wxDefaultSize,
                   long style = 0,
                   const wxString& name = wxCalendarNameStr);

    bool Create(wxWindow *parent,
                wxWindowID id,
                const wxDateTime& date = wxDefaultDateTime,
                const wxPoint& pos = wxDefaultPosition,
                const wxSize& size = wxDefaultSize,
                long style = 0,
                const wxString& name = wxCalendarNameStr);

    virtual ~wxMiniCalendar();

    virtual bool Destroy();

    // set/get the current date
    // ------------------------

    bool SetDate(const wxDateTime& date); // we need to be able to control if the event should be sent in SetDateAndNotify(...)
    const wxDateTime& GetDate() const { return m_date; }

    // set/get the range in which selection can occur
    // ---------------------------------------------

    bool SetLowerDateLimit(const wxDateTime& date = wxDefaultDateTime);
    const wxDateTime& GetLowerDateLimit() const { return m_lowdate; }
    bool SetUpperDateLimit(const wxDateTime& date = wxDefaultDateTime);
    const wxDateTime& GetUpperDateLimit() const { return m_highdate; }

    bool SetDateRange(const wxDateTime& lowerdate = wxDefaultDateTime, const wxDateTime& upperdate = wxDefaultDateTime);

    // calendar mode
    // -------------

    // some calendar styles can't be changed after the control creation by
    // just using SetWindowStyle() and Refresh() and the functions below
    // should be used instead for them

    // customization
    // -------------

    // header colours are used for painting the weekdays at the top
    void SetHeaderColours(const wxColour& colFg, const wxColour& colBg)
    {
        m_colHeaderFg = colFg;
        m_colHeaderBg = colBg;
    }

    const wxColour& GetHeaderColourFg() const { return m_colHeaderFg; }
    const wxColour& GetHeaderColourBg() const { return m_colHeaderBg; }

    // highlight colour is used for the currently selected date
    void SetHighlightColours(const wxColour& colFg, const wxColour& colBg)
    {
        m_colHighlightFg = colFg;
        m_colHighlightBg = colBg;
    }

    const wxColour& GetHighlightColourFg() const { return m_colHighlightFg; }
    const wxColour& GetHighlightColourBg() const { return m_colHighlightBg; }

    // an item without custom attributes is drawn with the default colours and
    // font and without border, setting custom attributes allows to modify this
    //
    // the dayPosition parameter should be in 1..(DAYS_PER_WEEK * WEEKS_TO_DISPLAY)
    // range.  For days that are not displayed the attribute is just unused

    wxMiniCalendarDateAttr *GetAttr(size_t dayPosition) const
    {
        wxCHECK_MSG( dayPosition > 0 && dayPosition < (DAYS_PER_WEEK * WEEKS_TO_DISPLAY + 1),
                     NULL, _T("invalid day") );

        return m_attrs[dayPosition - 1];
    }

    void SetAttr(size_t dayPosition, wxMiniCalendarDateAttr *attr)
    {
        wxCHECK_RET( dayPosition > 0 && dayPosition < (DAYS_PER_WEEK * WEEKS_TO_DISPLAY + 1),
                     _T("invalid day") );

        delete m_attrs[dayPosition - 1];
        m_attrs[dayPosition - 1] = attr;
    }

    void ResetAttr(size_t dayPosition) { SetAttr(dayPosition, (wxMiniCalendarDateAttr *)NULL); }

    // returns one of wxCAL_HITTEST_XXX constants and fills either date or wd
    // with the corresponding value (none for NOWHERE, the date for DAY and wd
    // for HEADER)
    wxCalendarHitTestResult HitTest(const wxPoint& pos,
                                    wxDateTime *date = NULL,
                                    wxDateTime::WeekDay *wd = NULL);

    // implementation only from now on
    // -------------------------------

    // forward these functions to all subcontrols
    virtual bool Enable(bool enable = true);
    virtual bool Show(bool show = true);

    virtual wxVisualAttributes GetDefaultAttributes() const
        { return GetClassDefaultAttributes(GetWindowVariant()); }

    static wxVisualAttributes
    GetClassDefaultAttributes(wxWindowVariant variant = wxWINDOW_VARIANT_NORMAL);

private:
    // common part of all ctors
    void Init();

    // event handlers
    void OnPaint(wxPaintEvent& event);
    void OnClick(wxMouseEvent& event);
    void OnDClick(wxMouseEvent& event);

    // override some base class virtuals
    virtual wxSize DoGetBestSize() const;
    virtual void DoGetPosition(int *x, int *y) const;
    virtual void DoGetSize(int *width, int *height) const;
    virtual void DoSetSize(int x, int y, int width, int height, int sizeFlags);
    virtual void DoMoveWindow(int x, int y, int width, int height);

    // (re)calc m_widthCol and m_heightRow
    void RecalcGeometry();

    // set the date and send the notification
    void SetDateAndNotify(const wxDateTime& date);

    // get the week (row, in range 1..WEEKS_TO_DISPLAY) for the given date
    size_t GetWeek(const wxDateTime& date) const;

    // get the date from which we start drawing days
    wxDateTime GetStartDate() const;

    // is this date shown?
    bool IsDateShown(const wxDateTime& date) const;

    // is this date in the given range?
    bool IsDateInRange(const wxDateTime& date) const;

    // redraw the given date
    void RefreshDate(const wxDateTime& date);

    // change the date inside the same month/year
    void ChangeDay(const wxDateTime& date);

    // generate the given calendar event(s)
    void GenerateEvent(wxEventType type)
    {
        wxMiniCalendarEvent event(this, type);
        (void)GetEventHandler()->ProcessEvent(event);
    }

    void GenerateEvents(wxEventType type1, wxEventType type2)
    {
        GenerateEvent(type1);
        GenerateEvent(type2);
    }

    // show the correct controls
    void ShowCurrentControls();

public:
    // get the currently shown control for month/year
    wxControl *GetMonthControl() const;
    wxControl *GetYearControl() const;

private:
    // OnPaint helper-methods

    // Highlight the [fromdate : todate] range using pen and brush
    void HighlightRange(wxPaintDC* dc, const wxDateTime& fromdate, const wxDateTime& todate, wxPen* pen, wxBrush* brush);

    // Get the "coordinates" for the date relative to the month currently displayed.
    // using (day, week): upper left coord is (1, 1), lower right coord is (7, 6)
    // if the date isn't visible (-1, -1) is put in (day, week) and false is returned
    bool GetDateCoord(const wxDateTime& date, int *day, int *week) const;

    // the subcontrols
    wxStaticText *m_staticMonth;
    wxStaticText *m_staticYear;

    // the current selection
    wxDateTime m_date;

    // the date-range
    wxDateTime m_lowdate;
    wxDateTime m_highdate;

    // default attributes
    wxColour m_colHighlightFg,
             m_colHighlightBg,
             m_colHeaderFg,
             m_colHeaderBg;

    // the attributes for each of the displayed days
    wxMiniCalendarDateAttr *m_attrs[DAYS_PER_WEEK * WEEKS_TO_DISPLAY];

    // the width and height of one column/row in the calendar
    wxCoord m_widthCol,
            m_heightRow,
            m_rowOffset,
            m_todayHeight,
            m_heightPreview;

    wxRect m_leftArrowRect,
           m_rightArrowRect,
           m_todayRect;

    // the week day names
    wxString m_weekdays[DAYS_PER_WEEK];

    // fonts
    wxFont m_normalFont,
           m_boldFont;

    // true if SetDate() is being called as the result of changing the year in
    // the year control
    bool m_userChangedYear;

    DECLARE_DYNAMIC_CLASS(wxMiniCalendar)
    DECLARE_EVENT_TABLE()
    DECLARE_NO_COPY_CLASS(wxMiniCalendar)
};

#endif // _WX_GENERIC_MINICAL_H
