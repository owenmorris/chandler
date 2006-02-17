__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks"

import application.Globals as Globals
from application import schema
import application.dialogs.RecurrenceDialog as RecurrenceDialog
from repository.item.Item import Item
from osaf.pim.items import ContentItem
from osaf.pim import collections
import wx
import logging

logger = logging.getLogger(__name__)


def getProxiedItem(item):
    """ Given an item, wrap it with a proxy if appropriate. """
    # @@@ BJS It's probably worthwhile to combine this with 
    # RecurrenceDialog.getProxy, but currently that function doesn't do the 
    # isDeleted -> return None mapping we need here. To avoid risk in 0.6, 
    # I'm checking things in this way and we can revisit this later.
    if item is not None:
        if item.isDeleted():
            item = None
        else:
            # We have an item - return a proxy for it if necessary
            item = RecurrenceDialog.getProxy(u'ui', item)
    return item

def WithoutSynchronizeWidget(method):
    """
    method decorator for making use of 'ignoreSynchronizeWidget' -
    usually used in wx event handlers that would otherwise cause
    recursive event calls
    
    usage:
    @WithoutSynchronizeWidget
    def OnSomeEvent(self,...)
        self.PostSelectItems(...) # PostSelectItems would normally
                                  # end up calling OnSomeEvent
    """
    def with_sync(*args, **kwds):
        if not wx.GetApp().ignoreSynchronizeWidget:
            method(*args, **kwds)

    return with_sync

def IgnoreSynchronizeWidget(syncValue, method, *args, **kwds):
    """
    wrapper method to call something while temporarily suspending
    or enabling SynchronizeWidget

    usage:

    IgnoreSyncWidget(True, method, arg1, kw1=blah)

    this will block wxSynchronizeWidget calls
    """
    app = wx.GetApp()
    oldIgnoreSynchronizeWidget = app.ignoreSynchronizeWidget
    app.ignoreSynchronizeWidget = syncValue
    try:
        result = method(*args, **kwds)
    finally:
        app.ignoreSynchronizeWidget = oldIgnoreSynchronizeWidget

    return result
    


