#   Copyright (c) 2004-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Canvas block for displaying item collections
"""

__parcel__ = "osaf.framework.blocks.calendar"

import wx

from chandlerdb.item.c import isitemref
from osaf.framework.blocks import Block, DragAndDrop, FocusEventHandlers
from application import schema
from application.dialogs import Util
from wx.lib import buttons
from i18n import ChandlerMessageFactory as _
from time import time as epochtime
from osaf.pim import EventStamp
from osaf import sharing

# temporary hack because Mac/Linux force BitmapButtons to
# have some specific borders
def GetPlatformBorder():
    if '__WXMAC__' in wx.PlatformInfo:
        return 3
    if '__WXGTK__' in wx.PlatformInfo:
        return  5
    return 0

ignore = [wx.WXK_SHIFT, wx.WXK_TAB, wx.WXK_CAPITAL, wx.WXK_SCROLL,
          wx.WXK_ESCAPE, wx.WXK_NUMLOCK, wx.WXK_PAUSE, wx.WXK_PAGEDOWN,
          wx.WXK_PAGEUP, wx.WXK_WINDOWS_LEFT, wx.WXK_WINDOWS_RIGHT,
          wx.WXK_WINDOWS_MENU, wx.WXK_HOME, wx.WXK_END]
ignore.extend([getattr(wx, 'WXK_F' + str(n)) for n in range(1,25)])

MAX_TITLE_IN_MENU = 30

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
    
    def __init__(self, bounds, itemOrEvent):
        """
        @param bounds: the bounds of the item as drawn on the canvas.
        @type bounds: wx.Rect
        @param item: the item drawn on the canvas in these bounds
        @type itemOrEvent: C{Item} or C{EventStamp}
        """
        
        # @@@ scaffolding: resize bounds is the lower 5 pixels
        self._bounds = bounds
        
        if isinstance(itemOrEvent, EventStamp):
            self.event = itemOrEvent
        else:
            self.event = EventStamp(itemOrEvent)

    @property
    def item(self):
        return self.event.itsItem

    def __repr__(self):
        return "<%s: item=%s box=%s>" % (self.__class__.__name__,
                                         self.item,
                                         self._bounds)
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
                 initialPosition,
                 resize = False):
        
        self.dragStartHandler = dragStartHandler
        self.dragHandler = dragHandler
        self.dragEndHandler = dragEndHandler
        self.dragged = False
        self.draggable = True

        # used ONLY for capture/release of the mouse

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
            self.draggable = canvasItem.CanDrag()
            if self.draggable:
                canvasItem.StartDrag(initialPosition)
        
        self._dragStarted = False
        self._dragCanceled = False
        self.resize = resize
        # when canvas items are dragged between all-day and timed, pretend
        # there's just one canvas and hide the item in the other canvas, but
        # for other drags (to the sidebar, for instance) leave the item visible
        self.hiddenWhileDraggedOut = False

    def ResetDrag(self):
        # do we need to have a handler for this?
        self.HandleDrag(self._originalPosition)

    def DragOut(self):
        self.HandleDrag(self._originalPosition)
        if self.currentDragBox is not None:
            self.draggedOutItem = self.currentDragBox.item
        
    def DragIn(self):
        self.draggedOutItem = None

    def HandleDragStart(self):
        if self._dragCanceled:
            return
        

        result = self.dragStartHandler()
        if not result:
            self._dragCanceled = True
            return
        
        self._dragStarted = True
        self.StartDragTimer()

    def StartDragTimer(self):
        self._dragTimer = wx.PyTimer(self.OnDragTimer)
        self._dragTimer.Start(100, wx.TIMER_CONTINUOUS)

    def StopDragTimer(self):
        if hasattr(self, '_dragTimer'):
            self._dragTimer.Stop()
            del self._dragTimer
                
    def OnDragTimer(self):
        if self._dragDirty:
            self.dragHandler(self.currentPosition)
            self._dragDirty = False
            
    def HandleDrag(self, unscrolledPosition):
        if self._dragCanceled:
            return
        
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
        if self._dragCanceled:
            return
        
        if self._dragStarted:
            self.StopDragTimer()
        self.dragEndHandler()

class wxCollectionCanvas(DragAndDrop.DropReceiveWidget, 
                         DragAndDrop.DraggableWidget,
                         DragAndDrop.FileOrItemClipboardHandler,
                         wx.ScrolledWindow):

    """
    Canvas used for displaying an ContentCollection

    This class handles:
      1. Mouse Events: the class sets up methods for selection, move, resize
      2. Scrolling

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

        # activeProxy is used to track changes to one recurring event without
        # having to wrap all canvas items in proxies
        self.activeProxy = None

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        self.dragState = self.draggedOutState = self._linuxHackDragState = None
        self.coercedCanvasItem = None

        self._cursorID = wx.CURSOR_DEFAULT
        
    def OnInit(self):
        # _focusWindow is used because wxPanel is much happier if it
        # has a child window that deals with focus stuff. We create an
        # invisible window and send all focus (i.e. keyboard) events
        # through it.
        self._focusWindow = wx.Window(self, -1, size=wx.Size(0,0), style=wx.WANTS_CHARS)
        self._focusWindow.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)
        self._focusWindow.Bind(wx.EVT_CHAR, self.OnChar)
        
    def SetPanelFocus(self):
        if self._focusWindow:
            self._focusWindow.SetFocus()

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
                                        unscrolledPosition, resize = True)
        
        elif hitBox.isHitResize(unscrolledPosition):
            # start resizing
            self.dragState = DragState(hitBox, self,
                                        self.OnBeginResizeItem,
                                        self.OnResizingItem,
                                        self.OnEndResizeItem,
                                        unscrolledPosition, resize = True)

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
            c = wx.CURSOR_SIZENS
        else:
            c = wx.CURSOR_DEFAULT
        # Only change the cursor if we currently have a different one.
        # This removes some cursor flicker on wxGTK for some
        # platforms.
        if c != self._cursorID:
            self.SetCursor(wx.StockCursor(c))
            self._cursorID = c
            
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
        else:
            self.WarnReadOnlyAdd(self.blockItem.contents)
            
    def _handleLeftClick(self, unscrolledPosition,
                         multipleSelection):
        """
        Handle a single left click, potentially hitting an item

        Possible client events::
            OnSelectItem()
            OnSelectNone()
        """

        hitBox = self.GetCanvasItemAt(unscrolledPosition)
        if hitBox:
            item = hitBox.item
            selection = self.blockItem.GetSelection()
            if multipleSelection:
                # need to add/remove from the selection
                
                if selection.isItemSelected(item):
                    self.OnRemoveFromSelection(item)
                    
                elif selection.isSelectionEmpty():
                    self.OnSelectItem(item)
                    
                else:
                    self.OnAddToSelection(item)
            else:
                # need to clear out the old selection, and select this
                self.OnSelectItem(item)
                
        else:
            self.OnSelectNone(unscrolledPosition)

        # create a drag state for resize dragging
        self._initiateDrag(hitBox, unscrolledPosition)

    def OnHover (self, x, y, dragResult):
        if not hasattr(self, 'lastHover'):
            self.lastHover = epochtime() - 1
        if epochtime() > self.lastHover + .05: # 20 scrolls a second
            self.lastHover = epochtime()
            self.RefreshCanvasItems(resort=False)

        unscrolledPosition = wx.Point(*self.CalcUnscrolledPosition(x, y))
        dragResult = wx.DragMove
        if self.dragState:
            if self.IsValidDragPosition(unscrolledPosition):
                self.dragState.HandleDrag(unscrolledPosition)
        else:
            # save unscrolledPosition in case an email is dragged in
            self.fileDragPosition = unscrolledPosition
            
        return dragResult

    def OnRequestDrop(self, x, y):
        """Let items be dragged and dropped from self to self."""
        return True

    def OnItemPaste(self):
        """Handle the paste of an item differently if it's being dragged."""
        # on Linux, a spurious OnLeave moves self.dragState to
        # self._linuxHackDragState, so make sure BOTH are none
        if self.dragState is None and self._linuxHackDragState is None:
            super(wxCollectionCanvas, self).OnItemPaste()
        else:
            if self.dragState is None:
                # Linux workaround
                self.dragState = self._linuxHackDragState
                self._linuxHackDragState = None
                if getattr(self, '_linuxHackCoercedCanvasItem', None):
                    self.coercedCanvasItem = self._linuxHackCoercedCanvasItem
                if getattr(self.dragState, '_linuxHackPosition', None):
                    self.dragState.HandleDrag(self.dragState._linuxHackPosition)
            self.dragState.HandleDragEnd()
            self.dragState = None

    def OnEnter(self, x, y, dragResult):
        source = self.GetDraggedFromWidget()
        if source not in (self, None):
            # On Linux, OnLeave doesn't reliably happen before OnEnter
            source.OnLeave()

        if self.draggingCoerced():
            source.draggedOutState.hiddenWhileDraggedOut = True
            source.RefreshCanvasItems(resort=False)
            self.makeCoercedCanvasItem(x, y, 
                                       source.draggedOutState.draggedOutItem)

        elif self.draggedOutState:
            self.dragState = self.draggedOutState
            self.dragState.hiddenWhileDraggedOut = False
            self.dragState.DragIn()
            self.draggedOutState = None

    def OnLeave(self):
        if self.draggingCoerced():
            source = self.GetDraggedFromWidget()
            if source.draggedOutState:
                source.draggedOutState.hiddenWhileDraggedOut = False
            source.Refresh()
            # Linux hack
            self._linuxHackDragState = self.dragState
            self._linuxHackCoercedCanvasItem = self.coercedCanvasItem
            
            self.dragState = None
            self.coercedCanvasItem = None
            
        elif self.dragState:
            # Linux gives a spurious OnLeave, so save position just in case
            self.dragState._linuxHackPosition = self.dragState.currentPosition
            self.dragState.DragOut()
            self.draggedOutState = self._linuxHackDragState = self.dragState
            self.dragState = None
            
        # make sure to redraw the canvas with the dragged item gone
        self.RefreshCanvasItems(resort=False)

    def makeCoercedCanvasItem(self, x, y, item):
        """
        When an all day item is dragged to the time canvas, or vice versa,
        create an appropriate self.coercedCanvasItem and set self.dragState
        appropriately.
        
        """        
        pass

    def draggingCoerced(self):
        """
        Return a boolean, whether an item has been dragged from another canvas.
        """
        source = self.GetDraggedFromWidget()
        return (source not in (self, None) and
                getattr(source, 'draggedOutState', None) is not None)

    def _getHiddenOrClearDraggedOut(self):
        """
        Return the item currently being dragged out if it should be hidden,
        or clear draggedOutState if the mouse isn't down.
        
        """
        if self.draggedOutState is not None:
            if wx.GetMouseState().leftDown:
                if self.draggedOutState.hiddenWhileDraggedOut:
                    return self.draggedOutState.draggedOutItem
            else:
                self.draggedOutState = None        
        return None

    def OnMouseEvent(self, event):
        """
        Handles mouse events, calls overridable methods related to:
          1. Selecting an item
          2. Dragging/moving an item
          3. Resizing an item
        """
        # On Linux, the dragState needs to be juggled between drop and
        # the paste handler while OnLeave happens, but this should be
        # None at other times
        self._linuxHackDragState = None
        
        # ignore entering and leaving events
        if (event.Entering() or event.Leaving()):
            # resize handling should probably be transitioned to using
            # wx drag and drop, like move.  For now, because CaptureMouse()
            # inexplicably fails to prevent LeftUp events from being captured by
            # windows other than the timed canvas, thus leaking PyTimers, manage
            # creating and deleting timers when entering and leaving.
            if self.dragState is not None and self.dragState.resize:
                if event.Leaving():
                    self.StopDragTimer()
                    self.dragState.StopDragTimer()
                    
                    # it would be nice to do:
                #elif event.Entering():
                    #self.StartDragTimer()
                    #self.dragState.StartDragTimer()
                    
                    # Unfortunately, to restart the timers, we need a reliable
                    # way of determining whether the drag ever stopped.  Since
                    # CaptureMouse doesn't seem to work reliably, this is hard
                    # to accomplish.  It seems preferable in the short term to
                    # avoid crashes by simply aborting resize when leaving.
                    
                    self.dragState.ResetDrag()
                    self.dragState = None
                    self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
                    self._cursorID = wx.CURSOR_DEFAULT
                    self.RefreshCanvasItems(resort=False)            
                    
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
            if not self.dragState.draggable:
                self.WarnReadOnlyTime([self.dragState.currentDragBox.item])
                event.Skip()
                return
            self.dragState.dragged = True
            if self.dragState.resize:
                if self.IsValidDragPosition(unscrolledPosition):
                    self.dragState.HandleDrag(unscrolledPosition)
                else:
                    # We've interrupted the resize within the calendar,
                    # so reset the drag state, putting the event where it started
                    self.dragState.ResetDrag()
                    self.dragState.HandleDragEnd()
                    self.dragState = None
                    self.DoDragAndDrop(copyOnly=True)
            else:
                self.DoDragAndDrop(copyOnly=True)


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
        else:
            # Pass right clicks, etc onto wx, which can generate
            # EVT_CONTEXT_MENU as appropriate.
            event.Skip()

    def OnContextMenu(self, event):
    
        # Event's position is in screen co-ordinates, so convert it
        position = self.ScreenToClient(event.GetPosition())

        # When doing calculations w.r.t. item positions on the
        # canvas, we want to use the unscrolled position. The
        # only place we use position is in the call to PopupMenu.
        unscrolledPosition = self.CalcUnscrolledPosition(position)

        data = {'collection' : self.blockItem.contentsCollection.displayName}

        canvasItem = self.GetCanvasItemAt(unscrolledPosition)
        
        menu = wx.Menu()

        if not canvasItem:
            addTxt = _(u"Create new item in '%(collection)s'") 
            menuItem = wx.MenuItem(menu, wx.NewId(), addTxt % data)
            menu.AppendItem(menuItem)
            menuItem.Enable(self.blockItem.CanAdd())
            eventcallback = lambda event: self.OnCreateItem(unscrolledPosition)
            menu.Bind(wx.EVT_MENU, eventcallback, menuItem)

            self.OnSelectNone(unscrolledPosition)        
        else:
            item = canvasItem.item
            selection = self.blockItem.GetSelection()
            self.OnSelectItem(item)
            title = item.displayName
            
            if len(title) > MAX_TITLE_IN_MENU:
                ellipsis = _(u"...")
                trim = {'ellipsis' : ellipsis, 
                        'title' : title[0 : MAX_TITLE_IN_MENU - len(ellipsis)]}
                title = _(u"%(title)s%(ellipsis)s") % trim
            data['title'] = title
            
            removeTxt = _(u"Remove from '%(collection)s'") 
            deleteTxt = _(u"Move to Trash") 
            
            menuItem = wx.MenuItem(menu, wx.NewId(), removeTxt % data)
            menu.AppendItem(menuItem)
            menuItem.Enable(self.blockItem.CanRemove())
            menu.Bind(wx.EVT_MENU, self.blockItem.onRemoveEvent, menuItem)

            menuItem = wx.MenuItem(menu, wx.NewId(), deleteTxt % data)
            menu.AppendItem(menuItem)
            menuItem.Enable(self.blockItem.CanDelete())
            menu.Bind(wx.EVT_MENU, self.blockItem.onDeleteEvent, menuItem)
            
        self.PopupMenu(menu, position)

    def SelectedCanvasItem(self):
        """
        Use the selection to find the currently selected canvas item,
        returning None if there isn't any
        """
        selection = self.SelectedItems()
        # try our best to avoid iterating the entire selection
        try:
            selectedItem = selection.next()
        except StopIteration:
            return None                 # no items selected, that's fine

        try:
            selection.next()
        except StopIteration:
            # great! exactly one item in the iteration

            # find the associated canvasItem. Would be nice if we
            # had dictionary mapping item->canvasItem, but this is
            # the first time we've needed it!
            selectedCanvasItems = [canvasItem
                                  for canvasItem in self.canvasItemList
                                  if canvasItem.item == selectedItem]

            # it's possible selecteCanvasItems will be empty if canvasItemList
            # was out of date.  That's OK, go ahead and return None in that case
            if len(selectedCanvasItems) == 1:
                return selectedCanvasItems[0]


        return None                     # oops, more than one item selected

    def EditCurrentItem(self, keyPressed = False):
        currentCanvasItem = self.SelectedCanvasItem()
        if currentCanvasItem is not None:
            self.OnEditItem(currentCanvasItem)
            
    def GetCanvasItems(self, *items):
        """
        Maps one or more items to their respective canvas items,
        returning a generator

        this isn't very efficient because its really only used for
        tests (if we really cared, we would just use a dict which
        maintains the mapping)
        """

        for item in items:
            for canvasItem in self.canvasItemList:
                if item == canvasItem.item:
                    yield canvasItem

    def SaveCharTyped(self, event):
        pass

    def OnKeyPressed(self, event):
        keyCode = event.GetKeyCode()

        # dispatch arrow keys, etc
        
        # (actually it would be really nice to just intercept
        # NavigationEvents somehow, but they aren't really documented
        navigation_keys = ("UP", "DOWN", "LEFT", "RIGHT")
        for key in navigation_keys:
            if (keyCode == getattr(wx, 'WXK_' + key) or
                keyCode == getattr(wx, 'WXK_NUMPAD_' + key)):
                self.OnNavigateItem(key)
                return
            
        # fix ugly bug 2749 - for some reason "BACK" isn't propagating
        # up to the menu when the _focusWindow has focus
        
        if ('__WXMAC__' in wx.PlatformInfo and 
            (keyCode in (wx.WXK_BACK, wx.WXK_DELETE))):
            # Fix bug 6126: make sure we can delete before calling
            # onDeleteEvent (and eat the key event either way).
            if self.blockItem.CanDelete():
                self.blockItem.onDeleteEvent(event)
            return # eat the key event.

        # didn't handle it so propagate the key event upward
        event.Skip()

    def OnChar(self, event):
        """Handle character after system translation."""
        keyCode = event.GetKeyCode()
        
        # is there a good way to find out if the key press was a normal
        # (for the current locale) key?
        
        if not (keyCode in ignore or event.AltDown() or event.ControlDown() or
                event.MetaDown()):
            
            # normal key presses should cause the item to start being edited
            self.EditCurrentItem(True)
            if keyCode not in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                # don't eat non-enter keypresses 
                self.SaveCharTyped(event)

    def ScrollIntoView(self, unscrolledPosition, buffer=0):
        clientSize = self.GetClientSize()
        
        # scrolling up
        if unscrolledPosition.y < buffer:
            # rectangle goes off the top - scroll up
            self.ScaledScroll(0, unscrolledPosition.y - buffer)
            
        # scrolling down
        elif unscrolledPosition.y > clientSize.y - buffer:
            # rectangle goes off the bottom - scroll down
            dy = unscrolledPosition.y - clientSize.y + buffer
            self.ScaledScroll(0, dy)

    def IsValidDragPosition(self, unscrolledPosition):
        # by default, any position is valid, even if it goes off the canvas
        return True
        
    def GrabFocusHack(self):
        pass

    def StartDragTimer(self):
        pass
    
    def StopDragTimer(self):
        pass

    def OnNavigateItem(self, direction):
        """
        Navigate from the currently selected item(s) in the direction given.

        The directions come from wx and currently include 'UP','DOWN',
        'LEFT', and 'RIGHT'
        """
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
        return True

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
        return True

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

        dc.BeginDrawing()
        self.DrawBackground(dc)
        self.DrawCells(dc)
        dc.EndDrawing()
        
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
        selection = self.blockItem.GetSelection()
        if item:
            selection.setSelectionToItem(item)
        else:
            selection.clearSelection()
        self.blockItem.postSelectItemsBroadcast()
        self.Refresh()

    def OnAddToSelection(self, item):
        blockItem = self.blockItem
        
        selection = blockItem.GetSelection()
        selection.selectItem(item)
        
        blockItem.postSelectItemsBroadcast()
        blockItem.synchronizeWidget()

    def OnRemoveFromSelection(self, item):
        blockItem = self.blockItem
        
        selection = blockItem.GetSelection()
        selection.unselectItem(item)
        
        #blockItem.selection.remove(item)
        blockItem.postSelectItemsBroadcast()
        blockItem.synchronizeWidget()
        
    def OnSelectNone(self, unscrolledPosition):
        """
        Called when the user clicks on an area that isn't an item
        """
        self.OnSelectItem(None)
    
    def OnBeginDragNone(self):
        return True
        
    def OnDraggingNone(self, unscrolledPosition):
        pass
        
    def OnEndDragNone(self):
        pass

    # Methods for Drag and Drop and Cut and Paste
    def DeleteSelection(self, *args, **kwargs):
        self.blockItem.DeleteSelection(*args, **kwargs)

    def WarnReadOnlyAdd(self, collection):
        Util.ok(self, _(u'Warning'), _(u'This collection is read-only. You cannot add items to read-only collections'))
        

