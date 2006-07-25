#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


__parcel__ = "osaf.views.main"

from osaf.framework.blocks import ControlBlocks, KindParameterizedEvent
import wx, os
from osaf.framework.blocks import (
    Block, BranchPoint, DrawingUtilities, Table, wxTable, GridCellAttributeEditor
    )

from osaf.pim import (
    ContentCollection, IntersectionCollection, KindCollection,
    UnionCollection, IndexedSelectionCollection, AppCollection
    )
    
from osaf.framework.prompts import promptYesNoCancel

from osaf import sharing, pim
from osaf.usercollections import UserCollection
from osaf.sharing import ChooseFormat
from application import schema
from i18n import OSAFMessageFactory as _

from colorsys import rgb_to_hsv

class SidebarElementDelegate (ControlBlocks.ListDelegate):
    def ReadOnly (self, row, column):
        """
          Second argument should be True if all cells have the first value
        """
        (item, attribute) = self.GetElementValue (row, column)
        return (not UserCollection (item).renameable), False

    def GetElementType (self, row, column):
        return "Item"

    def GetElementValue (self, row, column):
        itemIndex = self.RowToIndex(row)
        return (self.blockItem.contents [itemIndex],
                self.blockItem.columns[column].attributeName)
    
class wxSidebar(wxTable):
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

    def wxSynchronizeWidget(self, useHints=False):
        # clear out old 'checked' items
        sidebar = self.blockItem
        
        # sidebar.checkedItems is a python set,
        # it cannot be modified while iterating
        for checkedItem in list(sidebar.checkedItems):
            if checkedItem not in sidebar.contents:
                sidebar.checkedItems.remove (checkedItem)
        super (wxSidebar, self).wxSynchronizeWidget(useHints)

    @staticmethod
    def GetRectFromOffsets (rect, offsets):
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

        def stopHovering():
            del self.hoverImageRow
            """
            If we've got hoverImageRow that we must have captured the mouse
            """
            # NB: this assert fires on Mac at inconvenient times - e.g., editing collection names
            #assert gridWindow.HasCapture()
            if (gridWindow.HasCapture()):
                gridWindow.ReleaseMouse()
            for button in blockItem.buttons:
                method = getattr (type (button), "onOverButton", False)
                if method:
                    if button.buttonState['overButton']:
                        button.buttonState['overButton'] = False
                        method (button, item)

        blockItem.stopNotificationDirt()
        try:
            if (cellRect.InsideXY (x, y) and
                not self.IsCellEditControlEnabled() and
                UserCollection(item).allowOverlay):
                    if not hasattr (self, 'hoverImageRow'):
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
                                                  'blockChecked': checked,
                                                  'overButton': False}
                            self.RefreshRect (imageRect)
                    for button in blockItem.buttons:
                        method = getattr (type (button), "onOverButton", False)
                        if method:
                            overButton = button.buttonState['imageRect'].InsideXY (x, y)
                            if button.buttonState['overButton'] != overButton:
                                button.buttonState['overButton'] = overButton
                                method (button, item)
    
    
            if hasattr (self, 'hoverImageRow'):
                if event.LeftDown():
                    for button in blockItem.buttons:
                        buttonState = button.buttonState
                        if (buttonState['imageRect'].InsideXY (x, y) and
                            UserCollection(item).allowOverlay):
                            
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
                                selectedItems = list(blockItem.contents.iterSelection())
                                blockItem.postEventByName ("SelectItemsBroadcast",
                                                           {'items':selectedItems})
                                wx.GetApp().UIRepositoryView.commit()
                            else:
                                pressedButton.buttonState['screenMouseDown'] = False
                                self.RefreshRect (pressedButton.buttonState['imageRect'])
                        elif not self.cellRect.InsideXY (x, y):
                            self.RefreshRect (imageRect)
                            stopHovering()
                        self.pressedButton = None
    
                elif event.LeftDClick():
                    # Stop hover if we're going to edit
                    stopHovering()
    
                elif not (event.LeftIsDown() or self.cellRect.InsideXY (x, y)):
                    for button in blockItem.buttons:
                        self.RefreshRect (button.buttonState['imageRect'])
                    self.pressedButton = None
                    stopHovering()
    
                elif (self.pressedButton is not None):
                    buttonState = self.pressedButton.buttonState
                    imageRect = buttonState['imageRect']
                    screenMouseDown = buttonState['screenMouseDown']
                    if imageRect.InsideXY (x, y) == (screenMouseDown == buttonState['blockChecked']):
                        buttonState['screenMouseDown'] = not screenMouseDown
                        self.RefreshRect (imageRect)
        finally:
            blockItem.startNotificationDirt()

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
        whereToDropItem = getattr (self, 'whereToDropItem', None)
        if whereToDropItem is None:
            possibleCollections = self.SelectedItems()
        else:
            possibleCollections = [self.blockItem.contents[whereToDropItem]]
            self.SetRowHighlight(self.whereToDropItem, False)
            del self.whereToDropItem
        for possibleCollection in possibleCollections:
            for item in itemList:
                # Some items don't know how to add themselves
                method = getattr (type (item), "addToCollection", None)
                if method is not None:
                    method (item, possibleCollection)
    
    def OnItemDrag (self, event):
        # @@@ You currently can't drag out of the sidebar
        pass

    def onCopyEventUpdateUI(self, event):
        # You can't Cut or Copy items from the sidebar
        event.arguments['Enable'] = False
        
    def onClearEventUpdateUI(self, event):
        event.arguments['Enable'] = self.blockItem.canRenameSelection()

    def OnHover (self, x, y, dragResult):
        x, y = self.CalcUnscrolledPosition(x, y)
        hoverRow = self.YToRow(y)
        if not hasattr (self, 'hoverRow'):
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
        
        if hoverRow == wx.NOT_FOUND:
            # Allow file drops anywhere.  Unfortunately a wx.DropTarget
            # doesn't provide information about what data is actually in the 
            # DataObject hovering over it, so we can't use wx to determine if
            # the object is a file.  We resort to the Chandler specific
            # global, DraggedFromWidget, which gets set and unset by Chandler
            # when a widget is dragged.
            if self.GetDraggedFromWidget() is None:
                dragResult = wx.DragCopy
            # otherwise, don't allow the drag if we're not over an item
            else:
                dragResult = wx.DragNone
        else:
            # Switch to the "move" icon if we're over the trash
            possibleCollection = self.blockItem.contents[hoverRow]
            theTrash = schema.ns('osaf.pim', self.blockItem.itsView).trashCollection
            if possibleCollection is theTrash:
                if self.GetDragData() is not None: # make sure the data is the kind we want.
                    dragResult = wx.DragMove
            elif possibleCollection.isReadOnly():
                dragResult = wx.DragNone
    
        return dragResult

    OnEnter = OnHover # Enter callback same as Hover callback (Drag & Drop)

    def OnLeave (self):
        # check if we had a hover row
        hoverRow = getattr (self, 'hoverRow', None)
        if hoverRow is not None:
            # Clear the selection colour if necessary
            self.SetRowHighlight(self.hoverRow, False)
            self.hoverRow = wx.NOT_FOUND
            
    def SetRowHighlight (self, row, highlightOn):
        if highlightOn:
            color = wx.LIGHT_GREY
        else:
            color = wx.WHITE
        self.SetCellBackgroundColour(row, 0, color)

        # Just invalidate the changed rect
        rect = self.CalculateCellRect (row)
        self.RefreshRect(rect)
        self.Update()

    def OnFilePaste(self):
        coll = self.getCollectionDroppedOn()
        for filename in self.fileDataObject.GetFilenames():
            ChooseFormat.importFile(filename, self.blockItem.itsView, coll)

    def getCollectionDroppedOn(self):
        whereToDropItem = getattr (self, 'whereToDropItem', None)
        if whereToDropItem is None:
            coll = None
        else:
            coll = self.blockItem.contents[whereToDropItem]
            self.SetRowHighlight(self.whereToDropItem, False)
            del self.whereToDropItem
        return coll

    def OnEmailPaste(self, text):
        coll = self.getCollectionDroppedOn()
        ChooseFormat.importEmail(text, self.blockItem.itsView, coll)

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
        """
          Gray text forground color if the collection is empty
        """
        sidebarBPB = Block.Block.findBlockByName ("SidebarBranchPointBlock")
        if sidebarBPB is not None:
            filteredCollection = sidebarBPB.delegate.\
                               _mapItemToCacheKeyItem(item, {
                                   "getOnlySelectedCollection": True,
                                })
            if filteredCollection.isEmpty():
                dc.SetTextForeground (wx.SystemSettings.GetColour (wx.SYS_COLOUR_GRAYTEXT))
        """
          Confuse user by changing the name to something they won't understand
        """
        if hasattr (UserCollection(item), "displayNameAlternatives"):
            name = sidebar.getNameAlternative (item)
        else:
            name = getattr (item, attribute)
        """
          Draw the buttons
        """
        for button in sidebar.buttons:
            mouseOver = row == getattr (grid, 'hoverImageRow', wx.NOT_FOUND)
            image = button.getButtonImage (item, mouseOver)
            if image is not None:
                imageRect = wxSidebar.GetRectFromOffsets (rect, button.buttonOffsets)
                dc.DrawBitmap (image, imageRect.GetLeft(), imageRect.GetTop(), True)


        textRect = wxSidebar.GetRectFromOffsets (rect, sidebar.editRectOffsets)
        textRect.Inflate (-1, -1)
        dc.SetClippingRect (textRect)
        DrawingUtilities.DrawClippedTextWithDots (dc, name, textRect)
        dc.DestroyClippingRegion()