class Block(schema.Item):
    # @@@BJS: Should we show borders for debugging?
    showBorders = False

    contents = schema.One(ContentItem, otherName="contentsOwner")
    contentsCollection = schema.One(ContentItem, defaultValue=None)

    viewAttribute = schema.One(
        schema.Text,
        doc = 'Specifies which attribute of the selected Item should be '
              'associated with this block.',
        initialValue = u''
    )

    parentBlock = schema.One("Block",
        inverse="childrenBlocks",
        initialValue = None
    )
  
    childrenBlocks = schema.Sequence(
        "Block",
        inverse = parentBlock,
        initialValue = []
    )

    isShown = schema.One(schema.Boolean, initialValue=True)

    eventBoundary = schema.One(schema.Boolean, initialValue=False)

    contextMenu = schema.One("ControlBlocks.ContextMenu") 

    branchPointDetailItemOwner = schema.Sequence(
        "Block", 
        otherName = "detailItem"  # BranchPointBlock/detailItem
    )

    branchPointSelectedItemOwner = schema.Sequence(
        "Block",
        otherName = "selectedItem"     # BranchPointBlock/selectedItem
    )

    viewContainer = schema.Sequence(
        "Block",
        otherName = "views"     # ViewContainer/views
    )

    blockName = schema.One(schema.Text)
    eventsForNamedLookup = schema.Sequence("BlockEvent", defaultValue=None)

    parentBranchSubtrees = schema.Sequence(
        # The inverse of osaf.framework.blocks.BranchSubtree.rootBlocks
    )  

    position = schema.One(schema.Float)  #<!-- for tree-of-blocks sorting -->

    schema.addClouds(
        copying = schema.Cloud(
            byRef=[contents],
            byCloud=[childrenBlocks,eventsForNamedLookup]
        )
    )
    
    def post (self, event, arguments):
        """
          Events that are posted by the block pass along the block
        that sent it.
        
        @param event: the event to post
        @type event: a C{BlockEvent}
        @param arguments: arguments to pass to the event
        @type arguments: a C{dict}
        @return: the value returned by the event handler
        """
        try:
            try:
                stackedArguments = event.arguments
            except AttributeError:
                pass
            arguments ['sender'] = self
            arguments ['results'] = None
            event.arguments = arguments
            self.dispatchEvent (event)
            results = event.arguments ['results']
            return results # return after the finally clause
        finally:
            try:
                event.arguments = stackedArguments
            except UnboundLocalError:
                delattr (event, 'arguments')

    def postEventByName (self, eventName, args):
        assert self.eventNameToItemUUID.has_key (eventName), "Event name %s not found in %s" % (eventName, self)
        list = self.eventNameToItemUUID [eventName]
        return self.post (self.find (list [0]), args)

    eventNameToItemUUID = {}           # A dictionary mapping event names to event UUIDS
    blockNameToItemUUID = {}           # A dictionary mapping rendered block names to block UUIDS

    @classmethod
    def findBlockByName (theClass, name):
        list = theClass.blockNameToItemUUID.get (name, None)
        if list is not None:
            return wx.GetApp().UIRepositoryView.find (list[0])
        else:
            return None

    @classmethod
    def findBlockEventByName (theClass, name):
        list = theClass.eventNameToItemUUID.get (name, None)
        if list is not None:
            return wx.GetApp().UIRepositoryView.find (list[0])
        else:
            return None

    @classmethod
    def addToNameToItemUUIDDictionary (theClass, list, dictionary):
        for item in list:
            name = getattr (item, "blockName", None)
            if name is not None:
                list = dictionary.get (name, None)
                if list is None:
                    dictionary [name] = [item.itsUUID]
                else:
                    list.insert (0, item.itsUUID)

    @classmethod
    def removeFromNameToItemUUIDDictionary (theClass, list, dictionary):
        for item in list:
            name = getattr (item, "blockName", None)
            if name is not None:
                list = dictionary [name]
                list.remove (item.itsUUID)
                if len (list) == 0:
                    del dictionary [name]

    @classmethod
    def template(theClass, blockName, **attrs):
        """
        Very similar to the default template() routine, except that
        1) childrenBlocks is used for children
        2) the repository name and blockname are unified
        3) eventsForNamedLookup is automatically populated
        """
        
        # There might already be an eventsForNamedLookup, so just
        # append to the existing one if its already there
        event = attrs.get('event')
        eventsForNamedLookup = attrs.get('eventsForNamedLookup', [])

        if event and event not in eventsForNamedLookup:
            eventsForNamedLookup.append(event)
            # just in case it wasn't there originally
            attrs['eventsForNamedLookup'] = eventsForNamedLookup
            
        return BlockTemplate(theClass, blockName,
                             blockName=blockName, **attrs)

    def stopNotificationDirt (self):
        assert (self.ignoreNotifications >= 0)
        if self.ignoreNotifications == 0:
            collections.deliverNotifications (self.itsView)
        self.ignoreNotifications = self.ignoreNotifications + 1

    def startNotificationDirt (self):
        try:
            if self.ignoreNotifications == 1:
                collections.deliverNotifications (self.itsView)
        finally:
            assert (self.ignoreNotifications > 0)
            self.ignoreNotifications = self.ignoreNotifications - 1

    def setContentsOnBlock (self, item, collection):
        """
        A utility routine for onSetContents handlers that sets the
        contents of a block and updates the contents subscribers
        """
        self.contentsCollection = collection

        # manage subscriptions
        oldContents = getattr (self, 'contents', None)
        if oldContents is item:
            return
        if oldContents is not None:
            oldSubscribers = getattr(oldContents, 'subscribers', None)
            if oldSubscribers is not None and self in oldSubscribers:
                oldSubscribers.remove(self)
        if item is not None:
            newSubscribers = getattr(item, 'subscribers', None)
            if newSubscribers is not None:
                newSubscribers.add(self)
        self.contents = item

    def getProxiedContents(self):
        """ Get our 'contents', wrapped in a proxy if appropriate. """
        return getProxiedItem(getattr(self, 'contents', None))

    def render (self):
        method = getattr (type (self), "instantiateWidget", None)
        if method:
            widget = IgnoreSynchronizeWidget(True, method, self)
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
                method = getattr (type (widget), "OnInit", None)
                if method:
                    method (widget)
                """
                  For those blocks with Collection contents, we need to subscribe to notice changes
                to items in the contents.
                """
                contents = getattr (self, 'contents', None)
                if isinstance (contents, collections.AbstractCollection):
                    contents.subscribers.add (self)
                    # Add a non-persistent attribute that controls whether or not
                    # notifications will dirty the block.
                    self.ignoreNotifications = 0
                """
                  Add events to name lookup dictionary.
                """
                eventsForNamedLookup = self.eventsForNamedLookup
                if eventsForNamedLookup is not None:
                    self.addToNameToItemUUIDDictionary (eventsForNamedLookup,
                                                        self.eventNameToItemUUID)
                self.addToNameToItemUUIDDictionary ([self],
                                                    self.blockNameToItemUUID)
                """
                  Keep list of blocks that are have event boundarys in the global list views.
                """
                if self.eventBoundary:
                    self.pushView()

                method = getattr (type (widget), "Freeze", None)
                if method:
                    method (widget)

                for child in self.childrenBlocks:
                    child.render()

                """
                  After the blocks are wired up give the window a chance
                to synchronize itself to any persistent state.
                """
                IgnoreSynchronizeWidget(False, self.synchronizeWidget)

                method = getattr (type (widget), "Thaw", None)
                if method:
                    method (widget)

    def unRender (self):
        for child in self.childrenBlocks:
            child.unRender()
        widget = getattr (self, 'widget', None)

        if widget is not None:

            if __debug__:
                eventsForNamedLookup = self.eventsForNamedLookup
                if eventsForNamedLookup is not None:
                    oldCounts = []
                    for item in eventsForNamedLookup:
                        list = self.eventNameToItemUUID.get (item.blockName, None)
                        assert list is not None
                        oldCounts.append (list.count (item.itsUUID))

            method = getattr (type(widget), 'GetParent', None)
            if method is not None:
                parent = method (widget)
                """
                  Remove child from parent before destroying child.
                """
                if isinstance (widget, wx.Window):
                    parent = widget.GetParent()
                    if parent:
                        parent.RemoveChild (widget)

            method = getattr (type(widget), 'Destroy', None)
            if method is not None:
                method (widget)
        
            # If the block has eventsForNamedLookup, make sure they are all gone
            if __debug__:
                if eventsForNamedLookup is not None:
                    for item, oldCount in map (None, eventsForNamedLookup, oldCounts):
                        list = self.eventNameToItemUUID.get (item.blockName, None)
                        if list is None:
                            count = 0
                        else:
                            count = list.count (item.itsUUID)
                        assert count == oldCount - 1

        if (len (Globals.views) > 0 and Globals.views[-1] == self):
            Globals.views.pop()

    def onCollectionEvent (self, op, item, name, other, *args):
        """
          When our item collection has changed, we need to synchronize
        """
        if not self.ignoreNotifications:
            onItemNotification = getattr(self.widget, 'onItemNotification', None)
            if onItemNotification is not None:
                onItemNotification('collectionChange', (op, item, name, other, args))
            self.synchronizeSoon()

    def synchronizeSoon(self):
        """ Invoke our general deferred-synchronization mechanism """
        # each block should have a hints dictionary
        self.dirtyBlocks.add(self.itsUUID)

    IdToUUID = []               # A list mapping Ids to UUIDS
    UUIDtoIds = {}              # A dictionary mapping UUIDS to Ids
    dirtyBlocks = set()         # A set of blocks that need to be redrawn in OnIdle

    @classmethod
    def wxOnDestroyWidget (theClass, widget):
        if hasattr (widget, 'blockItem'):
            widget.blockItem.onDestroyWidget()

    def onDestroyWidget (self):
        """
          Called just before a widget is destroyed. It is the opposite of
        instantiateWidget.
        """
        contents = getattr (self, 'contents', None)
        if isinstance (contents, collections.AbstractCollection):
            # Remove the non-persistent attribute that controls whether or not
            # notifications will dirty the block.
            del self.ignoreNotifications
            contents.subscribers.remove (self)


        eventsForNamedLookup = self.eventsForNamedLookup
        if eventsForNamedLookup is not None:
            self.removeFromNameToItemUUIDDictionary (eventsForNamedLookup,
                                                     self.eventNameToItemUUID)
        self.removeFromNameToItemUUIDDictionary ([self],
                                                 self.blockNameToItemUUID)

        delattr (self, 'widget')
        assert self.itsView.isRefCounted(), "respoitory must be opened with refcounted=True"
            
        wx.GetApp().needsUpdateUI = True

    @classmethod
    def widgetIDToBlock (theClass, wxID):
        """
          Given a wxWindows Id, returns the corresponding Chandler block
        """
        return wx.GetApp().UIRepositoryView.find (theClass.IdToUUID [wxID - (wx.ID_HIGHEST + 1)])
 

    @classmethod
    def getWidgetID (theClass, object):
        """
        wxWindows needs a integer for a id. Commands between
        wx.ID_LOWEST and wx.ID_HIGHEST are reserved for wxWidgets.
        Calling wxNewId allocates incremental ids starting at 100.
        Passing -1 for new IDs starting with -1 and decrementing.
        Some rouge dialogs use IDs outside wx.ID_LOWEST and wx.ID_HIGHEST.
        
        Use IdToUUID to lookup the Id for a event's UUID. Use UUIDtoIds to
        lookup the UUID of a block that corresponds to an event id -- DJA
        """
        UUID = object.itsUUID
        try:
            id = Block.UUIDtoIds [UUID]
        except KeyError:
            length = len (Block.IdToUUID)
            Block.IdToUUID.append (UUID)
            id = length + wx.ID_HIGHEST + 1
            assert not Block.UUIDtoIds.has_key (UUID)
            Block.UUIDtoIds [UUID] = id
        return id

    @classmethod
    def getFocusBlock (theClass):
        focusWindow = wx.Window_FindFocus()
        while (focusWindow):
            block = getattr (focusWindow, "blockItem", None)
            if block is None:
                focusWindow = focusWindow.GetParent()
            else:
                return block
        return Globals.views[0]

    @classmethod
    def finishEdits(theClass, onBlock=None):
        """ 
        If the given block, or the focus block if no block given, has a 
        saveValue method, call it to write pending edits back.
        """
        if onBlock is None:
            onBlock = Block.getFocusBlock()
        if onBlock is not None:
            saveValueMethod = getattr(onBlock, 'saveValue', None)
            if saveValueMethod is not None:
                saveValueMethod()
        
    def onShowHideEvent(self, event):
        self.isShown = not self.isShown
        self.synchronizeWidget()
        self.parentBlock.synchronizeWidget()

    def onShowHideEventUpdateUI(self, event):
        event.arguments['Check'] = self.isShown

    def onModifyCollectionEvent(self, event):
        """
        Adds itms to a collection, by default the sidebarCollection.

        This method originally had an operation attribute that let you add,
        remove or toggle (e.g. add if not present or delete if present) items
        to a collection.
        
        Since this behavior is no longer used, we removed it. It can be added back
        if necessary
        """
        collection = getattr (schema.ns ("osaf.app", self.itsView), event.collectionName)
        itemList = []
        for item in event.items:

            if event.copyItems:
                # Do a cloud copy
                item = item.copy (parent = self.getDefaultParent(self.itsView),
                                  cloudAlias="copying")
                # And call setup if it exists
                method = getattr (type (item), "setup", None)
                if method:
                    method (item)

            # Call the item's onAddToCollection method if it has one. If it returns None
            # Exit. If it returns something else, add that to the collection
            method = getattr (type (item), "onAddToCollection", None)
            if method:
                result = method (item, event)
                if result is None:
                    if event.copyItems:
                        item.delete (cloudAlias="copying")
                    return
                item = result

            if event.disambiguateDisplayName:
                # You can only change the name if you make a copy
                assert self.copy
                displayName = item.displayName
                newDisplayName = displayName
                suffix = 1;
                while True:
                    for theCollection in collection:
                        if theCollection.displayName == newDisplayName:
                            newDisplayName = displayName + u'-' + unicode (suffix)
                            suffix += 1
                            break
                    else:
                        item.displayName = newDisplayName
                        break
            
            collection.add (item)

            # Optionally select the item in a named block and p;ossibly edit
            # an attribute on it
            selectInBlockNamed = getattr (event, "selectInBlockNamed", None)
            if selectInBlockNamed is not None:
                blockItem = self.findBlockByName (selectInBlockNamed)
                assert (blockItem is not None)
                arguments = {'items':[item]}
                editAttributeNamed = getattr (event, "editAttributeNamed", None)
                if editAttributeNamed is not None:
                    arguments ['editAttributeNamed'] = editAttributeNamed
                blockItem.postEventByName ("SelectItemsBroadcast", arguments)

            itemList.append (item)
        # Need to SelectFirstItem -- DJA based on self.selectInBlock
        return itemList

    def synchronizeWidget (self, useHints=False):
        """
        synchronizeWidget's job is to make the wxWidget match the
        state of the data persisted in the block.

        There's a tricky problem that occurs: Often we add a handler
        to the wxWidget of a block to, for example, get called when
        the user changes the selection, which we use to update the
        block's selection and post a selection item block event.

        It turns out that while we are in synchronizeWidget, changes
        to the wxWidget cause these handlers to be called, and in this
        case we don't want to post an event. So we wrap calls to
        synchronizeWidget and set a flag indicating that we're inside
        synchronizeWidget so the handlers can tell when not to post
        selection changed events. We use this flag in other similar
        situations, for example, during shutdown to ignore events
        caused by the framework tearing down wxWidgets.
        """
        widget = getattr (self, "widget", None)
        if widget is not None:
            method = getattr (type (widget), 'wxSynchronizeWidget', None)
            if method is not None:
                IgnoreSynchronizeWidget(True, method, widget, useHints)

    def pushView (self):
        """ 
        Pushes a new view on to our list of views.

        Currently, we're limited to a depth of four nested views

        @param self: the new view
        @type block: C{Block}
        @param Globals.mainViewRoot.lastDynamicBlock: the last block synched
        @type lastDynamicBlock: C{DynamicBlock}, or C{False} for no previous block,
                    or C{True} for forced resync.
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

    @classmethod
    def dispatchEvent (theClass, event):
        
        def callProfiledMethod(blockOrWidget, methodName, event):
            """
            Wrap callNamedMethod with a profiler runcall()
            """
            if not Block.__profilerActive:                        
                # create profiler lazily
                if not Block.__profiler:
                    import hotshot
                    Block.__profiler = hotshot.Profile('Events.prof')
                    
                Block.__profilerActive = True
                try:
                    #
                    # run the call inside the profiler
                    #
                    return Block.__profiler.runcall(callNamedMethod, blockOrWidget, methodName, event)
                finally:
                    # make sure that we turn off reentrancy check no matter what
                    Block.__profilerActive = False
            else:
                return callNamedMethod(blockOrWidget, methodName, event)
                            
        def callNamedMethod (blockOrWidget, methodName, event):
            """
              Call method named methodName on block or widget
            """
            member = getattr (type(blockOrWidget), methodName, None)
            if member is None:
                return False
            else:
                #if __debug__ and not methodName.endswith("UpdateUI"):
                    ## show dispatched events
                    #logger.debug("Calling %s on %s (%s): %s" % \
                                 #(methodName, getattr(block, "blockName", "?"),
                                  #block, getattr(event, "arguments", 
                                                 #"(no arguments)")))

                event.arguments ['results'] = member (blockOrWidget, event)
                return True

        if Block.profileEvents:
            # We're profiling, use the wrapper
            callMethod = callProfiledMethod
        else:
            # Not profiling, use the straight-up call
            callMethod = callNamedMethod

        def bubbleUpCallMethod (blockOrWidget, methodName, event):
            """
              Call a method on a block or widget or if it doesn't handle it try it's parents
            """
            event.arguments ['continueBubbleUp'] = False # default to stop bubbling
            while (blockOrWidget):
                if callMethod (blockOrWidget, methodName, event): # method called?
                    if event.arguments ['continueBubbleUp']: # overwrote the default?  
                        event.arguments ['continueBubbleUp'] = False # reset the default
                    else:
                        break
                if isinstance (blockOrWidget, Block):
                    blockOrWidget = blockOrWidget.parentBlock
                else:
                    # We should have a widget
                    assert isinstance (blockOrWidget, wx.Window)
                    # Try the block if the widget has one, otherwise
                    # try the widget's parent
                    block = getattr (blockOrWidget, 'blockItem', None)
                    if block is None:
                        blockOrWidget = blockOrWidget.GetParent()
                    else:
                        blockOrWidget = block

        
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
            # we want the text to default to the block title
            # this makes sure that if someone modifies Text during UpdateUI
            # that it later can get reset to the default from the block
            title = getattr(event.arguments['sender'], 'title', '')
            if title:
                accel = getattr(event.arguments['sender'], 'accel', '')
                if accel:
                    title += '\t' + accel
                    # this isn't a real wx argument, but is used later
                    # to re-attach the accelerator after the client has
                    # updated the 'Text' argument
                    event.arguments['Accel'] = accel
                event.arguments['Text'] = title
            methodName += 'UpdateUI'
            commitAfterDispatch = False
        else:
            commitAfterDispatch = event.commitAfterDispatch

        dispatchEnum = event.dispatchEnum
        if dispatchEnum == 'SendToBlockByReference':
            callMethod (event.destinationBlockReference, methodName, event)

        elif dispatchEnum == 'SendToSender':
            block = event.arguments['sender']
            callMethod (block, methodName, event)

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
                                          not child.eventBoundary))

        elif dispatchEnum == 'BroadcastEverywhere':
            broadcast (Globals.views[0],
                       methodName,
                       event,
                       lambda child: (child is not None))

        elif dispatchEnum == 'FocusBubbleUp':
            """
            FocusBubbleUp dispatches the event bubbling up from focused
            widget, or main view if there isn't a focus widget.
            
            Focused widgets are included so that attribute editors, which
            don't always have block counterparts, get a crack at handling events.
            """
            blockOrWidget = wx.Window_FindFocus()
            if blockOrWidget is None:
                blockOrWidget = Globals.views[0]
            bubbleUpCallMethod (blockOrWidget, methodName, event)

        elif dispatchEnum == 'ActiveViewBubbleUp':
            try:
                v = Globals.views [1]
                # the active view is typically a splitter, so really
                # we probably want the first child (and even if we
                # don't, the event will bubble up)
                
                # for some reason v.childrenBlocks[0] is busting
                block = v.childrenBlocks.first()
            except IndexError:
                pass
            else:                
                bubbleUpCallMethod (block, methodName, event)

        elif __debug__:
            assert (False)

        # clean up any accelerator mess left by wx
        if (event.arguments.has_key('Accel') and
            event.arguments.has_key('Text') and
            event.arguments['Text'] != title):
            event.arguments['Text'] += '\t' + event.arguments['Accel']
        if commitAfterDispatch:
            wx.GetApp().UIRepositoryView.commit()

    # event profiler (class attributes)
    profileEvents = False        # Make "True" to profile events
    __profilerActive = False       # to prevent reentrancy, if the profiler is currently active
    __profiler = None              # The hotshot profiler

def debugName(thing):
    """
    Debug method to get a useful name for this thing, which can be a 
    block or a widget, to use in a logging message.      
    """
    if thing is None:
        return '(None)'
    
    if isinstance(thing, Block):
        return getattr(thing, 'blockName', '(unnamed %s)' % thing.__class__.__name__)
    
    blockItem = getattr(thing, 'blockItem', None)
    if blockItem is not None:
        return '%s on %s' % (thing.__class__.__name__, debugName(blockItem))

    from osaf.framework.attributeEditors import BaseAttributeEditor
    if isinstance(thing, BaseAttributeEditor):
        widget = getattr(thing, 'control', None)
        return '%s on %s' % (thing.__class__.__name__, debugName(widget))

    return '(unknown)'
    
    
class ShownSynchronizer(object):
    """
    A mixin that handles isShown-ness: Make sure my visibility
    matches my block's.
    """
    def wxSynchronizeWidget(self, useHints=False):
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
    @classmethod
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
          wxWindows sizers only allow borders with the same width, or
          no width, however blocks allow borders of different sizes
          for each of the 4 edges, so we need to simulate this by
          adding spacers. I'm postponing this case for Jed to finish,
          and until then an assert will catch this case. DJA
        """
        assert not spacerRequired
        
        return int (border)

    @classmethod
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
    
