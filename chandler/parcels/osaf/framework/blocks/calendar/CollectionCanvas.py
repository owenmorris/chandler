"""
Canvas block for displaying item collections
"""

__copyright__ = "Copyright (c) 2004-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.calendar"

import wx

from osaf.framework.blocks import DragAndDrop
from osaf.framework.blocks import Block
from osaf.pim import AbstractCollection
from application import schema
from wx.lib import buttons
from i18n import OSAFMessageFactory as _

# temporary hack because Mac/Linux force BitmapButtons to
# have some specific borders
def GetPlatformBorder():
    if '__WXMAC__' in wx.PlatformInfo:
        return 3
    if '__WXGTK__' in wx.PlatformInfo:
        return  5
    return 0
    
# @@@ These buttons could become a more general utility

class CanvasBitmapButton(wx.lib.buttons.GenBitmapButton):
    """
    Flat bitmap button, no border.

    Currently, the wx.BitmapButton does not work well on MacOSX:
    wxWidgets doesn't implement a button with no border.
    Ideally, we would use a "proper" bitmap button that
    actually generated a accurate masked area,
    """

    def __init__(self, parent, name):
        """

        @param parent: like all controls, requires a parent window
        @type parent: wx.Window
        @param name: unicode name of an image file
        @type name: unicode
        """

        self.forcedBorder = GetPlatformBorder()

        app = wx.GetApp()
        bitmap = app.GetImage (name + ".png")
        super(CanvasBitmapButton, self).__init__(parent, -1,
                                                 bitmap, style=wx.NO_BORDER)
        # NB: forcing a white background (as needed by GenBitmapButton)
        # to match the Calendar header background
        pressedBitmap = app.GetImage(name + "MouseDown.png")
        self.SetBitmapSelected(pressedBitmap)
        self.SetBackgroundColour("white")
        self.UpdateSize()

    def UpdateSize(self):
        """
        Sizes the button to just fit the bitmap
        """
        #@@@ This copies CanvasTextButton.UpdateSize - to be fixed after 0.5
        bitmap = self.GetBitmapLabel()
        width = bitmap.GetWidth() + self.forcedBorder*2
        height = bitmap.GetHeight() + self.forcedBorder*2
        self.SetMinSize(wx.Size(width, height))

class CanvasItem(object):
    """
    Represents a list of items currently on the canvas for hit testing.
    Not responsible for drawing the object on the canvas. This class
    stores the bounds of the item on the canvas, subclasses can be more
    sophisticated.
    """
    
    def __init__(self, bounds, item):
        """
        @param bounds: the bounds of the item as drawn on the canvas.
        @type bounds: wx.Rect
        @param item: the item drawn on the canvas in these bounds
        @type item: Item
        """

        # @@@ scaffolding: resize bounds is the lower 5 pixels
        self._bounds = bounds
        self._item = item

    def isHit(self, point):
        """
        Hit testing (used for selection and moving items).

        @param point: point in unscrolled coordinates
        @type point: wx.Point
        @return: True if the point hit the item (includes resize region)
        @rtype: Boolean
        """
        return self._bounds.Inside(point)

    def isHitResize(self, point):
        """
        Hit testing of a resize region.

        Subclasses can define to turn on resizing behavior.
        
        @param point: point in unscrolled coordinates
        @type point: wx.Point
        @return: True if the point hit the resize region
        @rtype: Boolean
        """
        return False

    def GetItem(self):
        """
        Once we have a hit, give access to the item
        for selection, move, resize, etc.
        
        @return: the item associated with this region on the canvas.
        @rtype: Item
        """
        return self._item

    def GetDragOrigin(self):
        """
        This is just a stable coordinate that we can use so that when dragging
        items around, for example you can use this to know consistently where 
        the mouse started relative to this origin
        """
        return self._bounds.GetPosition()

    def StartDrag(self, position):
        """
        notify the canvasitem that is now part of a drag
        """
        pass

