
from Block import Block
from wxPython.wx import *

class ContainerChild(Block):

    def __init__(self, *arguments, **keywords):
        super (ContainerChild, self).__init__ (*arguments, **keywords)
 
class BoxContainer(ContainerChild):
    def __init__(self, *arguments, **keywords):
        super (BoxContainer, self).__init__ (*arguments, **keywords)
 
    def Render (self, parent):
        platformObject = self.RenderOneBlock (parent)
        if self.hasAttributeValue ('childrenBlocks'):
            for child in self.childrenBlocks:
                child.RenderOneBlock (platformObject)


    def RenderOneBlock (self, parent):
        if self.orientationEnum == 'Horizontal':
            orientation = wxHORIZONTAL
        else:
            orientation = wxVERTICAL

        sizer = wxBoxSizer(orientation)
        sizer.SetMinSize((self.minimumSize.width, self.minimumSize.height))

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

        i = 5
        #parent.add(sizer, 1, flag
