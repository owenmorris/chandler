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
	#include "wx/dcclient.h"
	#include "wx/settings.h"
	#include "wx/brush.h"
	#include "wx/listbox.h"
	#include "wx/stattext.h"
	#include "wx/textctrl.h"
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
	EVT_LEFT_DCLICK(wxColumnHeader::OnDClick)
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
	wxFLAGS_MEMBER(wxFULL_REPAINT_ON_RESIZE)
	wxFLAGS_MEMBER(wxALWAYS_SHOW_SB )
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
	mNativeBoundsR.x =
	mNativeBoundsR.y =
	mNativeBoundsR.width =
	mNativeBoundsR.height = 0;

	mItemList = NULL;
	mItemCount = 0;
	mItemSelected = kItemIndexInvalid;
	mBUseUnicode = false;

#if 0
#if defined(__WXMSW__)
	mBUseUnicode = sizeof(TCHAR*) > 1;
#endif
#endif
}

void wxColumnHeader::SetUnicodeFlag(
	bool			bSetFlag )
{
	mBUseUnicode = bSetFlag;
}

bool wxColumnHeader::Create(
	wxWindow			*parent,
	wxWindowID			id,
	const wxPoint		&pos,
	const wxSize		&size,
	long				style,
	const wxString		&name )
{
bool	bResultV;

#if defined(__WXMSW__)
	// FIXME: will almost certainly get mangled by wxControl::Create
	// does the class need to be registered?
	style |= HDS_BUTTONS | HDS_FLAT | HDS_HORZ;
#endif

	bResultV =
		wxControl::Create(
			parent, id, pos, size,
			style | wxCLIP_CHILDREN,
			wxDefaultValidator, name );

	if (bResultV)
	{
		// NB: is any of this necessary??

#if 0
		// needed to get the arrow keys normally used for the dialog navigation
		SetWindowStyle( style );

		// we need to set the position as well because the main control position is not
		// the same as the one specified in pos if we have the controls above it
		SetBestSize( size );
		SetPosition( pos );
#endif

		// FIXME: sloppy hack
		wxControl::DoGetPosition( &(mNativeBoundsR.x), &(mNativeBoundsR.y) );
		wxControl::DoGetSize( &(mNativeBoundsR.width), &(mNativeBoundsR.height) );
	}

	return bResultV;
}

// ----------------------------------------------------------------------------
// forward wxWin functions to subcontrols
// NB: useful for debugging, but anything else?
// ----------------------------------------------------------------------------

bool wxColumnHeader::Destroy( void )
{
bool	bResultV;

	bResultV = wxControl::Destroy();

	return bResultV;
}

bool wxColumnHeader::Show(
	bool		bShow )
{
bool	bResultV;

	bResultV = wxControl::Show( bShow );

	return bResultV;
}

bool wxColumnHeader::Enable(
	bool		bEnable )
{
bool	bResultV;

	bResultV = wxControl::Enable( bEnable );

	return bResultV;
}

// ----------------------------------------------------------------------------
// size management
// ----------------------------------------------------------------------------

// NB: is this implementation necessary ??
//
wxSize wxColumnHeader::DoGetBestSize( void ) const
{
	wxCoord		width = 0;
	wxCoord		height = 20;

#if 0
	if (! HasFlag( wxBORDER_NONE ))
	{
		// the border would clip the last line otherwise
		height += 6;
		width += 4;
	}
#endif

	wxSize best( width, height );
	CacheBestSize( best );

	return best;
}

void wxColumnHeader::DoSetSize(
	int		x,
	int		y,
	int		width,
	int		height,
	int		sizeFlags )
{
	wxControl::DoSetSize( x, y, width, height, sizeFlags );

	// FIXME: sloppy hack
	wxControl::DoGetPosition( &(mNativeBoundsR.x), &(mNativeBoundsR.y) );
	wxControl::DoGetSize( &(mNativeBoundsR.width), &(mNativeBoundsR.height) );

	RecalculateItemExtents();
}

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
	wxControl::DoGetPosition( &(mNativeBoundsR.x), &(mNativeBoundsR.y) );
}

void wxColumnHeader::DoGetPosition(
	int		*x,
	int		*y ) const
{
	wxControl::DoGetPosition( x, y );
}

void wxColumnHeader::DoGetSize(
	int		*width,
	int		*height ) const
{
	wxControl::DoGetSize( width, height );
}

