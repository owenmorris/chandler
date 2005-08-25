__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from osaf.pim import AbstractCollection

from i18n import OSAFMessageFactory as _

#XXX[i18n] this file needs to have displayName converted to _()

"""
At the moment, this is just a bunch of helper routines to find, fill,
and empty the trash collection.

After the ItemCollection landing, Trash will probably be a subclass of
ListCollection and there will just be one helper class to find the
trash folder. MoveItemToTrash and EmptyTrash should be methods on that
class

After OOTB collections are no longer copied to the soup, FindTrashCollection
will be tremendously simplified.
"""

def EmptyTrash(view):
    trash = schema.ns('osaf.app',view).TrashCollection
    for item in trash:
        # actually kill it from the repository!
        # should remove it from all collections, etc
        item.delete()

def MoveItemToTrash(item, trash=None):
    """
    Moves the item from all collections into the trash collection, and sets
    the deleted attribute on the item
    """

    # add to trash first, and skip trash later, in case the item is already
    # in the trash
    if not trash:
        trash = schema.ns('osaf.app',item.itsView).TrashCollection
        
    trash.add(item)

    # now remove it from all other collections
    for collection in item.itemCollectionInclusions:
        if collection is not trash:
            # perhaps we should skip collections that have a 'source'
            # attribute?
            try:
                collection.remove(item)
            except AttributeError:
                # not all collections support remove()
                pass


def RemoveItemFromCollection(item, collection):
    """
    Smart routine to remove an item from a collection, and optionally
    move it to the trash if this item appears only in this collection,
    and not any other user-defined collections
    """

    # first check for other collections. This is where we will eventually
    # handle deleting within the same 'sphere' of collections (i.e. mineness)
    # for now, we just check itemCollectionInclusions
    isInOtherCollections = False
    
    # the one problem right now is that often the "other" collection is
    # some sort of internal collection - we really want to know,
    # is this the only /sidebar/ collection that it appears in?
    for otherCollection in item.itemCollectionInclusions:
        if (otherCollection != collection and 
            not getattr(otherCollection, 'renameable', True)):
            isInOtherCollections = True
            break

    if isInOtherCollections:
        collection.remove(item)
    else:
        MoveItemToTrash(item)

