/////////////////////////////////////////////////////////////////////////////
// Name:        gauge.h
// Purpose:     wxGauge class
// Author:      Stefan Csomor
// Modified by:
// Created:     1998-01-01
// RCS-ID:      $Id: gauge.h 5166 2005-04-29 01:36:53Z davids $
// Copyright:   (c) Stefan Csomor
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_GAUGE_H_
#define _WX_GAUGE_H_

#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
#pragma interface "gauge.h"
#endif

#include "wx/control.h"

WXDLLEXPORT_DATA(extern const wxChar*) wxGaugeNameStr;

// Group box
class WXDLLEXPORT wxGauge: public wxGaugeBase
{
 public:
  inline wxGauge() { }

  inline wxGauge(wxWindow *parent, wxWindowID id,
           int range,
           const wxPoint& pos = wxDefaultPosition,
           const wxSize& size = wxDefaultSize,
           long style = wxGA_HORIZONTAL,
           const wxValidator& validator = wxDefaultValidator,
           const wxString& name = wxGaugeNameStr)
  {
    Create(parent, id, range, pos, size, style, validator, name);
  }

  bool Create(wxWindow *parent, wxWindowID id,
           int range,
           const wxPoint& pos = wxDefaultPosition,
           const wxSize& size = wxDefaultSize,
           long style = wxGA_HORIZONTAL,
           const wxValidator& validator = wxDefaultValidator,
           const wxString& name = wxGaugeNameStr);

    // set gauge range/value
    virtual void SetRange(int range);
    virtual void SetValue(int pos);
    virtual int  GetValue() const ;
 protected:
    DECLARE_DYNAMIC_CLASS_NO_COPY(wxGauge)
};

#endif
    // _WX_GAUGE_H_
