__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.views.main"

import osaf.framework.blocks.ControlBlocks as ControlBlocks
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.Trunk as Trunk
from osaf.pim import AbstractCollection, FilteredCollection, IntersectionCollection, KindCollection, UnionCollection
import wx
import osaf.framework.blocks.DrawingUtilities as DrawingUtilities
import os
from osaf import sharing
from application import schema
from i18n import OSAFMessageFactory as _

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
        gridWindow.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

    def onKeyDown(self, event):
        if self.IsCellEditControlEnabled():
            keyCode = event.GetKeyCode()
            if keyCode == wx.WXK_RETURN or keyCode == wx.WXK_NUMPAD_ENTER:
                self.DisableCellEditControl()
                return
        event.Skip()

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

    @classmethod
    def GetRectFromOffsets (theClass, rect, offsets):
        def GetEdge (rect, offset):
            if offset >= 0:
                edge = rect.GetLeft()
            else:
                edge = rect.GetRight()
            return edge + offset
        
        top = rect.GetTop()
        height = offsets [2]
        if height == 0:
            height = rect.GetHeight()
        else:
            top = top + (rect.GetHeight() - height) / 2.0
        left = GetEdge (rect, offsets [0])
        return wx.Rect (left,
                        top,
                        GetEdge (rect, offsets [1]) - left,
                        height)

    def OnDoubleClick (self, event):
        unscrolledX, unscrolledY = self.CalcUnscrolledPosition (event.GetX(), event.GetY())
        if self.YToRow (unscrolledY) == wx.NOT_FOUND:
            self.blockItem.postEventByName ('NewCollection', {})
        else:
            event.Skip() #Let the grid handle the event

    def OnMouseEvents (self, event):
        """
          This code is tricky, tread with care -- DJA
        """
        event.Skip() #Let the grid also handle the event by default

        gridWindow = self.GetGridWindow()
        blockItem = self.blockItem

        x = event.GetX()
        y = event.GetY()

        unscrolledX, unscrolledY = self.CalcUnscrolledPosition (x, y)
        row = self.YToRow (unscrolledY)

        cellRect = self.CalculateCellRect (row)

        item, attribute = self.GetTable().GetValue (row, 0)

        if (cellRect.InsideXY (x, y) and
            not hasattr (self, 'hoverImageRow') and
            not self.IsCellEditControlEnabled() and
            isinstance (item, AbstractCollection)):
                assert not gridWindow.HasCapture()
                gridWindow.CaptureMouse()

                self.hoverImageRow = row
                self.cellRect = cellRect
                self.pressedButton = None

                # Initialize the buttons state and store in temporary attributes that don't persist
                for button in blockItem.buttons:
                    method = getattr (type (button), "getChecked", False)
                    checked = method and method (button, item)
                    imageRect = self.GetRectFromOffsets (cellRect, button.buttonOffsets)
                    button.buttonState = {'imageRect': imageRect,
                                          'screenMouseDown': checked,
                                          'blockChecked': checked}
                    self.RefreshRect (imageRect)

        if hasattr (self, 'hoverImageRow'):
            if event.LeftDown():
                for button in blockItem.buttons:
                    buttonState = button.buttonState
                    if (buttonState['imageRect'].InsideXY (x, y) and
                        isinstance (item, AbstractCollection)):
                        
                        event.Skip (False) #Gobble the event
                        self.SetFocus()

                        method = getattr (type (button), "getChecked", False)
                        checked = method and method (button, item)

                        buttonState['blockChecked'] = checked
                        buttonState['screenMouseDown'] = not checked
                        self.pressedButton = button
                        self.RefreshRect (buttonState['imageRect'])
                        break

            elif event.LeftUp():
                if self.pressedButton is not None:
                    imageRect = self.pressedButton.buttonState['imageRect']
                    if (imageRect.InsideXY (x, y)):
                        pressedButton = self.pressedButton

                        method = getattr (type (pressedButton), "getChecked", False)
                        if method:
                            checked = not method (pressedButton, item)
                            pressedButton.setChecked (item, checked)
                            pressedButton.buttonState['screenMouseDown'] = checked
                            blockItem.postEventByName ("SelectItemBroadcast", {'item':blockItem.selectedItemToView})
                            wx.GetApp().UIRepositoryView.commit()
                        else:
                            pressedButton.buttonState['screenMouseDown'] = False
                            self.RefreshRect (pressedButton.buttonState['imageRect'])
                    elif not self.cellRect.InsideXY (x, y):
                        self.RefreshRect (imageRect)
                        del self.hoverImageRow
                        """
                        @@@ this comment is applicable for all 3 ReleaseMouse calls in this routine
                        A possible bug (either here in SideBar or perhaps within wxWidgets) causes
                        this window to not have the mouse capture event though it never explicit released it.
                        You can verify this by enabling (i.e., commenting in) this assert:
                        assert gridWindow.HasCapture()
                        """
                        if (gridWindow.HasCapture()):
                            gridWindow.ReleaseMouse()
                    self.pressedButton = None

            elif event.LeftDClick():
                if (gridWindow.HasCapture()):
                    gridWindow.ReleaseMouse()
                del self.hoverImageRow

            elif not (event.LeftIsDown() or self.cellRect.InsideXY (x, y)):
                for button in blockItem.buttons:
                    self.RefreshRect (button.buttonState['imageRect'])
                self.pressedButton = None
                del self.hoverImageRow
                if (gridWindow.HasCapture()):
                    gridWindow.ReleaseMouse()

            elif (self.pressedButton is not None):
                buttonState = self.pressedButton.buttonState
                imageRect = buttonState['imageRect']
                screenMouseDown = buttonState['screenMouseDown']
                if imageRect.InsideXY (x, y) == (screenMouseDown == buttonState['blockChecked']):
                    buttonState['screenMouseDown'] = not screenMouseDown
                    self.RefreshRect (imageRect)

    def OnRequestDrop (self, x, y):
        self.hoverRow = wx.NOT_FOUND
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
            self.hoverRow = wx.NOT_FOUND
            
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
      The sidebar design doesn't use any off the shelf parts, so we'll go roll a bunch
    of special purpose interface that can't be use anywhere else in CPIA.
    """
    def Draw (self, grid, attr, dc, rect, row, col, isSelected):
        DrawingUtilities.SetTextColorsAndFont (grid, attr, dc, isSelected)

        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangleRect(rect)

        dc.SetBackgroundMode (wx.TRANSPARENT)
        item, attribute = grid.GetTable().GetValue (row, col)

        sidebar = grid.blockItem
        if isinstance (item, AbstractCollection):
            """
              Gray text forground color if the collection is empty
            """
            sidebarTPB = Block.Block.findBlockByName ("SidebarTPB")
            if sidebarTPB is not None:
                (filteredCollection, rerender) = sidebarTPB.trunkDelegate._mapItemToCacheKeyItem(item, False)
                if len (filteredCollection) == 0:
                    dc.SetTextForeground (wx.SystemSettings.GetColour (wx.SYS_COLOUR_GRAYTEXT))
            """
              Confuse user by changing the name to something they won't understand
            """
            name = getattr (item, attribute)
            if hasattr (item, "displayNameAlternatives"):
                if sidebar.filterKind is None:
                    key = "None"
                else:
                    key = os.path.basename (str (sidebar.filterKind.itsPath))
                name = item.displayNameAlternatives [key]
            """
              Draw the buttons
            """
            for button in sidebar.buttons:
                mouseOver = row == getattr (grid, 'hoverImageRow', wx.NOT_FOUND)
                image = button.getButtonImage (item, mouseOver)
                if image is not None:
                    imageRect = wxSidebar.GetRectFromOffsets (rect, button.buttonOffsets)
                    dc.DrawBitmap (image, imageRect.GetLeft(), imageRect.GetTop(), True)

        else:
            name = getattr (item, attribute)

        textRect = wxSidebar.GetRectFromOffsets (rect, sidebar.editRectOffsets)
        textRect.Inflate (-1, -1)
        dc.SetClippingRect (textRect)
        DrawingUtilities.DrawClippedTextWithDots (dc, name, textRect)
        dc.DestroyClippingRegion()


class SSSidebarEditor (ControlBlocks.GridCellAttributeEditor):
    """
      The sidebar design doesn't use any off the shelf parts, so we'll go roll a bunch
    of special purpose interface that can't be use anywhere else in CPIA.
    """

    def SetSize(self, rect):
        sidebar = Block.Block.findBlockByName ("Sidebar")
        textRect = wxSidebar.GetRectFromOffsets (rect, sidebar.editRectOffsets)
        self.control.SetRect (textRect);


class SSSidebarButton (schema.Item):
    """
      Super specialized Sidebar button -- The sidebar design doesn't use
    any off the shelf parts, so we'll go roll a bunch of special purpose
    interface that can't be use anywhere else in CPIA.
    """
    # buttonName is 8 bit chars for programmers only.
    buttonName = schema.One(schema.String)

    # buttonOffsets is a list of left offset, right offset and height.
    # Left offset is the offset in pixels of the left edge of the button
    # where positive values are from the left edge of the cell rect and
    # negative values are from the left edge of the cell rect. Height
    # is the height of the button which is centered vertically in the
    # cell. A height of zero uses the height of the cell
    buttonOffsets = schema.Sequence (schema.Integer, required = True)

    buttonOwner = schema.One("SidebarBlock",
                             inverse="buttons",
                             initialValue = None)

class SSSidebarIconButton (SSSidebarButton):
    def getChecked (self, item):
        return item in self.buttonOwner.checkedItems

    def setChecked (self, item, checked):
        checkedItems = self.buttonOwner.checkedItems
        if checked:
            checkedItems.add (item)
        else:
            checkedItems.remove (item)

    def getButtonImage (self, item, mouseOverFlag):
        """
        The rules for naming icons are complicated, which is a
        reflection of complexity of our sidebar design, so here is a
        summary of the new rules:

        Names are made up of the following pieces:

        'Sidebar', ButtonName, IconName, 'Checked', 'MouseOver', '.png'

        They all begin with 'Sidebar', followed by ButtonName. Today,
        we only have two buttons named: 'Icon', and 'SharingIcon'.

        The ButtonName is followed by IconName. IconName is a property
        of the collection, e.g. the AllCollection has an IconName of
        'All'. The In, Out, and Trash collections have names 'In',
        'Out' and 'Trash' respectively. Currently, new collections
        have no icon name, so the IconName can be empty. Another
        property of the collection is whether or not the IconName has
        a kind variation, in which case the IconName is appended with
        the Kind, e.g. CalendarEventMixin, MailMessageMixin,
        TaskMixin.  Currently, only the All collection has this
        property, so the IconNames for the AllCollection are 'All',
        'AllCalendarEventMixin', 'AllMailMessageMixin' and
        'AllTaskMixin'.

        A property of a button in the siebar is whether or not it is
        checkable. Today the Icon button is checkable and the
        SharingIcon isn't. For checkable buttons, the IconName is
        followed by 'Checked', for the checked image.

        Next comes 'MouseOver' if a different image is necessary for
        the state when the mouse is over the item.

        Here are the new rules for defaults:

        First we lookup the fully qualified name, e.g. 'Sidebar',
        ButtonName, IconName, 'Checked', 'MouseOver', '.png'

        If we don't find an image by that name we next lookup the name
        without the IconName, e.g. 'Sidebar', ButtonName, 'Checked',
        'MouseOver', '.png'. This allows us to specify a default icon
        for Checked and MouseOver that is applied by default if you
        don't have a special one for a particular icon.

        If we still don't find an image, we next lookup the full image
        name without MouseOver, e.g. 'Sidebar', ButtonName, IconName,
        'Checked', '.png'. So if you don't have MouseOver icons they
        don't get displayed.

        Finally if we still don't have an image, we try to lookup the
        name without an IconName or MouseOver, e.g 'Sidebar',
        ButtonName, 'Checked', '.png'. This allows us to have a
        default for checkable buttons without MouseOver.
        """
        colorizeIcon = True
        imagePrefix = "Sidebar" + self.buttonName
        mouseOver = ""
        mouseDown = ""
        imageSuffix = ".png"

        if mouseOverFlag:
            mouseOver = "MouseOver"
            if self.buttonState['screenMouseDown']:
                mouseDown = "MouseDown"
        else:
            if self.getChecked (item):
                mouseDown = "MouseDown"
            else:
                colorizeIcon = item.colorizeIcon

        iconName = getattr(item, "iconName", "")
        sidebar = self.buttonOwner
        if item.iconNameHasKindVariant and sidebar.filterKind is not None:
            iconName += os.path.basename (str (sidebar.filterKind.itsPath))

        # First lookup full image name
        image = wx.GetApp().GetRawImage (imagePrefix + iconName + mouseDown + mouseOver + imageSuffix)
        
        # If that fails try the default image wihtout the name of the icon
        if image is None:
            image = wx.GetApp().GetRawImage (imagePrefix + mouseDown + mouseOver + imageSuffix)
                
        # If that fails try the full icon name wihtout mouseOver
        if image is None:
            image = wx.GetApp().GetRawImage (imagePrefix + iconName + mouseDown + imageSuffix)

        # If that fails try the default image name wihtout mouseOver
        if image is None:
            image = wx.GetApp().GetRawImage (imagePrefix + mouseDown + imageSuffix)


        if image is not None and colorizeIcon:
            color = getattr (item, 'color', None)
            if color is not None:
                hsvValue = wx.Image.RGBtoHSV (wx.Image_RGBValue (color.red, color.green, color.blue))
                image.RotateHue (hsvValue.hue)

        if image is not None:
            image = wx.BitmapFromImage (image)

        return image


class SSSidebarSharingButton (SSSidebarButton):
    def getButtonImage (self, item, mouseOverFlag):
        """
        """
        def UpDownLoad ():
            if (share.sharer is not None and
                str(share.sharer.itsPath) == "//userdata/me"):
                return "Upload"
            return "Download"

        imagePrefix = "Sidebar" + self.buttonName
        notMine = ""
        mouseOver = ""
        mouseDown = ""
        imageSuffix = ".png"
        shared = ""
        partial = ""

        share = sharing.getShare(item)
        if share is not None:
            filterKind = self.buttonOwner.filterKind

            # @@@MOR  John, I just changed share.filterKinds into
            # share.filterClasses, which is a list of dotted names
            # referring to classes, such as 'osaf.pim.CalendarEventMixin'
            # so I had to tweak the code below that determines if the
            # current button filterKind matches the share's filterClasses.
            # Let's figure out if there's a better way.

            filterMatches = False
            if filterKind is not None:
                klass = filterKind.classes['python']
                for className in share.filterClasses:
                    if klass is schema.importString(className):
                        filterMatches = True
                        break

            if ((filterKind is None) or filterMatches):

                if (share.sharer is not None and
                    str(share.sharer.itsPath) == "//userdata/me"):
                    shared = "Upload"
                shared = "Download"

                if filterKind is None and  len (share.filterClasses) != 0:
                    partial = "Partial"

        if mouseOverFlag:
            mouseOver = "MouseOver"
            if self.buttonState['screenMouseDown']:
                mouseDown = "MouseDown"

        iconName = ""
        if shared:
            # First check to see if we're offline
            if not sharing.isOnline (item):
                iconName = shared + "Offline"

            # If we're not Offline, check to see if we have an error
            # Don't have an error indicator yet
            elif getattr (share, "error", False):
                iconName = "Error"
            
            # Otherwise we're either Upload or Download
            else:
                iconName = shared + partial
        
        # We need an indication of NotMine
        if False:
            iconName += "NotMine"

        # First lookup full image name
        image = wx.GetApp().GetImage (imagePrefix + iconName + mouseDown + mouseOver + imageSuffix)
        
        # If that fails try the default image wihtout mouseOver
        if image is None:
            image = wx.GetApp().GetImage (imagePrefix + iconName + mouseDown + imageSuffix)
                
        # If that fails try the full icon name wihtout mouseDown and mouseOver
        if image is None:
            image = wx.GetApp().GetImage (imagePrefix + iconName + imageSuffix)

        return image


class SidebarBlock(ControlBlocks.Table):
    filterKind = schema.One(
        schema.TypeReference('//Schema/Core/Kind'), initialValue = None,
    )

    # A set of the items in the sidebar that are checked
    checkedItems = schema.Many(initialValue=set())

    buttons = schema.Sequence (SSSidebarButton,
                               inverse = "buttonOwner",
                               initialValue = [])
    
    # For the edit rect, a list of left offset, right offset and height.
    # Left offset is the offset in pixels of the left edge of the button
    # where positive values are from the left edge of the cell rect and
    # negative values are from the left edge of the cell rect. Height
    # is the height of the button which is centered vertically in the
    # cell. A height of zero uses the height of the cell
    editRectOffsets = schema.Sequence (schema.Integer, required = True)

    schema.addClouds(
        copying = schema.Cloud(byRef=[filterKind, buttons])
    )

    def instantiateWidget (self):
        if '__WXMAC__' in wx.PlatformInfo:
            widget = wxSidebar (self.parentBlock.widget, Block.Block.getWidgetID(self), style=wx.BORDER_SIMPLE)
        else:
            widget = wxSidebar (self.parentBlock.widget, Block.Block.getWidgetID(self), style = wx.BORDER_STATIC)
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
            return self.select(None, event.arguments['itemName'])
        else:
            return self.select(item)

    def select (self, item=None, name=''):
        # select the item by reference or name.
        # (polymorphic method used by scripts)
        if item is None:
            for item in self.contents:
                if item.displayName == name:
                    break
            else:
                return

        self.postEventByName("SelectItemBroadcast", {'item':item})
        return item

    def onRemoveItemEvent(self, event):
        """
        Permanently remove the collection - we eventually need a user
        confirmation here
        """
        def deleteItem(item):
            # TODO: for item collectionsactually call item.delete(),
            # and also delete any items that exist only in the
            # doomed itemcollection (garbage collection would be a
            # big help here)

            # in the mean time, just remove it.
            self.contents.remove(item)

        self.widget.DeleteSelection(deleteItem)

    onDeleteItemEvent = onRemoveItemEvent

    def onRemoveEventUpdateUI(self, event):
        # so you can't use the delete key to delete a collection
        event.arguments['Enabled'] = False
            
    def onDeleteEventUpdateUI(self, event):
        event.arguments['Text'] = _(u'Delete Collection')
        """
        this is enabled if any user item is selected in the sidebar
        """
        event.arguments['Enable'] = (self.selectedItemToView is not None and
                                     getattr(self.selectedItemToView, 'renameable', True))
            
    def onCollectionColorEvent(self, event):
        self.selectedItemToView.color = event.color
        
    def onCollectionColorEventUpdateUI(self, event):
        # color of the selected collection
        event.arguments['Enable'] = self.selectedItemToView is not None
        
        color = getattr(self.selectedItemToView, 'color', None)

        # the event contains the color, so we need to look at that
        # the only way to test for equality is by converting both
        # ColorType's to tuples
        event.arguments['Check'] = color is not None and color.toTuple() == event.color.toTuple()

class SidebarTrunkDelegate(Trunk.TrunkDelegate):

    tableTemplatePath = schema.One(schema.String)
    calendarTemplatePath = schema.One(schema.String)
    itemTupleKeyToCacheKey = schema.Mapping(schema.Item, initialValue = {})
    kindToKindCollectionCache = schema.Mapping(schema.Item, initialValue = {})

    schema.addClouds(
        copying = schema.Cloud(byRef=[itemTupleKeyToCacheKey])
    )

    def _mapItemToCacheKeyItem(self, item, includeCheckedItems=True):
        key = item
        rerender = False
        sidebar = Block.Block.findBlockByName ("Sidebar")
        """
        collectionList should be in the order that the source items
        are overlayed in the Calendar view
        """
        if includeCheckedItems:
            collectionList = [theItem for theItem in sidebar.contents if (theItem in sidebar.checkedItems) and (theItem is not item)]
        else:
            collectionList = []
        if isinstance (item, AbstractCollection):
            collectionList.insert (0, item)
            
        if len (collectionList) > 0:
            """
            tupleList is sorted so we always end up with on collection
            for any order of collections in the source
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
                    if len (collectionList) == 1:
                        key = collectionList [0]
                    else:
                        key = UnionCollection (view=self.itsView)
                        for col in collectionList:
                            key.addSource(col)

                    displayName = u" and ".join ([theItem.displayName for theItem in collectionList])

                    if filterKind is not None:
                        newKey = IntersectionCollection(view=self.itsView)
                        try:
                            kindCollection = self.kindToKindCollectionCache [filterKind]
                        except KeyError:
                            kindCollection = KindCollection (view=self.itsView)
                            kindCollection.kind = filterKind
                            kindCollection.recursive = True
                            self.kindToKindCollectionCache [filterKind] = kindCollection

                        newKey.sources = [key, kindCollection]
                        newKey.dontDisplayAsCalendar = key.dontDisplayAsCalendar
                        displayName += u" filtered by " + filterKind.displayName
                        key = newKey

                    key.displayName = displayName

                    key.collectionList = collectionList
                    self.itemTupleKeyToCacheKey [tupleKey] = key
                else: # try/except
                    """
                    Check to see if we need to reorder
                    collectionList. The list is kept sorted by the
                    order of the collections as they overlay one
                    another in the Calendar.  We don't bother to
                    reorder when we're looking up a collection that
                    isn't displayed in the summary view, both because
                    it's not necessary and because it causes the
                    source attribute to change which causes a
                    notification to update the sidebar, which causes
                    the order to change, causing a notification,
                    ... repeating forever.
                    """
                    if sidebar.selectedItemToView is item:
                        for new, old in map (None, key.collectionList, collectionList):
                            if new is not old:
                                key.collectionList = collectionList
                                rerender = True
                                break
        return key, rerender

    def _makeTrunkForCacheKey(self, keyItem):
        if isinstance (keyItem, AbstractCollection):
            sidebar = Block.Block.findBlockByName ("Sidebar")
            if (not keyItem.dontDisplayAsCalendar and
                sidebar.filterKind is schema.ns('osaf.pim.calendar.Calendar', self).CalendarEventMixin.getKind (self)):
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
        if isinstance (keyItem, AbstractCollection):
            trunk = self.findPath (self.templatePath)
        else:
            trunk = keyItem
        
        assert isinstance (trunk, Block.Block)
        return self._copyItem(trunk, onlyIfReadOnly=True)
