#!bin/env python

"""The SideBar contains navigation elements for Chandler.  It is a tabbed
display of the available views."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"


from wxPython.wx import *
from wxPython.xrc import *

from NavPanel import NavPanel

class SideBar(wxNotebook):
    def __init__(self, parent, mainFrame, id=-1, size=(160,-1), style=wxNB_BOTTOM):
        wxNotebook.__init__(self, parent, id, size=size, style=style)
        
        self.parent = parent
        self.navPanel = NavPanel(self, mainFrame)
        self.AddPage(self.navPanel, "Main")
               
        pan2 = wxPanel(self, -1)
        self.AddPage(pan2, "Other")
        
    def PopulateSideBar(self, components):
        self.navPanel.PopulateTree(components)