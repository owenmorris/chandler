__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from Container import Container
from wxPython.wx import *

class Document(Container):
    def GetSchemaLocation(self):
        return '//Schema/DocumentSchema/Document'

    def Render(self, view):
        view.DestroyChildren()
        sizer = wxBoxSizer(self.style['orientation'])
        self.RenderChildren(view, sizer)
        view.SetSizerAndFit(sizer)
        return view
 