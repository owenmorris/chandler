/////////////////////////////////////////////////////////////////////////////
// Name:        colheader.i
// Purpose:    SWIG definitions for the wxColumnHeader wxWidget
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

%include _colheader_rename.i

//---------------------------------------------------------------------------

enum wxColumnHeaderJustification
{
    wxCOLUMNHEADER_JUST_Left,
    wxCOLUMNHEADER_JUST_Center,
    wxCOLUMNHEADER_JUST_Right
};

enum wxColumnHeaderFlagAttr
{
    wxCOLUMNHEADER_FLAGATTR_Enabled,
    wxCOLUMNHEADER_FLAGATTR_Selected,
    wxCOLUMNHEADER_FLAGATTR_SortEnabled,
    wxCOLUMNHEADER_FLAGATTR_SortDirection,
    wxCOLUMNHEADER_FLAGATTR_FixedWidth
};

enum wxColumnHeaderHitTestResult
{
    wxCOLUMNHEADER_HITTEST_NoPart            = -1,    // outside of everything
    wxCOLUMNHEADER_HITTEST_ItemZero        = 0        // any other (non-negative) value is a sub-item
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
EVT_COLUMNHEADER_DOUBLECLICKED = wx.PyEventBinder(wxEVT_COLUMNHEADER_DOUBLECLICKED, 1)
EVT_COLUMNHEADER_SELCHANGED = wx.PyEventBinder(wxEVT_COLUMNHEADER_SELCHANGED, 1)
}


//---------------------------------------------------------------------------
MustHaveApp(wxColumnHeader);

class wxColumnHeader : public wxControl
{
public:
    // wxColumnHeader();
    // ~wxColumnHeader();

    wxColumnHeader(
        wxWindow        *parent,
        wxWindowID        id = -1,
        const wxPoint        &pos = wxDefaultPosition,
        const wxSize        &size = wxDefaultSize,
        long                style = 0,
        const wxString        &name = wxColumnHeaderNameStr );

    virtual bool Destroy( void );

    virtual void DoMoveWindow( int x, int y, int width, int height );
    virtual bool Enable( bool bEnable = true );
    virtual bool Show( bool bShow = true );
    virtual void DoSetSize( int x, int y, int width, int height, int sizeFlags );
    virtual wxSize DoGetBestSize( void ) const;

    wxSize CalculateDefaultSize( void ) const;
    long GetTotalUIExtent( void ) const;
    bool ResizeToFit( void );
    bool RescaleToFit(
        long            newWidth );
    bool ResizeDivision(
        long            itemIndex,
        long            originX );

    bool GetFlagProportionalResizing( void ) const;
    void SetFlagProportionalResizing(
        bool                bFlagValue );
    bool GetFlagVisibleSelection( void ) const;
    void SetFlagVisibleSelection(
        bool                bFlagValue );
    bool GetFlagUnicode( void ) const;
    void SetFlagUnicode(
        bool                bFlagValue );

    long GetItemCount( void ) const;
    long GetSelectedItem( void ) const;
    void SetSelectedItem(
        long            itemIndex );
    wxColumnHeaderHitTestResult HitTest(
        const wxPoint    &locationPt );
    void AppendItem(
        const wxString        &textBuffer,
        long                textJust,
        long                extentX,
        bool                bSelected = false,
        bool                bSortEnabled = true,
        bool                bSortAscending = false );
    void AddItem(
        long                beforeIndex,
        const wxString        &textBuffer,
        long                textJust,
        long                extentX,
        bool                bSelected = false,
        bool                bSortEnabled = true,
        bool                bSortAscending = false );
    void DeleteItem(
        long                itemIndex );
    void GetBitmapRef(
        long                itemIndex,
        wxBitmap        &imageRef ) const;
    void SetBitmapRef(
        long                itemIndex,
        wxBitmap        &imageRef );
    wxString GetLabelText(
        long                itemIndex ) const;
    void SetLabelText(
        long                itemIndex,
        const wxString        &textBuffer );
    long GetLabelJustification(
        long                itemIndex ) const;
    void SetLabelJustification(
        long                itemIndex,
        long                textJust );
    wxPoint GetUIExtent(
        long                itemIndex ) const;
    void SetUIExtent(
        long                itemIndex,
        wxPoint            &extentPt );
    bool GetFlagAttribute(
        long                            itemIndex,
        wxColumnHeaderFlagAttr    flagEnum ) const;
    bool SetFlagAttribute(
        long                            itemIndex,
        wxColumnHeaderFlagAttr        flagEnum,
        bool                        bFlagValue );
};

//---------------------------------------------------------------------------

%init %{
%}

//---------------------------------------------------------------------------

