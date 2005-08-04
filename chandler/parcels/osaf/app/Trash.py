__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from osaf.contentmodel.ItemCollection import ItemCollection

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
    trash = FindTrashCollection(view)
    for item in trash:
        # actually kill it from the repository!
        # should remove it from all collections, etc
        item.delete()

def MoveItemToTrash(item, view, trash=None):
    """
    Moves the item from all collections into the trash collection, and sets
    the deleted attribute on the item
    """

    # add to trash first, and skip trash later, in case the item is already
    # in the trash
    if not trash:
        trash = FindTrashCollection(view)
        
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

def IsTrashCollection(collection):
    """
    This is a nasty hack until we stop copying the Trash into the soup
    Right now its very i18n unfriendly for example, relying on the name being
    'Trash'
    """
    try:

        # i18n alert - I know this is totally wrong, this is just a stub!
        if collection.displayName != _('Trash') or \
               getattr(collection,'renameable', True):
            return False

        # walk up the path to find a sidebar. If any of this path
        # walking fails, then this isn't the collection and we'll
        # catch it later
        sidebar = collection.itemCollectionInclusions.first().contentsOwner.first()
        
        # rendered sidebar mean its the current trash. yay.
        if (sidebar.widget):
            return True
    except AttributeError, e:
        # any errors, it not it.
        return False
    return False
    
def FindTrashCollection(view):
    """
    this is a really ugly hack - basically we have to iterate through
    all ItemCollections until we find the right one
    when the special collections stop being copied into the soup, this
    will just look like:
    return schema.ns("osaf.app", view).trash
    """
    for collection in ItemCollection.iterItems(view):
        if IsTrashCollection(collection):
            return collection
    assert False, "No Trash collection!"