class DragState(object):
    """
    Encapsulates all information necessary to manage a drag
    Takes callbacks to notify clients about start/drag/end events

    All positions are UNSCROLLED - meaning relative to the virtual space of
    a scrolled window, not the actual coordinates on screen
    """

    def __init__(self, canvasItem, window,
                 dragStartHandler,
                 dragHandler,
                 dragEndHandler,
                 initialPosition):
        
        self.dragStartHandler = dragStartHandler
        self.dragHandler = dragHandler
        self.dragEndHandler = dragEndHandler

        # used ONLY for capture/release of the mouse
        self._window = window

        # current position of the dragbox
        # (Why can't we use currentDragBox._bounds or something?)
        self.currentPosition = \
            self._originalPosition = initialPosition

        # the current canvasItem being dragged
        # note that currentDragBox gets constantly reset as the drag happens
        self.originalDragBox = \
            self.currentDragBox = canvasItem

        # the offset of the mouse from the upper left corner of
        # the canvasItem
        if canvasItem:
            self.dragOffset = initialPosition - canvasItem.GetDragOrigin()
            # allow the originalDragBox to store state from the initial drag
            canvasItem.StartDrag(initialPosition)
        
        self._dragStarted = False

    def ResetDrag(self):
        # do we need to have a handler for this?
        self.HandleDrag(self._originalPosition)
        
    def HandleDragStart(self):
        self._window.CaptureMouse()
        self.dragStartHandler()
        self._dragStarted = True
        self._dragTimer = wx.PyTimer(self.OnDragTimer)
        self._dragTimer.Start(100, wx.TIMER_CONTINUOUS)

    def OnDragTimer(self):
        if self._dragDirty:
            self.dragHandler(self.currentPosition)
            self._dragDirty = False
            
    def HandleDrag(self, unscrolledPosition):
        if not self._dragStarted:
            # calculate the absolute drag delta
            dx, dy = \
                [abs(d) for d in unscrolledPosition - self._originalPosition]

            # Only initiate the drag if we move at least 5 pixels
            if (dx > 5 or dy > 5):
                self.HandleDragStart()
            else:
                return
            
        self.currentPosition = unscrolledPosition
        self._dragDirty = True

    def HandleDragEnd(self):
        if self._dragStarted:
            self._dragTimer.Stop()
            del self._dragTimer
            self.dragEndHandler()
            self._window.ReleaseMouse()

