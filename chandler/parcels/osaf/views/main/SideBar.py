__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ControlBlocks as ControlBlocks
import wx


class SideBarDelegate (ControlBlocks.AttributeDelegate):
    def GetElementValue (self, row, column):
        item = self.blockItem.contents [row]
        try:
            item = item.contents
        except AttributeError:
            pass
        return item, self.blockItem.columnAttributeNames [column]

    def SetElementValue (self, row, column, value):
        view = self.blockItem.contents[row]
        item = view
        try:
            item = item.contents
        except AttributeError:
            pass
        attributeName = self.blockItem.columnAttributeNames [column]
        item.setAttributeValue (attributeName, value)
        view.synchronizeWidget()


class Sidebar (ControlBlocks.Table):
    def onKindParameterizedEvent (self, notification):
        kindParameter = notification.event.kindParameter

        self.contents.beginUpdate()
        for view in self.contents:
            view.contents.removeFilterKind (None)
            if kindParameter:
                view.contents.addFilterKind (kindParameter)
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

        # Got the item. First tell ourself about it.
        self.onSelectionChangedEvent (notification)

        # Next broadcast inside our boundary to tell dependent
        self.Post (Globals.repository.findPath \
                   ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                   {'item':item})


