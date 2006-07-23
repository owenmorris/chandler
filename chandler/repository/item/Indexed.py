#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


from repository.item.Indexes import \
    AttributeIndex, ValueIndex, StringIndex, CompareIndex, SubIndex
from chandlerdb.item.ItemError import *


# A mixin class used by ref collections and abstract sets that provides
# indexing functionality.

class Indexed(object):

    # a real constructor cannot be used here because super won't get to it
    def _init_indexed(self):

        self._indexes = None

    def getIndex(self, indexName):

        if self._indexes is None:
            item, name = self._getOwner()
            raise NoSuchIndexError, (item, name, indexName)

        index = self._indexes.get(indexName)
        if index is None:
            item, name = self._getOwner()
            raise NoSuchIndexError, (item, name, indexName)

        return index

    def _anIndex(self):

        if self._indexes:
            return self._indexes.itervalues().next()

        return None

    def hasIndex(self, name):
        """
        Tell whether this indexed collection has an index by a given name.

        @param name: the name of the index sought
        @type name: string
        @return: boolean
        """

        return self._indexes and name in self._indexes

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

            - C{attribute}: an index sorted on the value of one or more
              attributes of items in the collection. The name of the
              attribute(s) is provided via the C{attribute} or C{attributes}
              keyword.

            - C{string}: an index sorted by locale-specific collation on the
              value of a string attribute of items in the collection. The
              name of the attribute is provided via the C{attribute}
              keyword. The locale name is provided via the C{locale} keyword.

            - C{compare}: an index sorted on the return value of a method
              invoked on items in the collection. The method is a comparison
              method whose name is provided with the C{compare} keyword, and
              it is invoked on C{i0}, with the other item being compared,
              C{i1}, and is expected to return a positive number if, in the
              context of this index, C{i0 > i1}, a negative number if C{i0 <
              i1}, or zero if C{i0 == i1}.

        By default, the C{attribute} and C{string} indexes monitor the
        attribute by which they are sorted in order to remain sorted. Which
        attribute(s) are monitored can be overriden by specifying one or
        more attribute names via the C{monitor} keyword.

        The C{attribute} and C{string} sorted indexes treat a missing or
        C{None} value as infinitely large.

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

        if not (self._getView().isLoading() or kwds.get('loading', False)):
            self.fillIndex(index)
            self._setDirty(True) # noMonitors=True
            monitor = kwds.get('monitor')

            if monitor is not None:
                from repository.item.Monitors import Monitors
                if isinstance(monitor, (str, unicode)):
                    Monitors.attach(item, '_reIndex',
                                    'set', monitor, name, indexName)
                    Monitors.attach(item, '_reIndex',
                                    'remove', monitor, name, indexName)
                else:
                    for m in monitor:
                        Monitors.attach(item, '_reIndex',
                                        'set', m, name, indexName)
                        Monitors.attach(item, '_reIndex',
                                        'remove', m, name, indexName)
                    
            elif indexType in ('attribute', 'value', 'string'):
                from repository.item.Monitors import Monitors
                attributes = kwds.get('attributes', None)
                if attributes is not None:
                    for attribute in attributes:
                        Monitors.attach(item, '_reIndex',
                                        'set', attribute, name, indexName)
                        Monitors.attach(item, '_reIndex',
                                        'remove', attribute, name, indexName)
                else:
                    attribute = kwds['attribute']
                    Monitors.attach(item, '_reIndex',
                                    'set', attribute, name, indexName)
                    Monitors.attach(item, '_reIndex',
                                    'remove', attribute, name, indexName)

            if indexType == 'subindex':
                uuid, superName, superIndexName = index._super
                superIndex = getattr(self._getView()[uuid],
                                     superName).getIndex(superIndexName)
                superIndex.addSubIndex(item.itsUUID, name, indexName)

        self._indexes[indexName] = index
        return index

    def setRanges(self, indexName, ranges):

        self.getIndex(indexName).setRanges(ranges)
        self._setDirty(True)

    def getRanges(self, indexName):

        return self.getIndex(indexName).getRanges()

    def isInRanges(self, indexName, range):

        return self.getIndex(indexName).isInRanges(range)

    def addRange(self, indexName, range):

        self.getIndex(indexName).addRange(range)
        self._setDirty(True)

    def removeRange(self, indexName, range):

        self.getIndex(indexName).removeRange(range)
        self._setDirty(True)

    def setDescending(self, indexName, descending=True):

        if self.getIndex(indexName).setDescending(descending) != descending:
            self._setDirty(True) # noMonitors=True 

    def isDescending(self, indexName):

        return self.getIndex(indexName).isDescending()

    def _collectIndexChanges(self, name, indexChanges):

        indexes = self._indexes
        if indexes:
            _indexChanges = {}

            for indexName, index in indexes.iteritems():
                if index._needsReindexing():
                    _indexChanges[indexName] = dict(index._iterChanges())

            if _indexChanges:
                indexChanges[name] = _indexChanges

    def _applyIndexChanges(self, view, indexChanges, deletes):

        indexes = self._indexes
        for name, _indexChanges in indexChanges.iteritems():
            index = indexes[name]

            moves = []
            insertions = []

            for key, value in _indexChanges.iteritems():
                if value is not None:
                    item = view.find(key)
                    if item is None:
                        if key not in deletes:
                            raise AssertionError, (key, "item not found")
                    elif item.isDirty():
                        if key in index:
                            moves.append(key)
                        else:
                            insertions.append(key)
                elif key in index:
                    index.removeKey(key)

            index.moveKeys(moves)
            for key in insertions:
                index.insertKey(key)

    def _createIndex(self, indexType, **kwds):

        if indexType == 'numeric':
            return self._getView()._createNumericIndex(**kwds)

        if indexType == 'attribute':
            return AttributeIndex(self, self._createIndex('numeric', **kwds),
                                  **kwds)

        if indexType == 'value':
            return ValueIndex(self, self._createIndex('numeric', **kwds),
                              **kwds)

        if indexType == 'string':
            return StringIndex(self, self._createIndex('numeric', **kwds),
                               **kwds)

        if indexType == 'compare':
            return CompareIndex(self, self._createIndex('numeric', **kwds),
                                **kwds)

        if indexType == 'subindex':
            return SubIndex(self, self._createIndex('numeric', **kwds),
                            **kwds)

        raise NotImplementedError, "indexType: %s" %(indexType)

    def removeIndex(self, indexName):

        if self._indexes is None or indexName not in self._indexes:
            item, name = self._getOwner()
            raise NoSuchIndexError, (item, name, indexName)

        index = self._indexes[indexName]
        if index.getIndexType() == 'subindex':
            uuid, superName, superIndexName = index._super
            item, name = self._getOwner()
            superIndex = getattr(self._getView()[uuid],
                                 superName).getIndex(superIndexName)
            superIndex.removeSubIndex(item.itsUUID, name, indexName)

        del self._indexes[indexName]
        self._setDirty(True) # noMonitors=True

    def fillIndex(self, index):

        prevKey = None
        for key in self.iterkeys():
            index.insertKey(key, prevKey)
            prevKey = key

    def _restoreIndexes(self, *ignore):  # extra afterLoad callback view arg

        item, name = self._getOwner()

        for index in self._indexes.itervalues():
            if index.isPersistent():
                index._restore(item.itsVersion)
            else:
                self.fillIndex(index)

    def _saveIndexes(self, itemWriter, buffer, version):

        size = 0
        for name, index in self._indexes.iteritems():
            itemWriter.writeSymbol(buffer, name)
            itemWriter.writeSymbol(buffer, index.getIndexType())
            index._writeValue(itemWriter, buffer, version)
            size += index._saveValues(version)

        return size

    def _clearIndexDirties(self):

        if self._indexes:
            for index in self._indexes.itervalues():
                index._clearDirties()

    def _loadIndex(self, itemReader, offset, data):

        offset, indexName = itemReader.readSymbol(offset, data)
        offset, indexType = itemReader.readSymbol(offset, data)
        index = self.addIndex(indexName, indexType, loading=True)

        return index._readValue(itemReader, offset, data)

    def findInIndex(self, indexName, mode, callable, *args):
        """
        Find a key in a sorted index via binary search.

        The C{mode} argument determines how the search is directed and can
        take the following values:
            - C{exact}: as soon as a match is found it is returned
            - C{first}: the lowest match in sort order is returned
            - C{last}: the highest match in sort order is returned

        The notion of match is defined by the C{callable}
        implementation. For example, a collection of events sorted by start
        time can be searched to return the first or the last match in a date
        range.

        The predicate implementation provided by C{callable} must take at
        least one argument, a key into the index and must return 0 when
        the corresponding value is 'equal' to the value sought, -1 when the
        value is 'less than' the value sought and 1 otherwise.
        The comparisons must be consistent with the sort order of the index.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param mode: the mode of the search (see above)
        @type mode: a string
        @param callable: the predicate implementation
        @type callable: a python callable function or method
        @param args: extra arguments to pass to the predicate
        @return: a C{UUID} key or C{None} if no match was found
        """

        return self._indexes[indexName].findKey(mode, callable, *args)

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

        return self[self.getIndex(indexName).getKey(position)]

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

        key = item.itsUUID
        if after is not None:
            afterKey = after.itsUUID
        else:
            afterKey = None

        for indexName in indexNames:
            self.getIndex(indexName).moveKey(key, afterKey)

        self._setDirty(True)

    def iterindexkeys(self, indexName, first=None, last=None):

        for key in self.getIndex(indexName).iterkeys(first, last):
            yield key

    def iterindexvalues(self, indexName, first=None, last=None):

        for key in self.iterindexkeys(indexName, first, last):
            yield self[key]

    def iterindexitems(self, indexName, first=None, last=None):

        for key in self.iterindexkeys(indexName, first, last):
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
        
        return self.getIndex(indexName).getEntryValue(item.itsUUID)

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

        self.getIndex(indexName).setEntryValue(item.itsUUID, value)
        self._setDirty()

    def resolveIndex(self, indexName, position):

        return self.getIndex(indexName).getKey(position)

    def positionInIndex(self, indexName, item):
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
            return self.getIndex(indexName).getPosition(item.itsUUID)

        ownerItem, name = self._getOwner()
        raise NoSuchItemInCollectionError, (ownerItem, name, item)

    def firstInIndex(self, indexName):
        """
        Get the first item referenced in the named index.

        @param indexName: the name of an index of this collection.
        @type indexName: a string
        @return: an C{Item} instance or C{None} if empty.
        """

        firstKey = self.getIndex(indexName).getFirstKey()
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

        lastKey = self.getIndex(indexName).getLastKey()
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

        key = previous.itsUUID

        try:
            nextKey = self.getIndex(indexName).getNextKey(key)
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

        key = next.itsUUID

        try:
            previousKey = self.getIndex(indexName).getPreviousKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                item, name = self._getOwner()
                raise NoSuchItemInCollectionError, (item, name, next)

        if previousKey is not None:
            return self[previousKey]

        return None

    def getIndexSize(self, indexName):

        return len(self.getIndex(indexName))

    def _checkIndexes(self, logger, item, attribute):

        result = True

        if self._indexes:
            try:
                indexes = self._indexes
                self._indexes = None
                count = len(self)
            finally:
                self._indexes = indexes

            for name, index in self._indexes.iteritems():
                if not index._checkIndex(index, logger, name, self,
                                         item, attribute, count):
                    result = False
                    
        return result