// ----------------------------------------------------------------------------
// drawing
// ----------------------------------------------------------------------------

void wxColumnHeader::OnPaint(
	wxPaintEvent		& WXUNUSED(event) )
{
	Draw();
}

// ----------------------------------------------------------------------------
// mouse handling
// ----------------------------------------------------------------------------

void wxColumnHeader::OnDClick(
	wxMouseEvent		&event )
{
	if (HitTest( event.GetPosition() ) < wxCOLUMNHEADER_HITTEST_ITEM_ZERO)
	{
		event.Skip();
	}
	else
	{
		// NB: unused for the present
		GenerateEvent( wxEVT_COLUMNHEADER_DOUBLECLICKED );
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
		if (itemIndex >= wxCOLUMNHEADER_HITTEST_ITEM_ZERO)
		{
			OnClick_DemoSortToggle( itemIndex );
			break;
		}

		// unknown message - unhandled - fall through
		wxFAIL_MSG( _T("unknown hittest code") );

	case wxCOLUMNHEADER_HITTEST_NOWHERE:
		event.Skip();
		break;
	}
}

// static
wxVisualAttributes
wxColumnHeader::GetClassDefaultAttributes(
	wxWindowVariant		variant )
{
	// use the same color scheme as wxListBox
	return wxListBox::GetClassDefaultAttributes( variant );
}

// ================
#if 0
#pragma mark -
#endif

void wxColumnHeader::DisposeItemList( void )
{
	if (mItemList != NULL)
	{
		for (long i=0; i<mItemCount; i++)
			delete mItemList[i];

		free( mItemList );
		mItemList = NULL;
	}

	mItemCount = 0;
	mItemSelected = kItemIndexInvalid;
}

long wxColumnHeader::GetSelectedItemIndex( void )
{
	return mItemSelected;
}

void wxColumnHeader::SetSelectedItemIndex(
	long			itemIndex )
{
bool		bActive, bEnabled, bSortAscending;

	if ((itemIndex >= 0) && (itemIndex < mItemCount))
		if (mItemSelected != itemIndex)
		{
			if (mItemList != NULL)
				for (long i=0; i<mItemCount; i++)
				{
					if (mItemList[i] != NULL)
					{
						mItemList[i]->GetFlags( bActive, bEnabled, bSortAscending );
						bActive = (i == itemIndex);
						mItemList[i]->SetFlags( bActive, bEnabled, bSortAscending );
					}

#if defined(__WXMSW__)
					(void)Win32ItemSelect( i, bActive, bSortAscending );
#endif
				}

			mItemSelected = itemIndex;
		}
}

long wxColumnHeader::GetItemCount( void )
{
	return (long)mItemCount;
}

void wxColumnHeader::DeleteItem(
	long			itemIndex )
{
	if ((itemIndex >= 0) && (itemIndex < mItemCount))
	{
#if defined(__WXMSW__)
		(void)Win32ItemDelete( itemIndex );
#endif

		if (mItemList != NULL)
		{
			if (mItemCount > 1)
			{
				// delete the target item
				delete mItemList[itemIndex];

				// close the list hole
				for (long i=itemIndex; i<mItemCount-1; i++)
					mItemList[i] = mItemList[i + 1];

				// leave a NULL spot at the end
				mItemList[mItemCount - 1] = NULL;
				mItemCount--;

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
	bool			bActive,
	bool			bSortAscending )
{
wxColumnHeaderItem		itemInfo;
long					originX, lastExtentX;

	itemInfo.mLabelTextRef = textBuffer;
	itemInfo.mTextJust = textJust;
	itemInfo.mExtentX = extentX;
	itemInfo.mBIsActive = bActive;
	itemInfo.mBSortAscending = bSortAscending;

	originX = 0;
	if (GetUIExtent( mItemCount - 1, originX, lastExtentX ))
		originX += lastExtentX;

	itemInfo.mOriginX = originX;
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

	// allocate new item list copy the original list items into it
	newItemList = (wxColumnHeaderItem**)calloc( mItemCount + itemCount, sizeof(wxColumnHeaderItem*) );
	if (mItemList != NULL)
	{
		for (i=0; i<mItemCount; i++)
			newItemList[i] = mItemList[i];

		free( mItemList );
	}
	mItemList = newItemList;

	// append the new items
	for (i=0; i<itemCount; i++)
	{
		targetIndex = mItemCount + i;
		mItemList[targetIndex] = new wxColumnHeaderItem( &itemList[i] );

		bIsSelected = (mItemList[targetIndex]->mBIsActive && mItemList[targetIndex]->mBIsEnabled);

#if defined(__WXMSW__)
		Win32ItemInsert(
			targetIndex, mItemList[targetIndex]->mExtentX,
			mItemList[targetIndex]->mLabelTextRef, mItemList[targetIndex]->mTextJust,
			false, // for Unicode - TBD
			bIsSelected, mItemList[targetIndex]->mBSortAscending );
#endif

		if (bIsSelected && (mItemSelected < 0))
			mItemSelected = targetIndex;
	}

	// update the counter
	mItemCount += itemCount;
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
	if ((itemIndex >= 0) && (itemIndex < mItemCount))
		return mItemList[itemIndex];
	else
		return NULL;
}

// NB: call is responsible for disposing text buffer (via free())
//
bool wxColumnHeader::GetLabelText(
	long			itemIndex,
	wxString		&textBuffer,
	long			&textJust )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		(void)itemRef->GetLabelText( textBuffer, textJust );
	}
	else
	{
		textBuffer = _T("");
		textJust = wxCOLUMNHEADER_JustLeft;
	}

	return bResultV;
}

bool wxColumnHeader::SetLabelText(
	long				itemIndex,
	const wxString		&textBuffer,
	long				textJust )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		itemRef->SetLabelText( textBuffer, textJust );
		RefreshItem( itemIndex );
	}

	return bResultV;
}

