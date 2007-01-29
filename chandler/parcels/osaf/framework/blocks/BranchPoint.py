#   Copyright (c) 2005-2006 Open Source Applications Foundation
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

import sys
from Block import Block, IgnoreSynchronizeWidget, debugName
from ContainerBlocks import wxBoxContainer, BoxContainer
from chandlerdb.item.c import isitem
from application import schema
import wx
import logging

"""
Classes for dynamically substituting child trees-of-blocks.

The idea is that you've got a block that wants different sets of child blocks
substituted within itself, based on some key (like a content item to be
displayed). The block inherits from this BranchPointBlock class; whenever
synchronizeWidget happens, the appropriate set of child blocks will be swapped
in. This mechanism is managed by a BranchPointDelegate object, which can be
subclassed and/or configured from parcel XML to customize its behavior.
"""

logger = logging.getLogger(__name__)

class BranchSubtree(schema.Annotation):
    """
    A mapping between an Item and the list of top-level blocks ('rootBlocks')
    that should appear when an Item inheriting from that Kind is displayed.
    Each rootBlock entry should have its 'position' attribute specified, to
    enable it to be sorted with other root blocks.)
    """
    schema.kindInfo(annotates=schema.Kind)
    rootBlocks = schema.Sequence(Block, inverse=schema.Sequence())

class StampBranchSubtree(BranchSubtree):
    """
    A mapping between an Item and the list of top-level blocks ('rootBlocks')
    that should appear when an Item inheriting from that Kind is displayed.
    Each rootBlock entry should have its 'position' attribute specified, to
    enable it to be sorted with other root blocks.)
    """
    schema.kindInfo(annotates=schema.Item)

class wxBranchPointBlock(wxBoxContainer):
    """
    A widget block that gives its BranchPointBlock a chance to change
    the tree of blocks within it.
    """
    def wxSynchronizeWidget(self, useHints=False):
        if self.blockItem.isShown:
            self.blockItem.installTreeOfBlocks()
        super(wxBranchPointBlock, self).wxSynchronizeWidget()

from Styles import ColorStyle

class BranchPointBlock(BoxContainer):
    """
    A block that can swap in different sets of child blocks (branch point
    "subtrees") based on its detailContents. It uses a BranchPointDelegate to
    do the heavy lifting.
    """
    colorStyle = schema.One(ColorStyle)

    delegate = schema.One(
        required = True
    )
    detailItem = schema.One(
        schema.Item, defaultValue = None, inverse=schema.Sequence()
    )

    detailItemCollection = schema.One(
        schema.Item, defaultValue = None
    )

    selectedItem = schema.One(
        schema.Item, defaultValue = None, inverse=schema.Sequence()
    )

    setFocus = schema.One (schema.Boolean, defaultValue = False)

    schema.addClouds(
        copying = schema.Cloud(
            byRef = [delegate,colorStyle,detailItem,selectedItem]
        )
    )

    def instantiateWidget(self):
        return wxBranchPointBlock(self.parentBlock.widget)

    def onSelectItemsEvent (self, event):
        # for the moment, multiple selection means, "select nothing"
        # i.e. multiple selection in the summary view means selecting
        # nothing in the detail view

        # eventually we might want selectedItem to be an iterable
        # of some kind
        items = event.arguments['items']
        if len(items)==1:
            self.selectedItem = items[0]
        else:
            self.selectedItem = None

        self.detailItemCollection = \
            self.delegate.getContentsCollection(self.selectedItem,
                                                event.arguments.get('collection'))
        widget = getattr (self, 'widget', None)
        if widget is not None:
            # eventually results in installTreeOfBlocks()
            widget.wxSynchronizeWidget ()

    def installTreeOfBlocks(self):
        """
        If necessary, replace our children with a tree of blocks appropriate
        for our content.

        Four steps:
        1) map the selected item to a cache key
        2) Use the cache key to get the appropriate tree of blocks
        3) Set contents on that new tree of blocks
        4) Render the tree of blocks
        """

        # Get a cache key from self.selectedItem using the delegate
        hints = {}
        keyItem = self.delegate._mapItemToCacheKeyItem(
            self.selectedItem, hints)

        # Ask the delegate for the right tree of blocks

        # (actually there is only implmentation of this function,
        # should probably be rolled into BranchParentBlock eventually)
        newView = self.delegate.getBranchForKeyItem(keyItem)
        if keyItem is None:
            detailItem = None
        else:
            """
              Seems like we should always mark new views with an event boundary
            """
            assert newView is None or newView.eventBoundary
            detailItem = self.delegate._getContentsForBranch(newView,
                                                             self.selectedItem,
                                                             keyItem)

        detailItemChanged = self.detailItem is not detailItem

        self.detailItem = detailItem

        # Set contents on the root of the tree of blocks

        # For bug 4269 in 0.6: If we've been given a contents collection,
        # it's so that we can put our detailItem in it, to get a notification
        # when that item is deleted. Update the collection if necessary.
        contents = getattr(self, 'contents', None)
        if (contents is not None and contents.first() is not detailItem):
            contents.clear()
            if detailItem is not None:
                contents.add(self.detailItem)

        oldView = self.childrenBlocks.first()
        treeChanged = newView is not oldView

        logger.debug("installTreeOfBlocks %s: treeChanged=%s, detailItemChanged=%s, detailItem=%s",
                     debugName(self), treeChanged, detailItemChanged, debugName(detailItem))

        # Render or rerender as necessary
        if treeChanged:
            # get rid of the old view
            if oldView is not None:
                # We need to get rid of our sizer that refers to widgets
                # that are going to get deleted
                assert hasattr (self, "widget")
                self.widget.SetSizer (None)
                oldView.unRender()

            # attach the new view
            self.childrenBlocks = []
            if newView is not None:
                self.childrenBlocks.append(newView)

        if newView is not None:
            def Rerender():
                if (detailItemChanged or
                    treeChanged or
                    hints.get ("sendSetContents", False)):
                    newView.postEventByName("SetContents", {
                        'item': detailItem,
                        'collection': self.detailItemCollection})

                if not hasattr (newView, "widget"):
                    newView.render()
                elif detailItemChanged or treeChanged:
                    resyncMethod = getattr(newView, 'synchronizeWidgetDeep', None)
                    if resyncMethod is not None:
                        resyncMethod()

                if self.setFocus:
                    newView.postEventByName("SetFocus", {})

            IgnoreSynchronizeWidget(False, Rerender)