class wxCollectionCanvas(DragAndDrop.DropReceiveWidget, 
                         DragAndDrop.DraggableWidget,
                         DragAndDrop.ItemClipboardHandler,
                         wx.ScrolledWindow):

    """
    Canvas used for displaying an AbstractCollection

    This class handles:
      1. Mouse Events: the class sets up methods for selection, move, resize
      2. Scrolling
      3. Double buffered painting: the class sets up methods for drawing

    Subclasses need to handle (by overriding appropriate methods):
      1. Background drawing
      2. Drawing items
      3. Creating regions for hit testing
      4. Resizing items (changing state, drawing the altered item)
      5. Moving/dragging items (changing state, drawing the altered item)

    This class assumes an associated blockItem for some default behavior,
    although subclasses can alter this by overriding the appropriate methods.

    This class currently provides two common fonts for subclasses to use
    in drawing as a convenience, subclasses are free to create their own fonts.

    @ivar bigFont: font size and face of the default big font
    @type bigFont: wx.Font
    @ivar bigFontColor: color of the default big font
    @type bigFontColor: wx.Colour
    @ivar smallFont: font size and face of the default small font
    @type smallFont: wx.Font
    @ivar smallFontColor: color of the default small font
    @type smallFontColor: wx.Colour

    @ivar dragState: holds details about the drag in progress, if any
    @type dragState: DragState
    """

    def __init__(self, *arguments, **keywords):
        """
        Same arguments as wx.ScrolledWindow
        Constructor sets up ivars, event handlers, etc.
        """
        super(wxCollectionCanvas, self).__init__(*arguments, **keywords)

        # canvasItemList is sorted in bottom-up order (in case some events
        #   overlap with each other
        # when drawing, iterate forward to draw bottom items first
        # when handling events, iterate with reversed() to send the events
        #   to the topmose items
        self.canvasItemList = []

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)

        self.dragState = None
        
    def OnInit(self):
        # _focusWindow is used because wxPanel is much happier if it
        # has a child window that deals with focus stuff. We create an
        # invisible window and send all focus (i.e. keyboard) events
        # through it.
        self._focusWindow = wx.Window(self, -1, size=wx.Size(0,0))
        self._focusWindow.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

    def SetPanelFocus(self):
        self._focusWindow.SetFocus()

    def OnKeyUp(self, event):
        if (event.m_keyCode in (wx.WXK_DELETE, wx.WXK_BACK) and
            self.blockItem.CanRemove()):
            self.blockItem.onRemoveEvent(event)
        else:
            event.Skip()

    def DrawCenteredText(self, dc, text, rect):
        textExtent = dc.GetTextExtent(text)
        middleRect = rect.width / 2
        middleText = textExtent[0] / 2
        dc.DrawText(text, rect.x + middleRect - middleText, rect.y)

    def GetCanvasItemAt(self, unscrolledPosition):
        for canvasItem in reversed(self.canvasItemList):
            if canvasItem.isHit(unscrolledPosition):
                return canvasItem
        return None

    def _initiateDrag(self, hitBox, unscrolledPosition):
        """
        Store state to get ready for a drag to start
        """
        # remember drag start whether or not we hit something
        if not hitBox:
            # user just dragging across the canvas
            self.dragState = DragState(hitBox, self,
                                        self.OnBeginDragNone,
                                        self.OnDraggingNone,
                                        self.OnEndDragNone,
                                        unscrolledPosition)
        
        elif hitBox.isHitResize(unscrolledPosition): 
            # start resizing
            self.dragState = DragState(hitBox, self,
                                        self.OnBeginResizeItem,
                                        self.OnResizingItem,
                                        self.OnEndResizeItem,
                                        unscrolledPosition)

        else: 
            # start dragging
            self.dragState = DragState(hitBox, self,
                                        self.OnBeginDragItem,
                                        self.OnDraggingItem,
                                        self.OnEndDragItem,
                                        unscrolledPosition)

    def _updateCursor(self, unscrolledPosition):
        """
        Show the resize cursor if we're over a resize area,
        otherwise restore the cursor
        
        This is potentially expensive, since we're iterating all the canvasItems
        """
        hitBox = self.GetCanvasItemAt(unscrolledPosition)
        if hitBox and hitBox.isHitResize(unscrolledPosition):
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
        else:
            self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            
    def _handleDoubleClick(self, unscrolledPosition):
        """
        Handle a double click on the canvas somewhere. Checks to see
        if we hit an item, and if not, creates one

        Possible client events::
            OnEditItem()
            OnCreateItem()
        """
        hitBox = self.GetCanvasItemAt(unscrolledPosition)
        if hitBox:
            self.OnEditItem(hitBox)
        elif self.blockItem.CanAdd():
            self.OnCreateItem(unscrolledPosition)
            
    def _handleLeftClick(self, unscrolledPosition,
                         multipleSelection):
        """
        Handle a single left click, potentially hitting an item

        Possible client events::
            OnSelectItem()
            OnSelectNone()
        """

        # at the moment, any kind of left-click will change
        # the selection in some way, taking us out of "select-all" mode
        self.blockItem.selectAllMode = False
        
        hitBox = self.GetCanvasItemAt(unscrolledPosition)
        if hitBox:
            item = hitBox.GetItem()
            if multipleSelection:
                # need to add/remove from the selection

                # XXX This it the first time wxCollectionCanvas
                # knows about selection, is this ok?
                selection = self.blockItem.selection
                
                if item in selection:
                    self.OnRemoveFromSelection(item)
                else:
                    if len(selection) == 0:
                        self.OnSelectItem(item)
                    else:
                        self.OnAddToSelection(item)
            else:
                # need to clear out the old selection, and select this
                self.OnSelectItem(item)
                
        else:
            self.OnSelectNone(unscrolledPosition)

        # create a drag state just in case
        self._initiateDrag(hitBox, unscrolledPosition)


    def OnMouseEvent(self, event):
        """
        Handles mouse events, calls overridable methods related to:
          1. Selecting an item
          2. Dragging/moving an item
          3. Resizing an item
        """

        # ignore entering and leaving events
        if (event.Entering() or event.Leaving()):
            event.Skip()
            return

        # @@@ wxPanels don't ever get the focus if they have a child window.
        # This causes us problems as we are using controls as in-place editors.
        # The current hack is to notice when the panel might want to grab
        # focus from the control, and hide the control. Entertaining better
        # solutions...
        if event.ButtonDown():
            self.GrabFocusHack()

        position = event.GetPosition()
        unscrolledPosition = self.CalcUnscrolledPosition(position)

        if event.Moving():
            self._updateCursor(unscrolledPosition)
        
        # checks if the event iself is from dragging the mouse
        elif self.dragState and event.Dragging():
            if self.IsValidDragPosition(unscrolledPosition):
                self.dragState.HandleDrag(unscrolledPosition)
            else:
                self.dragState.ResetDrag()
                self.DoDragAndDrop(copyOnly=True)
                self.dragState.HandleDragEnd()
                self.dragState = None

        elif event.LeftDClick():
            # cancel/stop any drag in progress
            if self.dragState:
                self.dragState.HandleDragEnd()
                self.dragState = None
            self._handleDoubleClick(unscrolledPosition)

        elif event.LeftDown():
            self._handleLeftClick(unscrolledPosition,
                                  event.ControlDown() or event.CmdDown())
            
        elif event.LeftUp():
            # we need to make sure we have a  dragState, because we
            # sometimes get extra LeftUp's if the user does a
            # double-click and drag
            if self.dragState:
                
                # We want to set focus only if a drag isn't in progress
                if not self.dragState._dragStarted:
                    self.SetPanelFocus()
                    
                self.dragState.HandleDragEnd()
                self.dragState = None

    def ScrollIntoView(self, unscrolledPosition):
        clientSize = self.GetClientSize()
        
        # scrolling up
        if unscrolledPosition.y < 0:
            # rectangle goes off the top - scroll up
            self.ScaledScroll(0, unscrolledPosition.y)
            
        # scrolling down
        elif unscrolledPosition.y > clientSize.y:
            # rectangle goes off the bottom - scroll down
            dy = unscrolledPosition.y - clientSize.y
            self.ScaledScroll(0, dy)

    def IsValidDragPosition(self, unscrolledPosition):
        # by default, any position is valid, even if it goes off the canvas
        return True
        
    def GrabFocusHack(self):
        pass

    def OnCreateItem(self, position):
        """
        Creates a new item on the canvas.

        Subclasses can define to create a new item on the canvas.

        If the new item is created during a drag, then this method needs
        to return a CanvasItem for the new item, for smooth dragging.
        (As soon as the new item is created, it becomes a resize operation.)

        @param position: unscrolled coordinates, location of the new item
        @type position: wx.Point
        """
        return None

    def OnBeginResizeItem(self):
        """
        Called when an item resize begins.
        
        Subclasses can define to handle resizing
        """
        pass

    def OnEndResizeItem(self):
        """
        Called when an item resize ends.
        
        Subclasses can define to handle resizing
        """
        pass

    def OnResizingItem(self, position):
        """
        Called when the mouse moves during a resize.
        
        Subclasses can define to handle resizing
        """
        pass

    def OnBeginDragItem(self):
        """
        Called when a drag/move begins.
        
        Subclasses can define to handle dragging
        """
        pass

    def OnEndDragItem(self):
        """
        Called when a drag/move ends.
        
        Subclasses can define to handle dragging
        """
        pass

    def OnDraggingItem(self, position):
        """
        Called when the mouse moves during a drag.
        
        Subclasses can define to handle dragging
        """
        pass

    def OnEditItem(self, hitBox):
        pass
            
    # Painting and drawing

    def OnEraseBackground(self, event):
        """
        Do nothing on EraseBackground events, to avoid flicker.
        """
        pass

    def OnPaint(self, event):
        dc = wx.PaintDC(self)

        # Sometimes we get empty regions to paint,
        # like when you mouseover the scrollbar
        region = self.GetUpdateRegion()
        if region.IsEmpty():
            return

        # a temporary performance boost for bug 4010, because
        # bug 4213 is causing the all day area to get extra damage
        # when bug 4213 is fixed, this code should be removed!
        regionBox = region.GetBox()
        if regionBox.y == 0 and regionBox.height == 1:
            return

        self.PrepareDC(dc)
        self.DrawCanvas(dc)
        
    def DrawCanvas(self, dc):

       if True:
           # if non-double buffered drawing is desired
           # esp. if top window is already composited
           dc.BeginDrawing()
           self.DrawBackground(dc)
           self.DrawCells(dc)
           dc.EndDrawing()
       else:
           # if double buffered drawing is desired
           # Find update rect in scrolled coordinates
           updateRect = self.GetUpdateRegion().GetBox()
           point = self.CalcUnscrolledPosition((updateRect.GetLeft(), updateRect.GetTop()))
           wBuffer = updateRect.GetWidth()
           hBuffer = updateRect.GetHeight()

           # Create offscreen buffer
           memoryDC = wx.MemoryDC()
           buffer = wx.EmptyBitmap(wBuffer, hBuffer)
           memoryDC.SelectObject(buffer)
           memoryDC.SetDeviceOrigin(-point.x, -point.y)

           memoryDC.BeginDrawing()
           self.DrawBackground(memoryDC)
           self.DrawCells(memoryDC)
           memoryDC.EndDrawing()

           dc.Blit(point.x, point.y,
                   wBuffer, hBuffer,
                   memoryDC,
                   point.x, point.y)

    def PrintCanvas(self, dc):
        dc.BeginDrawing()
        self.DrawBackground(dc)
        self.DrawCells(dc)
        dc.EndDrawing()

    def DrawCells(self, dc):
        """
        Subclasses should define to draw the canvas cells
        """
        pass

    def DrawBackground(self, dc):
        """
        Subclasses should define to draw the canvas background
        """
        pass

    def ScaledScroll(self, dx, dy):
        """
        Subclasses should scroll appropriately if they have
        changed the scroll rate with SetScrollRate
        buffer is -1, 0, or 1, depending if you want buffer space
        above, no buffer space, or buffer space below the area being
        made visible
        """
        (scrollX, scrollY) = self.CalcUnscrolledPosition(0,0)
        
        scrollX += dx
        scrollY += dy
        
        self.Scroll(scrollX, scrollY)
 
    # selection

    def OnSelectItem(self, item):
        """
        Called when an item is hit, to select the item.

        Subclasses can override to handle item selection.
        """
        if item:
            self.blockItem.selection = [item]
        else:
            self.blockItem.selection = []
        self.blockItem.postSelectItemsBroadcast()
        self.Refresh()

    def OnAddToSelection(self, item):
        self.blockItem.selection.append(item)
        self.blockItem.postSelectItemsBroadcast()
        self.blockItem.synchronizeWidget()

    def OnRemoveFromSelection(self, item):
        blockItem = self.blockItem
        blockItem.selection.remove(item)
        blockItem.postSelectItemsBroadcast()
        blockItem.synchronizeWidget()
        
    def OnSelectNone(self, unscrolledPosition):
        """
        Called when the user clicks on an area that isn't an item
        """
        self.OnSelectItem(None)
    
    def OnBeginDragNone(self):
        pass
        
    def OnDraggingNone(self, unscrolledPosition):
        pass
        
    def OnEndDragNone(self):
        pass

    # Methods for Drag and Drop and Cut and Paste
    def DeleteSelection(self):
        self.blockItem.DeleteSelection()
        

