__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"



from wxPython.wx import *
from Persistence import Persistent
import time

class wxCanvasDropSource (wxDropSource):
    def __init__(self, drawableObject, dataObject):
        wxDropSource.__init__(self, drawableObject.canvas)
        self.drawableObject = drawableObject
        self.SetData (dataObject)
        
    def GiveFeedback (self, effect):
        windowX, windowY = wxGetMousePosition()
        x, y = self.drawableObject.canvas.ScreenToClientXY (windowX, windowY)
        self.drawableObject.dragImage.Move((x, y))
        return true
        

class wxCanvasDropTarget (wxPyDropTarget):
    def __init__(self, canvas, dropTargetDataObject):
        wxPyDropTarget.__init__(self)
        self.canvas = canvas
        self.data = dropTargetDataObject
        self.SetDataObject (dropTargetDataObject)
        
    def OnData (self, x, y, result):
        """
          Delegate functionality to the canvas
        """
        if (self.GetData()):
            x, y = self.canvas.CalcUnscrolledPosition (x, y)
            result = self.canvas.OnData (self.data, x, y, result)
            return true;
        return false

    
class wxSimpleDrawableObject (wxEvtHandler):
    def __init__(self, canvas):
        wxEvtHandler.__init__ (self)
        self.bounds = wxRect ()
        self.canvas = canvas
        self.visible = true
        self.selected = false
        EVT_MOUSE_EVENTS (self, self.OnMouseEvent)

    def MoveTo (self, x, y):
        self.canvas.RefreshScrolledRect (self.bounds);
        self.bounds.SetLeft (x)
        self.bounds.SetTop (y)
        self.canvas.RefreshScrolledRect (self.bounds);

    def OnMouseEvent (self, event):
        event.Skip ()
        x, y = event.GetPositionTuple()
        if event.ButtonDown () and self.DragHitTest (x, y):
            self.DoDrag(x, y)
    
    def Show (self, show):
        """
          Python doesn't have logical exclusive or, so we need
        to first make sure show is true if not equal to zero
        """
        if show:
            show = true
        
        if (show ^ self.visible):
            self.visible = show
            self.canvas.RefreshScrolledRect (self.bounds);
            self.canvas.Update()
            
    def ConvertToCanvasDeviceCoordinates (self, x, y):
        return self.canvas.CalcScrolledPosition (self.bounds.GetLeft() + x,
                                                 self.bounds.GetTop() + y)

    def DoDrag(self, x, y):
        """
          Implement all the drag and drop functionality:
        """

        """
          Create the dragImage and begin dragging over the full screen
        """
        offscreenBuffer = wxEmptyBitmap (self.bounds.GetWidth(), self.bounds.GetHeight())
        memoryDC = wxMemoryDC()
        memoryDC.SelectObject (offscreenBuffer)

        memoryDC.BeginDrawing()
        self.Draw (memoryDC)

        maskBitmap = wxEmptyBitmap (self.bounds.GetWidth(), self.bounds.GetHeight(), 1)
        memoryDC.SelectObject (maskBitmap)

        memoryDC.SetBackground (wxBLACK_BRUSH)
        memoryDC.Clear()               

        self.DrawMask (memoryDC)
        memoryDC.EndDrawing()

        memoryDC.SelectObject (wxNullBitmap)
        
        offscreenBuffer.SetMask (wxMask (maskBitmap))

        """
          Create the dragImage and begin dragging
        """
        self.dragImage = wxDragImage (offscreenBuffer)

        self.dragImage.BeginDrag(wxPoint (x, y), self.canvas, true)
        self.dragImage.Move (self.ConvertToCanvasDeviceCoordinates (x, y))
        self.dragImage.Show()
        """
          We need to keep a reference to the dataObject, rather than create
        it in the construction because wxCanvasDropSource doesn't own the
        data so the garbage collector will delete it.
        """
        dataObject = self.ConvertDrawableObjectToDataObject(x, y)
        dropSource = wxCanvasDropSource (self, dataObject)

        self.canvas.InternalDnDItem = self
        result = dropSource.DoDragDrop (wxDrag_AllowMove)
        self.canvas.InternalDnDItem = None
        self.dragImage.Hide()
        self.dragImage.EndDrag()

    """
      You must implement the following functions for each kind of drawableobject
    """

    def Draw (self, dc):
        """
          You must implement this routine to do draw 
        """
        assert (false)
      
    def DrawMask (self, dc):
        """
          optionally implement this routine to draw a mask
        """
        pass
      
    def DragHitTest (self, x, y):
        """
          You must implement this routine to do hit testing for dragable region
        """
        assert (false)
      
    def ConvertDrawableObjectToDataObject (self, x, y):
        """
          You must implement this routine to create data object for drag and drop
        """
        assert (false)

    
