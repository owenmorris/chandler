/////////////////////////////////////////////////////////////////////////////
// Name:        generic/statline.cpp
// Purpose:     a generic wxStaticLine class
// Author:      Vadim Zeitlin
// Created:     28.06.99
// Version:     $Id: statline.cpp,v 1.5 2005/09/23 12:54:11 MR Exp $
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

#ifdef __BORLANDC__
    #pragma hdrstop
#endif

#include "wx/statline.h"
#include "wx/statbox.h"

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
    if ( !CreateBase(parent, id, pos, size, style, wxDefaultValidator, name) )
        return FALSE;

    // ok, this is ugly but it's better than nothing: use a thin static box to
    // emulate static line

    wxSize sizeReal = AdjustSize(size);

//    m_statbox = new wxStaticBox(parent, id, wxT(""), pos, sizeReal, style, name);

    return TRUE;
}
