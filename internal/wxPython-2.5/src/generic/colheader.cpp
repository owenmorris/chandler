///////////////////////////////////////////////////////////////////////////////
// Name:		generic/colheader.cpp
// Purpose:	generic implementation of a native-appearance column header
// Author:	David Surovell
// Modified by:
// Created:	01.01.2005
// RCS-ID:
// Copyright:
// License:
///////////////////////////////////////////////////////////////////////////////

// ============================================================================
// declarations
// ============================================================================

// ----------------------------------------------------------------------------
// headers
// ----------------------------------------------------------------------------

#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
	#pragma implementation "colheader.h"
#endif

// For compilers that support precompilation, includes "wx.h".
#include "wx/wxprec.h"

#if defined(__BORLANDC__)
	#pragma hdrstop
#endif

#if !defined(WX_PRECOMP)
//	#include "wx/dcclient.h"
	#include "wx/settings.h"
	#include "wx/brush.h"
	#include "wx/listbox.h"
#endif // WX_PRECOMP

//#if wxUSE_COLUMNHEADER

#if defined(__WXMSW__)
	#define _WIN32_WINNT	0x5010
	#include <commctrl.h>
#elif defined(__WXMAC__)
	#include <TextEdit.h>
#endif

#include "wx/colheader.h"


// ----------------------------------------------------------------------------
// wxWin macros
// ----------------------------------------------------------------------------

BEGIN_EVENT_TABLE(wxColumnHeader, wxControl)
	EVT_PAINT(wxColumnHeader::OnPaint)
	EVT_LEFT_DOWN(wxColumnHeader::OnClick)
	EVT_LEFT_DCLICK(wxColumnHeader::OnDoubleClick)
END_EVENT_TABLE()

#if wxUSE_EXTENDED_RTTI
WX_DEFINE_FLAGS( wxColumnHeaderStyle )

wxBEGIN_FLAGS( wxColumnHeaderStyle )
	// new style border flags:
	// we put them first to use them for streaming out
	wxFLAGS_MEMBER(wxBORDER_SIMPLE)
	wxFLAGS_MEMBER(wxBORDER_SUNKEN)
	wxFLAGS_MEMBER(wxBORDER_DOUBLE)
	wxFLAGS_MEMBER(wxBORDER_RAISED)
	wxFLAGS_MEMBER(wxBORDER_STATIC)
	wxFLAGS_MEMBER(wxBORDER_NONE)

	// old style border flags
	wxFLAGS_MEMBER(wxSIMPLE_BORDER)
	wxFLAGS_MEMBER(wxSUNKEN_BORDER)
	wxFLAGS_MEMBER(wxDOUBLE_BORDER)
	wxFLAGS_MEMBER(wxRAISED_BORDER)
	wxFLAGS_MEMBER(wxSTATIC_BORDER)
	wxFLAGS_MEMBER(wxBORDER)

	// standard window styles
	wxFLAGS_MEMBER(wxTAB_TRAVERSAL)
	wxFLAGS_MEMBER(wxCLIP_CHILDREN)
	wxFLAGS_MEMBER(wxTRANSPARENT_WINDOW)
	wxFLAGS_MEMBER(wxWANTS_CHARS)
	wxFLAGS_MEMBER(wxFULL_REPAINT_ON_RESIZE)
	wxFLAGS_MEMBER(wxALWAYS_SHOW_SB)
wxEND_FLAGS( wxColumnHeaderStyle )

IMPLEMENT_DYNAMIC_CLASS_XTI(wxColumnHeader, wxControl, "wx/colheader.h")

wxBEGIN_PROPERTIES_TABLE(wxColumnHeader)
	wxEVENT_RANGE_PROPERTY( Updated, wxEVT_COLUMNHEADER_SELCHANGED, wxEVT_COLUMNHEADER_DOUBLECLICKED, wxColumnHeaderEvent )
	wxHIDE_PROPERTY( Children )
	wxPROPERTY( 0 /*flags*/ , wxT("Helpstring"), wxT("group"))
	wxPROPERTY_FLAGS( WindowStyle, wxColumnHeaderStyle, long, SetWindowStyleFlag, GetWindowStyleFlag, , 0 /*flags*/, wxT("Helpstring"), wxT("group") ) // style
wxEND_PROPERTIES_TABLE()

wxBEGIN_HANDLERS_TABLE(wxColumnHeader)
wxEND_HANDLERS_TABLE()

wxCONSTRUCTOR_5( wxColumnHeader, wxWindow*, Parent, wxWindowID, Id, wxPoint, Position, wxSize, Size, long, WindowStyle )
#else
IMPLEMENT_DYNAMIC_CLASS(wxColumnHeader, wxControl)
#endif
IMPLEMENT_DYNAMIC_CLASS(wxColumnHeaderEvent, wxCommandEvent)

// ----------------------------------------------------------------------------
// events
// ----------------------------------------------------------------------------

DEFINE_EVENT_TYPE(wxEVT_COLUMNHEADER_SELCHANGED)
DEFINE_EVENT_TYPE(wxEVT_COLUMNHEADER_DOUBLECLICKED)

// ============================================================================
// implementation
// ============================================================================

// ----------------------------------------------------------------------------
// wxColumnHeader
// ----------------------------------------------------------------------------

wxColumnHeader::wxColumnHeader()
{
	Init();
}

wxColumnHeader::wxColumnHeader(
	wxWindow			*parent,
	wxWindowID			id,
	const wxPoint		&pos,
	const wxSize		&size,
	long				style,
	const wxString		&name )
{
	Init();

	(void)Create( parent, id, pos, size, style, name );
}

wxColumnHeader::~wxColumnHeader()
{
	DisposeItemList();
}

