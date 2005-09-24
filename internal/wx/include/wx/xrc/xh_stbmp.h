/////////////////////////////////////////////////////////////////////////////
// Name:        xh_stbmp.h
// Purpose:     XML resource handler for wxStaticBitmap
// Author:      Vaclav Slavik
// Created:     2000/04/22
// RCS-ID:      $Id: xh_stbmp.h,v 1.6 2005/09/23 12:51:16 MR Exp $
// Copyright:   (c) 2000 Vaclav Slavik
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_XH_STBMP_H_
#define _WX_XH_STBMP_H_

#include "wx/xrc/xmlres.h"


class WXDLLIMPEXP_XRC wxStaticBitmapXmlHandler : public wxXmlResourceHandler
{
DECLARE_DYNAMIC_CLASS(wxStaticBitmapXmlHandler)
public:
    wxStaticBitmapXmlHandler();
    virtual wxObject *DoCreateResource();
    virtual bool CanHandle(wxXmlNode *node);
};


#endif // _WX_XH_STBMP_H_
