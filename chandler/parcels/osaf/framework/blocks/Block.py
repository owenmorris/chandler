__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from chandlerdb.util.uuid import UUID
import wx
import logging
import hotshot

logger = logging.getLogger('cpia')
logger.setLevel(logging.INFO)

class Block(Item):
    # @@@BJS: Should we show borders for debugging?
    showBorders = False
    
    def post (self, event, arguments):
        """
          Events that are posted by the block pass along the block
        that sent it.
        """
        try:
            try:
                stackedArguments = event.arguments
            except AttributeError:
                pass
            arguments ['sender'] = self
            event.arguments = arguments
            self.dispatchEvent (event)
        finally:
            try:
                event.arguments = stackedArguments
            except UnboundLocalError:
                delattr (event, 'arguments')

    def postEventByName (self, eventName, args):
        assert self.eventNameToItemUUID.has_key (eventName), "Event name " + eventName + " not found"
        list = self.eventNameToItemUUID [eventName]
        self.post (self.find (list [0]), args)

    eventNameToItemUUID = {}           # A dictionary mapping event names to event UUIDS
    blockNameToItemUUID = {}           # A dictionary mapping rendered block names to block UUIDS

    def findBlockByName (theClass, name):
        assert theClass.blockNameToItemUUID.has_key (name), "Block name " + name + " not found"
        list = theClass.blockNameToItemUUID [name]
        return wx.GetApp().UIRepositoryView.find (list[0])
    findBlockByName = classmethod (findBlockByName)

    def addToNameToItemUUIDDictionary (theClass, list, dictionary):
        for item in list:
            try:
                name = item.blockName
            except AttributeError:
                pass
            else:
                try:
                    list = dictionary [name]
                except KeyError:
                    dictionary [name] = [item.itsUUID, 1]
                else:
                    list [1] = list [1] + 1 #increment the reference count
    addToNameToItemUUIDDictionary = classmethod (addToNameToItemUUIDDictionary)

    def removeFromNameToItemUUIDDictionary (theClass, list, dictionary):
        for item in list:
            try:
                name = item.blockName
            except AttributeError:
                pass
            else:
                list = dictionary [name]
                if list [0] == item.itsUUID:
                    list [1] = list [1] - 1 #decrement the reference count
                    if list [1] == 0:
                        del dictionary [name]
    removeFromNameToItemUUIDDictionary = classmethod (removeFromNameToItemUUIDDictionary)

    def render (self):
        try:
            instantiateWidgetMethod = getattr (type (self), "instantiateWidget")
        except AttributeError:
            pass
        else:
            oldIgnoreSynchronizeWidget = wx.GetApp().ignoreSynchronizeWidget
            wx.GetApp().ignoreSynchronizeWidget = True
            try:
                widget = instantiateWidgetMethod (self)
            finally:
                wx.GetApp().ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget
            """
              Store a non persistent pointer to the widget in the block. Store a pointer to
            the block in the widget. Undo all this when the widget is destroyed.
            """

            if widget:
                wx.GetApp().needsUpdateUI = True
                assert self.itsView.isRefCounted(), "repository must be opened with refcounted=True"
                self.widget = widget
                widget.blockItem = self
                """
                  After the blocks are wired up, call OnInit if it exists.
                """
                try:
                    method = getattr (type (widget), "OnInit")
                except AttributeError:
                    pass
                else:
                    method (widget)
                """
                  For those blocks with contents, we need to subscribe to notice changes
                to items in the contents.
                """
                try:
                    contents = self.contents
                except AttributeError:
                    pass
                else:
                    try:
                        subscribeMethod = getattr (type (contents), "subscribe")
                    except AttributeError:
                        pass
                    else:
                        subscribeMethod (contents, self, "onCollectionChanged")
                """
                  Add events to name lookup dictionary.
                """
                try:
                    eventsForNamedDispatch = self.eventsForNamedDispatch
                except AttributeError:
                    pass
                else:
                    self.addToNameToItemUUIDDictionary (eventsForNamedDispatch,
                                                        self.eventNameToItemUUID)
                self.addToNameToItemUUIDDictionary ([self],
                                                    self.blockNameToItemUUID)
                """
                  Keep list of blocks that are have event boundarys in the global list views.
                """
                if self.eventBoundary:
                    self.pushView()

                try:
                    method = getattr (type (self.widget), 'Freeze')
                except AttributeError:
                    pass
                else:
                    method (self.widget)

                for child in self.childrenBlocks:
                    child.render()

                """
                  After the blocks are wired up give the window a chance
                to synchronize itself to any persistent state.
                """
                oldIgnoreSynchronizeWidget = wx.GetApp().ignoreSynchronizeWidget
                wx.GetApp().ignoreSynchronizeWidget = False
                try:
                    self.synchronizeWidget()
                finally:
                    wx.GetApp().ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

                try:
                    method = getattr (type (self.widget), 'Thaw')
                except AttributeError:
                    pass
                else:
                    method (self.widget)

    def unRender (self):
        try:
            widget = self.widget
        except AttributeError:
            pass
        else:
            if not isinstance (widget, wx.ToolBarToolBase):
                """
                  Remove child from parent before destroying child.
                """
                if isinstance (widget, wx.Window):
                    parent = widget.GetParent()
                    if parent:
                        parent.RemoveChild (widget)

                try:
                    method = getattr (type(widget), 'Destroy')
                except AttributeError:
                    pass
                else:
                    method (widget)

        for child in self.childrenBlocks:
            child.unRender()
        try:
            lastView = Globals.views[-1]
        except IndexError:
            pass
        else:
            if lastView == self:
                Globals.views.pop()

    def onCollectionChanged (self, action):
        """
          When our item collection has changed, we need to synchronize
        """
        self.synchronizeWidget()

    IdToUUID = []               # A list mapping Ids to UUIDS
    UUIDtoIds = {}              # A dictionary mapping UUIDS to Ids

    MINIMUM_WX_ID = 2500
    MAXIMUM_WX_ID = 4999

    def wxOnDestroyWidget (theClass, widget):
        if hasattr (widget, 'blockItem'):
            widget.blockItem.onDestroyWidget()
    wxOnDestroyWidget = classmethod (wxOnDestroyWidget)

    def onDestroyWidget (self):
        """
          Called just before a widget is destroyed. It is the opposite of
        instantiateWidget.
        """
        try:
            contents = self.contents
        except AttributeError:
            pass
        else:
            try:
                unsubscribe = getattr (type (contents), "unsubscribe")
            except AttributeError:
                pass
            else:
                unsubscribe (contents, self)
        try:
            eventsForNamedDispatch = self.widget.eventsForNamedDispatch
        except AttributeError:
            pass
        else:
            self.removeFromNameToItemUUIDDictionary (eventsForNamedDispatch,
                                                     self.eventNameToItemUUID)
        self.removeFromNameToItemUUIDDictionary ([self],
                                                 self.blockNameToItemUUID)

        delattr (self, 'widget')
        assert self.itsView.isRefCounted(), "respoitory must be opened with refcounted=True"
            
        wx.GetApp().needsUpdateUI = True

    def widgetIDToBlock (theClass, wxID):
        """
          Given a wxWindows Id, returns the corresponding Chandler block
        """
        return wx.GetApp().UIRepositoryView.find (theClass.IdToUUID [wxID - theClass.MINIMUM_WX_ID])
 
    widgetIDToBlock = classmethod (widgetIDToBlock)

    def getWidgetID (theClass, object):
        """
          wxWindows needs a integer for a id. Commands between
        wxID_LOWEST and wxID_HIGHEST are reserved. wxPython doesn't export
        wxID_LOWEST and wxID_HIGHEST, which are 4999 and 5999 respectively.
        Passing -1 for an ID will allocate a new ID starting with 0. So
        I will use the range starting at 2500 for our events.
          Use IdToUUID to lookup the Id for a event's UUID. Use UUIDtoIds to
        lookup the UUID of a block that corresponds to an event id -- DJA
        """
        UUID = object.itsUUID
        try:
            id = Block.UUIDtoIds [UUID]
        except KeyError:
            length = len (Block.IdToUUID)
            Block.IdToUUID.append (UUID)
            id = length + Block.MINIMUM_WX_ID
            assert (id <= Block.MAXIMUM_WX_ID)
            assert not Block.UUIDtoIds.has_key (UUID)
            Block.UUIDtoIds [UUID] = id
        return id
    getWidgetID = classmethod (getWidgetID)

    def getFocusBlock (theClass):
        focusWindow = wx.Window_FindFocus()
        while (focusWindow):
            try:
                return focusWindow.blockItem
            except AttributeError:
                focusWindow = focusWindow.GetParent()
        return Globals.views[0]
    getFocusBlock = classmethod (getFocusBlock)

    def onShowHideEvent(self, event):
        self.isShown = not self.isShown
        self.synchronizeWidget()
        self.parentBlock.synchronizeWidget()

    def onShowHideEventUpdateUI(self, event):
        event.arguments['Check'] = self.isShown

    def onModifyContentsEvent(self, event):
        def modifyContents (item):
            if event.copyItems:
                item = item.copy(parent=userdata, cloudAlias='default')

            operation = event.operation
            if operation == 'toggle':
                try:
                    index = self.contents.index (item)
                except ValueError:
                    operation = 'add'
                else:
                    operation = 'remove'
            if operation == 'add':
                if event.disambiguateItemNames:
                    displayName = item.displayName
                    newDisplayName = displayName
                    suffix = 1;
                    while True:
                        for contentsItem in self.contents:
                            if contentsItem.displayName == newDisplayName:
                                newDisplayName = displayName + u'-' + unicode (suffix)
                                suffix += 1
                                break
                        else:
                            break
                    if displayName != newDisplayName:
                        item.displayName = newDisplayName
                if not event.arguments.has_key ('item'):
                    event.arguments ['item'] = item

            method = getattr (type(self.contents), operation)
            method (self.contents, item)

        assert not event.arguments.has_key ('item')
        if event.copyItems:
            userdata = self.findPath('//userdata')

        assert (event.copyItems or not event.disambiguateItemNames), "Can't disabiguate names unless items are copied"

        for item in event.items:
            modifyContents (item)
        try:
            items = event.arguments ['items']
        except KeyError:
            pass
        else:
            for item in items:
                modifyContents (item)

    def synchronizeWidget (self):
        """
          synchronizeWidget's job is to make the wxWidget match the state of
        the data persisted in the block. There's a tricky problem that occurs: Often
        we add a handler to the wxWidget of a block to, for example, get called
        when the user changes the selection, which we use to update the block's selection
        and post a selection item block event. It turns out that while we are in
        synchronizeWidget, changes to the wxWidget cause these handlers to be
        called, and in this case we don't want to post an event. So we wrap calls
        to synchronizeWidget and set a flag indicating that we're inside
        synchronizeWidget so the handlers can tell when not to post selection
        changed events. We use this flag in other similar situations, for example,
        during shutdown to ignore events caused by the framework tearing down wxWidgets.
        """
        try:
            method = getattr (type (self.widget), 'wxSynchronizeWidget')
        except AttributeError:
            pass
        else:
            if not wx.GetApp().ignoreSynchronizeWidget:
                oldIgnoreSynchronizeWidget = wx.GetApp().ignoreSynchronizeWidget
                wx.GetApp().ignoreSynchronizeWidget = True
                try:
                    method (self.widget)
                finally:
                    wx.GetApp().ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

    def pushView (self):
        """ 
        Pushes a new view on to our list of views.
        
        @param self: the new view
        @type block: C{Block}
        @param Globals.mainViewRoot.lastDynamicBlock: the last block synched
        @type lastDynamicBlock: C{DynamicBlock}, or C{False} for no previous block,
                    or C{True} for forced resync.

          Currently, we're limited to a depth of four nested views
        """
        assert len (Globals.views) <= 4
        Globals.views.append (self)

        def synchToDynamicBlock (block, isChild):
            """
            Function to set and remember the dynamic Block we synch to.
            If it's a child block, it will be used so we must sync, and 
            remember it for later.
            If it's not a child, we only need to sync if we had a different
            block last time.
            """
            previous = Globals.mainViewRoot.lastDynamicBlock
            if isChild:
                Globals.mainViewRoot.lastDynamicBlock = block
            elif previous and previous is not block:
                Globals.mainViewRoot.lastDynamicBlock = False
            else:
                return

            block.synchronizeDynamicBlocks ()

        """
          Cruise up the parent hierarchy looking for the first
        block that can act as a DynamicChild or DynamicContainer
        (Menu, MenuBar, ToolbarItem, etc). 
        If it's a child, or it's not the same Block found the last time 
        the focus changed (or if we are forcing a rebuild) then we need 
        to rebuild the Dynamic Containers.
        """
        candidate = None
        block = self
        while (block):
            for child in block.childrenBlocks:
                try:
                    method = getattr (type (child), 'isDynamicChild')
                except AttributeError:
                    pass
                else:
                    if candidate is None:
                        candidate = child
                    isChild = method(child)
                    if isChild:
                        synchToDynamicBlock (child, True)
                        return
            block = block.parentBlock
        # none found, to remove dynamic additions we synch to the Active View
        #assert candidate, "Couldn't find a dynamic child to synchronize with"
        if candidate:
            synchToDynamicBlock (candidate, False)

    def getFrame(self):
        """
          Cruse up the tree of blocks looking for the top-most block that
        has a python attribute, which is the wxWidgets wxFrame window.
        """
        block = self
        while (block.parentBlock):
            block = block.parentBlock
        return block.frame

    def dispatchEvent (theClass, event):
        
        def callMethod(block, methodName, event):
            """
            wrapper for callNamedMethod that optionally invokes the profiler
            """

            # allow the compiler to optimize for non-debug cases
            if not __debug__:
                return callNamedMethod(block, methodName, event)
            else:
                if Block.profileEvents and not Block.__profilerActive:                        
                    # create profiler lazily
                    if not Block.__profiler:
                        Block.__profiler = hotshot.Profile('Events.prof')
                        
                    Block.__profilerActive = True
                    try:
                        #
                        # run the call inside the profiler
                        #
                        Block.__profiler.runcall(callNamedMethod, block, methodName, event)
                        Block.__profilerActive = False
                    except:
                        # make sure that we turn off reentrancy check no matter what
                        Block.__profilerActive = False
                        raise
                else:
                    return callNamedMethod(block, methodName, event)
                            
        def callNamedMethod (block, methodName, event):
            """
              Call method named methodName on block
            """
            try:
                member = getattr (type(block), methodName)
            except AttributeError:
                result = False
            else:
                if __debug__ and not methodName.endswith("UpdateUI"):
                    # show dispatched events
                    logger.debug("Calling %s on %s (%s): %s" % \
                                 (methodName, getattr(block, "blockName", "?"),
                                  block, getattr(event, "arguments", 
                                                 "(no arguments)")))

                result = member (block, event)
                if result is None:
                    result = True
            return result
        
        def bubbleUpCallMethod (block, methodName, event):
            """
              Call a method on a block or if it doesn't handle it try it's parents
            """
            while (block):
                if callMethod (block, methodName, event):
                    break
                block = block.parentBlock
        
        def broadcast (block, methodName, event, childTest):
            callMethod (block, methodName, event)
            for child in block.childrenBlocks:
                if childTest (child):
                    broadcast (child, methodName, event, childTest)

        """
          Construct method name based upon the type of the event.
        """
        try:
            methodName = event.methodName
        except AttributeError:
            methodName = 'on' + event.blockName + 'Event'

        if event.arguments.has_key ('UpdateUI'):
            methodName += 'UpdateUI'
            commitAfterDispatch = False
        else:
            commitAfterDispatch = event.commitAfterDispatch

        dispatchEnum = event.dispatchEnum
        if dispatchEnum == 'SendToBlockByReference':
            callMethod (event.destinationBlockReference, methodName, event)

        elif dispatchEnum == 'SendToBlockByName':
            callMethod (Block.findBlockByName (event.dispatchToBlockName), methodName, event)

        elif dispatchEnum == 'BroadcastInsideMyEventBoundary':
            block = event.arguments['sender']
            while (not block.eventBoundary and block.parentBlock):
                block = block.parentBlock
                
            broadcast (block,
                       methodName,
                       event,
                       lambda child: (child is not None and
                                      child.isShown and 
                                      not child.eventBoundary))

        elif dispatchEnum == 'BroadcastInsideActiveViewEventBoundary':
            try:
                block = Globals.views [1]
            except IndexError:
                pass
            else:                
                broadcast (block,
                           methodName,
                           event,
                           lambda child: (child is not None and
                                          child.isShown and 
                                          not child.eventBoundary))

        elif dispatchEnum == 'BroadcastEverywhere':
            broadcast (Globals.views[0],
                       methodName,
                       event,
                       lambda child: (child is not None and child.isShown))

        elif dispatchEnum == 'FocusBubbleUp':
            block = theClass.getFocusBlock()
            bubbleUpCallMethod (block, methodName, event)

        elif dispatchEnum == 'ActiveViewBubbleUp':
            try:
                block = Globals.views [1]
            except IndexError:
                pass
            else:                
                bubbleUpCallMethod (block, methodName, event)

        elif __debug__:
            assert (False)

        if commitAfterDispatch:
            wx.GetApp().UIRepositoryView.commit()
    dispatchEvent = classmethod (dispatchEvent)

    # event profiler (class attributes)
    profileEvents = False        # Make "True" to profile events
    __profilerActive = False       # to prevent reentrancy, if the profiler is currently active
    __profiler = None              # The hotshot profiler
    
    
