#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from osaf.framework.blocks import ControlBlocks
import wx, time
from osaf.framework.blocks import (
    Block, BranchPoint, DrawingUtilities, Table, wxTable, GridCellAttributeEditor
    )

from osaf.pim import (
    ContentCollection, IntersectionCollection, DifferenceCollection,
    UnionCollection, IndexedSelectionCollection,
    calendar
    )

from osaf.framework.prompts import promptYesNoCancel
from application.dialogs import RecurrenceDialog

from osaf import sharing, pim, search
import twisted.internet.error
from osaf.usercollections import UserCollection
from osaf.sharing import ChooseFormat, Share
from repository.item.Item import MissingClass
from lucene import JavaError as LuceneError
from osaf.pim import isDead
from application import schema
from i18n import ChandlerMessageFactory as _

from colorsys import rgb_to_hsv

import logging
logger = logging.getLogger(__name__)

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
        if row >= 0:
            itemIndex = self.RowToIndex(row)
            return (self.blockItem.contents [itemIndex],
                    self.blockItem.columns[column].attributeName)
        else:
            return (None, None)

class wxSidebar(wxTable):
    def __init__(self, *arguments, **keywords):
        super (wxSidebar, self).__init__ (*arguments, **keywords)
        gridWindow = self.GetGridWindow()
        # wxTable already binds to self.OnMouseEvents and self.OnLoseFocus for us,
        # and we want to override wxTables's implementation, so we don't need to
        # do another Bind
        gridWindow.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        gridWindow.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)

        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

    def onKeyDown(self, event):
        if self.IsCellEditControlEnabled():
            keyCode = event.GetKeyCode()
            if keyCode == wx.WXK_RETURN or keyCode == wx.WXK_NUMPAD_ENTER:
                self.DisableCellEditControl()
                return
        event.Skip()

    def OnSetFocus (self, event):
        # If we already have the focus, let's keep the focus
        if self.GetGridWindow() is wx.Window_FindFocus():
            event.Skip()
        # If we've got the hint to setFocus, let's keep the focus and delete the hint
        if hasattr (self, "setFocus"):
            del self.setFocus
            event.Skip()

    def OnLoseFocus (self, event):
        # Override OnLoseFocus because of an apparent bug in Linux where
        # it fails to send us mouse events when we capture the mouse and a
        # dialog comes up. See bug #10002: Trying to delete the out of the box Work
        # collection hangs Chandler until I siwtch workspace
        super (wxSidebar, self).OnLoseFocus (event)
        gridWindow = self.GetGridWindow()
        if (gridWindow.HasCapture()):
            gridWindow.ReleaseMouse()
        
    def CalculateCellRect (self, row):
        if row >= 0:
            cellRect = self.CellToRect (row, 0)
            cellRect.OffsetXY (self.GetRowLabelSize(), self.GetColLabelSize())
            left, top = self.CalcScrolledPosition (cellRect.GetLeft(), cellRect.GetTop())
            cellRect.SetLeft (left)
            cellRect.SetTop (top)
        else:
            cellRect = wx.Rect (0,0,0,0)
        return cellRect

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
            
            # If we end up here and we don't have the mouse capture I think there is a reasonable
            # chance that Chandler will crash. So commenting out the following assert is
            # probably unsafe. Each time I comment it in someone always comments it out -- DJA

            #assert gridWindow.HasCapture().
            if (gridWindow.HasCapture()):
                gridWindow.ReleaseMouse()
            for button in blockItem.buttons:
                if button.buttonState['overButton']:
                    button.buttonState['overButton'] = False
                    button.onOverButton (item)

        blockItem.stopNotificationDirt()
        try:
            if cellRect.InsideXY (x, y) and not self.IsCellEditControlEnabled():
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
                            overButton = imageRect.InsideXY (x, y)
                            button.buttonState = {'imageRect': imageRect,
                                                  'screenMouseDown': checked,
                                                  'blockChecked': checked,
                                                  'overButton': overButton}
                            if overButton:
                                button.onOverButton (item)

                            self.RefreshRect (imageRect)
                    for button in blockItem.buttons:
                        overButton = button.buttonState['imageRect'].InsideXY (x, y)
                        if button.buttonState['overButton'] != overButton:
                            button.buttonState['overButton'] = overButton
                            button.onOverButton (item)

            if hasattr (self, 'hoverImageRow'):
                if event.LeftDown():
                    for button in blockItem.buttons:
                        buttonState = button.buttonState
                        if (buttonState['imageRect'].InsideXY (x, y) and button.allowOverlay (item)):

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

            if event.LeftDown():
                if blockItem.contents.isItemSelected (item):
                    self.setFocus = True

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
                # create a recurrence proxy if adding a recurring item
                if getattr(item, pim.EventStamp.rruleset.name) is not None:
                    RecurrenceDialog.getProxy(u'ui', item).addToCollection(possibleCollection)
                else:
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
            elif sharing.isReadOnly(possibleCollection):
                dragResult = wx.DragNone

        return dragResult

    OnEnter = OnHover # Enter callback same as Hover callback (Drag & Drop)

    def OnLeave (self):
        # check if we had a hover row
        hoverRow = getattr (self, 'hoverRow', None)
        if hoverRow not in (None, wx.NOT_FOUND):
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
            try:
                ChooseFormat.importFileGuessFormat(filename,
                                                   self.blockItem.itsView, coll)
            except sharing.ICalendar.ICalendarImportError:
                wx.GetApp().CallItemMethodAsync(
                    "MainView", 'setStatusMessage',
                    _(u"Problem with file, import failed"))


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

    def DeleteSelection (self, prompt=True, *args, **kwargs):
        # The widget really isn't the right place to have common collection
        # deletion logic live, but for now it seems the widget has to be
        # intimately involved in deletion, so this is the most central place
        blockItem = self.blockItem
        contents = blockItem.contents
        view = blockItem.itsView
        viewsmain = schema.ns('osaf.views.main', view)

        # If there are any "mine" collections selected, ask the user
        # if we should be deleting the entire collection including the
        # items, or just some things
        shouldClearCollection = True
        pim_ns = schema.ns('osaf.pim', view)
        mine = pim_ns.mine

        mineMessage = _(u'Would you like to delete just the collection or the '
                        u'collection and the items within it as well?\n\n'
                        u'Note: Items you have added to other collections will '
                        u'not be deleted.')
        mineTextTable = {wx.ID_YES : _(u"Collection and Items"),
                         wx.ID_NO  : _(u"Collection only")}
        notMineMessage = _(u"Deleting %(collectionName)s will move its "
                           u'contents to the Trash\n\n'
                           u'Note: Items you have added to other collections '
                           u'will not be deleted.')
        
        # If we're editing the name now, stop.
        self.DisableCellEditControl()
        
        # don't pop up a dialog when running functional tests
        if prompt:

            # Prompt for unpublish, and unpublish
            for collection in contents.iterSelection():
                try:
                    share = sharing.getShare(collection)
                    if sharing.isSharedByMe(share):
                        dialog = wx.MessageDialog(wx.GetApp().mainFrame,
                            _(u"Deleting the collection will also unpublish it from the server.  Proceed?"),
                            _(u"Unpublish Confirmation"),
                            wx.YES_NO | wx.ICON_INFORMATION)
                        response = dialog.ShowModal()
                        dialog.Destroy()
                        if response == wx.ID_YES:
                            sharing.unpublish(collection)
                        else:
                            return
                except (sharing.CouldNotConnect, twisted.internet.error.TimeoutError):
                    logger.exception("Connection error during unpublish")
                    pass
                except:
                    logger.exception("Unknown error during unpublish")
                    pass

            for collection in contents.iterSelection():
                if len(collection) == 0:
                    continue
                dataDict = {'collectionName' : collection.displayName}
                if collection in mine.sources:
                    shouldClearCollection = \
                        promptYesNoCancel(mineMessage % dataDict,
                                          viewsmain.clearCollectionPref,
                                          textTable=mineTextTable,
                                          caption=_(u"Delete collection"))
    
                    if shouldClearCollection is None: # user pressed cancel
                        return
    
                else:
                    if wx.MessageBox (notMineMessage % dataDict,
                                      _(u"Delete collection"),
                                      style = wx.OK | wx.CANCEL,
                                      parent = wx.GetApp().mainFrame) != wx.OK:
                        return

        # save a list copy of the ranges because we're about to clear them.
        selectionRanges = list(reversed(contents.getSelectionRanges()))

        """
          Clear the selection before removing the elements from the collection
        otherwise our delegate will get called asking for deleted items
        """
        self.ClearSelection()
        # now delete rows - since we reverse sorted, the
        # "newSelectedItemIndex" will be the highest row that we're
        # not deleting
        
        # this is broken - we shouldn't be going through the widget
        # to delete the items! Instead, when items are removed from the
        # current collection, the widget should be notified to remove
        # the corresponding rows.
        # (that probably can't be fixed until ItemCollection
        # becomes Collection and notifications work again)

        newSelectedItemIndex = -1
        for selectionStart,selectionEnd in selectionRanges:
            for itemIndex in xrange (selectionEnd, selectionStart - 1, -1):
                collection = contents[itemIndex]
                # clear out the collection contents, if appropriate
                if shouldClearCollection:
                    blockItem.ClearCollectionContents(collection)
                elif collection in mine.sources:
                    for item in collection:
                        item._prepareToRemoveFromCollection(collection)
    
                sharing.unsubscribe(collection)
                collection.delete(True)

                # remember the last deleted row
                newSelectedItemIndex = itemIndex
        
        contents.clearSelection()
        view.commit()
        
        # now select the "next" item
        """
          We call wxSynchronizeWidget here because the postEvent
          causes the DetailView to call it's wxSynchronizeWidget,
          which calls layout, which causes us to redraw the table,
          which hasn't had time to get it's notificaitons so its data
          is out of synch and chandler Crashes. So I think the long
          term fix is to not call wxSynchronizeWidget here or in the
          DetailView and instead let the notifications cause
          wxSynchronizeWidget to be called. -- DJA
        """
        blockItem.synchronizeWidget()
        totalItems = len(contents)
        if totalItems > 0:
            if newSelectedItemIndex != -1:
                newSelectedItemIndex = min(newSelectedItemIndex, totalItems - 1)
            blockItem.PostSelectItems([contents[newSelectedItemIndex]])
        else:
            blockItem.PostSelectItems([])


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

        name = getattr (item, attribute)
        sidebar = grid.blockItem
        if sidebar.showSearch:
            searchMatches = UserCollection(item).searchMatches
            if searchMatches != 0:
                name = name + u"(" + unicode (searchMatches) + u")"
        """
          Draw the buttons
        """
        for button in sidebar.buttons:
            mouseOver = row == getattr (grid, 'hoverImageRow', wx.NOT_FOUND)
            image = button.getButtonImage (item, mouseOver, isSelected)
            if image is not None:
                imageRect = wxSidebar.GetRectFromOffsets (rect, button.buttonOffsets)
                dc.DrawBitmap (image, imageRect.GetLeft(), imageRect.GetTop(), True)

        textRect = wxSidebar.GetRectFromOffsets (rect, sidebar.editRectOffsets)
        textRect.Inflate (-1, -1)
        dc.SetClippingRect (textRect)
        DrawingUtilities.DrawClippedTextWithDots (dc, name, textRect)
        dc.DestroyClippingRegion()
        """
          Optionally Draw the "Out of the box", "User" collection line separator
          It's drawn if the item is the first "Out of the box" collection
          in the table
        """
        if not UserCollection (item).outOfTheBoxCollection: # i.e. a "User" collection
            for theRow in xrange (row-1, -1, -1):
                theItem, theAttribute = grid.GetTable().GetValue (theRow, col)
                if not UserCollection (theItem).outOfTheBoxCollection:
                    break
            else:
                dc.SetPen (wx.Pen (grid.GetGridLineColour()))
                dc.DrawLine (rect.GetLeft(), rect.GetTop(), rect.GetRight() + 1, rect.GetTop())


