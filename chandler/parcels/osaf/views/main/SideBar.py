__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.blocks.ControlBlocks import AttributeDelegate


class SideBarDelegate (AttributeDelegate):
    def GetElementValue (self, row, column):
        item = self.blockItem.contents [row]
        try:
            item = item.contents
        except AttributeError:
            pass
        return item, self.blockItem.columnAttributeNames [column]

    def SetElementValue (self, row, column, value):
        view = self.blockItem.contents[row]
        item = view
        try:
            item = item.contents
        except AttributeError:
            pass
        attributeName = self.blockItem.columnAttributeNames [column]
        item.setAttributeValue (attributeName, value)
        view.synchronizeWidget()