void wxColumnHeader::Init( void )
{
	m_NativeBoundsR.x =
	m_NativeBoundsR.y =
	m_NativeBoundsR.width =
	m_NativeBoundsR.height = 0;

	m_ItemList = NULL;
	m_ItemCount = 0;
	m_ItemSelected = wxCOLUMNHEADER_HITTEST_NoPart;

#if wxUSE_UNICODE
	m_BUseUnicode = true;
#else
	m_BUseUnicode = false;
#endif
}

void wxColumnHeader::SetUnicodeFlag(
	bool			bSetFlag )
{
	m_BUseUnicode = bSetFlag;
}

bool wxColumnHeader::Create(
	wxWindow			*parent,
	wxWindowID			id,
	const wxPoint		&pos,
	const wxSize		&size,
	long				style,
	const wxString		&name )
{
wxString		localName;
bool			bResultV;

	// NB: the CreateControl call crashed on MacOS...
#if defined(__WXMSW__)
	localName = _T(WC_HEADER);
	bResultV =
		CreateControl(
			parent, id, pos, size,
			style, wxDefaultValidator, localName );

	if (bResultV)
	{
	WXDWORD		msStyle, exstyle;

		msStyle = MSWGetStyle( style, &exstyle );
		bResultV = MSWCreateControl( localName, msStyle, pos, size, wxEmptyString, exstyle );
	}

#else
	localName = name;
	bResultV =
		wxControl::Create(
			parent, id, pos, size,
			style, wxDefaultValidator, localName );
#endif

	if (bResultV)
	{
		// NB: is any of this necessary??

#if 0
		// needed to get the arrow keys normally used for dialog navigation
		SetWindowStyle( style );

		// we need to set the position as well because the main control position is not
		// the same as the one specified in pos if we have the controls above it
		SetBestSize( size );
		SetPosition( pos );
#endif
	}

	// FIXME: sloppy hack
	wxControl::DoGetPosition( &(m_NativeBoundsR.x), &(m_NativeBoundsR.y) );
	wxControl::DoGetSize( &(m_NativeBoundsR.width), &(m_NativeBoundsR.height) );

#if 0
	// for debugging
	if (m_NativeBoundsR.x < 0)
		m_NativeBoundsR.x = 0;
	if (m_NativeBoundsR.y < 0)
		m_NativeBoundsR.y = 0;
	if (m_NativeBoundsR.width)
		m_NativeBoundsR.width = 200;
	if (m_NativeBoundsR.height)
		m_NativeBoundsR.height = 17;
#endif

	return bResultV;
}

// virtual
bool wxColumnHeader::Destroy( void )
{
bool		bResultV;

	bResultV = wxControl::Destroy();

	return bResultV;
}

// virtual
bool wxColumnHeader::Show(
	bool		bShow )
{
bool		bResultV;

	bResultV = wxControl::Show( bShow );

	return bResultV;
}

// virtual
bool wxColumnHeader::Enable(
	bool		bEnable )
{
bool		bResultV;

	bResultV = wxControl::Enable( bEnable );

	for (long i=0; i<m_ItemCount; i++)
	{
		if ((m_ItemList != NULL) && (m_ItemList[i] != NULL))
			m_ItemList[i]->SetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_Enabled, bEnable );

#if defined(__WXMSW__)
	bool		bSelected, bSortEnabled, bSortAscending;

		bSelected = false;
		bSortEnabled = false;
		bSortAscending = false;
		if ((m_ItemList != NULL) && (m_ItemList[i] != NULL))
		{
			bSelected = m_ItemList[i]->GetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_Selected );
			bSortEnabled = m_ItemList[i]->GetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_SortEnabled );
			bSortAscending = m_ItemList[i]->GetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_SortDirection );
		}
		(void)Win32ItemSelect( i, bSelected, bSortEnabled, bSortAscending );
#endif
	}

	return bResultV;
}

// ----------------------------------------------------------------------------
// size management
// ----------------------------------------------------------------------------

// virtual
void wxColumnHeader::DoMoveWindow(
	int		x,
	int		y,
	int		width,
	int		height )
{
int		yDiff;

	yDiff = 0;

	wxControl::DoMoveWindow( x, y + yDiff, width, height - yDiff );

	// FIXME: sloppy hack
	wxControl::DoGetPosition( &(m_NativeBoundsR.x), &(m_NativeBoundsR.y) );
}

// NB: is this implementation necessary ??
//
// virtual
wxSize wxColumnHeader::DoGetBestSize( void ) const
{
wxCoord	width, height;

	// best width is parent's width; height is fixed by native drawing routines
	GetParent()->GetClientSize( &width, &height );

#if defined(__WXMSW__)
	{
	HDLAYOUT	hdl;
	WINDOWPOS	wp;
	HWND		targetViewRef;
	RECT		boundsR;

		targetViewRef = GetHwnd();
		boundsR.left = boundsR.top = 0;
		boundsR.right = width;
		boundsR.bottom = height;
		hdl.prc = &boundsR;
		hdl.pwpos = &wp;
		if (Header_Layout( targetViewRef, (LPARAM)&hdl ) != 0)
			height = wp.cy;
	}

#elif defined(__WXMAC__)
	{
	SInt32		standardHeight;
	OSStatus		errStatus;

		errStatus = GetThemeMetric( kThemeMetricListHeaderHeight, &standardHeight );
		height = standardHeight;
	}

#else
	height = 20;
#endif

#if 0
	if (! HasFlag( wxBORDER_NONE ))
	{
		// the border would clip the last line otherwise
		height += 6;
		width += 4;
	}
#endif

wxSize	best( width, height );

	CacheBestSize( best );

	return best;
}

// virtual
void wxColumnHeader::DoSetSize(
	int		x,
	int		y,
	int		width,
	int		height,
	int		sizeFlags )
{
	wxControl::DoSetSize( x, y, width, height, sizeFlags );

	// FIXME: sloppy hack
	wxControl::DoGetPosition( &(m_NativeBoundsR.x), &(m_NativeBoundsR.y) );
	wxControl::DoGetSize( &(m_NativeBoundsR.width), &(m_NativeBoundsR.height) );

	RecalculateItemExtents();
}

