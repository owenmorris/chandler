__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.gizmos import *


class MultipleColumnTreeCtrl(wxTreeListCtrl):
    def __init__(self, parent, numColumns, columnTitles):
        wxTreeListCtrl.__init__(self, parent)

        # FIXME:  Should calculate the actual size available
        width = 300
        column = 0
        while column < numColumns:
            self.AddColumn(columnTitles[column])
            self.SetColumnWidth(column, width)
            column += 1
                    
    def AddNewRoot(self, text):
        """
          Adds the specified root to the tree ctrl.
        """
        rootId = self.AddRoot(text)
        self.SetItemText(rootId, "", 1)
        return rootId

    def AddNewItem(self, parent, itemText, valueTextList, numColumns = 2):
        """
          Adds the supplied item to the tree ctrl.  itemText is the text for
        the tree ctrl and valueTextList is a list containing text entries for
        each of the value columns.
        """
        itemId = self.AppendItem(parent, itemText)
        col = 1
        while col < numColumns:
            self.SetItemText(itemId, valueTextList[col - 1], col)
            col += 1
        return itemId

