__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import application.Globals as Globals
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.ItemCollection as ItemCollection
import time

"""
Overview of Drag and Drop infrastructure:

Mixin classes are provided that should be mixed in to your widget class:
    Use DraggableWidget for things that export data through Drag & Drop.
    Use DropReceiveWidget for things that import data through Drag & Drop.
    Use one of the ClipboardDataHandlers to handle copying data from a
            widget or pasting data into a widget.
        TextClipboardHandler handles Text data with EditText widgets
        ItemClipboardHandler handles Item data, with help from the Content Model

Since most of Chandler data are Items, most widgets will use the ItemClipboardHandler.
    Widgets that mix in ItemClipboardHandler should implement:
        SelectedItems() to return a list of items currently selected (Copy, Drag)
        AddItems() to insert a list of items (Paste, Drop)
        DeleteSelection() to remove the selected items (Cut, Move)

It's easy to write new ClipboardHandlers for your own kind of data:
    CopyData() - gather data from your widget into a DataObject
    PasteData() - place data from a DataObject into your widget
    ClipboardDataFormat() - define the format of your DataObject
    ClipboardDataObject() - create your data object
    CanCopy(), CanCut(), CanPaste() - return booleans
    Cut(), Copy(), Paste() - interact with the clipboard calling 
        CopyData() or PasteData().

wxWidgets level:
    * wx.DropSource - the window you are dragging from
    * wx.DropTarget - the window you are dragging to
    * wx.DataObject - the stuff being dragged
    * wx.DataFormat - the format of the DataObject
   
CPIA level:
    * DraggableWidget - class to mixin that makes widget a DropSource
    * DropReceiveWidget - class to mixin to make a widget a DropTarget
    * _DropTarget - helper object connected to the DropReceiveWidget
       that converts wxWidget callbacks to CPIA DnD callbacks.
   
       Usually there's a one-to-one correspondence between your CPIA 
    DropReceiveWidget and the wx.DropTarget.  However, the Grid case
    is a little tricky; the wx.DropTarget is the Table, but the
    DropReceiveWidget is an individual Grid element (cell).  This
    allows the Table to decide if the drop should be onto itself
    or onto its Grid elements.  The default table implementation
    drops onto itself, but the Sidebar drops onto its Grid elements.
"""
   
   
class DraggableWidget (object):
    """
    Mixin class for widgets that are draggable.
    """
    def DoDragAndDrop(self, copyOnly=None):
        """
        Do a Drag And Drop operation, given the data in the selection.
        If you want to disable Move, pass True for copyOnly.  Passing
           False allows the Move.  Passing None (the default) will
           allow the Move iff you have a DeleteSelection method.
        """
        # make sure we got mixed in OK, so the __init__ got called.
        if __debug__:
            assert self.clipboardHandlerInited, "Object of type %s never inited its ClipboardHandler" % type(self)
        # set up copyOnly flag - so we know if a 'move' is allowed
        if copyOnly is None:
            if not hasattr (self, 'DeleteSelection'):
                copyOnly = True
            else:
                copyOnly = False

        # set up cursor icons for user feedback
        iconParams = {'copy': self._DROP_ICON("DragCopyCursor.png"),
                      'none': self._DROP_ICON("DragNotCursor.png")}

        # copyOnly mode - a 'move' operations are allowed, but we treat
        #  them like 'copy' to get the right cursor defaults
        flags = wx.Drag_AllowMove
        if copyOnly:
            # copy and move are the same - show the same cursor icon
            iconParams['move'] = iconParams['copy']
        else:
            # copy and move a different, load separate 'move' cursor
            moveCursor = self._DROP_ICON("DragMoveCursor.png")
            if moveCursor is not None:
                iconParams['move'] = moveCursor

        # create the drop source, set up its data
        dropSource = wx.DropSource(self, **iconParams)
        dataObject = self.CopyData()
        dropSource.SetData(dataObject)

        # capture the mouse, so mouse moves don't trigger activities
        # in other windows, like the sidebar.
        self.CaptureMouse()
        try:
            # drag and drop the DropSource.  Many callbacks happen here.
            result = dropSource.DoDragDrop(flags=flags)
        finally:
            if self.HasCapture():
                self.ReleaseMouse()

        # if we moved the item, instead of the usual copy, remove the original
        if not copyOnly and result == wx.DragMove:
            self.DeleteSelection()

    def _DROP_ICON(self, filename):
        # This macro from wxWidgets is going to be in wxPython soon.
        img = wx.GetApp().GetRawImage(filename)
        if img is None:
            return None
        if wx.Platform == '__WXGTK__':
            return wx.IconFromBitmap(wx.BitmapFromImage(img))
        else:
            return wx.CursorFromImage(img)

