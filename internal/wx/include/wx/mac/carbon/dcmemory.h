/////////////////////////////////////////////////////////////////////////////
// Name:        dcmemory.h
// Purpose:     wxMemoryDC class
// Author:      Stefan Csomor
// Modified by:
// Created:     1998-01-01
// RCS-ID:      $Id: dcmemory.h,v 1.6 2006/02/08 21:46:10 VZ Exp $
// Copyright:   (c) Stefan Csomor
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_DCMEMORY_H_
#define _WX_DCMEMORY_H_

#include "wx/dcclient.h"

class WXDLLEXPORT wxMemoryDC: public wxPaintDC
{
  DECLARE_DYNAMIC_CLASS(wxMemoryDC)

  public:
    wxMemoryDC(void);
    wxMemoryDC( wxDC *dc ); // Create compatible DC
    ~wxMemoryDC(void);
    virtual void SelectObject( const wxBitmap& bitmap );
        wxBitmap    GetSelectedObject() { return m_selected ; }

protected:
    virtual void DoGetSize( int *width, int *height ) const;

  private:
    wxBitmap  m_selected;
};

#endif
    // _WX_DCMEMORY_H_
