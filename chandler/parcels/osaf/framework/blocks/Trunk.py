__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys
import application.Globals as Globals
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
from repository.item.Item import Item

"""
Trunk.py - Classes for dynamically substituting child trees-of-blocks.

The idea is that you've got a block that wants different sets of child blocks substituted within itself,
based on some key (like a content item to be displayed). The block inherits from this TrunkParentBlock
class; whenever wxSynchronizeWidget happens, the appropriate set of child blocks will be swapped in. This
mechanism is managed by a TrunkDelegate object, which can be subclassed and/or configured from parcel XML
to customize its behavior.
"""

class wxTrunkParentBlock(ContainerBlocks.wxBoxContainer):
    """ 
    A widget block that gives its TrunkParentBlock a chance to change 
    the tree of blocks within it. 
    """
    def wxSynchronizeWidget(self, *arguments, **keywords):
        if self.blockItem.isShown:
            self.blockItem.installTreeOfBlocks()
        super(wxTrunkParentBlock, self).wxSynchronizeWidget(*arguments, **keywords)
    
class TrunkParentBlock(ContainerBlocks.SelectionContainer):
    # @@@ Will be a BoxContainer once SelectionContainer is obsolete.
    """
    A block that can swap in different sets of child blocks ("trunks") based
    on its detailContents. It uses a TrunkDelegate to do the heavy lifting.
    """    
    def instantiateWidget(self):
       widget = wxTrunkParentBlock(self.parentBlock.widget)
       widget.SetSizer(self.createSizer())
       return widget
    
    def installTreeOfBlocks(self):
        """ Maybe replace our children with a trunk of blocks appropriate for our content """
        newView = None
        try:
            # @@@ Should be this:
            # detailContents = self.detailContents
            # -- but until SelectionContainer goes away, we do this:
            detailContents = self.selectedItem()
        except AttributeError:
            detailContents = None
        else:
            if detailContents is not None:
                newView = self.trunkDelegate.getTrunkForItem(detailContents)
            
        oldView = self.childrenBlocks.first()
        if not newView is oldView:
            self.childrenBlocks = []

            if oldView is not None:
                oldView.unRender()

            if newView is not None:
                self.childrenBlocks.append(newView)
                
                # @@@ For now, sends SelectItem, until the DV can be updated to
                # use onContentsChanged (or whatever)... this should be: 
                # newView.PostEventByName("SelectItem", {'item': detailContents})
                # It's surprising the amount of work necessary to create an event --
                # all because it's an Item
                parent = Globals.repository.findPath ('//userdata')
                kind = Globals.repository.findPath('//parcels/osaf/framework/blocks/BlockEvent')
                event = Block.BlockEvent (None, parent, kind)
                try:
                    event.arguments = {'item': detailContents }
                    newView.onSelectItemEvent (event)
                finally:
                    event.delete()
                
                newView.render()

                sizer = self.widget.GetSizer()
                sizer.Clear()
                sizer.Add(newView.widget,
                          newView.stretchFactor, 
                          Block.wxRectangularChild.CalculateWXFlag (newView), 
                          Block.wxRectangularChild.CalculateWXBorder (newView))
            
            self.widget.Layout()

class TrunkDelegate(Item):
    """
    A mechanism to map an item to a view: call its getTrunkForItem(item)
    to get the view for that item.

    The default implementation is suitable when the item the view to be used;
    it'll be returned as-is (except that a copy will be made if the original's
    in the read-only part of the repository).
    """
    def getTrunkForItem(self, item):
        """ 
        Given an item, return the view to be used to display it.

        Can be overridden if you don't want the default behavior, which is to 
        cache the views, keyed by a value returned by _mapItemToCacheKey. Misses 
        are handled by _makeTrunkForItem.
        """
        trunk = None
        keyItem = self._mapItemToCacheKey(item)
        if not keyItem is None:
            # @@@ For now, we actually use the UUID of the item as the key.
            # It's be much better to use the item itself, but the repository doesn't
            # support this yet.
            keyUUID = keyItem.itsUUID
            try:
                trunkUUID = self.keyUUIDToTrunkUUID[keyUUID]
            except KeyError:
                trunk = self._makeTrunkForCacheKey(keyItem)
                self.keyUUIDToTrunkUUID[keyItem] = trunk.itsUUID
            else:
                trunk = Globals.repository.findUUID(trunkUUID)
        return trunk

    def _mapItemToCacheKey(self, item):
        """ 
        Given an item, determine the item to be used as the cache key.
        Can be overridden; defaults to using the item itself
        """
        return item

    def _makeTrunkForCacheKey(self, keyItem):
        """ 
        Handle a cache miss; build and return a tree-of-blocks for this keyItem. 
        Defaults to using the keyItem itself, copying it if it's in the read-only
        part of the repository. (This behavior fits with the simple case where
        the items are views.)
        """
        return self._copyItem(keyItem, onlyIfReadOnly=True)

    def _copyItem(self, item, onlyIfReadOnly=False):
        """
        Handy utility: Return a copy of this item using its default cloud.
        If onlyIfReadOnly, we'll return the item as-is if it's already in the
        writeable part of the repository.
        """
        # Look up the soup in the repository once per run.
        try:
            userData = self.userData
        except AttributeError:
            userData = Globals.repository.findPath('//userdata')
            self.userData = userData

        if onlyIfReadOnly and item.parent == userData:
            result = item
        else:
            # @@@ BJS Morgen has opined that "default" is a bad name for a cloud; use "copy" instead?
            result = item.copy(parent = userData, cloudAlias="default")
            
        return result


# @@@BJS: For John, a sample delegate that uses an itemcollection view
# if the item is an ItemCollection (the delegate block needs an itemCollectionView 
# attribute added), or uses the item itself if it's a block (making a copy if
# it's not in the soup).
class SampleSidebarTrunkDelegate(TrunkDelegate):
    def _mapItemToCacheKey(self, item):
        if isinstance(item, ItemCollection):
            result = self.itemCollectionView
        else:
            assert isinstance(item, Block)
            result = self._copyItem(item, onlyIfReadOnly=True)