// ----------------------------------------------------------------------------
// drawing
// ----------------------------------------------------------------------------

// virtual
void wxColumnHeader::OnPaint(
	wxPaintEvent		&event )
{
#if !defined(__WXMSW__)
	Draw();
#else
	event.Skip();
//	::DefWindowProc( GetHwnd(), WM_PAINT, 0, 0 );
//	wxControl::MSWWindowProc( WM_PAINT, 0, 0 );
//	wxWindow::OnPaint( event );
//	wxControl::OnPaint( event );
#endif
}

// ----------------------------------------------------------------------------
// mouse handling
// ----------------------------------------------------------------------------

void wxColumnHeader::OnDoubleClick(
	wxMouseEvent		&event )
{
long		itemIndex;

	itemIndex = HitTest( event.GetPosition() );
	if (itemIndex >= wxCOLUMNHEADER_HITTEST_ItemZero)
	{
		// NB: just call the single click handler for the present
		OnClick( event );

		// NB: unused for the present
		//GenerateEvent( wxEVT_COLUMNHEADER_DOUBLECLICKED );
	}
	else
	{
		event.Skip();
	}
}

void wxColumnHeader::OnClick(
	wxMouseEvent		&event )
{
long		itemIndex;

	itemIndex = HitTest( event.GetPosition() );
	switch (itemIndex)
	{
	default:
		if (itemIndex >= wxCOLUMNHEADER_HITTEST_ItemZero)
		{
			OnClick_SelectOrToggleSort( itemIndex, true );
			GenerateEvent( wxEVT_COLUMNHEADER_SELCHANGED );
			break;
		}
		else
		{
			// unknown message - unhandled - fall through
			//wxLogDebug( _T("wxColumnHeader::OnClick - unknown hittest code") );
		}

	case wxCOLUMNHEADER_HITTEST_NoPart:
		event.Skip();
		break;
	}
}

void wxColumnHeader::OnClick_SelectOrToggleSort(
	long				itemIndex,
	bool				bToggleSortDirection )
{
long			curSelectionIndex;

	curSelectionIndex = GetSelectedItemIndex();
	if (itemIndex != m_ItemSelected)
	{
		SetSelectedItemIndex( itemIndex );
	}
	else if (bToggleSortDirection)
	{
	wxColumnHeaderItem	*item;
	bool				bSortFlag;

		item = ((m_ItemList != NULL) ? m_ItemList[itemIndex] : NULL);
		if (item != NULL)
			if (item->GetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_SortEnabled ))
			{
				bSortFlag = item->GetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_SortDirection );
				item->SetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_SortDirection, ! bSortFlag );

#if defined(__WXMSW__)
				Win32ItemRefresh( itemIndex );
#endif

				SetViewDirty();
			}

		// for testing: can induce text wrapping outside of bounds rect
//		item->SetLabelText( _wxT("같같 YOW! 같같") );
	}
}

// static
wxVisualAttributes
wxColumnHeader::GetClassDefaultAttributes(
	wxWindowVariant		variant )
{
	// FIXME: is this dependency necessary?
	// use the same color scheme as wxListBox
	return wxListBox::GetClassDefaultAttributes( variant );
}

// ================
#if 0
#pragma mark -
#endif

void wxColumnHeader::DisposeItemList( void )
{
	if (m_ItemList != NULL)
	{
		for (long i=0; i<m_ItemCount; i++)
			delete m_ItemList[i];

		free( m_ItemList );
		m_ItemList = NULL;
	}

	m_ItemCount = 0;
	m_ItemSelected = wxCOLUMNHEADER_HITTEST_NoPart;
}

long wxColumnHeader::GetSelectedItemIndex( void )
{
	return m_ItemSelected;
}

void wxColumnHeader::SetSelectedItemIndex(
	long			itemIndex )
{
bool		bSelected;

	if ((itemIndex >= 0) && (itemIndex < m_ItemCount))
		if (m_ItemSelected != itemIndex)
		{
			for (long i=0; i<m_ItemCount; i++)
			{
				bSelected = (i == itemIndex);
				if ((m_ItemList != NULL) && (m_ItemList[i] != NULL))
					m_ItemList[i]->SetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_Selected, bSelected );

#if defined(__WXMSW__)
			bool		bSortEnabled, bSortAscending;

				bSortEnabled = false;
				bSortAscending = false;
				if ((m_ItemList != NULL) && (m_ItemList[i] != NULL))
				{
					bSortEnabled = m_ItemList[i]->GetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_SortEnabled );
					bSortAscending = m_ItemList[i]->GetFlagAttribute( wxCOLUMNHEADER_FLAGATTR_SortDirection );
				}

				(void)Win32ItemSelect( i, bSelected, bSortEnabled, bSortAscending );
#endif
			}

			m_ItemSelected = itemIndex;

			SetViewDirty();
		}
}

long wxColumnHeader::GetItemCount( void )
{
	return (long)m_ItemCount;
}

void wxColumnHeader::DeleteItem(
	long			itemIndex )
{
	if ((itemIndex >= 0) && (itemIndex < m_ItemCount))
	{
#if defined(__WXMSW__)
		(void)Win32ItemDelete( itemIndex );
#endif

		if (m_ItemList != NULL)
		{
			if (m_ItemCount > 1)
			{
				// delete the target item
				delete m_ItemList[itemIndex];

				// close the list hole
				for (long i=itemIndex; i<m_ItemCount-1; i++)
					m_ItemList[i] = m_ItemList[i + 1];

				// leave a NULL spot at the end
				m_ItemList[m_ItemCount - 1] = NULL;
				m_ItemCount--;

				// recalculate item origins
				RecalculateItemExtents();
			}
			else
				DisposeItemList();
		}
	}
}

