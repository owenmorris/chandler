
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from chandlerdb.util.uuid import UUID, _hash, _combine
from repository.util.Path import Path
from repository.util.LinkedMap import LinkedMap
from repository.item.Indexes import NumericIndex, AttributeIndex, CompareIndex
from chandlerdb.item.item import Nil
from chandlerdb.item.ItemError import *


class RefList(LinkedMap):
    """
    This class implements a double-linked list of bi-directional item
    references backed by a C{dict} mapping UUIDs to item references with
    predictable order. In addition to the UUID-based keys used by the
    implementation, an optional second set of keys, called aliases, can be
    used to name and access the references contained by a ref list.
    """
    
    def __init__(self, item, name, otherName, readOnly, new):
        """
        The constructor for this class. A RefList should not be instantiated
        directly but created through the item and attribute it is going to
        be used with instead, as for example with: C{item.name = []}.
        """
        
        super(RefList, self).__init__(new)

        self._name = name
        self._otherName = otherName
        self._item = None
        if item is not None:
            self._setItem(item)
        self._indexes = None

        if readOnly:
            self._flags |= RefList.READONLY
        
    def _isRefList(self):
        return True
    
    def _isItem(self):
        return False
    
    def _isUUID(self):
        return False
    
    def _isTransient(self):
        return False

    def _setFlag(self, flag, on):

        old = self._flags & flag != 0
        if on:
            self._flags |= flag
        else:
            self._flags &= ~flag

        return old

    def _getFlag(self, flag):

        return self._flags & flag != 0

    def _setDirty(self, noMonitors=False):

        if self._getFlag(RefList.SETDIRTY):
            item = self._item
            item.setDirty(item.RDIRTY, self._name, item._references, noMonitors)

    # copy the indexes from self into refList, empty
    def _copyIndexes(self, refList):

        if self._indexes is not None:
            refList._indexes = indexes = {}
            for name, index in self._indexes.iteritems():
                type = index.getIndexType()
                kwds = index.getInitKeywords()
                indexes[name] = refList._createIndex(type, **kwds)

    # copy the refs from self into copyItem._references
    def _copy(self, copyItem, name, policy, copyFn):

        try:
            refList = copyItem._references[name]
        except KeyError:
            refList = copyItem._refList(name)
            self._copyIndexes(refList)
            copyItem._references[name] = refList

        for key in self.iterkeys():
            link = self._get(key)
            copyOther = copyFn(copyItem, link.getValue(self), policy)
            if copyOther is not Nil:
                if copyOther not in refList:
                    refList.append(copyOther, link._alias)
                elif link._alias is not None:
                    refList.setAlias(copyOther, link._alias)

        return refList

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise AssertionError, 'Item is already set'
        
        self._item = item
        if item is not None:
            self._flags |= RefList.SETDIRTY
        else:
            self._flags &= ~RefList.SETDIRTY

    def _getRepository(self):

        return self._item.itsView

    def __repr__(self):

        return '<%s: %s.%s<->%s>' %(type(self).__name__,
                                    self._item.itsPath,
                                    self._name, self._otherName)

    def __contains__(self, key):
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

        if key._isItem():
            key = key._uuid
        
        return super(RefList, self).__contains__(key)

    def addIndex(self, indexName, indexType, **kwds):
        """
        Add an index to this ref collection.

        A ref collection index provides positional access into the
        collection and maintains a key order which is be determined by the
        sequence of collection mutation operations or by constraints
        on values.

        A ref collection may have any number of indexes. Each index has a
        name which is used with the L{placeItem}, L{getByIndex},
        L{getIndexEntryValue}, L{setIndexEntryValue}, L{resolveIndex},
        L{first}, L{last}, L{next}, L{previous} methods.

        Because the implementation of an index depends on the persistence
        layer, the type of index is chosen with the C{indexType} parameter
        which can have one of the following values:

            - C{numeric}: a simple index reflecting the sequence of mutation
              operations.

            - C{attribute}: an index sorted on the value of an attribute
              of items in the collection. The name of the attribute is
              provided via the C{attribute} keyword.

            - C{compare}: an index sorted on the return value of a method
              invoked on items in the collection. The method is a comparison
              method whose name is provided with the C{compare} keyword, and
              it is invoked on C{i0}, with the other item being compared,
              C{i1}, and is expected to return a positive number if, in the
              context of this index, C{i0 > i1}, a negative number if C{i0 <
              i1}, or zero if C{i0 == i1}.

        @param indexName: the name of the index
        @type indexName: a string
        @param indexType: the type of index
        @type indexType: a string
        """

        if self._indexes is not None:
            if indexName in self._indexes:
                raise IndexAlreadyExists, (self._item, self._name, indexName)
        else:
            self._indexes = {}

        index = self._createIndex(indexType, **kwds)
        self._indexes[indexName] = index

        if not self._getRepository().isLoading():
            self.fillIndex(index)
            self._setDirty(noMonitors=True)

            if indexType == 'attribute':
                from repository.item.Monitors import Monitors
                Monitors.attach(self._item, '_reIndex',
                                'set', kwds['attribute'], self._name, indexName)

        return index

    def _createIndex(self, indexType, **kwds):

        if indexType == 'numeric':
            return NumericIndex(**kwds)

        if indexType == 'attribute':
            return AttributeIndex(self, self._createIndex('numeric', **kwds),
                                  **kwds)

        if indexType == 'compare':
            return CompareIndex(self, self._createIndex('numeric', **kwds),
                                **kwds)

        raise NotImplementedError, "indexType: %s" %(indexType)

    def removeIndex(self, indexName):

        if self._indexes is None or indexName not in self._indexes:
            raise NoSuchIndexError, (self._item, self._name, indexName)

        del self._indexes[indexName]
        self._setDirty(noMonitors=True)

    def fillIndex(self, index):

        for key in self.iterkeys():
            link = self._get(key)
            index.insertKey(key, link._previousKey)

    def _restoreIndexes(self, view):

        for index in self._indexes.itervalues():
            if index.isPersistent():
                index._restore(self._item._version)
            else:
                self.fillIndex(index)

    def extend(self, valueList):
        """
        As with regular python lists, this method appends all items in the
        list to this ref collection.
        """
        
        try:
            sd = self._setFlag(RefList.SETDIRTY, False)
            for value in valueList:
                self.append(value)
        finally:
            self._setFlag(RefList.SETDIRTY, sd)

        self._setDirty()

    def update(self, dictionary, setAliases=False):
        """
        As with regular python dictionary, this method appends all items in
        the dictionary to this ref collection.

        @param setAliases: if C{True}, the keys in the dictionary are used
        as aliases for the references added to this ref collection. The keys
        should be strings.
        @type setAliases: boolean
        """

        try:
            sd = self._setFlag(RefList.SETDIRTY, False)
            if setAliases:
                for alias, value in dictionary.iteritems():
                    self.append(value, alias)
            else:
                for value in dictionary.itervalues():
                    self.append(value)
        finally:
            self._setFlag(RefList.SETDIRTY, sd)

        self._setDirty()

    def append(self, item, alias=None):
        """
        Append an item to this ref collection.

        @param alias: if this optional argument is specified it becomes an
        alias with which the item can be looked up using the L{getByAlias}
        or L{resolveAlias} methods.
        @type alias: a string
        """

        if not item in self:
            self._item._references._addValue(self._name, item, self._otherName,
                                             alias=alias)

    def clear(self):
        """
        Remove all references from this ref collection.
        """

        try:
            sd = self._setFlag(RefList.SETDIRTY, False)
            key = self.firstKey()
            while key is not None:
                del self[key]
                key = self.firstKey()
        finally:
            self._setFlag(RefList.SETDIRTY, sd)

        self._setDirty()

    def dir(self):
        """
        Debugging: print all items referenced in this ref collection.
        """
        for item in self:
            print item._repr_()

    def __getitem__(self, key):

        return self._getRef(key)

    def _getRef(self, key, load=True):

        return super(RefList, self).__getitem__(key, load)

    def _setRef(self, other, **kwds):

        key = other._uuid
        load = kwds.get('load', True)
        loading = self._getRepository().isLoading()
        
        old = super(RefList, self).get(key, None, load)
        if not (loading or old is None):
            self.linkChanged(self._get(key), key)

        link = super(RefList, self).__setitem__(key, other,
                                                kwds.get('previous'),
                                                kwds.get('next'),
                                                kwds.get('alias'))

        if not loading:
            if self._indexes:
                for index in self._indexes.itervalues():
                    index.insertKey(key, link._previousKey)
            if old is None:
                self._setDirty(noMonitors=kwds.get('noMonitors', False))

        if not load:
            other._references._getRef(self._otherName, self._item)

