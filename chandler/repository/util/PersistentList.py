
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class PersistentList(list):
    'A persistence aware list, tracking changes into a dirty bit.'

    def __init__(self, item, *args):

        super(PersistentList, self).__init__()

        self._dirty = False
        self._item = item

        if args:
            self.extend(args)

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, "List already owned by %s" %(self._item)

        self._item = item
        for value in self:
            if isinstance(value, PersistentList):
                value._setItem(item)

    def _setDirty(self):

        if not self._dirty and self._item:
            self._dirty = True
            self._item.setDirty()

    def __setitem__(self, index, value):

        super(PersistentList, self).__setitem__(index, value)
        self._setDirty()

    def __delitem__(self, index):

        super(PersistentList, self).__delitem__(index)        
        self._setDirty()

    def __setslice__(self, start, end, value):
        
        super(PersistentList, self).__setslice__(start, end, value)
        self._setDirty()

    def __delslice__(self, start, end):

        super(PersistentList, self).__delslice__(start, end)
        self._setDirty()

    def __iadd__(self, value):

        super(PersistentList, self).__iadd__(value)
        self._setDirty()

    def __imul__(self, value):

        super(PersistentList, self).__imul__(value)
        self._setDirty()

    def append(self, value):

        super(PersistentList, self).append(value)
        self._setDirty()

    def insert(self, index, value):

        super(PersistentList, self).insert(index, value)
        self._setDirty()

    def pop(self, index = -1):

        try:
            return super(PersistentList, self).pop(index)
        finally:
            self._setDirty()

    def remove(self, value):

        super(PersistentList, self).remove(value)
        self._setDirty()

    def reverse(self):

        super(PersistentList, self).reverse(value)
        self._setDirty()

    def sort(self, *args):

        super(PersistentList, self).sort(*args)
        self._setDirty()

    def extend(self, value):

        super(PersistentList, self).extend(value)
        self._setDirty()
