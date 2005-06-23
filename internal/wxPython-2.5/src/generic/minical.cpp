// ============================================================================
// declarations
// ============================================================================

// ----------------------------------------------------------------------------
// headers
// ----------------------------------------------------------------------------

#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
    #pragma implementation "minical.h"
#endif

// For compilers that support precompilation, includes "wx.h".
#include "wx/wxprec.h"

#ifdef __BORLANDC__
    #pragma hdrstop
#endif

#ifndef WX_PRECOMP
    #include "wx/dcclient.h"
    #include "wx/settings.h"
    #include "wx/brush.h"
    #include "wx/listbox.h"
    #include "wx/stattext.h"
    #include "wx/textctrl.h"
#endif //WX_PRECOMP

#if wxUSE_CALENDARCTRL

#include "wx/minical.h"

// ----------------------------------------------------------------------------
// wxWin macros
// ----------------------------------------------------------------------------

BEGIN_EVENT_TABLE(wxMiniCalendar, wxControl)
    EVT_PAINT(wxMiniCalendar::OnPaint)

    EVT_LEFT_DOWN(wxMiniCalendar::OnClick)
    EVT_LEFT_DCLICK(wxMiniCalendar::OnDClick)
END_EVENT_TABLE()

#if wxUSE_EXTENDED_RTTI
WX_DEFINE_FLAGS( wxMiniCalendarStyle )

wxBEGIN_FLAGS( wxMiniCalendarStyle )
    // new style border flags, we put them first to
    // use them for streaming out
    wxFLAGS_MEMBER(wxBORDER_SIMPLE)
    wxFLAGS_MEMBER(wxBORDER_SUNKEN)
    wxFLAGS_MEMBER(wxBORDER_DOUBLE)
    wxFLAGS_MEMBER(wxBORDER_RAISED)
    wxFLAGS_MEMBER(wxBORDER_STATIC)
    wxFLAGS_MEMBER(wxBORDER_NONE)

    // old style border flags
    wxFLAGS_MEMBER(wxSIMPLE_BORDER)
    wxFLAGS_MEMBER(wxSUNKEN_BORDER)
    wxFLAGS_MEMBER(wxDOUBLE_BORDER)
    wxFLAGS_MEMBER(wxRAISED_BORDER)
    wxFLAGS_MEMBER(wxSTATIC_BORDER)
    wxFLAGS_MEMBER(wxBORDER)

    // standard window styles
    wxFLAGS_MEMBER(wxTAB_TRAVERSAL)
    wxFLAGS_MEMBER(wxCLIP_CHILDREN)
    wxFLAGS_MEMBER(wxTRANSPARENT_WINDOW)
    wxFLAGS_MEMBER(wxFULL_REPAINT_ON_RESIZE)
    wxFLAGS_MEMBER(wxALWAYS_SHOW_SB )
    wxFLAGS_MEMBER(wxVSCROLL)
    wxFLAGS_MEMBER(wxHSCROLL)

    wxFLAGS_MEMBER(wxCAL_SUNDAY_FIRST)
    wxFLAGS_MEMBER(wxCAL_MONDAY_FIRST)
    wxFLAGS_MEMBER(wxCAL_SHOW_SURROUNDING_WEEKS)
    wxFLAGS_MEMBER(wxCAL_SHOW_PREVIEW)
    wxFLAGS_MEMBER(wxCAL_HIGHLIGHT_WEEK)

wxEND_FLAGS( wxMiniCalendarStyle )

IMPLEMENT_DYNAMIC_CLASS_XTI(wxMiniCalendar, wxControl,"wx/minical.h")

wxBEGIN_PROPERTIES_TABLE(wxMiniCalendar)
    wxEVENT_RANGE_PROPERTY( Updated , wxEVT_MINI_CALENDAR_SEL_CHANGED , wxEVT_MINI_CALENDAR_DOUBLECLICKED , wxMiniCalendarEvent )
    wxHIDE_PROPERTY( Children )
    wxPROPERTY( Date,wxDateTime, SetDate , GetDate, , 0 /*flags*/ , wxT("Helpstring") , wxT("group"))
    wxPROPERTY_FLAGS( WindowStyle , wxMiniCalendarStyle , long , SetWindowStyleFlag , GetWindowStyleFlag , , 0 /*flags*/ , wxT("Helpstring") , wxT("group")) // style
wxEND_PROPERTIES_TABLE()

wxBEGIN_HANDLERS_TABLE(wxMiniCalendar)
wxEND_HANDLERS_TABLE()

wxCONSTRUCTOR_6( wxMiniCalendar , wxWindow* , Parent , wxWindowID , Id , wxDateTime , Date , wxPoint , Position , wxSize , Size , long , WindowStyle )
#else
IMPLEMENT_DYNAMIC_CLASS(wxMiniCalendar, wxControl)
#endif
IMPLEMENT_DYNAMIC_CLASS(wxMiniCalendarEvent, wxCommandEvent)

// ----------------------------------------------------------------------------
// events
// ----------------------------------------------------------------------------

