#!bin/env python

"""The SideBar contains navigation elements for Chandler.  It is a tabbed
display of the available views."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from wxPython.xrc import *

from NavPanel import NavPanel

DEFAULT_SIDEBAR_WIDTH = 160

class SideBar(wxNotebook):
    def __init__(self, parent, mainFrame, id = -1, 
                 size = (DEFAULT_SIDEBAR_WIDTH, -1), style=wxNB_BOTTOM):
        """Sets up the sidebar, which basically just consists of creating a
        notebook and adding a NavPanel into the first tab.  We may or may not
        want to keep the notebook, but if not, it is very easy to remove."""
        wxNotebook.__init__(self, parent, id, size = size, style = style)
        
        self.parent = parent
        self.navPanel = NavPanel(self, mainFrame)
        self.AddPage(self.navPanel, "Main")
               
        pan2 = wxPanel(self, -1)
        self.AddPage(pan2, "Other")
        
    def PopulateSideBar(self, components):
        """This initially populates the tree control of the sidebar by 
        querying each of the components as to what it should display."""
        self.navPanel.PopulateTree(components)