class alignmentEnumType(schema.Enumeration):
    values = (
        "grow", "growConstrainAspectRatio", "alignCenter", "alignTopCenter",
        "alignMiddleLeft", "alignBottomCenter", "alignMiddleRight",
        "alignTopLeft", "alignTopRight", "alignBottomLeft", "alignBottomRight",
    )

class RectangularChild (Block):

    from osaf.pim.structs import SizeType, RectType

    size = schema.One(SizeType, initialValue = SizeType(0, 0))
    minimumSize = schema.One(SizeType, initialValue = SizeType(-1, -1))
    border = schema.One(RectType, initialValue = RectType(0.0, 0.0, 0.0, 0.0))
    alignmentEnum = schema.One(alignmentEnumType, initialValue = 'grow')
    stretchFactor = schema.One(schema.Float, initialValue = 1.0)

    def DisplayContextMenu(self, position, data):
        try:
            self.contextMenu
        except:
            return
        else:
            self.contextMenu.displayContextMenu(self.widget, position, data)
 
class dispatchEnumType(schema.Enumeration):
    values = (
        "BroadcastInsideMyEventBoundary",
        "BroadcastInsideActiveViewEventBoundary",
        "BroadcastEverywhere", "FocusBubbleUp", "ActiveViewBubbleUp",
        "SendToBlockByReference", "SendToBlockByName", "SendToSender",
    )

