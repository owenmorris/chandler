
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
        if window:
            UUID = self.getUUID()
            assert not Globals.association.has_key(UUID)
            Globals.association[UUID] = window
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
        parent.Add(staticText, int(self.stretchFactor), 
                   self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return staticText, None, None
        
     
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

    def renderOneBlock(self, parent, parentWindow):
        assert isinstance (parent, wxSizerPtr) #must be in a container
        
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
                               style)

        editText.SetFont(Font (self.characterStyle))
        parent.Add(editText, int(self.stretchFactor), 
                   self.Calculate_wxFlag(), self.Calculate_wxBorder())
        return editText, None, None