class ShownSynchronizer:
    """
    A mixin that handles isShown-ness: Make sure my visibility matches my block's.
    """
    def wxSynchronizeWidget(self):
        if self.blockItem.isShown != self.IsShown():
            self.Show (self.blockItem.isShown)

# These are the mappings looked up by wxRectangularChild.CalculateWXFlag, below
_wxFlagMappings = {
    'grow': wx.GROW,
    'growConstrainAspectRatio': wx.SHAPED, 
    'alignCenter': wx.ALIGN_CENTER,
    'alignTopCenter': wx.ALIGN_TOP,
    'alignMiddleLeft': wx.ALIGN_LEFT,
    'alignBottomCenter': wx.ALIGN_BOTTOM,
    'alignMiddleRight': wx.ALIGN_RIGHT, 
    'alignTopLeft': wx.ALIGN_TOP | wx.ALIGN_LEFT,
    'alignTopRight': wx.ALIGN_TOP | wx.ALIGN_RIGHT,
    'alignBottomLeft': wx.ALIGN_BOTTOM | wx.ALIGN_LEFT,
    'alignBottomRight': wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT,
}

class wxRectangularChild (ShownSynchronizer, wx.Panel):
    def CalculateWXBorder(self, block):
        border = 0
        spacerRequired = False
        for edge in (block.border.top, block.border.left, block.border.bottom, block.border.right):
            if edge != 0:
                if border == 0:
                    border = edge
                elif border != edge:
                    spacerRequired = False
                    break
        """
          wxWindows sizers only allow borders with the same width, or no width, however
        blocks allow borders of different sizes for each of the 4 edges, so we need to
        simulate this by adding spacers. I'm postponing this case for Jed to finish, and
        until then an assert will catch this case. DJA
        """
        assert not spacerRequired
        
        return int (border)
    CalculateWXBorder = classmethod(CalculateWXBorder)

    def CalculateWXFlag (theClass, block):
        # Map from the alignmentEnum string to wx constant(s)
        flag = _wxFlagMappings[block.alignmentEnum]

        # Each border can be 0 or not, but all the nonzero borders must be equal
        # (The assert in CalculateWXBorder above checks this)
        if block.border.top != 0:
            flag |= wx.TOP
        if block.border.left != 0:
            flag |= wx.LEFT
        if block.border.bottom != 0:
            flag |= wx.BOTTOM
        if block.border.right != 0:
            flag |= wx.RIGHT

        return flag
    CalculateWXFlag = classmethod(CalculateWXFlag)    
    

class RectangularChild (Block):
    def DisplayContextMenu(self, position, data):
        try:
            self.contextMenu
        except:
            return
        else:
            self.contextMenu.displayContextMenu(self.widget, position, data)
                
        
class BlockEvent(Item):
    pass
