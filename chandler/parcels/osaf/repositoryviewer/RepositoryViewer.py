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
from wxPython.html import *

from application.ViewerParcel import ViewerParcel
from application.ViewerParcel import wxViewerParcel

from application.Application import app
from model.util.Path import Path
import os
from application.SplashScreen import SplashScreen

class RepositoryViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__(self)

class wxRepositoryViewer(wxViewerParcel):
    def OnInit(self):
        """Initializes the repository viewer, setting up the layout
           and populating the tree ctrl.
        """
        # @@@ sizer layout should be handled in xrc, but xrc
        # does not yet support wxTreeListCtrl

        # Set up the title
        self.title = wxStaticText(self, -1, _("Repository Viewer"))
        self.title.SetFont(wxFont(18, wxSWISS, 
                                  wxNORMAL, wxNORMAL, 
                                  false, "Arial"))

        self.splitter = wxSplitterWindow(self, -1,
                                         style=wxNO_FULL_REPAINT_ON_RESIZE)

        # Set up the help page
        EVT_MENU(self, XRCID('AboutRepositoryViewer'), self.OnAboutRepositoryViewer)
        # Set up tree control
        self.treeCtrl = wxTreeListCtrl(self.splitter)
        self.treeCtrl.AddColumn(_('Item Name'))
        self.treeCtrl.AddColumn(_('Display Name'))
        self.treeCtrl.AddColumn(_('Kind'))
        self.treeCtrl.AddColumn(_('UUID'))
        self.treeCtrl.AddColumn(_('URL'))
        
        EVT_TREE_SEL_CHANGED(self, self.treeCtrl.GetId(), self.OnSelChanged)
        
        # Set up detail view
        self.detail = wxHtmlWindow(self.splitter, -1, 
                                   style=wxNO_FULL_REPAINT_ON_RESIZE | wxSUNKEN_BORDER)
        self.detail.SetPage("<html><body><h5>Item Viewer</h5></body></html>")
        self.splitter.SplitHorizontally(self.treeCtrl, self.detail, 200)

        # Set up sizer
        self.container = wxBoxSizer(wxVERTICAL)
        self.container.Add(self.title, 0, wxEXPAND)
        self.container.Add(self.splitter, 1, wxEXPAND)
        self.SetSizerAndFit(self.container)
        
        self.LoadTree()

    def OnSelChanged(self, event):
        """Display the selected Item.
        """
        itemId = event.GetItem()
        item = self.treeCtrl.GetItemData(itemId).GetData()

        if (item == "Repository"):
            self.detail.SetPage("<html><body><h5>Item Viewer</h5></body></html>")
        else:
            self.DisplayItem(item)
        
    def DisplayItem(self, item):
        """Display the given Item's details in an HTML window.
        """
        htmlString = "<html><body><h5>Item</h5><ul>"
        htmlString = htmlString + "<li><b>Path:</b> %s" % item.getItemPath()
        htmlString = htmlString + "<li><b>UUID:</b> %s" % item.getUUID()
        htmlString = htmlString + "</ul><h5>Attributes</h5><ul>"
        for attribute in item.iterAttributes():
            key = attribute[0]

            if isinstance(attribute[1], dict):
                htmlString = htmlString + ("<li><b>%s:</b></li><ul>" % key)
                for attr in attribute[1]:
                    attrString = str(attr)
                    attrString = attrString.replace("<", "&lt;")
                    attrString = attrString.replace(">", "&gt;")
                    htmlString = htmlString + ("<li>%s</li>" % attrString)
                htmlString = htmlString + ("</ul>")
            else:
                value = str(attribute[1])
                value = value.replace("<", "&lt;")
                value = value.replace(">", "&gt;")
                htmlString = htmlString + ("<li><b>%s: </b>%s</li>" % (key, value))

        htmlString = htmlString + "</ul></body></html>"
        
        self.detail.SetPage(htmlString)
        
        
    def LoadTree(self, item=None, path=None, parent=None):
        """Load the repository data into the tree.
           Recursively traverses the tree (by following the containment path), 
           creating a tree item for every repository Item.
        """

        if item is None:
            root = self.treeCtrl.AddRoot("\\\\")
            self.treeCtrl.SetItemData(root, wxTreeItemData("Repository"))
            for item in app.repository.getRoots():
                path = item.getItemPath()
                self.LoadTree(item, path, root)
            self.treeCtrl.Expand(root)
        else:
            path.append(item.getItemName())
            node = self.treeCtrl.AppendItem(parent, item.getItemName())
            self.treeCtrl.SetItemData(node, wxTreeItemData(item))
            self.LoadItem(item, node)
            for child in item:
                self.LoadTree(child, path, node)
            path.pop()

    def LoadItem(self, item, node):
        """Populates the tree's table with details of this particular item.
        """

        displayName = item.getItemDisplayName()
                
        if item.hasAttributeValue('kind'):
            kind = item.kind.getItemName()
        else:
            kind = "Kind not found"
        
        self.treeCtrl.SetItemText(node, displayName, 1)
        self.treeCtrl.SetItemText(node, kind, 2)
        self.treeCtrl.SetItemText(node, str(item.getUUID()), 3)
        self.treeCtrl.SetItemText(node, str(item.getItemPath()), 4)
        
        
    def OnAboutRepositoryViewer(self, event):
        pageLocation = self.model.path + os.sep + "AboutRepositoryViewer.html"
        infoPage = SplashScreen(self, _("About Repository Viewer"), pageLocation, 
                                False, False)
        infoPage.Show(True)

