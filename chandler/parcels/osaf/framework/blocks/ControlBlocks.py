__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import application.Globals as Globals
from application.Application import mixinAClass
from Block import *
from ContainerBlocks import *
from DragAndDrop import DraggableWidget as DraggableWidget
from Styles import Font
import wx
import wx.html
import wx.gizmos
import wx.grid
import webbrowser # for opening external links
import mx.DateTime as DateTime
from osaf.framework.attributeEditors.AttributeEditors import AttributeEditor

class Button(RectangularChild):
    def instantiateWidget(self):
        try:
            id = Block.getWidgetID(self)
        except AttributeError:
            id = 0

        parentWidget = self.parentBlock.widget
        if self.buttonKind == "Text":
            button = wx.Button (parentWidget,
                                id,
                                self.title,
                                wx.DefaultPosition,
                                (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Image":
            image = wx.Image(self.icon, 
                             wx.BITMAP_TYPE_PNG)
            bitmap = image.ConvertToBitmap()
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
            self.Post(event, {'item':self})

                              
class Choice(RectangularChild):
    def instantiateWidget(self):
        return wx.Choice (self.parentBlock.widget,
                          -1, 
                          wx.DefaultPosition,
                          (self.minimumSize.width, self.minimumSize.height),
                          self.choices)


class ComboBox(RectangularChild):
    def instantiateWidget(self):
        return wx.ComboBox (self.parentBlock.widget,
                            -1,
                            self.selection, 
                            wx.DefaultPosition,
                            (self.minimumSize.width, self.minimumSize.height),
                            self.choices)


class wxEditText(wx.TextCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxEditText, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterPressed, id=self.GetId())
        minW, minH = arguments[-1] # assumes minimum size passed as last arg
        self.SetSizeHints(minW=minW, minH=minH)

    def wxSynchronizeWidget(self):
        if self.blockItem.isShown != self.IsShown():
            self.Show (self.blockItem.isShown)

    def OnEnterPressed(self, event):
        self.blockItem.Post (Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/EnterPressed'),
                             {'text':self.GetValue()})


class EditText(RectangularChild):
    def instantiateWidget(self):
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

        editText.SetFont(Font (self.characterStyle))
        return editText
    
    """
    Edit Menu enabling and handling
    """
    def onUndoEventUpdateUI (self, notification):
        canUndo = self.widget.CanUndo()
        notification.data ['Enable'] = canUndo
        if canUndo:
            notification.data ['Text'] = 'Undo Command\tCtrl+Z'
        else:
            notification.data ['Text'] = "Can't Undo\tCtrl+Z"            

    def onUndoEvent (self, notification):
        self.widget.Undo()
        self.OnDataChanged()

    def onRedoEventUpdateUI (self, notification):
        notification.data ['Enable'] = self.widget.CanRedo()

    def onRedoEvent (self, notification):
        self.widget.Redo()
        self.OnDataChanged()

    def onCutEventUpdateUI (self, notification):
        notification.data ['Enable'] = self.widget.CanCut()

    def onCutEvent (self, notification):
        self.widget.Cut()
        self.OnDataChanged()

    def onCopyEventUpdateUI (self, notification):
        notification.data ['Enable'] = self.widget.CanCopy()

    def onCopyEvent (self, notification):
        self.widget.Copy()

    def onPasteEventUpdateUI (self, notification):
        notification.data ['Enable'] = self.widget.CanPaste()

    def onPasteEvent (self, notification):
        self.widget.Paste()
        self.OnDataChanged()
    
    def OnDataChanged (self):
        # override in subclass for notification when edit operations have taken place
        pass

class wxHTML(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())


class HTML(RectangularChild):
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
    to customize your behavior.
    """
    def GetColumnCount (self):
        return len (self.blockItem.columnHeadings)

    def GetElementCount (self):
        return len (self.blockItem.contents)

    def GetElementType (self, row, column):
        return "String"

    def GetColumnHeading (self, column, item):
        return self.blockItem.columnHeadings [column]


class AttributeDelegate (ListDelegate):
    def GetColumnCount (self):
        return len (self.blockItem.columnAttributeNames)

    def GetElementType (self, row, column):
        try:
            item = self.blockItem.contents[row]
        except IndexError:
            type = "_default"
        else:
            attributeName = self.blockItem.columnAttributeNames [column]
            type = item.getAttributeAspect (attributeName, 'type').itsName
        return type

    def GetElementValue (self, row, column):
        return self.blockItem.contents [row], self.blockItem.columnAttributeNames [column]

    def SetElementValue (self, row, column, value):
        item = self.blockItem.contents[row]
        attributeName = self.blockItem.columnAttributeNames [column]
        item.setAttributeValue (attributeName, value)

    def GetColumnHeading (self, column, item):
        if item:
            attributeName = self.blockItem.columnAttributeNames [column]
            attribute = item.itsKind.getAttribute (attributeName)
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

class wxList (DraggableWidget, wx.ListCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxList, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnWXSelectionChanged, id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnItemDrag)

    def OnInit (self):
        elementDelegate = self.blockItem.elementDelegate
        if not elementDelegate:
            elementDelegate = 'osaf.framework.blocks.ControlBlocks.AttributeDelegate'
        mixinAClass (self, elementDelegate)
        
    def OnSize(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            size = self.GetClientSize()
            widthMinusLastColumn = 0
            assert self.GetColumnCount() > 0, "We're assuming that there is at least one column"
            for column in xrange (self.GetColumnCount() - 1):
                widthMinusLastColumn += self.GetColumnWidth (column)
            lastColumnWidth = size.width - widthMinusLastColumn
            if lastColumnWidth > 0:
                self.SetColumnWidth (self.GetColumnCount() - 1, lastColumnWidth)
        event.Skip()

    def OnWXSelectionChanged(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            item = self.blockItem.contents [event.GetIndex()]
            if self.blockItem.selection != item:
                self.blockItem.selection = item
            self.blockItem.Post (Globals.repository.findPath ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                                                              {'item':item})
        event.Skip()

    def OnItemDrag(self, event):
        self.SetDragData (self.blockItem.contents[event.GetIndex()].itsUUID)
                            
    def wxSynchronizeWidget(self):
        self.blockItem.contents.resultsStale = True
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

    def GoToItem(self, item):
        self.Select (self.blockItem.contents.index (item))


class List(RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (List, self).__init__ (*arguments, **keywords)
        self.selection = None

    def instantiateWidget (self):
        return wxList (self.parentBlock.widget,
                       Block.getWidgetID(self),
                       style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.SUNKEN_BORDER|wx.LC_EDIT_LABELS)

    def onSelectionChangedEvent (self, notification):
        """
          Display the item in the widget.
        """
        self.selection = notification.data['item']
        self.widget.GoToItem (self.selection)


class wxTableData(wx.grid.PyGridTableBase):
    def __init__(self, *arguments, **keywords):
        super (wxTableData, self).__init__ (*arguments, **keywords)
        self.defaultAttribute = wx.grid.GridCellAttr()
        self.defaultAttribute.SetReadOnly (True)

    def __del__ (self):
        self.defaultAttribute.DecRef()
        
    def GetNumberRows (self):
        """
          We've got the usual chicken & egg problems: wxWidgets calls GetNumberRows &
        GetNumberCols before wiring up the view instance variable
        """
        if self.GetView():
            return self.GetView().GetElementCount()
        return 1

    def GetNumberCols (self):
        if self.GetView():
            return self.GetView().GetColumnCount()
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
        if not attribute and self.GetTypeName (row, column) == "_default":
            attribute = self.defaultAttribute
            attribute.IncRef()
        return attribute
        

class wxTable(DropReceiveWidget, wx.grid.Grid):
    def __init__(self, *arguments, **keywords):
        """
          Giant hack. Calling event.GetEventObject in OnShow of application, while the
        object is being created cause the object to get the wrong type because of a
        "feature" of SWIG. So we need to avoid OnShows in this case.
        """
        oldIgnoreSynchronizeWidget = Globals.wxApplication.ignoreSynchronizeWidget
        Globals.wxApplication.ignoreSynchronizeWidget = True
        try:
            super (wxTable, self).__init__ (*arguments, **keywords)
        finally:
            Globals.wxApplication.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

        self.SetRowLabelSize(0)
        self.AutoSizeRows()
        self.EnableGridLines(False)
        self.SetMargins(0-wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X),
                        0-wx.SystemSettings_GetMetric(wx.SYS_HSCROLL_Y))
        """
          Don't draw cursor outline on selected cells
        """
        self.SetCellHighlightPenWidth (0)
        self.SetCellHighlightROPenWidth (0)

        defaultName = "_default"
        self.SetDefaultRenderer (GridCellAttributeRenderer (defaultName))
        map = Globals.repository.findPath('//parcels/osaf/framework/attributeEditors/AttributeEditors')
        for key in map.editorString.keys():
            if key != defaultName:
                self.RegisterDataType (key,
                                       GridCellAttributeRenderer (key),
                                       GridCellAttributeEditor (key))

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColumnDrag)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnWXSelectionChanged)

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

        self.SetTable (gridTable, True, selmode=wx.grid.Grid.SelectRows)

        
    def OnSize(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            size = event.GetSize()
            widthMinusLastColumn = 0

            assert self.GetNumberCols() > 0, "We're assuming that there is at least one column"
            lastColumnIndex = self.GetNumberCols() - 1
            for column in xrange (lastColumnIndex):
                widthMinusLastColumn += self.GetColSize (column)
            lastColumnWidth = size.width - widthMinusLastColumn
            if lastColumnWidth > 0:
                self.SetColSize (lastColumnIndex, lastColumnWidth)
                self.ForceRefresh()
        event.Skip()

    def OnColumnDrag(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            columnIndex = event.GetRowOrCol()
            self.blockItem.columnWidths [columnIndex] = self.GetColSize (columnIndex)

    def AddItem(self, itemUUID):
        item = Globals.repository.findUUID(itemUUID)
        self.blockItem.contents.add(item)

    def OnWXSelectionChanged(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            item = self.blockItem.contents [event.GetRow()]
            if self.blockItem.selection != item:
                self.blockItem.selection = item

                ## Redraw headers
                gridTable = self.GetTable()
                for columnIndex in xrange (gridTable.GetNumberCols()):
                    self.SetColLabelValue (columnIndex, gridTable.GetColLabelValue (columnIndex))

            self.blockItem.Post (Globals.repository.findPath ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                                                              {'item':item})
            self.blockItem.selectedColumn = self.blockItem.columnAttributeNames [event.GetCol()]
        event.Skip()

    def Reset(self): 
        """
          A Grid can't easily redisplay its contents, so we write the following
        helper function to readjust everything after the contents change
        """
        #Trim/extend the control's rows and update all values
        self.BeginBatch()
        """
          Hack to work around Stuarts bug #1568 -- DJA
        """
        self.blockItem.contents._ItemCollection__refresh()

        if self.blockItem.hideColumnHeadings:
            self.SetColLabelSize (0)
        else:
            """
              Should be using wx.grid.GRID_DEFAULT_COL_LABEL_HEIGHT, but
            it hasn't been wrapped yet -- DJA
            """
            self.SetColLabelSize (32)

        gridTable = self.GetTable()
        newRows = gridTable.GetNumberRows()
        newColumns = gridTable.GetNumberCols()
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
        for columnIndex in xrange (newColumns):
            self.SetColSize (columnIndex, self.blockItem.columnWidths [columnIndex])

        #Update all displayed values
        message = wx.grid.GridTableMessage (gridTable, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES) 
        self.ProcessTableMessage (message) 
        self.EndBatch() 

        # The scroll bars aren't resized (at least on windows) 
        # Jiggling the size of the window rescales the scrollbars 
        w,h = self.GetSize() 
        self.SetSize ((w+1, h)) 
        self.SetSize ((w, h)) 
        self.ForceRefresh () 

    def wxSynchronizeWidget(self):
        self.blockItem.contents.resultsStale = True
        self.Reset()
        selection = self.blockItem.selection
        self.GoToItem (self.blockItem.selection)

    def GoToItem(self, item):
        if item:
            try:
                row = self.blockItem.contents.index (item)
            except ValueError:
                item = None
        if item:
            cursorColumn = 0
            selectedColumn = self.blockItem.selectedColumn
            for columnIndex in xrange (self.GetTable().GetNumberCols()):
                if self.blockItem.columnAttributeNames [columnIndex] == selectedColumn:
                    cursorColumn = columnIndex
                    break
            self.SelectRow (row)
            self.SetGridCursor (row, cursorColumn)
        else:
            self.ClearSelection()
            self.blockItem.Post (Globals.repository.findPath ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                                 {'item':item})


class GridCellAttributeRenderer (wx.grid.PyGridCellRenderer):
    def __init__(self, type):
        super (GridCellAttributeRenderer, self).__init__ ()
        self.delegate = AttributeEditor.GetAttributeEditor (type)

    def SetTextColorsAndFont (self, grid, attr, dc, isSelected):
        """
          Set the text foreground, text background, brush and font into the dc
        """
        if grid.IsEnabled():
            if isSelected:
                dc.SetTextBackground (grid.GetSelectionBackground())
                dc.SetTextForeground (grid.GetSelectionForeground())
                dc.SetBrush (wx.Brush (grid.GetSelectionBackground(), wx.SOLID))
            else:
                dc.SetTextBackground (attr.GetBackgroundColour())
                dc.SetTextForeground (attr.GetTextColour())
                dc.SetBrush (wx.Brush (attr.GetBackgroundColour(), wx.SOLID))
        else:
            dc.SetTextBackground (wxSystemSettings_GetSystemColour(wxSYS_COLOUR_BTNFACE))
            dc.SetTextForeground (wxSystemSettings_GetSystemColour(wxSYS_COLOUR_GRAYTEXT))
            dc.SetBrush (wx.Brush (wxSystemSettings_GetSystemColour(wxSYS_COLOUR_BTNFACE), wxSOLID))

        dc.SetFont (attr.GetFont())

    def Draw (self, grid, attr, dc, rect, row, column, isSelected):
        """
          Currently only handles left justified multiline text
        """
        self.SetTextColorsAndFont (grid, attr, dc, isSelected)
        item, attributeName = grid.GetElementValue (row, column)
        self.delegate.Draw (dc, rect, item, attributeName, isSelected)


class GridCellAttributeEditor (wx.grid.PyGridCellEditor):
    def __init__(self, type):
        super (GridCellAttributeEditor, self).__init__ ()
        self.delegate = AttributeEditor.GetAttributeEditor (type)

    def Create (self, parent, id, evtHandler):
        """
          Create an edit control to edit the text
        """
        self.control = self.delegate.Create (parent, id)
        self.SetControl (self.control)
        if evtHandler:
            self.control.PushEventHandler (evtHandler)

    def PaintBackground (self, *arguments, **keywords):
        """
          background drawing is done by the edit control
        """
        pass

    def BeginEdit (self, row,  column, grid):
        item, attributeName = grid.GetElementValue (row, column)
        self.initialValue = self.delegate.GetAttributeValue (item, attributeName)
        self.delegate.BeginControlEdit (self.control, self.initialValue)

    def EndEdit (self, row, column, grid):
        value = self.delegate.GetControlValue (self.control)
        if value == self.initialValue:
            changed = False
        else:
            changed = True
            grid.SetElementValue (row, column, value)
        return changed

    def Reset (self):
        self.delegate.SetControlValue (self.control, self.initialValue)

    def GetValue (self):
        return self.delegate.GetControlValue (self.control)


class ImageRenderer (wx.grid.PyGridCellRenderer):
    def Draw (self, grid, attr, dc, rect, row, col, isSelected):
        imageName = grid.GetTable().GetValue (row, col)
        image = Globals.wxApplication.GetImage (imageName)

        if image:
            offscreenBuffer = wx.MemoryDC()
    
            offscreenBuffer.SelectObject (image)
    
            dc.SetBackgroundMode (wx.SOLID)
    
            if isSelected:
                dc.SetBrush (wx.Brush (grid.GetSelectionBackground(), wx.SOLID))
                dc.SetPen (wx.Pen (grid.GetSelectionBackground(), 1, wx.SOLID))
            else:
                dc.SetBrush (wx.Brush (attr.GetBackgroundColour(), wx.SOLID))
                dc.SetPen (wx.Pen (attr.GetBackgroundColour(), 1, wx.SOLID))
     
            dc.DrawRectangleRect(rect)
    
            width, height = image.GetWidth(), image.GetHeight()
    
            if width > rect.width - 2:
                width = rect.width - 2
    
            if height > rect.height - 2:
                height = rect.height - 2
    
            dc.Blit ((rect.x + 1, rect.y + 1),
                     (width, height),
                     offscreenBuffer,
                     (0, 0),
                     wx.COPY,
                     True)

class Table(RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (Table, self).__init__ (*arguments, **keywords)
        self.selection = None

    def instantiateWidget (self):
        return wxTable (self.parentBlock.widget, Block.getWidgetID(self))

    def onSelectionChangedEvent (self, notification):
        """
          Display the item in the widget.
        """
        self.selection = notification.data['item']
        self.widget.GoToItem (self.selection)

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

    def onRequestSelectItemEvent (self, notification):
        # request the Table part of the Active View to change selection
        newSelection = notification.data['item']
        # A request to select None causes everything to be deselected
        # If the 'collection' flag is set, select the collection in
        # the Detail View.
        if newSelection is None:
            # deselect
            self.onSelectionChangedEvent (notification)
            if notification.data['collection'] == True:
                # tell the Detail View to select the whole collection
                self.Post (Globals.repository.findPath \
                           ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                           {'item':self.contents})
        elif newSelection in self.contents:
            # select the item
            self.onSelectionChangedEvent (notification)
            # tell the Detail View about the new selection
            self.Post (Globals.repository.findPath \
                       ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                       {'item':newSelection})


class RadioBox(RectangularChild):
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

class wxStaticText(wx.StaticText):
    def wxSynchronizeWidget(self):
        if self.blockItem.isShown != self.IsShown():
            self.Show (self.blockItem.isShown)

class StaticText(RectangularChild):
    def instantiateWidget (self):
        if self.textAlignmentEnum == "Left":
            style = wx.ALIGN_LEFT
        elif self.textAlignmentEnum == "Center":
            style = wx.ALIGN_CENTRE
        elif self.textAlignmentEnum == "Right":
            style = wx.ALIGN_RIGHT

        staticText = wxStaticText (self.parentBlock.widget,
                                   -1,
                                   self.title,
                                   wx.DefaultPosition,
                                   (self.minimumSize.width, self.minimumSize.height),
                                   style)

        staticText.SetFont(Font (self.characterStyle))
        return staticText

    
class wxStatusBar (wx.StatusBar):
    
    def wxSynchronizeWidget(self):
        if self.blockItem.isShown != self.IsShown():
            self.Show (self.blockItem.isShown)


class StatusBar(Block):
    def instantiateWidget (self):
        frame = Globals.wxApplication.mainFrame
        widget = wxStatusBar (frame, Block.getWidgetID(self))
        frame.SetStatusBar (widget)
        return widget

    def onShowHideEvent(self, notification):
        self.isShown = not self.isShown
        self.synchronizeWidget()
        Globals.wxApplication.mainFrame.Layout()


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


class wxTreeAndList(DraggableWidget):
    def __init__(self, *arguments, **keywords):
        super (wxTreeAndList, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpanding, id=self.GetId())
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnCollapsing, id=self.GetId())
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColumnDrag, id=self.GetId())
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnWXSelectionChanged, id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnItemDrag)

    def OnInit (self):
        mixinAClass (self, self.blockItem.elementDelegate)
        
    def OnSize(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
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
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            self.LoadChildren(event.GetItem())

    def LoadChildren(self, parentId):
        """
          Load the items in the tree only when they are visible.
        """
        child, cookie = self.GetFirstChild (parentId)
        if not child.IsOk():

            parentUUID = self.GetItemData(parentId).GetData()
            for child in self.GetElementChildren (Globals.repository [parentUUID]):
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
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            columnIndex = event.GetColumn()
            try:
                self.blockItem.columnWidths [columnIndex] = self.GetColumnWidth (columnIndex)
            except AttributeError:
                pass

    def OnWXSelectionChanged(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
    
            itemUUID = self.GetItemData(self.GetSelection()).GetData()
            selection = Globals.repository.find (itemUUID)
            if self.blockItem.selection != selection:
                self.blockItem.selection = selection
        
                self.blockItem.Post (Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                                     {'item':selection})
        event.Skip()

    def OnItemDrag(self, event):
        self.SetDragData (self.GetItemData(event.GetItem()).GetData())
        
    def wxSynchronizeWidget(self):
        def ExpandContainer (self, openedContainers, id):
            try:
                expand = openedContainers [self.GetItemData(id).GetData()]
            except KeyError:
                pass
            else:
                self.LoadChildren(id)

                if self.IsVisible (id):
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
            for index in xrange(self.GetColumnCount()):
                self.RemoveColumn (0)
    
            info = wx.gizmos.TreeListColumnInfo()
            for index in xrange (self.GetColumnCount()):
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

    def CalculateWXStyle(self, block):
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
    CalculateWXStyle = classmethod(CalculateWXStyle)
        
 
class wxTree(wxTreeAndList, wx.TreeCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxTree, self).__init__ (*arguments, **keywords)
    

class wxTreeList(wxTreeAndList, wx.gizmos.TreeListCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxTreeList, self).__init__ (*arguments, **keywords)
    

class Tree(RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (Tree, self).__init__ (*arguments, **keywords)
        self.openedContainers = {}
        self.rootPath = None
        self.selection = None

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

    def onSelectionChangedEvent (self, notification):
        self.widget.GoToItem (notification.GetData()['item'])
                            

class wxItemDetail(wx.html.HtmlWindow):
    def OnLinkClicked(self, wx_linkinfo):
        """
          Clicking on an item changes the selection (post notification).
          Clicking on a URL loads the page in a separate browser.
        """
        itemURL = wx_linkinfo.GetHref()
        item = Globals.repository.findPath(itemURL)
        if not item:
            webbrowser.open(itemURL)
        else:
            self.blockItem.Post (Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                                 {'item':item})

    def wxSynchronizeWidget(self):
        if self.blockItem.selection:
            self.SetPage (self.blockItem.getHTMLText (self.blockItem.selection))
        else:
            self.SetPage('<html><body></body></html>')


class ItemDetail(RectangularChild):
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

    def onSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWidget.
        """
        self.selection = notification.data['item']
        self.synchronizeWidget ()

    
class ContentItemDetail(BoxContainer):
    """
    ContentItemDetail
    Any container block in the Content Item's Detail View hierarchy.
    Not to be confused with ItemDetail (above) which uses an HTML-based widget.
    Keeps track of the current selected item
    Supports Color Style
    """
    
    def synchronizeWidget (self):
        super(ContentItemDetail, self).synchronizeWidget()
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            self.synchronizeColor()
        
    def synchronizeColor (self):
        # if there's a color style defined, syncronize the color
        if self.hasAttributeValue("colorStyle"):
            self.colorStyle.synchronizeColor(self)
           
    def selectedItem(self):
        # return the item viewed by the ContentItemDetail block
        # delegate to our parent, until we get to a SelectionContainer
        return self.parentBlock.selectedItem()

    def resynchronizeDetailView (self):
        # Resynchronize the item viewed by the ContentItemDetail block
        # delegate to our parent until we get to a SelectionContainer
        self.parentBlock.resynchronizeDetailView ()