DEFINE_EVENT_TYPE(wxEVT_MINI_CALENDAR_SEL_CHANGED)
DEFINE_EVENT_TYPE(wxEVT_MINI_CALENDAR_DAY_CHANGED)
DEFINE_EVENT_TYPE(wxEVT_MINI_CALENDAR_MONTH_CHANGED)
DEFINE_EVENT_TYPE(wxEVT_MINI_CALENDAR_YEAR_CHANGED)
DEFINE_EVENT_TYPE(wxEVT_MINI_CALENDAR_DOUBLECLICKED)

// ============================================================================
// implementation
// ============================================================================

// ----------------------------------------------------------------------------
// wxMiniCalendar
// ----------------------------------------------------------------------------

wxMiniCalendar::wxMiniCalendar(wxWindow *parent,
                   wxWindowID id,
                   const wxDateTime& date,
                   const wxPoint& pos,
                   const wxSize& size,
                   long style,
                   const wxString& name)
{
    Init();

    (void)Create(parent, id, date, pos, size, style, name);
}


void wxMiniCalendar::Init()
{
    m_staticYear = NULL;
    m_staticMonth = NULL;

    m_userChangedYear = false;

    m_widthCol = 0;
    m_heightRow = 0;
    m_todayHeight = 0;

    wxDateTime::WeekDay wd;
    for ( wd = wxDateTime::Sun; wd < wxDateTime::Inv_WeekDay; wxNextWDay(wd) )
    {
        m_weekdays[wd] = wxDateTime::GetWeekDayName(wd, wxDateTime::Name_Abbr).GetChar(0);
    }

    for ( size_t n = 0; n < WXSIZEOF(m_attrs); n++ )
    {
        m_attrs[n] = NULL;
    }

    m_colHighlightFg = wxSystemSettings::GetColour(wxSYS_COLOUR_HIGHLIGHTTEXT);
    m_colHighlightBg = wxSystemSettings::GetColour(wxSYS_COLOUR_HIGHLIGHT);

    m_colHeaderFg = *wxBLACK;
    m_colHeaderBg = *wxWHITE; 
}

bool wxMiniCalendar::Create(wxWindow *parent,
                            wxWindowID id,
                            const wxDateTime& date,
                            const wxPoint& pos,
                            const wxSize& size,
                            long style,
                            const wxString& name)
{
    if ( !wxControl::Create(parent, id, pos, size,
                            style | wxCLIP_CHILDREN,
                            wxDefaultValidator, name) )
    {
        return false;
    }

    // needed to get the arrow keys normally used for the dialog navigation
    SetWindowStyle(style);

    m_date = date.IsValid() ? date : wxDateTime::Today();

    m_lowdate = wxDefaultDateTime;
    m_highdate = wxDefaultDateTime;

    ShowCurrentControls();

    // we need to set the position as well because the main control position
    // is not the same as the one specified in pos if we have the controls
    // above it
    SetBestSize(size);
    SetPosition(pos);

    // Since we don't paint the whole background make sure that the platform
    // will use the right one.
    SetBackgroundColour(GetBackgroundColour());
    
    return true;
}

wxMiniCalendar::~wxMiniCalendar()
{
    for ( size_t n = 0; n < WXSIZEOF(m_attrs); n++ )
    {
        delete m_attrs[n];
    }
}

// ----------------------------------------------------------------------------
// forward wxWin functions to subcontrols
// ----------------------------------------------------------------------------

bool wxMiniCalendar::Destroy()
{
    if ( m_staticYear )
        m_staticYear->Destroy();
    if ( m_staticMonth )
        m_staticMonth->Destroy();

    m_staticYear = NULL;
    m_staticMonth = NULL;

    return wxControl::Destroy();
}

bool wxMiniCalendar::Show(bool show)
{
    if ( !wxControl::Show(show) )
    {
        return false;
    }

    if ( GetMonthControl() )
    {
        GetMonthControl()->Show(show);
        GetYearControl()->Show(show);
    }

    return true;
}

bool wxMiniCalendar::Enable(bool enable)
{
    if ( !wxControl::Enable(enable) )
    {
        return false;
    }

    GetMonthControl()->Enable(enable);
    GetYearControl()->Enable(enable);

    return true;
}

// ----------------------------------------------------------------------------
// enable/disable month/year controls
// ----------------------------------------------------------------------------

void wxMiniCalendar::ShowCurrentControls()
{
}

wxControl *wxMiniCalendar::GetMonthControl() const
{
    return (wxControl *)m_staticMonth;
}

wxControl *wxMiniCalendar::GetYearControl() const
{
    return (wxControl *)m_staticYear;
}

// ----------------------------------------------------------------------------
// changing date
// ----------------------------------------------------------------------------

bool wxMiniCalendar::SetDate(const wxDateTime& date)
{
    bool retval = true;

    bool sameMonth = m_date.GetMonth() == date.GetMonth(),
         sameYear = m_date.GetYear() == date.GetYear();

    if ( IsDateInRange(date) )
    {
        if ( sameMonth && sameYear )
        {
            // just change the day
            ChangeDay(date);
        }
        else
        {
            // change everything
            m_date = date;

            // update the calendar
            Refresh();
        }
    }

    m_userChangedYear = false;

    return retval;
}