class SSSidebarEditor (GridCellAttributeEditor):
    """
      The sidebar design doesn't use any off the shelf parts, so we'll go roll a bunch
    of special purpose interface that can't be use anywhere else in CPIA.
    """

    def SetSize(self, rect):
        sidebar = Block.Block.findBlockByName ("Sidebar")
        textRect = wxSidebar.GetRectFromOffsets (rect, sidebar.editRectOffsets)
        self.control.SetRect (textRect);


class SSSidebarButton(schema.Item):
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

    buttonOwner = schema.One(initialValue = None)

    schema.addClouds(
        copying = schema.Cloud (byCloud = [buttonOwner])
    )

    def allowOverlay (self, item):
        return True

    def onOverButton (self, item):
        return

    # Save all SSSidebarButtons' buttonStates in a global dictionary, keyed
    # by UUID. Otherwise, SSidebarButtons, which aren't referenced by objects
    # outside of the repository, may be discarded (during prune) and reloaded
    # by the repository, but would be missing their nonpersistent state.
    # [Bug 9420]
    _allButtonStates = {}
    
    def _getButtonState(self):
        return self._allButtonStates[self.itsUUID]
        
    def _setButtonState(self, bs):
        self._allButtonStates[self.itsUUID] = bs

    buttonState = property(fget=_getButtonState, fset=_setButtonState)

