
import sys
import wx.grid

from application import schema
from application.Application import mixinAClass

from osaf.pim import AbstractCollection
import application.dialogs.RecurrenceDialog as RecurrenceDialog

from Block import (
    RectangularChild,
    Block,
    WithoutSynchronizeWidget,
    IgnoreSynchronizeWidget
    )
import Styles
import DragAndDrop
import PimBlocks
import DrawingUtilities


class wxTableData(wx.grid.PyGridTableBase):
    def __init__(self, *arguments, **keywords):
        super (wxTableData, self).__init__ (*arguments, **keywords)
        self.defaultRWAttribute = wx.grid.GridCellAttr()
        self.defaultROAttribute = wx.grid.GridCellAttr()
        self.defaultROAttribute.SetReadOnly (True)

    def __del__ (self):
        self.defaultRWAttribute.DecRef()
        self.defaultROAttribute.DecRef()
        
    def GetNumberRows (self):
        return self.GetView().GetElementCount()

    def GetNumberCols (self):
        return self.GetView().GetColumnCount()

    def GetColLabelValue (self, column):
        grid = self.GetView()
        item = None
        
        if grid.GetElementCount() != 0:
            row = grid.GetGridCursorRow()
            itemIndex = grid.RowToIndex(row)
            if itemIndex != -1:
                item = grid.blockItem.contents [itemIndex]

        return grid.GetColumnHeading (column, item)

    def IsEmptyCell (self, row, column): 
        return False 

    def GetValue (self, row, column):
        return self.GetView().GetElementValue (row, column)

    def SetValue (self, row, column, value):
        self.GetView().SetElementValue (row, column, value) 

    def GetTypeName (self, row, column):
        return self.GetView().GetElementType (row, column)

    def GetAttr (self, row, column, kind):
        attribute = self.base_GetAttr (row, column, kind)
        if attribute is None:
            type = self.GetTypeName (row, column)
            delegate = AttributeEditors.getSingleton (type)
            attribute = self.defaultROAttribute
            grid = self.GetView()
            assert (row < self.GetNumberRows() and
                    column < self.GetNumberCols())

            if (not grid.blockItem.columnReadOnly[column] and
                not grid.ReadOnly (row, column)[0] and
                not delegate.ReadOnly (grid.GetElementValue (row, column))):
                attribute = self.defaultRWAttribute
            attribute.IncRef()
        return attribute

