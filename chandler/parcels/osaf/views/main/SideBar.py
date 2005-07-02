__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.views.main"

import osaf.framework.blocks.ControlBlocks as ControlBlocks
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.Trunk as Trunk
import osaf.contentmodel.ItemCollection as ItemCollection
import wx
import osaf.framework.blocks.DrawingUtilities as DrawingUtilities
import os
import osaf.framework.sharing.Sharing as Sharing
from application import schema

def GetRenderEditorTextRect (rect):
    image = wx.GetApp().GetImage ("SidebarAll.png")
    width = image.GetWidth() + 2
    return wx.Rect (rect.GetLeft() + width,
                    rect.GetTop(),
                    rect.GetWidth() - (2 * width),
                    rect.GetHeight())


class SidebarElementDelegate (ControlBlocks.ListDelegate):
    def ReadOnly (self, row, column):
        """
          Second argument should be True if all cells have the first value
        """
        (item, attribute) = self.GetElementValue (row, column)
        try:
            readOnly = not item.renameable
        except AttributeError:
            readOnly = False
        return readOnly, False

    def GetElementType (self, row, column):
        return "Item"

    def GetElementValue (self, row, column):
        return self.blockItem.contents [row], self.blockItem.columnData [column]


class wxSidebar(ControlBlocks.wxTable):
    def __init__(self, *arguments, **keywords):
        super (wxSidebar, self).__init__ (*arguments, **keywords)
        gridWindow = self.GetGridWindow()
        gridWindow.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)

    def CalculateCellRect (self, row):
        cellRect = self.CellToRect (row, 0)
        cellRect.OffsetXY (self.GetRowLabelSize(), self.GetColLabelSize())
        left, top = self.CalcScrolledPosition (cellRect.GetLeft(), cellRect.GetTop())
        cellRect.SetLeft (left)
        cellRect.SetTop (top)
        return cellRect

    def wxSynchronizeWidget(self):
        sidebar = self.blockItem
        for checkedItem in sidebar.checkedItems:
            if checkedItem not in sidebar.contents:
                sidebar.checkedItems.remove (checkedItem)
        super (wxSidebar, self).wxSynchronizeWidget()

    def OnMouseEvents (self, event):
        """
          This code is tricky, tread with care -- DJA
        """
        event.Skip() #Let the grid also handle the event
        gridWindow = self.GetGridWindow()

        x, y = self.CalcUnscrolledPosition (event.GetX(), event.GetY())
        row = self.YToRow (y)
        
        cellRect = self.CalculateCellRect (row)

        if not cellRect.InsideXY (event.GetX(), event.GetY()):
            row = wx.NOT_FOUND

        image = wx.GetApp().GetImage ("SidebarAll.png")
        imageRect = wx.Rect (cellRect.GetLeft() + 1,
                             cellRect.GetTop() + (cellRect.GetHeight() - image.GetHeight()) / 2,
                             image.GetWidth(),
                             image.GetHeight())

        item, attribute = self.GetTable().GetValue (row, 0)

        if event.LeftDown():
            if (imageRect.InsideXY (event.GetX(), event.GetY())
                and isinstance (item, ItemCollection.ItemCollection)):

                if not hasattr (self, "hoverImageRow"):
                    assert not gridWindow.HasCapture()
                    gridWindow.CaptureMouse()
                    self.cellRect = cellRect
                    self.imageRect = imageRect
                    self.hoverImageRow = row
                else:
                    event.Skip (False) #Gobble the event

                self.screenChecked = not item in self.blockItem.checkedItems
                self.blockChecked = self.screenChecked
                self.buttonPressed = True
                self.RefreshRect (self.imageRect)

        elif hasattr (self, "hoverImageRow"):
            assert gridWindow.HasCapture()
            if event.LeftUp():
                if self.imageRect.InsideXY (event.GetX(), event.GetY()):
                    checkedItems = self.blockItem.checkedItems
                    if item in checkedItems:
                        checkedItems.remove (item)
                    else:
                        checkedItems.append (item)
                    sidebar = self.blockItem
                    sidebar.postEventByName ("SelectItemBroadcast", {'item':sidebar.selectedItemToView})
                    wx.GetApp().UIRepositoryView.commit()
                elif not self.cellRect.InsideXY (event.GetX(), event.GetY()):
                    self.RefreshRect (self.imageRect)
                    del self.hoverImageRow
                    gridWindow.ReleaseMouse()
                self.buttonPressed = False

            elif not event.LeftIsDown():
                if not self.cellRect.InsideXY (event.GetX(), event.GetY()):
                    self.RefreshRect (self.imageRect)
                    del self.hoverImageRow
                    self.buttonPressed = False
                    gridWindow.ReleaseMouse()

            elif (self.buttonPressed and
                  self.imageRect.InsideXY (event.GetX(), event.GetY()) !=
                  (self.screenChecked == self.blockChecked)):
                self.screenChecked = not self.screenChecked
                self.RefreshRect (self.imageRect)
            

        elif (row != wx.NOT_FOUND) and event.Moving():
            assert not hasattr (self, "hoverImageRow")
            assert not gridWindow.HasCapture()
            self.screenChecked = item in self.blockItem.checkedItems
            self.blockChecked = self.screenChecked
            self.cellRect = cellRect
            self.imageRect = imageRect
            self.hoverImageRow = row
            self.buttonPressed = False
            self.RefreshRect (self.imageRect)
            """
              Capture the mouse until we lose the hover state or mouse up
            outside  a row
            """
            gridWindow.CaptureMouse()

    def OnRequestDrop (self, x, y):
        x, y = self.CalcUnscrolledPosition(x, y)
        self.whereToDropItem = self.YToRow(y)
        if self.whereToDropItem == wx.NOT_FOUND:
            del self.whereToDropItem
            return False
        return True
        
    def AddItems (self, itemList):
        # Adding due to Drag and Drop?
        try:
            whereToDropItem = self.whereToDropItem
        except AttributeError:
            possibleCollections = self.SelectedItems()
        else:
            possibleCollections = [self.blockItem.contents[whereToDropItem]]
            self.SetRowHighlight(self.whereToDropItem, False)
            del self.whereToDropItem
        for possibleCollection in possibleCollections:
            for item in itemList:
                try:
                    possibleCollection.add(item)
                except AttributeError:
                    break # possible collection doesn't know how to 'add'
    
    def OnItemDrag (self, event):
        # @@@ You currently can't drag out of the sidebar
        pass

    def CanCopy(self):
        # You also can't Cut or Copy items from the sidebar
        return False

    def OnHover (self, x, y):
        hoverRow = self.YToRow(y)
        try:
            self.hoverRow
        except AttributeError:
            # If it's our first time hovering then set previous state to be NOT_FOUND
            self.hoverRow = wx.NOT_FOUND
        else:
            # Clear the selection colour if necessary
            if self.hoverRow != wx.NOT_FOUND and self.hoverRow != hoverRow:
                self.SetRowHighlight(self.hoverRow, False)
                
            # Colour the item if it exists and isn't already coloured
            if hoverRow != wx.NOT_FOUND and hoverRow != self.hoverRow:
                self.SetRowHighlight(hoverRow, True)
            
            # Store current state
            self.hoverRow = hoverRow
            
    def OnHoverLeave (self):
        # check if we had a hover row
        try:
            self.hoverRow
        except AttributeError:
            return
        else:
            # Clear the selection colour if necessary
            self.SetRowHighlight(self.hoverRow, False)
            
    def SetRowHighlight (self, row, highlightOn):
        if highlightOn:
            self.SetCellBackgroundColour(row, 0, wx.LIGHT_GREY)
        else:
            self.SetCellBackgroundColour(row, 0, wx.WHITE)
        # Just invalidate the changed rect

        rect = self.CalculateCellRect (row)
        self.RefreshRect(rect)
        self.Update()

