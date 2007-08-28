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


from chandlerdb.persistence.c import Record
from chandlerdb.item.ItemError import *
from chandlerdb.util.c import Nil, Default
from repository.item.Indexes import __index_classes__


# A mixin class used by ref collections and abstract sets that provides
# indexing functionality.

class Indexed(object):

    # a real constructor cannot be used here because super won't get to it
    def _init_indexed(self):

        self._indexes = None

    def getIndex(self, indexName, default=Default):

        if self._indexes is None:
            item, name = self.itsOwner
            if default is Default:
                raise NoSuchIndexError, (item, name, indexName)
            return default

        index = self._indexes.get(indexName)
        if index is None:
            item, name = self.itsOwner
            if default is Default:
                raise NoSuchIndexError, (item, name, indexName)
            return default

        return index

    def _removeIndexes(self):

        if self._indexes:
            for name in self._indexes.keys():
                self.removeIndex(name)

    def _anIndex(self, exclude=Nil):

        if self._indexes:
            for index in self._indexes.itervalues():
                if index not in exclude:
                    return index

        return None

    def _reindex(self, index, key):

        item, attribute = self.itsOwner
        indexes = self._indexes
        for monitor in getattr(item, 'monitors', Nil):
            x, x, name = monitor.getItemIndex()
            if indexes.get(name) is index:
                monitor('set', item.itsView[key], monitor.attribute)
                break

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
        name which is used with the L{getByIndex}, L{resolveIndex},
        L{first}, L{last}, L{next}, L{previous} methods.

        The type of index to create is specified with the C{indexType}
        parameter. It can have one of the following values:

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

            - C{method}: as with C{compare}, an index sorted on the return
              value of a method invoked on a third party item. The method is
              a comparison method whose item and name are provided as a
              tuple with the C{method} keyword. Two methods are expected to
              be implemented on the third party item: the named method and
              another method with that name suffixed with C{_init}. The
              named method is expected to accept four arguments: the index
              object, the two C{UUID} keys being compared, C{k0} and C{k1},
              and C{vals}, a C{dict} that can be used to cache values for
              the keys the method will be invoked with. C{vals} always
              contains the value for C{k0} since it is returned by the
              C{_init} suffixed method which is invoked first with the index
              object, C{k0} and C{vals}. The comparison method should check
              C{vals} for values for C{k0} and C{k1} as it is normally
              faster to do this check than to compute or fetch the actual
              values from the database.

            - C{subindex}: an index that is a subset of another index whose
              keys are following the order of the superindex. The set the
              subindex is indexing must be a subset of the set the
              superindex is indexing.

        By default, the C{attribute} and C{string} indexes monitor the
        attribute by which they are sorted in order to remain sorted. Which
        attribute(s) are monitored may be overridden for these types of
        indexes with the C{monitor} keyword. Likewise, which attributes to
        monitor for the C{compare} and C{method} types of indexes can be
        specified with one or more attribute names in a tuple via the
        C{monitor} keyword.

        The C{attribute} and C{string} sorted indexes treat a missing or
        C{None} value as infinitely large.

        In addition to the C{subindex} type of index, the C{compare} or
        C{method} types of indexes can be defined as the subindex of another
        index as long as it indexes a subset of the set indexed by the
        chosen superindex in the same order. This has the advantage that the
        subindex no longer has to monitor the attribute(s) that are used to
        sort the superindex as the superindex will reindex its subindexes as
        needed. The methods used to compute the comparison values of two
        keys can use the difference in the keys' positions in the superindex
        instead of computing a more expensive comparison value. The
        superindex is specified with the C{superindex} keyword.

        To ensure that an index is still reindexed when reindexing is
        deferred via C{with view.reindexingDeferred():} use the C{nodefer}
        keyword set to C{True}.

        @param indexName: the name of the index
        @type indexName: a string
        @param indexType: the type of index
        @type indexType: a string
        """

        item, name = self.itsOwner
        view = self.itsView

        if self._indexes is not None:
            if indexName in self._indexes:
                raise IndexAlreadyExists, (item, name, indexName)
        else:
            self._indexes = {}

        isSubIndex = 'superindex' in kwds
        index = self._createIndex(indexType, **kwds)

        if not (view.isLoading() or kwds.get('loading', False)):

            if isSubIndex:
                uuid, superName, superIndexName = index._super
                superset = getattr(view[uuid], superName)
                reasons = set()
                if not self.isSubset(superset, reasons):
                    raise ValueError, "To support a subindex, %s must be a subset of %s but %s" %(self, superset, ', '.join("%s.%s is not a subset of %s.%s" %(sub_i._repr_(), sub_a, sup_i._repr_(), sup_a) for (sub_i, sub_a), (sup_i, sup_a) in ((sub.itsOwner, sup.itsOwner) for sub, sup in reasons)))

            self.fillIndex(index)
            self._setDirty(True) # noFireChanges=True
            monitor = kwds.get('monitor')
            kind = kwds.get('kind')
            correlation = set()

            def _attach(attrName, correlation):
                from repository.item.Monitors import Monitors
                Monitors.attachIndexMonitor(item, 'set',
                                            attrName, name, indexName)
                Monitors.attachIndexMonitor(item, 'remove',
                                            attrName, name, indexName)
                correlation.add(attrName)

            if monitor is not None:
                if isinstance(monitor, (str, unicode)):
                    _attach(monitor, correlation)
                else:
                    for m in monitor:
                        _attach(m, correlation)
                    
            elif indexType in ('attribute', 'value', 'string'):
                attributes = kwds.get('attributes', None)
                if attributes is not None:
                    for attribute in attributes:
                        _attach(attribute, correlation)
                else:
                    _attach(kwds['attribute'], correlation)

            if len(correlation) > 1:
                if kind is None:
                    view.logger.warn("Attributes (%s) in index (%s, %s, %s) are correlated but the kind of the items being indexed is not declared. This correlation will not be heeded during view merges", tuple(correlation), item._repr_(), name, indexName)
                else:
                    kind.declareCorrelation(correlation)

            if isSubIndex:
                superIndex = superset.getIndex(superIndexName)
                superIndex.addSubIndex(item.itsUUID, name, indexName)
                if not superIndex.isValid():
                    index.validateIndex(False)

            view._newIndexes.append((item.itsUUID, name, indexName))

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
            self._setDirty(True) # noFireChanges=True 

    def isDescending(self, indexName):

        return self.getIndex(indexName).isDescending()

    def _collectIndexChanges(self, view, name, indexChanges):

        indexes = self._indexes
        if indexes:
            _indexChanges = {}

            for indexName, index in indexes.iteritems():
                changes = {}
                for uItem, value in index._iterChanges():
                    for key in view.findValue(uItem, 'inheritTo',
                                              Nil).iterkeys():
                        if key in index:
                            changes[key] = key
                changes.update(index._iterChanges())
                _indexChanges[indexName] = [False, changes,
                                            index.getIndexType(),
                                            index.getInitKeywords()]
            if _indexChanges:
                indexChanges[name] = _indexChanges

    def _applyIndexChanges(self, view, indexChanges,
                           name, _indexChanges, deletes):

        done, __indexChanges, type, kwds = _indexChanges
        if not done:
            _indexChanges[0] = done = True

            def getChanges(uItem, attrName, indexName):
                changes = indexChanges.get(uItem)
                if changes is not None:
                    changes = changes.get(attrName)
                    if changes is not None:
                        return changes.get(indexName)

            if 'superindex' in kwds:
                uItem, attr, superName = kwds['superindex']
                superChanges = getChanges(uItem, attr, superName)
                if superChanges is not None:
                    getattr(view[uItem], attr)._applyIndexChanges(view, indexChanges, superName, superChanges, deletes)

            indexes = self._indexes
            if indexes is None:
                self._indexes = indexes = {}

            index = indexes.get(name)
            if index is None:
                if 'ranges' in kwds:
                    kwds['ranges'] = ()  # bug 7123
                indexes[name] = index = self._createIndex(type, **kwds)
                newIndex = True
            else:
                newIndex = False
                if 'ranges' in kwds:
                    index.setRanges(())  # bug 7123

            if 'superindex' in kwds: # bug 7324
                item, attr = index._valueMap.itsOwner
                uItem, superAttr, superName = index._super
                superset = getattr(view[uItem], superAttr)
                superIndex = superset.getIndex(superName)
                superIndex.addSubIndex(item.itsUUID, attr, name)

            if 'subindexes' in kwds: # bug 7324
                if getattr(index, '_subIndexes', None) is None:
                    index._subIndexes = set()
                for subIndex in kwds['subindexes']:
                    uItem, attr, subName = subIndex
                    item = view.find(uItem, False)
                    if item is not None:
                        indexed = getattr(item, attr, Nil)
                        if indexed is not Nil:
                            indexes = getattr(indexed, '_indexes', None)
                            if indexes and subName in indexes:
                                index.addSubIndex(uItem, attr, subName)
                                subChanges = getChanges(uItem, attr, subName)
                                if subChanges is not None:
                                    indexes[subName].validateIndex(False, False,
                                                                   False)

            removals = list(deletes)
            moves = []

            for key, value in __indexChanges.iteritems():
                if value is not None:
                    item = view.find(key)
                    if item is None:
                        if key not in deletes:
                            view.logger.warn("_applyIndexChanges: item %s not found", key)
                            removals.append(key)
                    elif newIndex or value is Nil:
                        if self.__contains__(key, False, True):
                            moves.append(key)
                    elif not self.__contains__(key, False, True):
                        # a neighbor key could be dirty but no longer a member
                        removals.append(key)
                    else:
                        moves.append(key)
                elif key in index:
                    removals.append(key)

            index.removeKeys(removals)
            index.moveKeys(moves, Default, True)
            if not index.isValid():
                index.validateIndex(True, True, False)

    def _createIndex(self, indexType, **kwds):

        if indexType == 'numeric':
            return self.itsView._createNumericIndex(**kwds)

        cls = __index_classes__.get(indexType)
        if cls is not None:
            return cls(self, self._createIndex('numeric', **kwds), **kwds)

        raise NotImplementedError, "indexType: %s" %(indexType)

    def removeIndex(self, indexName):

        item, name = self.itsOwner

        if self._indexes is None or indexName not in self._indexes:
            raise NoSuchIndexError, (item, name, indexName)

        index = self._indexes[indexName]
        if hasattr(index, '_super'):
            uuid, superName, superIndexName = index._super
            try:
                superValue = getattr(item.itsView[uuid], superName)
                superIndex = superValue._indexes[superIndexName]
                superIndex.removeSubIndex(item.itsUUID, name, indexName)
            except (AttributeError, KeyError):
                # no super value, no super index or sub-index not found
                pass

        indexRef = (item.itsUUID, name, indexName)
        monitors = [monitor for monitor in getattr(item, 'monitors', Nil)
                    if monitor.getItemIndex() == indexRef]
        for monitor in monitors:
            monitor.delete()

        del self._indexes[indexName]

        index = (item.itsUUID, name, indexName)
        newIndexes = item.itsView._newIndexes
        for i in xrange(len(newIndexes)):
            if newIndexes[i] == index:
                del newIndexes[i]
                break

        self._setDirty(True) # noFireChanges=True

    def fillIndex(self, index, excludeIndexes=False):

        prevKey = None
        for key in self.iterkeys(excludeIndexes):
            index.insertKey(key, prevKey)
            prevKey = key

    def _restoreIndexes(self, *ignore):  # extra afterLoad callback view arg

        item, name = self.itsOwner

        for index in self._indexes.itervalues():
            if index.isPersistent():
                index._restore(item.itsVersion)
            else:
                self.fillIndex(index)

    def _saveIndexes(self, itemWriter, record, version):

        size = 0
        for name, index in self._indexes.iteritems():
            record += (Record.SYMBOL, name,
                       Record.SYMBOL, index.getIndexType())
            index._writeValue(itemWriter, record, version)
            size += index._saveValues(version)

        return size

    def _clearDirties(self):

        if self._indexes:
            for index in self._indexes.itervalues():
                index._clearDirties()

    def _loadIndex(self, itemReader, offset, data):

        indexName = data[offset]
        indexType = data[offset + 1]
        index = self.addIndex(indexName, indexType, loading=True)

        return index._readValue(itemReader, offset + 2, data)

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

    def replaceByIndex(self, indexName, position, withItem):
        """
        Replace an item with another item in its position in an index.

        C{position} is 0-based and may be negative to begin search from end
        going backwards with C{-1} being the index of the last element.

        C{IndexError} is raised if C{position} is out of range.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param position: the position of the item in the index to replace
        @type position: integer
        @param withItem: the item to substitute in
        @type withItem: an C{Item} instance
        """

        raise NotImplementedError, "%s.replaceByIndex" %(type(self))

    def placeInIndex(self, item, after, insertMissing, *indexNames):
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
            self.getIndex(indexName).moveKey(key, afterKey, insertMissing)

        self._setDirty(True)

    def reindexKeys(self, keys, insertMissing, *indexNames):
        """
        Re-index an iterable of keys in one or more indexes.

        The keys are first removed from the index and then re-inserted.
        This is useful with sorted indexes whose sort order is currently
        invalid because the items behind the C{keys} have changed in a way
        that invalidated it.

        C{keys} must be iterable more than once.
        """

        for indexName in indexNames:
            self.getIndex(indexName).moveKeys(keys, Default, insertMissing)

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

        ownerItem, name = self.itsOwner
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
                item, name = self.itsOwner
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
                item, name = self.itsOwner
                raise NoSuchItemInCollectionError, (item, name, next)

        if previousKey is not None:
            return self[previousKey]

        return None

    def getIndexSize(self, indexName):

        return len(self.getIndex(indexName))

    def _rebuildIndex(self, logger, index, item, attribute, name,
                      subIndexes=True):
        
        logger.warning("Rebuilding index '%s' installed on value '%s' of type %s in attribute '%s' on %s", name, self, type(self), attribute, item._repr_())

        view = item.itsView
        kwds = index.getInitKeywords()
        if 'ranges' in kwds:
            kwds['ranges'] = ()

        index = self._createIndex(index.getIndexType(), **kwds)
        self._indexes[name] = index

        self.fillIndex(index, True)

        for uItem, attribute, name in kwds.get('subindexes', Nil):
            index.addSubIndex(uItem, attribute, name)
            if subIndexes:
                item = view[uItem]
                value = getattr(item, attribute)
                subIndex = value.getIndex(name)
                value._rebuildIndex(logger, subIndex, item, attribute, name)

        self._setDirty(True)

        return index

    def _checkIndexes(self, logger, item, attribute, repair):

        result = True

        if self._indexes:
            indexes = self._indexes
            try:
                count = self.countKeys()
            except:
                logger.exception("Length of indexed value %s installed on attribute '%s' of %s couldn't be determined because of an error", self, attribute, item._repr_())
                return False

            for name, index in indexes.iteritems():
                if not index._checkIndex(index, logger, name, self,
                                         item, attribute, count, repair):
                    if repair:
                        if hasattr(index, '_super'):
                            uItem, superAttr, superName = index._super
                            superItem = item.itsView[uItem]
                            value = getattr(superItem, superAttr)
                            superIndex = value.getIndex(superName)
                            value._rebuildIndex(logger, superIndex,
                                                superItem, superAttr, superName)
                            index = indexes[name]
                        else:
                            index = self._rebuildIndex(logger, index,
                                                       item, attribute, name)

                        result = index._checkIndex(index, logger, name,
                                                   self, item, attribute,
                                                   count, repair)
                    else:
                        result = False
                    
        return result
