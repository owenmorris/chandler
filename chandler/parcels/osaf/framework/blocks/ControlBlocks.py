__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
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
                               style=style, name=self._name)

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

 
class ListDelegate:
    """
      Default delegate for Lists that use the block's contents. Override
    to customize your behavior.
    """
    def GetElementValue (self, row, column):
        result = self.blockItem.contents[item]
        name = self.blockItem.columnHeadings[column]
        try:
            return str (result.getAttributeValue(name))
        except AttributeError:
            return ""

    def SetElementValue (self, row, column, value):
        result = self.blockItem.contents[item]
        column = self.blockItem.columnHeadings[column]
        result.setAttributeValue(column, value)

    def ElementCount (self):
        return len(self.blockItem.contents)


class wxList (DraggableWidget, wx.ListCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxList, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnWXSelectionChanged, id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnItemDrag)

    def OnInit (self):
        elementDelegate = self.blockItem.elementDelegate
        if not elementDelegate:
            elementDelegate = '//parcels/osaf/framework/blocks/ControlBlocks/ListDelegate'
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
        for index in xrange (len(self.blockItem.columnHeadings)):
            self.InsertColumn(index,
                              str(self.blockItem.columnHeadings[index]),
                              width = self.blockItem.columnWidths[index])

        self.SetItemCount (self.ElementCount())
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
          Display the item in the wxWidget.
        """
        self.selection = notification.data['item']
        self.GoToItem (self.selection)


class wxTableData(wx.grid.PyGridTableBase):
    def __init__(self, *arguments, **keywords):
        super (wxTableData, self).__init__ (*arguments, **keywords)

    def GetNumberRows(self):
        """
          We've got the usual chicken & egg problems: wxWidgets calls GetNumberRows &
        GetNumberCols before wiring up the view instance variable
        """
        if self.GetView():
            return self.GetView().ElementCount()
        return 1

    def GetNumberCols(self):
        if self.GetView():
            return len (self.GetView().blockItem.columnHeadings)
        return 1

    def GetColLabelValue(self, column):
        return self.GetView().blockItem.columnHeadings[column]

    def IsEmptyCell(self, row, column): 
        return False 

    def GetValue(self, row, column): 
        return self.GetView().GetElementValue(row, column)

    def SetValue(self, row, column, value):
        self.GetView().GetElementValue(row, column, value) 


class wxTable(wx.grid.Grid):
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
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColumnDrag)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnWXSelectionChanged)

    def OnInit (self):
        elementDelegate = self.blockItem.elementDelegate
        if not elementDelegate:
            elementDelegate = '//parcels/osaf/framework/blocks/ControlBlocks/ListDelegate'
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

    def OnWXSelectionChanged(self, event):
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            item = self.blockItem.contents [event.GetRow()]
            if self.blockItem.selection != item:
                self.blockItem.selection = item
            self.blockItem.Post (Globals.repository.findPath ('//parcels/osaf/framework/blocks/Events/SelectionChanged'),
                                                              {'item':item})
            self.blockItem.selectedColumn = self.GetTable().GetColLabelValue (event.GetCol())
        event.Skip()

    def Reset(self): 
        """
          A Grid can't easily redisplay its contents, so we write the following
        helper function to readjust everything after the contents change
        """
        #Trim/extend the control's rows and update all values
        self.BeginBatch()
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

        columnIndex = 0
        for importPath in self.blockItem.columnRenderer:
            if importPath:
                parts = importPath.split (".")
                assert len(parts) >= 2, "Renderer %s isn't a module and class" % importPath
                className = parts.pop ()
                module = __import__ ('.'.join(parts), globals(), locals(), className)
                theClass = vars (module) [className]
                renderer = theClass (gridTable)
        
                attribute = wx.grid.GridCellAttr()
                attribute.SetReadOnly (renderer.IsReadOnly())
                attribute.SetRenderer (renderer)
                self.SetColAttr (columnIndex, attribute)
            columnIndex = columnIndex + 1

        #Update all displayed values
        message = wx.grid.GridTableMessage (gridTable, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES) 
        self.ProcessTableMessage (message) 
        self.EndBatch() 

        # The scroll bars aren't resized (at least on windows) 
        # Jiggling the size of the window rescales the scrollbars 
        h,w = self.GetSize() 
        self.SetSize ((h+1, w)) 
        self.SetSize ((h, w)) 
        self.ForceRefresh () 

    def wxSynchronizeWidget(self):
        self.blockItem.contents.resultsStale = True
        self.Reset()
        if self.blockItem.selection:
            self.GoToItem (self.blockItem.selection)

    def GoToItem(self, item):
        row = self.blockItem.contents.index (item)

        cursorColumn = 0
        try:
            selectedColumn = self.blockItem.selectedColumn
        except AttributeError:
            pass
        else:
            table = self.GetTable()
            for columnIndex in xrange (table.GetNumberCols()):
                if table.GetColLabelValue(columnIndex) == selectedColumn:
                    cursorColumn = columnIndex
                    break

        self.SelectRow (row)
        self.SetGridCursor (row, cursorColumn)


class SmileRenderer (wx.grid.PyGridCellRenderer):
    def __init__(self, gridTable):
        super (SmileRenderer, self).__init__ ()
        self.gridTable = gridTable
        self.image = self.GetImage()

    def IsReadOnly (self):
        return True

    def Draw (self, grid, attr, dc, rect, row, col, isSelected):
        offscreenBuffer = wx.MemoryDC()
        offscreenBuffer.SelectObject(self.image)

        # clear the background
        dc.SetBackgroundMode(wx.SOLID)

        if isSelected:
            dc.SetBrush(wx.Brush(wx.BLUE, wx.SOLID))
            dc.SetPen(wx.Pen(wx.BLUE, 1, wx.SOLID))
        else:
            dc.SetBrush(wx.Brush(wx.WHITE, wx.SOLID))
            dc.SetPen(wx.Pen(wx.WHITE, 1, wx.SOLID))
        dc.DrawRectangleRect(rect)

        #dc.DrawRectangle((rect.x, rect.y), (rect.width, rect.height))

        # copy the offscreenBuffer but only to the size of the grid cell
        width, height = self.image.GetWidth(), self.image.GetHeight()

        if width > rect.width-2:
            width = rect.width-2

        if height > rect.height-2:
            height = rect.height-2

        dc.Blit ((rect.x+1, rect.y+1),
                 (width, height),
                 offscreenBuffer,
                 (0, 0),
                 wx.COPY,
                 True)

    def GetImage (self):
        data = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06' + \
               '\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00' + \
               '\x00\x02\x97IDATx\x9ce\x93\xcdkSi\x18\xc5\x7f\xef\xfd\x88iC\x85\x11\xeaW\xbd' + \
               '1Z\x83D\x04\x11a\x18\xc4\x8e\xd8\x8e\x9dB\x87Y\xe8N\xc2(6\xf1\x82[).\xdd\xa6' + \
               '\xfe\x01nj7\xf3?\x14\x06k\xbb)sA\x04Q\xd3!\tZ\xda\xe9\x07\xc8\xc0\x08\xc5' + \
               '\xb64\xefm<.r[[}\xe0,\xde\x8f\xf3>\xbc\xe7<\x07\xe3\xb8\xec\xc5\xf4\xf4\xb4' + \
               '\x8a\xc5[\xca\xe5\x8e\xc9\xf3\x8c|\xdfQ>\x1f(\x0c\xcb\x8a\xa2H\xdf\xde\xdf' + \
               '\xb7\x08\xc3\xb2\x82 \xa3J\xe5\'U\xab7emQ\xd6\xdeR\xb5\xfa\x9b*\x95\xac\x82' + \
               '\xc0(\x0cK\xfb\x1f1\x8e\x0b\xc0\xf5_~V6\xfb?O\x9e\xfc\x8e\xef[`\x03X\x07Z@' + \
               '\x13\x98\'\x8ek\xdc\xbfoYZ\xba\xcc\xd4\xf3\xc8\x008\x00\xf7\xcaw\x95\xcd\xc2' + \
               '\xf8x\x05\xdf/\x00\x99\x84(\xda\xb5\x05l\xe2\xfb\x86\xf1\xf1\x03d\xb3\xb3' + \
               '\xdc+\xdfi\x1fFQ\xa4 8$kk\x92\x16%=\xd3\xe8\xe8\xa8\x00IEIE\x01\xea\xee\xee' + \
               '\x96\xd4)\xa9C\xd6\xa2\xe0\x04mM\xc2\xb0\xacS\xa7\xb6y\xf8\xf0\x11\xe0\x02' + \
               '\xff`\xcc\x10\x00R\x11X\xa3PxG\xbd^G\xea\x04\xb5`\xdb0\xf6\xb8\xc5\xc2R\x11g' + \
               'f\xe6/\x86\x87{\x80U`\x1ex\xcd\xd7j\x02\xab,//\xef\xd9\xfb\x0c\xcdN\x86\x07' + \
               '\xba\x98\x99\x99\xc4\xf8\xbe\xa3\x8d\x8d\x07\xf8~\x17\xb0\xc5\xc8\xc8\x07&&' + \
               '\xec\xaep\xb0\x9c\x08\x9a\x90[-X;L\xbc\xe5\x929\xb9\xd4\x16\x11l\xa2\xf8\'&&' + \
               'b`\r\xa8\x02\x8d=d\x81\xb69}"\rq\x07\xc4i\x00\x9c\\\xae\x87Fc\x05\xf8\x0fhP(' + \
               '\xbc\x04^$\x9d\xf5\x95L\x0c-\x87\x85\x0f\x9f`\xb3\x8bF\xdd\x90;\xd9\x8d\xd7' + \
               '\xdf\xff+\x93\x93\x7fr\xfe|\n\x10\xb5\x1ad2bc\xa71\x9f\x81mh\x19.\x9d\xebB' + \
               '\x8b=\xb0y\x90\xc9g\x1f\xe9\xbf:\xb0c\xa3\x91\xb5\x1d\x89Mm\xab\x94N+\x95J' + \
               '\xc9\xf3\\e\xd2\x9e.\xf4\x1e\x92V\xcfJ\xb5>\xd9W\xd7\x14\x1cM)\x9a\x9dV2\xc2' + \
               '#*\x95\x8c$?\x81\'\xc9\x95\x8c\x91\x0ex\xea\xbfx\\Z\xbc \xd5\xafH\xd5\x01' + \
               '\x95n\x1cWx\xfb\x86\xf6eap\xb0O\xa5\x12\xb2\x16I\tZ\x8e\xb4\xfe\x83\xb4R\x90' + \
               '\xde\xff(\xfb\xe6\x8aJ7\x8fj\xf0\xea\xc5\xdd<8;?\x9dz\x1e\x19\xd7\x1d\xa1' + \
               '\xb7\x17\xc6\xc6`n\x0e\xe2\xa6K\xdct\x98{\xb7\xce\xd8\xd3\x7f\xe9\x1dz\x81{' + \
               '\xb0\x8f\xa9\xd9\xb7fw,\xbe\x8dg\x14E\n\xc3\xbb\xca\xe7\x8f\xc8\xf7\x90\xef' + \
               '\xa1\xfc\x99\xc3\n\xcb\x7f(\xfa{\xf6\xbb8\x7f\x01 \xf1c\xdaX\x1e\x99\x02\x00' + \
               '\x00\x00\x00IEND\xaeB`\x82' 
        from wx import ImageFromStream, BitmapFromImage
        import cStringIO
        return BitmapFromImage (ImageFromStream (cStringIO.StringIO (data)))


class Table(RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (Table, self).__init__ (*arguments, **keywords)
        self.selection = None

    def instantiateWidget (self):
        return wxTable (self.parentBlock.widget, Block.getWidgetID(self))

    def onSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWidget.
        """
        self.selection = notification.data['item']
        self.GoToItem (self.selection)


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

