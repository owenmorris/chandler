__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals


class RepositoryDelegate:
    def ElementParent(self, element):
        try:
            return element.getItemParent()
        except AttributeError:
            return None

    def ElementChildren(self, element):
        if element:
            return element
        else:
            return Globals.repository.view

    def ElementCellValues(self, element):
        cellValues = []
        if element == Globals.repository.view:
            cellValues.append ("//")
        else:
            cellValues.append (element.getItemName())
            cellValues.append (str (element.getItemDisplayName()))
            try:
                cellValues.append (element.kind.getItemName())
            except AttributeError:
                cellValues.append ('(kindless)')
            cellValues.append (str (element.getUUID()))
            cellValues.append (str (element.getItemPath()))
        return cellValues

    def ElementHasChildren(self, element):
        if element == Globals.repository.view:
            return True
        else:
            return element.hasChildren()

    def NeedsUpdate(self, notification):
        """
          We need to update the display when any container has
        a child that has been changed. When items are are added
        or modified we can ask for their parent. However, when
        they are deleted we can't access them, so the repository
        sends us their parent.
        """
        try:
            parentUUID = notification.data['parent']
        except KeyError:
            item = Globals.repository.find (notification.data['uuid'])
            parentUUID = item.getItemParent().getUUID()
        counterpart = Globals.repository.find (self.counterpartUUID)
        if self.hasKey ('openedContainers', parentUUID):
            self.scheduleUpdate = True