bool wxColumnHeader::GetUIExtent(
	long			itemIndex,
	long			&originX,
	long			&extentX )
{
wxColumnHeaderItem		*itemRef;
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

	return bResultV;
}

bool wxColumnHeader::SetUIExtent(
	long			itemIndex,
	long			originX,
	long			extentX )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		itemRef->SetUIExtent( originX, extentX );
		RefreshItem( itemIndex );
	}

	return bResultV;
}

bool wxColumnHeader::GetFlags(
	long			itemIndex,
	bool			&bActive,
	bool			&bEnabled,
	bool			&bSortAscending )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		itemRef->GetFlags( bActive, bEnabled, bSortAscending );
	}
	else
	{
		bActive =
		bEnabled =
		bSortAscending = FALSE;
	}

	return bResultV;
}

bool wxColumnHeader::SetFlags(
	long			itemIndex,
	bool			bActive,
	bool			bEnabled,
	bool			bSortAscending )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		itemRef->SetFlags( bActive, bEnabled, bSortAscending );
		RefreshItem( itemIndex );
	}

	return bResultV;
}

wxColumnHeaderHitTestResult wxColumnHeader::HitTest(
	const wxPoint		&locationPt )
{
wxColumnHeaderHitTestResult		resultV;

	resultV = wxCOLUMNHEADER_HITTEST_NOWHERE;

#if defined(__WXMSW__)
RECT		boundsR;
long		itemCount, i;

	HWND	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		wxFAIL_MSG( _T("targetViewRef = GetHwnd failed (NULL)") );
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
// Point	qdPt;
//
//	qdPt.h = locationPt.x;
//	qdPt.v = locationPt.y;
//	if (PtInRect( qdPt, &mNativeBoundsR ))
//	if (mNativeBoundsR.Contains( locationPt ))
	for (long i=0; i<mItemCount; i++)
		if (mItemList[i] != NULL)
			if (mItemList[i]->HitTest( locationPt ) != 0)
			{
				resultV = (wxColumnHeaderHitTestResult)i;
				break;
			}
#endif

	return resultV;
}

// NB: this routine is unused
//
long wxColumnHeader::Draw( void )
{
long		errStatus;

	errStatus = 0;

#if !defined(__WXMSW__)
	for (long i=0; i<mItemCount; i++)
		errStatus |= mItemList[i]->DrawSelf();
#endif

	return (long)errStatus;
}

void wxColumnHeader::SetViewDirty( void )
{
#if 0
#elif defined(__WXMSW__)
	HWND	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		wxFAIL_MSG( _T("targetViewRef = GetHwnd failed (NULL)") );
		return;
	}

	InvalidateRect( targetViewRef, NULL, FALSE );
#elif defined(__WXMAC__)
	// FIXME:
#endif
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

	if (mItemList != NULL)
	{
		originX = 0;
		for (i=0; i<mItemCount; i++)
			if (mItemList[i] != NULL)
			{
				mItemList[i]->mOriginX = originX;
				originX += mItemList[i]->mExtentX;
			}
	}
}