class DropReceiveWidget (object):
    """
    Mixin class for widgets that want to receive drag and drop events.
    """
    def __init__(self, *arguments, **keywords):
        super (DropReceiveWidget, self).__init__ (*arguments, **keywords)
        self.dropTarget = _DropTarget(self)
        # If it is a grid, then we need to use grid window rather than self
        try:
            window = self.GetGridWindow()
        except AttributeError:
            window = self
        window.SetDropTarget(self.dropTarget)
        
    def OnRequestDrop(self, x, y):
        """
          Override this to decide whether or not to accept a dropped 
        item.
        """
        return True
        
    def OnHover(self, x, y):
        """
          Override this to perform an action when a drag action is
        hovering over the widget.
        """
        pass

    def OnHoverLeave(self):
        """
          Override this to perform an action when hovering terminates.
        """
        pass

class _DropTarget(wx.DropTarget):
    """
        An instance of this class is a helper object that associates
        a wx.DropTarget with a receiver - a DropReceiveWidget.
        Usually these are the same object, but for Grids, they are not;
        the _DropTarget is the Table, and the Grid element is the receiver.
    """
    def __init__(self, receiver):
        super (_DropTarget, self).__init__ ()
        self.receiver = receiver
        # create a data object for the kind of data we'll accept
        self.dataObject = receiver.ClipboardDataObject()
        self.SetDataObject(self.dataObject)
    
    def OnDrop(self, x, y):
        return self.receiver.OnRequestDrop(x, y)
    
    def OnData(self, x, y, d):
        if self.GetData():
            dataToPaste = self.dataObject
            self.receiver.PasteData(dataToPaste)
        return d
    
    def OnDragOver(self, x, y, d):
        self.receiver.OnHover(x, y)
        return d
        
    def OnEnter(self, x, y, d):
        self.enterTime = time.time()
        return d

    def OnLeave(self):
        try:
            leaveMethod = self.receiver.OnHoverLeave
        except AttributeError:
            pass
        else:
            leaveMethod()

class _ClipboardHandler(object):
    if __debug__:
        def __init__(self, *args, **keys):
            super(_ClipboardHandler, self).__init__(*args, **keys)
            self.clipboardHandlerInited = True

    def DataObjectFormat(self):
        format = self.ClipboardDataFormat()
        if isinstance(format, int):
            return wx.DataFormat(format)
        else:
            return wx.CustomDataFormat(format)

class TextClipboardHandler(_ClipboardHandler):
    """
    Mixin class to give your widget Text-based clipboard handling.
    """
    def CopyData(self):
        """
        Called to get a widget's data at the beginning of a Copy or DnD.
        Returns a wxDataObject variant for use in Drag and Drop, or Cut and Paste.
        This implementation returns a Text data object.
        """
        dataObject = wx.TextDataObject()
        dataObject.SetText(self.GetStringSelection())
        # There's a bug on the Mac in DnD.  Here's the workaround:
        import os
        if not os.environ.get('CHANDLER_NO_DnD_WORKAROUND'): # set to disable workaround
            # wrap the TextDataObject in a CompositeDataObject.
            compositeObject = wx.DataObjectComposite()
            compositeObject.Add(dataObject)
            return compositeObject
        return dataObject

    def PasteData(self, data):
        """
        Paste the supplied data into ourself, either
        because of a Paste operation, or a Drag and Drop.
        Assumes that the datum is Text.
        """
        text = data.GetText()
        self.WriteText(text)

    def ClipboardDataFormat(self):
        """
          Override to define which kinds you allow to be dropped.
        """
        return wx.DF_TEXT # Default is any kind of Text.

    def ClipboardDataObject(self):
        return wx.TextDataObject()
    
    """ 
    EditText widgets already implement CanCopy, CanCut, CanPaste,
    Copy, Cut, Paste, etc, so we don't need to here.
    """

