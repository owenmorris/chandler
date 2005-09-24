/////////////////////////////////////////////////////////////////////////////
// Name:        xh_scrol.h
// Purpose:     XML resource handler for wxScrollBar
// Author:      Brian Gavin
// Created:     2000/09/09
// RCS-ID:      $Id: xh_scrol.h,v 1.7 2005/09/23 12:51:15 MR Exp $
// Copyright:   (c) 2000 Brian Gavin
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_XH_SCROL_H_
#define _WX_XH_SCROL_H_

#include "wx/xrc/xmlres.h"
#include "wx/defs.h"



class WXDLLIMPEXP_XRC wxScrollBarXmlHandler : public wxXmlResourceHandler
{
    DECLARE_DYNAMIC_CLASS(wxScrollBarXmlHandler)
    enum
    {
        wxSL_DEFAULT_VALUE = 0,
        wxSL_DEFAULT_MIN = 0,
        wxSL_DEFAULT_MAX = 100
    };

public:
    wxScrollBarXmlHandler();
    virtual wxObject *DoCreateResource();
    virtual bool CanHandle(wxXmlNode *node);
};


#endif // _WX_XH_SCROL_H_
