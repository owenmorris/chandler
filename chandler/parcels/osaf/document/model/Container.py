__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Block import Block
from wxPython.wx import *

class Container(Block):
    def RenderChildren(self, parent, sizer):
        childrenIterator = self.iterChildren()
        for childItem in childrenIterator:
            childItem.Render(parent, sizer)
    