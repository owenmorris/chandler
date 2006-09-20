#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


__parcel__ = "osaf.framework.blocks"

import application.Globals as Globals
from application import schema
import application.dialogs.RecurrenceDialog as RecurrenceDialog
from osaf.pim.items import ContentItem
from osaf.pim.collections import ContentCollection
from osaf.usercollections import UserCollection
import wx
import logging

logger = logging.getLogger(__name__)


def getProxiedItem(item):
    """
    Given an item, wrap it with a proxy if appropriate.
    """
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
    Method decorator for making use of 'ignoreSynchronizeWidget' -
    usually used in wx event handlers that would otherwise cause
    recursive event calls

    usage::
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
    Wrapper method to call something while temporarily suspending
    or enabling SynchronizeWidget

    usage::
        IgnoreSyncWidget(True, method, arg1, kw1=blah)

    This will block wxSynchronizeWidget calls
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

    # Blocks instances can be put into ListCollections or AppCollections
    collections = schema.Sequence(otherName='inclusions')

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
    
    #If the widget for your block requires a specific id, e.g. it's a standard
    #command handled by some standard part of wxWidgets, like a dialog that handles
    #cut/copy/paste you can specify it here, Also, when a dialog is topmost and
    #command has a non-zero wxId, it will be sent to the dialog instead of being
    #propagated like the usual CPIA events.
    #See Bug #5219
    wxId = schema.One (schema.Integer, defaultValue=0)
    
    # event profiler (class attributes)
    profileEvents = False          # Make "True" to profile events
    __profilerActive = False       # to prevent reentrancy, if the profiler is currently active
    __profiler = None              # The hotshot profiler

    depth = 0                      # Recursive post depth

    @classmethod
    def post (self, event, arguments, sender=None):
        """
        Events that are posted by the block pass along the block
        that sent it.
        
        @param event: the event to post
        @type event: a C{BlockEvent}
        @param arguments: arguments to pass to the event
        @type arguments: a C{dict}
        @param sender: the block that sent the event
        @type sender: a C{Block}
        @return: the value returned by the event handler
        """
        try:
            Block.depth += 1
            stackedArguments = getattr (event, "arguments", None)
            arguments ['sender'] = sender
            arguments ['results'] = None
            event.arguments = arguments
            
            hookListItem = schema.ns (__name__, wx.GetApp().UIRepositoryView).BlockDispatchHookList
            for hookItem in hookListItem.hooks:
                hookItem.dispatchEvent (event, Block.depth)

            results = event.arguments ['results']
            return results # return after the finally clause
        finally:
            Block.depth -= 1
            if stackedArguments is None:
                delattr (event, 'arguments')
            else:
                event.arguments = stackedArguments

    @classmethod
    def postEventByNameWithSender (theClass, eventName, args, sender=None):
        """
        A variant of post that looks up the event to post by name and
        includes a sender, which may be None
        """
        assert Block.eventNameToItemUUID.has_key (eventName), "Event name %s not found in %s" % (eventName, self)
        list = Block.eventNameToItemUUID [eventName]
        event = wx.GetApp().UIRepositoryView.findUUID (list [0])
        return theClass.post (event, args, sender)

    def postEventByName (self, eventName, args):
        """
        A variant of postEventByNameWithSender that sets the sender to self.
        """
        return self.postEventByNameWithSender (eventName, args, sender=self)


    eventNameToItemUUID = {}           # A dictionary mapping event names to event UUIDS
    blockNameToItemUUID = {}           # A dictionary mapping rendered block names to block UUIDS

    @classmethod
    def findBlockByName (theClass, name):
        list = Block.blockNameToItemUUID.get (name, None)
        if list is not None:
            return wx.GetApp().UIRepositoryView.find (list[0])
        else:
            return None

    @classmethod
    def findBlockEventByName (theClass, name):
        list = Block.eventNameToItemUUID.get (name, None)
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
    def template(theClass, itemName, blockName=None, **attrs):
        """
        Very similar to the default template() routine, except that
        1) childrenBlocks is used for children
        2) the repository name and blockname are unified by default
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
            
        return BlockTemplate(theClass, itemName,
                             blockName=blockName or itemName, 
                             **attrs)

    # Controls whether or not notifications will dirty the block.
    ignoreNotifications = property(
        lambda self: self.__dict__.get('__ignoreNotifications', 0),
        lambda self, v: self.__dict__.update(__ignoreNotifications=v)) 
    
    def stopNotificationDirt (self):
        assert (self.ignoreNotifications >= 0)
        if self.ignoreNotifications == 0:
            self.itsView.dispatchNotifications()
        self.ignoreNotifications = self.ignoreNotifications + 1

    def startNotificationDirt (self):
        try:
            if self.ignoreNotifications == 1:
                self.itsView.dispatchNotifications()
        finally:
            assert (self.ignoreNotifications > 0)
            self.ignoreNotifications = self.ignoreNotifications - 1

    def setContentsOnBlock (self, item, collection):
        """
        A utility routine for onSetContents handlers that sets the
        contents of a block and updates the contents subscribers.
        """
        self.stopWatchingForChanges()
        self.contentsCollection = collection
        self.contents = item
        self.watchForChanges()

    def getProxiedContents(self):
        """
        Get our 'contents', wrapped in a proxy if appropriate.
        """
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
                Subscribe to changes on our contents if appropriate.
                """
                self.watchForChanges()
                
                """
                Add events to name lookup dictionary.
                """
                eventsForNamedLookup = self.eventsForNamedLookup
                if eventsForNamedLookup is not None:
                    self.addToNameToItemUUIDDictionary (eventsForNamedLookup,
                                                        Block.eventNameToItemUUID)
                self.addToNameToItemUUIDDictionary ([self],
                                                    Block.blockNameToItemUUID)
                if self.eventBoundary:
                    self.rebuildDynamicBlocks()

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
                # If the block has eventsForNamedLookup, make sure they are all gone
                eventsForNamedLookup = self.eventsForNamedLookup
                if eventsForNamedLookup is not None:
                    oldCounts = []
                    for item in eventsForNamedLookup:
                        list = Block.eventNameToItemUUID.get (item.blockName, None)
                        assert list is not None
                        oldCounts.append (list.count (item.itsUUID))

                # Also, verify that the widget is deleted from it's parent
                numberChildren = None
                method = getattr (type(widget), 'GetParent', None)
                if method is not None:
                    parent = method (widget)
                    method = getattr (type(parent), 'GetChildren', None)
                    if method is not None:
                        parentsChildren = method (parent)
                        if widget in parentsChildren:
                            numberChildren = len (parentsChildren)

            method = getattr (type(widget), 'Destroy', None)
            if method is not None:
                method (widget)

            if __debug__:
                # If the block has eventsForNamedLookup, make sure they are all gone
                if eventsForNamedLookup is not None:
                    for item, oldCount in map (None, eventsForNamedLookup, oldCounts):
                        list = Block.eventNameToItemUUID.get (item.blockName, None)
                        if list is None:
                            count = 0
                        else:
                            count = list.count (item.itsUUID)
                        assert count == oldCount - 1
                
                # Also, verify that the widget is deleted from it's parent
                if numberChildren is not None:
                    assert numberChildren == len (parent.GetChildren()) + 1


    # We keep track of what items we're watching for which blocks.
    # watchingItems[itemUUID][attributeName] is a set() of blocks
    # to be notified when we get a change notification about that
    # item/attribute.
    watchingItems = {}
    if __debug__:
        @classmethod
        def dumpWatches(cls):
            view = wx.GetApp().UIRepositoryView
            for (uuid, attrDict) in Block.watchingItems.items():
                i = view.findUUID(uuid, False)
                print debugName(i or uuid)
                for (a, blockSet) in attrDict.items():
                    print "  %s: %s" % (a, ", ".join(map(debugName, blockSet)))

    def whichAttribute(self):
        # Which attribute is this block concerned with -- ours or our parent's
        # 'viewAttribute'?
        # @@@ BJS: this shouldn't need to use our parent's once the remaining old
        # detail view blocks are rewritten.
        return getattr(self, 'viewAttribute',
                       getattr(self.parentBlock, 'viewAttribute', u''))

    def getWatchList(self):
        """
        Get the list of item, attributeName tuples
        that we'll watch while rendered. By default, it's our
        'contents' item, and our viewAttribute; if we don't have a
        viewAttribute, we return an empty list.
        """
        whichAttr = self.whichAttribute()
        return whichAttr and [ (self.contents, whichAttr) ] or []

    def watchForChanges(self):
        if not hasattr(self, 'widget'):
            return

        contents = getattr (self, 'contents', None)
        if contents is None or contents.isDeleted():
            return # nothing to watch on

        # If this looks like a collection, we'll subscribe to
        # collection notifications.
        if isinstance(contents, ContentCollection):
            self.itsView.watchCollectionQueue(self, contents,
                                              'onCollectionNotification')

        # Do item subscription, if this block wants us to watch 
        # something and has an onItemNotification method
        if not (hasattr(type(self), 'onItemNotification') or
                hasattr(self.widget, 'onItemNotification')):
            return # no one to notify
        watchList = self.getWatchList()
        if not watchList:
            return # nothing to watch
        
        assert not hasattr(self, 'watchedItemAttributes')
        watchedItemAttributes = set()
        for (item, attr) in watchList:
            if attr:
                watchedItemAttributes.add((item, attr))
                self.addWatch(item, attr)
        if len(watchedItemAttributes):
            self.watchedItemAttributes = watchedItemAttributes

    def addWatch(self, item, *attributeNames):
        item = getattr(item, 'proxiedItem', item)
        uuid = item.itsUUID
        itemDict = Block.watchingItems.setdefault(uuid, {})
        if len(itemDict) == 0:
            # We're not watching this item yet - start.
            self.itsView.watchItem(self, item, 'onWatchNotification')
        
        getBasedMethod = getattr(type(item), 'getBasedAttributes', None)
        if getBasedMethod is not None:
            realAttributeNames = []
            for attribute in attributeNames:
                realAttributeNames.extend(getBasedMethod(item, attribute))
            attributeNames = realAttributeNames
            
        for attributeName in attributeNames:
            itemDict.setdefault(attributeName, set()).add(self)
            
    def stopWatchingForChanges(self):
        # unsubscribe from collection notifications
        contents = getattr (self, 'contents', None)
        if contents is not None and isinstance(contents, ContentCollection):
            self.itsView.unwatchCollectionQueue(self, contents,
                                                'onCollectionNotification')
            
        # do item notifications, too, if we had any
        try:
            watchedItemAttributes = self.watchedItemAttributes
        except AttributeError:
            pass
        else:
            for (item, attr) in watchedItemAttributes:
                self.removeWatch(item, attr)
            del self.watchedItemAttributes
            
    def removeWatch(self, item, *attributeNames):
        """
        Stop watching these attributes on this item.
        """
        item = getattr(item, 'proxiedItem', item)
        uuid = item.itsUUID
        itemDict = Block.watchingItems.get(uuid, None)
        if itemDict is not None:
            getBasedMethod = getattr(type(item), 'getBasedAttributes', None)
            if getBasedMethod is not None:
                realAttributeNames = []
                for attribute in attributeNames:
                    realAttributeNames.extend(getBasedMethod(item, attribute))
                attributeNames = realAttributeNames
    
            for attributeName in attributeNames:
                blockSet = itemDict.get(attributeName, None)
                if blockSet is not None:
                    blockSet.discard(self)
                    if len(blockSet) == 0:
                        # we're no longer watching this attribute
                        del itemDict[attributeName]

            if len(itemDict) == 0:
                # We're no longer watching any attributes on this item.
                del Block.watchingItems[uuid]
                self.itsView.unwatchItem(Block, item, 'onWatchNotification')
        
    @classmethod
    def onWatchNotification(cls, op, uuid, names):
        """
        When an item someone's watching has changed, we need to synchronize.
        """
        # Ignore notifications for items being stamped. (We get a lot then, 
        # but the items really aren't consistent. Anyone who cares about an 
        # item kind change should have another way to hear about it: the 
        # detail view explicitly monitors itsKind; that notification, as 
        # well as collection-change notifications that the rest of the app 
        # uses, happen outside isMutating.
        repoView = wx.GetApp().UIRepositoryView            
        item = repoView.find(uuid, False)
        if item is not None and item.isMutatingOrDeleting():
            return
                
        itemDict = Block.watchingItems.get(uuid, None)
        if itemDict is not None:
            notifications = {}
            # Collect all the blocks we're supposed to notify about
            # this item and these attributes
            for attributeName in names:
                for block in itemDict.get(attributeName, ()):
                    if not block.ignoreNotifications:
                        # add to (or start) the list of attributes on
                        # this block that we need to notify now.
                        notifications.setdefault(block, [])\
                                     .append(attributeName)
            # Do the notifications
            for (block, attrs) in notifications.items():
                #logger.debug("Notifying %s of change to '%s'",
                             #debugName(block), "', '".join(attrs))
                block._sendItemNotificationAndSynchronize('itemChange',
                                                          (op, uuid, attrs))
        
    def onCollectionNotification(self, op, collection, name, other):
        """
        When our item collection has changed, we need to synchronize.
        """
        if (not self.ignoreNotifications and
            self.itsView is wx.GetApp().UIRepositoryView):
            self._sendItemNotificationAndSynchronize('collectionChange',
                                                     (op, collection, 
                                                      name, other))

    def _sendItemNotificationAndSynchronize(self, notificationType, data):
        # Note that we need to be sync'd at the next idle.
        # (this is the normal case on receiving a notification like this, though
        # an onItemNotificationMethod can call markClean if the next-idle
        # sync isn't necessary) 
        self.markDirty()
        
        # See if the block and/or the widget want to be notified.
        # (We do both because some of the calendar blocks and widgets both
        # have handlers)
        onItemNotification = getattr(type(self), 'onItemNotification', None)
        if onItemNotification is not None:
            onItemNotification(self, notificationType, data)
        if hasattr(self, 'widget'):
            # (don't look up on type(self.widget) because it's not an Item,
            # and so doesn't pay a repository lookup penalty)
            onItemNotification = getattr(self.widget, 'onItemNotification', None)
            if onItemNotification is not None:
                onItemNotification(notificationType, data)
        
    idToBlock = {}              # A dictionary mapping wxWidgets Ids to Blocks
    freeWXIds = []              # A list of unused wxWidgets Ids
    dirtyBlocks = set()         # A set of blocks that need to be redrawn in OnIdle

    def markDirty(self):
        """
        Invoke our general deferred-synchronization mechanism
        """
        # each block should have a hints dictionary
        self.dirtyBlocks.add(self.itsUUID)

    def markClean(self):
        """
        Suppress our general deferred-synchronization mechanism.
        """
        self.dirtyBlocks.discard(self.itsUUID)

    @classmethod
    def wxOnDestroyWidget (theClass, widget):
        if hasattr (widget, 'blockItem'):
            widget.blockItem.onDestroyWidget()

    def onDestroyWidget (self):
        """
        Called just before a widget is destroyed. It is the opposite of
        instantiateWidget.
        """
        self.stopWatchingForChanges()

        eventsForNamedLookup = self.eventsForNamedLookup
        if eventsForNamedLookup is not None:
            self.removeFromNameToItemUUIDDictionary (eventsForNamedLookup,
                                                     Block.eventNameToItemUUID)
        self.removeFromNameToItemUUIDDictionary ([self],
                                                 Block.blockNameToItemUUID)

        #Remove the reference to the block in idToBlock and add the
        #id to the list of free ids. Also, if we don't remove the
        #reference to the block, it will be forced to be memory resident.
        method = getattr (type (self.widget), 'GetId', None)
        if method is not None:
            id = method (self.widget)
        else:
            id = -1

        if id > 0:
            del self.idToBlock[id]
            if self.wxId == 0:
                assert (not id in self.freeWXIds)
                self.freeWXIds.append (id)
        else:
            assert (not self.idToBlock.has_key(id))

        delattr (self, 'widget')
        assert self.itsView.isRefCounted(), "repository must be opened with refcounted=True"

        wx.GetApp().needsUpdateUI = True

    def getWidgetID (self):
        """
        wxWindows needs a integer for a id. Idss between wx.ID_LOWEST
        and wx.ID_HIGHEST are reserved for wxWidgets. Calling wx.NewId
        allocates incremental ids starting at 100. Passing -1 for new IDs
        starting with -1 and decrementing. Some rogue dialogs use IDs
        outside wx.ID_LOWEST and wx.ID_HIGHEST.

        idToBlock is used to associate a block with an Id. Blocks contain
        an attribute, wxId, that allow you to specify a particular id
        to the block. It defaults to 0, which will use an unused unique
        idf -- See Bug #5219
        """
        id = self.wxId
        if id == 0:
            if len (self.freeWXIds) > 0:
                id = self.freeWXIds.pop(0)
            else:
                id = wx.NewId()
                assert id < wx.ID_LOWEST

        assert id > 0

        assert not self.idToBlock.has_key (id)
        self.idToBlock [id] = self
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
        return Block.findBlockByName("MainView")

    @classmethod
    def finishEdits(theClass, onBlock=None):
        """ 
        If the given block, or the focus block if no block given, has a
        saveValue method, call it to write pending edits back.
        """
        if onBlock is None:
            onBlock = Block.getFocusBlock()
        if onBlock is not None:
            saveValueMethod = getattr(type(onBlock), 'saveValue', None)
            if saveValueMethod is not None:
                saveValueMethod(onBlock)
        
    def onShowHideEvent(self, event):
        self.isShown = not self.isShown
        self.synchronizeWidget()
        self.parentBlock.synchronizeWidget()

    def onShowHideEventUpdateUI(self, event):
        event.arguments['Check'] = self.isShown

    def onAddToViewableCollectionEvent(self, event):
        """
        Adds an item to a collection, typically the sidebarCollection, that is viewed
        by the user interface.
        """
        # You either have something in item or implement onNewItem, but not both
        onNewItemMethod = getattr (type (event), "onNewItem", None)
        assert (event.item is not None) ^ (onNewItemMethod is not None)

        collection = getattr (schema.ns ("osaf.app", self.itsView), event.collectionName)
        
        #Scripting expects the event to return the item that were added
        if onNewItemMethod:
            item = onNewItemMethod (event)
        else:
            item = event.item
            if event.copyItems:
                item = item.copy (parent = self.getDefaultParent(self.itsView),
                                  cloudAlias="copying")
        if item is not None:
            assert isinstance(item, ContentCollection) #Currently assumes a UserCollection
            UserCollection(item).ensureColor()

            # Create a unique display name
            if event.disambiguateDisplayName:
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

            # Add to to the approprate sphere, if any
            sphereCollection = getattr(event, "sphereCollection", None)
            if sphereCollection is not None:
                sphereCollection.addSource(item)

            # Optionally select the item in a named block and possibly edit
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
                
                # Let the block know about the preferred kind
                method = getattr(type(blockItem), 'setPreferredKind', None)
                if method is not None:
                    preferredKind = getattr(UserCollection (item), 'preferredKind', False)
                    if preferredKind is not False:
                        method(blockItem, preferredKind)
        return item

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

    def rebuildDynamicBlocks (self):
        """
        The MainViewRoot's lastDynamicBlock: the last block synched
        lastDynamicBlock: C{DynamicBlock}, or C{False} for no previous block,
        or C{True} for forced resync.

        @param self: the new view
        @type self: C{Block}
        """
        def synchToDynamicBlock (block, isChild):
            """
            Function to set and remember the dynamic Block we synch to.
            If it's a child block, it will be used so we must sync, and
            remember it for later.
            If it's not a child, we only need to sync if we had a different
            block last time.
            """
            mainViewRoot = Block.findBlockByName ('MainViewRoot')
            previous = mainViewRoot.lastDynamicBlock
            if isChild:
                mainViewRoot.lastDynamicBlock = block
            elif previous and previous is not block:
                mainViewRoot.lastDynamicBlock = False
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
                isDynamicChildMethod = getattr (type (child), "isDynamicChild", None)
                if isDynamicChildMethod is not None:
                    if candidate is None:
                        candidate = child
                    if isDynamicChildMethod (child):
                        synchToDynamicBlock (child, True)
                        return
            block = block.parentBlock
        # none found, to remove dynamic additions we synch to the Active View
        #assert candidate, "Couldn't find a dynamic child to synchronize with"
        if candidate:
            synchToDynamicBlock (candidate, False)

    def getFrame(self):
        """
        Cruise up the tree of blocks looking for the top-most block that
        has a python attribute, which is the wxWidgets wxFrame window.
        """
        block = self
        while (block.parentBlock):
            block = block.parentBlock
        return block.frame