void wxMiniCalendar::ChangeDay(const wxDateTime& date)
{
    if ( m_date != date )
    {
        // we need to refresh the row containing the old date and the one
        // containing the new one
        wxDateTime dateOld = m_date;
        m_date = date;

        RefreshDate(dateOld);

        // if the date is in the same row, it was already drawn correctly
        if ( GetWeek(m_date) != GetWeek(dateOld) )
        {
            RefreshDate(m_date);
        }
    }
}

void wxMiniCalendar::SetDateAndNotify(const wxDateTime& date)
{
    wxDateTime::Tm tm1 = m_date.GetTm(),
                   tm2 = date.GetTm();

    wxEventType type;
    if ( tm1.year != tm2.year )
        type = wxEVT_MINI_CALENDAR_YEAR_CHANGED;
    else if ( tm1.mon != tm2.mon )
        type = wxEVT_MINI_CALENDAR_MONTH_CHANGED;
    else if ( tm1.mday != tm2.mday )
        type = wxEVT_MINI_CALENDAR_DAY_CHANGED;
    else
        return;

    if ( SetDate(date) )
    {
        GenerateEvents(type, wxEVT_MINI_CALENDAR_SEL_CHANGED);
    }
}

// ----------------------------------------------------------------------------
// date range
// ----------------------------------------------------------------------------

bool wxMiniCalendar::SetLowerDateLimit(const wxDateTime& date /* = wxDefaultDateTime */)
{
    bool retval = true;

    if ( !(date.IsValid()) || ( ( m_highdate.IsValid() ) ? ( date <= m_highdate ) : true ) )
    {
        m_lowdate = date;
    }
    else
    {
        retval = false;
    }

    return retval;
}

bool wxMiniCalendar::SetUpperDateLimit(const wxDateTime& date /* = wxDefaultDateTime */)
{
    bool retval = true;

    if ( !(date.IsValid()) || ( ( m_lowdate.IsValid() ) ? ( date >= m_lowdate ) : true ) )
    {
        m_highdate = date;
    }
    else
    {
        retval = false;
    }

    return retval;
}

bool wxMiniCalendar::SetDateRange(const wxDateTime& lowerdate /* = wxDefaultDateTime */, const wxDateTime& upperdate /* = wxDefaultDateTime */)
{
    bool retval = true;

    if (
        ( !( lowerdate.IsValid() ) || ( ( upperdate.IsValid() ) ? ( lowerdate <= upperdate ) : true ) ) &&
        ( !( upperdate.IsValid() ) || ( ( lowerdate.IsValid() ) ? ( upperdate >= lowerdate ) : true ) ) )
    {
        m_lowdate = lowerdate;
        m_highdate = upperdate;
    }
    else
    {
        retval = false;
    }

    return retval;
}

// ----------------------------------------------------------------------------
// date helpers
// ----------------------------------------------------------------------------

wxDateTime wxMiniCalendar::GetStartDate() const
{
    wxDateTime::Tm tm = m_date.GetTm();

    wxDateTime date = wxDateTime(1, tm.mon, tm.year);

    // rewind back
    date.SetToPrevWeekDay(GetWindowStyle() & wxCAL_MONDAY_FIRST
                          ? wxDateTime::Mon : wxDateTime::Sun);

    return date;
}

bool wxMiniCalendar::IsDateShown(const wxDateTime& date) const
{
    if ( !(GetWindowStyle() & wxCAL_SHOW_SURROUNDING_WEEKS) )
    {
        return date.GetMonth() == m_date.GetMonth();
    }
    else
    {
        return true;
    }
}

bool wxMiniCalendar::IsDateInRange(const wxDateTime& date) const
{
    // Check if the given date is in the range specified
    return ( ( ( m_lowdate.IsValid() ) ? ( date >= m_lowdate ) : true )
        && ( ( m_highdate.IsValid() ) ? ( date <= m_highdate ) : true ) );
}

size_t wxMiniCalendar::GetWeek(const wxDateTime& date, bool useRelative) const
{
    size_t retval;
    if ( useRelative )
    {
        retval = date.GetWeekOfMonth(GetWindowStyle() & wxCAL_MONDAY_FIRST
                                   ? wxDateTime::Monday_First
                                   : wxDateTime::Sunday_First);
    }
    else
    {
        retval = date.GetWeekOfYear(GetWindowStyle() & wxCAL_MONDAY_FIRST
                                   ? wxDateTime::Monday_First
                                   : wxDateTime::Sunday_First);
    }
    return retval;
}

// ----------------------------------------------------------------------------
// size management
// ----------------------------------------------------------------------------

// the constants used for the layout
#define VERT_MARGIN     5
#ifdef __WXMAC__
#define HORZ_MARGIN    5
#else
#define HORZ_MARGIN    15
#endif
#define EXTRA_MONTH_HEIGHT    5
#define SEPARATOR_MARGIN      3
wxSize wxMiniCalendar::DoGetBestSize() const
{
    // calc the size of the calendar
    ((wxMiniCalendar *)this)->RecalcGeometry(); // const_cast

    wxCoord width = DAYS_PER_WEEK * m_widthCol,
            height = m_todayHeight + m_heightPreview + VERT_MARGIN +
            MONTHS_TO_DISPLAY * ( WEEKS_TO_DISPLAY * m_heightRow + m_rowOffset + EXTRA_MONTH_HEIGHT );

    if ( !HasFlag(wxBORDER_NONE) )
    {
        // the border would clip the last line otherwise
        height += 6;
        width += 4;
    }

    wxSize best(width, height);
    CacheBestSize(best);
    return best;   
}

