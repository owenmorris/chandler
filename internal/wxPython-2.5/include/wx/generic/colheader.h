#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
	#pragma interface "colheader.h"
#endif

#ifndef _WX_GENERIC_COLUMNHEADER_H
#define _WX_GENERIC_COLUMNHEADER_H

#include "wx/control.h"			// the base class
#include "wx/dcclient.h"		// for wxPaintDC

class WXDLLEXPORT wxStaticText;

#if defined(__WXMSW__)
#if !defined(WC_HEADER)
#define WC_HEADERNOWIN32        "SysHeader"
#define WC_HEADERA              "SysHeader32"
#define WC_HEADERW              L"SysHeader32"

#if defined(UNICODE)
#define WC_HEADER               WC_HEADERW
#elif defined(_WIN32)
#define WC_HEADER               WC_HEADERA
#else
#define WC_HEADER               WC_HEADERNOWIN32
#endif
#endif

#define wxColumnHeaderNameStr		_T(WC_HEADER)
#else
#define wxColumnHeaderNameStr		_T("ColumnHeader")
#endif


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

	long GetLabelText(
		wxString		&textBuffer,
		long			&textJust );
	void SetLabelText(
		const wxString	&textBuffer,
		long			textJust );

	void GetUIExtent(
		long			&originX,
		long			&extentX );
	void SetUIExtent(
		long			originX,
		long			extentX );

	void GetFlags(
		bool			&bActive,
		bool			&bEnabled,
		bool			&bSortAscending );
	void SetFlags(
		bool			bActive,
		bool			bEnabled,
		bool			bSortAscending );

public:
	static long ConvertJust(
		long		sourceEnum,
		bool		bToNative );

public:
	wxRect					mNativeBoundsR;
	wxString				mLabelTextRef;
	unsigned long			mFontID;
	long					mTextJust;
	long					mImageID;
	long					mOriginX;
	long					mExtentX;
	bool					mBIsActive;
	bool					mBIsEnabled;
	bool					mBSortAscending;
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
		bool				bSortAscending );
	bool GetLabelText(
		long				itemIndex,
		wxString			&textBuffer,
		long				&textJust );
	bool SetLabelText(
		long				itemIndex,
		const wxString		&textBuffer,
		long				textJust );
	bool GetUIExtent(
		long			itemIndex,
		long			&originX,
		long			&extentX );
	bool SetUIExtent(
		long			itemIndex,
		long			originX,
		long			extentX );
	bool GetFlags(
		long			itemIndex,
		bool			&bActive,
		bool			&bEnabled,
		bool			&bSortAscending );
	bool SetFlags(
		long			itemIndex,
		bool			bActive,
		bool			bEnabled,
		bool			bSortAscending );

	// implementation only from now on
	// -------------------------------

	// forward these functions to all subcontrols
	virtual bool Enable(
		bool	bEnable = true );
	virtual bool Show(
		bool	bShow = true );

	virtual wxVisualAttributes GetDefaultAttributes( void ) const
		{ return GetClassDefaultAttributes( GetWindowVariant() ); }

	static wxVisualAttributes GetClassDefaultAttributes(
		wxWindowVariant variant = wxWINDOW_VARIANT_NORMAL );

protected:
	void AppendItemList(
		const wxColumnHeaderItem		*itemList,
		long							itemCount );

	void OnClick_DemoSortToggle(
		long				itemIndex );

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
		bool			bSelected,
		bool			bSortAscending );
	long Win32ItemDelete(
		long			itemIndex );
	long Win32ItemRefresh(
		long			itemIndex );
	long Win32ItemSelect(
		long			itemIndex,
		bool			bSelected,
		bool			bSortAscending );
#endif

protected:
	// common part of all ctors
	void Init( void );

	// event handlers
	void OnPaint( wxPaintEvent &event );
	void OnClick( wxMouseEvent &event );
	void OnDClick( wxMouseEvent &event );

	// override some base class virtuals
	virtual wxSize DoGetBestSize( void ) const;
	virtual void DoGetPosition( int *x, int *y ) const;
	virtual void DoGetSize( int *width, int *height ) const;
	virtual void DoSetSize( int x, int y, int width, int height, int sizeFlags );
	virtual void DoMoveWindow( int x, int y, int width, int height );

	// generate the given calendar event(s)
	void GenerateEvent( wxEventType type )
	{
	wxColumnHeaderEvent	event( this, type );

		(void)GetEventHandler()->ProcessEvent( event );
	}

	void GenerateEvents( wxEventType type1, wxEventType type2 )
	{
		GenerateEvent( type1 );
		GenerateEvent( type2 );
	}

protected:
	wxRect					mNativeBoundsR;
	wxColumnHeaderItem		**mItemList;
	long					mItemCount;
	long					mItemSelected;
	bool					mBUseUnicode;

	// fonts
	wxFont		m_normalFont;
	wxFont		m_boldFont;

	DECLARE_DYNAMIC_CLASS(wxColumnHeader)
	DECLARE_EVENT_TABLE()
	DECLARE_NO_COPY_CLASS(wxColumnHeader)
};

#endif // _WX_GENERIC_COLUMNHEADER_H
