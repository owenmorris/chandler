__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.framework.blocks.ControlBlocks as ControlBlocks
import osaf.framework.blocks.Block as Block
import wx


class wxSidebar(ControlBlocks.wxTable):
    def OnRequestDrop(self, x, y):
        self.dropRow = self.YToRow(y)
        if self.dropRow == wx.NOT_FOUND:
            return False
        return True
        
    def AddItem(self, itemUUID):
        item = self.blockItem.findUUID(itemUUID)
        self.blockItem.contents[self.dropRow].contents.add(item)
    
    def OnItemDrag(self, event):
        # @@@ You currently can't drag out of the sidebar
        pass

    
class Sidebar (ControlBlocks.Table):
    def instantiateWidget (self):
        return wxSidebar (self.parentBlock.widget, Block.Block.getWidgetID(self))    

    def onKindParameterizedEvent (self, event):
        kindParameter = event.kindParameter

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

    def onRequestSelectSidebarItemEvent (self, event):
        # Request the sidebar to change selection
        # Item specified is usually by name
        try:
            item = event.arguments['item']
        except KeyError:
            # find the item by name
            itemName = event.arguments['itemName']
            for item in self.contents:
                if item.itsName == itemName:
                    event.arguments['item'] = item
                    break
            else:
                return

        self.onSelectItemEvent (event)