class BlockEvent(schema.Item):
    dispatchEnum = schema.One(
        dispatchEnumType, initialValue = 'SendToBlockByReference',
    )
    commitAfterDispatch = schema.One(schema.Boolean, initialValue = False)
    destinationBlockReference = schema.One(Block)
    dispatchToBlockName = schema.One(schema.Text)
    methodName = schema.One(schema.Text)
    blockName = schema.One(schema.Text)
    schema.addClouds(
        copying = schema.Cloud(byCloud=[destinationBlockReference])
    )
    def __repr__(self):
        # useful for debugging that i've done.  i dunno if event.arguments
        # is guaranteed to be there?  -brendano

        if hasattr(self, "arguments"):
            try:
                name = self.blockName
            except AttributeError:
                name = self.itsUUID
            return "%s, arguments=%s" %(name, repr(self.arguments))

        else:
            return super(BlockEvent, self).__repr__()

    @classmethod
    def template(theClass, blockName, dispatchEnum, **attrs):
        """
        Very similar to the default template() routine, except that
        1) the repository name and blockname are unified
        2) The dispatchEnum is required
        """
        return BlockTemplate(theClass, blockName,
                             blockName=blockName,
                             dispatchEnum=dispatchEnum,
                             **attrs)
class ChoiceEvent(BlockEvent):
    choice = schema.One(schema.Text, required = True)

