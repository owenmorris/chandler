__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.framework.blocks.ControlBlocks as ControlBlocks
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.Trunk as Trunk
import osaf.contentmodel.ItemCollection as ItemCollection
import wx


class SidebarAttributeDelegate (ControlBlocks.AttributeDelegate):
    def ReadOnly (self, row, column):
        """
          Second argument should be True if all cells have the first value
        """
        (item, attribute) = self.GetElementValue (row, column)
        try:
            readOnly = getattr (item, 'outOfTheBoxCollection')
        except AttributeError:
            readOnly = False
        return readOnly, False

class wxSidebar(ControlBlocks.wxTable):
    def OnRequestDrop(self, x, y):
        self.dropRow = self.YToRow(y)
        if self.dropRow == wx.NOT_FOUND:
            return False
        return True
        
    def AddItem(self, itemUUID):
        item = self.blockItem.findUUID(itemUUID)
        self.blockItem.contents[self.dropRow].add(item)
    
    def OnItemDrag(self, event):
        # @@@ You currently can't drag out of the sidebar
        pass

    
class Sidebar (ControlBlocks.Table):
    def instantiateWidget (self):
        return wxSidebar (self.parentBlock.widget, Block.Block.getWidgetID(self))    

    def onKindParameterizedEvent (self, event):
        # @@@ Temporary hack until we have persistence in the toolbar.
        # Whenever you get an event to select a kind of filter make sure that
        # the toolbar click state is in sync with the desired filter
        toolbar = Block.Block.findBlockByName('ApplicationBar')
        for childBlock in toolbar.dynamicChildren:
            try:
                childBlock.event
            except AttributeError:
                pass
            else:
                if childBlock.event == event:
                    if not childBlock.widget.IsToggled():
                        toolbar.widget.ToggleTool(childBlock.toolID, True)
                
        self.filterKind = event.kindParameter
        self.postEventByName("SelectItemBroadcast", {'item':self.selectedItemToView})

    def onRequestSelectSidebarItemEvent (self, event):
        # Request the sidebar to change selection
        # Item specified is usually by name
        try:
            item = event.arguments['item']
        except KeyError:
            # find the item by name
            itemName = event.arguments['itemName']
            for item in self.contents:
                if item.displayName == itemName:
                    break
            else:
                return

        self.postEventByName("SelectItemBroadcast", {'item':item})


class SidebarTrunkDelegate(Trunk.TrunkDelegate):
    def _mapItemToCacheKeyItem(self, item):
        key = item
        if isinstance (item, ItemCollection.ItemCollection):
            filterKind = Block.Block.findBlockByName ("Sidebar").filterKind
            if not filterKind is None:
                tupleKey = (item.itsUUID, filterKind.itsUUID)
                try:
                    key = self.itemTupleKeyToCacheKey [tupleKey]
                except KeyError:
                    """
                      We need to make a new filtered item collection that depends
                      upon the unfiltered collection. Unfortunately, making a new
                      ItemCollection with a rule whose results include all items
                      in the original ItemCollection has a problem: when the results
                      in the unfiltered ItemCollection change we don't get notified.

                      Alternatively we make a copy of the ItemCollection (and it's
                      rule) which has another problem: When the rule in the original
                      ItemCollection change we don't update our copied rule.                      
                    """
                    key = ItemCollection.ItemCollection (view=self.itsView)
                    key._rule = item._rule
                    key._inclusions = item._inclusions
                    key._exclusions = item._exclusions
                    key.displayName = item.displayName + u" filtered by " + filterKind.displayName
                    key.addFilterKind (filterKind)
                    self.itemTupleKeyToCacheKey [tupleKey] = key
        return key

    def _makeTrunkForCacheKey(self, keyItem):
        if isinstance (keyItem, ItemCollection.ItemCollection):
            sidebar = Block.Block.findBlockByName ("Sidebar")
            if (sidebar.filterKind is self.findPath ("//parcels/osaf/contentmodel/calendar/CalendarEventMixin") and
                keyItem.displayName != u"In filtered by Calendar Event Mixin Kind" and
                keyItem.displayName != u"Out filtered by Calendar Event Mixin Kind"):
                templatePath = self.calendarTemplatePath
            else:
                templatePath = self.tableTemplatePath
            trunk = self.findPath (templatePath)
        else:
            trunk = keyItem
        
        assert isinstance (trunk, Block.Block)
        return self._copyItem(trunk, onlyIfReadOnly=True)

    def _setContentsOnTrunk(self, trunk, item, keyItem):
        trunk.postEventByName("SetContents", {'item':keyItem})


class CPIATestSidebarTrunkDelegate(Trunk.TrunkDelegate):
    def _makeTrunkForCacheKey(self, keyItem):
        if isinstance (keyItem, ItemCollection.ItemCollection):
            trunk = self.findPath (self.templatePath)
        else:
            trunk = keyItem
        
        assert isinstance (trunk, Block.Block)
        return self._copyItem(trunk, onlyIfReadOnly=True)
