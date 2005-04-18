///////////////////////////////////////////////////////////////////////////////
// Name:		generic/colheader.h
// Purpose:	data definitions for a 2-platform (Mac,MSW) + generic native-appearance column header
// Author:	David Surovell
// Modified by:
// Created:	01.01.2005
// RCS-ID:
// Copyright:
// License:
///////////////////////////////////////////////////////////////////////////////

#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
	#pragma interface "colheader.h"
#endif

#if !defined(_WX_GENERIC_COLUMNHEADER_H)
#define _WX_GENERIC_COLUMNHEADER_H

#include "wx/control.h"			// the base class
#include "wx/dcclient.h"
#include "wx/font.h"
#include "wx/colour.h"
#include "wx/bitmap.h"


// forward decls
// class wxColumnHeaderItem;
// class wxBitmap;

// ----------------------------------------------------------------------------
// private data definitions
// ----------------------------------------------------------------------------

typedef enum
{
	wxCH_kMetricInsetX				= 4,
	wxCH_kMetricInsetY				= 4,
	wxCH_kMetricArrowSizeX		= 12,
	wxCH_kMetricArrowSizeY		= 12,
	wxCH_kMetricBitmapSizeX		= 12,
	wxCH_kMetricBitmapSizeY		= 12
}
wxColumnHeaderMetric;

class wxColumnHeaderItem
{
public:
	wxColumnHeaderItem(
		const wxColumnHeaderItem		*info );
	wxColumnHeaderItem();
	virtual ~wxColumnHeaderItem();

	long HitTest(
		const wxPoint		&locationPt ) const;

	void GetItemData(
		wxColumnHeaderItem				*info ) const;
	void SetItemData(
		const wxColumnHeaderItem		*info );

	void GetBitmapRef(
		wxBitmap			&bitmapRef ) const;
	void SetBitmapRef(
		wxBitmap			&bitmapRef,
		const wxRect		*boundsR );

	void GetLabelText(
		wxString			&textBuffer ) const;
	void SetLabelText(
		const wxString		&textBuffer );

	long GetLabelJustification( void ) const;
	void SetLabelJustification(
		long			textJust );

	void GetUIExtent(
		long			&originX,
		long			&extentX ) const;
	void SetUIExtent(
		long			originX,
		long			extentX );

	void GetTextUIExtent(
		long			&originX,
		long			&extentX ) const;

	bool GetFlagAttribute(
		wxColumnHeaderItemFlagAttr	flagEnum ) const;
	bool SetFlagAttribute(
		wxColumnHeaderItemFlagAttr	flagEnum,
		bool						bFlagValue );

	long GenericDrawItem(
		wxWindow		*parentW,
		wxClientDC		*dc,
		const wxRect		*boundsR,
		bool				bUseUnicode,
		bool				bVisibleSelection );

#if defined(__WXMAC__)
	long MacDrawItem(
		wxWindow		*parentW,
		wxClientDC		*dc,
		const wxRect		*boundsR,
		bool				bUseUnicode,
		bool				bVisibleSelection );
#endif

	long TruncateLabelText(
		wxDC			*dc,
		wxString			&targetStr,
		long				maxWidth,
		long				&charCount );

public:
	static void GenericDrawSelection(
		wxClientDC		*dc,
		const wxRect		*boundsR,
		const wxColour		*targetColour,
		long				drawStyle );

	static void GenericDrawSortArrow(
		wxClientDC		*dc,
		const wxRect		*boundsR,
		bool				bSortAscending );
	static void GenericGetSortArrowBounds(
		const wxRect		*itemBoundsR,
		wxRect			*targetBoundsR );
	static void GenericGetBitmapItemBounds(
		const wxRect		*itemBoundsR,
		long				targetJustification,
		const wxBitmap	*targetBitmap,
		wxRect			*targetBoundsR );

#if defined(__WXMAC__)
	static void MacDrawThemeBackgroundNoArrows(
		const void			*boundsR,
		bool				bSelected );
#endif

	static bool HasValidBitmapRef(
		const wxBitmap	*bitmapRef );

	static long ConvertJustification(
		long				sourceEnum,
		bool				bToNative );

public:
	wxString				m_LabelTextRef;
	wxSize				m_LabelTextExtent;
	long					m_TextJust;
	wxBitmap				*m_BitmapRef;
	long					m_OriginX;
	long					m_ExtentX;
	bool					m_BEnabled;
	bool					m_BSelected;
	bool					m_BSortEnabled;
	bool					m_BSortAscending;
	bool					m_BFixedWidth;
};

class WXDLLIMPEXP_ADV wxColumnHeader : public wxControl
{
public:
	// construction
	wxColumnHeader(
		wxWindow		*parent,
		wxWindowID		id = -1,
		const wxPoint	&pos = wxDefaultPosition,
		const wxSize	&size = wxDefaultSize,
		long			style = 0,
		const wxString	&name = wxColumnHeaderNameStr );
	wxColumnHeader();
	virtual ~wxColumnHeader();

	bool Create(
		wxWindow		*parent,
		wxWindowID		id = -1,
		const wxPoint	&pos = wxDefaultPosition,
		const wxSize	&size = wxDefaultSize,
		long			style = 0,
		const wxString	&name = wxColumnHeaderNameStr );

	virtual bool Destroy( void );

	// embellish (override) some base class virtuals
	virtual void DoMoveWindow( int x, int y, int width, int height );
	virtual bool Enable( bool bEnable = true );
	virtual bool Show( bool bShow = true );
	virtual void DoSetSize( int x, int y, int width, int height, int sizeFlags );
	virtual wxSize DoGetBestSize( void ) const;

