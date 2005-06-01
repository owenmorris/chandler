__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.ContainerBlocks as ContainerBlocks
from repository.item.Item import Item
import osaf.contentmodel.ContentModel as ContentModel
import logging

"""
Trunk.py - Classes for dynamically substituting child trees-of-blocks.

The idea is that you've got a block that wants different sets of child blocks substituted within itself,
based on some key (like a content item to be displayed). The block inherits from this TrunkParentBlock
class; whenever wxSynchronizeWidget happens, the appropriate set of child blocks will be swapped in. This
mechanism is managed by a TrunkDelegate object, which can be subclassed and/or configured from parcel XML
to customize its behavior.
"""

logger = logging.getLogger('trunk')
logger.setLevel(logging.INFO)

class wxTrunkParentBlock(ContainerBlocks.wxBoxContainer):
    """ 
    A widget block that gives its TrunkParentBlock a chance to change 
    the tree of blocks within it. 
    """
    def wxSynchronizeWidget(self):
        if self.blockItem.isShown:
            self.blockItem.installTreeOfBlocks()
        super(wxTrunkParentBlock, self).wxSynchronizeWidget()
    
class TrunkParentBlock(ContainerBlocks.BoxContainer):
    """
    A block that can swap in different sets of child blocks ("trunks") based
    on its detailContents. It uses a TrunkDelegate to do the heavy lifting.
    """    
    def instantiateWidget(self):
       return wxTrunkParentBlock(self.parentBlock.widget)
    
    def onSelectItemEvent (self, event):
        self.TPBSelectedItem = event.arguments['item']
        """
          Occasionally a block that contains a TrunkParentBlock will send
        a selectItem event to set TPBSelectedItem when it can't be set in parcel
        XML (for example when it isn't yet created). This can happen before
        the widget is actually created so we'll ignore this first call to 
        wxSynchronizeWidget since it will get called later.
        """
        try:
            widget = self.widget
        except AttributeError:
            pass
        else:
            widget.wxSynchronizeWidget ()

    def installTreeOfBlocks(self):
        """
          If necessary, replace our children with a trunk of blocks appropriate for our content
        """
        TPBSelectedItem = self.TPBSelectedItem
        (keyItem, rerender) = self.trunkDelegate._mapItemToCacheKeyItem(TPBSelectedItem)
        newView = self.trunkDelegate.getTrunkForKeyItem(keyItem)
        if keyItem is None:
            TPBDetailItem = None
            newContents = None
        else:
            """
              Seems like we should always mark new views with an event boundary
            """
            assert newView.eventBoundary
            TPBDetailItem = self.trunkDelegate._getContentsForTrunk (newView, TPBSelectedItem, keyItem)
            newContents = TPBDetailItem is not self.TPBDetailItem
            rerender = rerender or newContents or not hasattr (newView, "widget")

        self.TPBDetailItem = TPBDetailItem
        oldView = self.childrenBlocks.first()

        if (newView is not oldView) or rerender:
            logger.debug("changing tree to display %s", TPBSelectedItem)
            if oldView is not None:
                oldView.unRender()

            self.childrenBlocks = []

            if newView is not None:
                if (newView is not oldView) or newContents:
                    newView.postEventByName ("SetContents", {'item':TPBDetailItem})
                self.childrenBlocks.append(newView)
                newView.render()
        else:
            logger.debug("NOT changing tree to display %s", TPBSelectedItem)


class TrunkDelegate(Item):
    """
    A mechanism to map an item to a view: call its getTrunkForKeyItem(item)
    to get the view for that item.

    The default implementation is suitable when the item the view to be used;
    it'll be returned as-is (except that a copy will be made if the original's
    in the read-only part of the repository).
    """
    def getTrunkForKeyItem(self, keyItem):
        """ 
        Given an item, return the view to be used to display it.

        Can be overridden if you don't want the default behavior, which is to 
        cache the views, keyed by a value returned by _mapItemToCacheKeyItem. Misses 
        are handled by _makeTrunkForItem.
        """
        trunk = None
        if not keyItem is None:
            keyUUID = keyItem.itsUUID
            try:
                trunk = self.keyUUIDToTrunk[keyUUID]
            except KeyError:
                trunk = self._makeTrunkForCacheKey(keyItem)
                self.keyUUIDToTrunk[keyUUID] = trunk
        return trunk

    def _mapItemToCacheKeyItem(self, item):
        """ 
          Given an item, determine the item to be used as the cache key, and a boolean,
        which if True forces the view to be rerendered, otherwise it will only
        be rerendered if the view or it's contents change.
          Can be overridden; defaults to using the item itself.
        """
        return item, False

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
            userData = self.findPath('//userdata')
            self.userData = userData

        if onlyIfReadOnly and item.itsParent == userData:
            result = item
        else:
            # @@@ BJS Morgen has opined that "default" is a bad name for a cloud; use "copy" instead?
            result = item.copy(parent = userData, cloudAlias="default")
            
        return result

    def _getContentsForTrunk(self, trunk, item, keyItem):
        """ 
        Given a trunk, item and keyItem, return the contents for the trunk.
        """
        return item