void wxMiniCalendar::DoSetSize(int x, int y,
                               int width, int height,
                               int sizeFlags)
{
    wxControl::DoSetSize(x, y, width, height, sizeFlags);
}

void wxMiniCalendar::DoMoveWindow(int x, int y, int width, int height)
{
    int yDiff;

    yDiff = 0;

    wxControl::DoMoveWindow(x, y + yDiff, width, height - yDiff);
}

void wxMiniCalendar::DoGetPosition(int *x, int *y) const
{
    wxControl::DoGetPosition(x, y);
}

void wxMiniCalendar::DoGetSize(int *width, int *height) const
{
    wxControl::DoGetSize(width, height);
}

void wxMiniCalendar::RecalcGeometry()
{
    wxClientDC dc(this);

    dc.SetFont(GetFont());

    // determine the column width (we assume that the widest digit plus busy 
    // bar is wider than any weekday character (hopefully in any language))
    m_widthCol = 0;
    unsigned int day;

    for ( day = 1; day < 32; day++ )
    {
        wxCoord width;
        wxString dayStr = wxString::Format(_T("%u"), day);
        dc.GetTextExtent(dayStr, &width, &m_heightRow);
        if ( width > m_widthCol )
        {
            m_widthCol = width;
        }

    }

    // leave some margins
    m_widthCol += 8;
    m_heightRow += 4;
    if ( (GetWindowStyle() & wxCAL_SHOW_PREVIEW) != 0 )
    {
        m_heightPreview = NUMBER_TO_PREVIEW * m_heightRow;
    }
    else
    {
        m_heightPreview = 0;
    }

    m_rowOffset = m_heightRow * 2;
}

// ----------------------------------------------------------------------------
// drawing
// ----------------------------------------------------------------------------

void wxMiniCalendar::OnPaint(wxPaintEvent& WXUNUSED(event))
{
    wxPaintDC dc(this);

    dc.SetFont(GetFont());

    RecalcGeometry();

    wxCoord y = 0;

    // draw the preview portion
    y += m_heightPreview;

    // draw the sequential month-selector
    m_todayHeight = m_heightRow + 2;

    dc.SetBackgroundMode(wxTRANSPARENT);
    dc.SetTextForeground(*wxBLACK);
    dc.SetBrush(*wxTRANSPARENT_BRUSH);
    dc.SetPen(wxPen(*wxLIGHT_GREY, 1, wxSOLID));
    dc.DrawLine(0, y, GetClientSize().x, y);
    dc.DrawLine(0, y + m_todayHeight, GetClientSize().x, y + m_todayHeight);
    wxCoord buttonCoord = GetClientSize().x / 5;
    dc.DrawLine(buttonCoord, y, buttonCoord, y + m_todayHeight);
    dc.DrawLine(buttonCoord * 4, y, buttonCoord * 4, y + m_todayHeight);

    // Get extent of today button
    wxCoord todayw, todayh;
    m_normalFont = dc.GetFont();
    m_boldFont = wxFont(m_normalFont.GetPointSize(), m_normalFont.GetFamily(),
        m_normalFont.GetStyle(), wxBOLD, m_normalFont.GetUnderlined(), 
        m_normalFont.GetFaceName(), m_normalFont.GetEncoding());
    dc.SetFont(m_boldFont);
    wxString todaytext = wxT("Today");
    dc.GetTextExtent(todaytext, &todayw, &todayh);

    m_todayRect = wxRect(0, 0, 0, 0);

    // Draw today button
    m_todayRect = wxRect(buttonCoord, y, buttonCoord * 4, m_todayHeight);
    wxCoord todayx = ((m_widthCol * DAYS_PER_WEEK) - todayw) / 2;
    wxCoord todayy = ((m_todayHeight - todayh) / 2) + y;
    dc.DrawText(todaytext, todayx, todayy);
    dc.SetFont(m_normalFont);

    // calculate the "month-arrows"
    wxPoint leftarrow[3];
    wxPoint rightarrow[3];

    int arrowheight = todayh - 5;

    leftarrow[0] = wxPoint(0, arrowheight / 2);
    leftarrow[1] = wxPoint(arrowheight / 2, 0);
    leftarrow[2] = wxPoint(arrowheight / 2, arrowheight - 1);

    rightarrow[0] = wxPoint(0, 0);
    rightarrow[1] = wxPoint(arrowheight / 2, arrowheight / 2);
    rightarrow[2] = wxPoint(0, arrowheight - 1);

    // draw the "month-arrows"
    wxCoord arrowy = (m_todayHeight - arrowheight) / 2 + y;
    wxCoord larrowx = (buttonCoord - (arrowheight / 2)) / 2;
    wxCoord rarrowx = (buttonCoord / 2) + buttonCoord * 4;
    m_leftArrowRect = wxRect(0, 0, 0, 0);
    m_rightArrowRect = wxRect(0, 0, 0, 0);

    // Draw left arrow
    m_leftArrowRect = wxRect(0, y, buttonCoord - 1, m_todayHeight);
    dc.SetBrush(wxBrush(*wxBLACK, wxSOLID));
    dc.SetPen(wxPen(*wxBLACK, 1, wxSOLID));
    dc.DrawPolygon(3, leftarrow, larrowx , arrowy, wxWINDING_RULE);
    dc.SetBrush(*wxTRANSPARENT_BRUSH);

    // Draw right arrow
    m_rightArrowRect = wxRect(buttonCoord * 4 + 1, y, buttonCoord - 1, m_todayHeight);
    dc.SetBrush(wxBrush(*wxBLACK, wxSOLID));
    dc.SetPen(wxPen(*wxBLACK, 1, wxSOLID));
    dc.DrawPolygon(3, rightarrow, rarrowx , arrowy, wxWINDING_RULE);
    dc.SetBrush(*wxTRANSPARENT_BRUSH);

    y += m_todayHeight;


    wxDateTime dateToDraw = m_date;
    int i;
    for (i = 0; i < MONTHS_TO_DISPLAY; i++) {
        DrawMonth(dc, dateToDraw, &y, i == 0);
        dateToDraw += wxDateSpan::Month();
    }
}

