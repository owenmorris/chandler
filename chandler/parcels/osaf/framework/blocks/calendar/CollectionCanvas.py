""" Canvas block for displaying item collections
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx

import osaf.framework.blocks.DragAndDrop as DragAndDrop
import osaf.framework.blocks.Block as Block
import application.Globals as Globals

# Buttons used in the calendar, could be more general utilities eventually

class CanvasTextButton(wx.BitmapButton):
    def __init__(self, parent, text, font, fgcolor, bgcolor):
        bitmap = self.buildBitmap(parent, text, font, fgcolor, bgcolor)
        super(CanvasTextButton, self).__init__(parent, -1,
                                               bitmap, style=wx.BORDER_NONE)
        self.text = text
        self.font = font
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

    def OnEraseBackground(self, event):
        pass

    def buildBitmap(self, parent, text, font, fgcolor, bgcolor):

        # Have to ask the parent window for the text extent, asking
        # the memory dc doesn't work on the mac
        textExtent = parent.GetFullTextExtent(text, font)
        bitmap = wx.EmptyBitmap(textExtent[0], textExtent[1])

        dc = wx.MemoryDC()
        dc.SetFont(font)
        dc.SelectObject(bitmap)
        dc.SetBackground(wx.Brush(bgcolor))
        dc.Clear()
        dc.SetTextForeground(fgcolor)
        dc.DrawText(text, (0, 0))
        
        return bitmap
        
    def SetLabel(self, text):
        self.text = text
        bitmap = self.buildBitmap(self.GetParent(), text,
                                  self.font, self.fgcolor, self.bgcolor)
        self.SetBitmapLabel(bitmap)

class CanvasBitmapButton(wx.BitmapButton):
    def __init__(self, parent, path):
        bitmap = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        super(CanvasBitmapButton, self).__init__(parent, -1,
                                                 bitmap, style=wx.BORDER_NONE)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

    def OnEraseBackground(self, event):
        pass

class CanvasItem(object):
    def __init__(self, bounds, item):
        self.bounds = bounds
        self.item = item
        self.resizeBounds = wx.Rect(bounds.x, bounds.y + bounds.height - 5,
                                    bounds.width, 5)

    def isHit(self, point):
        return self.bounds.Inside(point)

    def isHitResize(self, point):
        return self.resizeBounds.Inside(point)

    def getItem(self):
        return self.item

class wxCollectionCanvas(wx.ScrolledWindow,
                         DragAndDrop.DropReceiveWidget,
                         DragAndDrop.DraggableWidget):
    def __init__(self, *arguments, **keywords):
        super(wxCollectionCanvas, self).__init__(*arguments, **keywords)
        self.canvasItemList = []

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)

        self._isDraggingItem = False
        self._isResizingItem = False
        self._dragStart = None
        self._dragBox = None

        # Create common fonts for drawing
        # @@@ move elsewhere
        if '__WXMAC__' in wx.PlatformInfo:
            self.bigFont = wx.Font(13, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            self.smallFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL,
                                     face="Verdana")
        else:
            self.bigFont = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            self.smallFont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL,
                                     face="Verdana")

        self.bigFontColor = wx.Colour(64, 64, 64)
        self.bgColor = wx.WHITE
        self.smallFontColor = wx.BLACK


    # Drawing utility -- scaffolding, we'll try using editor/renderers
    def DrawWrappedText(self, dc, text, rect):
        # Simple wordwrap, next step is to not overdraw the rect
        
        lines = text.splitlines()
        y = rect.y
        for line in lines:
            x = rect.x
            wrap = 0
            words = line.split(' ')
            for word in words:
                width, height = dc.GetTextExtent(word)
                if (x + width > rect.x + rect.width):
                    y += height
                    x = rect.x
                dc.DrawText(word, (x, y))
                x += width
                width, height = dc.GetTextExtent(' ')
                dc.DrawText(' ', (x, y))
                x += width
            y += height
        
    # Mouse movement

    def OnMouseEvent(self, event):

        position = event.GetPosition()
        unscrolledPosition = self.CalcUnscrolledPosition(position)

        # ignore entering and leaving events
        if (event.Entering() or event.Leaving()):
            return

        # handle dragging
        if self._isDraggingItem:
            if event.Dragging() and event.LeftIsDown():
                self.OnDraggingItem(unscrolledPosition)
            else: # end the drag
                self._isDraggingItem = False
                self.OnEndDragItem()
                self._dragBox = None
                self._dragStart = None
                self.ReleaseMouse()

        # handle resizing
        elif self._isResizingItem:
            if event.Dragging() and event.LeftIsDown():
                self.OnResizingItem(unscrolledPosition)
            else: # end the drag
                self._isResizingItem = False
                self.OnEndResizeItem()
                self._dragStart = None
                self.ReleaseMouse()
                
        else: # not dragging an item or rezising

            # create an item on double click
            if event.LeftDClick():
                self.OnCreateItem(unscrolledPosition, False)

            # handle selection if mouse down event, set up drag
            elif event.LeftDown(): 
                hitBox = None
                for box in self.canvasItemList:
                    if box.isHit(unscrolledPosition):
                        hitBox = box

                if hitBox:
                    self.OnSelectItem(hitBox.getItem())
                    self._dragBox = hitBox

                # notice drag start whether or not we hit something
                self._dragStart = position
                self._dragStartUnscrolled = unscrolledPosition

            # look for the beginning of a drag
            elif (event.Dragging() and
                  event.LeftIsDown() and
                  self._dragStart):
                
                tolerance = 2
                dx = abs(position.x - self._dragStart.x)
                dy = abs(position.y - self._dragStart.y)
                if (dx > tolerance or dy > tolerance):
                    if self._dragBox: 
                        resize = self._dragBox.isHitResize(self._dragStartUnscrolled)

                        if resize: # start resizing
                            self._isResizingItem = True
                            self.OnBeginResizeItem()
                            self.CaptureMouse()

                        else: # start dragging
                            self._isDraggingItem = True
                            self.OnBeginDragItem()
                            self.CaptureMouse()
                            
                    else: # try creating an item
                        itemBox = self.OnCreateItem(self._dragStartUnscrolled, True)
                        if itemBox: # if we have one, start resizing this item
                            self._dragBox = itemBox
                            self._isResizingItem = True
                            self.OnBeginResizeItem()
                            self.CaptureMouse()
                        else: # clear out the drag info, avoid creating more items
                            self._dragStart = None
                            self._dragBox = None
                        

    def OnCreateItem(self, position, createOnDrag):
        """ Subclasses can define to create a new item on the canvas """
        return None

    def OnBeginResizeItem(self):
        """ Subclasses can define to handle resizing """
        pass

    def OnEndResizeItem(self):
        """ Subclasses can define to handle resizing """
        pass

    def OnResizingItem(self, position):
        """ Subclasses can define to handle resizing """
        pass

    def OnBeginDragItem(self):
        """ Subclasses can define to handle dragging """
        pass

    def OnEndDragItem(self):
        """ Subclasses can define to handle dragging """
        pass

    def OnDraggingItem(self, position):
        """ Subclasses can define to handle dragging """
        pass
            
    # Painting and drawing

    def OnEraseBackground(self, event):
        pass

    def OnPaint(self, event):
        # @@@ we currently have a bug where the update regions don't 
        # always match the virtual size, creating a small black band 
        # at the bottom of the virtual window

        # double buffered drawing
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)

        # Find update rect in scrolled coordinates
        updateRect = self.GetUpdateRegion().GetBox()
        (xBuffer, yBuffer) = self.CalcUnscrolledPosition((updateRect.GetLeft(),
                                                          updateRect.GetTop()))
        wBuffer = updateRect.GetWidth()
        hBuffer = updateRect.GetHeight()

        # Create offscreen buffer
        memoryDC = wx.MemoryDC()
        buffer = wx.EmptyBitmap(wBuffer, hBuffer)
        memoryDC.SelectObject(buffer)
        memoryDC.SetDeviceOrigin(-xBuffer, -yBuffer)

        memoryDC.BeginDrawing()

        self.DrawBackground(memoryDC)
        self.DrawCells(memoryDC)

        dc.Blit((xBuffer, yBuffer),
                (wBuffer, hBuffer),
                memoryDC,
                (xBuffer, yBuffer))

        memoryDC.EndDrawing()
        
    def DrawCells(self, dc):
        """ Subclasses should define to draw the canvas cells"""
        pass

    def DrawBackground(self, dc):
        """ Subclasses should define to draw the canvas background"""
        pass

    # selection

    def OnSelectItem(self, item):
        self.blockItem.selection = item
        self.blockItem.postSelectionChanged()
        self.wxSynchronizeWidget()

    # DropReceiveWidget
    
    def OnRequestDrop(self, x, y):
        return False

    def AddItem(self, itemUUID):
        item = Globals.repository.findUUID(itemUUID)
        

    def OnHover(self, x, y):
        pass

    # DraggableWidget

    def RemoveItem(self, itemUUID):
        pass

class CollectionBlock(Block.RectangularChild):
    def __init__(self, *arguments, **keywords):
        super(CollectionBlock, self).__init__(*arguments, **keywords)
        self.selection = None

    # Event handling
    
    def onSelectionChangedEvent(self, notification):
        self.selection = notification.data['item']
        self.widget.wxSynchronizeWidget()

    def postSelectionChanged(self):
        event = Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/SelectionChanged')
        self.Post(event, {'item':self.selection})

