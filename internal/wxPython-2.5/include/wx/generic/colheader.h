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
#include "wx/bitmap.h"


// forward decls
// class wxColumnHeaderItem;
// class wxBitmap;

// ----------------------------------------------------------------------------
// wxColumnHeader: a control that provides a native-appearance column header
// ----------------------------------------------------------------------------

typedef enum
{
	wxCHI_kMetricInsetX			= 4,
	wxCHI_kMetricInsetY			= 4,
	wxCHI_kMetricArrowSizeX		= 12,
	wxCHI_kMetricArrowSizeY		= 12,
	wxCHI_kMetricBitmapSizeX		= 12,
	wxCHI_kMetricBitmapSizeY		= 12
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

	bool GetFlagAttribute(
		wxColumnHeaderFlagAttr		flagEnum ) const;
	bool SetFlagAttribute(
		wxColumnHeaderFlagAttr		flagEnum,
		bool						bFlagValue );

	long GenericDrawItem(
		wxWindow		*parentW,
		wxClientDC		*dc,
		const wxRect		*boundsR,
		bool				bUseUnicode,
		bool				bVisibleSelection ) const;

#if defined(__WXMAC__)
	long MacDrawItem(
		wxWindow		*parentW,
		wxClientDC		*dc,
		const wxRect		*boundsR,
		bool				bUseUnicode,
		bool				bVisibleSelection ) const;
#endif

public:
#if defined(__WXMSW__)
	static void MSWRenderSelection(
		wxClientDC		*dc,
		const wxRect		*boundsR );
#endif

#if defined(__WXMAC__)
	static void MacDrawThemeBackgroundNoArrows(
		const void			*boundsR,
		bool				bSelected );
#endif

	static void GenericGetSortArrowBounds(
		const wxRect		*itemBoundsR,
		wxRect			*targetBoundsR );
	static void GenericDrawSortArrow(
		wxClientDC		*dc,
		const wxRect		*boundsR,
		bool				bSortAscending );

	static bool HasValidBitmapRef(
		const wxBitmap	*bitmapRef );
	static void GetBitmapItemBounds(
		const wxRect		*itemBoundsR,
		long				targetJustification,
		wxRect			*targetBoundsR );

	static long ConvertJustification(
		long				sourceEnum,
		bool				bToNative );

public:
	wxString				m_LabelTextRef;
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
		long			itemIndex,
		long				originX );

	bool GetFlagProportionalResizing( void ) const;
	void SetFlagProportionalResizing(
		bool				bFlagValue );
	bool GetFlagVisibleSelection( void ) const;
	void SetFlagVisibleSelection(
		bool				bFlagValue );
	bool GetFlagUnicode( void ) const;
	void SetFlagUnicode(
		bool				bFlagValue );

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

	wxPoint GetUIExtent(
		long				itemIndex ) const;
	void SetUIExtent(
		long				itemIndex,
		wxPoint			&extentPt );
	bool GetFlagAttribute(
		long						itemIndex,
		wxColumnHeaderFlagAttr		flagEnum ) const;
	bool SetFlagAttribute(
		long						itemIndex,
		wxColumnHeaderFlagAttr		flagEnum,
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

	long GetLabelWidth(
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
	long Win32ItemInsert(
		long			iInsertAfter,
		long			nWidth,
		const void		*titleText,
		long			textJust,
		bool			bUseUnicode,
		bool			bSelected,
		bool			bSortEnabled,
		bool			bSortAscending );
	long Win32ItemDelete(
		long			itemIndex );
	long Win32ItemRefresh(
		long			itemIndex );
	long Win32ItemSelect(
		long			itemIndex,
		bool			bSelected,
		bool			bSortEnabled,
		bool			bSortAscending );
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
	wxColumnHeaderItem		**m_ItemList;
	long					m_ItemCount;
	long					m_ItemSelected;
	bool					m_BProportionalResizing;
	bool					m_BVisibleSelection;
	bool					m_BUseUnicode;

	DECLARE_DYNAMIC_CLASS(wxColumnHeader)
	DECLARE_EVENT_TABLE()
	DECLARE_NO_COPY_CLASS(wxColumnHeader)
};

#endif // _WX_GENERIC_COLUMNHEADER_H
