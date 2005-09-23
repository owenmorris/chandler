/////////////////////////////////////////////////////////////////////////////
// Name:        wx/palmos/msgdlg.h
// Purpose:     wxMessageDialog class
// Author:      William Osborne - minimal working wxPalmOS port
// Modified by:
// Created:     10/13/04
// RCS-ID:      $Id: msgdlg.h 5179 2005-04-30 01:45:07Z davids $
// Copyright:   (c) William Osborne
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_MSGBOXDLG_H_
#define _WX_MSGBOXDLG_H_

#if defined(__GNUG__) && !defined(NO_GCC_PRAGMA)
#pragma interface "msgdlg.h"
#endif

#include "wx/setup.h"
#include "wx/dialog.h"

/*
 * Message box dialog
 */

WXDLLEXPORT_DATA(extern const wxChar*) wxMessageBoxCaptionStr;

class WXDLLEXPORT wxMessageDialog: public wxDialog, public wxMessageDialogBase
{
DECLARE_DYNAMIC_CLASS(wxMessageDialog)
protected:
    wxString    m_caption;
    wxString    m_message;
    wxWindow *  m_parent;
public:
    wxMessageDialog(wxWindow *parent, const wxString& message, const wxString& caption = wxMessageBoxCaptionStr,
        long style = wxOK|wxCENTRE, const wxPoint& pos = wxDefaultPosition);

    int ShowModal(void);

    DECLARE_NO_COPY_CLASS(wxMessageDialog)
};


#endif
    // _WX_MSGBOXDLG_H_
