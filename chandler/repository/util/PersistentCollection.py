
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class PersistentCollection(object):
    '''A persistence aware collection, tracking changes into a dirty bit.

    This class is abstract and is to be used together with a concrete
    collection class such as list or dict.'''

    def __init__(self, item):

        super(PersistentCollection, self).__init__()

        self._dirty = False
        self._item = item

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, "Collection already owned by %s" %(self._item)

        self._item = item
        for value in self.itervalues():
            if isinstance(value, PersistentCollection):
                value._setItem(item)

    def _setDirty(self):

        if not self._dirty and self._item:
            self._dirty = True
            self._item.setDirty()

