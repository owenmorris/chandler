__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.gizmos import *        
        

class RepositoryValueWindow(wxTreeCompanionWindow):
    def __init__(self, parent, id, style):
        wxTreeCompanionWindow.__init__(self, parent, id, style=style)
        self.SetBackgroundColour("WHITE")

    # This method is called to draw each item in the value window
    def DrawItem(self, dc, itemId, rect):
        tree = self.GetTreeCtrl()
        if tree:
            text = tree.GetPyData(itemId)
            pen = wxPen(wxSystemSettings_GetSystemColour(wxSYS_COLOUR_3DLIGHT), 1, wxSOLID)
            dc.SetPen(pen)
            dc.SetBrush(wxBrush(self.GetBackgroundColour(), wxSOLID))
            dc.DrawRectangle(rect.x, rect.y, rect.width+1, rect.height+1)
            dc.SetTextForeground("BLACK")
            dc.SetBackgroundMode(wxTRANSPARENT)
            tw, th = dc.GetTextExtent(text)
            x = 5
            y = rect.y + max(0, (rect.height - th) / 2)
            dc.DrawText(text, x, y)

        