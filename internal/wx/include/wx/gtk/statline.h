/////////////////////////////////////////////////////////////////////////////
// Name:        wx/gtk/statline.h
// Purpose:
// Author:      Robert Roebling
// Id:          $Id: statline.h,v 1.13 2005/09/23 12:49:19 MR Exp $
// Copyright:   (c) 1998 Robert Roebling
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef __GTKSTATICLINEH__
#define __GTKSTATICLINEH__

#include "wx/defs.h"

#if wxUSE_STATLINE

// ----------------------------------------------------------------------------
// wxStaticLine
// ----------------------------------------------------------------------------

class WXDLLIMPEXP_CORE wxStaticLine : public wxStaticLineBase
{
public:
    wxStaticLine();
    wxStaticLine(wxWindow *parent,
                 wxWindowID id = wxID_ANY,
                 const wxPoint &pos = wxDefaultPosition,
                 const wxSize& size = wxDefaultSize,
                 long style = wxLI_HORIZONTAL,
                 const wxString &name = wxStaticTextNameStr);
    bool Create(wxWindow *parent,
                wxWindowID id = wxID_ANY,
                const wxPoint& pos = wxDefaultPosition,
                const wxSize& size = wxDefaultSize,
                long style = wxLI_HORIZONTAL,
                const wxString &name = wxStaticTextNameStr);

    static wxVisualAttributes
    GetClassDefaultAttributes(wxWindowVariant variant = wxWINDOW_VARIANT_NORMAL);


private:
    DECLARE_DYNAMIC_CLASS(wxStaticLine)
};

#endif // wxUSE_STATLINE

#endif // __GTKSTATICLINEH__

