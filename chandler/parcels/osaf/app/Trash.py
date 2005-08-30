__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from osaf.pim import AbstractCollection, ListCollection
from application import schema

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
        # this will automatically remove it from all collections, etc
        item.delete()

def isUserCollection(collection):
    """
    really simplistic for now - may eventually become mine/ismine
    detection, etc
    """
    return (isinstance(collection, ListCollection) and
            getattr(collection, 'renameable', True))

def GetUserCollections(view):
    sidebarCollections = \
        schema.ns('osaf.views.main', view).sidebarItemCollection
    return [c for c in sidebarCollections if isUserCollection(c)]

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
    userCollections = GetUserCollections(item.itsView)
    for collection in userCollections:
        try:
            collection.remove(item)
        except (AttributeError, KeyError):
            # ignore collections without .remove, and collections that
            # don't contain item
            pass
            
def RemoveItemsFromCollection(items, collection):
    """
    Smart routine to remove an item from a collection, and optionally
    move it to the trash if this item appears only in this collection,
    and not any other user-defined collections
    """

    # first check for other collections. This is where we will eventually
    # handle deleting within the same 'sphere' of collections (i.e. mineness)
    # for now, we just check user collections
    isInOtherCollections = False
    
    userCollections = GetUserCollections(collection.itsView)

    for item in items:
        for userCollection in userCollections:
            if (userCollection != collection and
                item in userCollection):
                isInOtherCollections = True
                break

        if isInOtherCollections:
            collection.remove(item)
        else:
            MoveItemToTrash(item)