class DispatchHook (Block):
    """
    Override dispatchEvent and assign hookList to get called each
    time an event is disspatched
    """
    hookList = schema.One("DispatcHookList", otherName='hooks')

    def dispatchEvent (self, event, depth):
        pass


class DispatcHookList (schema.Item):
    hooks = schema.Sequence("DispatchHook", otherName='hookList', defaultValue = [])


class BlockDispatchHook (DispatchHook):
    def dispatchEvent (self, event, depth):
        
        def callProfiledMethod(blockOrWidget, methodName, event):
            """
            Wrap callNamedMethod with a profiler runcall().
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
            Call method named methodName on block or widget.
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
            Call a method on a block or widget or if it doesn't handle it
            try it's parents.
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
            sender = event.arguments['sender']
            if sender is not None:
                title = getattr(sender, 'title', None)
                if title is not None:
                    accel = getattr(sender, 'accel', u'')
                    if len(accel) > 0:
                        title += u'\t' + accel
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
            assert block is not None
            callMethod (block, methodName, event)

        elif dispatchEnum == 'SendToBlockByName':
            block = Block.findBlockByName(event.dispatchToBlockName)
            if not block and event.arguments.has_key('UpdateUI'):
                event.arguments['Enable'] = False
            else:
                callMethod (block, methodName, event)

        elif dispatchEnum == 'BroadcastInsideMyEventBoundary':
            block = event.arguments['sender']
            assert block is not None
            while (not block.eventBoundary and block.parentBlock):
                block = block.parentBlock
                
            broadcast (block,
                       methodName,
                       event,
                       lambda child: (child is not None and 
                                      not child.eventBoundary))

        elif dispatchEnum == 'BroadcastEverywhere':
            broadcast (Block.findBlockByName("MainView"),
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
                blockOrWidget = Block.findBlockByName("MainView")
            bubbleUpCallMethod (blockOrWidget, methodName, event)

        elif dispatchEnum == 'ActiveViewBubbleUp':
            sidebarBPB = Block.findBlockByName ("SidebarBranchPointBlock")
            # This is alecf's hackery, which should be fixed:
            # the active view is typically a splitter, so really
            # we probably want the first child (and even if we
            # don't, the event will bubble up)
            probableMainView = sidebarBPB.childrenBlocks.first().childrenBlocks.first()
            bubbleUpCallMethod (probableMainView, methodName, event)

        elif __debug__:
            assert (False)

        # clean up any accelerator mess left by wx
        if (event.arguments.has_key('Accel') and
            event.arguments.has_key('Text') and
            event.arguments['Text'] != title):
            event.arguments['Text'] += '\t' + event.arguments['Accel']
        if commitAfterDispatch:
            wx.GetApp().UIRepositoryView.commit()


def debugName(thing):
    """
    Debug method to get a useful name for this thing, which can be a
    block or a widget, to use in a logging message.
    """
    if thing is None:
        return '(None)'
    
    if isinstance(thing, Block):
        return getattr(thing, 'blockName', '(unnamed %s)' % thing.__class__.__name__)
    
    if isinstance(thing, BlockEvent):
        return getattr(thing, 'itsName', '(unnamed %s)' % thing.__class__.__name__)
    
    blockItem = getattr(thing, 'blockItem', None)
    if blockItem is not None:
        return '%s on %s' % (thing.__class__.__name__, debugName(blockItem))

    from osaf.framework.attributeEditors import BaseAttributeEditor
    if isinstance(thing, BaseAttributeEditor):
        widget = getattr(thing, 'control', None)
        return '%s on %s' % (thing.__class__.__name__, debugName(widget))

    from osaf.pim import CalendarEventMixin, Note, Reminder
    if isinstance(thing, CalendarEventMixin):
        startTime = getattr(thing, 'startTime', None)
        if startTime and getattr(thing, 'allDay', False):
            timeMsg = "%s allDay" % startTime.date()
        elif startTime and getattr(thing, 'anyTime', False):
            timeMsg = "%s anyTime" % startTime.date()
        else:
            timeMsg = "%s" % startTime
        if getattr(thing, 'rruleset', None):
            recMsg = thing.getMaster() == thing and ", master" \
                   or (", R%s" % thing.recurrenceID)
        else:
            recMsg = ""
        return "%r %s @ %s%s" % (thing.__repr__(), 
            getattr(thing, 'displayName', None), timeMsg, recMsg)

    if isinstance(thing, Note):
        return "%r %s" % (thing.__repr__(),
                          getattr(thing, 'displayName', None))

    if isinstance(thing, Reminder):
        items = ["+%r" % r for r in thing.reminderItems]
        items.extend("-%r" % debugName(r) for r in thing.expiredReminderItems)
        return "%r on [%s]" % (thing.__repr__(), ", ".join(items))

    try:
        return thing.__repr__()
    except:
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

    def instantiateWidget(self):
        return wxRectangularChild(self.parentBlock.widget, self.getWidgetID(),
                                  wx.DefaultPosition, wx.DefaultSize)
 
class dispatchEnumType(schema.Enumeration):
    values = (
        "ActiveViewBubbleUp",
        "BroadcastInsideMyEventBoundary",
        "BroadcastEverywhere",
        "FocusBubbleUp",
        "SendToBlockByName",
        "SendToBlockByReference",
        "SendToSender",
    )

class BlockEvent(schema.Item):
    dispatchEnum = schema.One(dispatchEnumType, initialValue = 'SendToBlockByName')
    dispatchToBlockName = schema.One(schema.Text, initialValue = 'MainView')
    commitAfterDispatch = schema.One(schema.Boolean, initialValue = False)
    destinationBlockReference = schema.One(Block)
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
    def template(theClass, itemName, blockName=None, **attrs):
        """
        Very similar to the default template() routine, except that
        the repository name and blockname are unified by default
        """
        return BlockTemplate(theClass, itemName,
                             blockName=blockName or itemName,
                             **attrs)

class ChoiceEvent(BlockEvent):
    choice = schema.One(schema.Text, required = True)

class ColorEvent(BlockEvent):
    from osaf.pim.structs import ColorType
    color = schema.One(ColorType, required = True)

class KindParameterizedEvent(BlockEvent):
    kindParameter = schema.One(
        schema.TypeReference('//Schema/Core/Kind'),
        defaultValue = None
    )
    schema.addClouds(
        copying = schema.Cloud(byRef=[kindParameter])
    )
    
class NewItemEvent(KindParameterizedEvent):
    """
    Creates a new Item, adds it to a C{collection} and displays it properly.

    If the NewItemEvent implements the C{onNewItem} method it will be called to
    create the item. This is handy if you want to use a dialog to get some
    information to create the item. If C{onNewItem} returns None, no Item will
    be created.

    If you don't implement C{onNewItem} an Item of C{kindParamter} Kind is
    created. If C{kindParamter} is None, a Kind matching the ApplicationBar is
    created, e.g. if you're in Calendar View you'll get a Calendar Item. If
    you're in All you'll get a Note.

    The view in the sidebar is switched to match the kind, e.g. if you create a
    CalendarItem, you'll switch to the Calendar View. If there isn't a
    kind specific view, you'll switch to All view.

    If the C{collection} is None or it's not a UserCollection, the Item will be
    added to the all collection.
    
    If you specify a C{collectionAddEvent} that references an AddToSidebarEvent and
    your C{collection} is not in the Sidebar, it will be used to add your
    C{collection} if it's not in the sidebar.
    """
    collection = schema.One(ContentCollection, defaultValue = None)
    collectionAddEvent = schema.One("BlockEvent", defaultValue = None)
    methodName = schema.One(schema.Text, initialValue = 'onNewItemEvent')
    commitAfterDispatch = schema.One(schema.Boolean, initialValue = True)
    dispatchEnum = schema.One(dispatchEnumType, initialValue = 'ActiveViewBubbleUp')

class AddToViewableCollectionEvent(BlockEvent):
    commitAfterDispatch = schema.One(schema.Boolean, initialValue = True)
    methodName = schema.One(schema.Text, initialValue = 'onAddToViewableCollectionEvent')

    item = schema.One(schema.Item, defaultValue = None)
    collectionName = schema.One(schema.Text, initialValue = "sidebarCollection")
    copyItems = schema.One(schema.Boolean, defaultValue=True)
    selectInBlockNamed = schema.One(schema.Text, initialValue = "Sidebar")
    editAttributeNamed = schema.One(schema.Text)
    disambiguateDisplayName = schema.One(schema.Boolean, defaultValue=True)
    sphereCollection = schema.One(ContentCollection)
    
    schema.addClouds(
        copying = schema.Cloud(byRef=[item,sphereCollection])
    )

AddToSidebarEvent = AddToViewableCollectionEvent
"""
    Adds item to the sidebar. The item must be a collection.

    You can add an item to the sidebar in two different ways: Either add a
    reference to a template item to the C{item} attribute and a copy of
    the template will be added when the event is dispatched. Or implement
    the C{onNewItem} method on your subclass of AddToSidebarEvent and it
    will be called to create the item added to the sidebar. If your method
    returns None then nothing will be added to the sidebar.

    By default the item will be selected and it's displayName will be
    disambiguated, i.e. a "-NN" suffix added to make it unique.

    By setting the preferredKind UserCollection attribute of your collection,
    it will be displayed in a particular application area as follows:

    If preferredKind attribute is absent (the default) then the collection
    will be the current application area.

    If preferredKind attribute is None the collection will be viewed in All

    if preferredKind attribute is the kind associated with another application
    area it will be displayed in that area. For example if preferredKind is

    schema.ns('osaf.pim.calendar.Calendar', theView).CalendarEventMixin.getKind (theView)

    it will be displayed in the calendar area.

    For more advanced options see AddToViewableCollectionEvent.
"""

class NewBlockWindowEvent(BlockEvent):
    methodName = schema.One(schema.Text, initialValue = 'onNewBlockWindowEvent')
    treeOfBlocks = schema.One (Block, required = True)

    schema.addClouds(
        copying = schema.Cloud(byRef=[treeOfBlocks])
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
    Template class for easy domain-specific item creation.
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
