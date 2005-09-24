/////////////////////////////////////////////////////////////////////////////
// Name:        wx/print.h
// Purpose:     Base header for printer classes
// Author:      Julian Smart
// Modified by:
// Created:
// RCS-ID:      $Id: print.h,v 1.11 2005/05/04 18:52:01 JS Exp $
// Copyright:   (c) Julian Smart
// Licence:     wxWindows Licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_PRINT_H_BASE_
#define _WX_PRINT_H_BASE_

#if defined(__WXMSW__) && !defined(__WXUNIVERSAL__)

#include "wx/msw/printwin.h"

#elif defined(__WXMAC__)

#include "wx/mac/printmac.h"

#elif defined(__WXPM__)

#include "wx/os2/printos2.h"

#else

#include "wx/generic/printps.h"

#endif


#endif
    // _WX_PRINT_H_BASE_
