
from Block import Block
from wxPython.wx import *

class ContainerChild(Block):
    def Render (self, parent, parentWindow):
        (parent, parentWindow) = self.RenderOneBlock (parent, parentWindow)
        if self.hasAttributeValue ('childrenBlocks'):
            for child in self.childrenBlocks:
                child.RenderOneBlock (parent, parentWindow)

    def Calculate_wxFlag (self):
        if self.alignmentEnum == 'grow':
            flag = wxGROW
        elif self.alignmentEnum == 'growConstrainAspectRatio':
            flag = wxSHAPED
        elif self.alignmentEnum == 'alignCenter':
            flag = wxALIGN_CENTER
        elif self.alignmentEnum == 'alignCenterTop':
            flag = wxALIGN_TOP
        elif self.alignmentEnum == 'alignCenterLeft':
            flag = wxALIGN_LEFT
        elif self.alignmentEnum == 'alignCenterBottom':
            flag = wxALIGN_BOTTOM
        elif self.alignmentEnum == 'alignCenterRight':
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


class BoxContainer(ContainerChild):
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
    

class StaticText(ContainerChild):
    def RenderOneBlock (self, parent, parentWindow):
        staticText = wxStaticText (parentWindow,
                                   -1,
                                   "Test",
                                   wxDefaultPosition,
                                   (self.minimumSize.width, self.minimumSize.height))

        """
          I think sizers should always live in containers, but
        I'm not completely sure -- DJA
        """
        assert isinstance (parent, wxSizerPtr)
        parent.Add(staticText, 1, self.Calculate_wxFlag(), self.Calculate_wxBorder())

        
class EditText(ContainerChild):
    def __init__(self, *arguments, **keywords):
        super (EditText, self).__init__ (*arguments, **keywords)
