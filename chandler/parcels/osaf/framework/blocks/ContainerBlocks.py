import application.Globals as Globals
from Block import Block
from wxPython.wx import *
from wxPython.gizmos import *
from wxPython.html import *
from OSAF.framework.notifications.Notification import Notification


class Font(wxFont):
    def __init__(self, characterStyle):
        family = wxDEFAULT
        size = 12
        style = wxNORMAL
        underline = FALSE
        weight = wxNORMAL
        if characterStyle:
            if characterStyle.fontFamily == "SerifFont":
                family = wxROMAN
            elif characterStyle.fontFamily == "SanSerifFont":
                family = wxSWISS
            elif characterStyle.fontFamily == "FixedPitchFont":
                family = wxMODERN
    
            assert (size > 0)
            size = int (characterStyle.fontSize + 0.5) #round to integer

            for theStyle in characterStyle.fontStyle.split():
                lowerStyle = theStyle.lower()
                if lowerStyle == "bold":
                    weight = wxBOLD
                elif lowerStyle == "light":
                    weight = wxLIGHT
                elif lowerStyle == "italic":
                    style = wxITALIC
                elif lowerStyle == "underline":
                    underline = TRUE
                
        wxFont.__init__ (self,
                         size,
                         family,
                         style,
                         weight,
                         underline,
                         characterStyle.fontName)


class ContainerChild(Block):
    def render (self, parent, parentWindow):
        (window, parent, parentWindow) = self.renderOneBlock (parent, parentWindow)
        """
          Store the wxWindows version of the object in the association, so
        given the block we can find the associated wxWindows object.
        """
        if window:
            UUID = self.getUUID()
            assert not Globals.association.has_key(UUID)
            Globals.association[UUID] = window
            window.counterpartUUID = UUID
            for child in self.childrenBlocks:
                child.render (parent, parentWindow)
        return window


class RectContainer(ContainerChild):
    def Calculate_wxFlag (self):
        if self.alignmentEnum == 'grow':
            flag = wxGROW
        elif self.alignmentEnum == 'growConstrainAspectRatio':
            flag = wxSHAPED
        elif self.alignmentEnum == 'alignCenter':
            flag = wxALIGN_CENTER
        elif self.alignmentEnum == 'alignTopCenter':
            flag = wxALIGN_TOP
        elif self.alignmentEnum == 'alignMiddleLeft':
            flag = wxALIGN_LEFT
        elif self.alignmentEnum == 'alignBottomCenter':
            flag = wxALIGN_BOTTOM
        elif self.alignmentEnum == 'alignMiddleRight':
            flag = wxALIGN_RIGHT
        elif self.alignmentEnum == 'alignTopLeft':
            flag = wxALIGN_TOP | wxALIGN_LEFT
        elif self.alignmentEnum == 'alignTopRight':
            flag = wxALIGN_TOP | wxALIGN_RIGHT
        elif self.alignmentEnum == 'alignBottomLeft':
            flag = wxALIGN_BOTTOM | wxALIGN_LEFT
        elif self.alignmentEnum == 'alignBottomRight':
            flag = wxALIGN_BOTTOM | wxALIGN_RIGHT
        return flag


    def Calculate_wxBorder (self):
        border = 0
        spacerRequired = False
        for edge in (self.border.top, self.border.left, self.border.bottom, self.border.right):
            if edge != 0:
                if border == 0:
                    border = edge
                elif border != edge:
                    spacerRequired = False
                    break
        """
          wxWindows sizers only allow borders with the same width, or no width, however
        blocks allow borders of different sizes for each of the 4 edges, so we need to
        simulate this by adding spacers. I'm postponing this case for Jed to finish, and
        until then an assert will catch this case. DJA
        """
        assert not spacerRequired
        
        return int (border)


class BoxContainer(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        if self.orientationEnum == 'Horizontal':
            orientation = wxHORIZONTAL
        else:
            orientation = wxVERTICAL

        sizer = wxBoxSizer(orientation)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))
        panel = wxPanel(parentWindow, -1)
        panel.SetSizer(sizer)