class CollectionBlock(Block.RectangularChild):
    """
    Parent block class for a generic collection display. Handles selection,
    hit testing, notifications, and some event handling
    """

    # working under the assumption that selection will never be None,
    # and will always exist on this block, if only as an empty list
    selection = schema.Sequence(schema.Item,
                                doc = "List of currently selected items",
                                initialValue = [])

    selectAllMode = schema.One(schema.Boolean,
                               doc = "True if we're selecting all events. "
                               "This allows the UI to make recurring events "
                               "look like they're selected even if they "
                               "don't appear in self.selection",
                               initialValue=False)
    
    def __init__(self, *arguments, **keywords):
        super(CollectionBlock, self).__init__(*arguments, **keywords)
        self.selection = []

    # Event handling
    
    def onSetContentsEvent (self, event):
        self.setContentsOnBlock (event.arguments ['item'])
        """
        Clear the selection each time we view a new contents until we get
        a selection added to the contents item -- DJA
        """
        for item in self.selection:
            if item not in self.contents:
                selection.remove(item)
        self.synchronizeWidget()
        
        self.postSelectItemsBroadcast()


    def onSelectItemsEvent(self, event):
        """
        Sets the block selection

        NB this allows a selection on an item not in the current range.
        """
        self.selection = event.arguments['items']
        self.selectAllMode = event.arguments.get('selectAll', False)

        
    def postSelectItemsBroadcast(self):
        """
        Convenience method for posting a selection changed event.
        """
        self.postEventByName('SelectItemsBroadcast',
                             {'items': self.selection,
                              'selectAll': self.selectAllMode})

    def SelectCollectionInSidebar(self, collection):
        self.postEventByName('RequestSelectSidebarItem', {'item':collection})

    def onDeleteEvent(self, event):
        trash = schema.ns('osaf.app', self).TrashCollection
        for item in self.selection:
            item.addToCollection(trash)
        self.ClearSelection()
        
    def onRemoveEvent(self, event):
        self.DeleteSelection()

    def onSelectAllEvent(self, event):
        self.selection = list(self.contents)
        self.selectAllMode = True
        self.postSelectItemsBroadcast()

    def onSelectAllEventUpdateUI(self, event):
        return len(self.contents) > 0

    def DeleteSelection(self):
        for item in self.selection:
            item.removeFromCollection(self.contents.collectionList[0])
        self.ClearSelection()

    def ClearSelection(self):
        self.selection = []
        self.postSelectItemsBroadcast()

    def CanAdd(self):
        return not self.contents.collectionList[0].isReadOnly()

    def CanRemove(self):
        return (len(self.selection) > 0 and
                not self.contents.collectionList[0].isReadOnly())

    def onRemoveEventUpdateUI(self, event):
        event.arguments['Enable'] = self.CanRemove()
        event.arguments['Text'] = _(u"Delete from '%(collectionName)s'") % {'collectionName': self.contents.collectionList[0].displayName}

    def onDeleteEventUpdateUI(self, event):
        event.arguments['Enable'] = self.CanRemove()

