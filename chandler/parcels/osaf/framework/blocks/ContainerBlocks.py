
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
    def Render (self, parent, parentWindow):
        (parent, parentWindow) = self.RenderOneBlock (parent, parentWindow)
        """
          Store the wxWindows version of the object in the association, so
        given the block we can find the associated wxWindows object.
        """
        assert (not Globals.association.has_key(self.getUUID()))
        Globals.association[self.getUUID()] = parent
        for child in self.childrenBlocks:
            child.Render (parent, parentWindow)


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
    def RenderOneBlock (self, parent, parentWindow):
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
        return sizer, parentWindow


class StaticText(RectContainer):
    def RenderOneBlock (self, parent, parentWindow):
        assert isinstance (parent, wxSizerPtr) #must be in a container
        if self.alignment == "Left":
            style = wxALIGN_LEFT
        elif self.alignment == "Center":
            style = wxALIGN_CENTRE
        elif self.aignment == "Right":
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
        return None, None
        
     
class Menu(ContainerChild):
    def RenderOneBlock(self, parent, parentWindow):
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
        return menu, parentWindow

        
class MenuItem(ContainerChild):
    def RenderOneBlock(self, parent, parentWindow):
        assert isinstance (parent, wxMenu)
        title = self.title
        if len(self.accel) > 0:
            title = title + "\tChtrl+" + self.accel
        if self.menuItemKind == "Separator":
            parent.AppendSeparator()
        elif self.menuItemKind == "Normal":
            parent.Append(0, title, self.helpString)
        elif self.menuItemKind == "Check":
            parent.AppendCheckItem(0, title, self.helpString)
        elif self.menuItemKind == "Radio":
            parent.AppendRadioItem(0, title, self.helpString)
        return None, None


class TreeList(RectContainer):
    def RenderOneBlock(self, parent, parentWindow):
        treeList = wxTreeListCtrl(parentWindow)
        info = wxTreeListColumnInfo()
        for x in range(len(self.columnHeadings)):
            info.SetText(self.columnHeadings[x])
            info.SetWidth(self.columnWidths[x])
            treeList.AddColumnInfo(info)
        
        parent.Add(treeList, 1, self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return None, None


class EditText(RectContainer):
    def __init__(self, *arguments, **keywords):
        super (EditText, self).__init__ (*arguments, **keywords)
