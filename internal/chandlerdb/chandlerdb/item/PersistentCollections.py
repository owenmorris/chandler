#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from chandlerdb.util.c import Nil
from chandlerdb.item.c import isitem, isitemref, ItemValue
from chandlerdb.item import c


class PersistentCollection(ItemValue):
    """
    A persistence aware collection, tracking changes into a dirty bit.

    This class is abstract and is to be used together with a protocol
    class such as c.PersistentSequence, c.PersistentMapping or c.PersistentSet
    """

    def _setOwner(self, item, attribute, pure=None):

        oldItem, oldAttribute, pure = \
            super(PersistentCollection, self)._setOwner(item, attribute, pure)

        if oldItem is not item or oldAttribute is not attribute:
            for value in self._itervalues():
                if isinstance(value, ItemValue):
                    value._setOwner(item, attribute, pure)

    def prepareValue(self, item, attribute, value, setDirty=True):
        
        if isinstance(value, ItemValue):
            if value._owner is not Nil:
                value = value._copy(item, attribute, 'copy')
            else:
                value._setOwner(item, attribute)
        elif isinstance(value, list):
            value = PersistentList(item, attribute, value, setDirty)
        elif isinstance(value, dict):
            value = PersistentDict(item, attribute, value, setDirty)
        elif isinstance(value, tuple):
            value = PersistentTuple(item, attribute, value, setDirty)
        elif isinstance(value, set):
            value = PersistentSet(item, attribute, value, setDirty)
        elif isitem(value):
            value = value.itsRef

        return value

    def restoreValue(self, value):

        if self._owner is not Nil and isitemref(value):
            return value(True)

        return value

    def useValue(self, value):

        if isitem(value):
            return value.itsRef
        if isinstance(value, PersistentCollection):
            return value
        if isitemref(value):
            return value

        if isinstance(value, list):
            return [self.useValue(v) for v in value]
        elif isinstance(value, set):
            return set([self.useValue(v) for v in value])
        elif isinstance(value, tuple):
            return tuple([self.useValue(v) for v in value])
        elif isinstance(value, dict):
            d = {}
            for k, v in value.itervalues():
                d[k] = self.useValue(v)
            return d
        else:
            return value

    def _iterItems(self, items=None):

        if items is None:
            items = {}
        for value in self._itervalues():
            if isitemref(value):
                item = value(True)
                if isitem(item):
                    uuid = item.itsUUID
                    if uuid not in items:
                        items[uuid] = item
                        yield item
            elif isinstance(value, PersistentCollection):
                for v in value._iterItems(items):
                    yield v

    def _iterKeys(self, keys=None):

        if keys is None:
            keys = set()
        for value in self._itervalues():
            if isitemref(value):
                key = value.itsUUID
                if key not in keys:
                    keys.add(key)
                    yield key
            elif isinstance(value, PersistentCollection):
                for v in value._iterKeys(keys):
                    yield v


class PersistentList(PersistentCollection, c.PersistentSequence):
    'A persistence aware list proxy, tracking changes into a dirty bit.'

    __class__ = list
    __proxy_for__ = list # to placate unit tests

    def __init__(self, item=None, attribute=None, values=None,
                 setDirty=True, pure=False):

        c.PersistentSequence.__init__(self, [], None, item, attribute, pure)
        if values is not None:
            self.extend(values, setDirty)

    def _copy(self, item, attribute, copyPolicy, copyFn=None):

        copy = type(self)(item, attribute)
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       False, None, 'copy')

        for value in self:
            if isitem(value):
                if copyFn is not None:
                    value = copyFn(item, value, policy)
                if value is not Nil:
                    copy.append(value, False)
            elif isinstance(value, ItemValue):
                copy.append(value._copy(item, attribute, copyPolicy, copyFn),
                            False)
            else:
                copy.append(value, False)

        return copy

    def _clone(self, item, attribute):

        clone = type(self)(item, attribute)

        for value in self:
            if isinstance(value, ItemValue):
                value = value._clone(item, attribute)
            clone.append(value, False)

        return clone

    def remove(self, value, setDirty=True):

        self._sequence.remove(self._useValue(value))
        if setDirty:
            self._setDirty()

    def reverse(self, setDirty=True):

        self._sequence.reverse()
        if setDirty:
            self._setDirty()

    def sort(self, *args, **kwds):

        self._sequence.sort(*args, **kwds)
        self._setDirty()

    def _get(self, key):

        return self._sequence[key]

    def itervalues(self):

        return iter(self)

    def _itervalues(self):

        return iter(self._sequence)


