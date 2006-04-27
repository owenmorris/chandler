///////////////////////////////////////////////////////////////////////////////
// Name:		src/generic/colheader.cpp
// Purpose:	2-platform (Mac,MSW) + generic implementation of a native-appearance column header
// Author:	David Surovell
// Modified by:
// Created:	01.01.2005
// RCS-ID:
// Copyright:
// License:
///////////////////////////////////////////////////////////////////////////////

// For compilers that support precompilation, includes "wx.h".
#include "wx/wxprec.h"

#if defined(__BORLANDC__)
	#pragma hdrstop
#endif

//#if wxUSE_COLUMNHEADER

#if defined(__WXMSW__)
	#if !defined(_WIN32_WINNT)
		#define _WIN32_WINNT	0x5010
	#endif

	#include <commctrl.h>

#elif defined(__WXMAC__)
	#include <TextEdit.h>
#endif

#if !defined(WX_PRECOMP)
	#include "wx/settings.h"
	#include "wx/listbox.h"
	#include "wx/dcclient.h"
	#include "wx/bitmap.h"
	#include "wx/gdicmn.h"
	#include "wx/colour.h"
#endif

#if defined(__WXMAC__)
	#include "wx/mac/uma.h"
#endif

#include "wx/renderer.h"
#include "wx/colheader.h"
#include "wx/grid.h"

// ----------------------------------------------------------------------------
// wx binding macros
// ----------------------------------------------------------------------------

#if wxUSE_EXTENDED_RTTI
WX_DEFINE_FLAGS( wxColumnHeaderStyle )

wxBEGIN_FLAGS( wxColumnHeaderStyle )
	// new style border flags:
	// put them first to use them for streaming out
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

BEGIN_EVENT_TABLE( wxColumnHeader, wxControl )
	EVT_PAINT( wxColumnHeader::OnPaint )
	EVT_LEFT_DOWN( wxColumnHeader::OnClick )
	EVT_LEFT_DCLICK( wxColumnHeader::OnDoubleClick )
END_EVENT_TABLE()

// ----------------------------------------------------------------------------
// events
// ----------------------------------------------------------------------------

DEFINE_EVENT_TYPE(wxEVT_COLUMNHEADER_SELCHANGED)
DEFINE_EVENT_TYPE(wxEVT_COLUMNHEADER_DOUBLECLICKED)

// ============================================================================
// implementation
// ============================================================================

// ----------------------------------------------------------------------------
// wxChandlerGridLabelWindow
// ----------------------------------------------------------------------------

IMPLEMENT_DYNAMIC_CLASS( wxChandlerGridLabelWindow, wxClassParent_ChandlerGridLabelWindow )

BEGIN_EVENT_TABLE( wxChandlerGridLabelWindow, wxClassParent_ChandlerGridLabelWindow )
	EVT_PAINT( wxChandlerGridLabelWindow::OnPaint )
	EVT_MOUSEWHEEL( wxChandlerGridLabelWindow::OnMouseWheel )
	EVT_MOUSE_EVENTS( wxChandlerGridLabelWindow::OnMouseEvent )
	EVT_KEY_DOWN( wxChandlerGridLabelWindow::OnKeyDown )
	EVT_KEY_UP( wxChandlerGridLabelWindow::OnKeyUp )
	EVT_CHAR( wxChandlerGridLabelWindow::OnChar )
END_EVENT_TABLE()


#define wxCH_minimum_x		16


wxChandlerGridLabelWindow::wxChandlerGridLabelWindow(
	wxGrid *parent,
	wxWindowID id,
	const wxPoint& pos,
	const wxSize &size,
	long styleVariant )
	:
	wxClassParent_ChandlerGridLabelWindow(
		parent, id, pos, size,
		styleVariant | wxWANTS_CHARS | wxBORDER_NONE | wxFULL_REPAINT_ON_RESIZE )
{
	m_owner = parent;
	m_styleVariant = styleVariant;
}

wxChandlerGridLabelWindow::~wxChandlerGridLabelWindow()
{
}

// ================
#if 0
#pragma mark -
#endif

void wxChandlerGridLabelWindow::OnPaint( wxPaintEvent& WXUNUSED(event) )
{
#if defined(__GRID_LABELS_ARE_COLHEADERS__)
	// wxColumnHeader (inherited) method
	Draw();
#else
	// wxGrid method
	if (m_owner == NULL)
		return;

	wxPaintDC dc( this );

	// NO - don't do this because it will set both the x and y origin
	// coords to match the parent scrolled window and we just want to
	// set the x coord - MB
	//
	// m_owner->PrepareDC( dc );

	int x, y;

	m_owner->CalcUnscrolledPosition( 0, 0, &x, &y );
	if ((m_styleVariant & CH_STYLE_HeaderIsVertical) == 0)
	{
		dc.SetDeviceOrigin( -x, 0 );
		wxArrayInt cols = m_owner->CalcColLabelsExposed( GetUpdateRegion() );
		m_owner->DrawColLabels( dc, cols );
	}
	else
	{
		dc.SetDeviceOrigin( 0, -y );
		wxArrayInt rows = m_owner->CalcRowLabelsExposed( GetUpdateRegion() );
		m_owner->DrawRowLabels( dc, rows );
	}
#endif
}

void wxChandlerGridLabelWindow::OnMouseEvent( wxMouseEvent& event )
{
#if 0 && __WXDEBUG__
        if ( event.LeftIsDown() )
		DumpInfo(
			((m_styleVariant & CH_STYLE_HeaderIsVertical) == 0)
			? wxT("Row LH")
			: wxT("Column LH") );
#endif

	if (m_owner == NULL)
		return;

	if ((m_styleVariant & CH_STYLE_HeaderIsVertical) == 0)
		m_owner->ProcessColLabelMouseEvent( event );
	else
		m_owner->ProcessRowLabelMouseEvent( event );
}

void wxChandlerGridLabelWindow::OnMouseWheel( wxMouseEvent& event )
{
	if (m_owner == NULL)
		return;

	m_owner->GetEventHandler()->ProcessEvent( event );
}

// This seems to be required for wxMotif otherwise the mouse
// cursor must be in the cell edit control to get key events
//
void wxChandlerGridLabelWindow::OnKeyDown( wxKeyEvent& event )
{
	if ((m_owner == NULL) || !m_owner->GetEventHandler()->ProcessEvent( event ))
		event.Skip();
}

void wxChandlerGridLabelWindow::OnKeyUp( wxKeyEvent& event )
{
	if ((m_owner == NULL) || !m_owner->GetEventHandler()->ProcessEvent( event ))
		event.Skip();
}

void wxChandlerGridLabelWindow::OnChar( wxKeyEvent& event )
{
	if ((m_owner == NULL) || !m_owner->GetEventHandler()->ProcessEvent( event ))
		event.Skip();
}

// ================
#if 0
#pragma mark -
#endif

void wxChandlerGridLabelWindow::GetLabelValue( bool isColumn, int index, wxString& value )
{
	if (isColumn)
		value = m_owner->GetColLabelValue( index );
	else
		value = m_owner->GetRowLabelValue( index );
}

void wxChandlerGridLabelWindow::SetLabelValue( bool isColumn, int index, const wxString& value )
{
#if defined(__GRID_LABELS_ARE_COLHEADERS__)
	SetLabelText( index, value );
#else
	if (isColumn)
		m_owner->SetColLabelValue( index, value );
	else
		m_owner->SetRowLabelValue( index, value );
#endif
}

void wxChandlerGridLabelWindow::GetLabelSize( bool isColumn, int index, int& value )
{
// WXUNUSED( index )

	if (isColumn)
		value = m_owner->GetColLabelSize();
	else
		value = m_owner->GetRowLabelSize();
}

void wxChandlerGridLabelWindow::SetLabelSize( bool isColumn, int index, int value )
{
#if defined(__GRID_LABELS_ARE_COLHEADERS__)
wxSize	sizeV;

	// y is ignored
	sizeV.x = value;
	sizeV.y = 0;
	SetUIExtent( index, sizeV );
#else
// WXUNUSED( index )

	if (isColumn)
		m_owner->SetColLabelSize( value );
	else
		m_owner->SetRowLabelSize( value );
#endif
}

void wxChandlerGridLabelWindow::GetLabelAlignment( bool isColumn, int index, int& hAlign, int& vAlign )
{
// WXUNUSED( index )

	if (isColumn)
		m_owner->GetColLabelAlignment( &hAlign, &vAlign );
	else
		m_owner->GetRowLabelAlignment( &hAlign, &vAlign );
}

void wxChandlerGridLabelWindow::SetLabelAlignment( bool isColumn, int index, int hAlign, int vAlign )
{
// WXUNUSED( index )

#if defined(__GRID_LABELS_ARE_COLHEADERS__)
#else
	if (isColumn)
		m_owner->SetColLabelAlignment( hAlign, vAlign );
	else
		m_owner->SetRowLabelAlignment( hAlign, vAlign );
#endif
}

// ================
#if 0
#pragma mark -
#endif

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

	m_DefaultItemSize.x =
	m_DefaultItemSize.y = 0;

	m_ItemList = NULL;
	m_ItemCount = 0;
	m_ExpectedItemCount = 0;
	m_ItemViewBaseIndex = 0;
	m_ItemViewBaseOrigin = 0;
	m_ItemSelected = CH_HITTEST_NoPart;

	m_SelectionColour.Set( 0x66, 0x66, 0x66 );

	m_BUseVerticalOrientation = false;

#if wxUSE_UNICODE
	m_BUseUnicode = true;
#else
	m_BUseUnicode = false;
#endif

#if defined(__WXMSW__) || defined(__WXMAC__)
	m_BFixedHeight = true;
	m_BUseGenericRenderer = false;
#else
	m_BFixedHeight = false;
	m_BUseGenericRenderer = true;
#endif

	m_BProportionalResizing = true;
	m_BVisibleSelection = true;

#if defined(__WXMAC__)
	// NB: or kThemeSystemFontTag, kThemeViewsFontTag
	m_Font.MacCreateThemeFont( kThemeSmallSystemFont );
	m_SelectionDrawStyle = CH_SELECTIONDRAWSTYLE_Native;
#elif defined(__WXGTK__)
	// NB: perhaps for MSW too? (after testing, of course)
	m_Font = wxSystemSettings::GetFont( wxSYS_DEFAULT_GUI_FONT );
	m_SelectionDrawStyle = CH_SELECTIONDRAWSTYLE_Underline;
#else
	m_Font.SetFamily( 0 );
	m_SelectionDrawStyle = CH_SELECTIONDRAWSTYLE_Underline;
#endif
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
wxSize		actualSize;
bool			bResultV;

	localName = name;

	m_DefaultItemSize = CalculateDefaultItemSize( size );

	actualSize = size;
#if 1
	if (m_BFixedHeight)
	{
		actualSize = CalculateDefaultSize();
		if (size.x > 0)
			actualSize.x = size.x;
	}
#else
	if ((actualSize.x <= 0) || (m_BFixedHeight && (actualSize.x > 0)))
		actualSize.x = m_DefaultItemSize.x;
	if (actualSize.y <= 0)
		actualSize.y = m_DefaultItemSize.y;
#endif

	// NB: we're stealing a bit in the style argument from Win32 and wx to support ListHeader attributes
	// assumes CH_STYLE_HeaderIsVertical is integral power of two value
	if (style & CH_STYLE_HeaderIsVertical)
	{
		m_BUseVerticalOrientation = true;
		style &= ~CH_STYLE_HeaderIsVertical;
	}

	// NB: the CreateControl call crashes on MacOS
#if defined(__WXMSW__)
	// NB: this is a string from Win32 headers and is conditionally defined as Unicode or ANSI,
	// hence, no _T() nor wxT() macro is desirable
	localName = WC_HEADER;
	bResultV =
		CreateControl(
			parent, id, pos, actualSize,
			style, wxDefaultValidator, localName );

	if (bResultV)
	{
	WXDWORD		msStyle, exstyle;

		msStyle = MSWGetStyle( style, &exstyle );
		bResultV = MSWCreateControl( localName, msStyle, pos, actualSize, wxEmptyString, exstyle );
	}

#else
	bResultV =
		wxControl::Create(
			parent, id, pos, actualSize,
			style, wxDefaultValidator, localName );
#endif

#if 0
	if (bResultV)
	{
		// NB: is any of this necessary??

		// needed to get the arrow keys normally used for dialog navigation
		SetWindowStyle( style );

		// we need to set the position as well because the main control position is not
		// the same as the one specified in pos if we have the controls above it
		SetBestSize( actualSize );
		SetPosition( pos );
	}
