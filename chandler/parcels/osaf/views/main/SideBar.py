__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ControlBlocks as ControlBlocks
import osaf.framework.blocks.Block as Block
import wx


class SideBarDelegate (ControlBlocks.AttributeDelegate):
    def GetElementValue (self, row, column):
        item = self.blockItem.contents [row]
        try:
            item = item.contents
        except AttributeError:
            pass
        return item, self.blockItem.columnData [column]

    def SetElementValue (self, row, column, value):
        view = self.blockItem.contents[row]
        item = view
        try:
            item = item.contents
        except AttributeError:
            pass
        attributeName = self.blockItem.columnData [column]
        item.setAttributeValue (attributeName, value)
        view.synchronizeWidget()
        

class wxSidebar(ControlBlocks.wxTable):
    def OnRequestDrop(self, x, y):
        self.dropRow = self.YToRow(y)
        if self.dropRow == wx.NOT_FOUND:
            return False
        return True
        
    def AddItem(self, itemUUID):
        item = Globals.repository.findUUID(itemUUID)
        self.blockItem.contents[self.dropRow].contents.add(item)
    
    def OnItemDrag(self, event):
        # @@@ You currently can't drag out of the sidebar
        pass

    
class Sidebar (ControlBlocks.Table):
    def instantiateWidget (self):
        return wxSidebar (self.parentBlock.widget, Block.Block.getWidgetID(self))    

    def onKindParameterizedEvent (self, notification):
        kindParameter = notification.event.kindParameter

        self.contents.beginUpdate()
        for view in self.contents:
            try:
                contents = view.contents
            except AttributeError:
                pass
            else:
                contents.removeFilterKind (None)
                if kindParameter:
                    contents.addFilterKind (kindParameter)
        self.contents.endUpdate()

    def onRequestSelectSidebarItemEvent (self, notification):
        # Request the sidebar to change selection
        # Item specified is usually by name
        try:
            item = notification.data['item']
        except KeyError:
            # find the item by name
            itemName = notification.data['itemName']
            for item in self.contents:
                if item.itsName == itemName:
                    notification.data['item'] = item
                    break
            else:
                return

        self.onSelectItemEvent (notification)

