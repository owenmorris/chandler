/////////////////////////////////////////////////////////////////////////////
// Name:        _gdiobj.i
// Purpose:     SWIG interface for wxGDIObject
//
// Author:      Robin Dunn
//
// Created:     13-Sept-2003
// RCS-ID:      $Id: _gdiobj.i 5166 2005-04-29 01:36:53Z davids $
// Copyright:   (c) 2003 by Total Control Software
// Licence:     wxWindows license
/////////////////////////////////////////////////////////////////////////////

// Not a %module

//---------------------------------------------------------------------------
%newgroup

MustHaveApp(wxGDIObject);

class wxGDIObject : public wxObject {
public:
    wxGDIObject();
    ~wxGDIObject();

    bool GetVisible();
    void SetVisible( bool visible );

    bool IsNull();

};

//---------------------------------------------------------------------------