class ItemClipboardHandler(_ClipboardHandler):
    """
    Mixin class to give your widget Item-based clipboard handling.
    Defines methods to Cut & Paste, and enable the menus.
    Calls back to your widget for Item-based selection handling:
        SelectedItems(), DeleteSelection(), AddItems(), etc
    """
    def AddItems(self, itemList):
        """
          Override this to add the dropped items to your widget.
        """
        pass
    
    def SelectedItems(self):
        """
          Override this to return the list of selected items.
        """
        pass
    
    def DeleteSelection(self):
        """
          Override this to remove the selection.
        """
        pass
    
    def CopyData(self):
        """
        Called to get a widget's data at the beginning of a Copy or DnD.
        Returns a wxDataObject variant for use in Drag and Drop, or Cut and Paste.
        This implementation deals with Items using UUIDs, using the Content Model
            to determine what formats to export.
        """
        compositeObject = wx.DataObjectComposite()

        # Build a dictonary of Item data formats
        self.exportDict = {}
        items = self.SelectedItems()
        for item in items:
            # add to the 'Item' list of our dictionary
            self.ExportItemFormat(item, 'Item')
            try:
                # ask the ContentItem to append its kinds too
                item.ExportItemData(self)
            except AttributeError:
                pass

        # now create a custom data object for each kind
        for format, itemUUIDList in self.exportDict.items():
            customData = wx.CustomDataObject(wx.CustomDataFormat(format))
            customData.SetData(','.join(itemUUIDList))
            compositeObject.Add(customData)

        # Add Text format data - use the Item's display name
        names = []
        for item in items:
            try:
                names.append(item.about)
            except AttributeError:
                pass
        textObject = wx.TextDataObject()
        textObject.SetText(', '.join(names))
        compositeObject.Add(textObject)
        
        return compositeObject

    def ExportItemFormat(self, item, format):
        # Callback for the ContentModel to tell us what format data to export.
        # Builds a dictionary keyed by format with a lists of item UUID strings.
        try:
            itemUUIDList = self.exportDict[format]
        except KeyError:
            itemUUIDList = []
            self.exportDict[format] = itemUUIDList
        itemUUIDList.append(str(item.itsUUID))

    def ClipboardDataFormat(self):
        """
          Override to define which kind you allow to be dropped.
        """
        return "Note" # Default is any kind of Note or subclass of Note.
    
    def ClipboardDataObject(self):
        format = self.ClipboardDataFormat()
        return wx.CustomDataObject(wx.CustomDataFormat(format))

    def CanCopy(self):
        try:
            items = self.SelectedItems()
        except AttributeError:
            return False
        return len(items) > 0

    def CanCut(self):
        if not hasattr (self, 'DeleteSelection'):
            return False
        return self.CanCopy()

    def Copy(self):
        clipboard = wx.TheClipboard
        if clipboard.Open():
            data = self.CopyData()
            clipboard.SetData(data)
            clipboard.Close()

    def Cut(self):
        self.Copy()
        try:
            self.DeleteSelection()
        except AttributeError:
            pass # doesn't know DeleteSelection()

    def CanPaste(self):
        clipboard = wx.TheClipboard
        formatWeCanPaste = self.DataObjectFormat()
        supportsOurKinds = clipboard.IsSupported(formatWeCanPaste)
        return supportsOurKinds

    def Paste(self):
        clipboard = wx.TheClipboard
        if clipboard.Open():
            dataToPaste = self.ClipboardDataObject()
            if clipboard.GetData(dataToPaste):
                self.PasteData(dataToPaste)
            clipboard.Close()

    def PasteData(self, data):
        """
        Paste the supplied data into ourself, either
        because of a Paste operation, or a Drag and Drop.
        Assumes that the data are Items, override for other kinds.
        """
        itemUUIDList = data.GetData()
        itemList = []
        for itemUUID in itemUUIDList.split(','):
            item = self.blockItem.findUUID(itemUUID)
            if item is not None:
                itemList.append(item)
        if len(itemList)>0:
            self.AddItems(itemList)

