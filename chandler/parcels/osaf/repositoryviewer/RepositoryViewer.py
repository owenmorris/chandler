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

from application.ViewerParcel import *

from application.Application import app
from repository.util.Path import Path
from repository.item.Item import Item
import os
from application.SplashScreen import SplashScreen

class RepositoryViewer(ViewerParcel):
    def __init__(self, **args):
        super(RepositoryViewer, self).__init__(**args)
        self.newAttribute('detailItem', '')

    def GoToURL(self, remoteaddress, url):
        if remoteaddress != None:
            print "Odd error. Remote addresses not supported by repository viewer, now what?"
            return

        try:
            url = url[url.index("Repository Viewer")+17:]
        except ValueError:
            pass
        url = url.strip()
        self.SetDetailItem(url)

    def SetDetailItem(self, item):
        self.SynchronizeView()
        self.detailItem = str(item)
        viewer = app.association[id(self)]
        viewer.UpdateDisplay()

    def GetDetailItem(self):
        di = self.detailItem
        if (di == "") or (type(di) != type("")):
            return None
        else:
            an_item = app.repository.getRoots()[0]
            return an_item.find(di)

            
class wxRepositoryViewerEdit(wxSplitterWindow):
    """ An edit tab for the Repository viewer. """
    __dirty=False # __dirty is set when information is changed in any edit widget

    
    def __init__(self, parent, id):
        wxSplitterWindow.__init__(self, parent, id)     
        self.p2 = wxWindow(self, -1)
        
        box = wxBoxSizer(wxVERTICAL)
        b = wxButton(self.p2, -1, "Submit Changes")
        box.Add(b, 0, wxALIGN_CENTER|wxALL, 10)
        self.p2.SetAutoLayout(True)
        self.p2.SetSizer(box)        
        EVT_BUTTON(self, b.GetId(), self.UpdateRepository)
        b.SetBackgroundColour(wxBLUE)
        b.SetForegroundColour(wxWHITE)
        self.DisplayItem()  
        self.SplitVertically(self.p1, self.p2, 590)
        self.p1.Layout()
        
    def UpdateRepository(self, evt):     
        if not self.item: return
        if not self.__dirty: return
        for k in self.widgets:
            self.item.setAttributeValue(k, self.widgets[k].GetValue())
        self.__dirty=False#Now we're clean locally

    def TrackDirt(self, evt):
        """ Event handler to track when widgets get changed. """
        self.__dirty=True
        evt.Skip() 

    def DisplayItem(self, item=None):
        """
          Layout the edit panel for the given item.  First, destroy the existing
          widget panel, then create a new panel, populating it with widgets
          for each attribute of the item.
        """
        self.item=item
        self.widgets={}
        p1 = wxScrolledWindow(self, -1)

        if getattr(self, 'p1', 0):
            oldp1=self.p1
            self.ReplaceWindow(oldp1, p1)
            oldp1.Clear()
            oldp1.Destroy()
        self.p1=p1
        self.p1.maxWidth  = 600
        self.p1.maxHeight = 1000
        self.p1.x = self.p1.y = 0

        # Ideally the scrollbars would be dynamically created.  How?
        self.p1.SetScrollRate(0, 20)
        
        if item is None:
            self.label("Item Editor")
        else:
            displayName = item.getItemDisplayName()
                    
            if item.hasAttributeValue('kind'):
                kind = item.kind.getItemName()
            else:
                kind = "(kindless)"
            self.titleText=self.label("%s: %s" % (kind, displayName))
            
            #for now, don't do references
            self.value_attrs = [self.titleText, (0,0), (0,0)]
            for k, v in item.iterAttributes(valuesOnly=True):
                if isinstance(v, dict):
                    #don't deal with dictionaries for now
                    for attr in v:
                        pass
                else:
                    self.value_attrs.append(self.label(str(k)))
                    self.value_attrs.append(self.inputWidget(item, str(k), str(v)))
                    self.value_attrs.append((0,0))
            sizer = wxFlexGridSizer(cols=3, hgap=6, vgap=6)
            sizer.AddMany(self.value_attrs)
            self.p1.SetSizer(sizer)
            self.p1.SetAutoLayout(true)
            self.p1.Layout()

    def label(self, text):
        """ Put a label on the edit panel."""
        return wxStaticText(self.p1, -1, text)
        
    def inputWidget(self, item, attr_name, val=""):
        """
          Return an appropriate widget for the given item attribute.
          For now, just return a text box
        """
        self.widgets[attr_name]=wxTextCtrl(self.p1, -1, val, size=(300, 100), style=wxTE_MULTILINE)
        EVT_TEXT(self, self.widgets[attr_name].GetId(), self.TrackDirt)
        return self.widgets[attr_name]
        
        