// ================
#if 0
#pragma mark -
#endif

#if defined(__WXMSW__)
long wxColumnHeader::Win32ItemInsert(
	long			iInsertAfter,
	long			nWidth,
	const void		*titleText,
	long			textJust,
	bool			bUseUnicode,
	bool			bSelected,
	bool			bSortAscending )
{
HDITEM		itemData;
HWND		targetViewRef;
long		resultV;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		wxFAIL_MSG( _T("targetViewRef = GetHwnd failed (NULL)") );
		return (-1L);
	}

	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_TEXT | HDI_FORMAT | HDI_WIDTH;
	itemData.pszText = (LPSTR)titleText;
	itemData.cxy = (int)nWidth;
	itemData.cchTextMax = sizeof(itemData.pszText) / sizeof(itemData.pszText[0]);
	itemData.fmt = wxColumnHeaderItem::ConvertJust( textJust, TRUE ) | HDF_STRING;
	if (bSelected)
		itemData.fmt |= (bSortAscending ? HDF_SORTUP : HDF_SORTDOWN);

	resultV = (long)Header_InsertItem( targetViewRef, (int)iInsertAfter, &itemData );
//	resultV = SendMessage( mViewRef, bUseUnicode ? HDM_INSERTITEMW : HDM_INSERTITEMA, (WPARAM)iInsertAfter, (LPARAM)&itemData );

	return resultV;
}

long wxColumnHeader::Win32ItemDelete(
	long			itemIndex )
{
HWND		targetViewRef;
long			resultV;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		wxFAIL_MSG( _T("targetViewRef = GetHwnd failed (NULL)") );
		return (-1L);
	}

	resultV = (long)Header_DeleteItem( targetViewRef, itemIndex );

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
		wxFAIL_MSG( _T("targetViewRef = GetHwnd failed (NULL)") );
		return (-1L);
	}

	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_FORMAT | HDI_WIDTH;
	resultV = (long)Header_GetItem( targetViewRef, itemIndex, &itemData );

	itemData.mask = HDI_TEXT | HDI_FORMAT | HDI_WIDTH;
	itemData.pszText = (LPSTR)(itemRef->mLabelTextRef.c_str());
	itemData.cxy = (int)(itemRef->mExtentX);
	itemData.cchTextMax = sizeof(itemData.pszText) / sizeof(itemData.pszText[0]);
	itemData.fmt = wxColumnHeaderItem::ConvertJust( itemRef->mTextJust, TRUE ) | HDF_STRING;

	itemData.fmt &= ~(HDF_SORTDOWN | HDF_SORTUP);
	if (itemRef->mBIsActive && itemRef->mBIsEnabled)
		itemData.fmt |= (itemRef->mBSortAscending ? HDF_SORTUP : HDF_SORTDOWN);

	resultV = (long)Header_SetItem( targetViewRef, itemIndex, &itemData );
//	resultV = SendMessage( mViewRef, itemRef->mBTextUnicode ? HDM_SETITEMW : HDM_SETITEMA, (WPARAM)itemIndex, (LPARAM)&itemData );

	return resultV;
}

long wxColumnHeader::Win32ItemSelect(
	long			itemIndex,
	bool			bSelected,
	bool			bSortAscending )
{
HDITEM		itemData;
HWND		targetViewRef;
long		resultV;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		wxFAIL_MSG( _T("targetViewRef = GetHwnd failed (NULL)") );
		return (-1L);
	}

	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_FORMAT | HDI_WIDTH;
	resultV = (long)Header_GetItem( targetViewRef, itemIndex, &itemData );

	itemData.fmt &= ~(HDF_SORTDOWN | HDF_SORTUP);
	if (bSelected)
		itemData.fmt |= (bSortAscending ? HDF_SORTUP : HDF_SORTDOWN);

	resultV = (long)Header_SetItem( targetViewRef, itemIndex, &itemData );
//	resultV = SendMessage( mViewRef, itemRef->mBTextUnicode ? HDM_SETITEMW : HDM_SETITEMA, (WPARAM)itemIndex, (LPARAM)&itemData );

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

