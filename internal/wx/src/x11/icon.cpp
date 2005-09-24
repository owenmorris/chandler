/////////////////////////////////////////////////////////////////////////////
// Name:        icon.cpp
// Purpose:     wxIcon class
// Author:      Julian Smart
// Modified by:
// Created:     17/09/98
// RCS-ID:      $Id: icon.cpp,v 1.9 2005/09/23 12:56:05 MR Exp $
// Copyright:   (c) Julian Smart
// Licence:   	wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#include "wx/icon.h"
#include "wx/window.h"

#include "wx/x11/private.h"

//-----------------------------------------------------------------------------
// wxIcon
//-----------------------------------------------------------------------------

IMPLEMENT_DYNAMIC_CLASS(wxIcon,wxBitmap)

wxIcon::wxIcon( const char **bits, int WXUNUSED(width), int WXUNUSED(height) ) :
    wxBitmap( bits )
{
}

wxIcon::wxIcon( char **bits, int WXUNUSED(width), int WXUNUSED(height) ) :
    wxBitmap( bits )
{
}

wxIcon::wxIcon() :  wxBitmap()
{
}

wxIcon::wxIcon( const wxIcon& icon ) : wxBitmap()
{
    Ref(icon);
}

wxIcon& wxIcon::operator = ( const wxIcon& icon )
{
    if (*this == icon) return (*this);
    Ref(icon);
    return *this;
}

void wxIcon::CopyFromBitmap(const wxBitmap& bmp)
{
    wxIcon *icon = (wxIcon*)(&bmp);
    *this = *icon;
}
