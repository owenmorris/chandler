
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import repository.item.Item
import repository.item.Values 

from repository.util.UUID import UUID
from repository.util.SingleRef import SingleRef


class ReadOnlyError(ValueError):
    "thrown when a read-only collection is modified"
    

class PersistentCollection(object):
    '''A persistence aware collection, tracking changes into a dirty bit.

    This class is abstract and is to be used together with a concrete
    collection class such as list or dict.'''

    def __init__(self, item, attribute, companion):

        super(PersistentCollection, self).__init__()

        self._readOnly = False
        self.__setItem(item, attribute, companion)

    def setReadOnly(self, readOnly=True):

        self._readOnly = readOnly

    def isReadOnly(self):

        return self._readOnly

    def _setItem(self, item, attribute, companion):

        if self._item is not None and self._item is not item:
            raise ValueError, "Collection already owned by %s" %(self._item)

        self.__setItem(item, attribute, companion)
        for value in self.itervalues():
            if isinstance(value, PersistentCollection):
                value._setItem(item, attribute, companion)
            elif isinstance(value, repository.item.Values.ItemValue):
                value._setItem(item, attribute)

    def __setItem(self, item, attribute, companion):
        
        self._item = item
        self._attribute = attribute
        self._companion = companion

    def _setDirty(self):

        if self._readOnly:
            raise ReadOnlyError, 'collection is read-only'

        item = self._item
        if item is not None:
            item.setDirty(item.VDIRTY, self._attribute, item._values)

    def _prepareValue(self, value, setDirty=True):

        if isinstance(value, PersistentCollection):
            value = value._copy(self._item, self._attribute, self._companion,
                                'copy', lambda x, other, z: other)
        elif isinstance(value, list):
            persistentValue = PersistentList(self._item, self._attribute,
                                             self._companion)
            persistentValue.extend(value, setDirty)
            value = persistentValue
        elif isinstance(value, dict):
            persistentValue = PersistentDict(self._item, self._attribute,
                                             self._companion)
            persistentValue.update(value, setDirty)
            value = persistentValue
        elif isinstance(value, repository.item.Item.Item):
            value = SingleRef(value._uuid)
        elif isinstance(value, repository.item.Values.ItemValue):
            value._setItem(self._item, self._attribute)

        return value

    def _restoreValue(self, value):

        if self._item is not None and isinstance(value, SingleRef):
            uuid = value.itsUUID
            if self._companion is None:
                return self._item.find(uuid)
            else:
                return self._item.getAttributeValue(self._companion).get(uuid)

        return value

    def _storeValue(self, value):

        if self._companion is not None:
            if isinstance(value, repository.item.Item.Item):
                if not self._item.hasValue(self._companion, value):
                    self._item.addValue(self._companion, value)

    def _iterItems(self, items=None):

        if self._companion is not None:
            for item in self._item.getAttributeValue(self._companion):
                yield item
        else:
            if items is None:
                items = {}
            for value in self._itervalues():
                if isinstance(value, SingleRef):
                    value = self._restoreValue(value)
                    if value is not None:
                        uuid = value._uuid
                        if uuid not in items:
                            items[uuid] = value
                            yield value
                elif isinstance(value, PersistentCollection):
                    for v in value._iterItems(items):
                        yield v