void wxColumnHeader::AppendItem(
	const wxString	&textBuffer,
	long			textJust,
	long			extentX,
	bool			bSelected,
	bool			bSortEnabled,
	bool			bSortAscending )
{
wxColumnHeaderItem		itemInfo;
wxPoint					targetExtent;
long					originX;

	// set invariant values
	itemInfo.m_NativeBoundsR = m_NativeBoundsR;
	itemInfo.m_BEnabled = true;

#if defined(__WXMAC__)
	itemInfo.m_FontID = kThemeSmallSystemFont;		// or kThemeSystemFontTag, kThemeViewsFontTag
#else
	itemInfo.m_FontID = 0;
#endif

	itemInfo.m_LabelTextRef = textBuffer;
	itemInfo.m_TextJust = textJust;
	itemInfo.m_ExtentX = extentX;
	itemInfo.m_BSelected = ((m_ItemSelected < 0) ? bSelected : false);
	itemInfo.m_BSortEnabled = bSortEnabled;
	itemInfo.m_BSortAscending = bSortAscending;

	targetExtent = GetUIExtent( m_ItemCount - 1 );
	originX = ((targetExtent.x > 0) ? targetExtent.x : 0);

	itemInfo.m_OriginX = originX + targetExtent.y;
	AppendItemList( &itemInfo, 1 );
}

void wxColumnHeader::AppendItemList(
	const wxColumnHeaderItem		*itemList,
	long							itemCount )
{
wxColumnHeaderItem	**newItemList;
long				targetIndex, i;
bool				bIsSelected;

	if ((itemList == NULL) || (itemCount <= 0))
		return;

	// allocate new item list and copy the original list items into it
	newItemList = (wxColumnHeaderItem**)calloc( m_ItemCount + itemCount, sizeof(wxColumnHeaderItem*) );
	if (m_ItemList != NULL)
	{
		for (i=0; i<m_ItemCount; i++)
			newItemList[i] = m_ItemList[i];

		free( m_ItemList );
	}
	m_ItemList = newItemList;

	// append the new items
	for (i=0; i<itemCount; i++)
	{
		targetIndex = m_ItemCount + i;
		m_ItemList[targetIndex] = new wxColumnHeaderItem( &itemList[i] );

		bIsSelected = (m_ItemList[targetIndex]->m_BSelected && m_ItemList[targetIndex]->m_BEnabled);

#if defined(__WXMSW__)
		Win32ItemInsert(
			targetIndex, m_ItemList[targetIndex]->m_ExtentX,
			m_ItemList[targetIndex]->m_LabelTextRef, m_ItemList[targetIndex]->m_TextJust,
			m_BUseUnicode,
			bIsSelected,
			m_ItemList[targetIndex]->m_BSortEnabled,
			m_ItemList[targetIndex]->m_BSortAscending );
#endif

		if (bIsSelected && (m_ItemSelected < 0))
			m_ItemSelected = targetIndex;
	}

	// update the counter
	m_ItemCount += itemCount;
}

bool wxColumnHeader::GetItemData(
	long							itemIndex,
	wxColumnHeaderItem				*info )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
		itemRef->GetItemData( info );

	return bResultV;
}

bool wxColumnHeader::SetItemData(
	long							itemIndex,
	const wxColumnHeaderItem		*info )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
		itemRef->SetItemData( info );

	return bResultV;
}

wxColumnHeaderItem * wxColumnHeader::GetItemRef(
	long			itemIndex )
{
	if ((itemIndex >= 0) && (itemIndex < m_ItemCount))
		return m_ItemList[itemIndex];
	else
		return NULL;
}

wxString wxColumnHeader::GetLabelText(
	long			itemIndex )
{
wxColumnHeaderItem		*itemRef;
wxString				textBuffer;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		(void)itemRef->GetLabelText( textBuffer );
	}
	else
	{
		textBuffer = _T("");
	}

	return textBuffer;
}

void wxColumnHeader::SetLabelText(
	long				itemIndex,
	const wxString		&textBuffer )
{
wxColumnHeaderItem		*itemRef;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
	{
		itemRef->SetLabelText( textBuffer );
		RefreshItem( itemIndex );
	}
}

long wxColumnHeader::GetLabelJustification(
	long				itemIndex )
{
wxColumnHeaderItem		*itemRef;
long						textJust;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
		textJust = itemRef->GetLabelJustification();
	else
		textJust = 0;

	return textJust;
}

void wxColumnHeader::SetLabelJustification(
	long				itemIndex,
	long				textJust )
{
wxColumnHeaderItem		*itemRef;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
	{
		itemRef->SetLabelJustification( textJust );
		RefreshItem( itemIndex );
	}
}

wxPoint wxColumnHeader::GetUIExtent(
	long			itemIndex )
{
wxColumnHeaderItem		*itemRef;
wxPoint					extentPt;
long					originX, extentX;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		itemRef->GetUIExtent( originX, extentX );
	}
	else
	{
		originX =
		extentX = 0;
	}

	extentPt.x = originX;
	extentPt.y = extentX;

	return extentPt;
}

void wxColumnHeader::SetUIExtent(
	long			itemIndex,
	wxPoint		&extentPt )
{
wxColumnHeaderItem		*itemRef;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
	{
		itemRef->SetUIExtent( extentPt.x, extentPt.y );
		RefreshItem( itemIndex );
	}
}

bool wxColumnHeader::GetFlagAttribute(
	long						itemIndex,
	wxColumnHeaderFlagAttr		flagEnum )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
		bResultV = itemRef->GetFlagAttribute( flagEnum );

	return bResultV;
}

bool wxColumnHeader::SetFlagAttribute(
	long						itemIndex,
	wxColumnHeaderFlagAttr		flagEnum,
	bool						bFlagValue )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		if (itemRef->SetFlagAttribute( flagEnum, bFlagValue ))
			RefreshItem( itemIndex );
	}

	return bResultV;
}

