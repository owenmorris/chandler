__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
from osaf.framework.blocks.Block import Block as Block

class TabbedView(ContainerBlocks.TabbedContainer):
    def onSelectItemEvent(self, notification):
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
            self.parentBlock.widget.Freeze()
            if not found:
                page = self.widget.GetPage(activeTab)
                previousChild = self.childrenBlocks.previous(page.blockItem)
                page.blockItem.parentBlock = None
    
                item.parentBlock = self 
                self.childrenBlocks.placeItem(item, previousChild)
                item.render()                
                item.widget.SetSize (self.widget.GetClientSize())                
            self.synchronizeWidget()
            self.parentBlock.widget.Thaw()

    def onNewEvent (self, notification):
        "Create a new tab"
        originalItem = Globals.repository.findPath('parcels/osaf/views/content/UntitledView')
        name = self._getUniqueName("Untitled")
        newItem = originalItem.copy(name, self)
        newItem.contents.displayName = name
        
        self.widget.selectedTab = self.widget.GetPageCount()
        newItem.parentBlock = self
        self.parentBlock.widget.Freeze()
        newItem.render()
        self.synchronizeWidget()
        self.parentBlock.widget.Thaw()
        self.PostEventByName ('SelectItemBroadcast', {'item':newItem})

    def onCloseEvent (self, notification):
        """
          Will either close the current tab (if not data is present
        in the sender) or will close the tab specified by data.
        """
        try:
            item = notification.data['sender'].data
        except AttributeError:
            pageIndex = self.widget.GetSelection()
        else:
            for tabIndex in range (self.widget.GetPageCount()):
                tabName = self.widget.GetPageText(tabIndex)
                if tabName == self._getBlockName(item):
                    found = True
                    pageIndex = tabIndex
            if not found:
                # Tab isn't actually open
                return
        if pageIndex == self.widget.GetSelection():
            if pageIndex == (self.widget.GetPageCount() - 1):
                self.widget.selectedTab = pageIndex - 1
            else:
                self.widget.selectedTab = pageIndex
        elif pageIndex < self.widget.GetSelection():
            self.widget.selectedTab = self.widget.GetSelection() - 1
        page = self.widget.GetPage(pageIndex)
        page.blockItem.parentBlock = None
        self.parentBlock.widget.Freeze()        
        self.synchronizeWidget()
        self.parentBlock.widget.Thaw()
        self.PostEventByName ('SelectItemBroadcast',
                              {'item':self.widget.GetPage(self.widget.selectedTab).blockItem})

    def onOpenEvent (self, notification):
        "Opens the chosen item in a new tab"
        item = notification.data['sender'].data
        found = False
        for tabIndex in range (self.widget.GetPageCount()):
            tabName = self.widget.GetPageText (tabIndex)
            if tabName == self._getBlockName(item):
                found = True
                self.widget.SetSelection(tabIndex)
        if not found:
            self.widget.selectedTab = self.widget.GetPageCount()
            item.parentBlock = self
            self.parentBlock.widget.Freeze()
            item.render()
            item.widget.SetSize (self.widget.GetClientSize())
            self.synchronizeWidget()
            self.parentBlock.widget.Thaw()
            self.PostEventByName ('SelectItemBroadcast', {'item':item})
        
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

        