class wxRepositoryViewer(wxViewerParcel):
    def OnInit(self):
        """
          Initializes the repository viewer, setting up the layout
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
        # Set up tree control using a spacer column
        self.treeCtrl = wxTreeListCtrl(self.splitter)
        info = wxTreeListColumnInfo()
        labels=['Item Name', 'Display Name', 'Kind', 'UUID', '', 'URL']
        colLabels = map(_, labels)
        colSize = [80, 80, 80, 120, 10, 120]
        for x in range(len(colLabels)):
            info.SetText(colLabels[x])
            info.SetWidth(colSize[x])
            self.treeCtrl.AddColumnInfo(info)
        
        EVT_TREE_SEL_CHANGED(self, self.treeCtrl.GetId(), self.OnSelChanged)
        EVT_TREE_ITEM_EXPANDING(self, self.treeCtrl.GetId(), self.OnExpanding)
        
        # Set up notebook
        self.notebookPanel = wxPanel(self.splitter, -1)
        self.notebook = wxNotebook(self.notebookPanel, -1)
        EVT_NOTEBOOK_PAGE_CHANGED(self.notebook, self.notebook.GetId(), self.OnTabChanged)
        
        # Set up detail view
        self.viewTab = wxPanel(self.notebook, -1)
        self.detail = wxRepositoryViewerDetail(self.viewTab, -1, 
                                  style=wxNO_FULL_REPAINT_ON_RESIZE | wxSUNKEN_BORDER)
        self.detail.SetPage("<html><body><h5>Item Viewer</h5></body></html>")

        # Set up edit detail view
        self.editTab= wxRepositoryViewerEdit(self.notebook, -1)
        
        # Do layout

        self.notebook.AddPage(self.viewTab, "View", select=1)
        self.notebook.AddPage(self.editTab, "Edit")
        
        notebookContainer = wxBoxSizer(wxVERTICAL)
        notebookContainer.Add(wxNotebookSizer(self.notebook), 1, wxEXPAND, 0)
        self.notebookPanel.SetAutoLayout(1)
        self.notebookPanel.SetSizer(notebookContainer)
        notebookContainer.Fit(self.notebookPanel)
        notebookContainer.SetSizeHints(self.notebookPanel)

        viewContainer = wxBoxSizer(wxVERTICAL)
        viewContainer.Add(self.detail, -1, wxEXPAND)
        self.viewTab.SetAutoLayout(1)
        self.viewTab.SetSizer(viewContainer)

        self.splitter.SplitHorizontally(self.treeCtrl, self.notebookPanel, 200)
                
        self.container = wxBoxSizer(wxVERTICAL)
        self.container.Add(self.title, 0, wxEXPAND)
        self.container.Add(self.splitter, 1, wxEXPAND)
        self.SetSizerAndFit(self.container)
        
        self.treeItemsByUUID = {}
        self.LoadTree()

    def OnTabChanged(self, event):
        event.Skip()

    def OnSelChanged(self, event):
        """
          Display the selected Item.
        """
        itemId = event.GetItem()
        item = self.treeCtrl.GetItemData(itemId).GetData()
        if (item == "Repository"):
            item == ""
        else:
            item = item.getItemPath()
        app.wxMainFrame.GoToURL("Repository Viewer%s" % (item,), true)

    def OnExpanding(self, event):
        """
          Load the items in the tree only when they are visible.
        """
        itemId = event.GetItem()
        item = self.treeCtrl.GetItemData(itemId).GetData()
        if (item != "Repository"):
            if self.treeCtrl.GetChildrenCount(itemId, False) == 0:
                for child in item:
                    self.LoadTree(child, itemId)
        
    def UpdateDisplay(self):
        item = self.model.GetDetailItem()
        self.detail.DisplayItem(item)
        
        self.editTab.DisplayItem(item)     
        if not item: return

        uuid = str(item.getUUID())

        old = self.treeCtrl.GetSelection()        
        
        self.GenerateTreeItems(item, uuid)
        node = self.treeItemsByUUID[uuid]

        if old != node:
            self.treeCtrl.EnsureVisible(node)
            self.treeCtrl.SelectItem(node)
        
    def GenerateTreeItems(self, item, uuid):
        """
          Makes sure that the item being selected has its corresponding node 
        created within the tree (along with all of its ancestors).
        """
        try:
            self.treeItemsByUUID[uuid]
        except:
            parent = item.getItemParent()
            parentId = str(parent.getUUID())
            self.GenerateTreeItems(parent, parentId)

            parentNode = self.treeItemsByUUID[parentId]
            node = self.treeCtrl.AppendItem(parentNode, item.getItemName())
            self.treeCtrl.SetItemData(node, wxTreeItemData(item))
            self.LoadItem(item, node)
            if item.hasChildren():
                self.treeCtrl.SetItemHasChildren(node, True)        
        
    def LoadTree(self, item=None, parent=None):
        """
          Loads the tree at the level of the supplied item.
          
          The rest of the body of the tree is only loaded when it needs to 
        be displayed for for the first time.
        """
        if item is None:
            root = self.treeCtrl.AddRoot("\\\\")
            self.treeCtrl.SetItemData(root, wxTreeItemData("Repository"))
            for item in app.repository.getRoots():
                self.LoadTree(item, root)
            self.treeCtrl.Expand(root)
        else:
            node = self.treeCtrl.AppendItem(parent, item.getItemName())
            self.treeCtrl.SetItemData(node, wxTreeItemData(item))
            self.LoadItem(item, node)
            if item.hasChildren():
                self.treeCtrl.SetItemHasChildren(node, True)

    def LoadItem(self, item, node):
        """
          Populates the tree's table with details of this particular item.
        """
        displayName = str(item.getItemDisplayName())
        if displayName == str(item.getItemName()):
            displayName = "(unnamed)"
                
        if item.hasAttributeValue('kind'):
            kind = item.kind.getItemName()
        else:
            kind = "(kindless)"
        
        self.treeCtrl.SetItemText(node, displayName, 1)
        self.treeCtrl.SetItemText(node, kind, 2)
        u = str(item.getUUID())
        self.treeCtrl.SetItemText(node, u, 3)
        self.treeItemsByUUID[u] = node
        self.treeCtrl.SetItemText(node, str(item.getItemPath()), 5)

    def OnAboutRepositoryViewer(self, event):
        pageLocation = self.model.path + os.sep + "AboutRepositoryViewer.html"
        infoPage = SplashScreen(self, _("About Repository Viewer"), pageLocation, 
                                False, False)
        infoPage.Show(True)


class wxRepositoryViewerDetail(wxHtmlWindow):
    def OnLinkClicked(self, wx_linkinfo):
        uri = wx_linkinfo.GetHref()
        app.wxMainFrame.GoToURL(uri, true)

    def _formatReference(self, ref):
        """
          Formats the a reference attribute to be clickable, etcetera
        """
        url = ref.getItemPath()
        if ref.hasAttributeValue('kind'):
            kind = ref.kind.getItemName()
        else:
            kind = "(kindless)"
        # Originally I was masking the fallback to itemName here just like in
        # the listview, but that doesn't work for many of the more primitive
        # repository items, so I stopped doing that.
        dn = str(ref.getItemDisplayName())

        # Escape < and > for HTML display
        kind = kind.replace("<", "&lt;").replace(">", "&gt;")
        dn = dn.replace("<", "&lt;").replace(">", "&gt;")

        return "<a href=\"Repository Viewer%(url)s\">%(kind)s: %(dn)s</a>" % locals()

    def DisplayItem(self, item):
        """
          Display the given Item's details in an HTML window.
        """
        if item is None:
            self.SetPage("<html><body><h5>Item Viewer</h5></body></html>")
            return

        displayName = item.getItemDisplayName()
                
        if item.hasAttributeValue('kind'):
            kind = item.kind.getItemName()
        else:
            kind = "(kindless)"
        
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
        