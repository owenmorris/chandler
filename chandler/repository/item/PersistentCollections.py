
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
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

        if self._item:
            self._item.setDirty()

    def _prepareValue(self, value):

        if isinstance(value, PersistentCollection):
            value = value._copy(self._item, self._attribute, self._companion,
                                {}, 'copy')
        elif isinstance(value, list):
            value = PersistentList(self._item, self._attribute,
                                   self._companion, value)
        elif isinstance(value, dict):
            value = PersistentDict(self._item, self._attribute,
                                   self._companion, value)
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

    def _copyItem(self, value, item, copies, policy, copyPolicy):

        # value: item value to copy
        # item: item being copied causing item value to be copied

        if policy == 'copy':
            return value

        if policy == 'cascade':
            valueCopy = copies.get(value.itsUUID, None)

            if valueCopy is None:
                if self._item.itsParent is item.itsParent:
                    valueParent = item.itsParent
                else:
                    valueParent = value.itsParent
                valueCopy = value.copy(None, valueParent, copies, copyPolicy)

            return valueCopy

        return None

    def _getItems(self, items=None):

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
                        if value not in items:
                            items[value] = value
                            yield value
                elif isinstance(value, PersistentCollection):
                    for v in value._getItems(items):
                        yield v


class PersistentList(list, PersistentCollection):
    'A persistence aware list, tracking changes into a dirty bit.'

    def __init__(self, item, attribute, companion, initialValues=None):

        list.__init__(self)
        PersistentCollection.__init__(self, item, attribute, companion)

        if initialValues is not None:
            self.extend(initialValues)

    def _copy(self, item, attribute, companion, copies, copyPolicy):

        copy = type(self)(item, attribute, companion)
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       default='copy')

        for value in self:
            if isinstance(value, repository.item.Item.Item):
                value = self._copyItem(value, item, copies, policy, copyPolicy)
                if value is not None:
                    copy.append(value)
            elif isinstance(value, PersistentCollection):
                copy.append(value._copy(item, attribute, companion,
                                        copies, copyPolicy))
            else:
                copy.append(value)

        return copy

    def __setitem__(self, index, value):

        self._storeValue(value)
        value = self._prepareValue(value)
        self._setDirty()
        super(PersistentList, self).__setitem__(index, value)

    def __delitem__(self, index):

        self._setDirty()
        super(PersistentList, self).__delitem__(index)        

    def __setslice__(self, start, end, value):

        for v in value:
            self._storeValue(v)
        value = [self._prepareValue(v) for v in value]
        self._setDirty()
        super(PersistentList, self).__setslice__(start, end, value)

    def __delslice__(self, start, end):

        self._setDirty()
        super(PersistentList, self).__delslice__(start, end)

    def __iadd__(self, value):

        for v in value:
            self._storeValue(v)
        value = [self._prepareValue(v) for v in value]
        self._setDirty()
        super(PersistentList, self).__iadd__(value)

    def __imul__(self, value):

        self._setDirty()
        super(PersistentList, self).__imul__(value)

    def append(self, value):

        self._storeValue(value)
        value = self._prepareValue(value)
        self._setDirty()
        super(PersistentList, self).append(value)

    def insert(self, index, value):

        self._storeValue(value)
        value = self._prepareValue(value)
        self._setDirty()
        super(PersistentList, self).insert(index, value)

    def pop(self, index = -1):

        self._setDirty()
        value = super(PersistentList, self).pop(index)
        value = self._restoreValue(value)

        return value

    def remove(self, value):

        value = self._prepareValue(value)
        self._setDirty()
        super(PersistentList, self).remove(value)

    def reverse(self):

        self._setDirty()
        super(PersistentList, self).reverse()

    def sort(self, *args):

        self._setDirty()
        super(PersistentList, self).sort(*args)

    def extend(self, value):

        values = []
        for v in value:
            self._storeValue(v)
            values.append(self._prepareValue(v))
        self._setDirty()
        super(PersistentList, self).extend(values)

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

    def __init__(self, item, attribute, companion, initialValues=None):

        dict.__init__(self)
        PersistentCollection.__init__(self, item, attribute, companion)

        if initialValues is not None:
            self.update(initialValues)

    def _copy(self, item, attribute, companion, copies, copyPolicy):

        copy = type(self)(item, attribute, companion)
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       default='copy')
        
        for key, value in self.iteritems():
            if isinstance(value, repository.item.Item.Item):
                value = self._copyItem(value, item, copies, policy, copyPolicy)
                if value is not None:
                    copy[key] = value
            elif isinstance(value, PersistentCollection):
                copy[key] = value._copy(item, attribute, companion,
                                        copies, copyPolicy)
            else:
                copy[key] = value

        return copy

    def __delitem__(self, key):

        self._setDirty()
        super(PersistentDict, self).__delitem__(key)

    def __setitem__(self, key, value):

        self._storeValue(value)
        value = self._prepareValue(value)
        self._setDirty()
        super(PersistentDict, self).__setitem__(key, value)

    def clear(self):

        self._setDirty()
        super(PersistentDict, self).clear()

    def update(self, value):

        values = {}
        for k, v in value.iteritems():
            self._storeValue(v)
            values[k] = self._prepareValue(v)
        self._setDirty()
        super(PersistentDict, self).update(values)

    def setdefault(self, key, value=None):

        if not key in self:
            self._setDirty()

        self._storeValue(value)
        value = self._prepareValue(value)

        return super(PersistentDict, self).setdefault(key, value)

    def popitem(self):

        self._setDirty()

        value = super(PersistentDict, self).popitem()
        value = (value[0], self._restoreValue(value[1]))
        
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