class SSSidebarIconButton2 (SSSidebarButton):
    def getChecked (self, item):
        blockItem = self.buttonOwner
        return (blockItem.filterClass not in blockItem.disallowOverlaysForFilterClasses and
                UserCollection(item).checked)

    def setChecked (self, item, checked):
        UserCollection(item).checked = checked

    def onOverButton (self, item):
        sidebarWidget = self.buttonOwner.widget
        sidebarWidget.RefreshRect (self.buttonState['imageRect'])

    def getButtonImage (self, item, mouseOverFlag, isSelected):
        """
        The rules for naming icons are complicated, which is a
        reflection of complexity of our sidebar design. Here is a
        description of the rules:

        Names are made up of the following pieces:

        'Sidebar', ButtonName, iconName, Checked, MouseState, Deactive, '.png'

        They all begin with 'Sidebar', followed by ButtonName. Today,
        we only have two buttons named: 'Icon', and 'SharingIcon'. The
        rules for Icon follow -- see getButtonImage for the SharingIcon
        rules

        The ButtonName is followed by iconName. iconName is a property
        of the collection, e.g. the Dashboard has an iconName of
        'Dashboard'. The In, Out, and Trash collections have iconNames
        'In', 'Out' and 'Trash' respectively. Currently, new collections
        have no iconNme, so the iconName can be empty. Another
        property of the collection is whether or not the iconName has
        a class variation, in which case the iconName is appended with
        the class, e.g. EventStamp, MailStamp, or TaskStamp
        Currently, only the Dashboard collection has this
        property, so the iconNames for the Dashboard are 'Dashboard',
        'DashboardEventStamp', 'DashboardMailStamp' and
        'DashboardTaskStamp'.

        Another property of the collection, controlled by the allowOverlay
        attribute, determines whether or not it can be checked. If the
        collection is checked, Checked is the string "Checked". Next comes
        MouseState for checkable icons. It is the string "MouseDown" if the
        mouse is down over the icon, "MouseOver" if the mouse is up, but over
        the icon, and empty otherwise.

        Finally, comes Deactive, which equals "Deactive" when an collection
        is deactive, i.e. it can't be checked.

        Finally after looking up the icon we colorise it if the colorizeIcon
        attribute of the collection is True.
        """
        sidebarBlock = self.buttonOwner
        userCollection = UserCollection(item)

        imagePrefix = "Sidebar" + self.buttonName
        checked = self.getChecked (item)

        if mouseOverFlag and self.buttonState['overButton']:
            if self.buttonState['screenMouseDown'] == UserCollection(item).checked:
                mouseState = "MouseOver"
            else:
                mouseState = "MouseDown"
        else:
            mouseState = ""

        if checked:
            imagePrefix = imagePrefix + "Checked"

        selectedItem = sidebarBlock.contents.getFirstSelectedItem()
        if (not UserCollection (item).outOfTheBoxCollection and
            ( (selectedItem is not None and UserCollection (selectedItem).outOfTheBoxCollection) or
              sidebarBlock.filterClass in sidebarBlock.disallowOverlaysForFilterClasses) ):
            deactive = "Deactive"
        else:
            deactive = ""

        imageSuffix = ".png"

        iconName = userCollection.iconName
        filterClass = sidebarBlock.filterClass
        if userCollection.iconNameHasClassVariant and filterClass is not MissingClass:
            iconName += filterClass.__name__

        image = wx.GetApp().GetRawImage (imagePrefix + iconName + mouseState + deactive + imageSuffix)

        if image is not None:
            if userCollection.colorizeIcon:
                userCollection.ensureColor()
                color = userCollection.color
                rgbValue = DrawingUtilities.color2rgb(color.red, color.green, color.blue)
                hsvValue = rgb_to_hsv(*rgbValue)
                image.RotateHue (hsvValue[0])

            image = wx.BitmapFromImage (image)

        return image


