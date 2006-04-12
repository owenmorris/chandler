///////////////////////////////////////////////////////////////////////////////
// Name:		wx/colheader.h
// Purpose:	public definitions for a native-appearance column header
// Author:	David Surovell
// Modified by:
// Created:	01.01.2005
// RCS-ID:
// Copyright:
// License:
///////////////////////////////////////////////////////////////////////////////

#if !defined(_WX_COLUMNHEADER_H)
#define _WX_COLUMNHEADER_H

#include "wx/defs.h"

// #if wxUSE_COLUMNHEADER

#include "wx/control.h"			// the base class

// ----------------------------------------------------------------------------
// wxColumnHeader flags and constants
// ----------------------------------------------------------------------------

#define wxColumnHeaderNameStr		_T("ColumnHeader")


typedef enum
{
	CH_HITTEST_NoPart			= -1,	// not within a known sub-item (but within the client bounds)
	CH_HITTEST_ItemZero		= 0		// any other (non-negative) value is a sub-item
}
wxColumnHeaderHitTestResult;

typedef enum
{
	CH_ATTR_Unicode,
	CH_ATTR_GenericRenderer,
	CH_ATTR_VisibleSelection,
	CH_ATTR_ProportionalResizing
}
wxColumnHeaderAttribute;

typedef enum
{
	CH_ITEM_ATTR_Enabled,
	CH_ITEM_ATTR_Selected,
	CH_ITEM_ATTR_SortEnabled,
	CH_ITEM_ATTR_SortDirection,
	CH_ITEM_ATTR_FixedWidth
}
wxColumnHeaderItemAttribute;

typedef enum
{
	// NB: 1) wxID_JUSTIFY_ values enum as: center, fill, right, left
	// NB: 2) existing Wx justification enum has (too) many inapplicable elements
	CH_JUST_Left,
	CH_JUST_Center,
	CH_JUST_Right
}
wxColumnHeaderJustification;

typedef enum
{
	CH_SELECTIONDRAWSTYLE_None,
	CH_SELECTIONDRAWSTYLE_Native,
	CH_SELECTIONDRAWSTYLE_BoldLabel,
	CH_SELECTIONDRAWSTYLE_ColourLabel,
	CH_SELECTIONDRAWSTYLE_Grey,
	CH_SELECTIONDRAWSTYLE_InvertBevel,
	CH_SELECTIONDRAWSTYLE_Underline,
	CH_SELECTIONDRAWSTYLE_Overline,
	CH_SELECTIONDRAWSTYLE_Frame,
	CH_SELECTIONDRAWSTYLE_Bullet
}
wxColumnHeaderSelectionDrawStyle;

// NB: these should be enum members,
// but some compilers spit warnings at synonymic references to the same base value
// anyways, they're private
#define CH_SELECTIONDRAWSTYLE_FIRST		CH_SELECTIONDRAWSTYLE_None
#define CH_SELECTIONDRAWSTYLE_LAST		CH_SELECTIONDRAWSTYLE_Bullet

typedef enum
{
	CH_ARROWBUTTONSTYLE_None,
	CH_ARROWBUTTONSTYLE_Left,
	CH_ARROWBUTTONSTYLE_Right,
	CH_ARROWBUTTONSTYLE_Up,
	CH_ARROWBUTTONSTYLE_Down
}
wxColumnHeaderArrowButtonStyle;

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