#        if not loading:
#            item = self._item
#            onSetChange = getattr(type(item), 'onSetChange', None)
#            if onSetChange is not None:
#                onSetChange(item, 'add', item, self._name, other)

        return other

    def __setitem__(self, key, value):

        raise AssertionError, '%s: direct set not supported, use append' %(self)

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
        
        key = item._uuid
        if after is not None:
            afterKey = after._uuid
        else:
            afterKey = None

        if not indexNames:
            super(RefList, self).place(key, afterKey)
        else:
            for indexName in indexNames:
                self._index(indexName).moveKey(key, afterKey)
            self._setDirty()

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

    def replaceItem(self, item, with, *indexNames):
        """
        Replace an item in this collection with another one.

        Since an item can occur only once in a ref collection, if
        C{with} is in the collection already C{item} is removed and
        C{with} moved in its place.

        @param item: the item to replace
        @type item: an C{Item} instance
        @param with: the item to substitute in
        @type with: an C{Item} instance
        @param indexNames: zero or more names of indexes to place the item
        in instead of the collection's default intrinsic order
        """

        if with not in self:
            self.append(with)

        self.placeItem(with, item, *indexNames)
        self.remove(item)

    def removeItem(self, item):

        self.remove(item)

    def remove(self, item):
        """
        Remove an item from this ref collection.

        @param item: the item whose reference to remove.
        @type item: an C{Item} instance
        """

        self._item._references._removeValue(self._name, item, self._otherName)
            
    def __delitem__(self, key):

        self._item._references._removeValue(self._name, self._getRef(key),
                                            self._otherName)

    def _removeRef(self, other):

        if self._flags & RefList.READONLY:
            raise ReadOnlyAttributeError, (self._item, self._name)

        self._setDirty()
        key = other._uuid
        
        if self._indexes:
            for index in self._indexes.itervalues():
                index.removeKey(key)

        link = super(RefList, self).__delitem__(key)

