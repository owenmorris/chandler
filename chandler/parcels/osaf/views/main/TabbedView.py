__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
from osaf.framework.blocks.Block import Block as Block

class TabbedView(ContainerBlocks.TabbedContainer):
    def onSelectionChangedEvent(self, notification):
        item = notification.data['item']
        if isinstance(item, Block):
            self.ChangeCurrentTab(item)

    def ChangeCurrentTab(self, item):
        if hasattr (self, 'widget'):
            # tabbed container hasn't been rendered yet
            activeTab = self.widget.GetSelection()
            itemName = self._getBlockName(item)
            found = False
            for tabIndex in range(self.widget.GetPageCount()):
                tabName = self.widget.GetPageText(tabIndex)
                if tabName == itemName:
                    found = True
                    self.widget.SetSelection(tabIndex)
            if not found:
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
        originalItem = Globals.repository.findPath('parcels/osaf/views/content/UntitledView')
        name = self._getUniqueName("Untitled")
        newItem = originalItem.copy(name, self)
        newItem.contents.displayName = name
        
        self.widget.selectedTab = self.widget.GetPageCount()
        newItem.parentBlock = self
        newItem.render()
        self.synchronizeWidget()
        self.Post (Globals.repository.findPath ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                   {'item':newItem})

    def onCloseEvent (self, notification):
        "Close the current tab"
        selection = self.widget.GetSelection()
        page = self.widget.GetPage(selection)
        if selection == (self.widget.GetPageCount() - 1):
            self.widget.selectedTab = selection - 1
        else:
            self.widget.selectedTab = selection
        page.blockItem.parentBlock = None
        self.synchronizeWidget()
        self.Post (Globals.repository.findPath ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                   {'item':self.widget.GetPage(self.widget.selectedTab).blockItem})
        
    def onCloseEventUpdateUI(self, notification):
        notification.data['Enable'] = (self.widget.GetPageCount() > 1)
        
    def _getUniqueName (self, name):
        if not self.hasChild(name):
            return name
        number = 1
        uniqueName = name + "-" + str(number)
        while self.hasChild(uniqueName):
            number += 1
            uniqueName = name + "-" + str(number)
        return uniqueName

        
