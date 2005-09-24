/////////////////////////////////////////////////////////////////////////////
// Name:        xh_html.h
// Purpose:     XML resource handler for wxHtmlWindow
// Author:      Bob Mitchell
// Created:     2000/03/21
// RCS-ID:      $Id: xh_html.h,v 1.6 2005/09/23 12:51:13 MR Exp $
// Copyright:   (c) 2000 Bob Mitchell and Verant Interactive
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_XH_HTML_H_
#define _WX_XH_HTML_H_

#include "wx/xrc/xmlres.h"

#include "wx/defs.h"

#if wxUSE_HTML

class WXDLLIMPEXP_XRC wxHtmlWindowXmlHandler : public wxXmlResourceHandler
{
DECLARE_DYNAMIC_CLASS(wxHtmlWindowXmlHandler)
public:
    wxHtmlWindowXmlHandler();
    virtual wxObject *DoCreateResource();
    virtual bool CanHandle(wxXmlNode *node);
};

#endif

#endif // _WX_XH_SLIDER_H_