void wxMiniCalendar::DrawMonth(wxPaintDC& dc, wxDateTime startDate, wxCoord *y, bool highlightDay)
{
    dc.SetTextForeground(*wxBLACK);
    // Get extent of month-name + year
    wxCoord monthw, monthh;
    wxString headertext = startDate.Format(wxT("%B %Y"));
    dc.SetFont(m_boldFont);
    dc.GetTextExtent(headertext, &monthw, &monthh);

    // draw month-name centered above weekdays
    wxCoord monthx = ((m_widthCol * DAYS_PER_WEEK) - monthw) / 2;
    wxCoord monthy = ((m_heightRow - monthh) / 2) + *y + 3;
    dc.DrawText(headertext, monthx,  monthy);
    dc.SetFont(m_normalFont);

    *y += m_heightRow + EXTRA_MONTH_HEIGHT;

    // first draw the week days
    if ( IsExposed(0, *y, DAYS_PER_WEEK * m_widthCol, m_heightRow) )
    {
        dc.SetBackgroundMode(wxTRANSPARENT);
        dc.SetTextForeground(m_colHeaderFg);
        dc.SetBrush(wxBrush(m_colHeaderBg, wxSOLID));
        dc.SetPen(wxPen(m_colHeaderBg, 1, wxSOLID));
        dc.DrawRectangle(0, *y, GetClientSize().x, m_heightRow);

        bool startOnMonday = (GetWindowStyle() & wxCAL_MONDAY_FIRST) != 0;
        for ( size_t wd = 0; wd < DAYS_PER_WEEK; wd++ )
        {
            size_t n;
            if ( startOnMonday )
                n = wd == (DAYS_PER_WEEK - 1) ? 0 : wd + 1;
            else
                n = wd;
            wxCoord dayw, dayh;
            dc.GetTextExtent(m_weekdays[n], &dayw, &dayh);
            dc.DrawText(m_weekdays[n], (wd*m_widthCol) + ((m_widthCol- dayw) / 2), *y); // center the day-name
        }
    }

    *y += m_heightRow;
    wxDateTime::Tm tm = startDate.GetTm();
    wxDateTime date = wxDateTime(1, tm.mon, tm.year);
    date.SetToPrevWeekDay(GetWindowStyle() & wxCAL_MONDAY_FIRST
        ? wxDateTime::Mon : wxDateTime::Sun);

    dc.SetBackgroundMode(wxSOLID);

    int dayPosition;
    wxColour mainColour = wxColour(128, 128, 128);
    wxColour lightColour = wxColour(191, 191, 191);
    wxColour highlightColour = wxColour(204, 204, 204);
    wxColour lineColour = wxColour(229, 229, 229);

    dc.SetTextForeground(mainColour);
    for ( size_t nWeek = 1; nWeek <= WEEKS_TO_DISPLAY; nWeek++, *y += m_heightRow )
    {
        // if the update region doesn't intersect this row, don't paint it
        if ( !IsExposed(0, *y, DAYS_PER_WEEK * m_widthCol, m_heightRow - 1) )
        {
            date += wxDateSpan::Week();
            continue;
        }

        // don't draw last week if none of the days appear in the month
        if ( nWeek == WEEKS_TO_DISPLAY && (date.GetMonth() != startDate.GetMonth() || !IsDateInRange(date)) )
        {
            date += wxDateSpan::Week();
            continue;
        }

        for ( size_t wd = 0; wd < DAYS_PER_WEEK; wd++ )
        {
            dayPosition = (nWeek - 1) * DAYS_PER_WEEK + wd;
            if ( IsDateShown(date) )
            {
                // don't use wxDate::Format() which prepends 0s
                unsigned int day = date.GetDay();
                wxString dayStr = wxString::Format(_T("%u"), day);
                wxCoord width;
                dc.GetTextExtent(dayStr, &width, (wxCoord *)NULL);

                bool changedColours = false,
                     changedFont = false;

                wxMiniCalendarDateAttr *attr = NULL;
                wxCoord x = wd * m_widthCol + (m_widthCol - width) / 2;

                if ( highlightDay )
                {
                // either highlight the selected week or the selected day depending upon the style
                    if ( ( ( (GetWindowStyle() & wxCAL_HIGHLIGHT_WEEK) != 0 ) && ( GetWeek(date, false) == GetWeek(startDate, false) ) ) ||
                        ( ( (GetWindowStyle() & wxCAL_HIGHLIGHT_WEEK) == 0 ) && ( date.IsSameDate(startDate) ) ) )
                    {
                        dc.SetTextBackground(highlightColour);
                        dc.SetBrush(wxBrush(highlightColour, wxSOLID));
                        dc.SetPen(wxPen(highlightColour, 1, wxSOLID));
                        dc.DrawRectangle(wd * m_widthCol, *y, m_widthCol, m_heightRow);
    
                        changedColours = true;
                    }
                }

                
                if ( date.GetMonth() != startDate.GetMonth() || !IsDateInRange(date) )
                {
                    // surrounding week or out-of-range
                    // draw "disabled"
                    dc.SetTextForeground(lightColour);
                    changedColours = true;
                }
                else
                {
                    attr = m_attrs[dayPosition];

                    dc.SetBrush(wxBrush(*wxBLACK, wxSOLID));
                    dc.SetPen(wxPen(*wxBLACK, 1, wxSOLID));

                    // today should be printed as bold
                    if ( date.IsSameDate(wxDateTime::Today()) )
                    {
                        dc.SetFont(m_boldFont);
                        dc.SetTextForeground(*wxBLACK);
                        changedFont = true;
                        changedColours = true;
                    }
                }

                dc.DrawText(dayStr, x, *y + 1);

                // draw free/busy indicator
                if ( attr )
                {
                    double height = (m_heightRow - 6) * attr->GetBusy();
                    dc.DrawRectangle(x-2, *y + (m_heightRow - (int)height - 3), 2, (int)height);                                
                }

                dc.SetBrush(*wxTRANSPARENT_BRUSH);

                if ( changedColours )
                {
                    dc.SetTextForeground(mainColour);
                    dc.SetTextBackground(GetBackgroundColour());
                }

                if ( changedFont )
                {
                    dc.SetFont(m_normalFont);
                }
            }
            //else: just don't draw it
            date += wxDateSpan::Day();
        }

        // draw lines between each set of weeks
        if ( nWeek != WEEKS_TO_DISPLAY && nWeek != 1)
        {
            dc.SetPen(wxPen(lineColour, 1, wxSOLID));
            dc.DrawLine(SEPARATOR_MARGIN, *y - 1,  DAYS_PER_WEEK * m_widthCol - SEPARATOR_MARGIN, *y - 1);
        }
    }
}