class PersistentList(list, PersistentCollection):
    'A persistence aware list, tracking changes into a dirty bit.'

    def __init__(self, item, attribute, companion):

        list.__init__(self)
        PersistentCollection.__init__(self, item, attribute, companion)

    def _copy(self, item, attribute, companion, copyPolicy, copyFn):

        copy = type(self)(item, attribute, companion)
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       default='copy')

        for value in self:
            if isinstance(value, repository.item.Item.Item):
                value = copyFn(item, value, policy)
                if value is not None:
                    copy.append(value, False)
            elif isinstance(value, PersistentCollection):
                copy.append(value._copy(item, attribute, companion,
                                        copyPolicy, copyFn), False)
            else:
                copy.append(value, False)

        return copy

    def __setitem__(self, index, value):

        self._storeValue(value)
        value = self._prepareValue(value)
        super(PersistentList, self).__setitem__(index, value)
        self._setDirty()

    def __delitem__(self, index):

        super(PersistentList, self).__delitem__(index)        
        self._setDirty()

    def __setslice__(self, start, end, value):

        for v in value:
            self._storeValue(v)
        value = [self._prepareValue(v) for v in value]
        super(PersistentList, self).__setslice__(start, end, value)
        self._setDirty()

    def __delslice__(self, start, end):

        super(PersistentList, self).__delslice__(start, end)
        self._setDirty()

    def __iadd__(self, value):

        for v in value:
            self._storeValue(v)
        value = [self._prepareValue(v) for v in value]
        super(PersistentList, self).__iadd__(value)
        self._setDirty()

    def __imul__(self, value):

        super(PersistentList, self).__imul__(value)
        self._setDirty()

    def append(self, value, setDirty=True):

        self._storeValue(value)
        value = self._prepareValue(value)
        super(PersistentList, self).append(value)

        if setDirty:
            self._setDirty()

    def insert(self, index, value):

        self._storeValue(value)
        value = self._prepareValue(value)
        super(PersistentList, self).insert(index, value)
        self._setDirty()

    def pop(self, index=-1):

        value = super(PersistentList, self).pop(index)
        value = self._restoreValue(value)
        self._setDirty()

        return value

    def remove(self, value):

        value = self._prepareValue(value)
        super(PersistentList, self).remove(value)
        self._setDirty()

    def reverse(self):

        super(PersistentList, self).reverse()
        self._setDirty()

    def sort(self, *args):

        super(PersistentList, self).sort(*args)
        self._setDirty()

    def extend(self, value, setDirty=True):

        for v in value:
            self._storeValue(v)
            self.append(self._prepareValue(v, False), False)
        if setDirty:
            self._setDirty()

    def __getitem__(self, key):

        value = super(PersistentList, self).__getitem__(key)
        value = self._restoreValue(value)
        
        return value

    def __getslice__(self, start, end):

        value = super(PersistentList, self).__getslice__(start, end)
        value = [self._restoreValue(v) for v in value]

        return value

    def __iter__(self):

        for value in super(PersistentList, self).__iter__():
            yield self._restoreValue(value)

    def itervalues(self):

        return self.__iter__()

    def _itervalues(self):

        return super(PersistentList, self).__iter__()


class PersistentDict(dict, PersistentCollection):
    'A persistence aware dict, tracking changes into a dirty bit.'

    def __init__(self, item, attribute, companion):

        dict.__init__(self)
        PersistentCollection.__init__(self, item, attribute, companion)

    def _copy(self, item, attribute, companion, copyPolicy, copyFn):

        copy = type(self)(item, attribute, companion)
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       default='copy')
        
        for key, value in self.iteritems():
            if isinstance(value, repository.item.Item.Item):
                value = copyFn(item, value, policy)
                if value is not None:
                    copy.__setitem__(key, value, False)
            elif isinstance(value, PersistentCollection):
                copy.__setitem__(key, value._copy(item, attribute, companion,
                                                  copyPolicy, copyFn), False)
            else:
                copy.__setitem__(key, value, False)

        return copy

    def __delitem__(self, key):

        super(PersistentDict, self).__delitem__(key)
        self._setDirty()

    def __setitem__(self, key, value, setDirty=True):

        self._storeValue(value)
        value = self._prepareValue(value)
        super(PersistentDict, self).__setitem__(key, value)

        if setDirty:
            self._setDirty()

    def clear(self):

        super(PersistentDict, self).clear()
        self._setDirty()

    def update(self, value, setDirty=True):

        for k, v in value.iteritems():
            self._storeValue(v)
            self.__setitem__(k, self._prepareValue(v, False), False)
        if setDirty:
            self._setDirty()

    def setdefault(self, key, value=None):

        if not key in self:
            self._setDirty()

        self._storeValue(value)
        value = self._prepareValue(value)

        return super(PersistentDict, self).setdefault(key, value)

    def popitem(self):

        value = super(PersistentDict, self).popitem()
        value = (value[0], self._restoreValue(value[1]))
        self._setDirty()

        return value

    def __getitem__(self, key):

        value = super(PersistentDict, self).__getitem__(key)
        value = self._restoreValue(value)
        
        return value

    def get(self, key, default):

        value = super(PersistentDict, self).get(key, default)
        value = self._restoreValue(value)
        
        return value

    def itervalues(self):

        for value in super(PersistentDict, self).itervalues():
            yield self._restoreValue(value)

    def iteritems(self):

        for key, value in super(PersistentDict, self).iteritems():
            yield (key, self._restoreValue(value))

    def _itervalues(self):

        return super(PersistentDict, self).itervalues()

    def _iteritems(self):

        return super(PersistentDict, self).iteritems()
