__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Block import Block
from wxPython.wx import *

class Container(Block):
    def RenderChildren(self, parent, sizer):
        try:
            children = self._children
        except:
            return # Container has no children
        childList = []
        for key in children.keys():
            childItem = children[key]
            childList.append(childItem)
        childList.sort(self.SortChildren)
        for childItem in childList:
            childItem.Render(parent, sizer)

    def SortChildren(self, itemOne, itemTwo):
        return itemOne.positionInParent - itemTwo.positionInParent
    