class SSSidebarIconButton (SSSidebarButton):
    def getChecked (self, item):
        return UserCollection(item).checked

    def setChecked (self, item, checked):
        UserCollection(item).checked = checked

    def getButtonImage (self, item, mouseOverFlag, isSelected):
        """
        The rules for naming icons are complicated, which is a
        reflection of complexity of our sidebar design. Here is a
        description of the rules:

        Names are made up of the following pieces:

        'Sidebar', ButtonName, iconName, Checked, MouseState, Deactive, '.png'

        They all begin with 'Sidebar', followed by ButtonName. Today,
        we only have two buttons named: 'Icon', and 'SharingIcon'. The
        rules for Icon follow -- see getButtonImage for the SharingIcon
        rules

        The ButtonName is followed by IconName. IconName is a property
        of the collection, e.g. the Dashboard has an IconName of
        'Dashboard'. The In, Out, and Trash collections have names 'In',
        'Out' and 'Trash' respectively. Currently, new collections
        have no icon name, so the IconName can be empty. Another
        property of the collection is whether or not the IconName has
        a class variation, in which case the IconName is appended with
        the class name, e.g. EventStamp, MailStamp,
        TaskStamp.  Currently, only the Dashboard collection has this
        property, so the IconNames for the Dashboard are 'Dashboard',
        'DashboardEventStamp', 'DashboardMailStamp' and
        'DashboardTaskStamp'.


        Another property of the collection, controlled by the allowOverlay
        attribute, determines whether or not it can be checked. If the
        collection is checked, Checked is the string "Checked". Next comes
        MouseState for checkable icons. It is the string "MouseDown" if the
        mouse is down over the icon, "MouseOver" if the mouse is up, but over
        the icon, and empty otherwise.

        Finally, comes Deactive, which equals "Deactive" when an collection
        is deactive, i.e. it can't be checked.

        Finally after looking up the icon we colorise it if the colorizeIcon
        attribute of the collection is True.
        """
        sidebarBlock = self.buttonOwner
        userCollection = UserCollection(item)

        imagePrefix = "Sidebar" + self.buttonName
        mouseState = ""
        if self.allowOverlay (item):
            if self.getChecked (item):
                imagePrefix = imagePrefix + "Checked"
    
            if mouseOverFlag:
                if self.buttonState['screenMouseDown'] != self.buttonState['blockChecked']:
                    mouseState = "MouseDown"
                else:
                    mouseState = "MouseOver"

        selectedItem = sidebarBlock.contents.getFirstSelectedItem()
        if (not UserCollection (item).outOfTheBoxCollection and
            ( (selectedItem is not None and UserCollection (selectedItem).outOfTheBoxCollection) or
              sidebarBlock.filterClass in sidebarBlock.disallowOverlaysForFilterClasses) ):
            deactive = "Deactive"
        else:
            deactive = ""

        imageSuffix = ".png"

        iconName = userCollection.iconName
        filterClass = sidebarBlock.filterClass
        if (userCollection.iconNameHasClassVariant and
            filterClass is not MissingClass):
            iconName += filterClass.__name__

        image = wx.GetApp().GetRawImage (imagePrefix + iconName + mouseState + deactive + imageSuffix)

        if image is not None and userCollection.colorizeIcon:
            userCollection.ensureColor()
            color = userCollection.color
            rgbValue = DrawingUtilities.color2rgb(color.red, color.green, color.blue)
            hsvValue = rgb_to_hsv(*rgbValue)
            image.RotateHue (hsvValue[0])

        if image is not None:
            image = wx.BitmapFromImage (image)

        return image

    def allowOverlay (self, item):
        blockItem = self.buttonOwner
        selectedItem = blockItem.contents.getFirstSelectedItem()

        return (item is not None and
                UserCollection (item).allowOverlay and
                blockItem.filterClass not in blockItem.disallowOverlaysForFilterClasses and

                (selectedItem is None or
                 not UserCollection (selectedItem).outOfTheBoxCollection))


    def onOverButton (self, item):
        if self.allowOverlay (item):
            gridWindow = self.buttonOwner.widget.GetGridWindow()
            if self.buttonState['overButton']:
                if UserCollection(item).checked:
                    text = _(u"Remove overlay")
                else:
                    text = _(u"Overlay collection")
                gridWindow.SetToolTipString (text)
                gridWindow.GetToolTip().Enable (True)
            else:
                toolTip = gridWindow.GetToolTip()
                if toolTip:
                    gridWindow.GetToolTip().Enable (False)
                    gridWindow.SetToolTip (None)


