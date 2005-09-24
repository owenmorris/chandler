/////////////////////////////////////////////////////////////////////////////
// Name:        gdiobj.h
// Purpose:
// Author:      Robert Roebling
// Id:          $Id: gdiobj.h,v 1.11 2005/09/23 12:49:16 MR Exp $
// Copyright:   (c) 1998 Robert Roebling, Julian Smart
// Licence:   	wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef __GDIOBJH__
#define __GDIOBJH__

#include "wx/object.h"

class WXDLLIMPEXP_CORE wxGDIObject : public wxObject
{
public:
    inline wxGDIObject() { m_visible = FALSE; };
    inline ~wxGDIObject() {}

    virtual bool GetVisible() { return m_visible; }
    virtual void SetVisible( bool visible ) { m_visible = visible; }

    bool IsNull() const { return (m_refData == 0); }

protected:
    bool m_visible; /* can a pointer to this object be safely taken?
                     * - only if created within FindOrCreate... */
private:
    DECLARE_DYNAMIC_CLASS(wxGDIObject)
};

#endif
    // __GDIOBJH__
