__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.gizmos import *
from wxPython.html import *

from application.Application import app

from OSAF.document.model.Document import Document
from OSAF.document.model.SimpleContainers import *
from OSAF.document.model.SimpleControls import *

class RepositoryDocument:
    def __init__(self, view):
            self.view = view
            
    def ShowRepository(self, event):
        repositoryDocument = app.repository.find('//Document/Repository')
        if repositoryDocument != None:
            repositoryDocument.delete()
        repositoryDocument = self.CreateRepositoryDocument()
        doc = repositoryDocument.Render(self.view)
        self.view.GetContainingSizer().Layout()
        splitter = doc.FindWindowByName('splitter')
        self.tree = splitter.GetWindow1()
        self.detail = splitter.GetWindow2()

        self.LoadTree()
        EVT_TREE_SEL_CHANGED(self.view, self.tree.GetId(), self.OnSelChanged)
        
    def CreateRepositoryDocument(self):
        """
          Creates the Repository document to be shown.
        """
        repositoryDocument = Document('RepositoryDocument')
        container = BoxContainer('container', repositoryDocument)
        container.style['orientation'] = wxVERTICAL
        
        title = Label('title', container)
        title.style['label'] = 'Repository Viewer'
        title.style['weight'] = 0
        title.style['fontpoint'] = 18
                
        splitter = SplitterWindow('splitter', container)
        splitter.style['style'] = wxNO_FULL_REPAINT_ON_RESIZE
        splitter.style['orientation'] = wxHORIZONTAL
        
        treeList = TreeList('treelist', splitter)
        treeList.style['style'] = wxTR_HAS_BUTTONS
        treeList.style['columns'] = [_('Item Name'), 
                                 _('Display Name'), 
                                 _('Kind'), 
                                 _('UUID'), 
                                 _('URL')]
        detail = HtmlWindow('detail', splitter)
        detail.style['style'] = wxNO_FULL_REPAINT_ON_RESIZE|wxSUNKEN_BORDER
        detail.style['page'] = '<html><body><h5>Item Viewer</h5></body></html>'

        return repositoryDocument

    def OnSelChanged(self, event):
        itemId = event.GetItem()
        item = self.tree.GetItemData(itemId).GetData()

        if (item == 'Repository'):
            self.detail.SetPage("<html><body><h5>Item Viewer</h5></body></html>")
        else:
            self.DisplayItem(item)
    

    def DisplayItem(self, item):
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
        if item is None:
            root = self.tree.AddRoot('\\\\')
            self.tree.SetItemData(root, wxTreeItemData('Repository'))
            for item in app.repository.getRoots():
                path = item.getItemPath()
                self.LoadTree(item, path, root)
            self.tree.Expand(root)
        else:
            path.append(item.getItemName())
            node = self.tree.AppendItem(parent, item.getItemName())
            self.tree.SetItemData(node, wxTreeItemData(item))
            self.LoadItem(item, node)
            for child in item:
                self.LoadTree(child, path, node)
            path.pop()
            
    def LoadItem(self, item, node):
        displayName = item.getItemDisplayName()
        
        if item.hasAttributeValue('kind'):
            kind = item.kind.getItemName()
        else:
            kind = 'Kind not found'
        self.tree.SetItemText(node, displayName, 1)
        self.tree.SetItemText(node, kind, 2)
        self.tree.SetItemText(node, str(item.getUUID()), 3)
        self.tree.SetItemText(node, str(item.getItemPath()), 4)
    