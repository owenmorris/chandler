__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import application.Globals as Globals
import time

class DraggableWidget (object):
    def SetDragData(self, itemUUID):
        dropSource = wx.DropSource(self)
        data = wx.CustomDataObject(wx.CustomDataFormat("ItemUUID"))
        data.SetData(str(itemUUID))
        dropSource.SetData(data)
        result = dropSource.DoDragDrop(wx.Drag_AllowMove)
        if result == wx.DragMove:
            self.RemoveItem(itemUUID)

    def RemoveItem(self, itemUUID):
        """
          Override this to remove the item from the widget when that
        item is dragged out of the widget (and the drop is accepted by
        another widget).
        """
        pass
            
class DropReceiveWidget (object):
    def __init__(self, *arguments, **keywords):
        super (DropReceiveWidget, self).__init__ (*arguments, **keywords)
        self.dropTarget = DropTarget(self)
        self.SetDropTarget(self.dropTarget)
        
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
    def __init__(self, window):
        super (DropTarget, self).__init__ ()
        self.window = window
        self.dataFormat = wx.CustomDataFormat("ItemUUID")
        self.data = wx.CustomDataObject(self.dataFormat)
        self.SetDataObject(self.data)
    
    def OnDrop(self, x, y):
        return self.window.OnRequestDrop(x, y)
    
    def OnData(self, x, y, d):
        if self.GetData():
            itemUUID = self.data.GetData()
            self.window.AddItem(itemUUID)
        return d
    
    def OnDragOver(self, x, y, d):
        self.window.OnHover(x, y)
        return d
        
    def OnEnter(self, x, y, d):
        self.enterTime = time.time()
        return d

