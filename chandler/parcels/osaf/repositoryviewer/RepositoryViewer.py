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
from model.item.Item import Item
import os
from application.SplashScreen import SplashScreen

class RepositoryViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__(self)

class wxRepositoryViewerDetail(wxHtmlWindow):

    def OnLinkClicked(self, wx_linkinfo):
        uri = wx_linkinfo.GetHref()
        an_item = app.repository.getRoots()[0]
        item = an_item.find(uri)
        self.DisplayItem(item)

    def _formatReference(self, ref):
        """ formats the a reference attribute to be clickable, etcetera
        """
        url = ref.getItemPath()
        if ref.hasAttributeValue('kind'):
            kind = ref.kind.getItemName()
        else:
            kind = "(Kind not found)"
        # Originally I was masking the fallback to itemName here just like in
        # the listview, but that doesn't work for many of the more primitive
        # repository items, so I stopped doing that.
        dn = str(ref.getItemDisplayName())

        # Escape < and > for HTML display
        kind = kind.replace("<", "&lt;").replace(">", "&gt;")
        dn = dn.replace("<", "&lt;").replace(">", "&gt;")

        return "<a href=\"%(url)s\">%(kind)s: %(dn)s</a>" % locals()

    def DisplayItem(self, item):
        """Display the given Item's details in an HTML window.
        """
        displayName = item.getItemDisplayName()
                
        if item.hasAttributeValue('kind'):
            kind = item.kind.getItemName()
        else:
            kind = "Kind not found"
        
        htmlString = "<html><body><h5>%s: %s</h5><ul>" % (kind, displayName)
        htmlString = htmlString + "<li><b>Path:</b> %s" % item.getItemPath()
        htmlString = htmlString + "<li><b>UUID:</b> %s" % item.getUUID()
        htmlString = htmlString + "</ul><h5>Attributes</h5><ul>"

        # We build tuples (name, formatted) for all value-only, then
        # all reference-only. Then we concatenate the two lists and sort
        # the result, and append that to the htmlString.
        value_attrs = []
        for k, v in item.iterAttributes(valuesOnly=True):
            if isinstance(v, dict):
                tmpList = ["<li><b>%s:</b></li><ul>" % k]
                for attr in v:
                    attrString = str(attr)
                    attrString = attrString.replace("<", "&lt;")
                    attrString = attrString.replace(">", "&gt;")
                    tmpList.append("<li>%s</li>" % attrString)
                tmpList.append("</ul>")
                value_attrs.append((k, "".join(tmpList)))
            else:
                value = str(v)
                value = value.replace("<", "&lt;")
                value = value.replace(">", "&gt;")
                value_attrs.append((k,"<li><b>%s: </b>%s</li>" % (k, value)))

        ref_attrs = []
        for k, v in item.iterAttributes(referencesOnly=True):
            if isinstance(v, dict) or isinstance(v, list):
                tmpList = ["<li><b>%s:</b></li><ul>" % k]
                for attr in v:
                    tmpList.append("<li>%s</li>" % self._formatReference(attr))
                tmpList.append("</ul>")
                ref_attrs.append((k, "".join(tmpList)))
            else:
                value = self._formatReference(v)
                ref_attrs.append((k,"<li><b>%s: </b>%s</li>" % (k, value)))

        all_attrs = ref_attrs + value_attrs
        all_attrs.sort()
        dyn_html = "".join([y for x, y in all_attrs])

        all_html = "%s%s</ul></body></html>" % (htmlString, dyn_html)
        
        self.SetPage(all_html)

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
        self.detail = wxRepositoryViewerDetail(self.splitter, -1, 
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
        
        self.detail.DisplayItem(item)
        
        
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

        displayName = str(item.getItemDisplayName())
        if displayName == str(item.getItemName()):
            displayName = "(unnamed)"
                
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

