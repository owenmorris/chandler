
import application.Globals as Globals
from Block import Block
from wxPython.wx import *
from wxPython.gizmos import *

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
        UUID = self.getUUID()
        assert not Globals.association.has_key(UUID)
        Globals.association[UUID] = parent
        window.counterpartUUID = UUID
        for child in self.childrenBlocks:
            child.render (parent, parentWindow)


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

        if isinstance (parent, wxWindowPtr):
            parent.SetSizer (sizer)
        else:
            assert isinstance (parent, wxSizerPtr)
            parent.Add(sizer, 1, self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return sizer, sizer, parentWindow


class StaticText(RectContainer):
    def renderOneBlock (self, parent, parentWindow):
        assert isinstance (parent, wxSizerPtr) #must be in a container
        if self.alignment == "Left":
            style = wxALIGN_LEFT
        elif self.alignment == "Center":
            style = wxALIGN_CENTRE
        elif self.alignment == "Right":
            style = wxALIGN_RIGHT

        staticText = wxStaticText (parentWindow,
                                   -1,
                                   self.title,
                                   wxDefaultPosition,
                                   (self.minimumSize.width, self.minimumSize.height),
                                   style)

        staticText.SetFont(Font (self.characterStyle))
        parent.Add(staticText, int(self.stretchFactor), 
                   self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return staticText, None, None
        
     
class Menu(ContainerChild):
    def renderOneBlock(self, parent, parentWindow):
        frame = parentWindow.GetParent()
        while not isinstance (frame, wxFrame):
            frame = frame.GetParent()
        menuBar = frame.GetMenuBar()
        if not menuBar:
            menuBar = wxMenuBar()
            frame.SetMenuBar(menuBar)
        assert menuBar.FindMenu(self.title) == wxNOT_FOUND
        menu = wxMenu()
        menuBar.Insert(menuBar.GetMenuCount(), menu, self.title)
        assert isinstance (parent, wxSizerPtr)
        return menu, menu, parentWindow

        
class MenuItem(ContainerChild):
    def __init__(self, *arguments, **keywords):
        super (ContainerChild, self).__init__ (*arguments, **keywords)
        #self.event = None # Big hack, should set in XML DJA

    def renderOneBlock(self, parent, parentWindow):

        title = self.title
        if len(self.accel) > 0:
            title = title + "\tChtrl+" + self.accel

        id = 0
        if self.hasAttributeValue ("event"):  # Repository bug/feature -- DJA
            id = self.event.getwxID()
    
        if self.menuItemKind == "Separator":
            id = wxID_SEPARATOR
            kind = wxITEM_SEPARATOR
        elif self.menuItemKind == "Normal":
            kind = wxITEM_NORMAL
        elif self.menuItemKind == "Check":
            kind = wxITEM_CHECK
        elif self.menuItemKind == "Radio":
            kind = wxITEM_RADIO
        elif __debug__:
            assert (False)        
            
        assert isinstance (parent, wxMenu)
        menuItem = wxMenuItem (parent, id, title, self.helpString, kind)
        parent.AppendItem (menuItem)
        return menuItem, None, None


class TreeList(RectContainer):
    def renderOneBlock(self, parent, parentWindow):
        treeList = wxTreeListCtrl(parentWindow)
        info = wxTreeListColumnInfo()
        for x in range(len(self.columnHeadings)):
            info.SetText(self.columnHeadings[x])
            info.SetWidth(self.columnWidths[x])
            treeList.AddColumnInfo(info)
        
        parent.Add(treeList, 1, self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return treeList, None, None


class EditText(RectContainer):
    def __init__(self, *arguments, **keywords):
        super (EditText, self).__init__ (*arguments, **keywords)