class SSSidebarRenderer (wx.grid.PyGridCellRenderer):
    """
      Super specialized Sidebar Renderer, is so specialized that it works in
    only one context -- Mimi's Sidebar.
    """
    def Draw (self, grid, attr, dc, rect, row, col, isSelected):
        DrawingUtilities.SetTextColorsAndFont (grid, attr, dc, isSelected)

        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangleRect(rect)

        dc.SetBackgroundMode (wx.TRANSPARENT)
        item, attribute = grid.GetTable().GetValue (row, col)

        if isinstance (item, ItemCollection.ItemCollection):
            sidebarTPB = Block.Block.findBlockByName ("SidebarTPB")
            (filteredCollection, rerender) = sidebarTPB.trunkDelegate._mapItemToCacheKeyItem(item)
            if len (filteredCollection) == 0:
                dc.SetTextForeground (wx.SystemSettings.GetColour (wx.SYS_COLOUR_GRAYTEXT))
            """
              Draw the sharing state icon
            """
            share = Sharing.getShare(item)
            if share is not None:
                if hasattr(share, 'sharer') and share.sharer is not None and \
                   str(share.sharer.itsPath) == "//userdata/me":
                    imageName = "SidebarUpload.png"
                else:
                    imageName = "SidebarDownload.png"
                image = wx.GetApp().GetImage (imageName)
                x = rect.GetRight() - image.GetWidth() - 1
                y = rect.GetTop() + (rect.GetHeight() - image.GetHeight()) / 2
                dc.DrawBitmap (image, x, y, True)
            """
              Draw the left icon simulating a button
            """
            name = getattr (item, attribute)
            key = name
            sidebar = grid.blockItem
            if sidebar.filterKind is not None:
                key += os.path.basename (unicode (sidebar.filterKind.itsPath))
            try:
                name = sidebar.nameAlternatives [key]
            except KeyError:
                imageName = name
            else:
                imageName = key
    
            if row == getattr (grid, "hoverImageRow", wx.NOT_FOUND):
                imagePrefix = "SidebarMouseOver"
                checked = grid.screenChecked
            else:
                imagePrefix = "Sidebar"
                checked = item in grid.blockItem.checkedItems
    
            if checked:
                imageSuffix = "Checked.png"
            else:
                imageSuffix = ".png"
    
            image = wx.GetApp().GetImage (imagePrefix + imageName + imageSuffix)
    
            if image is None:
                image = wx.GetApp().GetImage (imagePrefix + imageSuffix)

            if image is not None:
                x = rect.GetLeft() + 1
                y = rect.GetTop() + (rect.GetHeight() - image.GetHeight()) / 2
                dc.DrawBitmap (image, x, y, True)
        else:
            name = getattr (item, attribute)

        textRect = GetRenderEditorTextRect (rect)
        textRect.Inflate (-1, -1)
        dc.SetClippingRect (textRect)
        DrawingUtilities.DrawWrappedText (dc, name, textRect)
        dc.DestroyClippingRegion()