wxColumnHeaderHitTestResult wxColumnHeader::HitTest(
	const wxPoint		&locationPt )
{
wxColumnHeaderHitTestResult		resultV;

	resultV = wxCOLUMNHEADER_HITTEST_NoPart;

#if defined(__WXMSW__)
RECT		boundsR;
HWND		targetViewRef;
long		itemCount, i;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		//wxLogDebug( _T("targetViewRef = GetHwnd failed (NULL)") );
		return resultV;
	}

	itemCount = Header_GetItemCount( targetViewRef );
	for (i=0; i<itemCount; i++)
	{
		Header_GetItemRect( targetViewRef, i, &boundsR );
		if ((locationPt.x >= boundsR.left) && (locationPt.x < boundsR.right)
			&& (locationPt.y >= boundsR.top) && (locationPt.y < boundsR.bottom))
		{
			resultV = (wxColumnHeaderHitTestResult)i;
			break;
		}
	}
#else

	for (long i=0; i<m_ItemCount; i++)
		if (m_ItemList[i] != NULL)
			if (m_ItemList[i]->HitTest( locationPt ) != 0)
			{
				resultV = (wxColumnHeaderHitTestResult)i;
				break;
			}
#endif

	return resultV;
}

// NB: this routine is unused for Win32
//
long wxColumnHeader::Draw( void )
{
long		errStatus;

	errStatus = 0;

#if !defined(__WXMSW__)
	for (long i=0; i<m_ItemCount; i++)
		errStatus |= m_ItemList[i]->DrawSelf();
#endif

	return (long)errStatus;
}

void wxColumnHeader::SetViewDirty( void )
{
	Refresh( true, NULL );
}

void wxColumnHeader::RefreshItem(
	long			itemIndex )
{
#if defined(__WXMSW__)
	// NB: need to update native item
	Win32ItemRefresh( itemIndex );
#endif
}

void wxColumnHeader::RecalculateItemExtents( void )
{
long		originX, i;

	if (m_ItemList != NULL)
	{
		originX = 0;
		for (i=0; i<m_ItemCount; i++)
			if (m_ItemList[i] != NULL)
			{
				m_ItemList[i]->m_NativeBoundsR = m_NativeBoundsR;
				m_ItemList[i]->m_OriginX = originX;
				originX += m_ItemList[i]->m_ExtentX;
			}
	}
}

// ================
#if 0
#pragma mark -
#endif

#if defined(__WXMSW__)
// virtual
WXDWORD wxColumnHeader::MSWGetStyle(
	long			style,
	WXDWORD			*exstyle ) const
{
WXDWORD		msStyle;

	style = (style & ~wxBORDER_MASK) | wxBORDER_NONE;

	msStyle = wxControl::MSWGetStyle( style, exstyle );
	msStyle |= HDS_BUTTONS | HDS_FLAT | HDS_HORZ;
	msStyle |= WS_CLIPSIBLINGS;

	return msStyle;
}

long wxColumnHeader::Win32ItemInsert(
	long			iInsertAfter,
	long			nWidth,
	const void		*titleText,
	long			textJust,
	bool			bUseUnicode,
	bool			bSelected,
	bool			bSortEnabled,
	bool			bSortAscending )
{
HDITEM		itemData;
HWND		targetViewRef;
long		resultV;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		//wxLogDebug( _T("Win32ItemInsert - GetHwnd failed (NULL)") );
		return (-1L);
	}

//	wxLogDebug( _T("Win32ItemInsert - item text [%s]"), (const TCHAR*)titleText );

	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_TEXT | HDI_FORMAT | HDI_WIDTH;
	itemData.pszText = (LPSTR)titleText;
	itemData.cxy = (int)nWidth;
	itemData.cchTextMax = 256;
//	itemData.cchTextMax = sizeof(itemData.pszText) / sizeof(itemData.pszText[0]);
	itemData.fmt = wxColumnHeaderItem::ConvertJust( textJust, TRUE ) | HDF_STRING;
	if (bSelected && bSortEnabled)
		itemData.fmt |= (bSortAscending ? HDF_SORTUP : HDF_SORTDOWN);

	resultV = (long)Header_InsertItem( targetViewRef, (int)iInsertAfter, &itemData );
//	resultV = (long)SendMessage( mViewRef, bUseUnicode ? HDM_INSERTITEMW : HDM_INSERTITEMA, (WPARAM)iInsertAfter, (LPARAM)&itemData );

	if (resultV < 0)
		wxLogDebug( _T("Win32ItemInsert - SendMessage failed") );

	return resultV;
}

long wxColumnHeader::Win32ItemDelete(
	long			itemIndex )
{
HWND		targetViewRef;
long		resultV;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		//wxLogDebug( _T("Win32ItemDelete - GetHwnd failed (NULL)") );
		return (-1L);
	}

	resultV = (long)Header_DeleteItem( targetViewRef, itemIndex );

	if (resultV == 0)
		wxLogDebug( _T("Win32ItemDelete - SendMessage failed") );

	return resultV;
}

long wxColumnHeader::Win32ItemRefresh(
	long			itemIndex )
{
wxColumnHeaderItem		*itemRef;
HDITEM					itemData;
HWND					targetViewRef;
long					resultV;

	itemRef = GetItemRef( itemIndex );
	if (itemRef == NULL)
		return (-1L);

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		//wxLogDebug( _T("Win32ItemRefresh - GetHwnd failed (NULL)") );
		return (-1L);
	}

	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_FORMAT | HDI_WIDTH;
	resultV = (long)Header_GetItem( targetViewRef, itemIndex, &itemData );

	itemData.mask = HDI_TEXT | HDI_FORMAT | HDI_WIDTH;
	itemData.pszText = (LPSTR)(itemRef->m_LabelTextRef.c_str());
	itemData.cxy = (int)(itemRef->m_ExtentX);
	itemData.cchTextMax = 256;
