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


from chandlerdb.util.c import _hash, _combine, CLink, CLinkedMap, Nil
from chandlerdb.util.LinkedMap import LinkedMap
from chandlerdb.item.Indexed import Indexed
from chandlerdb.item.ItemError import *
from chandlerdb.item.c import ItemRef, isitem


class RefList(LinkedMap, Indexed):
    """
    This class implements a double-linked list of bi-directional item
    references backed by a C{dict} mapping UUIDs to item references with
    predictable order. In addition to the UUID-based keys used by the
    implementation, an optional second set of keys, called aliases, can be
    used to name and access the references contained by a ref list.
    """
    
    def __init__(self, view, item, name, otherName, dictKey, readOnly, lmflags):
        """
        The constructor for this class. A RefList should not be instantiated
        directly but created through the item and attribute it is going to
        be used with instead, as for example with: C{item.name = []}.
        """
        
        super(RefList, self).__init__(view, lmflags)
        self._init_indexed()
        self._owner = Nil
        self._name = name
        self._otherName = otherName
        self._dictKey = dictKey

        if item is not None:
            self._setOwner(item, name)

        if readOnly:
            self._flags |= RefList.READONLY
        
    def _isRefs(self):
        return True
    
    def _isList(self):
        return True
    
    def _isSet(self):
        return False
    
    def _isDict(self):
        return False
    
    def _isDirty(self):
        return False

    def _setDirty(self, noFireChanges=False):

        if self._flags & RefList.SETDIRTY:
            item = self._owner()
            item.setDirty(item.RDIRTY, self._name, item._references, noFireChanges)

    def _setFlag(self, flag, on):

        old = self._flags & flag != 0
        if on:
            self._flags |= flag
        else:
            self._flags &= ~flag

        return old

    # copy the indexes from self into refList, empty
    def _copyIndexes(self, refList):

        if self._indexes is not None:
            refList._indexes = indexes = {}
            for name, index in self._indexes.iteritems():
                type = index.getIndexType()
                kwds = index.getInitKeywords()
                indexes[name] = refList._createIndex(type, **kwds)

    # copy the refs from self into copyItem._references
    def _copy(self, copyItem, name, policy, copyFn, refList=None):

        if refList is None:
            refList = copyItem._references.get(name, Nil)
            if refList is Nil:
                refList = copyItem._refList(name, self._otherName)
                self._copyIndexes(refList)
                copyItem._references[name] = refList

        for key in self.iterkeys():
            link = self._get(key)
            copyOther = copyFn(copyItem, link.value, policy)
            if copyOther is not Nil:
                if copyOther not in refList:
                    refList.append(copyOther, link.alias, link._otherKey)
                else:
                    refList.placeItem(copyOther, refList.last()) # copy order
                    if link.alias is not None:                   # and alias
                        refList.setAlias(copyOther, link.alias)

        return refList

    def _clone(self, owner):

        name = self._name
        otherName = self._otherName
        owner._references[name] = clone = owner._refList(name, otherName,
                                                         self._dictKey)

        if self:
            otherKind = owner.getAttributeAspect(name, 'type', False,
                                                 None, None)
            if otherKind is not None:
                otherAttr = otherKind.getAttribute(otherName)
                if otherAttr.getAspect('cardinality', 'single') == 'list':
                    clone.extend(self)
                return clone

            for other in self:
                otherCard = other.getAttributeAspect(otherName,
                                                     'cardinality', False,
                                                     None, 'single')
                if otherCard == 'list':
                    clone.append(other)

        return clone

    def _setOwner(self, item, name):

        if self._owner is not Nil and self._owner() is not item:
            raise AssertionError, 'Item is already set'
        
        if item is not None:
            self._owner = item.itsRef
            self._flags |= RefList.SETDIRTY
        else:
            self._owner = Nil
            self._flags &= ~RefList.SETDIRTY

    def _getOwner(self):
        return self._owner(), self._name
    itsOwner = property(_getOwner)

    def __repr__(self):

        owner = self._owner(True)
        if isitem(owner):
            owner = owner._repr_()

        return '<%s: %s.%s<->%s>' %(type(self).__name__,
                                    owner, self._name, self._otherName)

    def __contains__(self, key, excludeMutating=False, excludeIndexes=False):
        """
        The C{in} operator works both with C{Item} values or C{UUID} keys.

        To verify if there is a value for an alias, use the
        L{resolveAlias} method instead.

        @param key: the item or uuid sought
        @type key: an C{Item} instance, C{UUID} instance or C{None}
        @return: C{False} if C{key} is C{None} or is not this collection,
        C{True} otherwise.
        """

        if key is None:
            return False

        return super(RefList, self).__contains__(key.itsUUID)

    def isSubset(self, superset, reasons=None):
        """
        Tell if C{self} a subset of C{superset}.

        A ref collection can only be a subset of itself or, when its owning
        attribute has a C{Kind} set for its C{type} aspect, of any C{KindSet}
        of that kind or a superkind thereof.

        @param reasons: if specified, contains the C{(subset, superset)} pairs
                        that caused the predicate to fail.
        @type reasons: a C{set} or C{None}
        @return: C{True} or C{False}
        """

        if self is superset:
            return True

        return superset.isSuperset(self, reasons)

    def isSuperset(self, subset, reasons=None):
        """
        Tell if C{self} a superset of C{subset}.

        A ref collection can only be a superset of itself or of an
        C{AbstractSet} ultimately based off it.

        @param reasons: if specified, contains the C{(subset, superset)} pairs
                        that caused the predicate to fail.
        @type reasons: a C{set} or C{None}
        @return: C{True} or C{False}
        """

        if self is subset:
            return True

        if not isinstance(subset, RefList):
            return subset.isSubset(self, reasons)

        if reasons is not None:
            reasons.add((subset, self))

        return False

    def extend(self, valueList, _noFireChanges=False):
        """
        As with regular python lists, this method appends all items in the
        list to this ref collection.
        """
        
        try:
            sd = self._setFlag(RefList.SETDIRTY, False)
            for value in valueList:
                self.append(value, None, None, _noFireChanges)
        finally:
            self._setFlag(RefList.SETDIRTY, sd)

        self._setDirty(True)

    def add(self, item, alias=None, otherKey=None):
        """
        Add an item to this ref collection.

        This is method is a synonym for the L{append} method.
        """

        self.append(item, alias, otherKey)

    def set(self, item, alias=None, otherKey=None):

        if self:
            self.clear()
        
        self.append(item, alias, otherKey)

    def append(self, item, alias=None, otherKey=None, _noFireChanges=False):
        """
        Append an item to this ref collection.

        An item may occur only once in any given ref collection. If the item
        already occurs in this collection then only the alias is changed if
        passed in and not C{None}.

        @param alias: if this optional argument is specified it becomes an
        alias with which the item can be looked up using the L{getByAlias}
        or L{resolveAlias} methods.
        @type alias: a string
        """

        if item in self:
            if otherKey is not None and self.getOtherKey(item) != otherKey:
                self.remove(item)
            elif alias is not None:
                self.setAlias(item, alias)
            else:
                return

        if alias is not None:
            aliasedKey = self.resolveAlias(alias)
            if aliasedKey is not None:
                raise ValueError, "alias '%s' already set for key %s" %(alias, aliasedKey)
        self._owner().itsRefs._setValue(self._name, item, self._otherName,
                                        _noFireChanges, 'list',
                                        alias, self._dictKey, otherKey)

    def clear(self):
        """
        Remove all references from this ref collection.
        """

        # The first item is removed from the collection until it is empty.
        # This makes it possible for other items to be removed as side-effects
        # of a removal without throwing off the iteration (bug 9004).

        view = self.itsView
        while True:
            uOther = self.firstKey()
            if uOther is None:
                break
            other = view.find(uOther)
            if other is not None:
                self.remove(other)
            else:  # dangling ref, clean it up
                self._removeRef(uOther, None)

    def _clearRefs(self):

        while True:
            other = self.first()
            if other is None:
                break
            otherValue = getattr(other, self._otherName, None)
            if otherValue is None:
                self._removeRef(other)
            elif otherValue._isRefs():
                if self._owner() in otherValue:
                    self.remove(other)
                else:
                    self._removeRef(other)
            elif otherValue is self._owner():
                self.remove(other)
            else:
                self._removeRef(other)

    def dir(self):
        """
        Debugging: print all items referenced in this ref collection.
        """
        for item in self:
            print item._repr_()

    def _setRef(self, other, alias=None, dictKey=None, otherKey=None,
                fireChanges=False):

        if otherKey is not None and other.itsUUID in self:
            if self.getOtherKey(other) != otherKey:
                self.remove(other)

        key = other.itsUUID
        link = CLink(self, other.itsRef, None, None, alias, otherKey);
        self[key] = link

        if self._indexes:
            for index in self._indexes.itervalues():
                index.insertKey(key, link._previousKey, False, True)

        self._setDirty(not fireChanges)

        return other

    def placeItem(self, item, after, *indexNames):
        """
        Place an item in this collection after another one.

        Both items must already belong to the collection. To place an item
        first, pass C{None} for C{after}.

        @param item: the item to place, must belong to the collection.
        @type item: an C{Item} instance
        @param after: the item to place C{item} after or C{None} if C{item} is
        to be first in this ref collection.
        @type after: an C{Item} instance
        @param indexNames: zero or more names of indexes to place the item
        in instead of the collection's default intrinsic order
        """
        
        if not indexNames:
            key = item.itsUUID
            if after is not None:
                afterKey = after.itsUUID
            else:
                afterKey = None

            self.place(key, afterKey)
            self._setDirty()
        else:
            self.placeInIndex(item, after, None, *indexNames)

    def insertItem(self, item, after, *indexNames):
        """
        Insert an item in this collection after another one.

        To place an item first, pass C{None} for C{after}.

        Since an item can occur only once in a ref collection, if
        C{item} already belongs to the collection it is moved instead.

        @param item: the item to insert
        @type item: an C{Item} instance
        @param after: the item to place C{item} after or C{None} if C{item} is
        to be first in this ref collection.
        @type after: an C{Item} instance
        @param indexNames: zero or more names of indexes to place the item
        in instead of the collection's default intrinsic order 
        """

        if item not in self:
            self.append(item)
            
        self.placeItem(item, after, *indexNames)

    def replaceItem(self, item, withItem, *indexNames):
        """
        Replace an item in this collection with another one.

        Since an item can occur only once in a ref collection, if
        C{with} is in the collection already C{item} is removed and
        C{with} moved in its place.

        @param item: the item to replace
        @type item: an C{Item} instance
        @param withItem: the item to substitute in
        @type withItem: an C{Item} instance
        @param indexNames: zero or more names of indexes to place the item
        in instead of the collection's default intrinsic order
        """

        if withItem not in self:
            self.append(withItem)

        self.placeItem(withItem, item, *indexNames)
        self.remove(item)

    def removeItem(self, item):

        self.remove(item)

    def remove(self, item):
        """
        Remove an item from this ref collection.

        @param item: the item whose reference to remove.
        @type item: an C{Item} instance
        """

        self._owner().itsRefs._removeValue(self._name, item,
                                           self._otherName, self._dictKey)
            
    def __delitem__(self, key):

        self._owner().itsRefs._removeValue(self._name, self[key],
                                           self._otherName, self._dictKey)

    def _removeRef_(self, other):

        if self._flags & RefList.READONLY:
            raise ReadOnlyAttributeError, (self._owner(), self._name)

        key = other.itsUUID
        
        if self._indexes:
            for index in self._indexes.itervalues():
                index.removeKey(key)

        return super(RefList, self).__delitem__(key)

    def _removeRef(self, other, dictKey=None):

        link = self._removeRef_(other)
        if link is not None:
            self._setDirty()
            item = self._owner()
            view = self.itsView
            view._notifyChange(item._collectionChanged,
                               'remove', 'collection', self._name,
                               other.itsUUID, ())
            return link._otherKey

    def _removeRefs(self):

        self.clear()

    def _load(self, key):

        if self._flags & CLinkedMap.NEW:
            return False

        ref = self._loadRef(key)
        if ref is None:
            return False
        
        view = self.itsView
            
        previousKey, nextKey, alias, otherKey = ref[0:4]
        self._dict[key] = CLink(self, ItemRef(key, view), previousKey, nextKey,
                                alias, otherKey)
        if alias is not None:
            aliases = self._aliases
            if aliases is Nil:
                self._aliases = {alias: key}
            else:
                aliases[alias] = key

        return True

    def get(self, key, default=None, load=True):
        """
        Get the item referenced at C{key}.

        To get an item through its alias, use L{getByAlias} instead.

        @param key: the UUID of the item referenced.
        @type key: L{UUID<chandlerdb.util.c.UUID>}
        @param default: the default value to return if there is no reference
        for C{key} in this ref collection, C{None} by default.
        @type default: anything
        @param load: if the reference exists but hasn't been loaded yet,
        this method will return C{default} if this parameter is C{False}.
        @type load: boolean
        @return: an C{Item} instance or C{default}
        """

        return super(RefList, self).get(key, default, load)

    def getOtherKey(self, item):
        """
        Get the alias this item is keyed on in this collection.

        @param item: an item in the collection
        @type item: an L{Item<chandlerdb.item.Item.Item>} instance
        @return: the alias string or None if the item is not aliased
        """

        return self._get(item.itsUUID)._otherKey

    def getAlias(self, item):
        """
        Get the alias this item is keyed on in this collection.

        @param item: an item in the collection
        @type item: an L{Item<chandlerdb.item.Item.Item>} instance
        @return: the alias string or None if the item is not aliased
        """

        return self._get(item.itsUUID).alias

    def setAlias(self, item, alias):

        oldAlias = super(RefList, self).setAlias(item.itsUUID, alias)
        if oldAlias != alias:
            self._setDirty(True)

        return oldAlias

    def removeByIndex(self, indexName, position):

        del self[self.getIndex(indexName).getKey(position)]

    def insertByIndex(self, indexName, position, item):

        if position == 0:
            after = None
        else:
            after = self.getIndex(indexName).getKey(position - 1)
        self.insertItem(item, after, indexName)

    def replaceByIndex(self, indexName, position, withItem):

        item = self[self.getIndex(indexName).getKey(position)]
        self.replaceItem(self, item, withItem, indexName)

    def refCount(self, loaded):
        """
        Return the number of bi-directional references in this collection.

        if C{loaded} is C{True}, return only the number of currently loaded
        references.

        @return: an integer
        """
        
        if loaded:
            return super(RefList, self).__len__()
        
        return len(self)

    def _xmlValue(self, name, item, generator, withSchema, version, attrs):

        attrs['name'] = name
        if withSchema:
            attrs['cardinality'] = 'list'
            attrs['otherName'] = item.itsKind.getOtherName(name, item)

        generator.startElement('ref', attrs)
        self._xmlValues(generator, version)
        if self._indexes:
            for name, index in self._indexes.iteritems():
                attrs = { 'name': name, 'type': index.getIndexType() }
                index._xmlValue(generator, version, attrs)
        generator.endElement('ref')

    def _xmlValues(self, generator, version):

        refs = self._owner()._references
        for key in self.iterkeys():
            link = self._get(key)
            refs._xmlRef(key, link.value,
                         generator, False, version, {},
                         previous=link._previousKey, next=link._nextKey,
                         alias=link.alias)

    def _saveValues(self, version):
        raise NotImplementedError, "%s._saveValues" %(type(self))

    def copy(self):
        """
        This method is not directly supported on this class.

        To copy a ref collection into another one, call L{extend} with this
        collection on the target collection.
        """
        
        raise NotImplementedError, 'RefList.copy is not supported'

    def first(self):
        """
        Get the first item referenced in this ref collection.

        @return: an C{Item} instance or C{None} if empty.
        """

        firstKey = self.firstKey()
        if firstKey is not None:
            return self[firstKey]

        return None

    def last(self):
        """
        Get the last item referenced in this ref collection.

        @return: an C{Item} instance or C{None} if empty.
        """

        lastKey = self.lastKey()
        if lastKey is not None:
            return self[lastKey]

        return None

    def next(self, previous):
        """
        Get the next referenced item relative to previous.

        @param previous: the previous item relative to the item sought.
        @type previous: a C{Item} instance
        @return: an C{Item} instance or C{None} if C{previous} is the last
        referenced item in the collection.
        """

        key = previous.itsUUID

        try:
            nextKey = self.nextKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                raise NoSuchItemInCollectionError, (self._owner(), self._name,
                                                    previous)

        if nextKey is not None:
            return self[nextKey]

        return None

    def previous(self, next):
        """
        Get the previous referenced item relative to next.

        @param next: the next item relative to the item sought.
        @type next: a C{Item} instance
        @return: an C{Item} instance or C{None} if next is the first
        referenced item in the collection.
        """

        key = next.itsUUID

        try:
            previousKey = self.previousKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                raise NoSuchItemInCollectionError, (self._owner, self._name,
                                                    next)

        if previousKey is not None:
            return self[previousKey]

        return None

    def _check(self, logger, item, name, repair):
        """
        Debugging: verify this ref collection for consistency.

        Consistency errors are logged.

        @return: C{True} if no errors were found, {False} otherwise.
        """

        logger = self.itsView.logger
        refs = self._owner().itsRefs

        if item is not self._owner() or name != self._name:
            logger.error('Ref collection not owned by %s.%s: %s',
                         self._owner, self._name, self)
            return False
        
        while True:
            l = len(self)
            result = True
            key = self.firstKey()
            prevKey = None

            while key is not None and l > 0:
                try:
                    other = self[key]
                    result = result and refs._checkRef(logger, name, other,
                                                       repair)
                    if result is None:  # a key was removed during repair
                        break
                except:
                    logger.exception("Iterating %s caused an error", self)
                    return False
                l -= 1
                prevKey = key
                key = self.nextKey(key)

            if result is None:          # re-run check because of repair
                continue
            break
            
        if l != 0:
            logger.error("Iterator on %s doesn't match length (%d left for %d total)", self, l, len(self))
            return False

        if prevKey != self.lastKey():
            logger.error("iterator on %s doesn't finish on last key %s but on %s", self, self.lastKey(), prevKey)
            return False

        return result and self._checkIndexes(logger, self._owner(), self._name,
                                             repair)

    def _hashValues(self):

        hash = 0
        for key in self.iterkeys():
            link = self._get(key)
            hash = _combine(hash, key._hash)
            if link.alias is not None:
                hash = _combine(hash, _hash(link.alias))

        return hash

    def _inspect_(self, indent):
        return "\n%s<RefList> %s<->%s" %('  ' * indent,
                                         self._name, self._otherName)

    def __iter__(self, excludeIndexes=False):

        for key in self.iterkeys():
            yield self[key]

    def countKeys(self):
        return self._count

    def iterItems(self):
        return self.itervalues()

    def iterKeys(self):
        return self.iterkeys()

    #    NEW  = 0x0001 (defined on CLinkedMap)
    #    LOAD = 0x0002 (defined on CLinkedMap)
    # MERGING = 0x0004 (defined on CLinkedMap)
    SETDIRTY  = 0x0008
    READONLY  = 0x0010