void wxColumnHeader::OnClick_DemoSortToggle(
	long				itemIndex )
{
long			curSelectionIndex;

	curSelectionIndex = GetSelectedItemIndex();
	if (itemIndex != mItemSelected)
	{
		SetSelectedItemIndex( itemIndex );
	}
	else
	{
	wxColumnHeaderItem	*item;
	bool				bBoolFlag1, bBoolFlag2, bSortFlag;

		item = ((mItemList != NULL) ? mItemList[itemIndex] : NULL);
		if (item != NULL)
		{
			item->GetFlags( bBoolFlag1, bBoolFlag2, bSortFlag );
			item->SetFlags( bBoolFlag1, bBoolFlag2, ! bSortFlag );

#if defined(__WXMSW__)
			Win32ItemRefresh( itemIndex );
#endif

			SetViewDirty();
		}

		// for testing: can induce text wrapping outside of bounds rect
//		item->SetLabelText( _wxT("같같 YOW! 같같"), wxTextJustCenter );
	}
}

// ================
#if 0
#pragma mark -
#endif

// ----------------------------------------------------------------------------
// wxColumnHeaderEvent
// ----------------------------------------------------------------------------

void wxColumnHeaderEvent::Init( void )
{
}

wxColumnHeaderEvent::wxColumnHeaderEvent(
	wxColumnHeader *col,
	wxEventType type )
	:
	wxCommandEvent( type, col->GetId() )
{
	SetEventObject( col );
}

// ================
#if 0
#pragma mark -
#endif

wxColumnHeaderItem::wxColumnHeaderItem()
	:
	mFontID( 0 )
	, mTextJust( 0 )
	, mImageID( -1 )
	, mOriginX( 0 )
	, mExtentX( 0 )
	, mBIsActive( FALSE )
	, mBIsEnabled( FALSE )
	, mBSortAscending( FALSE )
{
}

wxColumnHeaderItem::wxColumnHeaderItem(
	const wxColumnHeaderItem		*info )
	:
	mFontID( 0 )
	, mTextJust( 0 )
	, mImageID( -1 )
	, mOriginX( 0 )
	, mExtentX( 0 )
	, mBIsActive( FALSE )
	, mBIsEnabled( FALSE )
	, mBSortAscending( FALSE )
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

	info->mNativeBoundsR = mNativeBoundsR;
	info->mFontID = mFontID;
	info->mImageID = mImageID;
	info->mOriginX = mOriginX;
	info->mExtentX = mExtentX;
	info->mBIsActive = mBIsActive;
	info->mBIsEnabled = mBIsEnabled;
	info->mBSortAscending = mBSortAscending;

	GetLabelText( info->mLabelTextRef, info->mTextJust );
}

void wxColumnHeaderItem::SetItemData(
	const wxColumnHeaderItem		*info )
{
	if (info == NULL)
		return;

	mNativeBoundsR = info->mNativeBoundsR;
	mFontID = info->mFontID;
	mImageID = info->mImageID;
	mImageID = info->mImageID;
	mOriginX = info->mOriginX;
	mExtentX = info->mExtentX;
	mBIsActive = info->mBIsActive;
	mBIsEnabled = info->mBIsEnabled;
	mBSortAscending = info->mBSortAscending;

	SetLabelText( info->mLabelTextRef, info->mTextJust );
}

long wxColumnHeaderItem::GetLabelText(
	wxString			&textBuffer,
	long				&textJust )
{
long		returnedSize;

	returnedSize = 0;

	textBuffer = mLabelTextRef;
	textJust = mTextJust;

	return returnedSize;
}

void wxColumnHeaderItem::SetLabelText(
	const wxString		&textBuffer,
	long				textJust )
{
	mLabelTextRef = textBuffer;
	mTextJust = textJust;
}

void wxColumnHeaderItem::GetUIExtent(
	long			&originX,
	long			&extentX )
{
	originX = mOriginX;
	extentX = mExtentX;
}

void wxColumnHeaderItem::SetUIExtent(
	long			originX,
	long			extentX )
{
	// FIXME: range-check these properly!
	if (originX >= 0)
		mOriginX = originX;
	if (extentX >= 0)
		mExtentX = extentX;
}

void wxColumnHeaderItem::GetFlags(
	bool			&bActive,
	bool			&bEnabled,
	bool			&bSortAscending )
{
	bActive = mBIsActive;
	bEnabled = mBIsEnabled;
	bSortAscending = mBSortAscending;
}

void wxColumnHeaderItem::SetFlags(
	bool			bActive,
	bool			bEnabled,
	bool			bSortAscending )
{
	mBIsActive = bActive;
	mBIsEnabled = bEnabled;
	mBSortAscending = bSortAscending;
}

