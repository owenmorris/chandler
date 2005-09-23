/////////////////////////////////////////////////////////////////////////////
// Name:        xh_cald.h
// Purpose:     XML resource handler for wxCalendarCtrl
// Author:      Brian Gavin
// Created:     2000/09/09
// RCS-ID:      $Id: xh_cald.h 5166 2005-04-29 01:36:53Z davids $
// Copyright:   (c) 2000 Brian Gavin
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_XH_CALD_H_
#define _WX_XH_CALD_H_

#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
#pragma interface "xh_cald.h"
#endif

#include "wx/xrc/xmlres.h"

class WXDLLIMPEXP_XRC wxCalendarCtrlXmlHandler : public wxXmlResourceHandler
{
DECLARE_DYNAMIC_CLASS(wxCalendarCtrlXmlHandler)
public:
    wxCalendarCtrlXmlHandler();
    virtual wxObject *DoCreateResource();
    virtual bool CanHandle(wxXmlNode *node);
};


#endif // _WX_XH_CALD_H_
