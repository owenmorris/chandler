
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.util.PersistentCollection import PersistentCollection


class PersistentDict(dict, PersistentCollection):
    'A persistence aware dict, tracking changes into a dirty bit.'

    def __init__(self, item, **kwds):

        dict.__init__(self)
        PersistentCollection.__init__(self, item)

        if kwds:
            self.update(kwds)

    def __delitem__(self, key):

        super(PersistentDict, self).__delitem__(key)
        self._setDirty()

    def __setitem__(self, key, value):

        super(PersistentDict, self).__setitem__(key, value)
        self._setDirty()

    def clear(self):

        super(PersistentDict, self).clear()
        self._setDirty()

    def update(self, dictionary):

        super(PersistentDict, self).update(dictionary)
        self._setDirty()

    def setdefault(self, key, value=None):

        if not key in self:
            self._setDirty()

        return super(PersistentDict, self).setdefault(key, value)

    def popitem(self):

        super(PersistentDict, self).popitem()
        self._setDirty()