#        if isinstance (parent, wxWindowPtr):
#            parent.SetSizer (sizer)
#        else:
        if isinstance (parent, wxSizerPtr):
            parent.Add(panel, 1, self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return panel, sizer, panel

 
class Button(RectContainer):
    def renderOneBlock(self, parent, parentWindow):
#        assert isinstance (parent, wxSizerPtr) #must be in a container
        id = 0
        if self.hasAttributeValue ("clicked"):  # Repository bug/feature -- DJA
            id = self.clicked.getwxID()

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
            button = wxToggleButton(parentWindow, id, self.title,
                              wxDefaultPosition,
                              (self.minimumSize.width, self.minimumSize.height))
        elif __debug__:
            assert (False)

        if isinstance (parent, wxSizerPtr):
            parent.Add(button, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return button, None, None


class Choice(RectContainer):
    def renderOneBlock(self, parent, parentWindow):
#        assert isinstance (parent, wxSizerPtr) #must be in a container
        choice = wxChoice(parentWindow, -1, 
                              wxDefaultPosition,
                              (self.minimumSize.width, self.minimumSize.height),
                              self.choices)
        if isinstance (parent, wxSizerPtr):
            parent.Add(choice, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return choice, None, None


class ComboBox(RectContainer):
    def renderOneBlock(self, parent, parentWindow):
#        assert isinstance (parent, wxSizerPtr) #must be in a container
        comboBox = wxComboBox(parentWindow, -1, self.selection, 
                              wxDefaultPosition,
                              (self.minimumSize.width, self.minimumSize.height),
                              self.choices)
        if isinstance (parent, wxSizerPtr):
            parent.Add(comboBox, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return comboBox, None, None

    
class EditText(RectContainer):
    def __init__(self, *arguments, **keywords):
        super (EditText, self).__init__ (*arguments, **keywords)

    def renderOneBlock(self, parent, parentWindow):
#        assert isinstance (parent, wxSizerPtr) #must be in a container
        
        style = 0
        if self.textAlignmentEnum == "Left":
            style |= wxTE_LEFT
        elif self.textAlignmentEnum == "Center":
            style |= wxTE_CENTRE
        elif self.textAlignmentEnum == "Right":
            style |= wxTE_RIGHT

        if self.lineStyleEnum == "MultiLine":
            style |= wxTE_MULTILINE

        if self.textStyleEnum == "RichText":
            style |= wxTE_RICH2

        if self.readOnly:
            style |= wxTE_READONLY

        editText = wxTextCtrl (parentWindow,
                               -1,
                               "",
                               wxDefaultPosition,
                               (self.minimumSize.width, self.minimumSize.height),
                               style, name=self._name)

        editText.SetFont(Font (self.characterStyle))
        if isinstance (parent, wxSizerPtr):
            parent.Add(editText, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return editText, None, None


class HTML(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        id = 0
        if self.hasAttributeValue ("pageLoaded"):  # Repository bug/feature -- DJA
            id = self.pageLoaded.getwxID()

        htmlWindow = wxHtmlWindow(parentWindow, id, wxDefaultPosition,
                                  (self.minimumSize.width, self.minimumSize.height))
        htmlWindow.LoadPage(self.url)
        
        if isinstance (parent, wxSizerPtr):
            parent.Add(htmlWindow, int(self.stretchFactor),
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return htmlWindow, None, None


class List(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        return None, None, None


class RadioBox(RectContainer):
    def renderOneBlock(self, parent, parentWindow):
#        assert isinstance (parent, wxSizerPtr) #must be in a container
        id = 0
        if self.hasAttributeValue ("selectionChanged"):  # Repository bug/feature -- DJA
            id = self.selectionChanged.getwxID()

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
        if isinstance (parent, wxSizerPtr):
            parent.Add(radioBox, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return radioBox, None, None


class ScrolledWindow(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        return None, None, None


class SplitterWindow(RectContainer):
    # @@@ Right now this is unnecessary boiler plate that should be removed.  We
    #  need a better way to allow items to hook themselves into their parent
    #  if that parent is not a sizer.  One possible solution is to have a method
    #  on that parent (AddChild) which the child can call when it is created and
    #  which does the correct hooking up.
    def render (self, parent, parentWindow):
        (window, parent, parentWindow) = self.renderOneBlock (parent, parentWindow)
        """
          Store the wxWindows version of the object in the association, so
        given the block we can find the associated wxWindows object.
        """
        if window:
            UUID = self.getUUID()
            assert not Globals.association.has_key(UUID)
            Globals.association[UUID] = window
            window.counterpartUUID = UUID
            for child in self.childrenBlocks:
                child.render (parent, parentWindow)

        children = window.GetChildren()
        if self.orientationEnum == "Horizontal":
            window.SplitVertically(children[0], children[1])
        else:
            window.SplitHorizontally(children[0], children[1])
        return window

    def renderOneBlock (self, parent, parentWindow):
 #       assert isinstance (parent, wxSizerPtr)
        id = 0
        if self.hasAttributeValue ("sashPosChanged"):  # Repository bug/feature -- DJA
            id = self.sashPosChanged.getwxID()
            
        splitter = wxSplitterWindow(parentWindow, id, 
                                    wxDefaultPosition,
                                    (self.minimumSize.width, self.minimumSize.height))
        if isinstance (parent, wxSizerPtr):
            parent.Add(splitter, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return splitter, splitter, splitter


class StaticText(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
#        assert isinstance (parent, wxSizerPtr) #must be in a container
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
        if isinstance (parent, wxSizerPtr):
            parent.Add(staticText, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return staticText, None, None


class TabbedContainer(RectContainer):
    # @@@ Right now this is unnecessary boiler plate that should be removed.  We
    #  need a better way to allow items to hook themselves into their parent
    #  if that parent is not a sizer.  One possible solution is to have a method
    #  on that parent (AddChild) which the child can call when it is created and
    #  which does the correct hooking up.
    def render (self, parent, parentWindow):
        (window, parent, parentWindow) = self.renderOneBlock (parent, parentWindow)
        """
          Store the wxWindows version of the object in the association, so
        given the block we can find the associated wxWindows object.
        """
        childList = []
        if window:
            UUID = self.getUUID()
            assert not Globals.association.has_key(UUID)
            Globals.association[UUID] = window
            window.counterpartUUID = UUID
            for child in self.childrenBlocks:
                childList.append(child.render (parent, parentWindow))

        i = 0
        for child in childList:
            window.AddPage(child, self.tabNames[i])
            i = i + 1
        return window

    def renderOneBlock (self, parent, parentWindow):
#        assert isinstance (parent, wxSizerPtr)
        id = 0
        if self.hasAttributeValue ("selectionChanged"):  # Repository bug/feature -- DJA
            id = self.selectionChanged.getwxID()
            
        if self.tabPosEnum == "Top":
            style = 0
        elif self.tabPosEnum == "Bottom":
            style = wxNB_BOTTOM
        elif self.tabPosEnum == "Left":
            style = wxNB_LEFT
        elif self.tabPosEnum == "Right":
            style = wxNB_RIGHT
        elif __debug__:
            assert (False)
            
        tabbedContainer = wxNotebook(parentWindow, id, 
                                    wxDefaultPosition,
                                    (self.minimumSize.width, self.minimumSize.height),
                                     style = style)
        if isinstance (parent, wxSizerPtr):
            parent.Add(tabbedContainer, int(self.stretchFactor), 
                       self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return tabbedContainer, tabbedContainer, tabbedContainer

    def on_chandler_TabChoice (self, notification):
        tabbedContainer = Globals.association[self.getUUID()]
        choice = notification.data ['event'].choice
        for index in xrange (tabbedContainer.GetPageCount()):
            if tabbedContainer.GetPageText(index) == choice:
                tabbedContainer.SetSelection (index)
                break


class Toolbar(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        return None, None, None


class ToolbarItem(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        return None, None, None


class Tree(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        return None, None, None


class TreeNode:
    def __init__(self, nodeId, treeList):
        self.nodeId = nodeId
        self.treeList = treeList

    def AddChildNode (self, data, title, hasChildren):
        childNodeId = self.treeList.AppendItem (self.nodeId,
                                                title,
                                                -1,
                                                -1,
                                                wxTreeItemData (data))
        self.treeList.SetItemHasChildren (childNodeId, hasChildren)


    def AddRootNode (self, data, title, hasChildren):
        rootNodeId = self.treeList.AddRoot (title, -1, -1, wxTreeItemData (data))
        self.treeList.SetItemHasChildren (rootNodeId, hasChildren)
        #self.treeList.Expand (rootNodeId)

                                             
    def GetData (self):
        if self.nodeId:
            return self.treeList.GetPyData (self.nodeId)
        else:
            return None        


class wxTreeList(wxTreeListCtrl):

    def __init__(self, *arguments, **keywords):
        wxTreeListCtrl.__init__ (self, *arguments, **keywords)
        EVT_TREE_ITEM_EXPANDING(self, self.GetId(), self.OnExpanding)
 

    def OnExpanding(self, event):
        """
          Load the items in the tree only when they are visible.
        """
        arguments = {'node':TreeNode (event.GetItem(), self),
                     'event':Globals.repository.find('//parcels/OSAF/framework/blocks/Events/GetTreeListData'),
                     'type':'Normal'}
        notification = Notification('chandler/GetTreeListData', None, None)
        notification.SetData(arguments)
        Globals.topView.dispatchEvent(notification)


class TreeList(RectContainer):
    def renderOneBlock(self, parent, parentWindow):
        treeList = wxTreeList(parentWindow, Block.getwxID(self))
        info = wxTreeListColumnInfo()
        for x in range(len(self.columnHeadings)):
            info.SetText(self.columnHeadings[x])
            info.SetWidth(self.columnWidths[x])
            treeList.AddColumnInfo(info)

        arguments = {'node':TreeNode (None, treeList),
                     'event':Globals.repository.find('//parcels/OSAF/framework/blocks/Events/GetTreeListData'),
                     'type':'Normal'}
        notification = Notification("chandler/GetTreeListData", None, None)
        notification.SetData(arguments)
        Globals.topView.dispatchEvent(notification)

        if isinstance (parent, wxSizerPtr):
            parent.Add(treeList, 1, self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return treeList, None, None