class SSSidebarSharingButton (SSSidebarButton):
    def getButtonImage (self, item, mouseOverFlag, isSelected):
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
        mouseOver = ""
        mouseDown = ""
        imageSuffix = ".png"
        shared = ""
        partial = ""

        share = sharing.getShare(item)
        if share is not None:
            filterClass = self.buttonOwner.filterClass

            if share.filterClasses:
                partial = "Partial"
                if filterClass is not MissingClass:
                    className = "%s.%s" % (filterClass.__module__, filterClass.__name__)
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
        image = app.GetRawImage (imagePrefix + iconName + mouseDown + mouseOver + imageSuffix)

        # If that fails try the default image wihtout mouseOver
        if image is None:
            image = app.GetRawImage (imagePrefix + iconName + mouseDown + imageSuffix)

        # If that fails try the full icon name wihtout mouseDown and mouseOver
        if image is None:
            image = app.GetRawImage (imagePrefix + iconName + imageSuffix)

        if image is not None:
            if isSelected:
                # Set the brightness of the icon to match the brightness
                # of the text color (i.e. selection foreground color)
                # so it stands out against the selection background color
                color = self.buttonOwner.widget.GetSelectionForeground()
                rgbValue = DrawingUtilities.color2rgb(color.Red(), color.Green(), color.Blue())
                hsvValue = rgb_to_hsv(*rgbValue)
                image.SetBrightness (hsvValue[2])

            image = wx.BitmapFromImage (image)

        return image

    def onOverButton (self, item):
        gridWindow = self.buttonOwner.widget.GetGridWindow()
        if self.buttonState['overButton']:
            share = sharing.getShare(item)
            if share is not None:
                text = getattr (share, "error", False)
                if not text:
                    mine = schema.ns('osaf.pim', self.itsView).mine
                    inMine = item in mine.sources or UserCollection(item).outOfTheBoxCollection
                    if (sharing.isSharedByMe(share)):
                        if inMine:
                            text = _(u"Published share")
                        else:
                            text = _(u"Published share that is being kept out of the Dashboard")
                    else:
                        if inMine:
                            text = _(u"Subscription")
                        else:
                            text = _(u"Subscription that is being kept out of the Dashboard")

                    lastSynced = getattr(share, 'lastSuccess', None)
                    if lastSynced is not None:
                        format = calendar.DateTimeUtil.shortDateFormat.format
                        syncDay = format(self.itsView, lastSynced)
                        syncTime = calendar.formatTime(self.itsView, lastSynced)
                        text += _(u"; Last synced on %(day)s at %(time)s") % {"day": syncDay,
                                  "time": syncTime}

                gridWindow.SetToolTipString (text)
                gridWindow.GetToolTip().Enable (True)
        else:
            toolTip = gridWindow.GetToolTip()
            if toolTip:
                gridWindow.GetToolTip().Enable (False)
                gridWindow.SetToolTip (None)