	wxSize CalculateDefaultSize( void ) const;
	long GetTotalUIExtent( void ) const;
	bool ResizeToFit( void );
	bool RescaleToFit(
		long				newWidth );
	bool ResizeDivision(
		long				itemIndex,
		long				originX );

	void GetSelectionColour(
		wxColor			&targetColour ) const;
	void SetSelectionColour(
		const wxColor		&targetColour );
	long GetSelectionDrawStyle( void ) const;
	void SetSelectionDrawStyle(
		long				styleValue );
	bool GetFlagAttribute(
		wxColumnHeaderFlagAttr		flagEnum ) const;
	bool SetFlagAttribute(
		wxColumnHeaderFlagAttr		flagEnum,
		bool						bFlagValue );

	// returns a non-negative value for a column header item
	// or wxCOLUMNHEADER_HITTEST_NOWHERE for no item
	wxColumnHeaderHitTestResult HitTest(
		const wxPoint		&locationPt );

	long GetItemCount( void ) const;
	long GetSelectedItem( void ) const;
	void SetSelectedItem(
		long				itemIndex );

	void DeleteItem(
		long				itemIndex );
	void AppendItem(
		const wxString		&textBuffer,
		long				textJust,
		long				extentX,
		bool				bActive,
		bool				bSortEnabled,
		bool				bSortAscending );
	void AddItem(
		long				beforeIndex,
		const wxString		&textBuffer,
		long				textJust,
		long				extentX,
		bool				bActive,
		bool				bSortEnabled,
		bool				bSortAscending );

	void GetBitmapRef(
		long				itemIndex,
		wxBitmap			&bitmapRef ) const;
	void SetBitmapRef(
		long				itemIndex,
		wxBitmap			&bitmapRef );

	wxString GetLabelText(
		long				itemIndex ) const;
	void SetLabelText(
		long				itemIndex,
		const wxString		&textBuffer );
	long GetLabelJustification(
		long				itemIndex ) const;
	void SetLabelJustification(
		long				itemIndex,
		long				textJust );

	wxSize GetUIExtent(
		long				itemIndex ) const;
	void SetUIExtent(
		long				itemIndex,
		wxSize			&extentPt );
	bool GetItemFlagAttribute(
		long						itemIndex,
		wxColumnHeaderItemFlagAttr	flagEnum ) const;
	bool SetItemFlagAttribute(
		long						itemIndex,
		wxColumnHeaderItemFlagAttr	flagEnum,
		bool						bFlagValue );

	// implementation only from now on
	// -------------------------------

#if defined(__WXMSW__)
	virtual WXDWORD MSWGetStyle(
		long		style,
		WXDWORD		*exstyle ) const;
#endif

	virtual wxVisualAttributes GetDefaultAttributes( void ) const
		{ return GetClassDefaultAttributes( GetWindowVariant() ); }

	static wxVisualAttributes GetClassDefaultAttributes(
		wxWindowVariant variant = wxWINDOW_VARIANT_NORMAL );

protected:
	void AddItemList(
		const wxColumnHeaderItem		*itemList,
		long							itemCount,
		long							beforeIndex );

	void OnClick_SelectOrToggleSort(
		long				itemIndex,
		bool				bToggleSortDirection );

	bool GetItemData(
		long							itemIndex,
		wxColumnHeaderItem				*info ) const;
	bool SetItemData(
		long							itemIndex,
		const wxColumnHeaderItem		*info );
	bool GetItemBounds(
		long				itemIndex,
		wxRect			*boundsR ) const;
	wxColumnHeaderItem * GetItemRef(
		long				itemIndex ) const;
	void RefreshItem(
		long				itemIndex );

	wxSize GetLabelTextExtent(
		wxClientDC			*dc,
		const wxString			&targetStr );

	void DisposeItemList( void );
	void SetViewDirty( void );
	void RecalculateItemExtents( void );

	long Draw( void );

#if defined(__WXMAC__)
	virtual void MacControlUserPaneActivateProc(
		bool				bActivating );
#endif

#if defined(__WXMSW__)
	long MSWItemInsert(
		long			iInsertAfter,
		long			nWidth,
		const void		*titleText,
		long			textJust,
		bool			bUseUnicode,
		bool			bSelected,
		bool			bSortEnabled,
		bool			bSortAscending );
	long MSWItemDelete(
		long			itemIndex );
	long MSWItemRefresh(
		long			itemIndex,
		bool			bCheckChanged = false );
#endif

protected:
	// called by all ctors
	void Init( void );

	// event handlers
	void OnPaint( wxPaintEvent &event );
	void OnClick( wxMouseEvent &event );
	void OnDoubleClick( wxMouseEvent &event );

	// event generator
	void GenerateEvent( wxEventType eventType );

protected:
	wxRect					m_NativeBoundsR;
	wxFont				m_Font;
	wxColour				m_SelectionColour;
	wxColumnHeaderItem		**m_ItemList;
	long					m_ItemCount;
	long					m_ItemSelected;
	long					m_SelectionDrawStyle;
	bool					m_BUseUnicode;			// set by compile flag, but not necessarily so - cannot be reset
	bool					m_BUseGenericRenderer;		// Mac,MSW: either true or false; otherwise: always true
	bool					m_BFixedHeight;			// Mac,MSW: always true; otherwise: false
	bool					m_BProportionalResizing;
	bool					m_BVisibleSelection;

	DECLARE_DYNAMIC_CLASS(wxColumnHeader)
	DECLARE_EVENT_TABLE()
	DECLARE_NO_COPY_CLASS(wxColumnHeader)
};

#endif // _WX_GENERIC_COLUMNHEADER_H