long wxColumnHeaderItem::HitTest(
	const wxPoint		&locationPt )
{
long		targetX, resultV;

	targetX = locationPt.x - mNativeBoundsR.x;
	resultV = ((targetX >= mOriginX) && (targetX < mOriginX + mExtentX));

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
	if (mOriginX >= mNativeBoundsR.width)
		return (-1L);

	qdBoundsR.left = mNativeBoundsR.x + mOriginX;
	qdBoundsR.top = mNativeBoundsR.y;
	qdBoundsR.right = qdBoundsR.left + mExtentX + 1;

	// a broken attempt to tinge the background
// Collection	origCol, newCol;
// RGBColor	tintRGB = { 0xFFFF, 0x0000, 0xFFFF };
//	errStatus = SetAppearanceTintColor( &tintRGB, origCol, newCol );

	if (mBIsEnabled)
		drawInfo.state = (mBIsActive ? kThemeStateActive: kThemeStateInactive);
	else
		drawInfo.state = (mBIsActive ? kThemeStateUnavailable : kThemeStateUnavailableInactive);
//	drawInfo.state = kThemeStatePressed;

	drawInfo.value = (SInt32)mBIsActive;	// zero draws w/o theme background shading

	drawInfo.adornment = (mBSortAscending ? kThemeAdornmentNone : kThemeAdornmentArrowDoubleArrow);
//	drawInfo.adornment = kThemeAdornmentNone;					// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentDefault;				// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentHeaderButtonShadowOnly;	// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentArrowDoubleArrow;		// doesn't work - same as "up-arrow" !!
//	drawInfo.adornment = kThemeAdornmentHeaderMenuButton;		// right-pointing arrow on left side
//	drawInfo.adornment = kThemeAdornmentHeaderButtonSortUp;
//	drawInfo.adornment = kThemeAdornmentArrowDownArrow;

	// NB: DrawThemeButton height is fixed, regardless of the boundsRect argument!
	errStatus = DrawThemeButton( &qdBoundsR, kThemeListHeaderButton, &drawInfo, NULL, NULL, NULL, 0 );

	// end of the dead attempt to tinge the background
//	errStatus = RestoreTheme( origCol, newCol );

	// exclude button adornment areas from further drawing consideration
	qdBoundsR.left += 4;
	qdBoundsR.right -= 16;
	qdBoundsR.top += 1;

	nativeTextJust = ConvertJust( mTextJust, TRUE );

	if (! mLabelTextRef.IsEmpty())
	{
	CFStringRef			cfLabelText;
	TextEncoding		targetEncoding;
	bool				bUseUnicode;

		bUseUnicode = FALSE;
		targetEncoding = (bUseUnicode ? kCFStringEncodingUnicode : kCFStringEncodingMacRoman);
		cfLabelText = CFStringCreateWithCString( NULL, (const char*)mLabelTextRef, targetEncoding );
		if (cfLabelText != NULL)
		{
			errStatus =
				(OSStatus)DrawThemeTextBox(
					cfLabelText, mFontID, drawInfo.state, true,
					&qdBoundsR, mTextJust, NULL );

			CFRelease( cfLabelText );
		}
	}

#if 0
	// FIX-ME: need implementation
	// TO-DO: can label text and an bitmap (icon) be shown simultaneously?
	if (mImageID != (-1))
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

	// FIXME: GTK - need implementation
	return (-1);
#endif
}

// static
long wxColumnHeaderItem::ConvertJust(
	long		sourceEnum,
	bool		bToNative )
{
typedef struct { long valA; long valB; } AnonLongPair;
static AnonLongPair	sMap[] =
{
#if defined(__WXMSW__)
	{ wxCOLUMNHEADER_JustLeft, HDF_LEFT }
	, { wxCOLUMNHEADER_JustCenter, HDF_CENTER }
	, { wxCOLUMNHEADER_JustRight, HDF_RIGHT }
#elif defined(__WXMAC__)
	{ wxCOLUMNHEADER_JustLeft, teJustLeft }
	, { wxCOLUMNHEADER_JustCenter, teJustCenter }
	, { wxCOLUMNHEADER_JustRight, teJustRight }
#else
	// FIX-ME: GTK - wild guess
	{ wxCOLUMNHEADER_JustLeft, 0 }
	, { wxCOLUMNHEADER_JustCenter, 1 }
	, { wxCOLUMNHEADER_JustRight, 2 }
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