class wxTable(DragAndDrop.DraggableWidget, 
              DragAndDrop.DropReceiveWidget, 
              DragAndDrop.FileOrItemClipboardHandler,
              wx.grid.Grid):
    def __init__(self, parent, widgetID, characterStyle, headerCharacterStyle, *arguments, **keywords):
        if '__WXMAC__' in wx.PlatformInfo:
            theStyle=wx.BORDER_SIMPLE
        else:
            theStyle=wx.BORDER_STATIC
        """
          Giant hack. Calling event.GetEventObject in OnShow of
          application, while the object is being created cause the
          object to get the wrong type because of a
          "feature" of SWIG. So we need to avoid OnShows in this case.
        """
        IgnoreSynchronizeWidget(True, super(wxTable, self).__init__,
                                parent, widgetID, style=theStyle,
                                *arguments, **keywords)

        self.SetDefaultCellFont(Styles.getFont(characterStyle))
        self.SetLabelFont(Styles.getFont(headerCharacterStyle))
        self.SetColLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        self.SetRowLabelSize(0)
        self.AutoSizeRows()
        self.EnableDragCell(True)
        self.DisableDragRowSize()
        self.SetDefaultCellBackgroundColour(wx.WHITE)
        """
          Big fat hack. Since the grid is a scrolled window we set a border equal to the size
        of the scrollbar so the scroll bars won't show. Instead we should consider modifying
        grid adding a new style for not showing scrollbars.  Bug #2375
        """
        self.SetMargins(-wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X),
                        -wx.SystemSettings_GetMetric(wx.SYS_HSCROLL_Y))
        self.EnableCursor (False)
        background = wx.SystemSettings.GetColour (wx.SYS_COLOUR_HIGHLIGHT)
        self.SetLightSelectionBackground()

        self.Bind(wx.EVT_KILL_FOCUS, self.OnLoseFocus)
        self.Bind(wx.EVT_SET_FOCUS, self.OnGainFocus)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.OnItemDrag)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColumnDrag)
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelLeftClicked)


    def OnGainFocus (self, event):
        self.SetSelectionBackground (wx.SystemSettings.GetColour (wx.SYS_COLOUR_HIGHLIGHT))
        self.InvalidateSelection ()

    def OnLoseFocus (self, event):
        self.SetLightSelectionBackground()
        self.InvalidateSelection ()

    def OnLabelLeftClicked (self, event):
        assert (event.GetRow() == -1) # Currently Table only supports column headers
        blockItem = self.blockItem
        attributeName = blockItem.columnData [event.GetCol()]
        contents = blockItem.contents
        indexName = contents.indexName

        if indexName != attributeName:
            contents.indexName = attributeName
        else:
            contents.setDescending (indexName, not contents.isDescending(indexName))

        self.wxSynchronizeWidget()

    def SetLightSelectionBackground (self):
        background = wx.SystemSettings.GetColour (wx.SYS_COLOUR_HIGHLIGHT)
        background.Set ((background.Red() + 255) / 2,
                        (background.Green() + 255) / 2,
                         (background.Blue() + 255) / 2)
        self.SetSelectionBackground (background)

    def InvalidateSelection (self):
        lastRow = self.GetNumberCols() - 1
        
        selectionRanges = self.blockItem.contents.getSelectionRanges()
        gridTable = self.GetTable()
        for indexStart, indexEnd in selectionRanges:
            rowStart = self.IndexToRow(indexStart)
            rowEnd = self.IndexToRow(indexEnd)
            dirtyRect = wx.Rect()
            dirtyRect.SetTopLeft(self.CellToRect(rowStart, 0).GetTopLeft())
            dirtyRect.SetBottomRight(self.CellToRect(rowEnd,
                                                     lastRow).GetBottomRight())
            dirtyRect.OffsetXY (self.GetRowLabelSize(), self.GetColLabelSize())
            self.RefreshRect (dirtyRect)

    def OnInit (self):
        elementDelegate = self.blockItem.elementDelegate
        if not elementDelegate:
            elementDelegate = 'osaf.framework.blocks.ControlBlocks.AttributeDelegate'
        mixinAClass (self, elementDelegate)
        self.InitElementDelegate()
        """
          wxTableData handles the callbacks to display the elements of the
        table. Setting the second argument to True cause the table to be deleted
        when the grid is deleted.

          We've also got the usual chicken and egg problem: SetTable uses the
        table before initializing it's view so let's first set the view.
        """
        gridTable = wxTableData()
        gridTable.SetView (self)
        self.SetTable (gridTable, True, selmode=wx.grid.Grid.SelectRows)

        self.EnableGridLines (self.blockItem.hasGridLines)

    @WithoutSynchronizeWidget
    def OnRangeSelect(self, event):
        """
        Synchronize the grid's selection back into the row
        """
        blockItem = self.blockItem
        # Ignore notifications that arrise as a side effect of
        # changes to the selection
        blockItem.stopNotificationDirt()
        try:
            # map row ranges to index ranges 
            contents = self.blockItem.contents
            contents.setSelectionRanges ([])
            firstItemIndex = -1
            # ranges = [(event.GetTopRow(), event.GetBottomRow()),]
            for indexStart, indexEnd in self.SelectedIndexRanges():

                # We'll need the first selected index later..
                if firstItemIndex == -1 or firstItemIndex > indexStart:
                    firstItemIndex = indexStart

                contents.addSelectionRange ((indexStart, indexEnd))
                
            item = None
            if firstItemIndex != -1:
                item = blockItem.contents[firstItemIndex]

            if item is not blockItem.selectedItemToView:
                blockItem.selectedItemToView = item
                if item is not None:
                    gridTable = self.GetTable()
                    for columnIndex in xrange (gridTable.GetNumberCols()):
                        self.SetColLabelValue (columnIndex, gridTable.GetColLabelValue (columnIndex))
                """
                Widgets needs to clear the selection before setting a
                brand new selection, e.g. when you have some rows in a
                table selected and you click on another cell. So you
                get two OnRangeSelect calls, one to clear the old
                selection and another to set the new selection.

                We don't want to broadcast the first deselection if
                we're pretty sure we're actually going to select
                something next.

                It turns out that ignoring all the clear selections
                except when control is down skips the extra clear
                selections.
                """
                if (item is not None or event.Selecting() or
                    event.ControlDown()):
                    blockItem.PostSelectItems([item])
        finally:
            blockItem.startNotificationDirt()

        event.Skip()

    @WithoutSynchronizeWidget
    def OnSize(self, event):
        size = event.GetSize()
        widthMinusLastColumn = 0

        assert self.GetNumberCols() > 0, "We're assuming that there is at least one column"
        lastColumnIndex = self.GetNumberCols() - 1
        for column in xrange (lastColumnIndex):
            widthMinusLastColumn += self.GetColSize (column)
        lastColumnWidth = size.width - widthMinusLastColumn
        """
          This is a temporary fix to get around an apparent bug in
          grids.  We only want to adjust for scrollbars if they
          are present.  The -2 is a hack, without which the
          sidebar will grow indefinitely when resizing the window.
        """
        if (self.GetSize() == self.GetVirtualSize()):
            lastColumnWidth = lastColumnWidth - 2
        else:
            lastColumnWidth = lastColumnWidth - wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X) - 1
        if lastColumnWidth > 0:
            self.SetColSize (lastColumnIndex, lastColumnWidth)
            self.ForceRefresh()
        event.Skip()

    @WithoutSynchronizeWidget
    def OnColumnDrag(self, event):
        columnIndex = event.GetRowOrCol()
        self.blockItem.columnWidths [columnIndex] = self.GetColSize (columnIndex)

    def OnItemDrag(self, event):

        # To fix bug 2159, tell the grid to release the mouse now because the
        # grid object may get destroyed before it has a chance to later on:
        gridWindow = self.GetGridWindow()
        if gridWindow.HasCapture():
            gridWindow.ReleaseMouse()

        # If we don't have a selection, set it the firstRow of the event.
        contents = self.blockItem.contents
        if len (contents.getSelectionRanges()) == 0:
            firstRow = event.GetRow()
            selectedItemIndex = self.RowToIndex(firstRow)
            if selectedItemIndex != -1:
                contents.setSelectionRanges([(selectedItemIndex,
                                              selectedItemIndex)])
        self.DoDragAndDrop(copyOnly=True)

    def AddItems(self, itemList):
        
        collection = self.blockItem.GetCurrentContents(writable=True)
        assert collection, "Can't add items to readonly collection - should block before the drop"
        
        for item in itemList:
            item.addToCollection(collection)

    def OnRightClick(self, event):
        itemIndex = self.RowToIndex(event.GetRow())
        if itemIndex == -1:
            item = []
        else:
            item = self.blockItem.contents[itemIndex]
            
        self.blockItem.DisplayContextMenu(event.GetPosition(), item)

    def wxSynchronizeWidget(self, useHints=False):
        """
          A Grid can't easily redisplay its contents, so we write the following
        helper function to readjust everything after the contents change
        """

        self.SynchronizeDelegate()

        self.UpdateRowsAndColumns()
        
        # Either we should move selectedItemToView into the selection
        # that is part of the contents or get rid of it. This would
        # eliminate the following code that keeps it up to date and
        # when we install a different contents on a block it would get
        # restored to the correct value -- DJA
        contents = self.blockItem.contents
        selectedItemToView = self.blockItem.selectedItemToView
        if (selectedItemToView not in contents and
            selectedItemToView is not None):
            selectedItemToView = contents.getFirstSelectedItem()
            self.blockItem.selectedItemToView = selectedItemToView
            if selectedItemToView is None:
                self.blockItem.PostSelectItems([selectedItemToView])
            else:
                self.blockItem.PostSelectItems([])

        if selectedItemToView is not None:
            index = contents.index (selectedItemToView)
            contents.addSelectionRange (index)
            column = 0
            editAttributeNamed = getattr (self.blockItem, "editAttributeNamed", None)
            if editAttributeNamed is not None:
                try:
                    column = self.blockItem.columnData.index (editAttributeNamed)
                except ValueError:
                    editAttributeNamed = None

            cursorRow = self.IndexToRow(index)
            if cursorRow != -1:
                self.SetGridCursor (cursorRow, column)
                self.MakeCellVisible (cursorRow, column)
                if editAttributeNamed is not None:
                    self.EnableCellEditControl()
                    
    def UpdateRowsAndColumns(self):

        #Trim/extend the control's rows and update all values
        if self.blockItem.hideColumnHeadings:
            self.SetColLabelSize (0)
        else:
            self.SetColLabelSize (wx.grid.GRID_DEFAULT_COL_LABEL_HEIGHT)


        gridTable = self.GetTable()
        newColumns = gridTable.GetNumberCols()
        newRows = gridTable.GetNumberRows()

        oldColumns = self.GetNumberCols()
        oldRows = self.GetNumberRows()
        # update the widget to reflect the new or removed rows or
        # columns. Note that we're only telling the grid HOW MANY rows
        # or columns to add/remove - the per-cell callbacks will
        # determine what actual text to display in each cell

        def SendTableMessage(current, new, deleteMessage, addMessage):
            if new == current: return
            
            if new < current: 
                message = wx.grid.GridTableMessage(gridTable, deleteMessage,
                                                   new, current-new) 
            elif new > current: 
                message = wx.grid.GridTableMessage(gridTable, addMessage,
                                                   new-current) 
            self.ProcessTableMessage (message) 


        self.BeginBatch()
        SendTableMessage(oldRows, newRows,
                         wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                         wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED)
        
        SendTableMessage(oldColumns, newColumns,
                         wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
                         wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED)
        
        assert (self.GetNumberCols() == gridTable.GetNumberCols() and
                self.GetNumberRows() == gridTable.GetNumberRows())

        self.UpdateColumnWidths(newColumns)
        
        # Workaround for bug #3994
        wx.CallAfter (self.AdjustScrollbars)

        self.UpdateSelection(newColumns)
        self.EndBatch()

        # Update all displayed values
        gridTable = self.GetTable()
        message = wx.grid.GridTableMessage (gridTable, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES) 
        self.ProcessTableMessage (message)
        self.ForceRefresh () 

    def UpdateColumnWidths(self, columns):
        # update all column widths but the last one
        widthMinusLastColumn = 0
        for columnIndex in xrange (columns - 1):
            widthMinusLastColumn += self.blockItem.columnWidths[columnIndex]
            self.SetColSize (columnIndex, self.blockItem.columnWidths [columnIndex])

        # update the last column to fill the rest of the widget
        remaining = self.GetSize().width - widthMinusLastColumn
        # Adjust for scrollbar if it is present
        if (self.GetSize() != self.GetVirtualSize()):
            remaining = remaining - wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X) - 1
        if remaining > 0:
            self.SetColSize(columns - 1, remaining)
    
    def UpdateSelection(self, columns):
        """
        Update the grid's selection based on the collection's selection.

        If we previously had selected items, but now are not, then we
        probably just deleted all the selected items so we should try
        to select the next logical item in the collection.
        """

        # remember the first row in the old selection
        topLeftSelection = self.GetSelectionBlockTopLeft()
        
        newRowSelection = -1
        if len(topLeftSelection) > 0:
            newRowSelection = topLeftSelection[0][0]
        
        self.ClearSelection()
        contents = self.blockItem.contents
        for selectionStart,selectionEnd in contents.getSelectionRanges():
            # since we're selecting something, we don't need to
            # auto-select any rows
            newRowSelection = -1

            # now just do the selection update
            rowStart = self.IndexToRow(selectionStart)
            rowEnd = self.IndexToRow(selectionEnd)
            self.SelectBlock (rowStart, 0,
                              rowEnd, columns, True)

        # now auto-select a row if necessary
        if newRowSelection != -1:
            itemIndex = self.RowToIndex(newRowSelection)
            if itemIndex != -1:
                # we need to do this after the current
                # wxSynchronizeWidget is over
                wx.CallAfter(self.blockItem.PostSelectItems,
                             [self.blockItem.contents[itemIndex]])
                
    def GoToItem(self, item):
        if item != None:
            try:
                index = self.blockItem.contents.index (item)
                row = self.IndexToRow(index)
            except ValueError:
                item = None
        blockItem = self.blockItem
        if item is not None:
            blockItem.contents.addSelectionRange (index)
            blockItem.selectedItemToView = item
            self.SelectBlock (row, 0, row, self.GetColumnCount() - 1)
            self.MakeCellVisible (row, 0)
        else:
            blockItem.contents.setSelectionRanges([])
            blockItem.selectedItemToView = None
            self.ClearSelection()
        self.blockItem.PostSelectItems([item])

    def SelectedIndexRanges(self):
        """
        Uses RowRangeToIndexRange to convert the selected rows to
        selected indexes
        """
        # filter out columns from grid selection
        topLeftList = self.GetSelectionBlockTopLeft()
        bottomRightList = self.GetSelectionBlockBottomRight()
        selectedRows = ((row1, row2) for ((row1, col1), (row2, col2)) in
                zip(topLeftList, bottomRightList))
        
        return self.RowRangeToIndexRange(selectedRows)

    def RowRangeToIndexRange(self, rowRanges):
        """
        Given a list of row ranges, [(a,b), (c,d), ...], generate
        corresponding index ranges [(w,x), (y, z),..]
        """
        
        for (topRow, bottomRow) in rowRanges:
            indexStart = self.RowToIndex(topRow)
            indexEnd = self.RowToIndex(bottomRow)

            # this is the ugly case where the user "selects" a
            # section. It would be nice to avoid this case
            # alltogether by making table sections
            # un-selectable.
            if -1 not in (indexStart, indexEnd):
                yield (indexStart, indexEnd)
        

    def DeleteSelection (self, DeleteItemCallback=None, *args, **kwargs):
        def DefaultCallback(item, collection=self.blockItem.contents):
            collection.remove(item)
            
        blockItem = self.blockItem
        if DeleteItemCallback is None:
            DeleteItemCallback = DefaultCallback
        topLeftList = self.GetSelectionBlockTopLeft()
        bottomRightList = self.GetSelectionBlockBottomRight()

        
        selectionRanges = reversed(self.blockItem.contents.getSelectionRanges())

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
        
        newRowSelection = 0
        contents = blockItem.contents
        newSelectedItemIndex = -1
        for selectionStart,selectionEnd in selectionRanges:
            for itemIndex in xrange (selectionEnd, selectionStart - 1, -1):
                DeleteItemCallback(contents[itemIndex])
                # remember the last deleted row
                newSelectedItemIndex = itemIndex
        
        blockItem.contents.setSelectionRanges([])
        blockItem.selectedItemToView = None
        blockItem.itsView.commit()
        
        # now select the "next" item
        """
          We call wxSynchronizeWidget here because the postEvent
          causes the DetailView to call it's wxSynchrnoizeWidget,
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

    def SelectedItems(self):
        """
        Return the list of selected items.
        """
        selectionRanges = self.blockItem.contents.getSelectionRanges()
        if not selectionRanges:
            detailItem = self.blockItem.selectedItemToView
            if detailItem is not None:
                yield detailItem
                return
        
        for selectionStart, selectionEnd in selectionRanges:
            for index in xrange(selectionStart, selectionEnd+1):

                yield self.blockItem.contents [index]

class GridCellAttributeRenderer (wx.grid.PyGridCellRenderer):
    def __init__(self, type):
        super (GridCellAttributeRenderer, self).__init__ ()
        self.delegate = AttributeEditors.getSingleton (type)

    def Draw (self, grid, attr, dc, rect, row, column, isInSelection):
        """
          Currently only handles left justified multiline text
        """
        DrawingUtilities.SetTextColorsAndFont (grid, attr, dc, isInSelection)
        value = grid.GetElementValue (row, column)
        if __debug__:
            item, attributeName = value
            assert not item.isDeleted()
            
        self.delegate.Draw (dc, rect, value, isInSelection)

class GridCellAttributeEditor (wx.grid.PyGridCellEditor):
    def __init__(self, type):
        super (GridCellAttributeEditor, self).__init__ ()
        self.delegate = AttributeEditors.getSingleton (type)

    def Create (self, parent, id, evtHandler):
        """
          Create an edit control to edit the text
        """
        self.control = self.delegate.CreateControl(True, False, parent, id, None, None)
        self.SetControl (self.control)
        if evtHandler:
            self.control.PushEventHandler (evtHandler)

    def PaintBackground (self, *arguments, **keywords):
        """
          background drawing is done by the edit control
        """
        pass

    def BeginEdit (self, row,  column, grid):
        assert getattr(self, 'editingCell', None) is None
        self.editingCell = (row, column)
        
        item, attributeName = grid.GetElementValue (row, column)
        assert not item.isDeleted()
        item = RecurrenceDialog.getProxy(u'ui', item)
        
        self.initialValue = self.delegate.GetAttributeValue (item, attributeName)
        self.delegate.BeginControlEdit (item, attributeName, self.control)
        self.control.SetFocus()
        self.control.SelectAll()

    def EndEdit (self, row, column, grid):
        assert self.editingCell == (row, column)
        self.editingCell = None
        if hasattr (grid.blockItem, "editAttributeNamed"):
            del grid.blockItem.editAttributeNamed
        
        value = self.delegate.GetControlValue (self.control)
        item, attributeName = grid.GetElementValue (row, column)
        assert not item.isDeleted()
        item = RecurrenceDialog.getProxy(u'ui', item)

        if value == self.initialValue:
            changed = False
        # @@@ For now we do not want to allow users to blank out fields.  This should eventually be
        #  replaced by proper editor validation.
        elif value.strip() == '':
            changed = False
        else:
            changed = True
            # set the value using the delegate's setter, if it has one.
            try:
                attributeSetter = self.delegate.SetAttributeValue
            except AttributeError:
                grid.SetElementValue (row, column, value)
            else:
                attributeSetter (item, attributeName, value)
        self.delegate.EndControlEdit (item, attributeName, self.control)
        return changed

    def Reset (self):
        self.delegate.SetControlValue (self.control, self.initialValue)

    def GetValue (self):
        assert False # who needs this?
        return self.delegate.GetControlValue (self.control)

class Table (PimBlocks.FocusEventHandlers, RectangularChild):

    columnHeadings = schema.Sequence(schema.Text, required = True)
    columnHeadingTypes = schema.Sequence(schema.Text)
    columnData = schema.Sequence(schema.Text)
    columnWidths = schema.Sequence(schema.Integer, required = True)
    columnReadOnly = schema.Sequence(schema.Boolean)
    elementDelegate = schema.One(schema.Text, initialValue = '')
    selectedItemToView = schema.One(schema.Item, initialValue = None)
    editAttributeNamed = schema.One(schema.Text)
    hideColumnHeadings = schema.One(schema.Boolean, initialValue = False)
    characterStyle = schema.One(Styles.CharacterStyle)
    headerCharacterStyle = schema.One(Styles.CharacterStyle)
    hasGridLines = schema.One(schema.Boolean, initialValue = False)

    schema.addClouds(
        copying = schema.Cloud(
            byRef=[characterStyle,headerCharacterStyle,selectedItemToView]
        )
    )

    def __init__(self, *arguments, **keywords):
        super (Table, self).__init__ (*arguments, **keywords)

    def instantiateWidget (self):
        widget = wxTable (self.parentBlock.widget, 
                          Block.getWidgetID(self),
                          characterStyle=getattr(self, "characterStyle", None),
                          headerCharacterStyle=getattr(self, "headerCharacterStyle", None))        
        defaultName = "_default"
        widget.SetDefaultRenderer (GridCellAttributeRenderer (defaultName))
        aeKind = AttributeEditors.AttributeEditorMapping.getKind(\
            wx.GetApp().UIRepositoryView)
        for ae in aeKind.iterItems():
            key = ae.itsName
            if key != defaultName and not '+' in key:
                widget.RegisterDataType (key,
                                         GridCellAttributeRenderer (key),
                                         GridCellAttributeEditor (key))
        return widget

    def GetCurrentContents(self, writable=False):
        """
        The table's self.contents may contain a collectionList, in
        case this collection is composed of other collections. In this
        case, collectionList[0] is the 'primary' collection that
        should handle adds/deletes and other status updates
        """
        if hasattr(self.contents, 'collectionList'):
            collection = self.contents.collectionList[0]
        else:
            collection = self.contents
            
        # Sometimes you need a non-readonly collection. Should we be
        # checking if the collection has an 'add' attribute too?
        if not (writable and not collection.isReadOnly()):
            return collection

    def onSetContentsEvent (self, event):
        item = event.arguments ['item']
        if isinstance (item, AbstractCollection):
            self.setContentsOnBlock(item, event.arguments['collection'])

    def onSelectItemsEvent (self, event):
        items = event.arguments ['items']
        self.selectItems (items)
        if len(items)>0:
            self.selectedItemToView = items[0]
            
        editAttributeNamed = event.arguments.get ('editAttributeNamed')
        if editAttributeNamed is not None:
            self.widget.EnableCellEditControl (False)
            self.editAttributeNamed = editAttributeNamed

    def PostSelectItems(self, items):
        self.postEventByName("SelectItemsBroadcast",
                             {'items': items,
                              'collection': self.contentsCollection })
        
    def select (self, item):
        # polymorphic method used by scripts
        self.selectItems ([item])

    def selectItems (self, items):
        """
        Select the row corresponding to each item, and account for the
        fact that not all of the items are int the table Also make the
        first visible.
        """

        self.contents.setSelectionRanges([])
        for item in items:
            if item in self.contents:
                self.contents.selectItem(item)
            
# Ewww, yuk.  Blocks and attribute editors are mutually interdependent
import osaf.framework.attributeEditors
AttributeEditors = sys.modules['osaf.framework.attributeEditors']
