/////////////////////////////////////////////////////////////////////////////
// Name:        wxPython/src/colheader.i
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

enum wxColumnHeaderStyle
{
    CH_STYLE_HeaderIsVertical        = (1L << 23)
};

enum wxColumnHeaderAttribute
{
    CH_ATTR_VerticalOrientation,
    CH_ATTR_Unicode,
    CH_ATTR_GenericRenderer,
    CH_ATTR_FixedHeight,
    CH_ATTR_ProportionalResizing,
    CH_ATTR_VisibleSelection,
    CH_ATTR_MultiItemSelection
};

enum wxColumnHeaderItemAttribute
{
    CH_ITEM_ATTR_Enabled,
    CH_ITEM_ATTR_Selected,
    CH_ITEM_ATTR_SortEnabled,
    CH_ITEM_ATTR_SortDirection,
    CH_ITEM_ATTR_FixedWidth
};

enum wxColumnHeaderAlignment
{
    // NB: 1) wxID_JUSTIFY_ values enum as: center, fill, right, left
    // NB: 2) existing Wx justification enum has (too) many inapplicable elements
    CH_ALIGN_Left = wxID_JUSTIFY_LEFT,
    CH_ALIGN_Center = wxID_JUSTIFY_CENTER,
    CH_ALIGN_Right = wxID_JUSTIFY_RIGHT
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

enum wxColumnHeaderArrowButtonStyle
{
    CH_ARROWBUTTONSTYLE_None,
    CH_ARROWBUTTONSTYLE_Left,
    CH_ARROWBUTTONSTYLE_Right,
    CH_ARROWBUTTONSTYLE_Up,
    CH_ARROWBUTTONSTYLE_Down
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

    wxColumnHeader(
        wxWindow        *parent,
        wxWindowID        id = wxID_ANY,
        const wxPoint        &pos = wxDefaultPosition,
        const wxSize        &size = wxDefaultSize,
        long                styleVariant = 0,
        const wxString        &name = wxColumnHeaderNameStr );

    // NB: is this proper? What about the dtor?
    %RenameCtor(PreColumnHeader, wxColumnHeader());
    // wxColumnHeader();
    // ~wxColumnHeader();

    virtual bool Destroy( void );

    virtual void DumpInfo(
        const wxString&    titleStr = wxEmptyString ) const;

    virtual void DoMoveWindow(
        int    x,
        int    y,
        int    width,
        int    height );
    virtual bool Enable(
        bool    bEnable = true );
    virtual bool Show(
        bool    bShow = true );
    virtual void DoSetSize(
        int    x,
        int    y,
        int    width,
        int    height,
        int    sizeFlags );
    virtual wxSize DoGetBestSize( void ) const;
    virtual wxSize DoGetMinSize( void ) const;

    wxSize CalculateDefaultSize( void ) const;
    wxSize GetDefaultItemSize( void ) const;
    void SetDefaultItemSize(
        wxSize        targetSize );

    wxSize GetTotalUIExtent(
        long            itemCount = (-1),
        bool            bStartAtBase = false ) const;
    bool ResizeToFit(
        long            itemCount = (-1) );
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

    wxColumnHeaderHitTestResult HitTest(
        const wxPoint    &locationPt );
    long GetSelectedItem( void ) const;
    void SetSelectedItem(
        long            itemIndex );
    long GetBaseViewItem( void ) const;
    void SetBaseViewItem(
        long            itemIndex );

    long GetExpectedItemCount( void ) const;
    void SetExpectedItemCount(
        long            itemCount );
    long GetItemCount( void ) const;
    void SetItemCount(
        long            itemCount );

    void DeleteItems(
        long                itemIndex,
        long                itemCount );
    void DeleteItem(
        long                itemIndex );
    void AppendItem(
        const wxString        &textBuffer,
        const wxSize        &textAlign,
        long                extentX = (-1),
        bool                bSelected = false,
        bool                bSortEnabled = false,
        bool                bSortAscending = false );
    void AddEmptyItems(
        long                beforeIndex,
        long                itemCount );
    void AddItem(
        long                beforeIndex,
        const wxString        &textBuffer,
        const wxSize        &textAlign,
        long                extentX = (-1),
        bool                bSelected = false,
        bool                bSortEnabled = false,
        bool                bSortAscending = false );

    bool GetItemVisibility(
        long                itemIndex ) const;
    void SetItemVisibility(
        long                itemIndex,
        bool                bVisible );
    long GetArrowButtonStyle(
        long                itemIndex ) const;
    void SetArrowButtonStyle(
        long                itemIndex,
        long                targetStyle );
    void GetBitmap(
        long                itemIndex,
        wxBitmap        &imageRef ) const;
    void SetBitmap(
        long                itemIndex,
        const wxBitmap        &imageRef );
    wxSize GetBitmapAlignment(
        long                itemIndex ) const;
    void SetBitmapAlignment(
        long                itemIndex,
        const wxSize        &targetAlign );
    wxString GetLabelText(
        long                itemIndex ) const;
    void SetLabelText(
        long                itemIndex,
        const wxString        &textBuffer );
    wxSize GetLabelAlignment(
        long                itemIndex ) const;
    void SetLabelAlignment(
        long                itemIndex,
        const wxSize        &textAlign );

    wxSize GetUIOrigin(
        long                itemIndex ) const;
    void SetUIOrigin(
        long                itemIndex,
        const wxSize        &targetSize );
    wxSize GetUIExtent(
        long                itemIndex ) const;
    void SetUIExtent(
        long                itemIndex,
        const wxSize        &targetSize );

    bool GetItemAttribute(
        long                            itemIndex,
        wxColumnHeaderItemAttribute    flagEnum ) const;
    bool SetItemAttribute(
        long                            itemIndex,
        wxColumnHeaderItemAttribute        flagEnum,
        bool                        bFlagValue );

    static long GetFixedHeight( void );

    static wxSize CalculateDefaultItemSize(
        const wxSize        &maxSize );

    static void GetDefaultLabelValue(
        bool                isColumn,
        long                itemIndex,
        wxString&        value );
};

//---------------------------------------------------------------------------

%init %{
%}

//---------------------------------------------------------------------------

