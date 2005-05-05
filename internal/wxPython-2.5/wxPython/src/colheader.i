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

enum wxColumnHeaderHitTestResult
{
    CH_HITTEST_NoPart            = -1,    // not within a known sub-item (but within the client bounds)
    CH_HITTEST_ItemZero        = 0        // any other (non-negative) value is a sub-item
};

enum wxColumnHeaderAttribute
{
    CH_ATTR_Unicode,
    CH_ATTR_GenericRenderer,
    CH_ATTR_VisibleSelection,
    CH_ATTR_ProportionalResizing
};

enum wxColumnHeaderItemAttribute
{
    CH_ITEM_ATTR_Enabled,
    CH_ITEM_ATTR_Selected,
    CH_ITEM_ATTR_SortEnabled,
    CH_ITEM_ATTR_SortDirection,
    CH_ITEM_ATTR_FixedWidth
};

enum wxColumnHeaderJustification
{
    // NB: 1) wxID_JUSTIFY_ values enum as: center, fill, right, left
    // NB: 2) existing Wx justification enum has (too) many inapplicable elements
    CH_JUST_Left,
    CH_JUST_Center,
    CH_JUST_Right
};

enum wxColumnHeaderSelectionDrawStyle
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
        %pythonAppend wxColumnHeader      "self._setOORInfo(self)"
        %pythonAppend wxColumnHeader()    ""

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
    virtual wxSize DoGetMinSize( void ) const;

    wxSize CalculateDefaultSize( void ) const;
    long GetTotalUIExtent( void ) const;
    bool ResizeToFit( void );
    bool RescaleToFit(
        long            newWidth );
    bool ResizeDivision(
        long            itemIndex,
        long            originX );

    void GetSelectionColour(
        wxColour            &targetColour ) const;
    void SetSelectionColour(
        const wxColour        &targetColour );
    long GetSelectionDrawStyle( void ) const;
    void SetSelectionDrawStyle(
        long                styleValue );
    bool GetAttribute(
        wxColumnHeaderAttribute    flagEnum ) const;
    bool SetAttribute(
        wxColumnHeaderAttribute        flagEnum,
        bool                        bFlagValue );

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
    wxSize GetUIExtent(
        long                itemIndex ) const;
    void SetUIExtent(
        long                itemIndex,
        wxSize            &extentPt );
    bool GetItemAttribute(
        long                            itemIndex,
        wxColumnHeaderItemAttribute    flagEnum ) const;
    bool SetItemAttribute(
        long                            itemIndex,
        wxColumnHeaderItemAttribute        flagEnum,
        bool                        bFlagValue );
};

//---------------------------------------------------------------------------

%init %{
%}

//---------------------------------------------------------------------------