class SidebarBlock(Table):
    filterClass = schema.One(schema.Class, defaultValue = MissingClass)

    showSearch = schema.One(schema.Boolean, defaultValue = False)

    disallowOverlaysForFilterClasses = schema.Sequence(
        schema.Class, initialValue = [],
    )

    buttons = schema.Sequence (inverse = SSSidebarButton.buttonOwner,
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
            byRef = [filterClass],
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

    def onClassParameterizedEvent(self, event):
        self.setPreferredClass(event.classParameter)

    def setShowSearch(self, showSearch):
        self.showSearch = showSearch
        self.postEventByName("SelectItemsBroadcast",
                             {'items':list(self.contents.iterSelection())})

    def setPreferredClass(self, filterClass, keepMissing=False):
        if (self.filterClass != filterClass and
            (not keepMissing or self.filterClass is not MissingClass)):

            # We need to update the click state of the toolbar as well.
            # By default we'll switch to all
            newFilterStamp = MissingClass
            buttonToSelect = self.findBlockByName("ApplicationBarAllButton")

            if filterClass is not MissingClass:
                toolBar = self.findBlockByName("ApplicationBar").widget
                for toolBarTool in toolBar.GetTools():
                    # The tool returned by GetTools isn't our Python object with the blockItem attribute
                    # so we'll have to look it up by it's Id.
                    toolBarToolBlock = Block.Block.idToBlock[toolBarTool.GetId()]
                    event = getattr (toolBarToolBlock, "event", None)
                    if event is not None:
                        buttonClass = getattr (event, "classParameter", None)
                        if buttonClass is not None and issubclass (filterClass, buttonClass):
                            newFilterStamp = buttonClass
                            buttonToSelect = toolBarToolBlock
                            break

            self.filterClass = newFilterStamp
            buttonToSelect.widget.selectTool()
            self.widget.Refresh()
            self.postEventByName("SelectItemsBroadcast",
                                 {'items':list(self.contents.iterSelection())})

    def onClassParameterizedEventUpdateUI (self, event):
        # check the appropriate menu item
        event.arguments['Check'] = event.classParameter == self.filterClass

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

    def onDeleteEvent(self, event):
        """
        Permanently remove the collection
        """
        prompt = not event.arguments.get('testing')
        self.widget.DeleteSelection(prompt=prompt)

    onRemoveEvent = onDeleteEvent

    def onRemoveEventUpdateUI(self, event):
        event.arguments['Enable'] = False

    def selectionContainsNoOOTB(self):
        """
        Returns False if selection is empty or contains any OOTB collections
        """
        enable = False
        for selectedItem in self.contents.iterSelection():
            if UserCollection(selectedItem).outOfTheBoxCollection:
                enable = False
                break
            else:
                enable = True
        return enable

    def onDeleteEventUpdateUI(self, event):
        """
        Disable if any selected collections are OOTB collections
        """
        event.arguments['Enable'] = self.selectionContainsNoOOTB()

    def onDuplicateEventUpdateUI(self, event):
        """
        Disable if any selected collections are OOTB collections
        """
        event.arguments['Enable'] = self.selectionContainsNoOOTB()

    def onDuplicateEvent(self, event):
        """
        Currently not available from any menu, Bug #8744
        """
        mine = schema.ns('osaf.pim', self.itsView).mine
        for item in self.contents.iterSelection():

            # don't duplicate an OOTB collection
            uc = UserCollection(item)
            if not uc.outOfTheBoxCollection:
                inMine = item in mine.sources
                item = item.copy(parent=self.getDefaultParent(self.itsView),
                                 cloudAlias="copying")
                
                # Give the copy a new color
                if hasattr(uc, 'color'):
                    del uc.color
                uc.ensureColor()

                # do not add a collection to 'mine' that has 'mine' in its structure
                # that causes 'mine' to become a recursive collection (bug 9369)
                if inMine:
                    mine.addSource(item)

                item.displayName = _(u"Copy of ") + item.displayName
                self.contents.add(item)
                self.postEventByName("SelectItemsBroadcast", {'items': [item]})

    def ClearCollectionContents(self, collection):
        """
        Remove items that should be removed, trash items that should
        be trashed. Note that we're not doing any proxy-aware code
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

        # deletion has side-effects on the collection's membership
        # therefore using a safe way to iterate and delete (bug 7945).
        view = collection.itsView
        for uuid in list(collection.iterkeys()):
            item = view.find(uuid)
            if not isDead(item):
                # if its in any user collection, then we just want to remove it
                # because we don't want to affect other collections
                for sbCollection in sidebarCollections:
                    if item in sbCollection:
                        collection.remove(item)
                        break
                else:
                    trash.add(item)

    def onCollectionColorEvent(self, event):
        assert (self.contents.getSelectionRanges() is not None and
                len(self.contents.getSelectionRanges()) == 1)

        selectedItem = self.contents.getFirstSelectedItem()
        if (selectedItem is not None):
            UserCollection(selectedItem).color = event.color

    def onCollectionColorEventUpdateUI(self, event):
        # color of the selected collection
        selectedItem = self.contents.getSelectedItemIfOnlyOneIsSelected()
        if (selectedItem is None or
            not UserCollection(selectedItem).colorizeIcon):
            event.arguments['Enable'] = False
        else:
            color = getattr(UserCollection(selectedItem), 'color', None)

            # the event contains the color, so we need to look at that
            # the only way to test for equality is by converting both
            # ColorType's to tuples
            event.arguments['Check'] = (color is not None and
                                        color.toTuple() == event.color.toTuple())

    def onRenameEventUpdateUI (self, event):
        selectedItem = self.contents.getSelectedItemIfOnlyOneIsSelected()
        event.arguments['Enable'] = selectedItem is not None and UserCollection (selectedItem).renameable

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
        selectedItem = second = None
        iterator = self.contents.iterSelection()
        try:
            selectedItem = iterator.next()
            second = iterator.next()
        except StopIteration:
            pass

        if selectedItem is None or second is not None:
            event.arguments['Enable'] = False
            event.arguments['Check'] = False
        else:
            menuTitle = _(u'&Keep out of Dashboard')

            if UserCollection(selectedItem).outOfTheBoxCollection:
                enabled = False
                checked = False
            else:
                enabled = True
                mine = schema.ns('osaf.pim', self.itsView).mine
                if selectedItem not in mine.sources:
                    checked = True
                else:
                    checked = False
            event.arguments['Check'] = checked
            event.arguments['Text'] = menuTitle
            event.arguments['Enable'] = enabled

    def render (self ):
        super (SidebarBlock, self).render()
        
        # Subscribe to notifications about shares since the state of the share
        # affects the display of the Sidebar
        self.itsView.watchKind (self, Share.getKind(self.itsView), 'shareChanged')

    def unRender (self ):
        super (SidebarBlock, self).unRender()
        self.itsView.unwatchKind (self, Share.getKind(self.itsView), 'shareChanged')

    def shareChanged (self, op, kind, uItem, dirties):
        """
        op is 'add', 'remove' or 'refresh'
          'add' means that a Share was created in the view
          'remove' means that a Share was removed in the view
          'refresh' means that a Share was changed in another view and that
                    you're now getting these changes via refresh()
        kind is the kind you called watchKind() on
        uItem is the UUID of the share item that changed
        dirties is the tuple of dirty attributes
        """
        share = self.find (uItem)
        if ('error' in dirties and
            (op == 'add' or op == 'refresh') and
            share.contents in self.contents):
            self.markDirty()
   

class SidebarBranchPointDelegate(BranchPoint.BranchPointDelegate):

    calendarTemplatePath = schema.One(schema.Text)
    dashboardTemplatePath = schema.One(schema.Text)
    searchResultsTemplatePath = schema.One(schema.Text)

    # Dictionary of template paths for eachh cache key
    keyUUIDToViewTemplatePath = schema.Mapping(schema.Text, defaultValue = {})

    # Dictionary of collections indexed by tuple key used as view cache key
    itemTupleKeyToCacheKey = schema.Mapping(schema.Item, initialValue = {})
    
    # Dictionary of FilterCollections indexed by stamp used to filter by app area
    stampToCollectionCache = schema.Mapping(schema.Item, initialValue = {})

    schema.addClouds(
        copying = schema.Cloud(byRef=[itemTupleKeyToCacheKey])
    )

    def getViewEventTemplate (self, event):
        viewTemplatePath = event.viewTemplatePath
        if viewTemplatePath == "Dashboard":
            sidebar = Block.Block.findBlockByName ("Sidebar")
            if sidebar.showSearch:
                viewTemplatePath = self.searchResultsTemplatePath
            else:
                viewTemplatePath = self.dashboardTemplatePath

        return viewTemplatePath

    def _mapItemToCacheKeyItem(self, item, hints):
        UC = UserCollection
        def wrapInIndexedSelectionCollection (key):
            # Finally, create a UI wrapper collection to manage
            # things like selection and sorting
            newKey = IndexedSelectionCollection(itsView=self.itsView,
                                                source=key, autoDelete=True)
            if len(newKey) > 0: # XXX if newKey: does not work; other code depends on index being created here
                newKey.addSelectionRange (0)
            UC(newKey).dontDisplayAsCalendar = UC(key).dontDisplayAsCalendar
            return newKey

        def wrapKey(oldKey, newKey, newName, startNewName=False):
            oldName = oldKey.displayName if not startNewName else ""
            # create an INTERNAL name for this collection, just for debugging
            newKey.displayName = oldName + newName
            UC(newKey).dontDisplayAsCalendar = UC(oldKey).dontDisplayAsCalendar
            return newKey

        sidebar = Block.Block.findBlockByName ("Sidebar")
        assert item is None or isinstance (item, ContentCollection) # The sidebar can only contain ContentCollections
        key = item
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
            # When item is none we have multiple selections
            if (item is None or
                (sidebar.filterClass not in sidebar.disallowOverlaysForFilterClasses and
                (not UserCollection (item).outOfTheBoxCollection))):
                for theItem in sidebar.contents:
                    if ((UserCollection(theItem).checked
                        or sidebar.contents.isItemSelected (theItem)) and
                         theItem not in collectionList):
                        collectionList.append (theItem)

        if collectionList:
            """
            tupleList is sorted so we always end up with one collection
            for any order of collections in the source
            """
            tupleList = [theItem.itsUUID for theItem in collectionList]
            tupleList.sort()

            filterClass = sidebar.filterClass
            if filterClass is not MissingClass:
                tupleList.append(filterClass)

            tupleList.append(sidebar.showSearch)
            tupleKey = tuple(tupleList)

            # Bug 5884: in order to overlay the allCollection remove
            # all 'mine' collections already included in collectionList.
            # Their inclusion in collectionList would be duplicated by
            # the inclusion of the allCollection and would invalidate
            # the resulting union.
            pim_ns = schema.ns('osaf.pim', self.itsView)
            if len(collectionList) > 1:
                if pim_ns.allCollection in collectionList:
                    mineCollections = pim_ns.mine.sources
                    collectionList = [c for c in collectionList
                                      if c not in mineCollections]

            key = self.itemTupleKeyToCacheKey.get(tupleKey, None)
            if key is not None and isDead(key): # item was deleted (bug 7338)
                del self.itemTupleKeyToCacheKey[tupleKey]
                key = None

            if (key is not None and
                [c for c in collectionList if c.itsUUID not in key.collectionList]):
                # See bug #6793: If a subscribed collection has been deleted, then resubscribed
                # our cached key will be stale because the subscribed collection will have
                # been removed but not added when resubscribed. In this case, the removed
                # collection will not be in the key's collectionList, so we need to
                # delete our key
                del self.itemTupleKeyToCacheKey [tupleKey]
                del key
                key = None
            if key is None:
                # we don't have a cached version of this key, so we'll
                # create a new one
                
                if len(collectionList) == 1:
                    key = collectionList[0]
                    # fix for bug 10726, Intersecting In or Out with MailStamp
                    # should be a no-op, since In and Out are already based
                    # on MailStamp's kind collection.  This is actually
                    # not quite right if In/Out have inclusions, but we're
                    # tolerating that for 0.7.0
                    if filterClass == pim.MailStamp:
                        if key in (pim_ns.inCollection, pim_ns.outCollection):
                            filterClass = MissingClass
                else:
                    # UnionCollection removes trash from its children before
                    # bringing them together
                    key = UnionCollection(itsView=self.itsView,
                                          sources=collectionList,
                                          autoDelete=True)

                # bug 10669, the final IndexedSelectionCollection will have
                # subindexes installed based on contentItems, so intersect all
                # collections displayed with contentItems
                newKey = IntersectionCollection(itsView=self.itsView,
                                                sources=[key, pim_ns.contentItems],
                                                autoDelete=True)
                name = u" and ".join(i.displayName for i in collectionList)
                key = wrapKey(key, newKey, name + " filtered by contentItems",
                              startNewName=True)

                if (filterClass is pim.EventStamp and
                    UserCollection(key).dontDisplayAsCalendar and
                    not sidebar.showSearch):
                    # filtering on calendar in the dashboard is a special case,
                    # we can't filter out both master events and intersect
                    # with events, so filter on nonMasterEvents
                    newKey = IntersectionCollection(itsView=self.itsView,
                                                    sources=[key, pim_ns.nonMasterEvents],
                                                    autoDelete=True)
                    key = wrapKey(key, newKey, " filtered by non-master events")

                else:
                    # Handle filtered collections by intersecting with
                    # the stamp collection
                    if filterClass is not MissingClass:
                        stampCollection = self.stampToCollectionCache.get(filterClass, None)
                        if stampCollection is None:
                            stampCollection = filterClass.getCollection(self.itsView)
                            self.stampToCollectionCache[filterClass] = stampCollection
                        newKey = IntersectionCollection(itsView=self.itsView,
                                                        sources=[key, stampCollection],
                                                        autoDelete=True)
                        key = wrapKey(key, newKey, " filtered by " + filterClass.__name__)
    
                    # don't include masterEvents in collections passed to 
                    # anything but the calendar view. Master events in tables should
                    # never be edited directly.  If view and filter are ever
                    # decoupled, this will need to be reworked.
                    if (not sidebar.showSearch and
                        filterClass is not pim.EventStamp):
        
                        newKey = DifferenceCollection(itsView=self.itsView,
                                                      sources=[key, pim_ns.masterEvents],
                                                      autoDelete=True)
                        key = wrapKey(key, newKey, " minus master events")
                    
                newKey = wrapInIndexedSelectionCollection(key)
                newKey.displayName = key.displayName + " ISC"
                newKey.collectionList = collectionList
                key = newKey
                self.itemTupleKeyToCacheKey[tupleKey] = newKey
                
            else: # if key is None
                # We found the key, but we might still need to reorder
                # collectionList. The list is kept sorted by the order
                # of the collections as they overlay one another in the
                # Calendar.  We don't bother to reorder when we're
                # looking up a collection that isn't displayed in the
                # summary view.
                if item in sidebar.contents.iterSelection():
                    for new, old in zip(key.collectionList, collectionList):
                        if new is not old:
                            key.collectionList = collectionList
                            # Force setContents to be true even if the
                            # contents hasn't changed since the order
                            # of collectionList has changed
                            hints["sendSetContents"] = True
                            break
                        
        if sidebar.showSearch:
            if hints.get ("search", True) and wx.GetApp().initialized:
                # Currently the UserCollection attributes are not watched on collections
                # so we just mark the sidebar dirty in this case. We should reconsider this
                # approach if we need to notice other UserCollection attributes or if we
                # get smart about only updating part of the sidebar when an attribute changes
                sidebar.markDirty()
                self.search (key)
            key = self.itemTupleKeyToCacheKey.get("Search", None)
            if key is None:
                key = wrapInIndexedSelectionCollection (schema.ns('osaf.pim', self.itsView).searchResults)
                key.displayName = u"Search Results"
                key.collectionList = [key]
                self.itemTupleKeyToCacheKey ["Search"] = key

        return key

    def search(self, searchCollection):

        try:
            view = self.itsView

            quickEntryBlock = Block.Block.findBlockByName ("ApplicationBarQuickEntry")
            mainView = Block.Block.findBlockByName("MainView")

            # make sure all changes are searchable
            mainView.setStatusMessage (_(u"Preparing to search..."))
            self.itsView.commit()
            self.itsView.repository.notifyIndexer(True)

            mainView.setStatusMessage (_(u"Searching..."))
            results = view.searchItems (quickEntryBlock.lastSearch)

            searchResultsUnfiltered = schema.ns('osaf.pim', view).searchResultsUnfiltered
            searchResultsUnfiltered.inclusions.clear()

            sidebarCollection = schema.ns("osaf.app", self).sidebarCollection
            for collection in sidebarCollection:
                UserCollection (collection).searchMatches = 0

            collectionList = searchCollection.collectionList

            app = wx.GetApp()
            itemsFound = 0
            searchAborted = False
            lastTime = time.time()
            for item in search.processResults(results):
                if item in searchCollection and item not in searchResultsUnfiltered:

                    searchAborted = itemsFound > 200 and (time.time() - lastTime) > 15
                    if searchAborted:
                        break
                    
                    searchResultsUnfiltered.add(item)
                    for collection in collectionList:
                        if item in collection:
                            UserCollection (collection).searchMatches += 1
                            
                    itemsFound = itemsFound + 1

            if itemsFound == 0:
                # For now we'll write a message to the status bar because it's easy
                # When we get more time to work on search, we should write the message
                # just below the search box in the toolbar.
                statusMessage = _(u"No results found")
            else:
                if searchAborted:
                    statusMessage = _(u"200 best results found (more exist, but search didn't have time to display them)")
                else:
                    statusMessage = _(u"%(itemsFound)i results found") % {"itemsFound": itemsFound}

            mainView.setStatusMessage (statusMessage)

        except LuceneError, error:
            exception = error.getJavaException()
            if (exception.getClass().getName() ==
                u'org.apache.lucene.queryParser.ParseException'):
                message = exception.getMessage()
            else:
                message = unicode(error)
            wx.MessageBox (_(u"An error occured during search.\n\nThe search engine reported the following error:\n\n%(message)s" ) % {"message": message},
                           _(u"Search Error"),
                           parent = app.mainFrame)
            mainView.setStatusMessage (_(u"An error occured during search"))


    def _makeBranchForCacheKey(self, keyItem):
        keyUUID = keyItem.itsUUID
        template = self.keyUUIDToViewTemplatePath.get (keyUUID, None)
        if template is None:
            sidebar = Block.Block.findBlockByName("Sidebar")
            if sidebar.showSearch:
                template = self.searchResultsTemplatePath
            else:
                if (not UserCollection(keyItem).dontDisplayAsCalendar and
                    sidebar.filterClass is pim.EventStamp):
                        template = self.calendarTemplatePath
                else:
                    template = self.dashboardTemplatePath
            self.keyUUIDToViewTemplatePath [keyUUID] = template

        parts = template.split('.')
        assert len (parts) >= 2
        name = parts.pop()
        template = getattr (schema.ns('.'.join(parts), self), name)
        keyUUID = template.itsUUID
        branch = self.keyUUIDToBranch.get (keyUUID, None)
        if branch is None:
            branch = self._copyItem(template, onlyIfReadOnly=True)
            self.keyUUIDToBranch[keyUUID] = branch
 
        assert isinstance (branch, Block.Block)
        return branch

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

    def setView (self, item, template):
        if item is not None:
            hints = {'search': False}
            keyUUID = self._mapItemToCacheKeyItem (item, hints).itsUUID
            if self.keyUUIDToViewTemplatePath.get (keyUUID, None) != template:
                self.keyUUIDToViewTemplatePath [keyUUID] = template
                del self.keyUUIDToBranch [keyUUID]

    def getView (self, item):
        hints = {'search': False}
        cachedItem = self._mapItemToCacheKeyItem (item, hints)
        if cachedItem is not None:
            keyUUID = cachedItem.itsUUID
            return self.keyUUIDToViewTemplatePath.get (keyUUID, None)
        return None