class SSSidebarEditor (ControlBlocks.GridCellAttributeEditor):
    """
      Super specialized Sidebar Editor, is so specialized that it works in
    only one context -- Mimi's Sidebar.
    """

    def SetSize(self, rect):
        textRect = GetRenderEditorTextRect (rect)
        self.control.SetRect (textRect);


class Sidebar(ControlBlocks.Table):

    filterKind = schema.One(
        schema.TypeReference('//Schema/Core/Kind'), initialValue = None,
    )

    # A dictionary of display names of items that don't show as Calendar Views
    dontShowCalendarForItemsWithName = schema.Mapping(schema.Boolean)

    # A dictionary mapping a name,kindpathComponent string to a new name.
    # It would be much nicer if the key could be a (name, kindItem) tuple, but
    # that's not possible with current parcel XML
    nameAlternatives = schema.Mapping(schema.String)

    # A list of the items in the sidebar that are checked
    checkedItems = schema.Sequence(schema.Item, initialValue = [])

    schema.addClouds(
        default = schema.Cloud(byRef=[filterKind])
    )

    def instantiateWidget (self):
        widget = wxSidebar (self.parentBlock.widget, Block.Block.getWidgetID(self))    
        widget.RegisterDataType ("Item", SSSidebarRenderer(), SSSidebarEditor("Item"))
        return widget

    def onKindParameterizedEvent (self, event):                
        self.filterKind = event.kindParameter
        # We need to update the click state of the toolbar as well
        toolbar = Block.Block.findBlockByName("ApplicationBar")
        for button in toolbar.childrenBlocks:
            try:
                buttonEvent = button.event
            except:
                continue
            if buttonEvent == event:
                button.widget.selectTool()
                continue
        self.widget.Refresh()
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

    tableTemplatePath = schema.One(schema.String)
    calendarTemplatePath = schema.One(schema.String)
    itemTupleKeyToCacheKey = schema.Mapping(schema.Item, initialValue = {})

    schema.addClouds(
        default = schema.Cloud(byRef=[itemTupleKeyToCacheKey])
    )

    def _mapItemToCacheKeyItem(self, item):
        key = item
        rerender = False
        sidebar = Block.Block.findBlockByName ("Sidebar")
        """
          collectionList should be in the order that the source items are overlayed in the Calendar view
        """
        collectionList = [theItem for theItem in sidebar.contents if (theItem in sidebar.checkedItems) and (theItem is not item)]
        if isinstance (item, ItemCollection.ItemCollection):
            collectionList.insert (0, item)
        if len (collectionList) > 0:
            """
              tupleList is sorted so we always end up with on collection for any order of collections
            in the source
            """
            tupleList = [theItem.itsUUID for theItem in collectionList]
            tupleList.sort()

            filterKind = sidebar.filterKind
            if not filterKind is None:
                tupleList.append (filterKind.itsUUID)
            
            if len (tupleList) > 1:
                tupleKey = tuple (tupleList)

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
                    key.source = collectionList
                    
                    displayName = u" and ".join ([theItem.displayName for theItem in collectionList])
                    if filterKind is not None:
                        key.addFilterKind (filterKind)
                        displayName += u" filtered by " + filterKind.displayName                    
                    key.displayName = displayName

                    self.itemTupleKeyToCacheKey [tupleKey] = key
                else:
                    """
                      Check to see if we need to reorder the source list
                    """
                    for new, old in map (None, key.source, collectionList):
                        if new is not old:
                            key.source = collectionList
                            rerender = True
        return key, rerender

    def _makeTrunkForCacheKey(self, keyItem):
        if isinstance (keyItem, ItemCollection.ItemCollection):
            sidebar = Block.Block.findBlockByName ("Sidebar")
            filterKind = sidebar.filterKind
            if (filterKind is not None and
                unicode (filterKind.itsPath) == "//parcels/osaf/contentmodel/calendar/CalendarEventMixin" and
                keyItem.displayName not in sidebar.dontShowCalendarForItemsWithName):
                    trunk = self.findPath (self.calendarTemplatePath)
                    keyUUID = trunk.itsUUID
                    try:
                        trunk = self.keyUUIDToTrunk[keyUUID]
                    except KeyError:
                        trunk = self._copyItem(trunk, onlyIfReadOnly=True)
                        self.keyUUIDToTrunk[keyUUID] = trunk
            else:
                trunk = self.findPath (self.tableTemplatePath)
        else:
            trunk = keyItem
        
        assert isinstance (trunk, Block.Block)
        return self._copyItem(trunk, onlyIfReadOnly=True)

    def _getContentsForTrunk(self, trunk, item, keyItem):
        return keyItem


class CPIATestSidebarTrunkDelegate(Trunk.TrunkDelegate):

    templatePath = schema.One(schema.String)

    def _makeTrunkForCacheKey(self, keyItem):
        if isinstance (keyItem, ItemCollection.ItemCollection):
            trunk = self.findPath (self.templatePath)
        else:
            trunk = keyItem
        
        assert isinstance (trunk, Block.Block)
        return self._copyItem(trunk, onlyIfReadOnly=True)
