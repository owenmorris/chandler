__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.gizmos import *

from RepositoryTreeCtrl import RepositoryTreeCtrl
from RepositoryValueWindow import RepositoryValueWindow


class TwoColumnTreeCtrlPanel(wxSplitterScrolledWindow):
    def __init__(self, parent):
        wxSplitterScrolledWindow.__init__(self, parent, -1, 
                                      style=wxSP_3DBORDER|\
                                          wxCLIP_CHILDREN|\
                                          wxVSCROLL)

        self.splitter = wxThinSplitterWindow(self, -1, 
                                        style=wxSP_3DBORDER|wxCLIP_CHILDREN)
        self.treeCtrl = RepositoryTreeCtrl(self.splitter, -1,
                                           style=wxTR_NO_LINES|\
                                           wxNO_BORDER|\
                                           wxTR_HAS_BUTTONS)
        self.valueWindow = RepositoryValueWindow(self.splitter, -1, 
                                                 style=wxNO_BORDER)
        self.splitter.SplitVertically(self.treeCtrl, self.valueWindow, 300)

        self.SetTargetWindow(self.treeCtrl)
        self.EnableScrolling(FALSE, FALSE)
        self.valueWindow.SetTreeCtrl(self.treeCtrl)
        self.treeCtrl.SetCompanionWindow(self.valueWindow)

        EVT_SIZE(self, self.OnSize)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        size = wxSize(w-15, h)
        self.splitter.SetSize(size)

    def AddNewRoot(self, text):
        rootId = self.treeCtrl.AddRoot(text)
        self.treeCtrl.SetPyData(rootId, "")
        return rootId
        
    def AddNewItem(self, parent, treeText, valueText):
        itemId = self.treeCtrl.AppendItem(parent, treeText)
        self.treeCtrl.SetPyData(itemId, valueText)
        return itemId
