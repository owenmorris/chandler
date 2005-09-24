/////////////////////////////////////////////////////////////////////////////
// Name:        xh_tree.h
// Purpose:     XML resource handler for wxTreeCtrl
// Author:      Brian Gavin
// Created:     2000/09/09
// RCS-ID:      $Id: xh_tree.h,v 1.6 2005/09/23 12:51:16 MR Exp $
// Copyright:   (c) 2000 Brian Gavin
// Licence:     wxWindows licence
/////////////////////////////////////////////////////////////////////////////

#ifndef _WX_XH_TREE_H_
#define _WX_XH_TREE_H_

#include "wx/xrc/xmlres.h"

class WXDLLIMPEXP_XRC wxTreeCtrlXmlHandler : public wxXmlResourceHandler
{
DECLARE_DYNAMIC_CLASS(wxTreeCtrlXmlHandler)
public:
    wxTreeCtrlXmlHandler();
    virtual wxObject *DoCreateResource();
    virtual bool CanHandle(wxXmlNode *node);
};


#endif // _WX_XH_TREE_H_
