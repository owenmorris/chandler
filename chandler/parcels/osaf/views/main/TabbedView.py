__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ControlBlocks as ControlBlocks
from osaf.framework.blocks.Node import Node as Node
from osaf.framework.blocks.Block import Block as Block

class TabbedView(ControlBlocks.TabbedContainer):
    def onSelectionChangedEvent(self, notification):
        item = notification.data['item']
        if isinstance(item, Block):
            self.ChangeCurrentTab(item)

    def ChangeCurrentTab(self, item):
        if hasattr (self, 'widget'):
            # tabbed container hasn't been rendered yet
            activeTab = self.widget.GetSelection()
            itemName = item.getItemDisplayName()
            found = False
            for tabIndex in range(self.widget.GetPageCount()):
                tabName = self.widget.GetPageText(tabIndex)
                if tabName == itemName:
                    found = True
                    self.widget.SetSelection(tabIndex)
            if not found:
                self.tabNames[activeTab] = itemName
                page = self.widget.GetPage(activeTab)
                previousChild = self.childrenBlocks.previous(page.blockItem)
                page.blockItem.parentBlock = None
    
                item.parentBlock = self 
                self.childrenBlocks.placeItem(item, previousChild)
                item.render()                
                item.widget.SetSize (self.widget.GetClientSize())                
            self.synchronizeWidget()

    def onNewEvent (self, notification):
        "Create a new tab"
        kind = Globals.repository.findPath("parcels/osaf/framework/blocks/HTML")
        name = self._getUniqueName("untitled")
        self.widget.selectedTab = len(self.tabNames)
        self.tabNames.append(name)
        item = kind.newItem(name, self)
        item.url = ""
        item.parentBlock = self
        item.render()
        self.synchronizeWidget()

    def onCloseEvent (self, notification):
        "Close the current tab"
        selection = self.widget.GetSelection()
        self.tabNames.remove(self.tabNames[selection])
        page = self.widget.GetPage(selection)
        if selection > (len(self.tabNames) - 1):
            self.widget.selectedTab = selection - 1
        else:
            self.widget.selectedTab = selection
        page.blockItem.parentBlock = None
        self.synchronizeWidget()
        
    def onCloseEventUpdateUI(self, notification):
        notification.data['Enable'] = (len(self.tabNames) > 1)
        
    def _getUniqueName (self, name):
        if not self.hasChild(name):
            return name
        number = 1
        while self.hasChild(name + str(number)):
            number += 1
        return name + str(number)

        