class RefDict(object):
    """
    This class implements a dictionary of RefList instances.
    """
    
    def __init__(self, item, name, otherName):
        
        super(RefDict, self).__init__()

        if item is None:
            self._owner = Nil
        else:
            self._owner = item.itsRef
            
        self._name = name
        self._otherName = otherName
        self._dict = {}

    def _isRefs(self):
        return True
    
    def _isList(self):
        return False
    
    def _isSet(self):
        return False
    
    def _isDict(self):
        return True
    
    def _refList(self, dictKey):

        if dictKey is None:
            raise ValueError, 'dictKey is None'

        refList = self._dict.get(dictKey)
        if refList is None:
            self._dict[dictKey] = refList = \
                self._owner()._refList(self._name, self._otherName, dictKey)

        return refList

    def _setRef(self, other, alias=None, dictKey=None, otherKey=None,
                fireChanges=False):

        self._refList(dictKey)._setRef(other, alias, dictKey, otherKey,
                                       fireChanges)

    def _removeRef(self, other, dictKey=None):

        if dictKey in self:
            return self[dictKey]._removeRef(other, dictKey)

    def _removeRefs(self):

        self.clear()

    def add(self, dictKey, other, alias=None, otherKey=None):

        self._refList(dictKey).append(other, alias, otherKey)

    def set(self, dictKey, other, alias=None, otherKey=None):

        refList = self._refList(dictKey)
        if refList:
            refList.clear()
        
        refList.append(other, alias, otherKey)

    def clear(self):
        
        for refList in self._dict.itervalues():
            refList.clear()

        self._dict.clear()

    def get(self, key, default=None):

        return self._dict.get(key, default)

    def __len__(self):

        return sum(len(refList) for refList in self._dict.itervalues())

    def __delitem__(self, dictKey):

        if dictKey is None:
            raise ValueError, 'dictKey is None'

        refList = self._dict[dictKey]
        refList.clear()

        del self._dict[dictKey]

    def __getitem__(self, dictKey):

        if dictKey is None:
            raise ValueError, 'dictKey is None'

        return self._dict[dictKey]

    def __setitem__(self, dictKey, value):

        if isitem(value):
            self._refList(dictKey).append(value)
        else:
            self._refList(dictKey).extend(value)

    def __contains__(self, dictKey):

        if dictKey is None:
            raise ValueError, 'dictKey is None'

        return dictKey in self._dict

    def containsKey(self, dictKey):

        if dictKey is None:
            raise ValueError, 'dictKey is None'

        return dictKey in self._dict

    def containsItem(self, item):

        for refList in self._dict.itervalues():
            if item in refList:
                return True

        return False

    def _check(self, logger, item, name, repair):

        for refList in self._dict.itervalues():
            if not refList._check(logger, item, name, repair):
                return False

        return True

    def _clearDirties(self):

        for refList in self._dict.itervalues():
            refList._clearDirties()

    def _setOwner(self, item, name):
        
        if item is None:
            self._owner = Nil
        else:
            self._owner = item.itsRef

        for refList in self._dict.itervalues():
            refList._setOwner(item, name)

    def keys(self):

        return self._dict.keys()

    def values(self):
        
        return self._dict.values()

    def iterkeys(self):

        return self._dict.iterkeys()

    def itervalues(self):

        return self._dict.itervalues()

    def iteritems(self):

        return self._dict.iteritems()

    def iterItems(self):

        for refList in self._dict.itervalues():
            for item in refList:
                yield item

    def iterKeys(self):

        for refList in self._dict.itervalues():
            for key in refList.iterKeys():
                yield key

    def refCount(self, loaded):

        return sum(refList.refCount(loaded) for refList in
                   self._dict.itervalues())
            
    # copy the refs from self into copyItem._references
    def _copy(self, copyItem, name, policy, copyFn, refDict=None):

        if refDict is None:
            refDict = copyItem._references.get(name, Nil)
            if refDict is Nil:
                refDict = RefDict(copyItem, name, self._otherName)
                copyItem._references[name] = refDict

        for key, refList in self._dict.iteritems():
            refList._copy(copyItem, name, policy, copyFn, refDict._refList(key))

        return refDict