//	itemData.cchTextMax = sizeof(itemData.pszText) / sizeof(itemData.pszText[0]);
	itemData.fmt = wxColumnHeaderItem::ConvertJust( itemRef->m_TextJust, TRUE ) | HDF_STRING;

	itemData.fmt &= ~(HDF_SORTDOWN | HDF_SORTUP);
	if (itemRef->m_BSelected && itemRef->m_BEnabled && itemRef->m_BSortEnabled)
		itemData.fmt |= (itemRef->m_BSortAscending ? HDF_SORTUP : HDF_SORTDOWN);

	resultV = (long)Header_SetItem( targetViewRef, itemIndex, &itemData );
//	resultV = (long)SendMessage( mViewRef, itemRef->m_BTextUnicode ? HDM_SETITEMW : HDM_SETITEMA, (WPARAM)itemIndex, (LPARAM)&itemData );

	if (resultV == 0)
		wxLogDebug( _T("Win32ItemRefresh - SendMessage failed") );

	return resultV;
}

long wxColumnHeader::Win32ItemSelect(
	long			itemIndex,
	bool			bSelected,
	bool			bSortEnabled,
	bool			bSortAscending )
{
HDITEM		itemData;
HWND		targetViewRef;
long		resultV;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		//wxLogDebug( _T("Win32ItemSelect - GetHwnd failed (NULL)") );
		return (-1L);
	}

	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_FORMAT | HDI_WIDTH;
	resultV = (long)Header_GetItem( targetViewRef, itemIndex, &itemData );

	itemData.fmt &= ~(HDF_SORTDOWN | HDF_SORTUP);
	if (bSelected && bSortEnabled)
		itemData.fmt |= (bSortAscending ? HDF_SORTUP : HDF_SORTDOWN);

	resultV = (long)Header_SetItem( targetViewRef, itemIndex, &itemData );
//	resultV = (long)SendMessage( mViewRef, itemRef->mBTextUnicode ? HDM_SETITEMW : HDM_SETITEMA, (WPARAM)itemIndex, (LPARAM)&itemData );

	if (resultV == 0)
		wxLogDebug( _T("Win32ItemSelect - SendMessage failed") );

	return resultV;
}
#endif

// ================
#if 0
#pragma mark -
#endif

#if 0
// static
void wxColumnHeader::GetDefaultRect(
	HWND			viewRef,
	wxRect			&boundsR )
{
	boundsR.left =
	boundsR.top =
	boundsR.right =
	boundsR.bottom = 0;

	if (viewRef != NULL)
	{
#if defined(__WXMSW__)
		GetClientRect( viewRef, boundsR );
#else
#endif

		// FIXME: hacky sizing stuff, but practical for the moment...
		OffsetRect( boundsR, -boundsR->left, -boundsR->top );
		boundsR->bottom = boundsR->top + 20;
	}
}
#endif

void wxColumnHeader::GenerateEvent(
	wxEventType		eventType )
{
wxColumnHeaderEvent	event( this, eventType );

	(void)GetEventHandler()->ProcessEvent( event );
}

// ================
#if 0
#pragma mark -
#endif

// ----------------------------------------------------------------------------
// wxColumnHeaderEvent
// ----------------------------------------------------------------------------

wxColumnHeaderEvent::wxColumnHeaderEvent(
	wxColumnHeader	*col,
	wxEventType		type )
	:
	wxCommandEvent( type, col->GetId() )
{
	SetEventObject( col );
}

void wxColumnHeaderEvent::Init( void )
{
}

// ================
#if 0
#pragma mark -
#endif

wxColumnHeaderItem::wxColumnHeaderItem()
	:
	m_FontID( 0 )
	, m_TextJust( 0 )
	, m_ImageID( -1 )
	, m_OriginX( 0 )
	, m_ExtentX( 0 )
	, m_BEnabled( FALSE )
	, m_BSelected( FALSE )
	, m_BSortEnabled( FALSE )
	, m_BSortAscending( FALSE )
{
}

wxColumnHeaderItem::wxColumnHeaderItem(
	const wxColumnHeaderItem		*info )
	:
	m_FontID( 0 )
	, m_TextJust( 0 )
	, m_ImageID( -1 )
	, m_OriginX( 0 )
	, m_ExtentX( 0 )
	, m_BEnabled( FALSE )
	, m_BSelected( FALSE )
	, m_BSortEnabled( FALSE )
	, m_BSortAscending( FALSE )
{
	SetItemData( info );
}

wxColumnHeaderItem::~wxColumnHeaderItem()
{
}

// NB: a copy and nothing else...
//
void wxColumnHeaderItem::GetItemData(
	wxColumnHeaderItem			*info )
{
	if (info == NULL)
		return;

	info->m_NativeBoundsR = m_NativeBoundsR;
	info->m_FontID = m_FontID;
	info->m_ImageID = m_ImageID;
	info->m_TextJust = m_TextJust;
	info->m_OriginX = m_OriginX;
	info->m_ExtentX = m_ExtentX;
	info->m_BEnabled = m_BEnabled;
	info->m_BSelected = m_BSelected;
	info->m_BSortEnabled = m_BSortEnabled;
	info->m_BSortAscending = m_BSortAscending;

	GetLabelText( info->m_LabelTextRef );
}

void wxColumnHeaderItem::SetItemData(
	const wxColumnHeaderItem		*info )
{
	if (info == NULL)
		return;

	m_NativeBoundsR = info->m_NativeBoundsR;
	m_FontID = info->m_FontID;
	m_ImageID = info->m_ImageID;
	m_TextJust = info->m_TextJust;
	m_OriginX = info->m_OriginX;
	m_ExtentX = info->m_ExtentX;
	m_BEnabled = info->m_BEnabled;
	m_BSelected = info->m_BSelected;
	m_BSortEnabled = info->m_BSortEnabled;
	m_BSortAscending = info->m_BSortAscending;

	SetLabelText( info->m_LabelTextRef );
}

void wxColumnHeaderItem::GetLabelText(
	wxString			&textBuffer )
{
	textBuffer = m_LabelTextRef;
}

