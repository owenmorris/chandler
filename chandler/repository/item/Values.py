
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Access import Permission, AccessDeniedError
from repository.item.PersistentCollections import PersistentCollection


class Values(dict):

    def __init__(self, item):

        super(Values, self).__init__()
        self._setItem(item)

    def __getitem__(self, key):

        if self._getAccess(Permission.READ):
            return super(Values, self).__getitem__(key)

        raise AccessDeniedError, "%s.%s: 0x%x" %(self._item.itsPath, key,
                                                 Permission.READ)

    def _getAccess(self, permission):

        return True

    def _setItem(self, item):

        self._item = item

    def _copy(self, item):

        values = type(self)(item)
        for name, value in self.iteritems():
            if isinstance(value, PersistentCollection):
                value = value._copy(item, name, value._companion)
            elif isinstance(value, ItemValue):
                value = value._copy(item, name)

            values[name] = value

        return values

    def _getItem(self):

        return self._item

    def __setitem__(self, key, value):

        if self._getAccess(Permission.WRITE):
            if self._item is not None:
                self._item.setDirty(attribute=key)

            super(Values, self).__setitem__(key, value)

        else:
            raise AccessDeniedError, "%s.%s: 0x%x" %(self._item.itsPath, key,
                                                     Permission.WRITE)

    def __delitem__(self, key):

        if self._getAccess(Permission.REMOVE):
            if self._item is not None:
                self._item.setDirty(attribute=key)

            super(Values, self).__delitem__(key)

        else:
            raise AccessDeniedError, "%s.%s: 0x%x" %(self._item.itsPath, key,
                                                     Permission.REMOVE)

    def _unload(self):

        self.clear()
        

class References(Values):

    def _setItem(self, item):

        for value in self.itervalues():
            value._setItem(item)

        self._item = item

    def _copy(self, item):

        references = type(self)(item)
        for name, value in self.iteritems():
            copyPolicy = item.getAttributeAspect(name, 'copyPolicy')
            if copyPolicy == 'copy':
                references[name] = value._copy(item, name)
                
        return references

    def __setitem__(self, key, value, *args):

        super(References, self).__setitem__(key, value)

    def _unload(self):

        for value in self.itervalues():
            value._unload(self._item)


class ItemValue(object):
    'A superclass for values that are owned by an item.'
    
    def __init__(self):

        self._item = None
        self._attribute = None
        self._dirty = False

    def _setItem(self, item, attribute):

        if self._item is not None and self._item is not item:
            raise ValueError, 'item attribute value %s is already owned by another item %s' %(self, self._item)
        
        self._item = item
        if self._dirty:
            item.setDirty()

        self._attribute = attribute

    def _getItem(self):

        return self._item

    def _getAttribute(self):

        return self._attribute

    def _setDirty(self):

        if not self._dirty:
            self._dirty = True
            item = self._item
            if item is not None:
                item.setDirty(attribute=self._attribute, dirty=item.VDIRTY)

    def _copy(self, item, attribute):

        raise NotImplementedError, 'ItemValue._copy is abstract'