class CollectionBlock(FocusEventHandlers, Block.RectangularChild):
    """
    Parent block class for a generic collection display. Handles selection,
    hit testing, notifications, and some event handling
    """

    def __init__(self, *arguments, **keywords):
        super(CollectionBlock, self).__init__(*arguments, **keywords)

    # Event handling
    
    def onSetContentsEvent (self, event):
        """
        Here would be a good place to make sure that items selected in
        the old contents are also selected in the new contents.

        """
        contents = event.arguments['item']
        # collectionList.first() is the currently selected collection in
        # the sidebar
        contentsCollection = contents.collectionList.first()
        self.setContentsOnBlock(contents, contentsCollection)

        # bug 5613, when a new collection is selected, items in overlaid
        # collections should be unselected
        selection = self.GetSelection()
        # Bug 5817, the iterable returned by iterSelection will complain if an
        # item is removed, so create a (seemingly useless) list before iterating
        for item in list(selection.iterSelection()):
            if (EventStamp(item).getMaster().itsItem not in
                self.contentsCollection):
                selection.unselectItem(item)
        
        # Posting select items event will display the correct item in the detail view.
        self.postSelectItemsBroadcast()
            
        self.synchronizeWidget()


    def onSelectItemsEvent(self, event):
        """
        XXX Temporarily moved this out to CalendarControl because it
        was really painful to have all canvases recieve the same
        event, and then all update their self.contents. So now there
        is just one instance that handles this event
        
        Sets the block selection

        NB this allows a selection on an item not in the current range.
        """
        pass
    
    def postSelectItemsBroadcast(self):
        """
        Convenience method for posting a selection changed event.
        """
        selection = self.GetSelection()
        self.postEventByName('SelectItemsBroadcast',
                             {'items': list(selection.iterSelection()),
                              'collection': self.contentsCollection})

    def SelectCollectionInSidebar(self, collection):
        self.postEventByName('RequestSelectSidebarItem', {'item':collection})

    def onSelectAllEvent(self, event):
        pass
#         self.selection = list(self.contents)
#         self.selectAllMode = True
#         self.postSelectItemsBroadcast()

    def onSelectAllEventUpdateUI(self, event):
        event.arguments['Enable'] =  self.contents is not None and len(self.contents) > 0

    def DeleteSelection(self, cutting=False, *args, **kwargs):
        selection = self.GetSelection()
        for item in selection.iterSelection():
            assert not isitemref(item)
            item.removeFromCollection(self.contentsCollection, cutting)
        self.ClearSelection()

    def ClearSelection(self):
        selection = self.GetSelection()
        selection.clearSelection()
        self.postSelectItemsBroadcast()

    def CanAdd(self):
        return not sharing.isReadOnly(self.contentsCollection)

    def GetSelection():
        # by default, selection is managed by the collection itself
        return self.contents
