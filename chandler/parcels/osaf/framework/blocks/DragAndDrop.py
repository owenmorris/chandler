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

wxWidgets level:
    * wx.DropSource - the window you are dragging from
    * wx.DropTarget - the window you are dragging to
    * wx.DataObject - the stuff being dragged
    * wx.DataFormat - the format of the DataObject
   
CPIA level:
    * DraggableWidget - class to mixin that makes widget a DropSource
    * DropReceiveWidget - class to mixin to makes widget a DropTarget
    * DropTarget - helper object connected to the DropReceiveWidget
       that converts wxWidget callbacks to CPIA DnD callbacks.
   
       Usually there's a one-to-one correspondence between your CPIA 
    DropReceiveWidget and the wx.DropTarget.  However, the Grid case
    is a little tricky; the wx.DropTarget is the Table, but the
    DropReceiveWidget is an individual Grid element (cell).
   """
   
   
class DraggableWidget (object):
    """
    Mixin class for widgets that are draggable.
    Note that you need to list the Mixin before the base class in your
      class declaration for the right method override behavior.
    """
    def SetDragData(self, kindsCreatedByDrag):
        """
        Called to set up a widget's drag data at the beginning of a DnD.
        """
        # create a DropSource, and put our custom data into it
        # @@@DLD get better icons for the DnD cursors
        dropSource = wx.DropSource(self, move=self._DROP_ICON("ApplicationBarSend.png"),
                                   copy=self._DROP_ICON("ApplicationBarSync.png"),
                                   none=self._DROP_ICON("ApplicationDelete.png"))
        dataObject = wx.DataObjectComposite()
        for dataKind, itemUUIDList in kindsCreatedByDrag.items():
            kindFormat = wx.CustomDataFormat(dataKind)
            customData = wx.CustomDataObject(kindFormat)
            customData.SetData(','.join(map(str,itemUUIDList)))
            dataObject.Add(customData)
        dropSource.SetData(dataObject)
        # capture the mouse, so mouse moves don't trigger activities
        # in other windows, like the sidebar.
        self.CaptureMouse()
        try:
            # drag and drop the DropSource.  Many callbacks happen here.
            result = dropSource.DoDragDrop(flags=wx.Drag_AllowMove)
        finally:
            self.ReleaseMouse()
        # if we moved the item, instead of the usual copy, remove the original
        if result == wx.DragMove:
            for itemUUID in itemUUIDList:
                self.RemoveItem(itemUUID)

    def _DROP_ICON(self, filename):
        img = wx.GetApp().GetRawImage(filename)
        if wx.Platform == '__WXGTK__':
            return wx.IconFromBitmap(wx.BitmapFromImage(img))
        else:
            return wx.CursorFromImage(img)

    def KindsCreatedByDrag(self):
        """
        Return a dictionary of data that can be dragged from this item.
        Each entry has the Kind as its key, and a list of data (as UUIDs for items) for
          its value.
        Default is to export Item, ContentItem, and ItemCollection (assuming the
          item(s) really are these Kinds).
        """
        def _ExportItem(exportDict, key, itemUUID):
            if not exportDict.has_key(key):
                exportDict[key]=[]
            exportDict[key].append(itemUUID)

        exportDict = {}
        items = self.SelectedItems()
        for item in items:
            itemUUID = item.itsUUID
            _ExportItem(exportDict, "Item", itemUUID)
            if isinstance (item, ContentModel.ContentItem):
                _ExportItem(exportDict, "ContentItem", itemUUID)
            if isinstance (item, ItemCollection.ItemCollection):
                _ExportItem(exportDict, "ItemCollection", itemUUID)
        return exportDict
    
    def RemoveItem(self, itemUUID):
        """
          Override this to remove the item from the widget when that
        item is dragged out of the widget (and the drop is accepted by
        another widget).
        """
        pass
            
class DropReceiveWidget (object):
    """
    Mixin class for widgets that want to receive drag and drop events.
    Note that you need to list the Mixin before the base class in your
      class declaration for the right method override behavior.
    """
    def __init__(self, *arguments, **keywords):
        super (DropReceiveWidget, self).__init__ (*arguments, **keywords)
        self.dropTarget = DropTarget(self)
        # If it is a grid, then we need to use grid window rather than self
        try:
            window = self.GetGridWindow()
        except AttributeError:
            window = self
        window.SetDropTarget(self.dropTarget)
        
    def KindAcceptedByDrop(self):
        """
          Override to define which kinds you allow to be dropped.
        """
        return "ContentItem" # Default is only ContentItems
    
    def OnRequestDrop(self, x, y):
        """
          Override this to decide whether or not to accept a dropped 
        item.
        """
        return True
        
    def AddItem(self, itemUUID):
        """
          Override this to add the dropped item to your widget.
        """
        pass
    
    def OnHover(self, x, y):
        """
          Override this to perform an action when a drag action is
        hovering over the widget.
        """
        pass

            
class DropTarget(wx.DropTarget):
    """
        An instance of this class is a helper object that associates
        a wx.DropTarget with a receiver - a DropReceiveWidget.
        Usually these are the same object, but for Grids, they are not;
        the DropTarget is the Table, and the Grid element is the receiver.
    """
    def __init__(self, receiver):
        super (DropTarget, self).__init__ ()
        self.receiver = receiver
        # declare the kind of data we'll accept
        kindAllowed = receiver.KindAcceptedByDrop()

        self.data = wx.CustomDataObject(wx.CustomDataFormat(kindAllowed))
        self.kindAllowed = kindAllowed # @@@DLD - remove
        self.SetDataObject(self.data)
    
    def OnDrop(self, x, y):
        return self.receiver.OnRequestDrop(x, y)
    
    def OnData(self, x, y, d):
        if self.GetData():
            itemUUIDList = self.data.GetData()
            for itemUUID in itemUUIDList.split(','):
                self.receiver.AddItem(itemUUID)
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