void wxMiniCalendar::RefreshDate(const wxDateTime& date)
{
    RecalcGeometry();

    wxRect rect;

    // always refresh the whole row at once because our OnPaint() will draw
    // the whole row anyhow - and this allows the small optimisation in
    // OnClick() below to work
    rect.x = 0;

    rect.y = (m_heightRow * (GetWeek(date) - 1)) + m_todayHeight + EXTRA_MONTH_HEIGHT + m_rowOffset + m_heightPreview;

    rect.width = DAYS_PER_WEEK * m_widthCol;
    rect.height = m_heightRow;

#ifdef __WXMSW__
    // VZ: for some reason, the selected date seems to occupy more space under
    //     MSW - this is probably some bug in the font size calculations, but I
    //     don't know where exactly. This fix is ugly and leads to more
    //     refreshes than really needed, but without it the selected days
    //     leaves even more ugly underscores on screen.
    rect.Inflate(0, 1);
#endif // MSW

    Refresh(true, &rect);
}

void wxMiniCalendar::HighlightRange(wxPaintDC* pDC, const wxDateTime& fromdate, const wxDateTime& todate, wxPen* pPen, wxBrush* pBrush)
{
    // Highlights the given range using pen and brush
    // Does nothing if todate < fromdate

    if ( todate >= fromdate )
    {
        // do stuff
        // date-coordinates
        int fd, fw;
        int td, tw;

        // implicit: both dates must be currently shown - checked by GetDateCoord
        if ( GetDateCoord(fromdate, &fd, &fw) && GetDateCoord(todate, &td, &tw) )
        {
            if ( ( (tw - fw) == 1 ) && ( td < fd ) )
            {
                // special case: interval 7 days or less not in same week
                // split in two seperate intervals
                wxDateTime tfd = fromdate + wxDateSpan::Days(DAYS_PER_WEEK - fd);
                wxDateTime ftd = tfd + wxDateSpan::Day();
                // draw seperately
                HighlightRange(pDC, fromdate, tfd, pPen, pBrush);
                HighlightRange(pDC, ftd, todate, pPen, pBrush);
            }
            else
            {
                int numpoints;
                wxPoint corners[8]; // potentially 8 corners in polygon

                if ( fw == tw )
                {
                    // simple case: same week
                    numpoints = 4;
                    corners[0] = wxPoint((fd - 1) * m_widthCol, (fw * m_heightRow) + m_rowOffset + m_heightPreview);
                    corners[1] = wxPoint((fd - 1) * m_widthCol, ((fw + 1 ) * m_heightRow) + m_rowOffset + m_heightPreview);
                    corners[2] = wxPoint(td * m_widthCol, ((tw + 1) * m_heightRow) + m_rowOffset + m_heightPreview);
                    corners[3] = wxPoint(td * m_widthCol, (tw * m_heightRow) + m_rowOffset + m_heightPreview);
                }
                else
                {
                    int cidx = 0;
                    // "complex" polygon
                    corners[cidx] = wxPoint((fd - 1) * m_widthCol, (fw * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;

                    if ( fd > 1 )
                    {
                        corners[cidx] = wxPoint((fd - 1) * m_widthCol, ((fw + 1) * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;
                        corners[cidx] = wxPoint(0, ((fw + 1) * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;
                    }

                    corners[cidx] = wxPoint(0, ((tw + 1) * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;
                    corners[cidx] = wxPoint(td * m_widthCol, ((tw + 1) * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;

                    if ( td < DAYS_PER_WEEK )
                    {
                        corners[cidx] = wxPoint(td * m_widthCol, (tw * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;
                        corners[cidx] = wxPoint(DAYS_PER_WEEK * m_widthCol, (tw * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;
                    }

                    corners[cidx] = wxPoint(DAYS_PER_WEEK * m_widthCol, (fw * m_heightRow) + m_rowOffset + m_heightPreview); cidx++;

                    numpoints = cidx;
                }

                // draw the polygon
                pDC->SetBrush(*pBrush);
                pDC->SetPen(*pPen);
                pDC->DrawPolygon(numpoints, corners);
            }
        }
    }
    // else do nothing
}

bool wxMiniCalendar::GetDateCoord(const wxDateTime& date, int *day, int *week) const
{
    bool retval = true;

    if ( IsDateShown(date) )
    {
        bool startOnMonday = ( GetWindowStyle() & wxCAL_MONDAY_FIRST ) != 0;

        // Find day
        *day = date.GetWeekDay();

        if ( *day == 0 ) // sunday
        {
            *day = ( startOnMonday ) ? DAYS_PER_WEEK : 1;
        }
        else
        {
            *day += ( startOnMonday ) ? 0 : 1;
        }

        int targetmonth = date.GetMonth() + (12 * date.GetYear());
        int thismonth = m_date.GetMonth() + (12 * m_date.GetYear());

        // Find week
        if ( targetmonth == thismonth )
        {
            *week = GetWeek(date);
        }
        else
        {
            if ( targetmonth < thismonth )
            {
                *week = 1; // trivial
            }
            else // targetmonth > thismonth
            {
                wxDateTime ldcm;
                int lastweek;
                int lastday;

                // get the datecoord of the last day in the month currently shown
                GetDateCoord(ldcm.SetToLastMonthDay(m_date.GetMonth(), m_date.GetYear()), &lastday, &lastweek);

                wxTimeSpan span = date - ldcm;

                int daysfromlast = span.GetDays();
                if ( daysfromlast + lastday > DAYS_PER_WEEK ) // past week boundary
                {
                    int wholeweeks = (daysfromlast / DAYS_PER_WEEK);
                    *week = wholeweeks + lastweek;
                    if ( (daysfromlast - (DAYS_PER_WEEK * wholeweeks) + lastday) > DAYS_PER_WEEK )
                    {
                        *week += 1;
                    }
                }
                else
                {
                    *week = lastweek;
                }
            }
        }
    }
    else
    {
        *day = -1;
        *week = -1;
        retval = false;
    }

    return retval;
}

// ----------------------------------------------------------------------------
// mouse handling
// ----------------------------------------------------------------------------

void wxMiniCalendar::OnDClick(wxMouseEvent& event)
{
    if ( HitTest(event.GetPosition()) != wxCAL_HITTEST_DAY )
    {
        event.Skip();
    }
    else
    {
        GenerateEvent(wxEVT_MINI_CALENDAR_DOUBLECLICKED);
    }
}

void wxMiniCalendar::OnClick(wxMouseEvent& event)
{
    wxDateTime date;
    wxDateTime::WeekDay wday;
    switch ( HitTest(event.GetPosition(), &date, &wday) )
    {
        case wxCAL_HITTEST_DAY:
            if ( IsDateInRange(date) )
            {
                ChangeDay(date);

                GenerateEvents(wxEVT_MINI_CALENDAR_DAY_CHANGED,
                               wxEVT_MINI_CALENDAR_SEL_CHANGED);
            }
            break;

        case wxCAL_HITTEST_HEADER:
            event.Skip();
            break;
        case wxCAL_HITTEST_TODAY:
        case wxCAL_HITTEST_SURROUNDING_WEEK:
            SetDateAndNotify(date);
            break;
        case wxCAL_HITTEST_DECMONTH:
        case wxCAL_HITTEST_INCMONTH:
            SetDate(date);
            break;

        default:
            wxFAIL_MSG(_T("unknown hittest code"));
            // fall through

        case wxCAL_HITTEST_NOWHERE:
            event.Skip();
            break;
    }
}

wxCalendarHitTestResult wxMiniCalendar::HitTest(const wxPoint& pos,
                                                wxDateTime *date,
                                                wxDateTime::WeekDay *wd)
{
    RecalcGeometry();

    wxCoord y = pos.y;

///////////////////////////////////////////////////////////////////////////////////////////////////////
    // Header: month

    // we need to find out if the hit is on left arrow, on month or on right arrow
    // left arrow?
    if ( wxRegion(m_leftArrowRect).Contains(pos) == wxInRegion )
    {
        if ( date )
        {
            if ( IsDateInRange(m_date - wxDateSpan::Month()) )
            {
                *date = m_date - wxDateSpan::Month();
            }
            else
            {
                *date = GetLowerDateLimit();
            }
        }

        return wxCAL_HITTEST_DECMONTH;
    }

    if ( wxRegion(m_rightArrowRect).Contains(pos) == wxInRegion )
    {
        if ( date )
        {
            if ( IsDateInRange(m_date + wxDateSpan::Month()) )
            {
                *date = m_date + wxDateSpan::Month();
            }
            else
            {
                *date = GetUpperDateLimit();
            }
        }

        return wxCAL_HITTEST_INCMONTH;
    }

    if ( wxRegion(m_todayRect).Contains(pos) == wxInRegion )
    {
        if ( date )
        {
            *date = wxDateTime::Today();
        }

        return wxCAL_HITTEST_TODAY;
    }

///////////////////////////////////////////////////////////////////////////////////////////////////////
    // Header: Days
    int wday = pos.x / m_widthCol;
    int initialHeight = m_todayHeight + m_heightPreview;
    int monthHeight = m_rowOffset + WEEKS_TO_DISPLAY * m_heightRow + EXTRA_MONTH_HEIGHT;
    int headerHeight = m_rowOffset + EXTRA_MONTH_HEIGHT;
    int month;
    for ( month = 0; month < MONTHS_TO_DISPLAY; month++)
    {

        if ( y < (month * monthHeight + initialHeight + headerHeight) )
        {
            if ( y > (month * monthHeight + initialHeight) )
            {
                if ( wd )
                {
                    if ( GetWindowStyle() & wxCAL_MONDAY_FIRST )
                    {
                        wday = wday == (DAYS_PER_WEEK - 1) ? 0 : wday + 1;
                    }

                    *wd = (wxDateTime::WeekDay)wday;
                }

                return wxCAL_HITTEST_HEADER;
            }
        }
    }
    int week;
    bool found = false;
    int month;
    for ( month = 0; month < MONTHS_TO_DISPLAY; month++ )
    {
        if ( y > ( initialHeight + month * monthHeight + headerHeight ) && 
            ( y < ( initialHeight + (month + 1) * monthHeight ) ) )
        {
            week = (y - initialHeight - month * monthHeight - headerHeight) / m_heightRow;
            found = true;
            break;
        }
    }

    if ( ( wday >= DAYS_PER_WEEK ) || !found )
    {
        return wxCAL_HITTEST_NOWHERE;
    }

    wxDateTime dt;
    wxDateTime::Tm tm = m_date.GetTm();
    dt = wxDateTime(1, tm.mon, tm.year);
    int monthsToAdd;
    for (monthsToAdd = 0; monthsToAdd < month; monthsToAdd++)
    {
        dt += wxDateSpan::Month();
    }
    dt.SetToPrevWeekDay(GetWindowStyle() & wxCAL_MONDAY_FIRST
            ? wxDateTime::Mon : wxDateTime::Sun);
    dt += wxDateSpan::Days(DAYS_PER_WEEK * week + wday);

    if ( IsDateShown(dt) )
    {
        if ( date )
            *date = dt;

        if ( dt.GetMonth() == m_date.GetMonth() )
        {

            return wxCAL_HITTEST_DAY;
        }
        else
        {
            return wxCAL_HITTEST_SURROUNDING_WEEK;
        }
    }
    else
    {
        return wxCAL_HITTEST_NOWHERE;
    }
    return wxCAL_HITTEST_NOWHERE;
}

//static
wxVisualAttributes
wxMiniCalendar::GetClassDefaultAttributes(wxWindowVariant variant)
{
    // Use the same color scheme as wxListBox
    return wxListBox::GetClassDefaultAttributes(variant);
}


// ----------------------------------------------------------------------------
// wxMiniCalendarEvent
// ----------------------------------------------------------------------------

void wxMiniCalendarEvent::Init()
{
    m_wday = wxDateTime::Inv_WeekDay;
}

wxMiniCalendarEvent::wxMiniCalendarEvent(wxMiniCalendar *cal, wxEventType type)
               : wxCommandEvent(type, cal->GetId())
{
    m_date = cal->GetDate();
    SetEventObject(cal);
}

#endif // wxUSE_CALENDARCTRL