#endif

	// NB: is this advisable?
	wxControl::DoGetPosition( &(m_NativeBoundsR.x), &(m_NativeBoundsR.y) );
	wxControl::DoGetSize( &(m_NativeBoundsR.width), &(m_NativeBoundsR.height) );

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
void wxColumnHeader::DumpInfo(
	const wxString&	titleStr ) const
{
//
// NB: cannot build this in non-debug wxGTK target, so disabling it for the time being...
//
#if (defined(__WXMSW__) || defined(__WXMAC__)) && defined(__WXDEBUG__) && __WXDEBUG__
#define PRINTFProc Printf
#define LOGProc(A) wxLogDebug((A).c_str())

#define wxFormatRect(resultArg,rectArg)	\
	(resultArg).PRINTFProc( wxT("%s: [%d, %d; %d, %d]"), \
	wxT(#rectArg), (rectArg).x, (rectArg).y, (rectArg).width, (rectArg).height )
#define wxFormatSize(resultArg,sizeArg)	\
	(resultArg).PRINTFProc( wxT("%s: [%d, %d]"), \
	wxT(#sizeArg), (sizeArg).x, (sizeArg).y )
#define wxFormatLong(resultArg,longArg)	\
	(resultArg).PRINTFProc( wxT("%s: [%ld]"), wxT(#longArg), (longArg) )
#define wxFormatString(resultArg,strArg)	\
	(resultArg).PRINTFProc( wxT("%s: [%s]"), wxT(#strArg), strArg.c_str() )
#define wxFormatBool(resultArg,boolArg)	\
	(resultArg).PRINTFProc( wxT("%s: [%s]"), wxT(#boolArg), (boolArg) ? wxT("T") : wxT("F") )

wxColumnHeaderItem	*itemRef;
wxString	msgStr, itemStr, dividerStr;
long		i;

	if (!titleStr.IsEmpty())
		LOGProc( titleStr );

	wxFormatRect( msgStr, m_NativeBoundsR );
	LOGProc( msgStr );

	wxFormatSize( msgStr, m_DefaultItemSize );
	LOGProc( msgStr );

	wxFormatLong( msgStr, m_ItemCount );
	LOGProc( msgStr );

	wxFormatLong( msgStr, m_ExpectedItemCount );
	LOGProc( msgStr );

	wxFormatLong( msgStr, m_ItemViewBaseIndex );
	LOGProc( msgStr );

	wxFormatLong( msgStr, m_ItemViewBaseOrigin );
	LOGProc( msgStr );

	wxFormatLong( msgStr, m_ItemSelected );
	LOGProc( msgStr );

	wxFormatLong( msgStr, m_SelectionDrawStyle );
	LOGProc( msgStr );

	wxFormatBool( msgStr, m_BUseVerticalOrientation );
	LOGProc( msgStr );

	wxFormatBool( msgStr, m_BUseUnicode );
	LOGProc( msgStr );

	wxFormatBool( msgStr, m_BUseGenericRenderer );
	LOGProc( msgStr );

	wxFormatBool( msgStr, m_BFixedHeight );
	LOGProc( msgStr );

	wxFormatBool( msgStr, m_BProportionalResizing );
	LOGProc( msgStr );

	itemStr = wxT("# name textSize origin extent");
	LOGProc( itemStr );

	dividerStr = wxT("===============");
	LOGProc( dividerStr );

	if (m_ItemCount <= 0)
	{
		itemStr = wxT("<no items>");
		LOGProc( itemStr );
	}

	for (i=0; i<m_ItemCount; i++)
	{
		itemRef = GetItemRef( i );
		if (itemRef != NULL)
		{
			msgStr.Printf(
				wxT("%ld: [%s] [%ld, %ld] [%ld, %ld] [%ld, %ld]"),
				i, itemRef->m_LabelTextRef.c_str(),
				itemRef->m_LabelTextExtent.x, itemRef->m_LabelTextExtent.y,
				itemRef->m_Origin.x, itemRef->m_Origin.y,
				itemRef->m_Extent.x, itemRef->m_Extent.y );
		}
		else
		{
			msgStr.Printf( wxT("%ld: [NULL]"), i );
		}
		LOGProc( msgStr );
	}

	LOGProc( dividerStr );

	msgStr = wxT("");
	LOGProc( msgStr );
#endif
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
long		i;
bool		bResultV;

	if (bEnable == IsEnabled())
		return bEnable;

	bResultV = wxControl::Enable( bEnable );

	for (i=0; i<m_ItemCount; i++)
	{
		if ((m_ItemList != NULL) && (m_ItemList[i] != NULL))
			m_ItemList[i]->SetAttribute( CH_ITEM_ATTR_Enabled, bEnable );

		RefreshItem( i, false );
	}

	// force a redraw
	SetViewDirty();

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

	// NB: is this advisable?
	wxControl::DoGetPosition( &(m_NativeBoundsR.x), &(m_NativeBoundsR.y) );
}

// virtual
wxSize wxColumnHeader::DoGetBestSize( void ) const
{
wxSize	targetSize;

	targetSize = CalculateDefaultSize();
	CacheBestSize( targetSize );

	return targetSize;
}

// virtual
wxSize wxColumnHeader::DoGetMinSize( void ) const
{
wxSize	targetSize;

	targetSize = CalculateDefaultSize();
	targetSize.x = 0;

	return targetSize;
}

// virtual
void wxColumnHeader::DoSetSize(
	int		x,
	int		y,
	int		width,
	int		height,
	int		sizeFlags )
{
	// FIXME: should be - invalidate( origBoundsR )

	// NB: correct height for native platform limitations as needed
	if (!m_BUseVerticalOrientation && m_BFixedHeight)
	{
	wxSize		actualSize;

		actualSize = CalculateDefaultSize();
		height = actualSize.y;
	}

	wxControl::DoSetSize( x, y, width, height, sizeFlags );

	if (m_BProportionalResizing)
		RescaleToFit( width );

	// NB: is this advisable?
	wxControl::DoGetPosition( &(m_NativeBoundsR.x), &(m_NativeBoundsR.y) );
	wxControl::DoGetSize( &(m_NativeBoundsR.width), &(m_NativeBoundsR.height) );

	// RecalculateItemExtents();
	SetViewDirty();
}

wxSize wxColumnHeader::CalculateDefaultSize( void ) const
{
wxWindow	*parentW;
wxSize		targetSize, itemSize, minSize, parentSize;
bool			bIsVertical;

	targetSize.x =
	targetSize.y = 0;

	minSize.x = wxCH_minimum_x;
	minSize.y = 17;

	parentSize.x =
	parentSize.y = 0;

	// "best" width is parent's width;
	// height is (relatively) invariant,
	// as determined by native (HI/CommonControls) drawing routines
	parentW = GetParent();
	if (parentW != NULL)
		parentW->GetClientSize( &(parentSize.x), &(parentSize.y) );

	itemSize = GetDefaultItemSize();

	bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
	if (bIsVertical)
	{
		targetSize.x = parentSize.x;
		targetSize.y = parentSize.y;
	}
	else
	{
		targetSize.x = parentSize.x;
		targetSize.y = itemSize.y;
	}

	targetSize.x = ((targetSize.x > minSize.x) ? targetSize.x : minSize.x);
	targetSize.y = ((targetSize.y > minSize.y) ? targetSize.y : minSize.y);

#if 0
	if (! HasFlag( wxBORDER_NONE ))
	{
		// the border would clip the last line otherwise
		targetSize.x += 4;
		targetSize.y += 6;
	}
#endif

	return targetSize;
}

wxSize wxColumnHeader::CalculateDefaultItemSize(
	wxSize		maxSize ) const
{
wxSize		targetSize, minSize, parentSize;

	targetSize.x =
	targetSize.y = 0;

	minSize.x = wxCH_minimum_x;
	minSize.y = 17;

	// "best" width is parent's width;
	// height is (relatively) invariant,
	// as determined by native (HI/CommonControls) drawing routines
	parentSize = maxSize;
	targetSize.x = parentSize.x;
	if (m_ExpectedItemCount > 1)
		targetSize.x /= m_ExpectedItemCount;

	// get (platform-dependent) height
#if defined(__WXMSW__)
	{
	HDLAYOUT	hdl;
	WINDOWPOS	wp;
	HWND		targetViewRef;
	RECT		boundsR;

		targetViewRef = GetHwnd();
		boundsR.left =
		boundsR.top = 0;
		boundsR.right = parentSize.x;
		boundsR.bottom = parentSize.y;

		ZeroMemory( &hdl, sizeof(hdl) );
		hdl.prc = &boundsR;
		hdl.pwpos = &wp;
		if (Header_Layout( targetViewRef, (LPARAM)&hdl ))
		{
			targetSize.x = wp.cx;
			targetSize.y = wp.cy;
		}
	}

#elif defined(__WXMAC__)
	{
	SInt32		standardHeight;
	OSStatus		errStatus;

		errStatus = GetThemeMetric( kThemeMetricListHeaderHeight, &standardHeight );
		if (errStatus == noErr)
			targetSize.y = standardHeight;
	}
#endif

	targetSize.x = ((targetSize.x > minSize.x) ? targetSize.x : minSize.x);
	targetSize.y = ((targetSize.y > minSize.y) ? targetSize.y : minSize.y);

	return targetSize;
}

wxSize wxColumnHeader::GetDefaultItemSize( void ) const
{
	return m_DefaultItemSize;
}

void wxColumnHeader::SetDefaultItemSize(
	wxSize		targetSize )
{
	if (targetSize.x > 0)
		m_DefaultItemSize.x = targetSize.x;
	if (targetSize.y > 0)
		m_DefaultItemSize.y = targetSize.y;
}

// static
void wxColumnHeader::GetDefaultLabelValue(
	bool			isColumn,
	int			index,
	wxString		&value )
{
	if (isColumn)
	{
		// default column labels are:
		// columns 0 to 25: A-Z
		// columns 26 to 675: AA-ZZ
		// and so on
		wxString s;
		unsigned int i, n;
		for (n = 1; index >= 0; n++)
		{
			s += (wxChar)(wxT('A') + (wxChar)(index % 26));
			index /= 26;
			index--;
		}

		// reverse the string
		value = wxEmptyString;
		for (i = 0; i < n; i++)
			value += s[n - i - 1];
	}
	else
	{
		// starting the rows at zero confuses users,
		// no matter how much it makes sense to geeks.
		value << index + 1;
	}
}

// static
wxVisualAttributes wxColumnHeader::GetClassDefaultAttributes(
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

// ----------------------------------------------------------------------------
// event handlers
// ----------------------------------------------------------------------------

// virtual
void wxColumnHeader::OnPaint(
	wxPaintEvent		& WXUNUSED(event) )
{
	Draw();

#if 0 && defined(__WXMSW__)
	// NB: moved all drawing code into (where else?) ::Draw

	// these work...
//	event.Skip();
//	wxWindowMSW::MSWDefWindowProc( WM_PAINT, 0, 0 );

	// ...and these fail to work.
//	wxControl::OnPaint( event );
//	wxWindow::OnPaint( event );
//	wxControl::MSWWindowProc( WM_PAINT, 0, 0 );
//	::DefWindowProc( GetHwnd(), WM_PAINT, 0, 0 );
#endif
}

void wxColumnHeader::OnDoubleClick(
	wxMouseEvent		&event )
{
long		itemIndex;

	itemIndex = HitTest( event.GetPosition() );
	if (itemIndex >= CH_HITTEST_ItemZero)
	{
		// NB: just call the single click handler for the present
		OnClick( event );

		// NB: unused for the present
		//GenerateSelfEvent( wxEVT_COLUMNHEADER_DOUBLECLICKED );
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
		if (itemIndex >= CH_HITTEST_ItemZero)
		{
			if (IsEnabled())
			{
				OnClick_SelectOrToggleSort( itemIndex, true );
				GenerateSelfEvent( wxEVT_COLUMNHEADER_SELCHANGED );
			}
			break;
		}
		else
		{
			// unknown message - unhandled - fall through
			//wxLogDebug( wxT("wxColumnHeader::OnClick - unknown hittest code") );
		}

	case CH_HITTEST_NoPart:
		event.Skip();
		break;
	}
}

void wxColumnHeader::OnClick_SelectOrToggleSort(
	long				itemIndex,
	bool				bToggleSortDirection )
{
long			curSelectionIndex;

	curSelectionIndex = GetSelectedItem();
	if (itemIndex != m_ItemSelected)
	{
		SetSelectedItem( itemIndex );
	}
	else if (bToggleSortDirection)
	{
	wxColumnHeaderItem	*item;
	bool				bSortFlag;

		item = ((m_ItemList != NULL) ? m_ItemList[itemIndex] : NULL);
		if (item != NULL)
			if (item->GetAttribute( CH_ITEM_ATTR_SortEnabled ))
			{
				bSortFlag = item->GetAttribute( CH_ITEM_ATTR_SortDirection );
				item->SetAttribute( CH_ITEM_ATTR_SortDirection, ! bSortFlag );

				if (m_BVisibleSelection)
					RefreshItem( itemIndex, true );
			}

		// for testing: can induce text wrapping outside of bounds rect
//		item->SetLabelText( _wxT("같같 YOW! 같같") );
	}
}

void wxColumnHeader::OnMouseEvent( wxMouseEvent &WXUNUSED(event) )
{
#if 1
	// under construction
	// NB: remove WXUNUSED() macro when routine is inplemented
#else
#endif
}

// WARNING: this is lifted from "grid.cpp" and probably obsolete
// also note that it's NOPped out
//
void wxColumnHeader::ProcessLabelMouseEvent( wxMouseEvent &WXUNUSED(event) )
{
#if 1
	// under construction
	// NB: remove WXUNUSED() macro when routine is inplemented
#else
	int x, y, col;
	wxPoint pos( event.GetPosition() );
	CalcUnscrolledPosition( pos.x, pos.y, &x, &y );

	if (event.Dragging())
	{
		if (! m_isDragging)
		{
			m_isDragging = true;
			m_ParentWin->CaptureMouse();
		}

		if (event.LeftIsDown())
		{
			int cw, ch, dummy, top;
			m_gridWin->GetClientSize( &cw, &ch );
			CalcUnscrolledPosition( 0, 0, &dummy, &top );

			wxClientDC dc( m_ParentWin );
			PrepareDC( dc );

			x = wxMax(
				x,
				GetColLeft( m_dragRowOrCol )
				+ GetColMinimalWidth( m_dragRowOrCol ) );
			dc.SetLogicalFunction( wxINVERT );
			if (m_dragLastPos >= 0)
				dc.DrawLine( m_dragLastPos, top, m_dragLastPos, top + ch );
			dc.DrawLine( x, top, x, top + ch );
			m_dragLastPos = x;
		}

		return;
	}

	if (m_isDragging && (event.Entering() || event.Leaving()))
		return;

	if (m_isDragging)
	{
		if (m_colLabelWin->HasCapture())
			m_colLabelWin->ReleaseMouse();
		m_isDragging = false;
	}

	if (event.Entering() || event.Leaving())
	{
		// -- Entering or leaving the window
		ChangeCursorMode( WXGRID_CURSOR_SELECT_CELL, m_colLabelWin );
	}
	else if (event.LeftDown())
	{
		// -- Left button pressed
		// don't send a label click event for a hit on the edge of the column label
		// - this is probably the user wanting to resize the column
		//
		if (XToEdgeOfCol( x ) < 0)
		{
			col = XToCol( x );
			if ((col >= 0) &&
				! SendEvent( wxEVT_GRID_LABEL_LEFT_CLICK, -1, col, event ))
			{
				if (! event.ShiftDown() && !event.ControlDown())
					ClearSelection();
				if (m_selection)
				{
					if (event.ShiftDown())
					{
						m_selection->SelectBlock(
							0,
							m_currentCellCoords.GetCol(),
							GetNumberRows() - 1,
							col,
							event.ControlDown(),
							event.ShiftDown(),
							event.AltDown(),
							event.MetaDown() );
					}
					else
					{
						m_selection->SelectCol(
							col,
							event.ControlDown(),
							event.ShiftDown(),
							event.AltDown(),
							event.MetaDown() );
					}
				}

				ChangeCursorMode( WXGRID_CURSOR_SELECT_COL, m_colLabelWin );
			}
		}
		else
		{
			// starting to drag-resize a column
			if (CanDragColSize())
				ChangeCursorMode( WXGRID_CURSOR_RESIZE_COL, m_colLabelWin );
		}
	}

	if (event.LeftDClick())
	{
		// -- Left double click
		int col = XToEdgeOfCol( x );
		if (col < 0)
		{
			col = XToCol( x );
			if ((col >= 0) &&
				! SendEvent( wxEVT_GRID_LABEL_LEFT_DCLICK, -1, col, event ))
			{
				// no default action at the moment
			}
		}
		else
		{
			// adjust column width depending on label text
			AutoSizeColLabelSize( col );

			ChangeCursorMode(WXGRID_CURSOR_SELECT_CELL, m_colLabelWin);
			m_dragLastPos = (-1);
		}
	}
	else if (event.LeftUp())
	{
		// -- Left button released
		DoEndDragResizeCol();

		// Note: we are ending the event *after* doing
		// default processing in this case
		//
		SendEvent( wxEVT_GRID_COL_SIZE, -1, m_dragRowOrCol, event );

		ChangeCursorMode( WXGRID_CURSOR_SELECT_CELL, m_colLabelWin );
		m_dragLastPos = (-1);
	}
	else if (event.RightDown())
	{
		// -- Right button down
		col = XToCol( x );
		if ((col >= 0) &&
			! SendEvent( wxEVT_GRID_LABEL_RIGHT_CLICK, -1, col, event ))
		{
			// no default action at the moment
		}
	}
	else if (event.RightDClick())
	{
		// -- Right double click
		col = XToCol( x );
		if ((col >= 0) &&
			! SendEvent( wxEVT_GRID_LABEL_RIGHT_DCLICK, -1, col, event ))
		{
			// no default action at the moment
		}
	}
	else if (event.Moving())
	{
		// -- No buttons down and mouse moving
		m_dragRowOrCol = XToEdgeOfCol( x );
		if (m_dragRowOrCol >= 0)
		{
			if (m_cursorMode == WXGRID_CURSOR_SELECT_CELL)
			{
				// don't capture the cursor yet
				if (CanDragColSize())
					ChangeCursorMode( WXGRID_CURSOR_RESIZE_COL, m_colLabelWin, false );
			}
		}
		else if (m_cursorMode != WXGRID_CURSOR_SELECT_CELL)
		{
			ChangeCursorMode( WXGRID_CURSOR_SELECT_CELL, m_colLabelWin, false );
		}
	}
#endif
}

// ================
#if 0
#pragma mark -
#endif

void wxColumnHeader::GetSelectionColour(
	wxColour			&targetColour ) const
{
	targetColour = m_SelectionColour;
}

void wxColumnHeader::SetSelectionColour(
	const wxColour		&targetColour )
{
	m_SelectionColour = targetColour;
}

long wxColumnHeader::GetSelectionDrawStyle( void ) const
{
	return m_SelectionDrawStyle;
}

// NB: this has no effect on the Mac selection UI,
// which is well-defined.
//
void wxColumnHeader::SetSelectionDrawStyle(
	long			styleValue )
{
	if (m_SelectionDrawStyle == styleValue)
		return;
	if ((styleValue < CH_SELECTIONDRAWSTYLE_FIRST)
			|| (styleValue > CH_SELECTIONDRAWSTYLE_LAST))
		return;

	m_SelectionDrawStyle = styleValue;

	if (m_ItemSelected >= 0)
		RefreshItem( m_ItemSelected, true );
}

bool wxColumnHeader::GetAttribute(
	wxColumnHeaderAttribute		flagEnum ) const
{
bool			bResult;

	bResult = false;

	switch (flagEnum)
	{
	case CH_ATTR_VerticalOrientation:
		bResult = m_BUseVerticalOrientation;
		break;

	case CH_ATTR_Unicode:
		bResult = m_BUseUnicode;
		break;

	case CH_ATTR_GenericRenderer:
		bResult = m_BUseGenericRenderer;
		break;

	case CH_ATTR_VisibleSelection:
		bResult = m_BVisibleSelection;
		break;

	case CH_ATTR_ProportionalResizing:
		bResult = m_BProportionalResizing;
		break;

	default:
		break;
	}

	return bResult;
}

bool wxColumnHeader::SetAttribute(
	wxColumnHeaderAttribute		flagEnum,
	bool						bFlagValue )
{
bool			bResult;

	bResult = true;

	switch (flagEnum)
	{
	case CH_ATTR_VerticalOrientation:
		// NB: runtime assignment not (currently) supported
		// m_BUseVerticalOrientation = bFlagValue;
		break;

	case CH_ATTR_Unicode:
		// NB: runtime assignment not (currently) supported
		// m_BUseUnicode = bFlagValue;
		break;

	case CH_ATTR_GenericRenderer:
#if defined(__WXMSW__) || defined(__WXMAC__)
		if (m_BUseGenericRenderer != bFlagValue)
		{
		long		i;

			m_BUseGenericRenderer = bFlagValue;

			for (i=0; i<m_ItemCount; i++)
				m_ItemList[i]->InvalidateTextExtent();

			SetViewDirty();
		}
#endif
		break;

	case CH_ATTR_VisibleSelection:
		if (m_BVisibleSelection != bFlagValue)
		{
			m_BVisibleSelection = bFlagValue;

			if (m_ItemSelected >= 0)
				RefreshItem( m_ItemSelected, true );
		}
		break;

	case CH_ATTR_ProportionalResizing:
		if (m_BProportionalResizing != bFlagValue)
			m_BProportionalResizing = bFlagValue;
		break;

	default:
		bResult = false;
		break;
	}

	return bResult;
}

// ================
#if 0
#pragma mark -
#endif

// ----------------------------------------------------------------------------
// utility
// ----------------------------------------------------------------------------

long wxColumnHeader::GetTotalUIExtent(
	long				itemCount,
	bool				bStartAtBase ) const
{
long		extentDim, i, startItem;

	if ((itemCount < 0) || (itemCount > m_ItemCount))
		itemCount = m_ItemCount;

	extentDim = 0;

	startItem = 0;
	if (bStartAtBase)
		startItem = 0;

	if (m_ItemList != NULL)
		for (i=0; i<itemCount; i++)
		{
			if (m_ItemList[i] != NULL)
				if (m_ItemList[i]->m_BVisible)
					extentDim += m_ItemList[i]->m_Extent.x;
		}

	return extentDim;
}

// NB: ignores current view range
//
bool wxColumnHeader::RescaleToFit(
	long				newWidth )
{
long		scaleItemCount, scaleItemAmount, i;
long		deltaX, summerX, resultX, originX, incX;
bool		bIsVertical;

	if ((newWidth <= 0) || (m_ItemList == NULL))
		return false;

	// FIXME: needs work for vertical row headers
	bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
	if (bIsVertical)
		return false;

	// count visible, non-fixed-width items and tabulate size
	scaleItemCount = 0;
	scaleItemAmount = 0;
	for (i=0; i<m_ItemCount; i++)
	{
		if ((m_ItemList[i] == NULL) || !m_ItemList[i]->m_BVisible || m_ItemList[i]->m_BFixedWidth)
			continue;

		scaleItemCount++;
		scaleItemAmount += m_ItemList[i]->m_Extent.x;
	}

	// determine width delta
	deltaX = newWidth - m_NativeBoundsR.width;
	summerX = deltaX;
	originX = 0;

	// move and resize items as appropriate
	for (i=0; i<m_ItemCount; i++)
	{
		if (m_ItemList[i] == NULL)
			continue;

		// move to new origin
		m_ItemList[i]->m_Origin.x = originX;
//		m_ItemList[i]->m_Origin = origin;

		// resize item, if non-fixed
		if (m_ItemList[i]->m_BVisible && !m_ItemList[i]->m_BFixedWidth)
		{
			scaleItemCount--;

			if (scaleItemCount > 0)
				incX = (deltaX * m_ItemList[i]->m_Extent.x) / scaleItemAmount;
			else
				incX = summerX;

			if (incX != 0)
			{
				resultX = m_ItemList[i]->m_Extent.x + incX;
				m_ItemList[i]->ResizeToWidth( resultX );
			}

			summerX -= incX;
		}

		originX += m_ItemList[i]->m_Extent.x;
	}

	for (i=0; i<m_ItemCount; i++)
		RefreshItem( i, false );
	SetViewDirty();

	return true;
}

bool wxColumnHeader::ResizeToFit(
	long				itemCount )
{
long		extentV;
bool		bIsVertical, bScaling;

	if ((itemCount < 0) || (itemCount > m_ItemCount))
		itemCount = m_ItemCount;

	bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
	if (bIsVertical)
	{
		extentV = itemCount * m_DefaultItemSize.y;
		DoSetSize( m_NativeBoundsR.x, m_NativeBoundsR.y, m_DefaultItemSize.x, extentV, 0 );
	}
	else
	{
		// temporarily turn off proportional resizing
		bScaling = m_BProportionalResizing;
		m_BProportionalResizing = false;

		extentV = GetTotalUIExtent( itemCount );
		DoSetSize( m_NativeBoundsR.x, m_NativeBoundsR.y, extentV, m_NativeBoundsR.height, 0 );

		if (bScaling)
			m_BProportionalResizing = true;
	}

	return true;
}

bool wxColumnHeader::ResizeDivision(
	long				itemIndex,
	long				originX )
{
wxColumnHeaderItem		*itemRef1, *itemRef2;
long					deltaV, newExtent1, newExtent2;
bool					bIsVertical;

	if ((itemIndex <= 0) || (itemIndex >= m_ItemCount))
		return false;

	// FIXME: needs work for vertical row headers;
	// may not be meaningful because Y dimension is assumed to be invariant
	bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
	if (bIsVertical)
		return false;

	itemRef1 = GetItemRef( itemIndex - 1 );
	itemRef2 = GetItemRef( itemIndex );
	if ((itemRef1 == NULL) || (itemRef2 == NULL))
		return false;

//	if (bIsVertical)
//	{
//		if ((originY <= itemRef1->m_OriginY) || (originY >= itemRef2->m_OriginY + itemRef2->m_ExtentY))
//			return false;
//	}
//	else
	{
		if ((originX <= itemRef1->m_Origin.x) || (originX >= itemRef2->m_Origin.x + itemRef2->m_Extent.x))
			return false;
	}

	deltaV = itemRef2->m_Origin.x - originX;
	newExtent1 = itemRef1->m_Extent.x - deltaV;
	newExtent2 = itemRef2->m_Extent.x + deltaV;

	itemRef2->m_Origin.x = itemRef1->m_Origin.x + newExtent1;
	itemRef1->ResizeToWidth( newExtent1 );
	itemRef2->ResizeToWidth( newExtent2 );

	RefreshItem( itemIndex - 1, true );
	RefreshItem( itemIndex, true );

	return true;
}

// ================
#if 0
#pragma mark -
#endif

long wxColumnHeader::GetSelectedItem( void ) const
{
	return m_ItemSelected;
}

void wxColumnHeader::SetSelectedItem(
	long			itemIndex )
{
long		i;
bool		bSelected;

	if (m_ItemSelected != itemIndex)
	{
		for (i=0; i<m_ItemCount; i++)
		{
			bSelected = (i == itemIndex);
			if ((m_ItemList != NULL) && (m_ItemList[i] != NULL))
				m_ItemList[i]->SetAttribute( CH_ITEM_ATTR_Selected, bSelected );

			RefreshItem( i, false );
		}

		m_ItemSelected = itemIndex;

		SetViewDirty();
	}
}

bool wxColumnHeader::GetItemVisibility(
	long				itemIndex ) const
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
		bResultV = itemRef->m_BVisible;

	return bResultV;
}

void wxColumnHeader::SetItemVisibility(
	long				itemIndex,
	bool				bVisible )
{
wxColumnHeaderItem		*itemRef;

	if ((itemIndex < 0) || (itemIndex >= m_ItemCount))
		return;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
		if (itemRef->m_BVisible != bVisible)
		{
			itemRef->m_BVisible = bVisible;
			if (ItemInView( itemIndex ))
				SetViewDirty();
		}
}

long wxColumnHeader::GetBaseViewItem( void ) const
{
	return m_ItemViewBaseIndex;
}

void wxColumnHeader::SetBaseViewItem(
	long			itemIndex )
{
	if ((itemIndex < 0) || (itemIndex >= m_ItemCount))
		return;

	if (m_ItemViewBaseIndex != itemIndex)
	{
		m_ItemViewBaseIndex = itemIndex;

		m_ItemViewBaseOrigin = 0;
		if (itemIndex > 0)
		{
		wxColumnHeaderItem		*itemRef;

			// cache the value of the starting left/top edge
			// in order to simplify item bounds calculations
			itemRef = GetItemRef( itemIndex );
			if (itemRef != NULL)
				m_ItemViewBaseOrigin = itemRef->m_Origin.x;
		}

		RecalculateItemExtents();
		SetViewDirty();
	}
}

// ================
#if 0
#pragma mark -
#endif

// NB: hinting - unused
//
long wxColumnHeader::GetExpectedItemCount( void ) const
{
	return m_ExpectedItemCount;
}

void wxColumnHeader::SetExpectedItemCount(
	long			itemCount )
{
	if (itemCount < 0)
		itemCount = 0;

	m_ExpectedItemCount = itemCount;
}

long wxColumnHeader::GetItemCount( void ) const
{
	return (long)m_ItemCount;
}

void wxColumnHeader::SetItemCount(
	long			itemCount )
{
	if (itemCount < 0)
		itemCount = 0;

	if (itemCount > m_ItemCount)
		AddEmptyItems( -1, itemCount - m_ItemCount, true );
	else if (itemCount < m_ItemCount)
		DeleteItems( itemCount, m_ItemCount - itemCount );
}

void wxColumnHeader::DeleteItems(
	long			itemIndex,
	long			itemCount )
{
long		i;

	for (i=0; i<itemCount; i++)
		DeleteItem( itemIndex );
}

void wxColumnHeader::DeleteItem(
	long			itemIndex )
{
long		i;

	if ((itemIndex >= 0) && (itemIndex < m_ItemCount))
	{
#if defined(__WXMSW__)
		(void)MSWItemDelete( itemIndex );
#endif

		if (m_ItemList != NULL)
		{
			if (m_ItemCount > 1)
			{
				// delete the target item
				delete m_ItemList[itemIndex];

				// close the list hole
				for (i=itemIndex; i<m_ItemCount-1; i++)
					m_ItemList[i] = m_ItemList[i + 1];

				// leave a NULL spot at the end
				m_ItemList[m_ItemCount - 1] = NULL;
				m_ItemCount--;

				// recalculate item origins
				RecalculateItemExtents();
			}
			else
				DisposeItemList();

			// if this item was selected, then there is a selection no longer
			if (m_ItemSelected == itemIndex)
				m_ItemSelected = CH_HITTEST_NoPart;

			SetViewDirty();
		}
	}
}

void wxColumnHeader::AppendItem(
	const wxString		&textBuffer,
	long				textJust,
	long				extentX,
	bool				bSelected,
	bool				bSortEnabled,
	bool				bSortAscending )
{
	AddItem( -1, textBuffer, textJust, extentX, bSelected, bSortEnabled, bSortAscending );
}

void wxColumnHeader::AddEmptyItems(
	long				beforeIndex,
	long				itemCount,
	bool				bUseDefaultLabel )
{
wxString	labelValue;
long		i;

	for (i=0; i<itemCount; i++)
	{
		if (bUseDefaultLabel)
			GetDefaultLabelValue( !m_BUseVerticalOrientation, i, labelValue );
		AddItem( beforeIndex, labelValue, CH_JUST_Left, -1, false, true, true );
	}
}

void wxColumnHeader::AddItem(
	long				beforeIndex,
	const wxString		&textBuffer,
	long				textJust,
	long				extentX,
	bool				bSelected,
	bool				bSortEnabled,
	bool				bSortAscending )
{
wxColumnHeaderItem		itemInfo;
wxSize					targetExtent;
long					originX;
bool					bIsVertical;

	// set (initially) invariant values
	itemInfo.m_BVisible = true;
	itemInfo.m_BEnabled = true;
	itemInfo.m_BitmapJust = CH_JUST_Center;
	itemInfo.m_Origin.y = 0;
	itemInfo.m_Extent.y = 0;

	// set default-specified values
	bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
	if (extentX < 0)
	{
		if (!bIsVertical)
			extentX = m_DefaultItemSize.x;
		else
			extentX = m_DefaultItemSize.y;
	}

	// set specified values
	itemInfo.m_LabelTextRef = textBuffer;
	itemInfo.m_TextJust = textJust;
	itemInfo.m_Extent.x = extentX;
	itemInfo.m_BSelected = ((m_ItemSelected < 0) ? bSelected : false);
	itemInfo.m_BSortEnabled = bSortEnabled && !bIsVertical;
	itemInfo.m_BSortAscending = bSortAscending;

	// determine new item origin
	itemInfo.m_Origin.x = 0;
	if ((beforeIndex < 0) || (beforeIndex > m_ItemCount))
		beforeIndex = m_ItemCount;
	if (beforeIndex > 0)
	{
		if (!bIsVertical)
		{
			// ALERT: currently, GetUIExtent returns (x = origin, y = extent);
			// this will change
			targetExtent = GetUIExtent( beforeIndex - 1 );
			originX = ((targetExtent.x > 0) ? targetExtent.x : 0);
			itemInfo.m_Origin.x = originX + targetExtent.y;
		}
	}

	AddItemList( &itemInfo, 1, beforeIndex );
}

void wxColumnHeader::AddItemList(
	const wxColumnHeaderItem		*itemList,
	long							itemCount,
	long							beforeIndex )
{
wxColumnHeaderItem	**newItemList;
long				targetIndex, i;
bool				bIsSelected;

	if ((itemList == NULL) || (itemCount <= 0))
		return;

	if ((beforeIndex < 0) || (beforeIndex > m_ItemCount))
		beforeIndex = m_ItemCount;

	// allocate new item list and copy the original list items into it
	newItemList = (wxColumnHeaderItem**)calloc( m_ItemCount + itemCount, sizeof(wxColumnHeaderItem*) );
	if (m_ItemList != NULL)
	{
		for (i=0; i<m_ItemCount; i++)
		{
			targetIndex = ((i < beforeIndex) ? i : itemCount + i);
			newItemList[targetIndex] = m_ItemList[i];
		}

		free( m_ItemList );
	}
	m_ItemList = newItemList;

	// append the new items
	for (i=0; i<itemCount; i++)
	{
		targetIndex = beforeIndex + i;
		m_ItemList[targetIndex] = new wxColumnHeaderItem( &itemList[i] );

		bIsSelected = (m_ItemList[targetIndex]->m_BSelected && m_ItemList[targetIndex]->m_BEnabled);

#if defined(__WXMSW__)
		MSWItemInsert(
			targetIndex,
			m_ItemList[targetIndex]->m_Extent.x,
			m_ItemList[targetIndex]->m_LabelTextRef.c_str(),
			m_ItemList[targetIndex]->m_TextJust,
			m_BUseUnicode,
			bIsSelected,
			m_ItemList[targetIndex]->m_BSortEnabled,
			m_ItemList[targetIndex]->m_BSortAscending );
#endif

		if (bIsSelected && (m_ItemSelected < 0))
			m_ItemSelected = targetIndex;
	}

	// update the item count
	m_ItemCount += itemCount;

	// if this was an insertion, refresh the end items
	if (beforeIndex < m_ItemCount - itemCount)
	{
		RecalculateItemExtents();
		for (i=0; i<itemCount; i++)
			RefreshItem( i + (m_ItemCount - itemCount), false );
	}

	// if this moves the selection, reset it
	if (m_ItemSelected >= beforeIndex)
	{
	long		savedIndex;

		savedIndex = m_ItemSelected;
		m_ItemSelected = CH_HITTEST_NoPart;
		SetSelectedItem( savedIndex );
	}

	SetViewDirty();
}

void wxColumnHeader::DisposeItemList( void )
{
long		i;

	if (m_ItemList != NULL)
	{
		for (i=0; i<m_ItemCount; i++)
			delete m_ItemList[i];

		free( m_ItemList );
		m_ItemList = NULL;
	}

	m_ItemCount = 0;
	m_ItemSelected = CH_HITTEST_NoPart;
}

// ================
#if 0
#pragma mark -
#endif

bool wxColumnHeader::GetItemData(
	long							itemIndex,
	wxColumnHeaderItem				*info ) const
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

bool wxColumnHeader::ItemInView(
	long				itemIndex ) const
{
wxColumnHeaderItem		*itemRef;
bool				bResultV;

	if (itemIndex < m_ItemViewBaseIndex)
		return false;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);

	return bResultV;
}

bool wxColumnHeader::GetItemBounds(
	long				itemIndex,
	wxRect				*boundsR ) const
{
wxColumnHeaderItem		*itemRef;
bool				bResultV, bIsVertical;

	if (boundsR == NULL)
		return false;

	bResultV = ItemInView( itemIndex );
	if (bResultV)
	{
		itemRef = GetItemRef( itemIndex );
		bResultV = (itemRef != NULL);
	}

	if (bResultV)
	{
		bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
		if (bIsVertical)
		{
			// is this item beyond the bottom edge?
//			if (bResultV)
//				bResultV = (itemRef->m_Origin.x < m_NativeBoundsR.height);

			if (bResultV)
			{
				boundsR->x = 0;
				boundsR->y = m_DefaultItemSize.y * (itemIndex - m_ItemViewBaseIndex);
				boundsR->width = m_DefaultItemSize.x;
				boundsR->height = m_DefaultItemSize.y;

//				if (boundsR->height > m_NativeBoundsR.height - itemRef->m_Origin.x)
//					boundsR->height = m_NativeBoundsR.height - itemRef->m_Origin.x;

				bResultV = ((boundsR->width > 0) && (boundsR->height > 0));
			}
		}
		else
		{
			// is this item beyond the right edge?
			if (bResultV)
				bResultV = (itemRef->m_Origin.x < m_NativeBoundsR.width);

			if (bResultV)
			{
				boundsR->x = itemRef->m_Origin.x;
				boundsR->y = 0; // m_NativeBoundsR.y;
				boundsR->width = itemRef->m_Extent.x + 1;
				boundsR->height = m_NativeBoundsR.height;

				if (boundsR->width > m_NativeBoundsR.width - itemRef->m_Origin.x)
					boundsR->width = m_NativeBoundsR.width - itemRef->m_Origin.x;

				bResultV = ((boundsR->width > 0) && (boundsR->height > 0));
			}
		}
	}

	if (! bResultV)
	{
		boundsR->x =
		boundsR->y =
		boundsR->width =
		boundsR->height = 0;
	}

	return bResultV;
}

wxColumnHeaderItem * wxColumnHeader::GetItemRef(
	long			itemIndex ) const
{
	if ((itemIndex >= 0) && (itemIndex < m_ItemCount))
		return m_ItemList[itemIndex];
	else
		return NULL;
}

long wxColumnHeader::GetArrowButtonStyle(
	long				itemIndex ) const
{
wxColumnHeaderItem		*itemRef;
long					targetStyle;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
		targetStyle = itemRef->GetArrowButtonStyle();
	else
		targetStyle = 0;

	return targetStyle;
}

void wxColumnHeader::SetArrowButtonStyle(
	long				itemIndex,
	long				targetStyle )
{
wxColumnHeaderItem		*itemRef;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
	{
		itemRef->SetArrowButtonStyle( targetStyle );
		RefreshItem( itemIndex, true );
	}
}

void wxColumnHeader::GetBitmapRef(
	long				itemIndex,
	wxBitmap			&bitmapRef ) const
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		itemRef->GetBitmapRef( bitmapRef );
	}
	else
	{
//		bitmapRef.SetOK( false );
	}
}

void wxColumnHeader::SetBitmapRef(
	long				itemIndex,
	wxBitmap			&bitmapRef )
{
wxColumnHeaderItem		*itemRef;
wxRect					boundsR;

	if (GetItemBounds( itemIndex, &boundsR ))
	{
		itemRef = GetItemRef( itemIndex );
		if (itemRef != NULL)
		{
			itemRef->SetBitmapRef( bitmapRef, &boundsR );
			RefreshItem( itemIndex, true );
		}
	}
}

long wxColumnHeader::GetBitmapJustification(
	long				itemIndex ) const
{
wxColumnHeaderItem		*itemRef;
long					targetJust;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
		targetJust = itemRef->GetBitmapJustification();
	else
		targetJust = 0;

	return targetJust;
}

void wxColumnHeader::SetBitmapJustification(
	long				itemIndex,
	long				targetJust )
{
wxColumnHeaderItem		*itemRef;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
	{
		itemRef->SetBitmapJustification( targetJust );
		RefreshItem( itemIndex, true );
	}
}

wxString wxColumnHeader::GetLabelText(
	long				itemIndex ) const
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
		textBuffer = wxT("");
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
		RefreshItem( itemIndex, true );
	}
}

long wxColumnHeader::GetLabelJustification(
	long				itemIndex ) const
{
wxColumnHeaderItem		*itemRef;
long					targetJust;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
		targetJust = itemRef->GetLabelJustification();
	else
		targetJust = 0;

	return targetJust;
}

void wxColumnHeader::SetLabelJustification(
	long				itemIndex,
	long				targetJust )
{
wxColumnHeaderItem		*itemRef;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
	{
		itemRef->SetLabelJustification( targetJust );
		RefreshItem( itemIndex, true );
	}
}

wxSize wxColumnHeader::GetUIExtent(
	long				itemIndex ) const
{
wxColumnHeaderItem		*itemRef;
wxSize					extentPt;
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
	long				itemIndex,
	wxSize				&extentPt )
{
wxColumnHeaderItem		*itemRef;

	itemRef = GetItemRef( itemIndex );
	if (itemRef != NULL)
	{
		itemRef->SetUIExtent( extentPt.x, extentPt.y );

		RecalculateItemExtents();
		RefreshItem( itemIndex, true );
	}
}

bool wxColumnHeader::GetItemAttribute(
	long						itemIndex,
	wxColumnHeaderItemAttribute	flagEnum ) const
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
		bResultV = itemRef->GetAttribute( flagEnum );

	return bResultV;
}

bool wxColumnHeader::SetItemAttribute(
	long						itemIndex,
	wxColumnHeaderItemAttribute	flagEnum,
	bool						bFlagValue )
{
wxColumnHeaderItem		*itemRef;
bool					bResultV;

	itemRef = GetItemRef( itemIndex );
	bResultV = (itemRef != NULL);
	if (bResultV)
	{
		if (itemRef->SetAttribute( flagEnum, bFlagValue ))
			RefreshItem( itemIndex, true );
	}

	return bResultV;
}

wxColumnHeaderHitTestResult wxColumnHeader::HitTest(
	const wxPoint		&locationPt )
{
wxColumnHeaderHitTestResult		resultV;
bool					bIsVertical;

	resultV = CH_HITTEST_NoPart;

	bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
	if (bIsVertical)
	{
	wxRect	boundsR;
	long		i;

		for (i=0; i<m_ItemCount; i++)
		{
			if (GetItemBounds( i, &boundsR ))
			{
				if ((locationPt.x >= boundsR.x) && (locationPt.x < boundsR.x + boundsR.width)
					&& (locationPt.y >= boundsR.y) && (locationPt.y < boundsR.y + boundsR.height))
				{
					resultV = (wxColumnHeaderHitTestResult)i;
					break;
				}
			}
		}

		return resultV;
	}

#if defined(__WXMSW__)
RECT		boundsR;
HWND		targetViewRef;
long		itemCount, i;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		//wxLogDebug( wxT("targetViewRef = GetHwnd failed (NULL)") );
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
long		i;

	for (i=0; i<m_ItemCount; i++)
		if (m_ItemList[i] != NULL)
			if (m_ItemList[i]->HitTest( locationPt ) != 0)
			{
				resultV = (wxColumnHeaderHitTestResult)i;
				break;
			}
#endif

	return resultV;
}

long wxColumnHeader::Draw( void )
{
wxRect		boundsR;
long		resultV, i;

	resultV = 0;

#if 0
	wxLogDebug( wxT("wxColumnHeader::Draw - entered") );
#endif

	if (m_BUseGenericRenderer)
	{
	wxPaintDC	dc( this );

		// FIXME: what about transparency ??
		dc.Clear();

		// NB: various experiments in graphics state prophylaxis
		// most don't appear to be necessary, but may be needed in the future;
		// however, the SetFont is required
		dc.SetTextForeground( *wxBLACK );
		dc.SetFont( m_Font );
#if defined(__WXMAC__)
		dc.MacInstallFont();
#endif

		// dc.SetLogicalFunction( wxCOPY );
		// dc.SetBrush( wxBrush(*wxBLACK, wxSOLID) );
		// dc.SetPen( wxPen(*wxBLACK, 1, wxSOLID) );

		dc.DestroyClippingRegion();

		for (i=0; i<m_ItemCount; i++)
		{
			if ((i < m_ItemViewBaseIndex) || !GetItemVisibility( i ))
				continue;

			if (GetItemBounds( i, &boundsR ))
			{
				dc.SetClippingRegion( boundsR.x, boundsR.y, boundsR.width, boundsR.height );

				// generic case - add selection indicator
				resultV |= m_ItemList[i]->GenericDrawItem( this, &dc, &boundsR, m_BUseUnicode, m_BVisibleSelection );
				if (m_BVisibleSelection && (i == m_ItemSelected))
					wxColumnHeaderItem::GenericDrawSelection(
						&dc, &boundsR,
						&m_SelectionColour, m_SelectionDrawStyle );

				// NB: for wxMSW, existing clips must be destroyed before changing the clipping geometry;
				// on wxMac (and perhaps other platforms) this limitation doesn't apply.
				dc.DestroyClippingRegion();
			}
		}
	}

#if defined(__WXMSW__)
	if (! m_BUseGenericRenderer)
	{
		// render native control window
		wxWindowMSW::MSWDefWindowProc( WM_PAINT, 0, 0 );

		{
		// NB: the DC has to be a wxClientDC instead of a wxPaintDC - why?
		wxClientDC			dc( this );
		wxColumnHeaderItem	*itemRef;

			// if specified, render any button arrows
			for (i=0; i<m_ItemCount; i++)
			{
				if ((i < m_ItemViewBaseIndex) || !GetItemVisibility( i ))
					continue;

				itemRef = GetItemRef( i );
				if ((itemRef != NULL) && (itemRef->m_ButtonArrowStyle != CH_ARROWBUTTONSTYLE_None))
					if (GetItemBounds( i, &boundsR ))
						itemRef->DrawButtonArrow( &dc, &boundsR );
			}

			// wxMSW case - add selection indicator - no appropriate native adornment exists
			// rendering selection after all items are drawn allows for selection to be rendered
			// on top of (parts of) neighboring items
			if (m_BVisibleSelection && (m_ItemSelected >= 0))
				if ((m_ItemSelected >= m_ItemViewBaseIndex) && GetItemBounds( m_ItemSelected, &boundsR ))
				{
					dc.SetClippingRegion( boundsR.x, boundsR.y, boundsR.width, boundsR.height );

					wxColumnHeaderItem::GenericDrawSelection(
						&dc, &boundsR,
						&m_SelectionColour, m_SelectionDrawStyle );

					dc.DestroyClippingRegion();
				}
		}
	}

#elif defined(__WXMAC__)
	if (! m_BUseGenericRenderer)
	{
	wxPaintDC	dc( this );

		// NB: various experiments in graphics state prophylaxis
		// most don't appear to be necessary, but may be needed in the future;
		// however, the SetFont is required

		dc.SetTextForeground( *wxBLACK );
		dc.SetFont( m_Font );
		dc.MacInstallFont();

		// dc.SetLogicalFunction( wxCOPY );
		// dc.SetBrush( wxBrush(*wxBLACK, wxSOLID) );
		// dc.SetPen( wxPen(*wxBLACK, 1, wxSOLID) );

		dc.DestroyClippingRegion();

		for (i=0; i<m_ItemCount; i++)
		{
			if ((i < m_ItemViewBaseIndex) || !GetItemVisibility( i ))
				continue;

			if (GetItemBounds( i, &boundsR ))
			{
				dc.SetClippingRegion( boundsR.x, boundsR.y, boundsR.width, boundsR.height );

				// wxMac case - selection indicator is drawn as needed
				resultV |= m_ItemList[i]->MacDrawItem( this, &dc, &boundsR, m_BUseUnicode, m_BVisibleSelection );

				// NB: for wxMSW, existing clips must be destroyed before changing the clipping geometry;
				// on wxMac (and perhaps other platforms) this limitation doesn't apply, but it's used here
				// with the tenuous justification of "balance" with the wxMSW and generic versions.
				dc.DestroyClippingRegion();
			}
//			else
//				wxLogDebug( wxT("wxColumnHeader::Draw - GetItemBounds failed") );
		}
	}
#endif

	return resultV;
}

void wxColumnHeader::SetViewDirty( void )
{
	Refresh( false, NULL );
}

void wxColumnHeader::RefreshItem(
	long				itemIndex,
	bool				bForceRedraw )
{
	if (!ItemInView( itemIndex ))
		return;

#if defined(__WXMSW__)
	if (! m_BUseGenericRenderer)
	{
		// NB: need to update native item
		MSWItemRefresh( itemIndex, false );

		return;
	}
#endif

wxRect	wxClientR;
wxSize	itemExtent;

	// NB: may need to set graphics context in some cases!
	// NB: is Freeze-Thaw needed only for wxMac?

#if defined(__WXMAC__)
	if (bForceRedraw)
		Freeze();
#endif

	wxClientR = GetClientRect();
	itemExtent = GetUIExtent( itemIndex );
	wxClientR.x = itemExtent.x;
	wxClientR.width = itemExtent.y;
	Refresh( false, &wxClientR );

#if defined(__WXMAC__)
	if (bForceRedraw)
		Thaw();
#endif
}

void wxColumnHeader::RecalculateItemExtents( void )
{
long		originX, baseOriginX, i;
bool		bIsVertical;

	if (m_ItemList != NULL)
	{
		originX = 0;
		baseOriginX = m_ItemViewBaseOrigin;
		bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );

		for (i=0; i<m_ItemCount; i++)
			if (m_ItemList[i] != NULL)
			{
				m_ItemList[i]->m_Origin.x = originX - baseOriginX;
				if (! bIsVertical)
					originX += m_ItemList[i]->m_Extent.x;
			}
	}
}

wxSize wxColumnHeader::GetLabelTextExtent(
	wxDC				*dc,
	const wxString		&targetStr )
{
wxSize		resultV;

	resultV.x = resultV.y = 0;

	if (targetStr.IsEmpty())
		return resultV;

#if defined(__WXMAC__)
wxMacCFStringHolder	cfString( targetStr, m_Font.GetEncoding() );
Point				xyPt;
SInt16				baselineV;

	xyPt.h = xyPt.v = 0;

	GetThemeTextDimensions(
		(CFStringRef)cfString,
		m_Font.MacGetThemeFontID(),
		kThemeStateActive,
		false,
		&xyPt,
		&baselineV );

	resultV.x = (wxCoord)(xyPt.h);
	resultV.y = (wxCoord)(xyPt.v);

#else
wxCoord		targetWidth, targetHeight;

	if (dc != NULL)
	{
		dc->SetFont( m_Font );
		dc->GetTextExtent(
			targetStr,
			&targetWidth, &targetHeight,
			NULL, NULL, NULL );

		resultV.x = (wxCoord)targetWidth;
		resultV.y = (wxCoord)targetHeight;
	}
#endif

	return resultV;
}

// ================
#if 0
#pragma mark -
#endif

#if defined(__WXMAC__)
// virtual
void wxColumnHeader::MacControlUserPaneActivateProc(
	bool			bActivating )
{
	// FIXME: is this the right way to handle activate events ???
	Enable( bActivating );
}
#endif

#if defined(__WXMSW__)
// virtual
WXDWORD wxColumnHeader::MSWGetStyle(
	long			style,
	WXDWORD			*exstyle ) const
{
WXDWORD		msStyle;
bool			bIsVertical;

	style = (style & ~wxBORDER_MASK) | wxBORDER_NONE;

	msStyle = wxControl::MSWGetStyle( style, exstyle );

	// NB: no HDS_DRAGDROP, HDS_FILTERBAR, HDS_FULLDRAG, HDS_HOTTRACK
	msStyle |= HDS_BUTTONS | HDS_FLAT;

	// FIXME: is WS_CLIPSIBLINGS necessary ???
	msStyle |= WS_CLIPSIBLINGS;

	// if specified, set horizontal orientation flag
	bIsVertical = GetAttribute( CH_ATTR_VerticalOrientation );
	if (! bIsVertical)
		msStyle |= HDS_HORZ;

	return msStyle;
}

long wxColumnHeader::MSWItemInsert(
	long			iInsertAfter,
	long			nWidth,
	const void		*titleText,
	long			textJust,
	bool			WXUNUSED(bUseUnicode),
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
		// wxLogDebug( wxT("MSWItemInsert - GetHwnd failed (NULL)") );
		return (-1L);
	}

//	wxLogDebug( wxT("MSWItemInsert - item text [%s]"), (const TCHAR*)titleText );

	// FIXME: the first item lines up short, so hack-fix it
	if (iInsertAfter <= 0)
		nWidth += 2;

	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_TEXT | HDI_FORMAT | HDI_WIDTH;
	itemData.pszText = (LPTSTR)titleText;
	itemData.cxy = (int)nWidth;
	itemData.cchTextMax = 256;
//	itemData.cchTextMax = sizeof(itemData.pszText) / sizeof(itemData.pszText[0]);
	itemData.fmt = wxColumnHeaderItem::ConvertJustification( textJust, true ) | HDF_STRING;
	if (bSelected && bSortEnabled)
		itemData.fmt |= (bSortAscending ? HDF_SORTUP : HDF_SORTDOWN);

	// NB: wxUSE_UNICODE, _UNICODE, itemRef->m_BTextUnicode must agree or SendMessage must be used
	resultV = (long)Header_InsertItem( targetViewRef, (int)iInsertAfter, &itemData );
//	resultV = (long)SendMessage( mViewRef, bUseUnicode ? HDM_INSERTITEMW : HDM_INSERTITEMA, (WPARAM)iInsertAfter, (LPARAM)&itemData );

	if (resultV < 0)
		wxLogDebug( wxT("MSWItemInsert - SendMessage failed") );

	return resultV;
}

long wxColumnHeader::MSWItemDelete(
	long			itemIndex )
{
HWND		targetViewRef;
long		resultV;

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		// wxLogDebug( wxT("MSWItemDelete - GetHwnd failed (NULL)") );
		return (-1L);
	}

	resultV = (long)Header_DeleteItem( targetViewRef, itemIndex );

	if (resultV == 0)
		wxLogDebug( wxT("MSWItemDelete - SendMessage failed") );

	return resultV;
}

long wxColumnHeader::MSWItemRefresh(
	long			itemIndex,
	bool			bCheckChanged )
{
wxColumnHeaderItem		*itemRef;
HDITEM					itemData;
HWND					targetViewRef;
LONG					newFmt;
long					resultV, nWidth;
BOOL					bHasButtonArrow;

	itemRef = GetItemRef( itemIndex );
	if (itemRef == NULL)
		return (-1L);

	targetViewRef = GetHwnd();
	if (targetViewRef == NULL)
	{
		//wxLogDebug( wxT("MSWItemRefresh - GetHwnd failed (NULL)") );
		return (-1L);
	}

	// FIXME: the first item lines up short, so hack-fix it
	nWidth = itemRef->m_Extent.x;
	if (itemIndex <= 0)
		nWidth += 2;

	// FIXME: protect against HBMP leaks?
	ZeroMemory( &itemData, sizeof(itemData) );
	itemData.mask = HDI_FORMAT | HDI_WIDTH;
	resultV = (long)Header_GetItem( targetViewRef, itemIndex, &itemData );

	itemData.mask = HDI_TEXT | HDI_FORMAT | HDI_WIDTH;
	itemData.pszText = NULL;
	itemData.cxy = (int)nWidth;
	itemData.cchTextMax = 256;
//	itemData.cchTextMax = sizeof(itemData.pszText) / sizeof(itemData.pszText[0]);

	bHasButtonArrow = (itemRef->m_ButtonArrowStyle != CH_ARROWBUTTONSTYLE_None);

	// NB: should sort arrows and bitmaps be MutEx?
	newFmt = wxColumnHeaderItem::ConvertJustification( itemRef->m_BitmapJust, true );
	if (! bHasButtonArrow)
	{
		if (itemRef->ValidBitmapRef( itemRef->m_BitmapRef ))
		{
			// add bitmap reference
			newFmt |= HDF_BITMAP;
			itemData.mask |= HDI_BITMAP;
			itemData.hbm = (HBITMAP)(itemRef->m_BitmapRef->GetHBITMAP());
		}
		else
		{
			newFmt = wxColumnHeaderItem::ConvertJustification( itemRef->m_TextJust, true );

			// add string reference
			newFmt |= HDF_STRING;
			itemData.pszText = (LPTSTR)(itemRef->m_LabelTextRef.c_str());
		}

		// add sort arrows as needed
		if (itemRef->m_BSelected && itemRef->m_BEnabled && itemRef->m_BSortEnabled)
			newFmt |= (itemRef->m_BSortAscending ? HDF_SORTUP : HDF_SORTDOWN);
	}

	if (! bCheckChanged || (itemData.fmt != newFmt))
	{
		// NB: wxUSE_UNICODE, _UNICODE, itemRef->m_BTextUnicode must agree or SendMessage must be used
		itemData.fmt = newFmt;
		resultV = (long)Header_SetItem( targetViewRef, itemIndex, &itemData );
//		resultV = (long)SendMessage( mViewRef, itemRef->m_BTextUnicode ? HDM_SETITEMW : HDM_SETITEMA, (WPARAM)itemIndex, (LPARAM)&itemData );
	}
	else
		resultV = 1;

	if (resultV == 0)
		wxLogDebug( wxT("MSWItemRefresh - SendMessage failed") );

	return resultV;
}
#endif

// ================
#if 0
#pragma mark -
#endif

void wxColumnHeader::GenerateSelfEvent(
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
	m_TextJust( 0 )
	, m_BitmapRef( NULL )
	, m_BitmapJust( 0 )
	, m_ButtonArrowStyle( 0 )
	, m_Origin( 0, 0 )
	, m_Extent( 0, 0 )
	, m_BVisible( true )
	, m_BEnabled( false )
	, m_BSelected( false )
	, m_BSortEnabled( false )
	, m_BSortAscending( false )
	, m_BFixedWidth( false )
{
	InvalidateTextExtent();
}

wxColumnHeaderItem::wxColumnHeaderItem(
	const wxColumnHeaderItem		*info )
	:
	m_TextJust( 0 )
	, m_BitmapRef( NULL )
	, m_BitmapJust( 0 )
	, m_ButtonArrowStyle( 0 )
	, m_Origin( 0, 0 )
	, m_Extent( 0, 0 )
	, m_BVisible( true )
	, m_BEnabled( false )
	, m_BSelected( false )
	, m_BSortEnabled( false )
	, m_BSortAscending( false )
	, m_BFixedWidth( false )
{
	InvalidateTextExtent();
	SetItemData( info );
}

wxColumnHeaderItem::~wxColumnHeaderItem()
{
	delete m_BitmapRef;
}

// NB: a copy and nothing else...
//
void wxColumnHeaderItem::GetItemData(
	wxColumnHeaderItem			*info ) const
{
	if (info == NULL)
		return;

	info->m_TextJust = m_TextJust;
	info->m_LabelTextExtent = m_LabelTextExtent;
	info->m_LabelTextVisibleCharCount = m_LabelTextVisibleCharCount;
	info->m_ButtonArrowStyle = m_ButtonArrowStyle;
	info->m_Origin = m_Origin;
	info->m_Extent = m_Extent;
	info->m_BVisible = m_BVisible;
	info->m_BEnabled = m_BEnabled;
	info->m_BSelected = m_BSelected;
	info->m_BSortEnabled = m_BSortEnabled;
	info->m_BSortAscending = m_BSortAscending;
	info->m_BFixedWidth = m_BFixedWidth;

	GetLabelText( info->m_LabelTextRef );

	info->m_BitmapJust = m_BitmapJust;
	if (info->m_BitmapRef != m_BitmapRef)
		if (info->m_BitmapRef != NULL)
			GetBitmapRef( *(info->m_BitmapRef) );
}

void wxColumnHeaderItem::SetItemData(
	const wxColumnHeaderItem		*info )
{
	if (info == NULL)
		return;

	m_TextJust = info->m_TextJust;
	m_LabelTextExtent = info->m_LabelTextExtent;
	m_LabelTextVisibleCharCount = info->m_LabelTextVisibleCharCount;
	m_ButtonArrowStyle = info->m_ButtonArrowStyle;
	m_Origin = info->m_Origin;
	m_Extent = info->m_Extent;
	m_BVisible = info->m_BVisible;
	m_BEnabled = info->m_BEnabled;
	m_BSelected = info->m_BSelected;
	m_BSortEnabled = info->m_BSortEnabled;
	m_BSortAscending = info->m_BSortAscending;
	m_BFixedWidth = info->m_BFixedWidth;

	SetLabelText( info->m_LabelTextRef );

	m_BitmapJust = info->m_BitmapJust;
	if (info->m_BitmapRef != m_BitmapRef)
		SetBitmapRef( *(info->m_BitmapRef), NULL );
}

long wxColumnHeaderItem::GetArrowButtonStyle( void ) const
{
	return m_ButtonArrowStyle;
}

void wxColumnHeaderItem::SetArrowButtonStyle(
	long				targetStyle )
{
	m_ButtonArrowStyle = targetStyle;
}

void wxColumnHeaderItem::GetBitmapRef(
	wxBitmap			&bitmapRef ) const
{
	if (m_BitmapRef != NULL)
		bitmapRef = *m_BitmapRef;
//	else
//		bitmapRef.SetOK( false );
}

void wxColumnHeaderItem::SetBitmapRef(
	wxBitmap			&bitmapRef,
	const wxRect		*boundsR )
{
wxRect			targetBoundsR;

	delete m_BitmapRef;
	m_BitmapRef = NULL;

	if ((boundsR != NULL) && ValidBitmapRef( &bitmapRef ))
	{
		GenericGetBitmapItemBounds( boundsR, m_BitmapJust, NULL, &targetBoundsR );
		if ((bitmapRef.GetWidth() > targetBoundsR.width) || (bitmapRef.GetHeight() > targetBoundsR.height))
		{
		wxBitmap		localBitmap;

			// copy from the upper left-hand corner
			targetBoundsR.x = targetBoundsR.y = 0;
			localBitmap = bitmapRef.GetSubBitmap( targetBoundsR );
			m_BitmapRef = new wxBitmap( localBitmap );
		}
		else
		{
			// copy the entire bitmap
			m_BitmapRef = new wxBitmap( bitmapRef );
		}
	}
	else
	{
		// this case is OK - can be used to clear an existing bitmap
		// wxLogDebug( wxT("wxColumnHeaderItem::SetBitmapRef failed") );
	}
}

long wxColumnHeaderItem::GetBitmapJustification( void ) const
{
	return m_BitmapJust;
}

void wxColumnHeaderItem::SetBitmapJustification(
	long				targetJust )
{
	m_BitmapJust = targetJust;
}

void wxColumnHeaderItem::GetLabelText(
	wxString			&textBuffer ) const
{
	textBuffer = m_LabelTextRef;
}

void wxColumnHeaderItem::SetLabelText(
	const wxString		&textBuffer )
{
	m_LabelTextRef = textBuffer;
	InvalidateTextExtent();
}

long wxColumnHeaderItem::GetLabelJustification( void ) const
{
	return m_TextJust;
}

void wxColumnHeaderItem::SetLabelJustification(
	long				targetJust )
{
	m_TextJust = targetJust;
}

void wxColumnHeaderItem::GetUIExtent(
	long				&originX,
	long				&extentX ) const
{
	originX = m_Origin.x;
	extentX = m_Extent.x;
}

void wxColumnHeaderItem::SetUIExtent(
	long				originX,
	long				extentX )
{
	wxUnusedVar( originX );

	// NB: not currently permitted
//	if ((originX >= 0) && (m_Origin.x != originX))
//		m_Origin.x = originX;

	ResizeToWidth( extentX );
}

void wxColumnHeaderItem::ResizeToWidth(
	long				extentX )
{
	if ((extentX >= 0) && (m_Extent.x != extentX))
	{
		m_Extent.x = extentX;
		InvalidateTextExtent();
	}
}

bool wxColumnHeaderItem::GetAttribute(
	wxColumnHeaderItemAttribute		flagEnum ) const
{
bool			bResult;

	bResult = false;

	switch (flagEnum)
	{
	case CH_ITEM_ATTR_Enabled:
		bResult = m_BEnabled;
		break;

	case CH_ITEM_ATTR_Selected:
		bResult = m_BSelected;
		break;

	case CH_ITEM_ATTR_SortEnabled:
		bResult = m_BSortEnabled;
		break;

	case CH_ITEM_ATTR_SortDirection:
		bResult = m_BSortAscending;
		break;

	case CH_ITEM_ATTR_FixedWidth:
		bResult = m_BFixedWidth;
		break;

	default:
		break;
	}

	return bResult;
}

bool wxColumnHeaderItem::SetAttribute(
	wxColumnHeaderItemAttribute	flagEnum,
	bool						bFlagValue )
{
bool			bResult;

	bResult = true;

	switch (flagEnum)
	{
	case CH_ITEM_ATTR_Enabled:
		m_BEnabled = bFlagValue;
		break;

	case CH_ITEM_ATTR_Selected:
		m_BSelected = bFlagValue;
		break;

	case CH_ITEM_ATTR_SortEnabled:
		m_BSortEnabled = bFlagValue;
		break;

	case CH_ITEM_ATTR_SortDirection:
		m_BSortAscending = bFlagValue;
		break;

	case CH_ITEM_ATTR_FixedWidth:
		m_BFixedWidth = bFlagValue;
		break;

	default:
		bResult = false;
		break;
	}

	return bResult;
}

long wxColumnHeaderItem::HitTest(
	const wxPoint		&locationPt ) const
{
long		targetX, resultV;

	targetX = locationPt.x;
	resultV = ((targetX >= m_Origin.x) && (targetX < m_Origin.x + m_Extent.x));

	return resultV;
}

#if defined(__WXMAC__)
long wxColumnHeaderItem::MacDrawItem(
	wxWindow			*parentW,
	wxDC				*dc,
	const wxRect		*boundsR,
	bool				bUseUnicode,
	bool				bVisibleSelection )
{
ThemeButtonDrawInfo		drawInfo;
Rect					qdBoundsR;
bool					bSelected, bHasButtonArrow, bHasBitmap;
OSStatus				errStatus;

	if ((boundsR == NULL) || boundsR->IsEmpty())
		return (-1L);

	errStatus = noErr;

	qdBoundsR.left = boundsR->x;
	qdBoundsR.right = qdBoundsR.left + boundsR->width;
	qdBoundsR.top = boundsR->y;
	qdBoundsR.bottom = qdBoundsR.top + boundsR->height;

	// determine selection and bitmap rendering conditions
	bSelected = m_BSelected && bVisibleSelection;
	bHasButtonArrow = (m_ButtonArrowStyle != CH_ARROWBUTTONSTYLE_None);
	bHasBitmap = ((dc != NULL) && ValidBitmapRef( m_BitmapRef ));

	if (m_BEnabled)
		drawInfo.state = (bSelected && bVisibleSelection ? kThemeStateActive: kThemeStateInactive);
	else
		drawInfo.state = (bSelected && bVisibleSelection ? kThemeStateUnavailable : kThemeStateUnavailableInactive);
//	drawInfo.state = kThemeStatePressed;

	// zero draws w/o theme background shading
	drawInfo.value = (SInt32)m_BSelected && bVisibleSelection;

	drawInfo.adornment = (m_BSortAscending ? kThemeAdornmentArrowDoubleArrow : kThemeAdornmentNone);
//	drawInfo.adornment = kThemeAdornmentNone;					// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentDefault;				// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentHeaderButtonShadowOnly;	// doesn't work - draws down arrow !!
//	drawInfo.adornment = kThemeAdornmentArrowDoubleArrow;		// doesn't work - same as "up-arrow" !!
//	drawInfo.adornment = kThemeAdornmentHeaderMenuButton;		// right-pointing arrow on left side
//	drawInfo.adornment = kThemeAdornmentHeaderButtonSortUp;
//	drawInfo.adornment = kThemeAdornmentArrowDownArrow;

	// NB: DrawThemeButton height is fixed, regardless of the boundsRect argument!
	if (! m_BSortEnabled || bHasButtonArrow)
		MacDrawThemeBackgroundNoArrows( &qdBoundsR, bSelected && m_BEnabled );
	else
		// FIXME: should have HIDrawThemeButton version for CORE_GRAPHICS build
		errStatus = DrawThemeButton( &qdBoundsR, kThemeListHeaderButton, &drawInfo, NULL, NULL, NULL, 0 );

	// as specified, render (justified) either: button arrow, bitmap or label text
	if (bHasButtonArrow)
	{
		DrawButtonArrow( dc, boundsR );
	}
	else if (bHasBitmap)
	{
	wxRect		subItemBoundsR;

		GenericGetBitmapItemBounds( boundsR, m_BitmapJust, m_BitmapRef, &subItemBoundsR );
		dc->DrawBitmap( *m_BitmapRef, subItemBoundsR.x, subItemBoundsR.y, false );
	}
	else if (! m_LabelTextRef.IsEmpty())
	{
	wxString		targetStr;
	long			startX, originX, maxExtentX;
	UInt16		nativeFontID;
	SInt16		nativeTextJust;
	bool			bIsMultiline;

		bIsMultiline = false;
		nativeTextJust = (SInt16)ConvertJustification( m_TextJust, true );

		// calculate and cache text extent
		CalculateTextExtent( dc, false );
		GetTextUIExtent( startX, originX, maxExtentX );

		qdBoundsR.left = originX;
		qdBoundsR.right = qdBoundsR.left + maxExtentX;
		qdBoundsR.top = boundsR->y + 1;
		qdBoundsR.bottom = qdBoundsR.top + boundsR->height;

		nativeFontID = dc->GetFont().MacGetThemeFontID();

		targetStr = m_LabelTextRef;
		if (m_LabelTextExtent.x > maxExtentX)
			TruncateLabelText( targetStr, m_LabelTextVisibleCharCount );

		if (bUseUnicode)
		{
		wxMacCFStringHolder	localCFSHolder( targetStr, wxFONTENCODING_UNICODE );

			errStatus =
				(OSStatus)DrawThemeTextBox(
					(CFStringRef)localCFSHolder,
					nativeFontID, drawInfo.state, bIsMultiline,
					&qdBoundsR, nativeTextJust, NULL );
		}
		else
		{
		CFStringRef			cfLabelText;

			cfLabelText =
				CFStringCreateWithCString(
					NULL, (const char*)(targetStr.c_str()),
					kCFStringEncodingMacRoman );
			if (cfLabelText != NULL)
			{
				errStatus =
					(OSStatus)DrawThemeTextBox(
						cfLabelText,
						nativeFontID, drawInfo.state, bIsMultiline,
						&qdBoundsR, nativeTextJust, NULL );

				CFRelease( cfLabelText );
			}
		}

//		if (errStatus != noErr)
//			wxLogDebug(
//				wxT("wxColumnHeaderItem::MacDraw(%s: %s) failure [%ld]"),
//				bUseUnicode ? wxT("unicode") : wxT("ascii"), targetStr.c_str(), (long)errStatus );
	}

	return (long)errStatus;
}
#endif

long wxColumnHeaderItem::GenericDrawItem(
	wxWindow			*parentW,
	wxDC				*dc,
	const wxRect		*boundsR,
	bool				bUseUnicode,
	bool				bVisibleSelection )
{
wxRect			localBoundsR, subItemBoundsR;
long			startX, originX, maxExtentX, descentY;
int			drawFlags;
bool			bSelected, bHasButtonArrow, bHasBitmap;

	wxUnusedVar( bUseUnicode );

	if ((boundsR == NULL) || boundsR->IsEmpty())
		return (-1L);

	if ((parentW == NULL) || (dc == NULL))
		return (-1L);

	// calculate actual rendering area:
	// tweak left side of left-most items
	localBoundsR = *boundsR;
	if (localBoundsR.x == 0)
	{
		localBoundsR.x++;
		localBoundsR.width--;
	}
	localBoundsR.Deflate( 0, 1 );

	// determine selection and bitmap rendering conditions
	bSelected = m_BSelected && bVisibleSelection;
	bHasButtonArrow = (m_ButtonArrowStyle != CH_ARROWBUTTONSTYLE_None);
	bHasBitmap = ((dc != NULL) && ValidBitmapRef( m_BitmapRef ));

	// draw column header background:
	// leverage native (GTK?) wxRenderer
	drawFlags = 0;
	wxRendererNative::Get().DrawHeaderButton( parentW, *dc, localBoundsR, drawFlags );

	// as specified, render (justified) either: button arrow, bitmap or label text
	if (bHasButtonArrow)
	{
		DrawButtonArrow( dc, &localBoundsR );
	}
	else if (bHasBitmap)
	{
		GenericGetBitmapItemBounds( &localBoundsR, m_BitmapJust, m_BitmapRef, &subItemBoundsR );
		dc->DrawBitmap( *m_BitmapRef, subItemBoundsR.x, subItemBoundsR.y, false );
	}
	else if (! m_LabelTextRef.IsEmpty())
	{
		// calculate and cache text extent
		CalculateTextExtent( dc, false );
		GetTextUIExtent( startX, originX, maxExtentX );

		descentY = 0;
		if ((m_LabelTextExtent.y > 0) && (m_LabelTextExtent.y < localBoundsR.height))
			descentY = ((localBoundsR.height - m_LabelTextExtent.y) / 2) - 1;

		if (m_LabelTextExtent.x <= maxExtentX)
		{
			dc->DrawText( m_LabelTextRef.c_str(), startX, localBoundsR.y + descentY );
		}
		else
		{
		wxString		truncStr;

			truncStr = m_LabelTextRef;
			TruncateLabelText( truncStr, m_LabelTextVisibleCharCount );
			dc->DrawText( truncStr.c_str(), startX, localBoundsR.y + descentY );
		}
	}

	// draw sort direction arrows (if specified)
	// NB: what if icon avail? mutually exclusive?
	if (bSelected && m_BSortEnabled && !bHasButtonArrow)
	{
		GenericGetSortArrowBounds( &localBoundsR, &subItemBoundsR );
		dc->SetPen( *wxGREY_PEN );
		dc->SetBrush( *wxGREY_BRUSH );
		GenericDrawArrow( dc, &subItemBoundsR, m_BSortAscending, true );
	}

	return 0;
}

void wxColumnHeaderItem::DrawButtonArrow(
	wxDC				*dc,
	const wxRect		*localBoundsR )
{
wxRect		subItemBoundsR;

	if ((dc == NULL) || (localBoundsR == NULL))
		return;

	GenericGetBitmapItemBounds( localBoundsR, m_BitmapJust, NULL, &subItemBoundsR );
	dc->SetPen( *wxBLACK_PEN );
	dc->SetBrush( *wxBLACK_BRUSH );
	GenericDrawArrow(
		dc, &subItemBoundsR,
		((m_ButtonArrowStyle == CH_ARROWBUTTONSTYLE_Up) || (m_ButtonArrowStyle == CH_ARROWBUTTONSTYLE_Left)),
		((m_ButtonArrowStyle == CH_ARROWBUTTONSTYLE_Up) || (m_ButtonArrowStyle == CH_ARROWBUTTONSTYLE_Down)) );
}

void wxColumnHeaderItem::CalculateTextExtent(
	wxDC				*dc,
	bool				bForceRecalc )
{
wxCoord			targetWidth, targetHeight;
long			startX, originX, maxExtentX;
long			charCount;

	if (dc == NULL)
		return;

	if (bForceRecalc || (m_LabelTextExtent.x < 0) || (m_LabelTextExtent.y < 0))
	{
		charCount = m_LabelTextRef.length();
		if (charCount > 0)
		{
			dc->GetTextExtent(
				m_LabelTextRef,
				&targetWidth, &targetHeight,
				NULL, NULL, NULL );

			m_LabelTextExtent.x = targetWidth;
			m_LabelTextExtent.y = targetHeight;
		}
		else
		{
			m_LabelTextExtent.x =
			m_LabelTextExtent.y = 0;
		}

		m_LabelTextVisibleCharCount = charCount;

		GetTextUIExtent( startX, originX, maxExtentX );
		if (m_LabelTextExtent.x > maxExtentX)
			(void)MeasureLabelText( dc, m_LabelTextRef, maxExtentX, m_LabelTextVisibleCharCount );
	}
}

long wxColumnHeaderItem::MeasureLabelText(
	wxDC				*dc,
	const wxString		&targetStr,
	long				maxWidth,
	long				&charCount )
{
wxString		truncStr, ellipsisStr;
wxCoord			targetWidth, targetHeight, ellipsisWidth;
bool			bContinue;

	if ((dc == NULL) || (maxWidth <= 0))
		return 0;

	charCount = targetStr.Length();
	if (charCount <= 0)
		return 0;

	// determine the minimum width
	ellipsisStr = wxString( GetEllipsesString() );
	dc->GetTextExtent( ellipsisStr, &ellipsisWidth, &targetHeight );
	if (ellipsisWidth > maxWidth)
	{
		charCount = 0;
		return 0;
	}

	// determine if the string can fit inside the current width
	dc->GetTextExtent( targetStr, &targetWidth, &targetHeight );

	bContinue = (targetWidth > maxWidth);
	while (bContinue)
	{
		charCount--;

		if (charCount > 0)
		{
			truncStr = targetStr.Left( charCount );
			dc->GetTextExtent( truncStr, &targetWidth, &targetHeight );
			bContinue = (targetWidth + ellipsisWidth > maxWidth);
		}
		else
		{
			targetWidth = ellipsisWidth;
			bContinue = false;
		}
	}

	return (long)targetWidth;
}

// NB: horizontal item layout is one of the following:
// || InsetX || label text or bitmap || InsetX ||
// || InsetX || label text or bitmap || InsetX || sort arrow || InsetX ||
//
void wxColumnHeaderItem::GetTextUIExtent(
	long				&startX,
	long				&originX,
	long				&extentX ) const
{
long		leftDeltaX, leftInsetX, rightInsetX;
long		insetX;

	insetX = wxCH_kMetricInsetX;
	if (m_TextJust == CH_JUST_Center)
		insetX /= 2;

	rightInsetX =
		(m_BSortEnabled
		? (2 * insetX) + wxCH_kMetricArrowSizeX
		: insetX);

	switch (m_TextJust)
	{
	case CH_JUST_Center:
		leftInsetX = rightInsetX;
		break;

	case CH_JUST_Right:
	case CH_JUST_Left:
	default:
		leftInsetX = insetX;
		break;
	}

	originX = m_Origin.x + leftInsetX;
	if (originX > m_Origin.x + m_Extent.x)
		originX = m_Origin.x + m_Extent.x;

	extentX = m_Extent.x - (leftInsetX + rightInsetX);
	if (extentX < 0)
		extentX = 0;

	// determine left side text origin
	leftDeltaX = 0;
	switch (m_TextJust)
	{
	case CH_JUST_Right:
	case CH_JUST_Center:
		if ((m_LabelTextExtent.x >= 0) && (m_LabelTextExtent.x < extentX))
		{
			leftDeltaX = extentX - m_LabelTextExtent.x;
			if (m_TextJust == CH_JUST_Center)
				leftDeltaX /= 2;
		}
		break;

	case CH_JUST_Left:
	default:
		break;
	}

	startX = originX;
	if (leftDeltaX > 0)
		startX += leftDeltaX;
}

void wxColumnHeaderItem::TruncateLabelText(
	wxString			&targetStr,
	long				cutoffCharCount )
{
wxString		truncStr;

	if ((cutoffCharCount > 0) && (cutoffCharCount <= (long)(targetStr.length())))
	{
		truncStr = targetStr.Left( cutoffCharCount );
		targetStr = truncStr + wxString( GetEllipsesString() );
	}
	else
	{
		targetStr = wxString( GetEllipsesString() );
	}
}

void wxColumnHeaderItem::InvalidateTextExtent( void )
{
	m_LabelTextExtent.x =
	m_LabelTextExtent.y = (-1);

	m_LabelTextVisibleCharCount = (-1);
}

// ================
#if 0
#pragma mark -
#endif

#if defined(__WXMAC__)
// static
void wxColumnHeaderItem::MacDrawThemeBackgroundNoArrows(
	const void				*boundsR,
	bool					bSelected )
{
ThemeButtonDrawInfo	drawInfo;
Rect				qdBoundsR;
RgnHandle			savedClipRgn;
OSStatus			errStatus;

	if ((boundsR == NULL) || EmptyRect( (const Rect*)boundsR ))
		return;

	qdBoundsR = *(const Rect*)boundsR;

	// NB: zero draws w/o theme background shading
	drawInfo.value = (SInt32)bSelected;
	drawInfo.state = (bSelected ? kThemeStateActive: kThemeStateInactive);
	drawInfo.adornment = kThemeAdornmentNone;

	// clip down to the item bounds
	savedClipRgn = NewRgn();
	GetClip( savedClipRgn );
	ClipRect( &qdBoundsR );

	// FIXME: should have HIDrawThemeButton version for CORE_GRAPHICS build

	// first, render the entire area normally: fill, border and arrows
	errStatus = DrawThemeButton( &qdBoundsR, kThemeListHeaderButton, &drawInfo, NULL, NULL, NULL, 0 );

	// now render fill over the arrows, but preserve the right-side one-pixel border
	qdBoundsR.right--;
	ClipRect( &qdBoundsR );
	qdBoundsR.right += 25;
	errStatus = DrawThemeButton( &qdBoundsR, kThemeListHeaderButton, &drawInfo, NULL, NULL, NULL, 0 );

	// restore the clip region
	SetClip( savedClipRgn );
	DisposeRgn( savedClipRgn );
}
#endif

// static
void wxColumnHeaderItem::GenericDrawSelection(
	wxDC					*dc,
	const wxRect			*boundsR,
	const wxColour			*targetColour,
	long					drawStyle )
{
wxPen			targetPen( *wxLIGHT_GREY, 1, wxSOLID );
wxRect		localBoundsR;
long			borderWidth, offsetY;

	if ((dc == NULL) || (boundsR == NULL))
		return;

	if (targetColour != NULL)
		targetPen.SetColour( *targetColour );

#if 0
	wxLogDebug(
		wxT("GenericDrawSelection: [%ld, %ld, %ld, %ld]"),
		boundsR->x, boundsR->y, boundsR->width, boundsR->height );
#endif

	localBoundsR = *boundsR;

	switch (drawStyle)
	{
	case CH_SELECTIONDRAWSTYLE_None:
	case CH_SELECTIONDRAWSTYLE_Native:
	case CH_SELECTIONDRAWSTYLE_BoldLabel:
		// performed elsewheres or not at all
		break;

	case CH_SELECTIONDRAWSTYLE_ColourLabel:
	case CH_SELECTIONDRAWSTYLE_Grey:
	case CH_SELECTIONDRAWSTYLE_InvertBevel:
	case CH_SELECTIONDRAWSTYLE_Bullet:
		// NB: not yet implemented
		break;

	case CH_SELECTIONDRAWSTYLE_Frame:
		// frame border style
		borderWidth = 2;
		targetPen.SetWidth( borderWidth );
		dc->SetPen( targetPen );
		dc->SetBrush( *wxTRANSPARENT_BRUSH );

		localBoundsR.Deflate( 1, 1 );
		dc->DrawRectangle(
			localBoundsR.x,
			localBoundsR.y,
			localBoundsR.width,
			localBoundsR.height );
		break;

	case CH_SELECTIONDRAWSTYLE_Underline:
	case CH_SELECTIONDRAWSTYLE_Overline:
	default:
		// underline style - similar to MSW rollover drawing
		// overline style - similar to MSW tab highlighting
		borderWidth = 3;
		targetPen.SetWidth( borderWidth );
		dc->SetPen( targetPen );

		offsetY = 1;
		if (drawStyle == CH_SELECTIONDRAWSTYLE_Underline)
			offsetY += localBoundsR.height - borderWidth;

		borderWidth = 1;
		dc->DrawLine(
			localBoundsR.x,
			localBoundsR.y + offsetY,
			localBoundsR.x + localBoundsR.width - borderWidth,
			localBoundsR.y + offsetY );
		break;
	}
}

// static
void wxColumnHeaderItem::GenericGetSortArrowBounds(
	const wxRect			*itemBoundsR,
	wxRect					*targetBoundsR )
{
int		sizeX, sizeY, insetX;

	if (targetBoundsR == NULL)
		return;

	if (itemBoundsR != NULL)
	{
		sizeX = wxCH_kMetricArrowSizeX;
		sizeY = wxCH_kMetricArrowSizeY;
		insetX = wxCH_kMetricInsetX;

		targetBoundsR->x = itemBoundsR->x + itemBoundsR->width - (sizeX + insetX);
		targetBoundsR->y = itemBoundsR->y + ((itemBoundsR->height - sizeY) / 2);
		targetBoundsR->width = sizeX;
		targetBoundsR->height = sizeY;

		// FIXME: why is this needed? The previous calculations should be exact.
		targetBoundsR->x--;
		targetBoundsR->y--;
	}
	else
	{
		targetBoundsR->x =
		targetBoundsR->y =
		targetBoundsR->width =
		targetBoundsR->height = 0;
	}
}

// static
void wxColumnHeaderItem::GenericDrawArrow(
	wxDC					*dc,
	const wxRect			*boundsR,
	bool					bIsAscending,
	bool					bIsVertical )
{
wxPoint		triPt[3];

	if ((dc == NULL) || (boundsR == NULL))
		return;

	if (bIsVertical)
	{
		if (bIsAscending)
		{
			triPt[0].x = boundsR->width / 2;
			triPt[0].y = 0;
			triPt[1].x = boundsR->width;
			triPt[1].y = boundsR->height;
			triPt[2].x = 0;
			triPt[2].y = boundsR->height;
		}
		else
		{
			triPt[0].x = 0;
			triPt[0].y = 0;
			triPt[1].x = boundsR->width;
			triPt[1].y = 0;
			triPt[2].x = boundsR->width / 2;
			triPt[2].y = boundsR->height;
		}
	}
	else
	{
		if (bIsAscending)
		{
			triPt[0].x = 0;
			triPt[0].y = boundsR->height / 2;
			triPt[1].x = boundsR->width;
			triPt[1].y = boundsR->height;
			triPt[2].x = boundsR->width;
			triPt[2].y = 0;
		}
		else
		{
			triPt[0].x = 0;
			triPt[0].y = 0;
			triPt[1].x = boundsR->width;
			triPt[1].y = boundsR->height / 2;
			triPt[2].x = 0;
			triPt[2].y = boundsR->height;
		}
	}

	dc->DrawPolygon( 3, triPt, boundsR->x, boundsR->y );
}

// static
void wxColumnHeaderItem::GenericGetBitmapItemBounds(
	const wxRect			*itemBoundsR,
	long					targetJustification,
	const wxBitmap			*targetBitmap,
	wxRect					*targetBoundsR )
{
int		sizeX, sizeY, insetX;

	if (targetBoundsR == NULL)
		return;

	if (itemBoundsR != NULL)
	{
		sizeX = wxCH_kMetricBitmapSizeX;
		sizeY = wxCH_kMetricBitmapSizeY;
		insetX = wxCH_kMetricInsetX;

		targetBoundsR->x = itemBoundsR->x;
		targetBoundsR->y = (itemBoundsR->height - sizeY) / 2;
//		targetBoundsR->y = itemBoundsR->y + (itemBoundsR->height - sizeY) / 2;
		targetBoundsR->width = sizeX;
		targetBoundsR->height = sizeY;

		switch (targetJustification)
		{
		case CH_JUST_Right:
			targetBoundsR->x += (itemBoundsR->width - sizeX) - insetX;
			break;

		case CH_JUST_Center:
			targetBoundsR->x += (itemBoundsR->width - sizeX) / 2;
			break;

		case CH_JUST_Left:
		default:
			targetBoundsR->x += insetX;
			break;
		}

		// if a bitmap was specified and it's smaller than the default bounds,
		// then center and shrink to fit
		if (targetBitmap != NULL)
		{
		long		deltaV;

			deltaV = targetBoundsR->width - targetBitmap->GetWidth();
			if (deltaV > 0)
			{
				targetBoundsR->width -= deltaV;
				targetBoundsR->x += deltaV / 2;
			}

			deltaV = targetBoundsR->height - targetBitmap->GetHeight();
			if (deltaV > 0)
			{
				targetBoundsR->height -= deltaV;
				targetBoundsR->y += deltaV / 2;
			}
		}
	}
	else
	{
		targetBoundsR->x =
		targetBoundsR->y =
		targetBoundsR->width =
		targetBoundsR->height = 0;
	}
}

// static
bool wxColumnHeaderItem::ValidBitmapRef(
	const wxBitmap		*bitmapRef )
{
bool		bResultV;

	bResultV = ((bitmapRef != NULL) && bitmapRef->Ok());

	return bResultV;
}

// static
wxChar * wxColumnHeaderItem::GetEllipsesString( void )
{
	return wxT("...");
}

// static
long wxColumnHeaderItem::ConvertJustification(
	long			sourceEnum,
	bool			bToNative )
{
typedef struct { long valA; long valB; } AnonLongPair;
static AnonLongPair	sMap[] =
{
#if defined(__WXMSW__)
	{ CH_JUST_Left, HDF_LEFT }
	, { CH_JUST_Center, HDF_CENTER }
	, { CH_JUST_Right, HDF_RIGHT }
#elif defined(__WXMAC__)
	{ CH_JUST_Left, teJustLeft }
	, { CH_JUST_Center, teJustCenter }
	, { CH_JUST_Right, teJustRight }
#else
	// FIXME: generic - wild guess - irrelevant
	{ CH_JUST_Left, 0 }
	, { CH_JUST_Center, 1 }
	, { CH_JUST_Right, 2 }
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

