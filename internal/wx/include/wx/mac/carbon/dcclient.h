/////////////////////////////////////////////////////////////////////////////
// Name:        dcclient.h
// Purpose:     wxClientDC, wxPaintDC and wxWindowDC classes
// Author:      Stefan Csomor
// Modified by:
// Created:     1998-01-01
// RCS-ID:      $Id: dcclient.h,v 1.6 2006/02/08 21:46:10 VZ Exp $
// Copyright:   (c) Stefan Csomor
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_DCCLIENT_H_
#define _WX_DCCLIENT_H_

#include "wx/dc.h"

//-----------------------------------------------------------------------------
// classes
//-----------------------------------------------------------------------------

class WXDLLEXPORT wxPaintDC;
class WXDLLEXPORT wxWindow;

class WXDLLEXPORT wxWindowDC: public wxDC
{
  DECLARE_DYNAMIC_CLASS(wxWindowDC)

 public:
  wxWindowDC(void);

  // Create a DC corresponding to a canvas
  wxWindowDC(wxWindow *win);

  ~wxWindowDC(void);
  protected :
    virtual void DoGetSize( int *width, int *height ) const;
    wxWindow     *m_window;
};


class WXDLLEXPORT wxClientDC: public wxWindowDC
{
  DECLARE_DYNAMIC_CLASS(wxClientDC)

 public:
  wxClientDC(void);

  // Create a DC corresponding to a canvas
  wxClientDC(wxWindow *win);

  ~wxClientDC(void);

protected:
  virtual void DoGetSize( int *width, int *height ) const;
};

class WXDLLEXPORT wxPaintDC: public wxWindowDC
{
  DECLARE_DYNAMIC_CLASS(wxPaintDC)

 public:
  wxPaintDC(void);

  // Create a DC corresponding to a canvas
  wxPaintDC(wxWindow *win);

  ~wxPaintDC(void);

protected:
  virtual void DoGetSize( int *width, int *height ) const;
};

#endif
    // _WX_DCCLIENT_H_