class SSSidebarEditor (GridCellAttributeEditor):
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
    buttonName = schema.One(schema.Text)

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

    schema.addClouds(
        copying = schema.Cloud (byCloud = [buttonOwner])
    )

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
        summary of the rules:

        Names are made up of the following pieces:

        'Sidebar', ButtonName, IconName, 'MouseDown', 'MouseOver', '.png'

        They all begin with 'Sidebar', followed by ButtonName. Today,
        we only have two buttons named: 'Icon', and 'SharingIcon'. The
        rules for Icon follow -- see getButtonImage for the SharingIcon
        rules

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

        IconButtons are checkable. The checked state is indicated by
        adding "MouseDown".

        Next comes 'MouseOver' if a different image is necessary for
        the state when the mouse is over the item.

        Here are the rules for defaults:

        First we lookup the fully qualified name, e.g. 'Sidebar',
        ButtonName, IconName, 'MouseDown', 'MouseOver', '.png'

        If we don't find an image by that name we next lookup the name
        without the IconName, e.g. 'Sidebar', ButtonName, 'MouseDown',
        'MouseOver', '.png'. This allows us to specify a default icon
        for MouseDown and MouseOver that is applied by default if you
        don't have a special one for a particular icon.

        If we still don't find an image, we next lookup the full image
        name without MouseOver, e.g. 'Sidebar', ButtonName, IconName,
        'MouseDown', '.png'. So if you don't have MouseOver icons they
        don't get displayed.

        Finally if we still don't have an image, we try to lookup the
        name without an IconName or MouseOver, e.g 'Sidebar',
        ButtonName, 'MouseDown', '.png'. This allows us to have a
        default for buttons without MouseOver.
        """
        colorizeIcon = True
        imagePrefix = "Sidebar" + self.buttonName
        mouseOver = ""
        mouseDown = ""
        imageSuffix = ".png"
        userCollection = UserCollection(item)

        if mouseOverFlag:
            mouseOver = "MouseOver"
            if self.buttonState['screenMouseDown']:
                mouseDown = "MouseDown"
        else:
            if self.getChecked (item):
                mouseDown = "MouseDown"
            else:
                colorizeIcon = userCollection.colorizeIcon

        iconName = getattr(userCollection, "iconName", "")
        sidebar = self.buttonOwner
        if userCollection.iconNameHasKindVariant and sidebar.filterKind is not None:
            iconName += os.path.basename (str (sidebar.filterKind.itsPath))

        # First lookup full image name
        app = wx.GetApp()
        image = app.GetRawImage (imagePrefix + iconName + mouseDown + mouseOver + imageSuffix)
        
        # If that fails try the default image wihtout the name of the icon
        if image is None:
            image = app.GetRawImage (imagePrefix + mouseDown + mouseOver + imageSuffix)
                
        # If that fails try the full icon name wihtout mouseOver
        if image is None:
            image = app.GetRawImage (imagePrefix + iconName + mouseDown + imageSuffix)

        # If that fails try the default image name wihtout mouseOver
        if image is None:
            image = app.GetRawImage (imagePrefix + mouseDown + imageSuffix)


        if image is not None and colorizeIcon:
            userCollection = UserCollection(item)
            userCollection.ensureColor()
            color = getattr (UserCollection(item), 'color', None)
            rgbValue = DrawingUtilities.color2rgb(color.red, color.green, color.blue)
            hsvValue = rgb_to_hsv(*rgbValue)
            image.RotateHue (hsvValue[0])

        if image is not None:
            image = wx.BitmapFromImage (image)

        return image


class SSSidebarSharingButton (SSSidebarButton):
    def getButtonImage (self, item, mouseOverFlag):
        """
        The rules for naming icons are complicated, which is a
        reflection of complexity of our sidebar design, so here is a
        summary of the rules:

        Names are made up of the following pieces:

        'Sidebar', ButtonName, IconName, 'MouseDown', 'MouseOver', '.png'

        They all begin with 'Sidebar', followed by ButtonName. Today,
        we only have two buttons named: 'Icon', and 'SharingIcon'. The
        rules for SharingIcon follow -- see getButtonImage for the Icon
        rules

        The ButtonName is followed by IconName. IconName may take on
        the following values depending upon the state of the collection

        "Offline"
        "OfflineNotMine"
        
        "Error"
        "ErrorNotMine"
        
        "Upload"
        "UploadNotMine"
        "Download"
        "DownloadNotMine"
        "UploadPartial"
        "UploadPartialNotMine"
        "DownloadPartial"
        "DownloadPartialNotMine"

        ""
        "NotMine"
        
        Offline icons take precedence over the Error icon. The Error icon
        takes precedence over the remaining icons. Partial indicates that
        only some of the items in the collection are shared, e.g. when
        viewing All only calendar events are shared. If the collection
        isn't shared then the IconName is empty, i.e. "". NotMine is appended
        to the IconName if the collection is in the NotMine set of items.

        SharingIcon are momentary switches, i.e. you can click them and 
        while the mouse is down they show a down state icon. When the mouse
        is and the button is pressed "MouseDown" is appended.

        Next comes 'MouseOver' if a different image is necessary for
        the state when the mouse is over the item.

        Here are the rules for defaults:

        First we lookup the fully qualified name, e.g. 'Sidebar',
        ButtonName, IconName, 'MouseDown', 'MouseOver', '.png'

        If we don't find an image by that name we next lookup the name
        without the MouseOver, e.g. 'Sidebar', ButtonName, 'MouseDown',
        '.png'. So for Icons that don't have a special MouseOver state
        we use theMouseDown variation of the icon.

        Finally if we still don't find an image, we next lookup the full
        image name without MouseDown or MouseOver, e.g. 'Sidebar',
        ButtonName, IconName, '.png'. So if the button doesn't have a
        special icon for MouseDown or MouseOver you don't need to specify
        one.
        """
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

            if share.filterClasses:
                partial = "Partial"
                if filterKind is not None:
                    klass = filterKind.classes['python']
                    className = "%s.%s" % (klass.__module__, klass.__name__)
                    if className in share.filterClasses:
                        partial = ""

            if (sharing.isSharedByMe(share)):
                shared = "Upload"
            else:
                shared = "Download"

        if mouseOverFlag:
            mouseOver = "MouseOver"
            if self.buttonState['screenMouseDown']:
                mouseDown = "MouseDown"

        iconName = ""
        if shared:
            # First check to see if we're offline
            if not sharing.isOnline (item):
                iconName = "Offline"

            # If we're not Offline, check to see if we have an error
            # Don't have an error indicator yet
            elif getattr (share, "error", False):
                iconName = "Error"
            
            # Otherwise we're either Upload or Download
            else:
                iconName = shared + partial
        
        # We need an indication of NotMine
        mine = schema.ns('osaf.pim', self.itsView).mine
        if item not in mine.sources and not UserCollection(item).outOfTheBoxCollection:
            iconName += "NotMine"

        # First lookup full image name
        app = wx.GetApp()
        image = app.GetImage (imagePrefix + iconName + mouseDown + mouseOver + imageSuffix)
        
        # If that fails try the default image wihtout mouseOver
        if image is None:
            image = app.GetImage (imagePrefix + iconName + mouseDown + imageSuffix)
                
        # If that fails try the full icon name wihtout mouseDown and mouseOver
        if image is None:
            image = app.GetImage (imagePrefix + iconName + imageSuffix)

        return image

    def onOverButton (self, item):
        gridWindow = self.buttonOwner.widget.GetGridWindow()
        errorString = getattr (sharing.getShare(item), "error", False)
        if self.buttonState['overButton']:
            if errorString:
                gridWindow.SetToolTipString (errorString)
                gridWindow.GetToolTip().Enable (True)
        else:
            toolTip = gridWindow.GetToolTip()
            if toolTip:
                gridWindow.GetToolTip().Enable (False)
                gridWindow.SetToolTip (None)
    

class SidebarBlock(Table):
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
        copying = schema.Cloud(
            byRef = [filterKind],
            byCloud = [buttons]
        )
    )

    def instantiateWidget (self):
        widget = wxSidebar (self.parentBlock.widget, 
                            Block.Block.getWidgetID(self), 
                            characterStyle=getattr(self, "characterStyle", None),
                            headerCharacterStyle=getattr(self, "headerCharacterStyle", None))
        widget.RegisterDataType ("Item", SSSidebarRenderer(), SSSidebarEditor("Item"))
        return widget

    def onKindParameterizedEvent (self, event):
        self.setPreferredKind (event.kindParameter)

    def setPreferredKind (self, filterKind):
        if self.filterKind != filterKind:

            # We need to update the click state of the toolbar as well
            toolbar = Block.Block.findBlockByName("ApplicationBar")
            for button in toolbar.childrenBlocks:

                buttonEvent = getattr (button, 'event', None)
                if isinstance (buttonEvent, KindParameterizedEvent):
                    if (filterKind is not None and filterKind.isKindOf (buttonEvent.kindParameter)):
                        newFilterKind = buttonEvent.kindParameter
                        buttonToSelect = button
                        break
            else:
                #If we don't have a button with the appropriate kind
                #We'll switch to all
                newFilterKind = None
                buttonToSelect = self.findBlockByName ("ApplicationBarAllButton")

            self.filterKind = newFilterKind
            buttonToSelect.widget.selectTool()
            self.widget.Refresh()
            self.postEventByName("SelectItemsBroadcast",
                                 {'items':list(self.contents.iterSelection())})

    def onKindParameterizedEventUpdateUI (self, event):
        # check the appropriate menu item
        event.arguments['Check'] = event.kindParameter == self.filterKind

    def onRequestSelectSidebarItemEvent (self, event):
        # Request the sidebar to change selection
        # Item specified is usually by name
        item = event.arguments.get ('item', None)
        if item is None:
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

        self.postEventByName("SelectItemsBroadcast", {'items':[item]})
        return item

    def onRemoveEvent(self, event):
        """
        Permanently remove the collection - we eventually need a user
        confirmation here
        """

        viewsmain = schema.ns('osaf.views.main', self.itsView)
        
        # If there are any "mine" collections selected, ask the user
        # if we should be deleting the entire collection including the
        # items, or just some things
        shouldClearCollection = True
        pim_ns = schema.ns('osaf.pim', self.itsView)
        mine = pim_ns.mine
        allCollection = pim_ns.allCollection
        for collection in self.contents.iterSelection():
            if collection in mine.sources:
                # we found a "mine" collection, so prompt the user
                shouldClearCollection = \
                    promptYesNoCancel(_(u'Do you also want to delete the items in this collection?'),
                                      viewsmain.clearCollectionPref)
                
                if shouldClearCollection is None: # user pressed cancel
                    return
                
                break
            
        
        def deleteItem(collection):

            # clear out the collection contents, if appropriate
            if shouldClearCollection:
                self.ClearCollectionContents(collection)
            elif collection in mine.sources:

                # if the item doesn't exist in any other 'mine'
                # collection, we need to manually add it to 'all'
                # to keep the item 'mine'.

                # We don't want to do this blindly though, or
                # all's inclusions will get unnecessarily full.

                # We also don't want to remove collection from
                # mine.sources. That will cause a notification
                # storm as items temporarily leave and re-enter
                # being 'mine'
                for item in collection:
                    for otherCollection in item.appearsIn:
                        if otherCollection is collection:
                            continue

                        if otherCollection in mine.sources:
                            # we found it in another 'mine'
                            break
                    else:
                        # we didn't find it in a 'mine' Collection
                        allCollection.add(item)

            sharing.unsubscribe(collection)
            collection.delete(True)

        self.widget.DeleteSelection(DeleteItemCallback=deleteItem)

    onDeleteEvent = onRemoveEvent

    def onRemoveEventUpdateUI(self, event):
        event.arguments['Enable'] = False
            
    def onDeleteEventUpdateUI(self, event):
        """
        this is enabled if any user item is selected in the sidebar
        """
        # can remove anything except library collections
        if self.contents.isSelectionEmpty():
            enable = False
        else:
            for selectedItem in self.contents.iterSelection():
                if (UserCollection(selectedItem).outOfTheBoxCollection):
                    enable = False
                    break
            else:
                enable = True
        event.arguments['Enable'] = enable

    def ClearCollectionContents(self, collection):
        """
        Remove items that should be removed, delete items that should
        be deleted. Note that we're not doing any proxy-aware code
        here, because we're dealing with the actual items that are in
        the collection.
        """
        
        app_ns = schema.ns('osaf.app', self.itsView)
        pim_ns = schema.ns('osaf.pim', self.itsView)
        sidebarCollections = app_ns.sidebarCollection
        mine = pim_ns.mine
        trash = pim_ns.trashCollection
        
        # filter out the usable collections
        def IsValidCollection(col):
            return (col is not collection and
                    not UserCollection(col).outOfTheBoxCollection)

        # ultimately we'd like to use collection.appearsIn here rather
        # than sidebarCollections, and this becomes
        # [col for col in collection.appearsIn
        #  if not UserCollection(col).outOfTheBoxCollection)]
        sidebarCollections = [col for col in sidebarCollections
                              if IsValidCollection(col)]
        

        def DoDeleteAction(item):
            # useful as a separate function so we can return at any point
        
            # first test: if its in any user collection, then of
            # course we just want to remove it because we don't want
            # to affect other collections
            for sbCollection in sidebarCollections:
                if item in sbCollection:
                    collection.remove(item)
                    return
                
            # if a not-mine item doesn't exist anywhere else, then we
            # just want to delete it. But not-mine events shouldn't
            # all end up the trash, we just want to get rid of them
            # entirely
            if item not in mine:
                item.delete()
                return
            
            # finally, 'mine' items that don't exist anywhere else
            # just get added to the trash
            trash.add(item)
        
        # here's the meat of it
        for item in collection:
            DoDeleteAction(item)
        
    def onCollectionColorEvent(self, event):
        assert (self.contents.getSelectionRanges() is not None and
                len(self.contents.getSelectionRanges()) == 1)

        selectedItem = self.contents.getFirstSelectedItem()
        if (selectedItem is not None):
            UserCollection(selectedItem).color = event.color
        
    def onCollectionColorEventUpdateUI(self, event):
        # color of the selected collection
        selectedRanges = self.contents.getSelectionRanges()
        if selectedRanges is None or len(selectedRanges) != 1:
            event.arguments['Enable'] = False
        else:
            selectedItem = self.contents.getFirstSelectedItem()
            
            color = getattr(UserCollection(selectedItem), 'color', None)

            # the event contains the color, so we need to look at that
            # the only way to test for equality is by converting both
            # ColorType's to tuples
            event.arguments['Check'] = (color is not None and
                                        color.toTuple() == event.color.toTuple())

    def canRenameSelection(self):
        result = True

        selectionRanges = self.contents.getSelectionRanges()
        if selectionRanges is not None and len(self.contents.getSelectionRanges()) == 1:
            item = self.contents.getFirstSelectedItem()
            result = UserCollection (item).renameable
        
        return result

    def onRenameEventUpdateUI (self, event):
        event.arguments['Enable'] = self.canRenameSelection()

    def onRenameEvent (self, event):
        self.widget.EnableCellEditControl()

    def onToggleMineEvent(self, event):

        assert len(list(self.contents.iterSelection())) == 1
        mine = schema.ns('osaf.pim', self.itsView).mine
        for item in self.contents.iterSelection():
            if item in mine.sources:
                mine.removeSource(item)
            else:
                mine.addSource(item)

    def onToggleMineEventUpdateUI(self, event):
        selectionRanges = self.contents.getSelectionRanges()
        if selectionRanges is None or len(selectionRanges) != 1:
            event.arguments['Enable'] = False
            return

        selectedItem = self.contents.getFirstSelectedItem()
        if selectedItem is not None:
            if hasattr (UserCollection(selectedItem), "displayNameAlternatives"):
                collectionName = self.getNameAlternative (selectedItem)
            else:
                collectionName = selectedItem.getItemDisplayName()
        else:
            collectionName = ""

        arguments = {'collection': collectionName,
                     'kind': self.getNameAlternative (schema.ns('osaf.pim', self.itsView).allCollection)}

        if selectedItem is None:
            enabled = False
            menuTitle = _(u'Keep out of %(kind)s') % arguments
        elif UserCollection(selectedItem).outOfTheBoxCollection:
            enabled = False
            menuTitle = _(u'Keep "%(collection)s" out of %(kind)s') % arguments
        else:
            enabled = True
            mine = schema.ns('osaf.pim', self.itsView).mine
            if selectedItem not in mine.sources:
                menuTitle = _(u'Add "%(collection)s" to %(kind)s') % arguments
            else:
                menuTitle = _(u'Keep "%(collection)s" out of %(kind)s') % arguments

        event.arguments ['Text'] = menuTitle
        event.arguments['Enable'] = enabled

    def getNameAlternative (self, item):
        """
        Chandler has a very confusing feature that some collection's names change
        when the app bar is filtering, so we need to calculate the alternative name
        """
        if self.filterKind is None:
            key = "None"
        else:
            key = os.path.basename (str (self.filterKind.itsPath))
        return UserCollection(item).displayNameAlternatives [key]

class SidebarBranchPointDelegate(BranchPoint.BranchPointDelegate):

    tableTemplatePath = schema.One(schema.Text)
    calendarTemplatePath = schema.One(schema.Text)
    itemTupleKeyToCacheKey = schema.Mapping(schema.Item, initialValue = {})
    kindToKindCollectionCache = schema.Mapping(schema.Item, initialValue = {})

    schema.addClouds(
        copying = schema.Cloud(byRef=[itemTupleKeyToCacheKey])
    )

    def _mapItemToCacheKeyItem(self, item, hints):
        assert item is None or isinstance (item, ContentCollection) # The sidebar can only contain ContentCollections
        key = item
        sidebar = Block.Block.findBlockByName ("Sidebar")
        """
        collectionList should be in the order that the source items
        are overlayed in the Calendar view

        'item' in this case is more or less only used to determine
        order. We're not so much mapping item => cacheKeyItem, but
        rather mapping the sidebar's current state to a cacheKeyItem.
        """
        collectionList = []
        if not hints.get ("getOnlySelectedCollection", False):
            # make sure 'item' is at the front of the list so that
            # consumers know what the 'primary' collection is.
            if item is not None:
                collectionList.append (item)
            for theItem in sidebar.contents:
                if ((theItem in sidebar.checkedItems or sidebar.contents.isItemSelected (theItem)) and
                    theItem not in collectionList):
                    collectionList.append (theItem)

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
            
            tupleKey = tuple (tupleList)

            key = self.itemTupleKeyToCacheKey.get (tupleKey, None)
            if key is None:
                # we don't have a cached version of this key, so we'll
                # create a new one

                # Bug 5884: in order to overlay the allCollection remove
                # all 'mine' collections already included in collectionList.
                # Their inclusion in collectionList would be duplicated by
                # the inclusion of the allCollection and would invalidate
                # the resulting union.
                if len(collectionList) > 1:
                    pim_ns = schema.ns('osaf.pim', self.itsView)
                    if pim_ns.allCollection in collectionList:
                        mineCollections = pim_ns.mine.sources
                        collectionList = [c for c in collectionList
                                          if c not in mineCollections]

                if len(collectionList) == 1:
                    key = collectionList[0]
                else:
                    # eventually it would be nice to just make a
                    # Union here, but we need to make sure each
                    # withoutTrash gets called
                    combined = UnionCollection(itsView=self.itsView,
                                               sources=collectionList)
                    
                    # unioning Smart/AppCollections makes them
                    # lose their trash (which is good) so add it
                    # back by wrapping with an AppCollection
                    # (AppCollections are more transitory than
                    # SmartCollections)
                    key = AppCollection(itsView=self.itsView,
                                        source=combined)

                # create an INTERNAL name for this collection, just
                # for debugging purposes
                displayName = u" and ".join ([theItem.displayName for theItem in collectionList])

                # Handle filtered collections by intersecting with
                # the kind collection
                if filterKind is not None:
                    kindCollection = self.kindToKindCollectionCache.get(filterKind, None)
                    if kindCollection is None:
                        kindCollection = KindCollection(itsView=self.itsView,
                                                        kind=filterKind,
                                                        recursive=True)
                        self.kindToKindCollectionCache [filterKind] = kindCollection
                    newKey = IntersectionCollection(itsView=self.itsView,
                                                    sources=[key, kindCollection])
                    UserCollection(newKey).dontDisplayAsCalendar = UserCollection(key).dontDisplayAsCalendar
                    displayName += u" filtered by " + filterKind.itsName
                    key = newKey

                # Finally, create a UI wrapper collection to manage
                # things like selection and sorting
                newKey = IndexedSelectionCollection(itsView=self.itsView,
                                                    source=key)
                if len (newKey) > 0:
                    newKey.addSelectionRange (0)
                UserCollection(newKey).dontDisplayAsCalendar = \
                    UserCollection(key).dontDisplayAsCalendar
                key = newKey

                key.displayName = displayName

                key.collectionList = collectionList
                self.itemTupleKeyToCacheKey [tupleKey] = key
            else: # if key is None
                """
                We found the key, but we might still need to reorder
                collectionList. The list is kept sorted by the order
                of the collections as they overlay one another in the
                Calendar.  We don't bother to reorder when we're
                looking up a collection that isn't displayed in the
                summary view.
                """
                if item in sidebar.contents.iterSelection():
                    for new, old in zip(key.collectionList, collectionList):
                        if new is not old:
                            key.collectionList = collectionList
                            # Force setContents to be true even if the
                            # contents hasn't changed since the order
                            # of collectionList has changed
                            hints["sendSetContents"] = True
                            break
        return key

    def _makeBranchForCacheKey(self, keyItem):
        sidebar = Block.Block.findBlockByName("Sidebar")
        if (not UserCollection(keyItem).dontDisplayAsCalendar and
            sidebar.filterKind is schema.ns('osaf.pim.calendar.Calendar', self).CalendarEventMixin.getKind (self)):
                template = self.findPath (self.calendarTemplatePath)
                keyUUID = template.itsUUID
                branch = self.keyUUIDToBranch.get (keyUUID, None)
                if branch is None:
                    branch = self._copyItem(template, onlyIfReadOnly=True)
                    self.keyUUIDToBranch[keyUUID] = branch
        else:
            branch = self.findPath (self.tableTemplatePath)

        assert isinstance (branch, Block.Block)
        return self._copyItem(branch, onlyIfReadOnly=True)

    def _getContentsForBranch(self, branch, item, keyItem):
        return keyItem

    def getContentsCollection(self, item, collection):
        """
        The collection that the sidebar wants to deal with happens to
        actually be the collection that is selected in the
        sidebar. This ensures that the primary selected item in the
        sidebar is also the collection that gets passed down the views
        to the detail view
        """
        return item

class CPIATestSidebarBranchPointDelegate(BranchPoint.BranchPointDelegate):

    templatePath = schema.One(schema.Text)

    def _makeBranchForCacheKey(self, keyItem):
        branch = self.findPath (self.templatePath)

        assert isinstance (branch, Block.Block)
        return self._copyItem(branch, onlyIfReadOnly=True)
