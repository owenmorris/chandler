__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Container import Container
from wxPython.wx import *

class BoxContainer(Container):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/BoxContainer'

    def Render(self, parent, parentSizer):
        sizer = wxBoxSizer(self.style['orientation'])
        parentSizer.Add(sizer, self.style['weight'], self.style['flag'], 
                        self.style['border'])
        self.RenderChildren(parent, sizer)
        
    