
from Block import Block
from wxPython.wx import *

class ContainerChild(Block):

    def __init__(self, *arguments, **keywords):
        super (ContainerChild, self).__init__ (*arguments, **keywords)
 
    def RenderOneBlock (self, parent):
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
        
        return flag, border


class BoxContainer(ContainerChild):
    def __init__(self, *arguments, **keywords):
        super (BoxContainer, self).__init__ (*arguments, **keywords)
 
    def Render (self, parent):
        platformObject = self.RenderOneBlock (parent)
        if self.hasAttributeValue ('childrenBlocks'):
            for child in self.childrenBlocks:
                child.RenderOneBlock (platformObject)


    def RenderOneBlock (self, parent):
        (flag, border) = ContainerChild.RenderOneBlock (self, parent)
        if self.orientationEnum == 'Horizontal':
            orientation = wxHORIZONTAL
        else:
            orientation = wxVERTICAL

        sizer = wxBoxSizer(orientation)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))

        sizer.Add (wxTextCtrl (parent, 100, "text", wxDefaultPosition, wxSize (100, 24)))
        if isinstance (parent, wxFrame):
            parent.SetSizer (sizer)
        else:
            assert isinstance (parent, wxSizer)
            parent.add(sizer, 1, flag, int (border))

class StaticText(ContainerChild):
    def __init__(self, *arguments, **keywords):
        super (BoxContainer, self).__init__ (*arguments, **keywords)

class EditText(ContainerChild):
    def __init__(self, *arguments, **keywords):
        super (BoxContainer, self).__init__ (*arguments, **keywords)
