__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from wxPython.wx import *
import time


class wxCanvasDragImage(wxFrame):
    """
    A class similar to wxDragImage except that it uses a shaped frame
    to display the image, and that it is always full screen.
    """
    def __init__(self, bitmap):
        wxFrame.__init__(self, None, -1, "",
                         style = wxFRAME_SHAPED
                         | wxSIMPLE_BORDER
                         | wxFRAME_NO_TASKBAR
                         | wxSTAY_ON_TOP)
        self.bmp = bitmap
        w, h = self.bmp.GetWidth(), self.bmp.GetHeight()
        self.SetClientSize( (w, h) )
        self.hotspot = None
        self.window = None

        EVT_PAINT(self, self.OnPaint)

        if wxPlatform == "__WXGTK__":
            # wxGTK requires that the window be created before you can
            # set its shape, so delay the call to SetWindowShape until
            # this event.
            EVT_WINDOW_CREATE(self, self.SetWindowShape)
        else:
            # On wxMSW and wxMac the window has already been created, so go for it.
            self.SetWindowShape()



    def SetWindowShape(self, evt=None, hotspot=None):
        # Use the bitmap's mask to determine the region
        rgn = wxRegionFromBitmap(self.bmp)
        if hotspot is not None:
            # punch a hole in the region at the hotspot to allow mouse events
            # through to the window below
            rect = wxRect(hotspot.x-1, hotspot.y-1, 3, 3)
            rgn.SubtractRect(rect)
        self.SetShape(rgn)


    def BeginDrag(self, hotspot, window, *ignoreOthers):
        self.hotspot = wxPoint(hotspot[0], hotspot[1])
        if wxPlatform != "__WXGTK__":
            self.SetWindowShape(hotspot = self.hotspot)
        self.window = window
        if self.window:
            self.window.CaptureMouse()


    def EndDrag(self, doDestroy=True):
        if self.window and self.window.HasCapture():
            self.window.ReleaseMouse()
        self.Hide()
        if doDestroy:
            self.Destroy()


    def Move(self, pt):
        """
        Move the image to a new location on screen.  The pt parameter
        is a point in client coordinants relative to the window
        specifed in BeginDrag.  (Only for compatibility with
        wxDragImage, otherwise I would just use screen coordinants...)
        """
        pt2 = pt
        if self.window:
            pt2 = self.window.ClientToScreen(pt)
        self.SetPosition(pt2 - self.hotspot)


    def Show(self):
        wxFrame.Show(self)
        self.Update()


    def OnPaint(self, evt):
        dc = wxPaintDC(self)
        dc.DrawBitmap(self.bmp, 0,0, True)



class wxCanvasDropSource (wxDropSource):
    def __init__(self, drawableObject, dataObject):
        wxDropSource.__init__(self, drawableObject.canvas)
        self.drawableObject = drawableObject
        self.SetData (dataObject)

    def GiveFeedback (self, effect):
        windowX, windowY = wxGetMousePosition()
        x, y = self.drawableObject.canvas.ScreenToClientXY (windowX, windowY)
        self.drawableObject.dragImage.Move((x, y))
        return False


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
        return result