void wxColumnHeaderItem::SetLabelText(
	const wxString		&textBuffer )
{
	m_LabelTextRef = textBuffer;
}

long wxColumnHeaderItem::GetLabelJustification( void )
{
	return m_TextJust;
}

void wxColumnHeaderItem::SetLabelJustification(
	long				textJust )
{
	m_TextJust = textJust;
}

void wxColumnHeaderItem::GetUIExtent(
	long			&originX,
	long			&extentX )
{
	originX = m_OriginX;
	extentX = m_ExtentX;
}

void wxColumnHeaderItem::SetUIExtent(
	long			originX,
	long			extentX )
{
	// FIXME: range-check these properly!
	if (originX >= 0)
		m_OriginX = originX;
	if (extentX >= 0)
		m_ExtentX = extentX;
}

bool wxColumnHeaderItem::GetFlagAttribute(
	wxColumnHeaderFlagAttr		flagEnum )
{
bool			bResult;

	bResult = false;

	switch (flagEnum)
	{
	case wxCOLUMNHEADER_FLAGATTR_Enabled:
		bResult = m_BEnabled;
		break;

	case wxCOLUMNHEADER_FLAGATTR_Selected:
		bResult = m_BSelected;
		break;

	case wxCOLUMNHEADER_FLAGATTR_SortEnabled:
		bResult = m_BSortEnabled;
		break;

	case wxCOLUMNHEADER_FLAGATTR_SortDirection:
		bResult = m_BSortAscending;
		break;

	default:
		break;
	}

	return bResult;
}

bool wxColumnHeaderItem::SetFlagAttribute(
	wxColumnHeaderFlagAttr		flagEnum,
	bool						bFlagValue )
{
bool			bResult;

	bResult = true;

	switch (flagEnum)
	{
	case wxCOLUMNHEADER_FLAGATTR_Enabled:
		m_BEnabled = bFlagValue;
		break;

	case wxCOLUMNHEADER_FLAGATTR_Selected:
		m_BSelected = bFlagValue;
		break;

	case wxCOLUMNHEADER_FLAGATTR_SortEnabled:
		m_BSortEnabled = bFlagValue;
		break;

	case wxCOLUMNHEADER_FLAGATTR_SortDirection:
		m_BSortAscending = bFlagValue;
		break;

	default:
		bResult = false;
		break;
	}

	return bResult;
}

long wxColumnHeaderItem::HitTest(
	const wxPoint		&locationPt )
{
long		targetX, resultV;

//	targetX = locationPt.x - m_NativeBoundsR.x;
	targetX = locationPt.x;
	resultV = ((targetX >= m_OriginX) && (targetX < m_OriginX + m_ExtentX));

	return resultV;
}

long wxColumnHeaderItem::DrawSelf( void )
{
#if defined(__WXMSW__)
	// NB: implementation not needed ??
	return 0;

#elif defined(__WXMAC__)
ThemeButtonDrawInfo		drawInfo;
Rect					qdBoundsR;
long					nativeTextJust;
OSStatus				errStatus;

	// is this item beyond the right edge?
	if (m_OriginX >= m_NativeBoundsR.width)
	{
		//wxLogDebug( _T("wxColumnHeaderItem::DrawSelf - bailout!") );
		return (-1L);
	}

	errStatus = noErr;

//	qdBoundsR.left = m_NativeBoundsR.x + m_OriginX;
//	qdBoundsR.top = m_NativeBoundsR.y;
	qdBoundsR.left = m_OriginX;
	qdBoundsR.top = 0;
	qdBoundsR.right = qdBoundsR.left + m_ExtentX + 1;
	if (qdBoundsR.right > m_NativeBoundsR.width)
		qdBoundsR.right = m_NativeBoundsR.width;
	qdBoundsR.bottom = qdBoundsR.top + m_NativeBoundsR.height;

	// a broken, dead attempt to tinge the background
// Collection	origCol, newCol;
// RGBColor	tintRGB = { 0xFFFF, 0x0000, 0xFFFF };
//	errStatus = SetAppearanceTintColor( &tintRGB, origCol, newCol );

	if (m_BEnabled)
		drawInfo.state = (m_BSelected ? kThemeStateActive: kThemeStateInactive);
	else
		drawInfo.state = (m_BSelected ? kThemeStateUnavailable : kThemeStateUnavailableInactive);
//	drawInfo.state = kThemeStatePressed;

	drawInfo.value = (SInt32)m_BSelected;	// zero draws w/o theme background shading

	drawInfo.adornment = (m_BSortAscending ? kThemeAdornmentNone : kThemeAdornmentArrowDoubleArrow);
//	drawInfo.adornment = kThemeAdornmentNone;					// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentDefault;				// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentHeaderButtonShadowOnly;	// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentArrowDoubleArrow;		// doesn't work - same as "up-arrow" !!
//	drawInfo.adornment = kThemeAdornmentHeaderMenuButton;		// right-pointing arrow on left side
//	drawInfo.adornment = kThemeAdornmentHeaderButtonSortUp;
//	drawInfo.adornment = kThemeAdornmentArrowDownArrow;

	// NB: DrawThemeButton height is fixed, regardless of the boundsRect argument!
	if (m_BSelected && ! m_BSortEnabled)
		MacDrawThemeBackgroundNoArrows( &qdBoundsR );
	else
		errStatus = DrawThemeButton( &qdBoundsR, kThemeListHeaderButton, &drawInfo, NULL, NULL, NULL, 0 );

	// end of the dead attempt to tinge the background
//	errStatus = RestoreTheme( origCol, newCol );

	// exclude button adornment areas from further drawing consideration
	qdBoundsR.left += 4;
	qdBoundsR.right -= 16;
	qdBoundsR.top += 1;

	nativeTextJust = ConvertJust( m_TextJust, TRUE );

	if (! m_LabelTextRef.IsEmpty())
	{
	CFStringRef			cfLabelText;
	TextEncoding		targetEncoding;
	bool				bUseUnicode;

		bUseUnicode = FALSE;
		targetEncoding = (bUseUnicode ? kCFStringEncodingUnicode : kCFStringEncodingMacRoman);
		cfLabelText = CFStringCreateWithCString( NULL, (const char*)m_LabelTextRef, targetEncoding );
		if (cfLabelText != NULL)
		{
			errStatus =
				(OSStatus)DrawThemeTextBox(
					cfLabelText, m_FontID, drawInfo.state, true,
					&qdBoundsR, m_TextJust, NULL );

			CFRelease( cfLabelText );
		}
	}

#if 0
	// FIX-ME: need implementation
	// TO-DO: can label text and an bitmap (icon) be shown simultaneously?
	if (m_ImageID != (-1))
	{
//	IconSuiteRef	iconRef;
//		errStatus = GetIconSuite( &iconRef, (SInt16)mIconRef, kSelectorSmall32Bit );

	IconAlignmentType	icAlign;
	IconTransformType	icTransform;

		switch (nativeTextJust)
		{
		case teJustLeft:	icAlign = kAlignCenterLeft;			break;
		case teJustRight:	icAlign = kAlignCenterRight;		break;
		default:			icAlign = kAlignHorizontalCenter;	break;
		}
		icTransform = kTransformNone;
		errStatus = (long)PlotIconID( &qdBoundsR, icAlign, icTransform, (SInt16)mImageID );
	}
#endif

	return (long)errStatus;
#else

#if 0		// copied from generic wxRenderer
const int			kCorner = 1;
const wxCoord		x = rect.x;
const wxCoord		y = rect.y;
const wxCoord		w = rect.width;
const wxCoord		h = rect.height;

	wxClientDC	dc( this );
	dc.SetBrush( *wxTRANSPARENT_BRUSH );

	// (outer) right and bottom
	dc.SetPen( m_penBlack );
	dc.DrawLine( x + w + 1 - kCorner, y, x + w, y + h );
	dc.DrawRectangle( x, y+h, w+1, 1 );

	// (inner) right and bottom
	dc.SetPen( m_penDarkGrey );
	dc.DrawLine( x + w - kCorner, y, x + w - 1, y + h );
	dc.DrawRectangle( x + 1, y + h - 1, w - 2, 1 );

	// (outer) top and left
	dc.SetPen( m_penHighlight );
	dc.DrawRectangle( x, y, w + 1 - kCorner, 1 );
	dc.DrawRectangle( x, y, 1, h );
	dc.DrawLine( x, y + h - 1, x + 1, y + h - 1 );
	dc.DrawLine( x + w - 1, y, x + w - 1, y + 1 );
#endif

	// FIXME: GTK - need implementation
	return (-1);
#endif
}