class StaticText(RectangularChild):
    def instantiateWidget (self):
        if self.textAlignmentEnum == "Left":
            style = wx.ALIGN_LEFT
        elif self.textAlignmentEnum == "Center":
            style = wx.ALIGN_CENTRE
        elif self.textAlignmentEnum == "Right":
            style = wx.ALIGN_RIGHT

        staticText = wx.StaticText (self.parentBlock.widget,
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
        assert frame.GetStatusBar() == None
        widget = wxStatusBar (frame, Block.getWidgetID(self))
        frame.SetStatusBar (widget)
        return widget


class ToolbarItem(Block):
    """
      Under construction
    """
    def instantiateWidget (self):
        # @@@ Must use self.toolbarLocation rather than wxMainFrame.GetToolBar()
        tool = None
        wxToolbar = self.toolbarLocation.widget
        id = Block.getWidgetID(self)
        if self.toolbarItemKind == 'Button':
            bitmap = wx.Image (self.bitmap, 
                               wx.BITMAP_TYPE_PNG).ConvertToBitmap()
            tool = wxToolbar.AddSimpleTool (id, bitmap, 
                                            self.title, self.statusMessage)
            wxToolbar.Bind (wx.EVT_TOOL, wxToolbar.blockItem.toolPressed, id=id)
        elif self.toolbarItemKind == 'Separator':
            # hack - if the title looks like a number, then add that many spearators.
            numSeps = 1
            if self.hasAttributeValue("title"):
                numSeps = int(self.title)
                if numSeps < 1:
                    numSeps = 1
            for i in range(0, numSeps):
                wxToolbar.AddSeparator()
        elif self.toolbarItemKind == 'Check':
            pass
        elif self.toolbarItemKind == 'Radio':
            pass
        elif self.toolbarItemKind == 'Text':
            tool = wx.TextCtrl (wxToolbar, id, "", 
                               wx.DefaultPosition, 
                               wx.Size(300,-1), 
                               wx.TE_PROCESS_ENTER)
            tool.SetName(self.title)
            wxToolbar.AddControl (tool)
            tool.Bind(wx.EVT_TEXT_ENTER, wxToolbar.blockItem.toolEnterPressed, id=id)
        elif self.toolbarItemKind == 'Combo':
            proto = self.prototype
            choices = proto.choices
            tool = wx.ComboBox (wxToolbar,
                            -1,
                            proto.selection, 
                            wx.DefaultPosition,
                            (proto.minimumSize.width, proto.minimumSize.height),
                            proto.choices)            
            wxToolbar.AddControl (tool)
        elif __debug__:
            assert False, "unknown toolbarItemKind"

        wxToolbar.Realize()

        return tool


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
            for child in self.ElementChildren (Globals.repository [parentUUID]):
                cellValues = self.ElementCellValues (child)
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
            self.blockItem.columnHeadings
        except AttributeError:
            pass # A wx.TreeCtrl won't use columnHeadings
        else:
            for index in xrange(self.GetColumnCount()):
                self.RemoveColumn (0)
    
            info = wx.gizmos.TreeListColumnInfo()
            for index in xrange (len(self.blockItem.columnHeadings)):
                info.SetText (self.blockItem.columnHeadings[index])
                info.SetWidth (self.blockItem.columnWidths[index])
                self.AddColumnInfo (info)

        self.DeleteAllItems()

        root = self.blockItem.rootPath
        if not root:
            root = self.ElementChildren (None)
        cellValues = self.ElementCellValues (root)
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
            parent = self.ElementParent (item)
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
            self.columnHeadings
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
            event = Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged')
            event.Post({'item':item, 'type':'Normal'})

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
        
class SelectionContainer(BoxContainer):
    """
    SelectionContainer
    Keeps track of the current selected item
    """
    def __init__(self, *arguments, **keywords):
        super (SelectionContainer, self).__init__ (*arguments, **keywords)
        self.selection = None

    def onSelectionChangedEvent (self, notification):
        """
          just remember the new selected ContentItem.
        """
        self.selection = notification.data['item']

    def selectedItem(self):
        # return the item being viewed
        return self.selection
    
class ContentItemDetail(SelectionContainer):
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
           
