/////////////////////////////////////////////////////////////////////////////
// Name:        colheader.i
// Purpose:    SWIG definitions for the wxColumnHeader
//
// Author:      David Surovell
//
/////////////////////////////////////////////////////////////////////////////

%define DOCSTRING
"Classes for a column header control with a native appearance."
%enddef

%module(package="wx", docstring=DOCSTRING) colheader


%{
#include "wx/wxPython/wxPython.h"
#include "wx/wxPython/pyclasses.h"

#include <wx/colheader.h>
%}

//----------------------------------------------------------------------

%import misc.i
%pythoncode { wx = _core }
%pythoncode { __docfilter__ = wx.__DocFilter(globals()) }

//---------------------------------------------------------------------------

enum wxColumnHeaderJustification
{
    wxCOLUMNHEADER_JustLeft,
    wxCOLUMNHEADER_JustCenter,
    wxCOLUMNHEADER_JustRight
};

enum wxColumnHeaderHitTestResult
{
    wxCOLUMNHEADER_HITTEST_NOWHERE            = -1,    // outside of everything
    wxCOLUMNHEADER_HITTEST_ITEM_ZERO        = 0        // any other (non-negative) value is a sub-item
};

//---------------------------------------------------------------------------

class wxColumnHeader;

class wxColumnHeaderEvent : public wxCommandEvent
{
public:
    wxColumnHeaderEvent( wxColumnHeader *col, wxEventType type );
};


%constant wxEventType wxEVT_COLUMNHEADER_DOUBLECLICKED;
%constant wxEventType wxEVT_COLUMNHEADER_SELCHANGED;


%pythoncode {
EVT_COLUMNHEADER_DOUBLECLICKED =  wx.PyEventBinder( wxEVT_COLUMNHEADER_DOUBLECLICKED, 1)
EVT_COLUMNHEADER_SELCHANGED =     wx.PyEventBinder( wxEVT_COLUMNHEADER_SELCHANGED, 1)
}


//---------------------------------------------------------------------------
MustHaveApp(wxColumnHeader);

class wxColumnHeader : public wxControl
{
public:
    wxColumnHeader(
        wxWindow        *parent,
        wxWindowID        id = -1,
        const wxPoint        &pos = wxDefaultPosition,
        const wxSize        &size = wxDefaultSize,
        long                style = 0,
        const wxString        &name = wxColumnHeaderNameStr );
    wxColumnHeader();
    void SetUnicodeFlag(
        bool            bSetFlag );
    long GetSelectedItemIndex( void );
    void SetSelectedItemIndex(
        long            itemIndex );
    wxColumnHeaderHitTestResult HitTest(
        const wxPoint    &locationPt );
    long GetItemCount( void );
    void AppendItem(
        const wxString        &textBuffer,
        long                textJust,
        long                extentX,
        bool                bActive,
        bool                bSortAscending );
    void DeleteItem(
        long                itemIndex );
    bool GetLabelText(
        long                itemIndex,
        wxString            &textBuffer,
        long                &textJust );
    bool SetLabelText(
        long                itemIndex,
        const wxString        &textBuffer,
        long                textJust );
    bool GetUIExtent(
        long            itemIndex,
        long            &originX,
        long            &extentX );
    bool SetUIExtent(
        long            itemIndex,
        long            originX,
        long            extentX );
    bool GetFlags(
        long            itemIndex,
        bool            &bActive,
        bool            &bEnabled,
        bool            &bSortAscending );
    bool SetFlags(
        long            itemIndex,
        bool            bActive,
        bool            bEnabled,
        bool            bSortAscending );
};

//---------------------------------------------------------------------------

%init %{
%}

//---------------------------------------------------------------------------

