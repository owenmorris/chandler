#ifndef _WX_COLUMNHEADER_H
#define _WX_COLUMNHEADER_H

#include "wx/defs.h"

// #if wxUSE_COLUMNHEADER

#include "wx/control.h"			// the base class
#include "wx/dcclient.h"		// for wxPaintDC
#include "wx/font.h"

// ----------------------------------------------------------------------------
// wxColumnHeader flags and constants
// ----------------------------------------------------------------------------

#if defined(__WXMSW__)
#define wxColumnHeaderNameStr		_T(WC_HEADER)
#else
#define wxColumnHeaderNameStr		_T("ColumnHeader")
#endif


typedef enum
{
	wxCOLUMNHEADER_JUST_Left,
	wxCOLUMNHEADER_JUST_Center,
	wxCOLUMNHEADER_JUST_Right
}
wxColumnHeaderJustification;

typedef enum
{
	wxCOLUMNHEADER_FLAGATTR_Enabled,
	wxCOLUMNHEADER_FLAGATTR_Selected,
	wxCOLUMNHEADER_FLAGATTR_SortDirection
}
wxColumnHeaderFlagAttr;

typedef enum
{
	wxCOLUMNHEADER_HITTEST_NoPart			= -1,	// outside of everything
	wxCOLUMNHEADER_HITTEST_ItemZero		= 0		// any other (non-negative) value is a sub-item
}
wxColumnHeaderHitTestResult;


// ----------------------------------------------------------------------------
// wxColumnHeader events
// ----------------------------------------------------------------------------

class WXDLLIMPEXP_ADV wxColumnHeader;

class WXDLLIMPEXP_ADV wxColumnHeaderEvent : public wxCommandEvent
{
friend class wxColumnHeader;

public:
	wxColumnHeaderEvent()
		{ Init(); }
	wxColumnHeaderEvent( wxColumnHeader *col, wxEventType type );

protected:
	void Init( void );

private:
	DECLARE_DYNAMIC_CLASS_NO_COPY(wxColumnHeaderEvent)
};


// ----------------------------------------------------------------------------
// wxColumnHeader
// ----------------------------------------------------------------------------

// so far we only have a generic version, so keep it simple
#include "wx/generic/colheader.h"

// ----------------------------------------------------------------------------
// column header event types and macros for handling them
// ----------------------------------------------------------------------------

BEGIN_DECLARE_EVENT_TYPES()
	DECLARE_EXPORTED_EVENT_TYPE(WXDLLIMPEXP_ADV, wxEVT_COLUMNHEADER_DOUBLECLICKED, 1950)
	DECLARE_EXPORTED_EVENT_TYPE(WXDLLIMPEXP_ADV, wxEVT_COLUMNHEADER_SELCHANGED, 1951)
END_DECLARE_EVENT_TYPES()

typedef void (wxEvtHandler::*wxColumnHeaderEventFunction)( wxColumnHeaderEvent & );

#define EVT_COLUMNHEADER_DOUBLECLICKED(id, fn) DECLARE_EVENT_TABLE_ENTRY(wxEVT_COLUMNHEADER_DOUBLECLICKED, id, wxID_ANY, (wxObjectEventFunction) (wxEventFunction) (wxCommandEventFunction) wxStaticCastEvent( wxColumnHeaderEventFunction, & fn ), (wxObject*)NULL),
#define EVT_COLUMNHEADER_SELCHANGED(id, fn) DECLARE_EVENT_TABLE_ENTRY(wxEVT_COLUMNHEADER_SELCHANGED, id, wxID_ANY, (wxObjectEventFunction) (wxEventFunction) (wxCommandEventFunction) wxStaticCastEvent( wxColumnHeaderEventFunction, &fn ), (wxObject*)NULL),

// #endif // wxUSE_COLUMNHEADER

#endif // _WX_COLUMNHEADER_H
