""" Repository Viewer. Creates a view of the entire repository, based
    on the containment path.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.xrc import *
from wxPython.gizmos import *

from application.ViewerParcel import ViewerParcel
from application.ViewerParcel import wxViewerParcel

from application.Application import app
from model.util.Path import Path

class RepositoryViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__(self)

class wxRepositoryViewer(wxViewerParcel):
    def OnInit(self):
        # @@@ sizer layout should be handled in xrc, but xrc
        # does not yet support wxTreeListCtrl
        
        self.treeCtrl = wxTreeListCtrl(self)
        self.treeCtrl.AddColumn('Containment Path')
        self.treeCtrl.AddColumn('Display Name')
        self.treeCtrl.AddColumn('Kind')
        self.treeCtrl.AddColumn('UUID')
        self.treeCtrl.AddColumn('URI')
        
        font = wxFont(18, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
        
        self.container = wxBoxSizer(wxVERTICAL)
        self.title = wxStaticText(self, -1, _("Repository Viewer"))
        self.title.SetFont(wxFont(18, wxSWISS, 
                                  wxNORMAL, wxNORMAL, 
                                  false, "Arial"))
        self.container.Add(self.title, 0, wxEXPAND)
        self.container.Add(self.treeCtrl, 1, wxEXPAND)
        self.SetSizerAndFit(self.container)
        
        self.LoadTree()
    
    def LoadTree(self, item=None, path=None, parent=None):

        if item is None:
            path = Path('//Schema')
            item = app.repository.find(path)
            root = self.treeCtrl.AddRoot(item.getName())
            self.LoadItem(item, root)
            self.LoadTree(item, path, root)
            self.treeCtrl.Expand(root)
        else:
            path.append(item.getName())
            node = self.treeCtrl.AppendItem(parent, item.getName())
            self.LoadItem(item, node)
            for child in item:
                self.LoadTree(child, path, node)
            path.pop()

        #for attribute in item.attributes():
        #    attributeNode = self.treeCtrl.AppendItem(node, attribute[0])
        #    self.treeCtrl.SetItemText(attributeNode, str(attribute[1]), 1)

    def LoadItem(self, item, node):
        if (item.hasAttribute('DisplayName')):
            displayName = item.DisplayName
        else:
            displayName = item.getName()
            
        if (item.hasAttribute('Kind')):
            kind = item.Kind.getName()
        else:
            kind = 'Item'
        
        self.treeCtrl.SetItemText(node, displayName, 1)
        self.treeCtrl.SetItemText(node, kind, 2)
        self.treeCtrl.SetItemText(node, str(item.getUUID()), 3)
        self.treeCtrl.SetItemText(node, '?', 4)
        
        