class wxSimpleDrawableObject (wxEvtHandler):
    def __init__(self, canvas):
        wxEvtHandler.__init__ (self)
        self.bounds = wxRect ()
        self.canvas = canvas
        self.visible = True
        self.selected = False
        self.dragStartPos = None
        EVT_MOUSE_EVENTS (self, self.OnMouseEvent)

    def MoveTo (self, x, y):
        self.canvas.RefreshScrolledRect (self.bounds);
        self.bounds.SetLeft (x)
        self.bounds.SetTop (y)
        self.canvas.RefreshScrolledRect (self.bounds);

    def SetSize (self, width, height):
        self.canvas.RefreshScrolledRect (self.bounds);
        self.bounds.SetWidth (width)
        self.bounds.SetHeight (height)
        self.canvas.RefreshScrolledRect (self.bounds);

    def OnMouseEvent (self, event):
        x, y = event.GetPositionTuple()
        if event.ButtonDown(1) and self.SelectedHitTest (x, y) :
            self.canvas.DeSelectAll()
            self.SetSelected()
            self.canvas.Update()
            if self.DragHitTest (x, y):
                self.dragStartPos = (x, y)
        elif event.ButtonUp(1):
            self.dragStartPos = None
        elif event.Dragging() and event.LeftIsDown():
            tolerance = 2
            if abs(x - self.dragStartPos[0]) > tolerance or abs(y - self.dragStartPos[1]) > tolerance:
                self.DoDrag(x, y)
                return True
        event.Skip()
        return False

    def SetBounds (self, bounds):
        self.canvas.RefreshScrolledRect (self.bounds);
        self.bounds = bounds
        self.canvas.RefreshScrolledRect (self.bounds);

    def Show (self, show):

        # Make sure show is a Boolean
        show = bool(show)

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

        if wxPlatform == "__WXMAC__":  # workaround for wxMac bug
            offscreenBuffer.SetMask (wxMaskColour(maskBitmap, wxBLACK))
        else:
            offscreenBuffer.SetMask (wxMask(maskBitmap))

        """
          Create the dragImage and begin dragging
        """
        if wxPlatform == "__WXGTK__":
            # The "hole punching" trick dosen't work on wxGTK, move the hostspot
            # to be just outside the image
            x, y = -1, -1
        self.dragImage = wxCanvasDragImage (offscreenBuffer)

        self.dragImage.BeginDrag(wxPoint (x,y), self.canvas, True)
        self.dragImage.Move (self.ConvertToCanvasDeviceCoordinates (x, y))
        self.dragImage.Show()

        """
          We need to keep a reference to the dataObject, rather than create
        it in the construction because wxCanvasDropSource doesn't own the
        data so the garbage collector will delete it.
        """
        dataObject = self.ConvertDrawableObjectToDataObject(x, y)
        dropSource = wxCanvasDropSource (self, dataObject)

        self.canvas.internalDnDItem = self
        result = dropSource.DoDragDrop (wxDrag_AllowMove)
        self.canvas.internalDnDItem = None
        self.dragImage.Hide()
        self.dragImage.EndDrag()
        del self.dragImage


    def DrawMask (self, dc):
        """
          optionally implement this routine to draw a mask
        """
        pass

    def SizeDrag (self, dragRect, startDrag, endDrag):
        self.canvas.RefreshScrolledRect (self.bounds)
        self.bounds = dragRect
        self.canvas.RefreshScrolledRect (self.bounds)

    """
      You must implement the following functions
    """

    def Draw (self, dc):
        """
          You must implement this routine to do draw
        """
        assert (False)

    def DragHitTest (self, x, y):
        """
          You must implement this routine to do hit testing for dragable region
        of drawable object
        """
        assert (False)

    def ConvertDrawableObjectToDataObject (self, x, y):
        """
          You must implement this routine to create data object for drag and drop
        """
        assert (False)

    def SelectedHitTest (self, x, y):
        """
        You must implement this routine to do hit testing to identify the region
        for selecting the object.
        """
        assert (False)

    def SetSelected(self, selected=True):
        """
        Sets the selected bit for this object. Does a canvas refresh on the object
        if it has changed state. Does not call Update on the canvas.
        """
        # Use the same trick as Show()
        selected = bool(selected)

        # Only do a refresh if we've changed state.
        if (selected ^ self.selected):
            self.selected = selected
            self.canvas.RefreshScrolledRect (self.bounds);