class PersistentDict(PersistentCollection, c.PersistentMapping):
    'A persistence aware dict, tracking changes into a dirty bit.'

    __class__ = dict
    __proxy_for__ = dict # to placate unit tests

    def __init__(self, item=None, attribute=None, values=None,
                 setDirty=True, pure=False):

        c.PersistentMapping.__init__(self, {}, None, item, attribute, pure)
        if values is not None:
            self.update(values, setDirty)

    def _copy(self, item, attribute, copyPolicy, copyFn=None):

        copy = type(self)(item, attribute)
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       False, None, 'copy')
        
        for key, value in self.iteritems():
            if isitem(value):
                if copyFn is not None:
                    value = copyFn(item, value, policy)
                if value is not Nil:
                    copy.__setitem__(key, value, False)
            elif isinstance(value, ItemValue):
                copy.set(key, value._copy(item, attribute, policy,
                                          copyFn), False)
            else:
                copy.set(key, value, False)

        return copy

    def _clone(self, item, attribute):

        clone = type(self)(item, attribute)

        for key, value in self.iteritems():
            if isinstance(value, ItemValue):
                value = value._clone(item, attribute)
            clone.set(key, value, False)

        return clone

    def clear(self, setDirty=True):

        self._mapping.clear()
        if setDirty:
            self._setDirty()

    def update(self, values, setDirty=True):

        if self.isPure():
            self._mapping.update(values)
        else:
            item = self._owner()
            attribute = self._attribute
            self._mapping.update((k, self.prepareValue(item, attribute,
                                                       v, False))
                                 for k, v in values.iteritems())
        if setDirty:
            self._setDirty()

    def popitem(self, setDirty=True):

        key, value = self._mapping.popitem()
        value = self.restoreValue(value)
        if setDirty:
            self._setDirty()

        return key, value

    def _get(self, key):

        return self._mapping.get(key)

    def iterkeys(self):

        return self._mapping.iterkeys()

    def itervalues(self):

        if self.isPure():
            for value in self._mapping.itervalues():
                yield value
        else:
            for value in self._mapping.itervalues():
                yield self.restoreValue(value)

    def iteritems(self):

        if self.isPure():
            for pair in self._mapping.iteritems():
                yield pair
        else:
            for key, value in self._mapping.iteritems():
                yield key, self.restoreValue(value)

    def _itervalues(self):

        return self._mapping.itervalues()

    def _iteritems(self):

        return self._mapping.iteritems()

    def _values(self):

        return self._mapping.values()

    def _items(self):

        return self._mapping.items()


class PersistentTuple(PersistentCollection, c.PersistentSequence):

    __class__ = tuple
    __proxy_for__ = tuple # to placate unit tests

    def __init__(self, item=None, attribute=None, values=None,
                 setDirty=True, pure=False):

        c.PersistentSequence.__init__(self, (), None, item, attribute, pure)

        if values:
            if not pure:
                values = tuple([self.prepareValue(item, attribute, value,
                                                  setDirty)
                                for value in values])
            elif not isinstance(values, tuple):
                values = tuple(values)
            else:
                values = ()

            self._sequence = values

    def _copy(self, item, attribute, copyPolicy, copyFn=None):

        copy = []
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       False, None, 'copy')

        for value in self:
            if isitem(value):
                if copyFn is not None:
                    value = copyFn(item, value, policy)
                if value is not Nil:
                    copy.append(value)
            elif isinstance(value, ItemValue):
                copy.append(value._copy(item, attribute, policy, copyFn))
            else:
                copy.append(value)

        return type(self)(item, attribute, copy, False)

    def _clone(self, item, attribute):

        clone = []

        for value in self:
            if isinstance(value, ItemValue):
                value = value._clone(item, attribute)
            clone.append(value)

        return type(self)(item, attribute, clone, False)

    def itervalues(self):

        return iter(self)

    def _itervalues(self):

        return iter(self._sequence)


class PersistentSet(PersistentCollection, c.PersistentSet):
    'A persistence aware set, tracking changes into a dirty bit.'

    __class__ = set
    __proxy_for__ = set # to placate unit tests

    def __init__(self, item=None, attribute=None, values=None,
                 setDirty=True, pure=False):

        c.PersistentSet.__init__(self, set(), None, item, attribute, pure)
        if values is not None:
            self.update(values, setDirty)

    def _copy(self, item, attribute, copyPolicy, copyFn=None):

        copy = type(self)(item, attribute)
        policy = copyPolicy or item.getAttributeAspect(attribute, 'copyPolicy',
                                                       False, None, 'copy')
        
        for value in self:
            if isitem(value):
                if copyFn is not None:
                    value = copyFn(item, value, policy)
                if value is not Nil:
                    copy.add(value, False)
            elif isinstance(value, ItemValue):
                copy.add(value._copy(item, attribute, policy, copyFn), False)
            else:
                copy.add(value, False)

        return copy

    def _clone(self, item, attribute):

        clone = type(self)(item, attribute)

        for value in self:
            if isinstance(value, ItemValue):
                value = value._clone(item, attribute)
            clone.add(value, False)

        return clone

    def itervalues(self):

        return iter(self)

    def _itervalues(self):

        return iter(self._set)

    def intersection_update(self, value, setDirty=True):

        if self.isPure():
            self._set &= value
        else:
            for v in [v for v in self if v not in value]:
                self.remove(v, False)

        if setDirty:
            self._setDirty()

    def difference_update(self, value, setDirty=True):

        if self.isPure():
            self._set -= value
        else:
            for v in [v for v in self if v in value]:
                self.remove(v, False)

        if setDirty:
            self._setDirty()

    def symmetric_difference_update(self, value, setDirty=True):

        if self.isPure():
            self._set.symmetric_difference_update(value)
        else:
            for v in [v for v in self if v in value]:
                self.remove(v, False)
            for v in [v for v in value if v not in self]:
                self.add(v, False)

        if setDirty:
            self._setDirty()