#if defined(__WXMAC__)
// static
void wxColumnHeaderItem::MacDrawThemeBackgroundNoArrows(
	const void			*boundsR )
{
ThemeButtonDrawInfo	drawInfo;
Rect				qdBoundsR;
RgnHandle			savedClipRgn;
OSStatus			errStatus;
bool				bSelected;

	if ((boundsR == NULL) || EmptyRect( (const Rect*)boundsR ))
		return;

	bSelected = true;
	qdBoundsR = *(const Rect*)boundsR;

	drawInfo.state = (bSelected ? kThemeStateActive: kThemeStateInactive);
	drawInfo.value = (SInt32)bSelected;	// zero draws w/o theme background shading
	drawInfo.adornment = kThemeAdornmentNone;

	savedClipRgn = NewRgn();
	GetClip( savedClipRgn );
	ClipRect( &qdBoundsR );

	qdBoundsR.right += 25;
	errStatus = DrawThemeButton( &qdBoundsR, kThemeListHeaderButton, &drawInfo, NULL, NULL, NULL, 0 );

	// NB: draw the right-side one-pixel border
	// qdBoundsR.left = qdBoundsR.right - 25;
	// errStatus = DrawThemeButton( &qdBoundsR, kThemeListHeaderButton, &drawInfo, NULL, NULL, NULL, 0 );

	SetClip( savedClipRgn );
	DisposeRgn( savedClipRgn );
}
#endif

// static
long wxColumnHeaderItem::ConvertJust(
	long		sourceEnum,
	bool		bToNative )
{
typedef struct { long valA; long valB; } AnonLongPair;
static AnonLongPair	sMap[] =
{
#if defined(__WXMSW__)
	{ wxCOLUMNHEADER_JUST_Left, HDF_LEFT }
	, { wxCOLUMNHEADER_JUST_Center, HDF_CENTER }
	, { wxCOLUMNHEADER_JUST_Right, HDF_RIGHT }
#elif defined(__WXMAC__)
	{ wxCOLUMNHEADER_JUST_Left, teJustLeft }
	, { wxCOLUMNHEADER_JUST_Center, teJustCenter }
	, { wxCOLUMNHEADER_JUST_Right, teJustRight }
#else
	// FIX-ME: GTK - wild guess
	{ wxCOLUMNHEADER_JUST_Left, 0 }
	, { wxCOLUMNHEADER_JUST_Center, 1 }
	, { wxCOLUMNHEADER_JUST_Right, 2 }
#endif
};

long		defaultResultV, itemCount, i;

	itemCount = (long)(sizeof(sMap) / sizeof(*sMap));

	if (bToNative)
	{
		defaultResultV = sMap[0].valB;

		for (i=0; i<itemCount; i++)
		{
			if (sMap[i].valA == sourceEnum)
				return sMap[i].valB;
		}
	}
	else
	{
		defaultResultV = sMap[0].valA;

		for (i=0; i<itemCount; i++)
		{
			if (sMap[i].valB == sourceEnum)
				return sMap[i].valA;
		}
	}

	return defaultResultV;
}


// #endif // wxUSE_COLUMNHEADER