class wxSimpleCanvas (wxScrolledWindow):

    def __init__ (self, *_args, **_kwargs):
        wxScrolledWindow.__init__ (self, *_args, **_kwargs)

    def OnInit (self, dropTargetDataObject):
        """
          We have an extra OnInit in addition to the __init__, which you must
        remember to call. This is necessary because of how wxSimpleCanvases are
        stored in XRC, but treated like wxScrolledWindows
        """
        self.autoCreateDistance = 0
        self.zOrderedDrawableObjects = []
        self.internalDnDItem = None
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
        x, y = event.GetPositionTuple()
        x, y = self.CalcUnscrolledPosition (x, y)
        for drawableObject in self.zOrderedDrawableObjects:
            if drawableObject.bounds.Inside ((x, y)):
                event.m_x = x - drawableObject.bounds.GetX()
                event.m_y = y - drawableObject.bounds.GetY()
                if drawableObject.ProcessEvent (event):
                    return True

        if self.autoCreateDistance != 0:
            if event.ButtonDown() and self.CreateHitTest (x, y):
                self.dragStart = wxPoint (x, y)
                self.CaptureMouse()
                return True
            elif hasattr (self, 'dragStart'):
                if event.Dragging():
                    """
                      Clip mouse position to the scrolling window's bounds
                    """
                    boundsX, boundsY = self.GetVirtualSizeTuple()
                    if x < 0:
                        x = 0
                    if x > boundsX:
                        x = boundsX
                    if y < 0:
                        y = 0
                    if y > boundsY:
                        y = boundsY

                    deltaX =  x - self.dragStart.x
                    deltaY =  y - self.dragStart.y

                    if deltaX >= 0:
                        left = self.dragStart.x
                        width = deltaX
                    else:
                        left = x
                        width = -deltaX

                    if deltaY >= 0:
                        top = self.dragStart.y
                        height = deltaY
                    else:
                        top = y
                        height = -deltaY
                    dragRect = wxRect (left, top, width, height)

                    if not hasattr (self, 'dragCreateDrawableObject'):
                        if (deltaX * deltaX) + (deltaY * deltaY) > (self.autoCreateDistance * self.autoCreateDistance):
                            """
                               Create a new drawable object if we've dragged autoCreateDistance
                            pixels
                            """
                            self.dragCreateDrawableObject = self.CreateNewDrawableObject (dragRect,
                                                                                          self.dragStart,
                                                                                          wxPoint (x, y))
                            # if we weren't allowed to create one, give up
                            if self.dragCreateDrawableObject == None:
                                return True

                            self.DeSelectAll()
                            self.dragCreateDrawableObject.selected = True
                            self.zOrderedDrawableObjects.insert (0, self.dragCreateDrawableObject)
                            self.RefreshScrolledRect (self.dragCreateDrawableObject.bounds);
                        return True
                    else:
                        if self.dragCreateDrawableObject != None:
                            self.dragCreateDrawableObject.SizeDrag (dragRect,
                                                                    self.dragStart,
                                                                    wxPoint (x, y))

                elif event.ButtonUp():
                    del self.dragStart
                    if hasattr (self, 'dragCreateDrawableObject'):
                        del self.dragCreateDrawableObject
                    self.ReleaseMouse()
                    return True
        return False

    def OnData (self, dataObject, x, y, result):
        """
          Handle default behavior of copy and move
        """
        if result == wxDragMove or result == wxDragCopy:
            if (self.internalDnDItem != None) and (result == wxDragMove):
                assert (self.zOrderedDrawableObjects.count (self.internalDnDItem) == 1)
                
                drawableObject = self.ConvertDataObjectToDrawableObject (dataObject, x, y, True)
                x = drawableObject.bounds.GetLeft()
                y = drawableObject.bounds.GetTop()

                self.zOrderedDrawableObjects.remove (self.internalDnDItem)
                self.zOrderedDrawableObjects.insert (0, self.internalDnDItem)
                self.internalDnDItem.MoveTo (x, y)
            else:

                drawableObject = self.ConvertDataObjectToDrawableObject(dataObject, x, y, False)
                x = drawableObject.bounds.GetLeft()
                y = drawableObject.bounds.GetTop()
                
                self.zOrderedDrawableObjects.insert (0, drawableObject)
                self.RefreshScrolledRect (drawableObject.bounds);
        return result

    def CreateHitTest (self, x, y):
        """
          Set self.autoCreateDistance to some value other than zero to enable
        dragging autoCreateDistance pixels to automatically create new drawable
        objects.
          By default, drawable objects are created if you click and drag in the
        canvas anwhere there isn't a drawable object. You can restrict this location
        that drawable objects are created by overriding this routine
        """
        return True

    """
      You must implement the following functions
    """

    def ConvertDataObjectToDrawableObject (self, dataObject, x, y, move):
        """
          You must implement this routine to convert a dataobject, used in
        drag and drop into a drawable object.
        """
        assert (False)

    def CreateNewDrawableObject (self, dragRect, startDrag, endDrag):
        """
          You must implement this routine to create new drawable objects by
        dragging on the blank canvas.
        """
        assert (False)

    def DeSelectAll (self):
        """
        Mark all selected objects as not selected. Only Refresh the objects
        that change, don't call Update.
        """
        for drawableObject in self.zOrderedDrawableObjects:
            if (drawableObject.selected):
                drawableObject.selected = False
                self.RefreshScrolledRect (drawableObject.bounds)

