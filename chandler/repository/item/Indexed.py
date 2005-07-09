
__revision__  = "$Revision: 5719 $"
__date__      = "$Date: 2005-06-21 13:15:07 -0700 (Tue, 21 Jun 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Indexes import AttributeIndex, CompareIndex
from chandlerdb.item.ItemError import *


# A mixin class used by ref collections and abstract sets that provides
# indexing functionality.

class Indexed(object):

    def _index(self, indexName):

        if self._indexes is None:
            item, name = self._getOwner()
            raise NoSuchIndexError, (item, name, indexName)

        try:
            return self._indexes[indexName]
        except KeyError:
            item, name = self._getOwner()
            raise NoSuchIndexError, (item, name, indexName)

    def addIndex(self, indexName, indexType, **kwds):
        """
        Add an index to this collection.

        A collection index provides positional access into the collection
        and maintains a key order which is be determined by the sequence of
        collection mutation operations or by constraints on values.

        A collection may have any number of indexes. Each index has a
        name which is used with the L{getByIndex}, L{getIndexEntryValue},
        L{setIndexEntryValue}, L{resolveIndex}, L{first}, L{last}, L{next},
        L{previous} methods.

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

        item, name = self._getOwner()

        if self._indexes is not None:
            if indexName in self._indexes:
                raise IndexAlreadyExists, (item, name, indexName)
        else:
            self._indexes = {}

        index = self._createIndex(indexType, **kwds)
        self._indexes[indexName] = index

        if not self._getView().isLoading():
            self.fillIndex(index)
            self._setDirty(True) # noMonitors=True

            if indexType == 'attribute':
                from repository.item.Monitors import Monitors
                Monitors.attach(item, '_reIndex',
                                'set', kwds['attribute'], name, indexName)

        return index

    def setDescending(self, indexName, descending=True):

        self._index(indexName).setDescending(descending)
        self._setDirty(True) # noMonitors=True 

    def _createIndex(self, indexType, **kwds):

        if indexType == 'numeric':
            return self._getView()._createNumericIndex(**kwds)

        if indexType == 'attribute':
            return AttributeIndex(self, self._createIndex('numeric', **kwds),
                                  **kwds)

        if indexType == 'compare':
            return CompareIndex(self, self._createIndex('numeric', **kwds),
                                **kwds)

        raise NotImplementedError, "indexType: %s" %(indexType)

    def removeIndex(self, indexName):

        if self._indexes is None or indexName not in self._indexes:
            item, name = self._getOwner()
            raise NoSuchIndexError, (item, name, indexName)

        del self._indexes[indexName]
        self._setDirty(True) # noMonitors=True

    def fillIndex(self, index):

        prevKey = None
        for key in self.iterkeys():
            index.insertKey(key, prevKey)
            prevKey = key

    def _restoreIndexes(self, view):

        item, name = self._getOwner()

        for index in self._indexes.itervalues():
            if index.isPersistent():
                index._restore(item._version)
            else:
                self.fillIndex(index)

    def _saveIndexes(self, itemWriter, buffer, version):

        size = 0
        for name, index in self._indexes.iteritems():
            itemWriter.writeSymbol(buffer, name)
            itemWriter.writeSymbol(buffer, index.getIndexType())
            index._writeValue(itemWriter, buffer)
            size += index._saveValues(version)

        return size

    def _loadIndex(self, itemReader, offset, data):

        offset, indexName = itemReader.readSymbol(offset, data)
        offset, indexType = itemReader.readSymbol(offset, data)
        index = self.addIndex(indexName, indexType, loading=True)

        return index._readValue(itemReader, offset, data)

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

        raise NotImplementedError, "%s.removeByIndex" %(type(self))

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

        raise NotImplementedError, "%s.insertByIndex" %(type(self))

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

        raise NotImplementedError, "%s.replaceByIndex" %(type(self))

    def placeInIndex(self, item, after, *indexNames):
        """
        Place an item in one or more indexes after another one.

        Both items must already belong to the collection. To place an item
        first, pass C{None} for C{after}.

        @param item: the item to place, must belong to the collection.
        @type item: an C{Item} instance
        @param after: the item to place C{item} after or C{None} if C{item} is
        to be first in this collection.
        @type after: an C{Item} instance
        @param indexNames: one or more names of indexes to place the item in.
        @type indexNames: strings
        """

        key = item._uuid
        if after is not None:
            afterKey = after._uuid
        else:
            afterKey = None

        for indexName in indexNames:
            self._index(indexName).moveKey(key, afterKey)

        self._setDirty()

    def iterindexkeys(self, indexName):

        index = self._index(indexName)
        nextKey = index.getFirstKey()

        while nextKey is not None:
            key = nextKey
            nextKey = index.getNextKey(nextKey)
            yield key

    def iterindexvalues(self, indexName):

        for key in self.iterindexkeys(indexName):
            yield self[key]

    def iterindexitems(self, indexName):

        for key in self.iterindexkeys(indexName):
            yield (key, self[key])

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
            ownerItem, name = self._getOwner()
            raise NoSuchItemInCollectionError, (ownerItem, name, item)

    def firstInIndex(self, indexName):
        """
        Get the first item referenced in the named index.

        @param indexName: the name of an index of this collection.
        @type indexName: a string
        @return: an C{Item} instance or C{None} if empty.
        """

        firstKey = self._index(indexName).getFirstKey()
        if firstKey is not None:
            return self[firstKey]

        return None

    def lastInIndex(self, indexName):
        """
        Get the last item referenced in the named index.

        @param indexName: the name of an index of this collection.
        @type indexName: a string
        @return: an C{Item} instance or C{None} if empty.
        """

        lastKey = self._index(indexName).getLastKey()
        if lastKey is not None:
            return self[lastKey]

        return None

    def nextInIndex(self, previous, indexName):
        """
        Get the next referenced item relative to previous in the named index.

        @param previous: the previous item relative to the item sought.
        @type previous: a C{Item} instance
        @param indexName: the name of an index of this collection.
        @type indexName: a string
        @return: an C{Item} instance or C{None} if C{previous} is the last
        referenced item in the collection.
        """

        key = previous._uuid

        try:
            nextKey = self._index(indexName).getNextKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                item, name = self._getOwner()
                raise NoSuchItemInCollectionError, (item, name, previous)

        if nextKey is not None:
            return self[nextKey]

        return None

    def previousInIndex(self, next, indexName):
        """
        Get the previous referenced item relative to next in the named index.

        @param next: the next item relative to the item sought.
        @type next: a C{Item} instance
        @param indexName: the name of an index of this collection.
        @type indexName: a string
        @return: an C{Item} instance or C{None} if next is the first
        referenced item in the collection.
        """

        key = next._uuid

        try:
            previousKey = self._index(indexName).getPreviousKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                item, name = self._getOwner()
                raise NoSuchItemInCollectionError, (item, name, next)

        if previousKey is not None:
            return self[previousKey]

        return None
