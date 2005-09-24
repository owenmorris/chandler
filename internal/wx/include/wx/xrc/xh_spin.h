/////////////////////////////////////////////////////////////////////////////
// Name:        xh_spin.h
// Purpose:     XML resource handler for wxSpinButton
// Author:      Bob Mitchell
// Created:     2000/03/21
// RCS-ID:      $Id: xh_spin.h,v 1.7 2005/09/23 12:51:15 MR Exp $
// Copyright:   (c) 2000 Bob Mitchell and Verant Interactive
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_XH_SPIN_H_
#define _WX_XH_SPIN_H_

#include "wx/xrc/xmlres.h"
#include "wx/defs.h"

#if wxUSE_SPINBTN
class WXDLLIMPEXP_XRC wxSpinButtonXmlHandler : public wxXmlResourceHandler
{
    DECLARE_DYNAMIC_CLASS(wxSpinButtonXmlHandler)
    enum
    {
        wxSP_DEFAULT_VALUE = 0,
        wxSP_DEFAULT_MIN = 0,
        wxSP_DEFAULT_MAX = 100
    };

public:
    wxSpinButtonXmlHandler();
    virtual wxObject *DoCreateResource();
    virtual bool CanHandle(wxXmlNode *node);
};
#endif

#if wxUSE_SPINCTRL
class WXDLLIMPEXP_XRC wxSpinCtrlXmlHandler : public wxXmlResourceHandler
{
    DECLARE_DYNAMIC_CLASS(wxSpinCtrlXmlHandler)
    enum
    {
        wxSP_DEFAULT_VALUE = 0,
        wxSP_DEFAULT_MIN = 0,
        wxSP_DEFAULT_MAX = 100
    };

public:
    wxSpinCtrlXmlHandler();
    virtual wxObject *DoCreateResource();
    virtual bool CanHandle(wxXmlNode *node);
};
#endif

#endif // _WX_XH_SPIN_H_
