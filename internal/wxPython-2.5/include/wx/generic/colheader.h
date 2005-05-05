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
// class wxBitmap;
class wxColumnHeaderItem;

// ----------------------------------------------------------------------------
// private data definitions
// ----------------------------------------------------------------------------

typedef enum
{
	wxCH_kMetricInsetX				= 4,
	wxCH_kMetricInsetY				= 4,
	wxCH_kMetricArrowSizeX		= 8,
	wxCH_kMetricArrowSizeY		= 8,
	wxCH_kMetricBitmapSizeX		= 12,
	wxCH_kMetricBitmapSizeY		= 12
}
wxColumnHeaderMetric;

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
	virtual wxSize DoGetMinSize( void ) const;

	wxSize CalculateDefaultSize( void ) const;
	long GetTotalUIExtent( void ) const;
	bool ResizeToFit( void );
	bool RescaleToFit(
		long				newWidth );
	bool ResizeDivision(
		long				itemIndex,
		long				originX );

	void GetSelectionColour(
		wxColour			&targetColour ) const;
	void SetSelectionColour(
		const wxColour		&targetColour );
	long GetSelectionDrawStyle( void ) const;
	void SetSelectionDrawStyle(
		long				styleValue );
	bool GetAttribute(
		wxColumnHeaderAttribute		flagEnum ) const;
	bool SetAttribute(
		wxColumnHeaderAttribute		flagEnum,
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
	bool GetItemAttribute(
		long						itemIndex,
		wxColumnHeaderItemAttribute	flagEnum ) const;
	bool SetItemAttribute(
		long						itemIndex,
		wxColumnHeaderItemAttribute	flagEnum,
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
		wxDC				*dc,
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

class wxColumnHeaderItem
{
friend class wxColumnHeader;

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
		long				textJust );

	void GetUIExtent(
		long				&originX,
		long				&extentX ) const;
	void SetUIExtent(
		long				originX,
		long				extentX );

	bool GetAttribute(
		wxColumnHeaderItemAttribute	flagEnum ) const;
	bool SetAttribute(
		wxColumnHeaderItemAttribute	flagEnum,
		bool						bFlagValue );

	long GenericDrawItem(
		wxWindow		*parentW,
		wxDC			*dc,
		const wxRect		*boundsR,
		bool				bUseUnicode,
		bool				bVisibleSelection );

#if defined(__WXMAC__)
	long MacDrawItem(
		wxWindow		*parentW,
		wxDC			*dc,
		const wxRect		*boundsR,
		bool				bUseUnicode,
		bool				bVisibleSelection );
#endif

	void ResizeToWidth(
		long				extentX );
	void CalculateTextExtent(
		wxDC			*dc,
		bool				bForceRecalc );
	long MeasureLabelText(
		wxDC			*dc,
		const wxString		&targetStr,
		long				maxWidth,
		long				&charCount );
	void GetTextUIExtent(
		long				&startX,
		long				&originX,
		long				&extentX ) const;
	void TruncateLabelText(
		wxString			&targetStr,
		long				cutoffCharCount );
	void InvalidateTextExtent( void );

public:
	static void GenericDrawSelection(
		wxDC			*dc,
		const wxRect		*boundsR,
		const wxColour		*targetColour,
		long				drawStyle );

	static void GenericDrawSortArrow(
		wxDC			*dc,
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

	static bool ValidBitmapRef(
		const wxBitmap	*bitmapRef );

	static wxChar * GetEllipsesString( void );

	static long ConvertJustification(
		long				sourceEnum,
		bool				bToNative );

protected:
	wxString				m_LabelTextRef;
	wxSize				m_LabelTextExtent;
	long					m_LabelTextVisibleCharCount;
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

#endif // _WX_GENERIC_COLUMNHEADER_H
