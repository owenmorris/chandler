///////////////////////////////////////////////////////////////////////////////
// Name:		generic/colheader.h
// Purpose:	generic definitions for a native-appearance column header
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
#include "wx/font.h"

class WXDLLEXPORT wxStaticText;


// forward decls
// class wxColumnHeaderItem;

// ----------------------------------------------------------------------------
// wxColumnHeader: a control that provides a native-appearance column header
// ----------------------------------------------------------------------------

class wxColumnHeaderItem
{
public:
	wxColumnHeaderItem(
		const wxColumnHeaderItem		*info );
	wxColumnHeaderItem();
	virtual ~wxColumnHeaderItem();

	virtual long DrawSelf( void );

	long HitTest(
		const wxPoint		&locationPt );

	void GetItemData(
		wxColumnHeaderItem				*info );
	void SetItemData(
		const wxColumnHeaderItem		*info );

	void GetLabelText(
		wxString		&textBuffer );
	void SetLabelText(
		const wxString	&textBuffer );

	long GetLabelJustification( void );
	void SetLabelJustification(
		long			textJust );

	void GetUIExtent(
		long			&originX,
		long			&extentX );
	void SetUIExtent(
		long			originX,
		long			extentX );

	bool GetFlagAttribute(
		wxColumnHeaderFlagAttr		flagEnum );
	bool SetFlagAttribute(
		wxColumnHeaderFlagAttr		flagEnum,
		bool						bFlagValue );

public:
#if defined(__WXMAC__)
	static void MacDrawThemeBackgroundNoArrows(
		const Rect		*boundsR );
#endif

	static long ConvertJust(
		long			sourceEnum,
		bool			bToNative );

public:
	wxRect				m_NativeBoundsR;
	wxString				m_LabelTextRef;
	unsigned long			m_FontID;
	long					m_TextJust;
	long					m_ImageID;
	long					m_OriginX;
	long					m_ExtentX;
	bool					m_BEnabled;
	bool					m_BSelected;
	bool					m_BSortEnabled;
	bool					m_BSortAscending;
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

	void SetUnicodeFlag(
		bool				bSetFlag );

	// returns one of wxCOLUMNHEADER_HITTEST_XXX constants and fills either date or wd
	// with the corresponding value (none for NOWHERE, or a non-negative value for a column header item)
	wxColumnHeaderHitTestResult HitTest(
		const wxPoint	&locationPt );

	long GetSelectedItemIndex( void );
	void SetSelectedItemIndex(
		long				itemIndex );
	long GetItemCount( void );

	void DeleteItem(
		long				itemIndex );
	void AppendItem(
		const wxString		&textBuffer,
		long				textJust,
		long				extentX,
		bool				bActive,
		bool				bSortEnabled,
		bool				bSortAscending );
	wxString GetLabelText(
		long				itemIndex );
	void SetLabelText(
		long				itemIndex,
		const wxString		&textBuffer );
	long GetLabelJustification(
		long				itemIndex );
	void SetLabelJustification(
		long				itemIndex,
		long				textJust );

	wxPoint GetUIExtent(
		long				itemIndex );
	void SetUIExtent(
		long				itemIndex,
		wxPoint			&extentPt );
	bool GetFlagAttribute(
		long						itemIndex,
		wxColumnHeaderFlagAttr		flagEnum );
	bool SetFlagAttribute(
		long						itemIndex,
		wxColumnHeaderFlagAttr		flagEnum,
		bool						bFlagValue );

	// implementation only from now on
	// -------------------------------

	// embellish (override) some base class virtuals
	virtual void DoMoveWindow( int x, int y, int width, int height );
	virtual bool Enable( bool bEnable = true );
	virtual bool Show( bool bShow = true );
	virtual void DoSetSize( int x, int y, int width, int height, int sizeFlags );
	virtual wxSize DoGetBestSize( void ) const;

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
	void AppendItemList(
		const wxColumnHeaderItem		*itemList,
		long							itemCount );

	void OnClick_SelectOrToggleSort(
		long				itemIndex,
		bool				bToggleSortDirection );

	bool GetItemData(
		long							itemIndex,
		wxColumnHeaderItem				*info );
	bool SetItemData(
		long							itemIndex,
		const wxColumnHeaderItem		*info );
	wxColumnHeaderItem * GetItemRef(
		long			itemIndex );
	void RefreshItem(
		long			itemIndex );

	void SetViewDirty( void );
	void RecalculateItemExtents( void );
	void DisposeItemList( void );

	long Draw( void );

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
	// common part of all ctors
	void Init( void );

	// event handlers
	void OnPaint( wxPaintEvent &event );
	void OnClick( wxMouseEvent &event );
	void OnDoubleClick( wxMouseEvent &event );

	// event generator
	void GenerateEvent( wxEventType eventType );

protected:
	wxRect					m_NativeBoundsR;
	wxColumnHeaderItem		**m_ItemList;
	long					m_ItemCount;
	long					m_ItemSelected;
	bool					m_BUseUnicode;

	// fonts
	wxFont		m_normalFont;
	wxFont		m_boldFont;

	DECLARE_DYNAMIC_CLASS(wxColumnHeader)
	DECLARE_EVENT_TABLE()
	DECLARE_NO_COPY_CLASS(wxColumnHeader)
};

#endif // _WX_GENERIC_COLUMNHEADER_H