class ColorEvent(BlockEvent):
    from osaf.pim.structs import ColorType
    color = schema.One(ColorType, required = True)

class KindParameterizedEvent(BlockEvent):
    kindParameter = schema.One(
        schema.TypeReference('//Schema/Core/Kind'),
        required = True,
    )
    schema.addClouds(
        copying = schema.Cloud(byRef=[kindParameter])
    )
    


class ModifyCollectionEvent(BlockEvent):
    items = schema.Sequence(schema.Item, initialValue = [])
    collectionName = schema.One(schema.Text, initialValue = "sidebarCollection")
    copyItems = schema.One(schema.Boolean, defaultValue=False)
    selectInBlockNamed = schema.One(schema.Text)
    editAttributeNamed = schema.One(schema.Text)
    disambiguateDisplayName = schema.One(schema.Boolean, defaultValue=False)
    schema.addClouds(
        copying = schema.Cloud(byRef=[items])
    )


class EventList(schema.Item):
    eventsForNamedLookup = schema.Sequence(BlockEvent)


class lineStyleEnumType(schema.Enumeration):
      values = "SingleLine", "MultiLine"

# -------------
# Item creation
# -------------
class BlockTemplate(object):
    """
    Template class for easy domain-specific item creation
    In general, this allows a class to make a 'template' wrapper which
    will create all items and their children appropriately.
    """
    def __init__(self, target_class, itsName, **attrs):
        self.attrs = attrs
        self.itsName = itsName
        self.target_class = target_class

    def install(self, parent, name=None):
        if name is None: name=self.itsName

        # first make parent exist
        me = self.target_class.update(parent, name)

        # this is a temporary attribute list, which will contain
        # all the instantiated children, to be passed to .update
        attrs = self.attrs.copy()

        # this allows childrenBlocks to actually refer to blocks, or
        # just to templates
        def install(templateOrBlock):
            if isinstance(templateOrBlock, Block):
                return templateOrBlock
            return templateOrBlock.install(parent)
        
        # now hook up the children, and replace the templates
        # with the real things
        if 'childrenBlocks' in attrs:
            children = [install(t) for t in attrs['childrenBlocks']]
            attrs['childrenBlocks'] = children
            
        return self.target_class.update(parent, name, **attrs)
