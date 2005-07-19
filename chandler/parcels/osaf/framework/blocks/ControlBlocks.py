__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks"

import os, sys
from application.Application import mixinAClass
from application import schema
from Block import *
from ContainerBlocks import *
import DragAndDrop
from chandlerdb.item.ItemError import NoSuchAttributeError
import wx
import wx.html
import wx.gizmos
import wx.grid
import webbrowser # for opening external links
import osaf.framework.attributeEditors.AttributeEditors as AttributeEditors
from osaf.framework.blocks import DrawingUtilities
import application.dialogs.ReminderDialog as ReminderDialog
import Styles
from datetime import datetime, time, timedelta


class textAlignmentEnumType(schema.Enumeration):
    values = "Left", "Center", "Right"

class buttonKindEnumType(schema.Enumeration):
     values = "Text", "Image", "Toggle"

class Button(RectangularChild):

    characterStyle = schema.One(Styles.CharacterStyle)
    title = schema.One(schema.String)
    buttonKind = schema.One(buttonKindEnumType)
    icon = schema.One(schema.String)
    rightClicked = schema.One(BlockEvent)
    event = schema.One(BlockEvent)

    def instantiateWidget(self):
        id = self.getWidgetID(self)
        parentWidget = self.parentBlock.widget
        if self.buttonKind == "Text":
            button = wx.Button (parentWidget,
                                id,
                                self.title,
                                wx.DefaultPosition,
                                (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Image":
            bitmap = wx.GetApp().GetImage (self.icon)
            button = wx.BitmapButton (parentWidget,
                                      id,
                                      bitmap,
                                      wx.DefaultPosition,
                                      (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Toggle":
                button = wx.ToggleButton (parentWidget, 
                                          id, 
                                          self.title,
                                          wx.DefaultPosition,
                                          (self.minimumSize.width, self.minimumSize.height))
        elif __debug__:
            assert False, "unknown buttonKind"

        parentWidget.Bind(wx.EVT_BUTTON, self.buttonPressed, id=id)
        return button

    def buttonPressed(self, event):
        try:
            event = self.event
        except AttributeError:
            pass
        else:
            self.post(event, {'item':self})

                              
class wxCheckBox(ShownSynchronizer, wx.CheckBox):
    pass

class CheckBox(RectangularChild):

    event = schema.One(BlockEvent)
    title = schema.One(schema.String)
    schema.addClouds(
        copying = schema.Cloud(byCloud=[event])
    )

    def instantiateWidget(self):
        try:
            id = Block.getWidgetID(self)
        except AttributeError:
            id = 0

        parentWidget = self.parentBlock.widget
        checkbox = wxCheckBox (parentWidget,
                          id, 
                          self.title,
                          wx.DefaultPosition,
                          (self.minimumSize.width, self.minimumSize.height))
        checkbox.Bind(wx.EVT_CHECKBOX, wx.GetApp().OnCommand, id=id)
        return checkbox
    
class wxChoice(ShownSynchronizer, wx.Choice):
    pass

class Choice(RectangularChild):

    characterStyle = schema.One(Styles.CharacterStyle)
    event = schema.One(BlockEvent)
    choices = schema.Sequence(schema.String)
    schema.addClouds(
        copying = schema.Cloud(byCloud=[characterStyle])
    )

    def instantiateWidget(self):
        try:
            id = Block.getWidgetID(self)
        except AttributeError:
            id = 0

        parentWidget = self.parentBlock.widget
        choice = wxChoice (parentWidget,
                         id, 
                         wx.DefaultPosition,
                         (self.minimumSize.width, self.minimumSize.height),
                         self.choices)
        choice.Bind(wx.EVT_CHOICE, wx.GetApp().OnCommand, id=id)
        
        try:
            charStyle = self.characterStyle
        except AttributeError:
            charStyle = None
        choice.SetFont(Styles.getFont(charStyle))
        
        return choice

class ComboBox(RectangularChild):

    selection = schema.One(schema.String)
    choices = schema.Sequence(schema.String)
    itemSelected = schema.One(BlockEvent)

    def instantiateWidget(self):
        return wx.ComboBox (self.parentBlock.widget,
                            -1,
                            self.selection, 
                            wx.DefaultPosition,
                            (self.minimumSize.width, self.minimumSize.height),
                            self.choices)

    
class ContextMenu(RectangularChild):
    def displayContextMenu(self, parentWindow, position, data):
        menu = wx.Menu()
        for child in self.childrenBlocks:
            child.addItem(menu, data)
        parentWindow.PopupMenu(menu, position)
        menu.Destroy()
        

class ContextMenuItem(RectangularChild):

    event = schema.One(BlockEvent)
    title = schema.One(schema.String)
    schema.addClouds(
        copying = schema.Cloud(byCloud=[event])
    )

    def addItem(self, wxContextMenu, data):
        id = Block.getWidgetID(self)
        self.data = data
        wxContextMenu.Append(id, self.title)
        wxContextMenu.Bind(wx.EVT_MENU, wx.GetApp().OnCommand, id=id)

    
class wxEditText(ShownSynchronizer, 
                 DragAndDrop.DraggableWidget,
                 DragAndDrop.DropReceiveWidget,
                 DragAndDrop.TextClipboardHandler,
                 wx.TextCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxEditText, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterPressed, id=self.GetId())
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        minW, minH = arguments[-1] # assumes minimum size passed as last arg
        self.SetSizeHints(minW=minW, minH=minH)

    def OnEnterPressed(self, event):
        self.blockItem.postEventByName ('EnterPressed', {'text':self.GetValue()})
        event.Skip()

    def OnMouseEvents(self, event):
        # trigger a Drag and Drop if we're a single line and all selected
        if self.IsSingleLine() and event.LeftDown():
            selStart, selEnd = self.GetSelection()
            if selStart==0 and selEnd>1 and selEnd==self.GetLastPosition():
                if event.LeftIsDown(): # still down?
                    # have we had the focus for a little while?
                    if hasattr(self, 'focusedSince'):
                        if datetime.now() - self.focusedSince > timedelta(seconds=.2):
                            self.DoDragAndDrop()
                            return # don't skip, eat the click.
        event.Skip()

    def OnSetFocus(self, event):
        self.focusedSince = datetime.now()

    def OnKillFocus(self, event):
        del self.focusedSince



class textStyleEnumType(schema.Enumeration):
      values = "PlainText", "RichText"


class EditText(RectangularChild):

    characterStyle = schema.One(Styles.CharacterStyle)
    lineStyleEnum = schema.One(lineStyleEnumType)
    textStyleEnum = schema.One(textStyleEnumType, initialValue = 'PlainText')
    readOnly = schema.One(schema.Boolean, initialValue = False)
    textAlignmentEnum = schema.One(
        textAlignmentEnumType, initialValue = 'Left',
    )
    schema.addClouds(
        copying = schema.Cloud(byRef=[characterStyle])
    )

    def instantiateWidget(self):
        # Remove STATIC_BORDER: it wrecks padding on WinXP; was: style = wx.STATIC_BORDER
        style = 0
        if self.textAlignmentEnum == "Left":
            style |= wx.TE_LEFT
        elif self.textAlignmentEnum == "Center":
            style |= wx.TE_CENTRE
        elif self.textAlignmentEnum == "Right":
            style |= wx.TE_RIGHT

        if self.lineStyleEnum == "MultiLine":
            style |= wx.TE_MULTILINE
        else:
            style |= wx.TE_PROCESS_ENTER

        if self.textStyleEnum == "RichText":
            style |= wx.TE_RICH2

        if self.readOnly:
            style |= wx.TE_READONLY

        editText = wxEditText (self.parentBlock.widget,
                               -1,
                               "",
                               wx.DefaultPosition,
                               (self.minimumSize.width, self.minimumSize.height),
                               style=style, name=self.itsUUID.str64())

        editText.SetFont(Styles.getFont(getattr(self, "characterStyle", None)))
        return editText
    
class wxHTML(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())


class HTML(RectangularChild):

    url = schema.One(schema.String)

    def instantiateWidget (self):
        htmlWindow = wxHTML (self.parentBlock.widget,
                             Block.getWidgetID(self),
                             wx.DefaultPosition,
                             (self.minimumSize.width, self.minimumSize.height))
        if self.url:
            htmlWindow.LoadPage(self.url)
        return htmlWindow

 
class ListDelegate (object):
    """
      Default delegate for Lists that use the block's contents. Override
    to customize your behavior. You must implement GetElementValue.
    """
    def GetColumnCount (self):
        return len (self.blockItem.columnHeadings)

    def GetElementCount (self):
        return len (self.blockItem.contents)

    def GetElementType (self, row, column):
        return "String"

    def GetColumnHeading (self, column, item):
        return self.blockItem.columnHeadings [column]

    def ReadOnly (self, row, column):
        """
          Second argument should be True if all cells have the first value
        """
        return False, True


class AttributeDelegate (ListDelegate):
    def GetElementType (self, row, column):
        """
          An apparent bug in wxWidgets occurs when there are no items in a table,
        the Table asks for the type of cell 0,0
        """
        typeName = "_default"
        try:
            item = self.blockItem.contents [row]
        except IndexError:
            pass
        else:
            attributeName = self.blockItem.columnData [column]
            if item.itsKind.hasAttribute (attributeName):
                try:
                    typeName = item.getAttributeAspect (attributeName, 'type').itsName
                except NoSuchAttributeError:
                    # We special-case the non-Chandler attributes we want to use (_after_ trying the
                    # Chandler attribute, to avoid a hit on Chandler-attribute performance). If we
                    # want to add other itsKind-like non-Chandler attributes, we'd add more tests here.
                    raise
            elif attributeName == 'itsKind':
                typeName = 'Kind'
            else:
                try:
                    # to support properties, we get the value, and use its type's name.
                    value = getattr (item, attributeName)
                except AttributeError:
                    pass
                else:
                    typeName = type (value).__name__
        return typeName

    def GetElementValue (self, row, column):
        return self.blockItem.contents [row], self.blockItem.columnData [column]
    
    def SetElementValue (self, row, column, value):
        item = self.blockItem.contents [row]
        attributeName = self.blockItem.columnData [column]
        assert item.itsKind.hasAttribute (attributeName), "You cannot set a non-Chandler attribute value of an item (like itsKind)"
        item.setAttributeValue (attributeName, value)

    def GetColumnHeading (self, column, item):
        attributeName = self.blockItem.columnData [column]
        if item is not None:
            try:
                attribute = item.itsKind.getAttribute (attributeName)
            except NoSuchAttributeError:
                # We don't need to redirect non-Chandler attributes (eg, itsKind).
                heading = self.blockItem.columnHeadings[column]
            else:
                heading = attribute.getItemDisplayName()
                redirect = item.getAttributeAspect(attributeName, 'redirectTo')
                if redirect is not None:
                    names = redirect.split('.')
                    for name in names [:-1]:
                        item = item.getAttributeValue (name)
                    actual = item.itsKind.getAttribute (names[-1]).getItemDisplayName()
                    heading = "%s (%s)" % (heading, actual)
                self.blockItem.columnHeadings [column] = heading
        else:
            heading = self.blockItem.columnHeadings [column]
        return heading
    

class wxList (DragAndDrop.DraggableWidget, 
              DragAndDrop.ItemClipboardHandler,
              wx.ListCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxList, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnWXSelectItem, id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnItemDrag)

    def OnInit (self):
        elementDelegate = self.blockItem.elementDelegate
        if not elementDelegate:
            elementDelegate = 'osaf.framework.blocks.ControlBlocks.ListDelegate'
        mixinAClass (self, elementDelegate)
        
    def OnSize(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            size = self.GetClientSize()
            widthMinusLastColumn = 0
            assert self.GetColumnCount() > 0, "We're assuming that there is at least one column"
            for column in xrange (self.GetColumnCount() - 1):
                widthMinusLastColumn += self.GetColumnWidth (column)
            lastColumnWidth = size.width - widthMinusLastColumn
            if lastColumnWidth > 0:
                self.SetColumnWidth (self.GetColumnCount() - 1, lastColumnWidth)
        event.Skip()

    def OnWXSelectItem(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            item = self.blockItem.contents [event.GetIndex()]
            if self.blockItem.selection != item:
                self.blockItem.selection = item
            self.blockItem.postEventByName("SelectItemBroadcast", {'item':item})
        event.Skip()

    def OnItemDrag(self, event):
        self.DoDragAndDrop()

    def SelectedItems(self):
        """
        Return the list of items currently selected.
        """
        curIndex = -1
        itemList = []
        while True:
            curIndex = self.GetNextItem(curIndex, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            itemList.append(self.blockItem.contents [curIndex])
            if curIndex is -1:
                break
        return itemList

    def wxSynchronizeWidget(self):
        self.Freeze()
        self.ClearAll()
        self.SetItemCount (self.GetElementCount())
        for columnIndex in xrange (self.GetColumnCount()):
            self.InsertColumn (columnIndex,
                               self.GetColumnHeading (columnIndex, self.blockItem.selection),
                               width = self.blockItem.columnWidths [columnIndex])

        self.Thaw()

        if self.blockItem.selection:
            self.GoToItem (self.blockItem.selection)

    def OnGetItemText (self, row, column):
        """
          OnGetItemText won't be called if it's in the delegate -- WxPython won't
        call it if it's in a base class
        """
        return self.GetElementValue (row, column)

    def OnGetItemImage (self, item):
        return -1
    
    def GoToItem(self, item):
        self.Select (self.blockItem.contents.index (item))


class List(RectangularChild):

    columnHeadings = schema.Sequence(schema.String, required = True)
    columnData = schema.Sequence(schema.String)
    columnWidths = schema.Sequence(schema.Integer, required = True)
    elementDelegate = schema.One(schema.String, initialValue = '')
    selection = schema.One(schema.Item, initialValue = None)
    schema.addClouds(
        copying = schema.Cloud(byRef=[selection])
    )

    def __init__(self, *arguments, **keywords):
        super (List, self).__init__ (*arguments, **keywords)
        self.selection = None

    def instantiateWidget (self):
        return wxList (self.parentBlock.widget,
                       Block.getWidgetID(self),
                       style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.SUNKEN_BORDER|wx.LC_EDIT_LABELS)

    def onSelectItemEvent (self, event):
        """
          Display the item in the widget.
        """
        self.selection = event.arguments['item']
        self.widget.GoToItem (self.selection)


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
        """
          We've got the usual chicken & egg problems: wxWidgets calls GetNumberRows &
        GetNumberCols before wiring up the view instance variable
        """
        view = self.GetView()
        if view is not None:
            return view.GetElementCount()
        return 1

    def GetNumberCols (self):
        view = self.GetView()
        if view is not None:
            return view.GetColumnCount()
        return 1

    def GetColLabelValue (self, column):
        grid = self.GetView()
        if grid.GetElementCount():
            item = grid.blockItem.contents [grid.GetGridCursorRow()]
        else:
            item = None
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
            """
              An apparent bug in table asks for an attribute even when
            there are no entries in the table
            """
            grid = self.GetView()
            if (grid.GetElementCount() != 0 and
                not grid.blockItem.columnReadOnly[column] and
                not grid.ReadOnly (row, column)[0] and
                not delegate.ReadOnly (grid.GetElementValue (row, column))):
                attribute = self.defaultRWAttribute
            attribute.IncRef()
        return attribute
        

class wxTable(DragAndDrop.DraggableWidget, 
              DragAndDrop.DropReceiveWidget, 
              DragAndDrop.ItemClipboardHandler,
              wx.grid.Grid):
    def __init__(self, *arguments, **keywords):
        """
          Giant hack. Calling event.GetEventObject in OnShow of application, while the
        object is being created cause the object to get the wrong type because of a
        "feature" of SWIG. So we need to avoid OnShows in this case.
        """
        oldIgnoreSynchronizeWidget = wx.GetApp().ignoreSynchronizeWidget
        wx.GetApp().ignoreSynchronizeWidget = True
        try:
            super (wxTable, self).__init__ (*arguments, **keywords)
        finally:
            wx.GetApp().ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

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

    def OnGainFocus (self, event):
        self.SetSelectionBackground (wx.SystemSettings.GetColour (wx.SYS_COLOUR_HIGHLIGHT))
        self.InvalidateSelection ()

    def OnLoseFocus (self, event):
        self.SetLightSelectionBackground()
        self.InvalidateSelection ()

    def SetLightSelectionBackground (self):
        background = wx.SystemSettings.GetColour (wx.SYS_COLOUR_HIGHLIGHT)
        background.Set ((background.Red() + 255) / 2,
                        (background.Green() + 255) / 2,
                         (background.Blue() + 255) / 2)
        self.SetSelectionBackground (background)

    def InvalidateSelection (self):
        for range in self.blockItem.selection:
            dirtyRect = wx.Rect()
            dirtyRect.SetTopLeft (self.CellToRect (range[0], 0).GetTopLeft())
            dirtyRect.SetBottomRight (self.CellToRect (range[1], self.GetNumberCols() - 1).GetBottomRight())
            dirtyRect.OffsetXY (self.GetRowLabelSize(), self.GetColLabelSize())
            self.RefreshRect (dirtyRect)

    def OnInit (self):
        elementDelegate = self.blockItem.elementDelegate
        if not elementDelegate:
            elementDelegate = 'osaf.framework.blocks.ControlBlocks.AttributeDelegate'
        mixinAClass (self, elementDelegate)
        """
          wxTableData handles the callbacks to display the elements of the
        table. Setting the second argument to True cause the table to be deleted
        when the grid is deleted.

          We've also got the usual chicken and egg problem: SetTable uses the
        table before initializing it's view so GetView() returns none.
        """
        gridTable = wxTableData()

        self.currentRows = gridTable.GetNumberRows()
        self.currentColumns = gridTable.GetNumberCols()
        self.EnableGridLines (self.blockItem.hasGridLines)
        self.SetTable (gridTable, True, selmode=wx.grid.Grid.SelectRows)
    
    def OnRangeSelect(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            topLeftList = self.GetSelectionBlockTopLeft()
            self.blockItem.selection = []
            for topLeft, bottomRight in zip (topLeftList,
                                             self.GetSelectionBlockBottomRight()):
                self.blockItem.selection.append ([topLeft[0], bottomRight[0]])
           
            topLeftList.sort()
            try:
                (row, column) = topLeftList [0]
            except IndexError:
                item = None
            else:
                item = self.blockItem.contents [row]

            if item is not self.blockItem.selectedItemToView:
                self.blockItem.selectedItemToView = item
                if item is not None:
                    gridTable = self.GetTable()
                    for columnIndex in xrange (gridTable.GetNumberCols()):
                        self.SetColLabelValue (columnIndex, gridTable.GetColLabelValue (columnIndex))
                """
                  So happens that under some circumstances widgets needs to clear the selection before
                setting a new selection, e.g. when you have some rows in a table selected and you click
                on another cell. However, we need to catch changes to the selection in OnRangeSelect to
                keep track of the selection and broadcast selection changes to other blocks. So under
                some circumstances you get two OnRangeSelect calls, one to clear the selection and another
                to set the new selection. When the first OnRangeSelect is called to clear the selection
                we used to broadcast a select item event with None as the selection. This has two
                unfortunate side effects: it causes other views (e.g. the detail view) to draw blank
                and it causes the subsequent call to OnRangeSelect to not occur, causing the selection
                to vanish.
                  It turns out that ignoring all the clear selections except when control is down
                skips the extra clear selections.
                """
                if (item is not None or event.Selecting() or event.ControlDown()):
                    self.blockItem.postEventByName("SelectItemBroadcast", {'item':item})
                
        event.Skip()

    def OnSize(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            size = event.GetSize()
            widthMinusLastColumn = 0

            assert self.GetNumberCols() > 0, "We're assuming that there is at least one column"
            lastColumnIndex = self.GetNumberCols() - 1
            for column in xrange (lastColumnIndex):
                widthMinusLastColumn += self.GetColSize (column)
            lastColumnWidth = size.width - widthMinusLastColumn
            """
              This is a temporary fix to get around an apparent bug in grids.  We only want to adjust
            for scrollbars if they are present.  The -2 is a hack, without which the sidebar will grow
            indefinitely when resizing the window.
            """
            if (self.GetSize() == self.GetVirtualSize()):
                lastColumnWidth = lastColumnWidth - 2
            else:
                lastColumnWidth = lastColumnWidth - wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
            if lastColumnWidth > 0:
                self.SetColSize (lastColumnIndex, lastColumnWidth)
                self.ForceRefresh()
        event.Skip()

    def OnColumnDrag(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            columnIndex = event.GetRowOrCol()
            self.blockItem.columnWidths [columnIndex] = self.GetColSize (columnIndex)

    def OnItemDrag(self, event):

        # To fix bug 2159, tell the grid to release the mouse now because the
        # grid object may get destroyed before it has a chance to later on:
        gridWindow = self.GetGridWindow()
        if gridWindow.HasCapture():
            gridWindow.ReleaseMouse()

        # make sure SelectedItemToView is up-to-date (shouldn't need to do this!)
        if not self.blockItem.selection:
            firstRow = event.GetRow()
            self.blockItem.selection = [[firstRow, firstRow]]
        self.DoDragAndDrop(copyOnly=True)

    def AddItems(self, itemList):
        for item in itemList:
            self.blockItem.contents.add (item)

    def OnRightClick(self, event):
        self.blockItem.DisplayContextMenu(event.GetPosition(),
                                          self.blockItem.contents [event.GetRow()])

    def wxSynchronizeWidget(self):
        """
          A Grid can't easily redisplay its contents, so we write the following
        helper function to readjust everything after the contents change
        """
        #Trim/extend the control's rows and update all values

        if self.blockItem.hideColumnHeadings:
            self.SetColLabelSize (0)
        else:
            self.SetColLabelSize (wx.grid.GRID_DEFAULT_COL_LABEL_HEIGHT)

        gridTable = self.GetTable()
        newRows = gridTable.GetNumberRows()
        newColumns = gridTable.GetNumberCols()

        self.BeginBatch()
        for current, new, deleteMessage, addMessage in [
            (self.currentRows, newRows, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED), 
            (self.currentColumns, newColumns, wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED)]: 
                if new < current: 
                    message = wx.grid.GridTableMessage (gridTable, deleteMessage, new, current-new) 
                    self.ProcessTableMessage (message) 
                elif new > current: 
                    message = wx.grid.GridTableMessage (gridTable, addMessage, new-current) 
                    self.ProcessTableMessage (message) 
        self.currentRows = newRows
        self.currentColumns = newColumns
        # update all column widths but the last one
        widthMinusLastColumn = 0
        for columnIndex in xrange (newColumns - 1):
            widthMinusLastColumn += self.blockItem.columnWidths[columnIndex]
            self.SetColSize (columnIndex, self.blockItem.columnWidths [columnIndex])

        # update the last column to fill the rest of the widget
        remaining = self.GetSize().width - widthMinusLastColumn
        # Adjust for scrollbar if it is present
        if (self.GetSize() != self.GetVirtualSize()):
            remaining = remaining - wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
        if remaining > 0:
            self.SetColSize(newColumns - 1, remaining)
        
        self.ClearSelection()
        firstSelectedRow = None
        if len (self.blockItem.contents) > 0:
            for range in self.blockItem.selection:
                if firstSelectedRow is None:
                    firstSelectedRow = range[0]
                self.SelectBlock (range[0], 0, range[1], newColumns, True)
        else:
            self.blockItem.selection = []
        self.EndBatch() 

        #Update all displayed values
        message = wx.grid.GridTableMessage (gridTable, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES) 
        self.ProcessTableMessage (message) 
        self.ForceRefresh () 

        if (self.blockItem.selectedItemToView not in self.blockItem.contents and
            firstSelectedRow is not None):
            selectedItemToView = self.blockItem.contents [firstSelectedRow]
            self.blockItem.selectedItemToView = selectedItemToView
            self.blockItem.postEventByName("SelectItemBroadcast", {'item':selectedItemToView})

        try:
            row = self.blockItem.contents.index (self.blockItem.selectedItemToView)
        except ValueError:
            pass
        else:
            self.MakeCellVisible (row, 0)

    def GoToItem(self, item):
        if item != None:
            try:
                row = self.blockItem.contents.index (item)
            except ValueError:
                item = None
        if item is not None:
            self.blockItem.selection.append ([row, row])
            self.blockItem.selectedItemToView = item
            self.SelectBlock (row, 0, row, self.GetColumnCount() - 1)
            self.MakeCellVisible (row, 0)
        else:
            self.blockItem.selection = []
            self.blockItem.selectedItemToView = None
            self.ClearSelection()
        self.blockItem.postEventByName("SelectItemBroadcast", {'item':item})

    def DeleteSelection (self):
        topLeftList = self.GetSelectionBlockTopLeft()
        bottomRightList = self.GetSelectionBlockBottomRight()
        """
          Clear the selection before removing the elements from the collection
        otherwise our delegate will get called asking for deleted items
        """
        self.ClearSelection()
        
        # build up a list of selection ranges [[tl1, br1], [tl2, br2]]
        selectionRanges = []
        for topLeft in topLeftList:
            bottomRight = bottomRightList.pop (0)
            selectionRanges.append ([topLeft[0], bottomRight[0]])
        selectionRanges.sort()
        selectionRanges.reverse()

        # now delete rows - since we reverse sorted, the 
        # "newRowSelection" will be the highest row that we're not deleting
        newRowSelection = 0
        contents = self.blockItem.contents
        for range in selectionRanges:
            for row in xrange (range[1], range [0] - 1, -1):
                contents.remove (contents [row])
                newRowSelection = row

        self.blockItem.selection = []
        self.blockItem.selectedItemToView = None
        self.blockItem.itsView.commit()
        
        # now select the "next" item
        totalItems = len(contents)
        """
          We call wxSynchronizeWidget here because the postEvent causes the DetailView
        to call it's wxSynchrnoizeWidget, which calls layout, which causes us to redraw
        the table, which hasn't had time to get it's notificaitons so its data is out
        of synch and chandler Crashes. So I think the long term fix is to not call
        wxSynchronizeWidget here or in the DetailView and instead let the notifications
        cause wxSynchronizeWidget to be called. -- DJA
        """
        self.wxSynchronizeWidget()
        if totalItems > 0:
            newRowSelection = min(newRowSelection, totalItems - 1)
            self.blockItem.postEventByName("SelectItemBroadcast", {'item':contents[newRowSelection]})

    def SelectedItems(self):
        """
        Return the list of selected items.
        """
        selectionRanges = self.blockItem.selection
        if not selectionRanges:
            detailItem = self.blockItem.selectedItemToView
            if detailItem is None:
                return []
            else:
                return [detailItem]
        itemList = []
        for selectionRange in selectionRanges:
            for index in xrange(selectionRange[0], selectionRange[1]+1):
                itemList.append(self.blockItem.contents [index])
        return itemList

    """
    Cut and Paste support for Grid cells.
    When a single cell is selected, these methods delegate the
        cut and paste operations to the attribute editor.
    """
    def _DelegateCellEdit(self, operation):
        # maybe we're in grid select - see if the widget there can do it.
        method = getattr(super(wxTable, self), operation) # super method to fall back on
        cursorPos = (self.GetGridCursorRow(), self.GetGridCursorCol())
        editor = self.GetCellEditor(*cursorPos)
        try:
            editingCell = editor.editingCell
        except AttributeError:
            return method()
        if editingCell == cursorPos:
            try:
                method = getattr(editor.control, operation)
            except AttributeError:
                pass
        return method()

    def CanCopy(self):
        return self._DelegateCellEdit('CanCopy')

    def Copy(self):
        return self._DelegateCellEdit('Copy')

    def CanCut(self):
        return self._DelegateCellEdit('CanCut')

    def Cut(self):
        return self._DelegateCellEdit('Cut')

    def CanPaste(self):
        return self._DelegateCellEdit('CanPaste')

    def Paste(self):
        return self._DelegateCellEdit('Paste')

class GridCellAttributeRenderer (wx.grid.PyGridCellRenderer):
    def __init__(self, type):
        super (GridCellAttributeRenderer, self).__init__ ()
        self.delegate = AttributeEditors.getSingleton (type)

    def Draw (self, grid, attr, dc, rect, row, column, isInSelection):
        """
          Currently only handles left justified multiline text
        """
        DrawingUtilities.SetTextColorsAndFont (grid, attr, dc, isInSelection)
        item, attributeName = grid.GetElementValue (row, column)
        self.delegate.Draw (dc, rect, item, attributeName, isInSelection)

class GridCellAttributeEditor (wx.grid.PyGridCellEditor):
    def __init__(self, type):
        super (GridCellAttributeEditor, self).__init__ ()
        self.delegate = AttributeEditors.getSingleton (type)

    def Create (self, parent, id, evtHandler):
        """
          Create an edit control to edit the text
        """
        self.control = self.delegate.CreateControl(True, parent, id, None, None)
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
        self.initialValue = self.delegate.GetAttributeValue (item, attributeName)
        self.delegate.BeginControlEdit (item, attributeName, self.control)
        self.control.SetFocus()

    def EndEdit (self, row, column, grid):
        assert self.editingCell == (row, column)
        self.editingCell = None

        value = self.delegate.GetControlValue (self.control)
        item, attributeName = grid.GetElementValue (row, column)
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

class Table (RectangularChild):

    columnHeadings = schema.Sequence(schema.String, required = True)
    columnHeadingTypes = schema.Sequence(schema.String)
    columnData = schema.Sequence(schema.String)
    columnWidths = schema.Sequence(schema.Integer, required = True)
    columnReadOnly = schema.Sequence(schema.Boolean)
    elementDelegate = schema.One(schema.String, initialValue = '')
    selection = schema.Sequence(schema.List, initialValue = [])
    selectedItemToView = schema.One(schema.Item, initialValue = None)
    hideColumnHeadings = schema.One(schema.Boolean, initialValue = False)
    characterStyle = schema.One(Styles.CharacterStyle)
    headerCharacterStyle = schema.One(Styles.CharacterStyle)
    hasGridLines = schema.One(schema.Boolean, initialValue = False)

    schema.addClouds(
        copying = schema.Cloud(
            byCloud=[selectedItemToView],
            byRef=[characterStyle,headerCharacterStyle]
        )
    )

    def __init__(self, *arguments, **keywords):
        super (Table, self).__init__ (*arguments, **keywords)

    def instantiateWidget (self):
        if '__WXMAC__' in wx.PlatformInfo:
            widget = wxTable (self.parentBlock.widget, Block.getWidgetID(self), style=wx.BORDER_SIMPLE)
        else:
            widget = wxTable (self.parentBlock.widget, Block.getWidgetID(self), style=wx.BORDER_STATIC)                
        widget.SetDefaultCellFont(Styles.getFont(getattr(self, "characterStyle", None)))
        widget.SetLabelFont(Styles.getFont(getattr(self, "headerStyle", None)))
        defaultName = "_default"
        widget.SetDefaultRenderer (GridCellAttributeRenderer (defaultName))
        aeKind = AttributeEditors.AttributeEditor.getKind(wx.GetApp().UIRepositoryView)
        for ae in aeKind.iterItems():
            key = ae.itsName
            if key != defaultName and not '+' in key:
                widget.RegisterDataType (key,
                                         GridCellAttributeRenderer (key),
                                         GridCellAttributeEditor (key))
        return widget

    def onSetContentsEvent (self, event):
        item = event.arguments ['item']
        if isinstance (item, ItemCollection):
            self.contents = item

    def onSelectItemEvent (self, event):
        item = event.arguments ['item']
        if item != self.selectedItemToView:
            self.selectedItemToView = item
            row = -1
            if item is not None:
                try:
                    row = self.contents.index (item)
                except ValueError:
                    pass
            if row < 0:
                self.widget.ClearSelection()
            else:
                self.widget.SelectBlock (row, 0, row, self.widget.GetColumnCount() - 1)
                self.widget.MakeCellVisible (row, 0)

    def onModifyContentsEvent(self, event):
        super (Table, self).onModifyContentsEvent (event)
        if event.selectFirstItem:
            self.onSelectItemEvent (event)
            self.postEventByName ('SelectItemBroadcast', {'item':event.arguments ['item']})

    def onRemoveEvent (self, event):
        self.widget.DeleteSelection()
        
    def onRemoveEventUpdateUI (self, event):
        readOnly = True
        for range in self.selection:
            for row in xrange (range[0], range[1] + 1):
                readOnly, always = self.widget.ReadOnly (row, 0)
                if not readOnly or always:
                    break

        event.arguments['Enable'] = not readOnly
        return True


class radioAlignEnumType(schema.Enumeration):
      values = "Across", "Down"


class RadioBox(RectangularChild):

    title = schema.One(schema.String)
    choices = schema.Sequence(schema.String)
    radioAlignEnum = schema.One(radioAlignEnumType)
    itemsPerLine = schema.One(schema.Integer)
    event = schema.One(BlockEvent)
    schema.addClouds(
        copying = schema.Cloud(byCloud=[event])
    )

    def instantiateWidget(self):
        if self.radioAlignEnum == "Across":
            dimension = wx.RA_SPECIFY_COLS
        elif self.radioAlignEnum == "Down":
            dimension = wx.RA_SPECIFY_ROWS
        elif __debug__:
            assert False, "unknown radioAlignEnum"
                                    
        return wx.RadioBox (self.parentBlock.widget,
                            -1,
                            self.title,
                            wx.DefaultPosition, 
                            (self.minimumSize.width, self.minimumSize.height),
                            self.choices, self.itemsPerLine, dimension)

class wxStaticText(ShownSynchronizer, wx.StaticText):
    pass

class StaticText(RectangularChild):

    textAlignmentEnum = schema.One(
        textAlignmentEnumType, initialValue = 'Left',
    )
    characterStyle = schema.One(Styles.CharacterStyle)
    title = schema.One(schema.String)

    schema.addClouds(
        copying = schema.Cloud(byRef=[characterStyle])
    )

    def instantiateWidget (self):
        if self.textAlignmentEnum == "Left":
            style = wx.ALIGN_LEFT
        elif self.textAlignmentEnum == "Center":
            style = wx.ALIGN_CENTRE
        elif self.textAlignmentEnum == "Right":
            style = wx.ALIGN_RIGHT
            
        if Block.showBorders:
            style |= wx.SIMPLE_BORDER

        staticText = wxStaticText (self.parentBlock.widget,
                                   -1,
                                   self.title,
                                   wx.DefaultPosition,
                                   (self.minimumSize.width, self.minimumSize.height),
                                   style)
        staticText.SetFont(Styles.getFont(getattr(self, "characterStyle", None)))
        return staticText

    
class wxStatusBar (ShownSynchronizer, wx.StatusBar):
    def __init__(self, *arguments, **keyWords):
        super (wxStatusBar, self).__init__ (*arguments, **keyWords)
        self.gauge = wx.Gauge(self, -1, 100, size=(125, 30), style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.gauge.Show(False)

    def Destroy(self):
        self.blockItem.getFrame().SetStatusBar(None)
        super (wxStatusBar, self).Destroy()
        
    def wxSynchronizeWidget(self):
        super (wxStatusBar, self).wxSynchronizeWidget()
        self.blockItem.getFrame().Layout()


class StatusBar(Block):
    def instantiateWidget (self):
        frame = self.getFrame()
        widget = wxStatusBar (frame, Block.getWidgetID(self))
        frame.SetStatusBar (widget)
        return widget

    def setStatusMessage(self, statusMessage, progressPercentage=-1):
        """
          Allows you to set the message contained in the status bar.  You can also specify 
        values for the progress bar contained on the right side of the status bar.  If you
        specify a progressPercentage (as a float 0 to 1) the progress bar will appear.  If 
        no percentage is specified the progress bar will disappear.
        """
        if progressPercentage == -1:
            if self.widget.GetFieldsCount() != 1:
                self.widget.SetFieldsCount(1)
            self.widget.SetStatusText(statusMessage)
            self.widget.gauge.Show(False)
        else:
            if self.widget.GetFieldsCount() != 2:
                self.widget.SetFieldsCount(2)
                self.widget.SetStatusWidths([-1, 150])
            if statusMessage is not None:
                self.widget.SetStatusText(statusMessage)
            self.widget.gauge.Show(True)
            self.widget.gauge.SetValue((int)(progressPercentage*100))
            # By default widgets are added to the left side...we must reposition them
            rect = self.widget.GetFieldRect(1)
            self.widget.gauge.SetPosition((rect.x+2, rect.y+2))
                            
"""
  To use the TreeAndList you must provide a delegate to perform access
to the data that is displayed. 
  You might be able to subclass ListDelegate and implement the following methods:

class TreeAndListDelegate (ListDelegate):

    def GetElementParent(self, element):

    def GetElementChildren(self, element):

    def GetElementValues(self, element):

    def ElementHasChildren(self, element):
        
    Optionally override GetColumnCount and GetColumnHeading
"""


class wxTreeAndList(DragAndDrop.DraggableWidget, DragAndDrop.ItemClipboardHandler):
    def __init__(self, *arguments, **keywords):
        super (wxTreeAndList, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpanding, id=self.GetId())
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnCollapsing, id=self.GetId())
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColumnDrag, id=self.GetId())
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnWXSelectItem, id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnItemDrag)

    def OnInit (self):
        mixinAClass (self, self.blockItem.elementDelegate)
        
    def OnSize(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            if isinstance (self, wx.gizmos.TreeListCtrl):
                size = self.GetClientSize()
                widthMinusLastColumn = 0
                assert self.GetColumnCount() > 0, "We're assuming that there is at least one column"
                for column in xrange (self.GetColumnCount() - 1):
                    widthMinusLastColumn += self.GetColumnWidth (column)
                lastColumnWidth = size.width - widthMinusLastColumn
                if lastColumnWidth > 0:
                    self.SetColumnWidth (self.GetColumnCount() - 1, lastColumnWidth)
            else:
                assert isinstance (self, wx.TreeCtrl), "We're assuming the only other choice is a wx.Tree"
        event.Skip()

    def OnExpanding(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            self.LoadChildren(event.GetItem())

    def LoadChildren(self, parentId):
        """
          Load the items in the tree only when they are visible.
        """
        child, cookie = self.GetFirstChild (parentId)
        if not child.IsOk():

            parentUUID = self.GetItemData(parentId).GetData()
            for child in self.GetElementChildren (wx.GetApp().UIRepositoryView [parentUUID]):
                cellValues = self.GetElementValues (child)
                childNodeId = self.AppendItem (parentId,
                                               cellValues.pop(0),
                                               -1,
                                               -1,
                                               wx.TreeItemData (child.itsUUID))
                index = 1
                for value in cellValues:
                    self.SetItemText (childNodeId, value, index)
                    index += 1
                self.SetItemHasChildren (childNodeId, self.ElementHasChildren (child))
 
            self.blockItem.openedContainers [parentUUID] = True

    def OnCollapsing(self, event):
        id = event.GetItem()
        """
          if the data passed in has a UUID we'll keep track of the
        state of the opened tree
        """
        del self.blockItem.openedContainers [self.GetItemData(id).GetData()]
        self.DeleteChildren (id)

    def OnColumnDrag(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
            columnIndex = event.GetColumn()
            try:
                self.blockItem.columnWidths [columnIndex] = self.GetColumnWidth (columnIndex)
            except AttributeError:
                pass

    def OnWXSelectItem(self, event):
        if not wx.GetApp().ignoreSynchronizeWidget:
    
            itemUUID = self.GetItemData(self.GetSelection()).GetData()
            selection = self.blockItem.find (itemUUID)
            if self.blockItem.selection != selection:
                self.blockItem.selection = selection
        
                self.blockItem.postEventByName("SelectItemBroadcast", {'item':selection})
        event.Skip()
        
    def SelectedItems(self):
        """
        Return the list of selected items.
        """
        try:
            idList = self.GetSelections() # multi-select API supported?
        except:
            idList = [self.GetSelection(), ] # use single-select API
        # convert from ids, which are UUIDs, to items.
        itemList = []
        for id in idList:
            itemUUID = self.GetItemData(id).GetData()
            itemList.append(self.blockItem.findUUID(itemUUID))
        return itemList

    def OnItemDrag(self, event):
        self.DoDragAndDrop()
        
    def wxSynchronizeWidget(self):
        def ExpandContainer (self, openedContainers, id):
            try:
                expand = openedContainers [self.GetItemData(id).GetData()]
            except KeyError:
                pass
            else:
                self.LoadChildren(id)

                self.Expand(id)

                child, cookie = self.GetFirstChild (id)
                while child.IsOk():
                    ExpandContainer (self, openedContainers, child)
                    child = self.GetNextSibling (child)

        try:
            self.blockItem.columnWidths
        except AttributeError:
            pass # A wx.TreeCtrl won't use columnWidths
        else:
            for index in xrange(wx.gizmos.TreeListCtrl.GetColumnCount(self)):
                self.RemoveColumn (0)
    
            for index in xrange (self.GetColumnCount()):
                info = wx.gizmos.TreeListColumnInfo()
                info.SetText (self.GetColumnHeading (index, None))
                info.SetWidth (self.blockItem.columnWidths [index])
                self.AddColumnInfo (info)

        self.DeleteAllItems()

        root = self.blockItem.rootPath
        if not root:
            root = self.GetElementChildren (None)
        cellValues = self.GetElementValues (root)
        rootNodeId = self.AddRoot (cellValues.pop(0),
                                   -1,
                                   -1,
                                   wx.TreeItemData (root.itsUUID))        
        index = 1
        for value in cellValues:
            self.SetItemText (rootNodeId, value, index)
            index += 1
        self.SetItemHasChildren (rootNodeId, self.ElementHasChildren (root))
        self.LoadChildren (rootNodeId)
        ExpandContainer (self, self.blockItem.openedContainers, rootNodeId)

        selection = self.blockItem.selection
        if not selection:
            selection = root
        self.GoToItem (selection)
        
    def GoToItem(self, item):
        def ExpandTreeToItem (self, item):
            parent = self.GetElementParent (item)
            if parent:
                id = ExpandTreeToItem (self, parent)
                self.LoadChildren(id)
                if self.IsVisible(id):
                    self.Expand (id)
                itemUUID = item.itsUUID
                child, cookie = self.GetFirstChild (id)
                while child.IsOk():
                    if self.GetItemData(child).GetData() == itemUUID:
                        return child
                    child = self.GetNextSibling (child)
                assert False, "Didn't find the item in the tree"
                return None
            else:
                return self.GetRootItem()

        id = ExpandTreeToItem (self, item)
        self.SelectItem (id)
        self.ScrollTo (id)

    @classmethod
    def CalculateWXStyle(theClass, block):
        style = wx.TR_DEFAULT_STYLE|wx.NO_BORDER
        if block.hideRoot:
            style |= wx.TR_HIDE_ROOT
        if block.noLines:
            style |= wx.TR_NO_LINES
        if block.useButtons:
            style |= wx.TR_HAS_BUTTONS
        else:
            style |= wx.TR_NO_BUTTONS
        return style
        
 
class wxTree(wxTreeAndList, wx.TreeCtrl):
    pass
    

class wxTreeList(wxTreeAndList, wx.gizmos.TreeListCtrl):
    pass


class Tree(RectangularChild):

    columnHeadings = schema.Sequence(schema.String, required = True)
    columnData = schema.Sequence(schema.String)
    columnWidths = schema.Sequence(schema.Integer, required = True)
    elementDelegate = schema.One(schema.String, initialValue = '')
    selection = schema.One(schema.Item, initialValue = None)
    hideRoot = schema.One(schema.Boolean, initialValue = True)
    noLines = schema.One(schema.Boolean, initialValue = True)
    useButtons = schema.One(schema.Boolean, initialValue = True)
    openedContainers = schema.Mapping(schema.Boolean, initialValue = {})
    rootPath = schema.One(schema.Item, initialValue = None)

    schema.addClouds(
        copying = schema.Cloud(byRef=[selection])
    )

    def instantiateWidget(self):
        try:
            self.columnWidths
        except AttributeError:
            tree = wxTree (self.parentBlock.widget, Block.getWidgetID(self), 
                           style=wxTreeAndList.CalculateWXStyle(self))
        else:
            tree = wxTreeList (self.parentBlock.widget, Block.getWidgetID(self), 
                               style=wxTreeAndList.CalculateWXStyle(self))
        return tree

    def onSelectItemEvent (self, event):
        self.widget.GoToItem (event.arguments['item'])
                            

class wxItemDetail(wx.html.HtmlWindow):
    def OnLinkClicked(self, wx_linkinfo):
        """
          Clicking on an item changes the selection (post event).
          Clicking on a URL loads the page in a separate browser.
        """
        itemURL = wx_linkinfo.GetHref()
        item = self.blockItem.findPath(itemURL)
        if not item:
            webbrowser.open(itemURL)
        else:
            self.blockItem.postEventByName("SelectItemBroadcast", {'item':item})

    def wxSynchronizeWidget(self):
        if self.blockItem.selection is not None:
            self.SetPage (self.blockItem.getHTMLText (self.blockItem.selection))
        else:
            self.SetPage('<html><body></body></html>')


class ItemDetail(RectangularChild):

    selection = schema.One(schema.Item, initialValue = None)
    schema.addClouds(
        copying = schema.Cloud(byRef=[selection])
    )

    def __init__(self, *arguments, **keywords):
        super (ItemDetail, self).__init__ (*arguments, **keywords)
        self.selection = None

    def instantiateWidget (self):
        return wxItemDetail (self.parentBlock.widget,
                             Block.getWidgetID(self),
                             wx.DefaultPosition,
                             (self.minimumSize.width,
                              self.minimumSize.height))

    def getHTMLText(self, item):
        return '<body><html><h1>%s</h1></body></html>' % item.getDisplayName()

    def onSelectItemEvent (self, event):
        """
          Display the item in the wxWidget.
        """
        self.selection = event.arguments['item']
        self.synchronizeWidget ()

    
class ContentItemDetail(BoxContainer):
    """
    ContentItemDetail
    Any container block in the Content Item's Detail View hierarchy.
    Not to be confused with ItemDetail (above) which uses an HTML-based widget.
    Keeps track of the current selected item
    Supports Color Style
    """
    colorStyle = schema.One(Styles.ColorStyle)
    selectedItemsAttribute = schema.One(
        schema.String,
        doc = 'Specifies which attribute of the selected Item should be '
              'associated with this block.',
        initialValue = '',
    )
    
class wxPyTimer(wx.PyTimer):
    """ 
    A wx.PyTimer that has an IsShown() method, like all the other widgets
    that blocks deal with; it also generates its own event from Notify
    """              
    def IsShown(self):
        return True
    
    def Notify(self):
        event = wx.PyEvent()
        event.SetEventType(wx.wxEVT_TIMER)
        event.SetId(Block.getWidgetID(self.blockItem))
        wx.GetApp().OnCommand(event)

    def Destroy(self):
       Block.wxOnDestroyWidget (self)

class Timer(Block):
    """
    A Timer block. Fires (sending a BlockEvent) at a particular time.
    A passed time will fire "shortly".
    """

    event = schema.One(
        BlockEvent,
        doc = "The event we'll send when we go off",
    )

    schema.addClouds(
        copying = schema.Cloud(byCloud=[event])
    )

    def instantiateWidget (self):
        timer = wxPyTimer(self.parentBlock.widget)
        return timer

    def setFiringTime(self, when):
        # First turn off the old timer
        timer = self.widget
        timer.Stop()

        # Set the new time, if we have one. If it's in the past, fire "really soon". If it's way in the future,
        # don't bother firing.
        if when is not None:
            td = when - datetime.now()
            millisecondsUntilFiring = ((td.days * 86400) + td.seconds) * 1000L
            if millisecondsUntilFiring < 100:
                millisecondsUntilFiring = 100
            elif millisecondsUntilFiring > sys.maxint:
                millisecondsUntilFiring = sys.maxint

            # print "*** setFiringTime: will fire at %s in %s minutes" % (when, millisecondsUntilFiring / 60000)
            timer.Start(millisecondsUntilFiring, True)
        else:
            # print "*** setFiringTime: No new time."
            pass

class ReminderTimer(Timer):
    def synchronizeWidget (self):
        # logger.debug("*** Synchronizing ReminderTimer widget!")
        super(ReminderTimer, self).synchronizeWidget()
        if not wx.GetApp().ignoreSynchronizeWidget:            
            pending = self.getPendingReminders()
            if len(pending) > 0:
                self.setFiringTime(pending[0].reminderTime)
    
    def getPendingReminders (self):
        # @@@BJS Eventually, the query should be able to do the sorting for us;
        # for now, that doesn't seem to work so we're doing it here.
        # ... this routine should just be "return self.contents.resultSet"
        timesAndReminders = []
        for item in self.contents:
            try:
                reminderTime = item.reminderTime
            except AttributeError:
                pass
            else:
                timesAndReminders.append((reminderTime, item))
            
        if len(timesAndReminders) != 0:
            timesAndReminders.sort()
            timesAndReminders = [ item[1] for item in timesAndReminders ]
        return timesAndReminders
    
    def onCollectionChanged(self, event):
        # logger.debug("*** Got reminders collection changed!")
        pending = self.getPendingReminders()
        closeIt = False
        reminderDialog = self.getReminderDialog(False)
        if reminderDialog is not None:
            (nextReminderTime, closeIt) = reminderDialog.UpdateList(pending)
        elif len(pending) > 0:
            nextReminderTime = pending[0].reminderTime
        else:
            nextReminderTime = None
        if closeIt:
            self.closeReminderDialog();
        self.setFiringTime(nextReminderTime)
    
    def onReminderTimeEvent(self, event):
        # Run the reminders dialog and re-queue our timer if necessary
        # logger.debug("*** Got reminders time event!")
        pending = self.getPendingReminders()
        reminderDialog = self.getReminderDialog(True)
        assert reminderDialog is not None
        (nextReminderTime, closeIt) = reminderDialog.UpdateList(pending)
        if closeIt:
            # logger.debug("*** closing the dialog!")
            self.closeReminderDialog()
        self.setFiringTime(nextReminderTime)

    def getReminderDialog(self, createIt):
        try:
            reminderDialog = self.widget.reminderDialog
        except AttributeError:
            if createIt:
                reminderDialog = ReminderDialog.ReminderDialog(wx.GetApp().mainFrame, -1)
                self.widget.reminderDialog = reminderDialog
            else:
                reminderDialog = None
        return reminderDialog

    def closeReminderDialog(self):
        try:
            reminderDialog = self.widget.reminderDialog
        except AttributeError:
            pass
        else:
            del self.widget.reminderDialog
            reminderDialog.Destroy()

    def setFiringTime(self, when):
        # logger.debug("*** next reminder due %s" % when)
        super(ReminderTimer, self).setFiringTime(when)

class PresentationStyle(schema.Item):
    schema.kindInfo(
        displayName = "Presentation Style"
    )
    sampleText = schema.One(
        schema.String,
        doc = 'Localized in-place sample text (optional); if "", will use the attr\'s displayName.',
    )
    format = schema.One(
        schema.String,
        doc = 'customization of presentation format',
    )
    choices = schema.Sequence(
        schema.String,
        doc = 'options for multiple-choice values',
    )
    editInPlace = schema.One(
        schema.Boolean,
        doc = 'For text controls, True if we should wait for a click to become editable',
    )
    lineStyleEnum = schema.One(
        lineStyleEnumType,
        doc = 'SingleLine vs MultiLine for textbox-based editors',
    )
    schema.addClouds(
        copying = schema.Cloud(
            byValue=[sampleText,format,choices,editInPlace,lineStyleEnum]
        )
    )

class AEBlock(BoxContainer):
    """
    Attribute Editor Block: instantiates an Attribute Editor appropriate for
    the value of the specified attribute; the Attribute Editor then creates
    the widget. Issues:
    - Finalization.  We're relying on EVT_KILL_FOCUS to know when to end 
      editing.  We know the Detail View doesn't always operate in ways that 
      cause this to be reliable, but I think these problems can be fixed there.
    """
    schema.kindInfo(
        displayName="Attribute Editor Block Kind",
        description="Block that instantiates an appropriate Attribute Editor."
    )

    characterStyle = schema.One(Styles.CharacterStyle)
    readOnly = schema.One(schema.Boolean, initialValue = False)
    presentationStyle = schema.One(PresentationStyle)
    event = schema.One(BlockEvent)

    schema.addClouds(
        copying = schema.Cloud(byRef=[characterStyle, presentationStyle])
    )
    
    def getItem(self): return getattr(self, 'contents', None)
    def setItem(self, value): self.contents = value
    item = property(getItem, setItem, 
                    doc="Safely access the selected item (or None)")
    
    def getAttributeName(self): return getattr(self, 'viewAttribute', None)
    def setAttributeName(self, value): self.viewAttribute = value
    attributeName = property(getAttributeName, setAttributeName, doc=\
                             "Safely access the configured attribute name (or None)")
    
    def instantiateWidget(self):
        """
        Ask our attribute editor to create a widget for us.
        """
        existingWidget = getattr(self, 'widget', None) 
        if existingWidget is not None:
            return existingWidget
        
        forEditing = getattr(self, 'forEditing', False)

        # Tell the control what font we expect it to use
        try:
            charStyle = self.characterStyle
        except AttributeError:
            charStyle = None
        font = Styles.getFont(charStyle)

        editor = self.lookupEditor()
        widget = editor.CreateControl(forEditing, self.parentBlock.widget, 
                                      Block.getWidgetID(self), self, font)
        widget.SetFont(font)
        # logger.debug("Instantiated a %s, forEditing = %s" % (widget, forEditing))
        
        # Cache a little information in the widget.
        widget.editor = editor
        
        widget.Bind(wx.EVT_SET_FOCUS, self.onGainFocusFromWidget)
        widget.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocusFromWidget)
        widget.Bind(wx.EVT_KEY_UP, self.onKeyUpFromWidget)
        widget.Bind(wx.EVT_LEFT_DOWN, self.onClickFromWidget)
                    
        return widget
        
    def synchronizeWidget (self):
        """
        Override to call the editor to do the synchronization
        """
        if not wx.GetApp().ignoreSynchronizeWidget:
            oldIgnoreSynchronizeWidget = wx.GetApp().ignoreSynchronizeWidget
            wx.GetApp().ignoreSynchronizeWidget = True
            try:
                editor = self.lookupEditor()
                editor.BeginControlEdit(editor.item, editor.attributeName, self.widget)
            finally:
                wx.GetApp().ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

    def ChangeWidgetIfNecessary(self, forEditing, grabFocus):
        """
        Make sure we've got the right widget, given
        the item+attribute we're configured for, our
        presentationstyle, and the state we're in (editing or not).
        """
        def rerender():
            # Find the widget that corresponds to the view we're in
            existingWidget = getattr(self, 'widget', None)
            evtBoundaryWidget = existingWidget
            while evtBoundaryWidget is not None:
                if evtBoundaryWidget.blockItem.eventBoundary:
                    break
                evtBoundaryWidget = evtBoundaryWidget.GetParent()
            assert evtBoundaryWidget
                
            # Tell it not to update
            evtBoundaryWidget.Freeze()
            try:
                # Destroy the old widget
                if existingWidget is not None:
                    self.saveValue()
                    self.unRender()
                
                # Set up the new widget
                self.render()
                
                # Grab focus if we're supposed to.
                if self.forEditing and grabFocus:
                    logger.debug("AEBlock.ChangeWidgetIfNecessary: '%s': Grabbing focus." % \
                                 self.attributeName)
                    self.widget.SetFocus()

                # Sync the view to update the sizers
                if evtBoundaryWidget:
                    evtBoundaryWidget.blockItem.synchronizeWidget()
            finally:
                if evtBoundaryWidget:
                    evtBoundaryWidget.Thaw()
                
        editor = self.lookupEditor()
        existingWidget = getattr(self, 'widget', None)
        changing = editor.MustChangeControl(forEditing, existingWidget)
        if changing:
            self.forEditing = forEditing
            logger.debug("AEBlock.ChangeWidgetIfNecessary: '%s': Must change." % \
                         self.attributeName)
            wx.CallAfter(rerender)
        else:
            logger.debug("AEBlock.ChangeWidgetIfNecessary: '%s': Not changing." % \
                         self.attributeName)

        return changing
        
    def lookupEditor(self):
        """
        Make sure we've got the right attribute editor for this type
        """
        # Get the parameters we'll use to pick an editor
        typeName = self.getItemAttributeTypeName()
        try:
            presentationStyle = self.presentationStyle
        except AttributeError:
            presentationStyle = None

        # If we have one already, and it's the right one, return it.
        try:
            oldEditor = self.widget.editor
        except AttributeError:
            pass
        else:
            if (oldEditor is not None) and (oldEditor.typeName == typeName) \
               and (oldEditor.attributeName == self.attributeName) and \
               (oldEditor.presentationStyle is presentationStyle):
                assert oldEditor.item is self.item # this shouldn't've changed.
                return oldEditor

        # We need a new editor - create one.
        # logger.debug("Creating new AE for %s (%s.%s)", typeName, item, attributeName)
        selectedEditor = AttributeEditors.getInstance\
                       (typeName, self.item, self.attributeName, presentationStyle)
        
        # Note the characteristics that made us pick this editor
        selectedEditor.typeName = typeName
        selectedEditor.attributeName = self.attributeName
        try:
            selectedEditor.presentationStyle = self.presentationStyle
        except AttributeError:
            selectedEditor.presentationStyle = None
        selectedEditor.item = self.item

        # Register for value changes
        selectedEditor.SetChangeCallback(self.onAttributeEditorValueChange)
        return selectedEditor

    def onSetContentsEvent (self, event):
        self.item = event.arguments['item']
        assert not hasattr(self, 'widget')
            
    def getItemAttributeTypeName(self):
        # Get the type of the current attribute
        if self.item is None:
            return None

        # Ask the schema for the attribute's type first
        try:
            theType = self.item.getAttributeAspect(self.attributeName, "type")
        except:
            # If the repository doesn't know about it (it might be a property),
            # get its value and use its type
            try:
                attrValue = getattr(self.item, self.attributeName)
            except:
                typeName = "_default"
            else:
                typeName = type(attrValue).__name__
        else:
            if theType is None:
                typeName = "NoneType"
            else:
                typeName = theType.itsName
        
        return typeName

    def onClickFromWidget(self, event):
        """
          The widget got clicked on - make sure we're in edit mode.
        """
        logger.debug("AEBlock: %s widget got clicked on", self.attributeName)
        changing = self.ChangeWidgetIfNecessary(True, True)

        # If the widget didn't get focus as a result of the click,
        # grab focus now.
        # @@@ This was an attempt to fix bug 2878 on Mac, which doesn't focus
        # on popups when you click on them (or tab to them!)
        if not changing:
            oldFocus = wx.Window.FindFocus()
            if oldFocus is not self.widget:
                # Find our view - if it has a finishSelectionChanges method, call it.
                b = self
                while b is not None and not b.eventBoundary:
                    b = b.parentBlock
                if b is not None:
                    try:
                        method = b.finishSelectionChanges
                    except AttributeError:
                        pass
                    else:
                        method()
            
                logger.debug("Grabbing focus.")
                wx.Window.SetFocus(self.widget)

        event.Skip()

    def onGainFocusFromWidget(self, event):
        """
          The widget got the focus - make sure we're in edit mode.
        """
        logger.debug("AEBlock: %s widget gained focus", self.attributeName)
        
        self.ChangeWidgetIfNecessary(True, True)
        event.Skip()

    def onLoseFocusFromWidget(self, event):
        """
          The widget lost focus - we're finishing editing.
        """
        logger.debug("AEBlock: %s, widget losing focus" % self.blockName)
        
        if event is not None:
            event.Skip()
        
        # Workaround for wx Mac crash bug, 2857: ignore the event if we're being deleted
        widget = getattr(self, 'widget', None)
        if widget is None or widget.IsBeingDeleted() or widget.GetParent().IsBeingDeleted():
            logger.debug("AEBlock: skipping onLoseFocus because the widget is being deleted.")
            return

        # Make sure the value is written back to the item. 
        self.saveValue()

        self.ChangeWidgetIfNecessary(False, False)

    def saveValue(self):
        # Make sure the value is written back to the item. 
        widget = getattr(self, 'widget', None)
        if widget is not None:
            editor = self.lookupEditor()
            editor.EndControlEdit(self.item, self.attributeName, widget)

    def unRender(self):
        # Last-chance write-back.
        if getattr(self, 'forEditing', False):
            self.saveValue()
        super(AEBlock, self).unRender()
            
    def onKeyUpFromWidget(self, event):
        if event.m_keyCode == wx.WXK_RETURN:
            if not self.ChangeWidgetIfNecessary(False, True):
                self.saveValue()
            
            # Do the tab thing if we're not a multiline thing
            # @@@ Actually, don't; it doesn't mix well when one of the fields you'd
            # "enter" through is multiline - it clears the content.
            if False:
                try:
                    isMultiLine = self.presentationStyle.lineStyleEnum == "MultiLine"
                except AttributeError:
                    isMultiLine = False
                if not isMultiLine:
                    self.widget.Navigate()
        event.Skip()

    def onAttributeEditorValueChange(self):
        """ Called when the attribute editor changes the value """
        logger.debug("onAttributeEditorValueChange: %s %s", 
                     self.item, self.attributeName)
        try:
            event = self.event
        except AttributeError:
            pass
        else:
            self.post(event, {'item': self.item, 
                              'attribute': self.attributeName })
