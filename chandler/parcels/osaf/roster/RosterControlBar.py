#!bin/env python

"""
This class implements the control bar for the roster parcel
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
        
# here's the main class for the control bar		
class RosterControlBar(wxPanel):
    def __init__(self, parent, rosterViewer):
        self.rosterViewer = rosterViewer
        
        wxPanel.__init__(self, parent, -1)
                
        # load resources used by the control bar
        self.labelFont = wxFont(18, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")

        self.LayoutWidgets()
                    
    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()
        
    def GetViewTitle(self):
         return self.rosterViewer.GetViewTitle()
                    
    def LayoutWidgets(self):
        container = wxBoxSizer(wxHORIZONTAL)
        
        viewLabel = self.GetViewTitle()
        self.titleWidget = wxStaticText(self, -1, viewLabel)
        self.titleWidget.SetFont(self.labelFont)
        container.Add(self.titleWidget, 0, wxEXPAND | wxEAST | wxWEST | wxTOP, 4)
        
        self.SetSizerAndFit(container)
              
    def UpdateTitle(self):
        self.RenderWidgets()       
        
                