class wxSimpleCanvas (wxScrolledWindow):
    def __init__(self, parent, dropTargetDataObject):
        wxScrolledWindow.__init__( self, parent, -1, style=wxSUNKEN_BORDER)
        self.zOrderedDrawableObjects = []
        self.InternalDnDItem = None
        EVT_PAINT (self, self.OnPaint)
        EVT_ERASE_BACKGROUND (self, self.OnEraseBackground)
        EVT_MOUSE_EVENTS (self, self.OnMouseEvent)
        self.SetDropTarget (wxCanvasDropTarget (self, dropTargetDataObject))

    def RefreshScrolledRect (self, rect):
        position = rect.GetPosition()
        x, y = self.CalcScrolledPosition (position.x, position.y)
        self.RefreshRect (wxRect (x, y, rect.GetWidth(), rect.GetHeight()));
        
    def OnPaint (self, event):
        """
          wxBufferedDC doesn't work here since it doesn't handle scrolled windows
        and always allocates a buffer the size of the client area. So instead we'll
        allocate a wxMemoryDC, draw into it then blit it to our paintDC.
          Eventually, if we're printing, we should bypass the wxMemoryDC.
          The updateRegion is not in scrolled coordinates.
        """
        scrollWindowOriginX, scrollWindowOriginY = self.CalcUnscrolledPosition (0, 0)

        paintDC = wxPaintDC (self)
        self.PrepareDC (paintDC)

        """
          Calculate the rectangle that needs updating in scrolled coordinates
        """
        updateRect = self.GetUpdateRegion().GetBox()
        bufferX = updateRect.GetLeft() + scrollWindowOriginX
        bufferY = updateRect.GetTop() + scrollWindowOriginY
        bufferWidth = updateRect.GetWidth()
        bufferHeight = updateRect.GetHeight()

        memoryDC = wxMemoryDC()
        offscreenBuffer = wxEmptyBitmap (bufferWidth, bufferHeight)
        memoryDC.SelectObject (offscreenBuffer)
        memoryDC.SetDeviceOrigin (-bufferX, -bufferY)

        """
          Debugging code that makes it easy to see which areas are updating.
        """
        if 0:
            success = paintDC.Blit (bufferX,
                                    bufferY,
                                    bufferWidth,
                                    bufferHeight,
                                    paintDC,
                                    bufferX,
                                    bufferY,
                                    wxSRC_INVERT)
            time.sleep(1)
            success = paintDC.Blit (bufferX,
                                    bufferY,
                                    bufferWidth,
                                    bufferHeight,
                                    paintDC,
                                    bufferX,
                                    bufferY,
                                    wxSRC_INVERT)

        
        memoryDC.BeginDrawing()

        self.DrawBackground (memoryDC)
        self.Draw (memoryDC)

        paintDC.Blit (bufferX,
                     bufferY,
                     bufferWidth,
                     bufferHeight,
                     memoryDC,
                     bufferX,
                     bufferY)

        memoryDC.EndDrawing()
 
    def Draw (self, dc):
        updateRegion = self.GetUpdateRegion()
        scrollWindowOriginX, scrollWindowOriginY = self.CalcUnscrolledPosition (0, 0)
        dcOriginX, dcOriginY = dc.GetDeviceOrigin()
        index = len (self.zOrderedDrawableObjects) - 1
        while index >= 0:
            drawableObject = self.zOrderedDrawableObjects [index]
            objectX = drawableObject.bounds.GetLeft()
            objectY = drawableObject.bounds.GetTop()
            objectWidth = drawableObject.bounds.GetWidth()
            objectHeight = drawableObject.bounds.GetHeight()

            bounds = wxRect (objectX - scrollWindowOriginX,
                             objectY - scrollWindowOriginY,
                             objectWidth,
                             objectHeight)

            if updateRegion.ContainsRect (bounds) != wxOutRegion and drawableObject.visible:
                dc.SetDeviceOrigin (objectX + dcOriginX, objectY + dcOriginY)
                drawableObject.Draw (dc)
                dc.SetDeviceOrigin (dcOriginX, dcOriginY)
            index -= 1
    
    def OnEraseBackground (self, event):
        """
          Override OnEraseBackground to avoid erasing background. Instead
        implement OnDrawBackground to draw/erase the background. This
        design alternative will eliminate flicker
        """
        pass

    def OnMouseEvent (self, event):
        for drawableObject in self.zOrderedDrawableObjects:
            x, y = event.GetPositionTuple()
            x, y = self.CalcUnscrolledPosition (x, y)
            if drawableObject.bounds.Inside (x, y):
                event.m_x = x - drawableObject.bounds.GetX()
                event.m_y = y - drawableObject.bounds.GetY()
                if drawableObject.ProcessEvent (event):
                    return
        event.Skip()

    def OnData (self, dataObject, x, y, result):
        """
          Handle default behavior of copy and move
        """
        drawableObject = self.ConvertDataObjectToDrawableObject (dataObject, x, y)
        x = drawableObject.bounds.GetLeft()
        y = drawableObject.bounds.GetTop()
        if result == wxDragMove or result == wxDragCopy:
            if (self.InternalDnDItem != None) and (result == wxDragMove):
                assert (self.zOrderedDrawableObjects.count (self.InternalDnDItem) == 1)
                self.zOrderedDrawableObjects.remove (self.InternalDnDItem)
                self.zOrderedDrawableObjects.insert (0, self.InternalDnDItem)
                self.InternalDnDItem.MoveTo (x, y)
            else:
                self.zOrderedDrawableObjects.insert (0, drawableObject)
                self.RefreshScrolledRect (drawableObject.bounds);
        return result

    """
      You must implement the following functions for each kind of drawableobject
    """

    def ConvertDataObjectToDrawableObject (self, dataObject, x, y):
        """
          You must implement this routine to do draw 
        """
        assert (false)