#        item = self._item
#        onSetChange = getattr(type(item), 'onSetChange', None)
#        if onSetChange is not None:
#            onSetChange(item, 'remove', item, self._name, other)

        return link

    def _load(self, key):

        if self._flags & LinkedMap.NEW:
            return False

        ref = self._loadRef(key)
        if ref is None:
            return False
        
        repository = self._getRepository()
            
        try:
            loading = repository._setLoading(True)
            other = repository.find(key)
            if other is None:
                raise DanglingRefError, (self._item, self._name, key)
            
            self._setRef(other, previous=ref[0], next=ref[1], alias=ref[2],
                         load=False)
                    
            return True
        finally:
            repository._setLoading(loading, True)

        return False

    def _unload(self):

        references = self._item._references
        name = self._name
        otherName = self._otherName
        
        for link in self._values():
            # accessing _value directly to prevent reloading
            references._unloadValue(name, link._value, otherName)

    def linkChanged(self, link, key):

        if self._flags & RefList.READONLY:
            raise ReadOnlyAttributeError, (self._item, self._name)

        if key is not None:
            self._setDirty(noMonitors=True)

    def get(self, key, default=None, load=True):
        """
        Get the item referenced at C{key}.

        To get an item through its alias, use L{getByAlias} instead.

        @param key: the UUID of the item referenced.
        @type key: L{UUID<chandlerdb.util.uuid.UUID>}
        @param default: the default value to return if there is no reference
        for C{key} in this ref collection, C{None} by default.
        @type default: anything
        @param load: if the reference exists but hasn't been loaded yet,
        this method will return C{default} if this parameter is C{False}.
        @type load: boolean
        @return: an C{Item} instance or C{default}
        """

        return super(RefList, self).get(key, default, load)

    def getAlias(self, item):
        """
        Get the alias this item is keyed on in this collection.

        @param item: an item in the collection
        @type item: an L{Item<repository.item.Item.Item>} instance
        @return: the alias string or None if the item is not aliased
        """

        return self._get(item._uuid)._alias

    def setAlias(self, item, alias):

        return super(RefList, self).setAlias(item._uuid, alias)

    def getByIndex(self, indexName, position):
        """
        Get an item through its position in an index.

        C{position} is 0-based and may be negative to begin search from end
        going backwards with C{-1} being the index of the last element.

        C{IndexError} is raised if C{position} is out of range.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param position: the position of the item in the index
        @type position: integer
        @return: an C{Item} instance
        """

        return self[self._index(indexName).getKey(position)]

    def removeByIndex(self, indexName, position):
        """
        Remove an item through its position in an index.

        C{position} is 0-based and may be negative to begin search from end
        going backwards with C{-1} being the index of the last element.

        C{IndexError} is raised if C{position} is out of range.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param position: the position of the item in the index
        @type position: integer
        """

        del self[self._index(indexName).getKey(position)]

    def insertByIndex(self, indexName, position, item):
        """
        Insert an item at a position in an index.

        C{position} is 0-based and may be negative to begin search from end
        going backwards with C{-1} being the index of the last element.

        C{IndexError} is raised if C{position} is out of range.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param position: the position of the item in the index
        @type position: integer
        """

        if position == 0:
            after = None
        else:
            after = self._index(indexName).getKey(position - 1)
        self.insertItem(item, after, indexName)

    def replaceByIndex(self, indexName, position, with):
        """
        Replace an item with another item in its position in an index.

        C{position} is 0-based and may be negative to begin search from end
        going backwards with C{-1} being the index of the last element.

        C{IndexError} is raised if C{position} is out of range.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param position: the position of the item in the index to replace
        @type position: integer
        @param with: the item to substitute in
        @type with: an C{Item} instance
        """

        item = self[self._index(indexName).getKey(position)]
        self.replaceItem(self, item, with, indexName)

    def resolveIndex(self, indexName, position):

        return self._index(indexName).getKey(position)

    def getIndexPosition(self, indexName, item):
        """
        Return the position of an item in an index of this collection.

        Raises C{NoSuchItemInCollectionError} if the item is not in this
        collection.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param item: the item sought
        @type item: an C{Item} instance
        @return: the 0-based position of the item in the index.
        """

        if item in self:
            return self._index(indexName).getPosition(item._uuid)
        else:
            raise NoSuchItemInCollectionError, (self._item, self._name, item)

    def getIndexEntryValue(self, indexName, item):
        """
        Get an index entry value.

        Each entry in a index may store one integer value. This value is
        initialized to zero.

        @param indexName: the name of the index
        @type indexName: a string
        @param item: the item's whose index entry is to be set
        @type item: an L{Item<repository.item.Item.Item>} instance
        @return: the index entry value
        """
        
        return self._index(indexName).getEntryValue(item._uuid)

    def setIndexEntryValue(self, indexName, item, value):
        """
        Set an index entry value.

        Each index entry may store one integer value.

        @param indexName: the name of the index
        @type indexName: a string
        @param item: the item whose index entry is to be set
        @type item: an L{Item<repository.item.Item.Item>} instance
        @param value: the value to set
        @type value: int
        """

        self._index(indexName).setEntryValue(item._uuid, value)
        self._setDirty()

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

    def _refCount(self):

        return super(RefList, self).__len__() + 1

    def _xmlValue(self, name, item, generator, withSchema, version, attrs):

        attrs['name'] = name
        if withSchema:
            attrs['cardinality'] = 'list'
            attrs['otherName'] = item._kind.getOtherName(name, None, item)

        generator.startElement('ref', attrs)
        self._xmlValues(generator, version)
        if self._indexes:
            for name, index in self._indexes.iteritems():
                attrs = { 'name': name, 'type': index.getIndexType() }
                index._xmlValue(generator, version, attrs)
        generator.endElement('ref')

    def _xmlValues(self, generator, version):

        refs = self._item._references
        for key in self.iterkeys():
            link = self._get(key)
            refs._xmlRef(key, link.getValue(self),
                         generator, False, version, {},
                         previous=link._previousKey, next=link._nextKey,
                         alias=link._alias)

    def _saveValues(self, version):
        raise NotImplementedError, "%s._saveValues" %(type(self))

    def copy(self):
        """
        This method is not directly supported on this class.

        To copy a ref collection into another one, call L{extend} with this
        collection on the target collection.
        """
        
        raise NotImplementedError, 'RefList.copy is not supported'

    def first(self, indexName=None):
        """
        Get the first item referenced in this ref collection.

        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if empty.
        """

        if indexName is None:
            firstKey = self.firstKey()
        else:
            firstKey = self._index(indexName).getFirstKey()
            
        if firstKey is not None:
            return self[firstKey]

        return None

    def last(self, indexName=None):
        """
        Get the last item referenced in this ref collection.

        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if empty.
        """

        if indexName is None:
            lastKey = self.lastKey()
        else:
            lastKey = self._index(indexName).getLastKey()
            
        if lastKey is not None:
            return self[lastKey]

        return None

    def next(self, previous, indexName=None):
        """
        Get the next referenced item relative to previous.

        @param previous: the previous item relative to the item sought.
        @type previous: a C{Item} instance
        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if C{previous} is the last
        referenced item in the collection.
        """

        key = previous._uuid

        try:
            if indexName is None:
                nextKey = self.nextKey(key)
            else:
                nextKey = self._index(indexName).getNextKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                raise NoSuchItemInCollectionError, (self._item, self._name,
                                                    previous)

        if nextKey is not None:
            return self[nextKey]

        return None

    def previous(self, next, indexName=None):
        """
        Get the previous referenced item relative to next.

        @param next: the next item relative to the item sought.
        @type next: a C{Item} instance
        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if next is the first
        referenced item in the collection.
        """

        key = next._uuid

        try:
            if indexName is None:
                previousKey = self.previousKey(key)
            else:
                previousKey = self._index(indexName).getPreviousKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                raise NoSuchItemInCollectionError, (self._item, self._name,
                                                    next)

        if previousKey is not None:
            return self[previousKey]

        return None

    def iterkeys(self, indexName=None):

        if indexName is None:
            for key in super(RefList, self).iterkeys():
                yield key

        else:
            index = self._index(indexName)
            nextKey = index.getFirstKey()
            while nextKey is not None:
                key = nextKey
                nextKey = index.getNextKey(nextKey)
                yield key

    def itervalues(self, indexName=None):

        for key in self.iterkeys(indexName):
            yield self[key]

    def iteritems(self, indexName=None):

        for key in self.iterkeys(indexName):
            yield (key, self[key])

    def setDescending(self, indexName, descending=True):

        self._index(indexName).setDescending(descending)
        self._setDirty(noMonitors=True)

    def _index(self, indexName):

        if self._indexes is None:
            raise NoSuchIndexError, (self._item, self._name, indexName)

        try:
            return self._indexes[indexName]
        except KeyError:
            raise NoSuchIndexError, (self._item, self._name, indexName)

    def check(self, logger, name, item):
        """
        Debugging: verify this ref collection for consistency.

        Consistency errors are logged.

        @return: C{True} if no errors were found, {False} otherwise.
        """

        l = len(self)
        logger = self._getRepository().logger

        if item is not self._item or name != self._name:
            logger.error('Ref collection not owned by %s.%s: %s',
                         self._item.itsPath, self._name, self)
            return False
        
        refs = self._item._references
        result = True

        key = self.firstKey()
        prevKey = None
        while key:
            try:
                other = self._getRef(key)
                result = result and refs._checkRef(logger, name, other)
            except DanglingRefError, e:
                logger.error("Iterator on %s caused DanglingRefError: %s",
                             self, str(e))
                return False
            except BadRefError, e:
                logger.error("Iterator on %s caused BadRefError: %s",
                             self, str(e))
                return False
            l -= 1
            prevKey = key
            key = self.nextKey(key)
            
        if l != 0:
            logger.error("Iterator on %s doesn't match length (%d left for %d total)", self, l, len(self))
            return False

        if prevKey != self.lastKey():
            logger.error("iterator on %s doesn't finish on last key %s but on %s", self, self.lastKey(), prevKey)
            return False

        return result

    def _clearDirties(self):
        pass

    def _hashValues(self):

        hash = 0
        for key in self.iterkeys():
            link = self._get(key)
            hash = _combine(hash, key._hash)
            if link._alias is not None:
                hash = _combine(hash, _hash(link._alias))

        return hash
    
    SETDIRTY = 0x0002
    READONLY = 0x0004


class TransientRefList(RefList):
    """
    A ref collection class for transient attributes.
    """

    def __init__(self, item, name, otherName, readOnly):

        super(TransientRefList, self).__init__(item, name, otherName, readOnly,
                                               True)

    def linkChanged(self, link, key):
        pass
    
    def check(self, logger, name, item):
        return True

    def _load(self, key):
        return False
    
    def _isTransient(self):
        return True

    def _setDirty(self, noMonitors=False):
        pass

    def _unloadRef(self, item):

        key = item._uuid

        if self.has_key(key, load=False):
            link = self._get(key, load=False)
            if link is not None:
                if link._alias is not None:
                    del self._aliases[link._alias]
                    self._remove(key)                   
            else:
                raise AssertionError, '%s: unloading non-loaded ref %s' %(self, item._repr_())
