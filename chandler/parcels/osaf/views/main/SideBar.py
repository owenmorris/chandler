__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import OSAF.framework.blocks.ControlBlocks as ControlBlocks

        
class SideBar(ControlBlocks.Tree):
    def renderOneBlock(self, parent, parentWindow):
        returnArguments = ControlBlocks.Tree.renderOneBlock(self, parent, parentWindow)
        self.showOrHideSideBar(returnArguments[0])
        return returnArguments
    
    def OnViewSideBarEvent(self, notification):
        self.open = not self.open
        self.showOrHideSideBar(Globals.association[self.itsUUID])

    def showOrHideSideBar(self, sidebar):
        if sidebar.IsShown() != self.open:
            sidebar.Show(self.open)
            parentWindow = Globals.association[self.parentBlock.itsUUID]
            if self.open:
                self.parentBlock.addToContainer(parentWindow, sidebar, None, None, None)
            else:
                self.parentBlock.removeFromContainer(parentWindow, sidebar, False)
            self.parentBlock.handleChildren(parentWindow)
            
    def OnViewSideBarEventUpdateUI(self, notification):
        notification.data['Check'] = self.open


class SideBarDelegate:
    def ElementParent(self, element):
        return element.parent

    def ElementChildren(self, element):
        return element.children

    def ElementCellValues(self, element):
        return [element.getItemDisplayName()]

    def ElementHasChildren(self, element):
        return len(element.children) != 0

    def NeedsUpdate(self, notification):
        """
          We need to update the display when any opened URL node has
        a child that has been changed. When items are are added or deleted
        their parents are modified. However, when they are changed we need
        to get their parent.
        """
        itemUUID = notification.data['uuid']
        if notification.event.itsName == "item_changed":
            item = Globals.repository.find (itemUUID)
            itemUUID = item.itsParent.itsUUID
        counterpart = Globals.repository.find (self.counterpartUUID)
        if counterpart.openedContainers.has_key (itemUUID):
            self.scheduleUpdate = True

