__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import time
import application.Globals as Globals
from Block import *
from ContainerBlocks import *
from Node import Node
from Styles import Font
from repository.util.UUID import UUID
from wxPython.wx import *
from wxPython.gizmos import *
from wxPython.html import *


class Button(RectangularChild):
    def renderOneBlock(self, parent, parentWindow):
        try:
            id = self.clicked.getwxID()
        except AttributeError:
            id = 0

        if self.buttonKind == "Text":
            button = wxButton(parentWindow, id, self.title,
                              wxDefaultPosition,
                              (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Image":
            image = wxImage(self.icon, wxBITMAP_TYPE_PNG)
            bitmap = image.ConvertToBitmap()
            button = wxBitmapButton(parentWindow, id, bitmap,
                              wxDefaultPosition,
                              (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Toggle":
            if wxPlatform == '__WXMAC__': # @@@ Toggle buttons are not supported under OSX
                button = wxButton(parentWindow, id, self.title,
                                  wxDefaultPosition,
                                  (self.minimumSize.width, self.minimumSize.height))
            else:
                button = wxToggleButton(parentWindow, id, self.title,
                                        wxDefaultPosition,
                                        (self.minimumSize.width, self.minimumSize.height))
        elif __debug__:
            assert (False)

        self.getParentBlock(parentWindow).addToContainer(parent, button, self.stretchFactor,
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return button, None, None


class Choice(RectangularChild):
    def renderOneBlock(self, parent, parentWindow):
        choice = wxChoice(parentWindow, -1, 
                              wxDefaultPosition,
                              (self.minimumSize.width, self.minimumSize.height),
                              self.choices)
        self.getParentBlock(parentWindow).addToContainer(parent, choice, self.stretchFactor, 
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return choice, None, None


class ComboBox(RectangularChild):
    def renderOneBlock(self, parent, parentWindow):
        comboBox = wxComboBox(parentWindow, -1, self.selection, 
                              wxDefaultPosition,
                              (self.minimumSize.width, self.minimumSize.height),
                              self.choices)
        self.getParentBlock(parentWindow).addToContainer(parent, comboBox, self.stretchFactor, 
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return comboBox, None, None


class wxEditText(wxTextCtrl):
    def __init__(self, *arguments, **keywords):
        wxTextCtrl.__init__ (self, *arguments, **keywords)
        EVT_TEXT_ENTER(self, self.GetId(), self.OnEnterPressed)

    def OnEnterPressed(self, event):
        counterpart = Globals.repository.find (self.counterpartUUID)
        counterpart.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/EnterPressed'),
                          {'text':self.GetValue()})

            
class EditText(RectangularChild):
    def renderOneBlock(self, parent, parentWindow):
        style = 0
        if self.textAlignmentEnum == "Left":
            style |= wxTE_LEFT
        elif self.textAlignmentEnum == "Center":
            style |= wxTE_CENTRE
        elif self.textAlignmentEnum == "Right":
            style |= wxTE_RIGHT

        if self.lineStyleEnum == "MultiLine":
            style |= wxTE_MULTILINE
        else:
            style |= wxTE_PROCESS_ENTER

        if self.textStyleEnum == "RichText":
            style |= wxTE_RICH2

        if self.readOnly:
            style |= wxTE_READONLY

        editText = wxEditText (parentWindow,
                               -1,
                               "",
                               wxDefaultPosition,
                               (self.minimumSize.width, self.minimumSize.height),
                               style=style, name=self._name)

        editText.SetFont(Font (self.characterStyle))
        self.getParentBlock(parentWindow).addToContainer(parent,
                                                         editText,
                                                         self.stretchFactor, 
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return editText, None, None

    
class HTML(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        htmlWindow = wxHtmlWindow(parentWindow,
                                  Block.getwxID(self),
                                  wxDefaultPosition,
                                  (self.minimumSize.width, self.minimumSize.height))
        if self.url:
            htmlWindow.LoadPage(self.url)
        
        self.getParentBlock(parentWindow).addToContainer(parent,
                                                         htmlWindow,
                                                         self.stretchFactor,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return htmlWindow, None, None

    
class wxListBlock(wxListCtrl):
    def __init__(self, *arguments, **keywords):
        wxListCtrl.__init__(self, *arguments, **keywords)
        EVT_LIST_ITEM_SELECTED(self, self.GetId(), self.On_wxSelectionChanged)

    def AddListItem(self, row, labels, data):
        self.InsertStringItem(row, labels.pop(0))
        column = 1
        for label in labels:
            self.SetStringItem(row, column, label)
            column += 1
#        self.SetItemData(row, self.GetPyData(data))

    def On_wxSelectionChanged(self, event):
        counterpart = Globals.repository.find (self.counterpartUUID)
        counterpart.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                          {'id':event.GetItem()})
        
    def SynchronizeFramework(self):
        counterpart = Globals.repository.find (self.counterpartUUID)

        for index in range (self.GetColumnCount()):
            self.DeleteColumn(index)
                    
        for index in range (len(counterpart.columnHeadings)):
            heading = str(counterpart.columnHeadings[index])
            width = counterpart.columnWidths[index]
            self.InsertColumn(index, heading, width=width)            
        self.DeleteAllItems()
        counterpart.GetListData(self)

class List(RectangularChild):
    """
      List is an abstract class. To use it, you must subclass it and
    implement GetListData.
    """
    def renderOneBlock (self, parent, parentWindow):
        list = wxListBlock(parentWindow, Block.getwxID(self), 
                           style=self.Calculate_wxStyle())
        self.getParentBlock(parentWindow).addToContainer(parent, 
                                                         list,
                                                         1,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return list, None, None

    def Calculate_wxStyle (self):
        style = wxLC_REPORT|wxSUNKEN_BORDER|wxLC_EDIT_LABELS
        return style

        
class RadioBox(RectangularChild):
    def renderOneBlock(self, parent, parentWindow):
        if self.radioAlignEnum == "Across":
            dimension = wxRA_SPECIFY_COLS
        elif self.radioAlignEnum == "Down":
            dimension = wxRA_SPECIFY_ROWS
        elif __debug__:
            assert (False)
                                    
        radioBox = wxRadioBox(parentWindow, -1, self.title,
                              wxDefaultPosition, 
                              (self.minimumSize.width, self.minimumSize.height),
                              self.choices, self.itemsPerLine, dimension)
        self.getParentBlock(parentWindow).addToContainer(parent, radioBox, self.stretchFactor, 
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return radioBox, None, None


class ScrolledWindow(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        return None, None, None


class StaticText(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        if self.textAlignmentEnum == "Left":
            style = wxALIGN_LEFT
        elif self.textAlignmentEnum == "Center":
            style = wxALIGN_CENTRE
        elif self.textAlignmentEnum == "Right":
            style = wxALIGN_RIGHT

        staticText = wxStaticText (parentWindow,
                                   -1,
                                   self.title,
                                   wxDefaultPosition,
                                   (self.minimumSize.width, self.minimumSize.height),
                                   style)

        staticText.SetFont(Font (self.characterStyle))
        self.getParentBlock(parentWindow).addToContainer(parent, staticText,
                                                         self.stretchFactor,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return staticText, None, None


class StatusBar(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        frame = Globals.wxApplication.mainFrame
        assert (frame.GetStatusBar () == None)
        frame.CreateStatusBar ()
        
        return None, None, None
    

class ToolbarItem(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        # @@@ Must use self.toolbarLocation rather than wxMainFrame.GetToolBar()
        tool = None
        wxToolbar = Globals.wxApplication.mainFrame.GetToolBar()
        toolbar = Globals.repository.find(wxToolbar.counterpartUUID)
        if self.toolbarItemKind == 'Button':
            id = Block.getwxID(self)
            bitmap = wxImage (self.bitmap, wxBITMAP_TYPE_PNG).ConvertToBitmap()
            tool = wxToolbar.AddSimpleTool (id, bitmap, 
                                            self.title, self.statusMessage)
            EVT_TOOL(parentWindow, id, toolbar.toolPressed)
        elif self.toolbarItemKind == 'Separator':
            wxToolbar.AddSeparator()
        elif self.toolbarItemKind == 'Check':
            pass
        elif self.toolbarItemKind == 'Radio':
            pass
        elif self.toolbarItemKind == 'Text':
            tool = wxTextCtrl (wxToolbar, -1, "", 
                               wxDefaultPosition, 
                               wxSize(300,-1), 
                               wxTE_PROCESS_ENTER)
            tool.SetName(self.title)
            wxToolbar.AddControl (tool)
            EVT_TEXT_ENTER(tool, tool.GetId(), toolbar.toolEnterPressed)
        elif __debug__:
            assert (False)

        wxToolbar.Realize()

        return tool, None, None


class TreeNode:
    def __init__(self, nodeId, tree):
        self.nodeId = nodeId
        self.tree = tree

    def AddChildNode (self, item, names, hasChildren):
        try:
            data = item.getUUID()
        except AttributeError:
            data = item
        childNodeId = self.tree.AppendItem (self.nodeId,
                                            names.pop(0),
                                            -1,
                                            -1,
                                            wxTreeItemData (data))
        index = 1
        for name in names:
            self.tree.SetItemText (childNodeId, name, index)
            index += 1

        self.tree.SetItemHasChildren (childNodeId, hasChildren)

    def AddRootNode (self, item, names, hasChildren):
        try:
            data = item.getUUID()
        except AttributeError:
            data = item
        rootNodeId = self.tree.AddRoot (names.pop(0), -1, -1,
                                        wxTreeItemData (data))
        """
          wxTreeListCtrl's AddRoot generates an item expanded event if the root
        is hidden, but a wxTreeList does not.  Therefore, we have to expand a
        tree's hidden root manually.
        """
        counterpart = Globals.repository.find (self.tree.counterpartUUID)
        if (self.tree.__class__.__bases__[0] == wxTreeCtrl) and counterpart.hideRoot:
            self.tree.LoadChildren(rootNodeId)

        index = 1
        for name in names:
            SetItemText (rootNodeId, name, index)
            index += 1

        self.tree.SetItemHasChildren (rootNodeId, hasChildren)
                                             
    def GetData (self):
        if self.nodeId:
            return self.tree.GetItemData (self.nodeId)
        else:
            return None        

def TreeFactory(parent):
    class wxTree(parent):
        def __init__(self, *arguments, **keywords):
            parent.__init__ (self, *arguments, **keywords)
            EVT_TREE_ITEM_EXPANDING(self, self.GetId(), self.OnExpanding)
            EVT_TREE_ITEM_COLLAPSING(self, self.GetId(), self.OnCollapsing)
            EVT_LIST_COL_END_DRAG(self, self.GetId(), self.OnColumnDrag)
            EVT_TREE_SEL_CHANGED(self, self.GetId(), self.On_wxSelectionChanged)
            EVT_IDLE(self, self.OnIdle)
            self.scheduleUpdate = False
            self.lastUpdateTime = 0
            self.ignoreExpand = False
    
        def OnIdle(self, event):
            """
              Don't update screen more than once a second
            """
            if self.scheduleUpdate and (time.time() - self.lastUpdateTime) > 1.0:
                self.SynchronizeFramework()
            event.Skip()
    
        def GetItemData(self, id):
            data = self.GetPyData (id)
            try:
                data = Globals.repository [data]
            except TypeError:
                pass
            return data
    
        def OnExpanding(self, event):
            if self.ignoreExpand:
                return
            self.LoadChildren(event.GetItem())

        def LoadChildren(self, parentId):
            """
              Load the items in the tree only when they are visible.
            """
            counterpart = Globals.repository.find (self.counterpartUUID)
            counterpart.GetTreeData(TreeNode (parentId, self))
            """
              if the data passed in has a UUID we'll keep track of the
            state of the opened tree
            """
            if isinstance (self.GetPyData(parentId), UUID):
                counterpart.openedContainers [self.GetPyData(parentId)] = True
    
        def OnCollapsing(self, event):
            counterpart = Globals.repository.find (self.counterpartUUID)
            id = event.GetItem()
            self.DeleteChildren (id)
            """
              if the data passed in has a UUID we'll keep track of the
            state of the opened tree
            """
            try:
                del counterpart.openedContainers [self.GetPyData(id)]
            except AttributeError:
                pass
    
        def OnColumnDrag(self, event):
            counterpart = Globals.repository.find (self.counterpartUUID)
            columnIndex = event.GetColumn()
            try:
                counterpart.columnWidths [columnIndex] = self.GetColumnWidth (columnIndex)
            except AttributeError:
                pass
    
        def On_wxSelectionChanged(self, event):
            selection = ''
            id = self.GetSelection()
            while id.IsOk():
                selection = '/' + self.GetItemText(id) + selection
                id = self.GetItemParent (id)
    
            counterpart = Globals.repository.find (self.counterpartUUID)
            if counterpart.selection != selection:
                counterpart.selection = selection
        
                counterpart.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                                  {'item':self.GetItemData(event.GetItem())})
    
        def ExpandItem(self, id):
            # @@@ Needs to handle the difference in how wxTreeCtrls and wxTreeListCtrls
            # expand items.
            self.Expand (id)

        def SynchronizeFramework(self):
            def ExpandContainer (self, openedContainers, id):
                try:
                    expand = openedContainers [self.GetPyData(id)]
                except:
                    return
    
                self.ExpandItem(id)
                child, cookie = self.GetFirstChild (id, 0)
                while child.IsOk():
                    ExpandContainer (self, openedContainers, child)
                    child = self.GetNextSibling (child)
    
            counterpart = Globals.repository.find (self.counterpartUUID)
            try:
                counterpart.columnHeadings
                for index in range (self.GetColumnCount()):
                    self.RemoveColumn (index)
        
                info = wxTreeListColumnInfo()
                for index in range (len(counterpart.columnHeadings)):
                    info.SetText (counterpart.columnHeadings[index])
                    info.SetWidth (counterpart.columnWidths[index])
                    self.AddColumnInfo (info)
            except AttributeError:
                pass # A wxTreeCtrl won't use columnHeadings
        
            self.DeleteAllItems()
            counterpart.GetTreeData(TreeNode (None, self))
            
            ExpandContainer (self, counterpart.openedContainers, self.GetRootItem ())
            self.GoToPath (counterpart.selection)
            try:
                subscription = self.subscriptionUUID
            except AttributeError:
                events = [Globals.repository.find('//parcels/OSAF/framework/item_changed'),
                          Globals.repository.find('//parcels/OSAF/framework/item_added'),
                          Globals.repository.find('//parcels/OSAF/framework/item_deleted')]
                counterpart = Globals.repository.find (self.counterpartUUID)
                self.subscriptionUUID = UUID()
                Globals.notificationManager.Subscribe (events,
                                                       self.subscriptionUUID,
                                                       counterpart.ItemModified)
            self.scheduleUpdate = False
            self.lastUpdateTime = time.time()
    
    
        def GoToPath(self, path):
            treeNode = self.GetRootItem()
            counterpart = Globals.repository.find (self.counterpartUUID)
            child = treeNode
            for name in path.split ('/'):
                if name:
                    """
                      A wxTreeCtrl with a hidden root reports ItemHasChildren(rootId) 
                    as false and we haven't added children for items that aren't yet 
                    expanded, so we must test both.
                    """
                    assert (self.GetChildrenCount(treeNode) > 0 or
                            self.ItemHasChildren (treeNode))
                    self.ExpandItem(treeNode)
                    child, cookie = self.GetFirstChild (treeNode, 0)
                    while child.IsOk():
                        try:
                            if name == counterpart.GetTreeDataName (self.GetItemData(child)):
                                break
                        except AttributeError:
                            pass
                        child = self.GetNextSibling (child)
    
                    if child.IsOk():
                        treeNode = child
                    else:
                        """
                          path doesn't exist
                        """
                        return
            self.SelectItem (child)
            self.ScrollTo (child)
            
            pass
    return wxTree


class Tree(RectangularChild):
    """
      Tree is an abstract class. To use it, you must subclass it and
    implement GetTreeData and GetTreeDataName. See RepositoryTree
    for an example
    """
    def __init__(self, *arguments, **keywords):
        super (Tree, self).__init__ (*arguments, **keywords)
        self.openedContainers = {}
        self.rootPath = None

    def renderOneBlock(self, parent, parentWindow, nativeWindow=None):
        if nativeWindow:
            tree = nativeWindow
        else:
            try:
                self.columnHeadings
                type = wxTreeListCtrl
            except AttributeError:
                type = wxTreeCtrl
            tree = TreeFactory(type)(parentWindow, Block.getwxID(self), style = self.Calculate_wxStyle())
        self.getParentBlock(parentWindow).addToContainer(parent,
                                                         tree,
                                                         1,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return tree, None, None

    def Calculate_wxStyle (self):
        style = wxTR_DEFAULT_STYLE|wxNO_BORDER
        if self.hideRoot:
            style |= wxTR_HIDE_ROOT
        if self.noLines:
            style |= wxTR_NO_LINES
        if self.useButtons:
            style |= wxTR_HAS_BUTTONS
        else:
            style |= wxTR_NO_BUTTONS
        return style

