/////////////////////////////////////////////////////////////////////////////
// Name:        wx/progdlg.h
// Purpose:     Base header for wxProgressDialog
// Author:      Julian Smart
// Modified by:
// Created:
// RCS-ID:      $Id: progdlg.h 6038 2005-07-18 21:58:47Z davids $
// Copyright:   (c) Julian Smart
// Licence:     wxWindows Licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_PROGDLG_H_BASE_
#define _WX_PROGDLG_H_BASE_

#include "wx/defs.h"

#ifdef __WXPALMOS__
    #include "wx/palmos/progdlg.h"
#else
    #include "wx/generic/progdlgg.h"
#endif

#endif // _WX_PROGDLG_H_BASE_