class BranchPointDelegate(schema.Item):
    """
    A mechanism to map an item to a view: call its getBranchForKeyItem(item)
    to get the view for that item.

    The default implementation is suitable when the item the view to be used;
    it'll be returned as-is.

    Issues:
     - We'd like to use itemrefs as keys, so reference tracking & cleanup
       would work.
    """

    blocks = schema.Sequence(
        BranchPointBlock,
        inverse = BranchPointBlock.delegate,
        required = True,
    )

    keyUUIDToBranch = schema.Mapping(Block, initialValue = {})

    def deleteCopiesFromCache(self):
        defaultParent = self.getDefaultParent (self.itsView)
        # create the list before iterating because we're modifing the dictionary in the loop
        for key, item in [tuple for tuple in self.keyUUIDToBranch.iteritems()]:
            if isitem(item) and item.itsParent == defaultParent:
                del self.keyUUIDToBranch [key]
                item.delete (cloudAlias="copying")

    def getBranchForKeyItem(self, keyItem):
        """
        Given an item, return the view to be used to display it.

        Can be overridden if you don't want the default behavior, which is to
        cache the views, keyed by a value returned by _mapItemToCacheKeyItem. Misses
        are handled by _makeBranchForItem.
        """
        branch = None
        if not keyItem is None:
            keyUUID = keyItem.itsUUID
            branch = self.keyUUIDToBranch.get (keyUUID, None)
            if branch is None:
                branch = self._makeBranchForCacheKey(keyItem)
                self.keyUUIDToBranch[keyUUID] = branch
        return branch

    def _mapItemToCacheKeyItem(self, item, hints):
        """
        Given an item, determine the item to be used as the cache key.
        Can be overridden; defaults to using the item itself. hints is
        a dictionary that includes domain specific information. See
        the other implementations of _mapItemToCacheKeyItem for more
        information.
        """
        return item

    def _makeBranchForCacheKey(self, keyItem):
        """
        Handle a cache miss; build and return a tree-of-blocks for this keyItem.
        Defaults to using the keyItem itself, copying it if it's in the read-only
        part of the repository. (This behavior fits with the simple case where
        the items are views.)
        """
        return keyItem

    def _copyItem(self, item, onlyIfReadOnly=False):
        """
        Handy utility: Return a copy of this item using its default cloud.
        If onlyIfReadOnly, we'll return the item as-is if it's already in the
        writeable part of the repository.
        """
        defaultParent = item.getDefaultParent (item.itsView)
        if onlyIfReadOnly and item.itsParent == defaultParent:
            result = item
        else:
            result = item.copy(parent = defaultParent, cloudAlias="copying")

        return result

    def _getContentsForBranch(self, branch, item, keyItem):
        """
        Given a branch, item and keyItem,
        return the contents for the branch.
        """
        return item


    def getContentsCollection(self, item, collection):
        """
        Get the actual parent collection used
        """
        return collection
