__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals


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
        itemUUID = Globals.repository.find (notification.data['uuid'])
        if notification.getItemName() == "item_changed":
            item = Globals.repository.find (itemUUID)
            itemUUID = item.parent().getUUID()
        counterpart = Globals.repository.find (self.counterpartUUID)
        if counterpart.hasKey ('openedContainers', itemUUID):
            self.scheduleUpdate = False

