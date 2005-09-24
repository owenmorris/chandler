/////////////////////////////////////////////////////////////////////////////
// Name:        generic/statline.cpp
// Purpose:     a generic wxStaticLine class
// Author:      Vadim Zeitlin
// Created:     28.06.99
// Version:     $Id: statlmac.cpp,v 1.20 2005/09/23 12:54:11 MR Exp $
// Copyright:   (c) 1998 Vadim Zeitlin
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

// ============================================================================
// declarations
// ============================================================================

// ----------------------------------------------------------------------------
// headers
// ----------------------------------------------------------------------------

// For compilers that support precompilation, includes "wx.h".
#include "wx/wxprec.h"

#if wxUSE_STATLINE

#ifdef __BORLANDC__
    #pragma hdrstop
#endif

#include "wx/statline.h"
#include "wx/statbox.h"

#include "wx/mac/uma.h"

// ============================================================================
// implementation
// ============================================================================

IMPLEMENT_DYNAMIC_CLASS(wxStaticLine, wxControl)

// ----------------------------------------------------------------------------
// wxStaticLine
// ----------------------------------------------------------------------------

bool wxStaticLine::Create( wxWindow *parent,
                           wxWindowID id,
                           const wxPoint &pos,
                           const wxSize &size,
                           long style,
                           const wxString &name)
{
    m_macIsUserPane = FALSE ;
    
    if ( !wxStaticLineBase::Create(parent, id, pos, size,
                                   style, wxDefaultValidator, name) )
        return false;

    Rect bounds = wxMacGetBoundsForControl( this , pos , size ) ;
    m_peer = new wxMacControl(this) ;
    verify_noerr(CreateSeparatorControl(MAC_WXHWND(parent->MacGetTopLevelWindowRef()),&bounds, m_peer->GetControlRefAddr() ) ) ;  

    MacPostControlCreate(pos,size) ;

    return TRUE;
}

#endif //wxUSE_STATLINE
