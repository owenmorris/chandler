__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ControlBlocks as ControlBlocks
from osaf.framework.blocks.Node import Node as Node
from osaf.framework.blocks.Block import Block as Block
from repository.util.UUID import UUID

class TabbedView(ControlBlocks.TabbedContainer):
    def OnSelectionChangedEvent(self, notification):
        node = notification.data['item']
        if node and isinstance(node, Node):
            newChild = node.item
            if isinstance(newChild, Block):
                try:
                    tabbedContainer = Globals.association [self.itsUUID]
                except KeyError:
                    return  # tabbed container hasn't been rendered yet
                activeTab = tabbedContainer.GetSelection()
                self.tabNames[activeTab] = self.getUniqueName(node.getItemDisplayName())
                page = tabbedContainer.GetPage(activeTab)
                item = Globals.repository.find(page.blockUUID)
                previousChild = self.childrenBlocks.previous(item)
                item.parentBlock = None

                newChild.parentBlock = self                
                self.childrenBlocks.placeItem(newChild, previousChild)
                newChild.render()                
                wxNewChild = Globals.association [newChild.itsUUID]
                wxNewChild.SetSize (tabbedContainer.GetClientSize())                
                Globals.mainView.onSetActiveView(newChild)
                self.synchronizeWidget()

    def OnNewEvent (self, notification):
        "Create a new tab"
        tabbedContainer = Globals.association[self.itsUUID]
        kind = Globals.repository.find("parcels/osaf/framework/blocks/HTML")
        name = self.getUniqueName("untitled")
        tabbedContainer.selectedTab = len(self.tabNames)
        self.tabNames.append(name)
        item = kind.newItem(name, self)
        item.url = ""
        item.parentBlock = self
        item.render()
        self.synchronizeWidget()

    def OnCloseEvent (self, notification):
        "Close the current tab"
        tabbedContainer = Globals.association[self.itsUUID]
        selection = tabbedContainer.GetSelection()
        self.tabNames.remove(self.tabNames[selection])
        page = tabbedContainer.GetPage(selection)
        if selection > (len(self.tabNames) - 1):
            tabbedContainer.selectedTab = selection - 1
        else:
            tabbedContainer.selectedTab = selection
        item = Globals.repository.find(page.blockUUID)
        item.parentBlock = None
        self.synchronizeWidget()
        
    def OnCloseEventUpdateUI(self, notification):
        notification.data['Enable'] = (len(self.tabNames) > 1)
        
    def getUniqueName (self, name):
        if not self.hasChild(name):
            return name
        number = 1
        while self.hasChild(name + str(number)):
            number += 1
        return name + str(number)

        
