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
from new import classobj
import webbrowser # for opening external links


class Button(RectangularChild):
    def renderOneBlock(self, parent, parentWindow):
        try:
            id = Block.getwxID(self.event)
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
            assert False, "unknown buttonKind"

        EVT_BUTTON(parentWindow, id, self.buttonPressed)
        self.getParentBlock(parentWindow).addToContainer(parent, button, self.stretchFactor,
                              self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return button, None, None

    def buttonPressed(self, event):
        try:
            event = self.event
        except AttributeError:
            pass
        else:
            self.Post(event, {'item':self})

                              
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
                                                         self.stretchFactor,
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
            assert False, "unknown radioAlignEnum"
                                    
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
        assert (frame.GetStatusBar () == None), "mainFrame already has a StatusBar"
        frame.CreateStatusBar ()
        
        return None, None, None
    

class ToolbarItem(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        # @@@ Must use self.toolbarLocation rather than wxMainFrame.GetToolBar()
        tool = None
        wxToolbar = Globals.wxApplication.mainFrame.GetToolBar()
        toolbar = Globals.repository.find(wxToolbar.counterpartUUID)
        id = Block.getwxID(self)
        if self.toolbarItemKind == 'Button':
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
            tool = wxTextCtrl (wxToolbar, id, "", 
                               wxDefaultPosition, 
                               wxSize(300,-1), 
                               wxTE_PROCESS_ENTER)
            tool.SetName(self.title)
            wxToolbar.AddControl (tool)
            EVT_TEXT_ENTER(tool, id, toolbar.toolEnterPressed)
        elif __debug__:
            assert False, "unknown toolbarItemKind"

        wxToolbar.Realize()

        return tool, None, None


def TreeFactory(parent):
    class wxTree(parent):
        classesByName = {}
        def __init__(self, *arguments, **keywords):
            parent.__init__ (self, *arguments, **keywords)
            EVT_TREE_ITEM_EXPANDING(self, self.GetId(), self.OnExpanding)
            EVT_TREE_ITEM_COLLAPSING(self, self.GetId(), self.OnCollapsing)
            EVT_LIST_COL_END_DRAG(self, self.GetId(), self.OnColumnDrag)
            EVT_TREE_SEL_CHANGED(self, self.GetId(), self.On_wxSelectionChanged)
            EVT_IDLE(self, self.OnIdle)
            EVT_SIZE(self, self.OnSize)
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
    
        def OnSize(self, event):
            size = event.GetSize()
            if isinstance (self, wxTreeListCtrl):
                widthMinusLastColumn = 0
                assert self.GetColumnCount() > 0, "We're assuming that there is at least one column"
                for column in range (self.GetColumnCount() - 1):
                    widthMinusLastColumn += self.GetColumnWidth (column)
                lastColumnWidth = size.width - widthMinusLastColumn
                if lastColumnWidth > 0:
                    self.SetColumnWidth (self.GetColumnCount() - 1, lastColumnWidth)
            else:
                assert isinstance (self, wxTreeList), "We're assuming the only other choice is a wxTree"
                self.SetSize (size)
            event.Skip()
    
        def OnExpanding(self, event):
            if self.ignoreExpand:
                return
            self.LoadChildren(event.GetItem())

        def LoadChildren(self, parentId):
            """
              Load the items in the tree only when they are visible.
            """
            counterpart = Globals.repository.find (self.counterpartUUID)

            parentUUID = self.GetPyData (parentId)
            for child in self.ElementChildren (Globals.repository [parentUUID]):
                cellValues = self.ElementCellValues (child)
                childNodeId = self.AppendItem (parentId,
                                               cellValues.pop(0),
                                               -1,
                                               -1,
                                               wxTreeItemData (child.getUUID()))
                index = 1
                for value in cellValues:
                    self.SetItemText (childNodeId, value, index)
                    index += 1
                self.SetItemHasChildren (childNodeId, self.ElementHasChildren (child))

            counterpart.openedContainers [parentUUID] = True
    
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
            counterpart = Globals.repository.find (self.counterpartUUID)

            itemUUID = self.GetPyData(self.GetSelection())
            selection = Globals.repository.find (itemUUID)
            if counterpart.selection != selection:
                counterpart.selection = selection
        
                counterpart.Post (Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged'),
                                  {'item':selection})

        def ExpandItem(self, id):
            # @@@ Needs to handle the difference in how wxTreeCtrls and wxTreeListCtrls
            # expand items.
            self.Expand (id)

        def SynchronizeFramework(self):
            def ExpandContainer (self, openedContainers, id):
                try:
                    expand = openedContainers [self.GetPyData(id)]
                except KeyError:
                    return

                self.ExpandItem(id)
                child, cookie = self.GetFirstChild (id, 0)
                while child.IsOk():
                    ExpandContainer (self, openedContainers, child)
                    child = self.GetNextSibling (child)
    
            counterpart = Globals.repository.find (self.counterpartUUID)
            """
              Implement the knowlege of the item that a tree displays with a mixin
            class specified by self.elementDelegate. We make a new class for our
            block that is subclassed from the block's original class and the delegate
            class with a little Python magic:
            """
            theClass = wxTree.classesByName.get (self.__class__.__name__)
            if not theClass:
                parts = counterpart.elementDelegate.split (".")
                assert len(parts) >= 2, "Delegate % isn't a module and class" % counterpart.elementDelegate
                delegateClassName = parts.pop ()
                newClassName = self.__class__.__name__ + '_' + delegateClassName
                theClass = wxTree.classesByName.get (newClassName)
                if not theClass:
                    module = __import__ ('.'.join(parts), globals(), locals(), delegateClassName)
                    assert module.__dict__.get (delegateClassName), "Class % doesn't exist" % counterpart.elementDelegate
                    theClass = classobj (str(newClassName),
                                         (self.__class__, module.__dict__[delegateClassName]),
                                         {})
                    wxTree.classesByName [newClassName] = theClass
                self.__class__ = theClass

            try:
                counterpart.columnHeadings
            except AttributeError:
                pass # A wxTreeCtrl won't use columnHeadings
            else:
                for index in range (self.GetColumnCount()):
                    self.RemoveColumn (index)
        
                info = wxTreeListColumnInfo()
                for index in range (len(counterpart.columnHeadings)):
                    info.SetText (counterpart.columnHeadings[index])
                    info.SetWidth (counterpart.columnWidths[index])
                    self.AddColumnInfo (info)

            self.DeleteAllItems()

            root = counterpart.rootPath
            if not root:
                root = self.ElementChildren (None)
            cellValues = self.ElementCellValues (root)
            rootNodeId = self.AddRoot (cellValues.pop(0),
                                       -1,
                                       -1,
                                       wxTreeItemData (root.getUUID()))
            self.SetItemHasChildren (rootNodeId, self.ElementHasChildren (root))        
            ExpandContainer (self, counterpart.openedContainers, self.GetRootItem ())

            selection = counterpart.selection
            if not selection:
                selection = root
            self.GoToItem (selection)

            try:
                subscription = self.subscriptionUUID
            except AttributeError:
                events = [Globals.repository.find('//parcels/OSAF/framework/item_changed'),
                          Globals.repository.find('//parcels/OSAF/framework/item_added'),
                          Globals.repository.find('//parcels/OSAF/framework/item_deleted')]
                counterpart = Globals.repository.find (self.counterpartUUID)
                self.subscriptionUUID = UUID()
                """
                  Temporarily comment out event subscriptions. This cause gazillions of
                crashes, which may be related to threads, race conditions, repository
                interactions. We'll need some more time to track this down in detail.
                """
                Globals.notificationManager.Subscribe (events,
                                                       self.subscriptionUUID,
                                                       self.NeedsUpdate)
            self.scheduleUpdate = False
            self.lastUpdateTime = time.time()
            
        def __del__(self):
            Globals.notificationManager.Unsubscribe(self.subscriptionUUID)
            del Globals.association [self.counterpartUUID]

        def GoToItem(self, item):
            def ExpandTreeToItem (self, item):
                parent = self.ElementParent (item)
                if parent:
                    id = ExpandTreeToItem (self, parent)
                    self.Expand (id)
                    itemUUID = item.getUUID()
                    child, cookie = self.GetFirstChild (id, 0)
                    while child.IsOk():
                        if self.GetPyData(child) == itemUUID:
                            return child
                        child = self.GetNextSibling (child)
                    assert False, "Didn't find the item in the tree"
                    return None
                else:
                    return self.GetRootItem()

            id = ExpandTreeToItem (self, item)
            self.SelectItem (id)
            self.ScrollTo (id)

    return wxTree


class Tree(RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (Tree, self).__init__ (*arguments, **keywords)
        self.openedContainers = {}
        self.rootPath = None
        self.selection = None

    def renderOneBlock(self, parent, parentWindow, nativeWindow=None):
        if nativeWindow:
            tree = nativeWindow
        else:
            try:
                self.columnHeadings
            except AttributeError:
                type = wxTreeCtrl
            else:
                type = wxTreeListCtrl
            tree = TreeFactory(type)(parentWindow, Block.getwxID(self), style = self.Calculate_wxStyle())
        self.getParentBlock(parentWindow).addToContainer(parent,
                                                         tree,
                                                         self.stretchFactor,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return tree, None, None

    def OnSelectionChangedEvent (self, notification):
        wxCounterpart = Globals.association[self.getUUID()]
        wxCounterpart.GoToItem (notification.GetData()['item'])


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

class wxItemDetail(wxHtmlWindow):
    def OnLinkClicked(self, wx_linkinfo):
        """ Clicking on an item changes the selection (post notification).
            Clicking on a URL loads the page in a separate browser.
        """
        itemURL = wx_linkinfo.GetHref()
        item = Globals.repository.find(itemURL)
        if not item:
            webbrowser.open(itemURL)
        else:
            event = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged')
            event.Post({'item':item, 'type':'Normal'})

    def SynchronizeFramework(self):
        counterpart = Globals.repository.find (self.counterpartUUID)
        item = Globals.repository.find (counterpart.selection)
        try:
            self.SetPage(counterpart.getHTMLText(item))
        except TypeError:
            self.SetPage('<body><html><h1>Error displaying the item</h1></body></html>')

class ItemDetail(RectangularChild):
    def renderOneBlock (self, parent, parentWindow):
        htmlWindow = wxItemDetail(parentWindow,
                                  Block.getwxID(self),
                                  wxDefaultPosition,
                                  (self.minimumSize.width,
                                   self.minimumSize.height))
        
        parentBlock = self.getParentBlock(parentWindow)
        parentBlock.addToContainer(parent,
                                   htmlWindow,
                                   self.stretchFactor,
                                   self.Calculate_wxFlag(),
                                   self.Calculate_wxBorder())

        return htmlWindow, None, None

    def getHTMLText(self, item):
        return '<body><html><h1>%s</h1></body></html>' % item.getDisplayName()

    def OnSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWindow counterpart.
        """
        item = notification.data['item']
        self.selection = item.getUUID()
        wxWindow = Globals.association[self.getUUID()]
        wxWindow.SynchronizeFramework ()
