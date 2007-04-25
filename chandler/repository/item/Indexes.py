#   Copyright (c) 2004-2007 Open Source Applications Foundation
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


from itertools import izip
from traceback import format_exc

from chandlerdb.item.c import CIndex, DelegatingIndex
from chandlerdb.persistence.c import Record
from chandlerdb.util.c import Nil, Default, SkipList
from PyICU import Collator, Locale
  
from repository.util.RangeSet import RangeSet


class Index(CIndex):

    def iterkeys(self, firstKey=None, lastKey=None):

        getFirstKey = self.getFirstKey
        getNextKey = self.getNextKey
        nextKey = firstKey or getFirstKey()

        while nextKey != lastKey:
            key = nextKey
            nextKey = getNextKey(nextKey)
            yield key

        if lastKey is not None:
            yield lastKey

    def getKey(self, n):
        raise NotImplementedError, "%s.getKey" %(type(self))

    def getPosition(self, key):
        raise NotImplementedError, "%s.getPosition" %(type(self))

    def getFirstKey(self):
        raise NotImplementedError, "%s.getFirstKey" %(type(self))

    def getNextKey(self, key):
        raise NotImplementedError, "%s.getNextKey" %(type(self))

    def getPreviousKey(self, key):
        raise NotImplementedError, "%s.getPreviousKey" %(type(self))

    def getLastKey(self):
        raise NotImplementedError, "%s.getLastKey" %(type(self))

    def getIndexType(self):
        raise NotImplementedError, "%s.getIndexType" %(type(self))

    def getInitKeywords(self):
        raise NotImplementedError, "%s.getInitKeywords" %(type(self))

    def getUUID(self):
        raise NotImplementedError, "%s.getUUID" %(type(self))

    def isPersistent(self):
        return False

    def _writeValue(self, itemWriter, record, version):
        pass

    def _readValue(self, itemReader, offset, data):
        return offset

    def _checkIndex(self, _index, logger, name, value, item, attribute, count,
                    repair):

        result = True

        if count != len(self):
            logger.error("Lengths of index '%s' (%d) installed on value '%s' (%d) of type %s in attribute '%s' on %s don't match", name, len(self), value, count, type(value), attribute, item._repr_())
            result = False

        else:
            try:
                size, result = _index._checkIterateIndex(logger, name, value,
                                                         item, attribute,
                                                         repair)
                if size != 0:
                    logger.error("Iteration of index '%s' (%d) installed on value '%s' of type %s in attribute '%s' on %s doesn't match length (%d)", name, count - size, value, type(value), attribute, item._repr_(), count)
                    result = False
            except Exception, e:
                logger.error("Iteration of index '%s' installed on value '%s' of type %s in attribute '%s' on %s caused an error: %s", name, value, type(value), attribute, item._repr_(), format_exc(5))
                result = False

        return result

    def _checkIterateIndex(self, logger, name, value, item, attribute, repair):
        
        size = len(self)

        for key in iter(self):
            size -= 1
            if size < 0:
                break

        return size, True


class NumericIndex(Index):
    """
    This implementation of a numeric index is not persisted, it is
    reconstructed when the owning item is loaded. The persistence layer is
    responsible for providing persisted implementations.
    """

    def __init__(self, **kwds):

        super(NumericIndex, self).__init__(**kwds)
        self.skipList = SkipList(self)

        self._ranges = None
        self._descending = False

        if not kwds.get('loading', False):
            if 'ranges' in kwds:
                self._ranges = RangeSet(kwds.pop('ranges'))
            self._descending = str(kwds.pop('descending', 'False')) == 'True'

    def validateIndex(self, valid):

        self.skipList.validate(valid)

    def setDescending(self, descending=True):

        wasDescending = self._descending
        self._descending = descending

        return wasDescending

    def isDescending(self):
        return self._descending

    def _keyChanged(self, key):
        pass

    def setRanges(self, ranges):

        if ranges is None:
            self._ranges = None
        else:
            self._ranges = RangeSet(ranges)
            assert self._ranges.rangesAreValid()

    def getRanges(self):

        ranges = self._ranges
        if ranges is not None:
            return ranges.ranges

        return None

    def isInRanges(self, range):

        ranges = self._ranges
        if ranges is None:
            return False

        return ranges.isSelected(range)

    def addRange(self, range):

        if self._ranges is None:
            if isinstance(range, int):
                range = (range, range)                
            self._ranges = RangeSet([range])
        else:
            self._ranges.selectRange(range)

    def removeRange(self, range):

        if self._ranges is not None:
            self._ranges.unSelectRange(range)

    def getKey(self, n):

        if self._descending:
            return self.skipList[self._count - n - 1]
        else:
            return self.skipList[n]

    def getPosition(self, key):

        if self._descending:
            return self._count - self.skipList.position(key) - 1
        else:
            return self.skipList.position(key)

    def getFirstKey(self):

        if self._descending:
            return self.skipList.last()
        else:
            return self.skipList.first()

    def getNextKey(self, key):

        if self._descending:
            return self.skipList.previous(key)
        else:
            return self.skipList.next(key)

    def getPreviousKey(self, key):

        if self._descending:
            return self.skipList.next(key)
        else:
            return self.skipList.previous(key)

    def getLastKey(self):

        if self._descending:
            return self.skipList.first()
        else:
            return self.skipList.last()

    def getIndexType(self):

        return 'numeric'

    def getInitKeywords(self):

        kwds = {}

        if self._ranges is not None:
            kwds['ranges'] = self._ranges.ranges
        if self._descending:
            kwds['descending'] = self._descending

        return kwds

    # key: None -> first, Default -> last
    def insertKey(self, key, afterKey=Default, selected=False):

        skipList = self.skipList
        if afterKey is Default:
            afterKey = skipList.last()

        skipList.insert(key, afterKey)
        self._keyChanged(key)

        super(NumericIndex, self).insertKey(key, afterKey)

        ranges = self._ranges
        if ranges is not None:
            pos = self.getPosition(key)
            ranges.onInsert(key, pos)
            if selected:
                ranges.selectRange(pos)

    # if afterKey is None, move to the beginning of the index
    # if afterKey is Default, don't move the key (insert only)
    # if afterKey is None, move to the beginning of the index
    # if afterKey is Default, don't move the key (insert only)
    # if insertMissing is None, raise error if key not present
    # if insertMissing is False, skip key if key not present
    def moveKey(self, key, afterKey=None, insertMissing=None):

        if key not in self:
            if insertMissing:
                self.insertKey(key, afterKey)
            elif insertMissing is None:
                raise KeyError, key

        elif afterKey is not Default:
            ranges = self._ranges
            if ranges is not None:
                ranges.onRemove(key, self.getPosition(key))

            self.skipList.move(key, afterKey)
            self._keyChanged(key)

            if ranges is not None:
                ranges.onInsert(key, self.getPosition(key))

            super(NumericIndex, self).moveKey(key, afterKey)

    def moveKeys(self, keys, afterKey=None, insertMissing=None):

        for key in keys:
            self.moveKey(key, afterKey, insertMissing)

    def removeKey(self, key):

        if key in self:
            ranges = self._ranges
            if ranges is not None:
                pos = self.getPosition(key)
                selected = ranges.isSelected(pos)
                ranges.onRemove(key, pos)
            else:
                selected = False

            self.skipList.remove(key)
            return super(NumericIndex, self).removeKey(key), selected

        return False, False

    def removeKeys(self, keys):

        removed = False

        for key in keys:
            removed, selected = self.removeKey(key)

        return removed

    def clear(self):

        key = self.getFirstKey()
        while key is not None:
            next = self.getNextKey(key)
            self.removeKey(key)
            key = next

    def _writeValue(self, itemWriter, record, version):

        super(NumericIndex, self)._writeValue(itemWriter, record, version)

        if self._ranges is not None:
            ranges = self._ranges.ranges
            record += (Record.BYTE, 1,
                       Record.INT, len(ranges))
            for s, e in ranges:
                record += (Record.INT, s, Record.INT, e)
        else:
            record += (Record.BYTE, 0)

        record += (Record.BOOLEAN, self._descending)

    def _readValue(self, itemReader, offset, data):

        offset = super(NumericIndex, self)._readValue(itemReader, offset, data)

        withRanges = data[offset]
        offset += 1

        if withRanges:
            count = data[offset] * 2
            offset += 1
            ranges = [data[i:i+2] for i in xrange(offset, offset+count, 2)]
            self._ranges = RangeSet(ranges)
            offset += count

        else:
            self._ranges = None

        self._descending = data[offset]

        return offset + 1


class SortedIndex(DelegatingIndex):

    def __init__(self, valueMap, index, **kwds):
        
        super(SortedIndex, self).__init__(index, **kwds)

        if not kwds.get('loading', False):
            if 'superindex' in kwds:
                item, attr, name = kwds.pop('superindex')
                self._super = (item.itsUUID, attr, name)

        self._valueMap = valueMap
        self._subIndexes = None

    def __iter__(self):

        return self.iterkeys()

    def getInitKeywords(self):

        kwds = self._index.getInitKeywords()

        if hasattr(self, '_super'):
            kwds['superindex'] = self._super

        if self._subIndexes:
            kwds['subindexes'] = self._subIndexes

        return kwds

    def compare(self, k0, k1, vals):

        raise NotImplementedError, '%s is abstract' % type(self)

    def _reindex(self, key):

        if hasattr(self, '_super'):
            uuid, attr, name = self._super
            index = getattr(self._valueMap.itsView[uuid], attr).getIndex(name)
            index._reindex(key)
        else:
            self._valueMap._reindex(self, key)

    def validateIndex(self, valid):

        self._index.validateIndex(valid)

        if self._subIndexes:
            view = self._valueMap.itsView
            for uuid, attr, name in self._subIndexes:
                indexed = getattr(view[uuid], attr)
                index = indexed.getIndex(name).validateIndex(valid)

    def insertKey(self, key, ignore=None, selected=False):

        index = self._index
        skipList = index.skipList

        superindex = self.getSuperIndex()
        if superindex is not None and superindex._valueMap is self._valueMap:
            if key not in superindex:
                superindex.insertKey(key, ignore, selected)

        if skipList.isValid():
            afterKey = skipList.after(key, self.compare, {})
            index.insertKey(key, afterKey, selected)
        else:
            afterKey = None
            index.insertKey(key, afterKey, selected)
            self._reindex(key)

    def moveKey(self, key, ignore=None, insertMissing=None):

        index = self._index
        skipList = index.skipList
        selected = False
        insert = True
        vals = {}

        if key in index:
            prevKey = skipList.previous(key)
            nextKey = skipList.next(key)
            if ((prevKey is None or self.compare(key, prevKey, vals) >= 0) and
                (nextKey is None or self.compare(key, nextKey, vals) <= 0)):
                return

            removed, selected = index.removeKey(key)
            if not removed:
                if insertMissing is None:
                    raise KeyError, key
                elif not insertMissing:
                    insert = False

        if insert:
            afterKey = skipList.after(key, self.compare, vals)
            index.insertKey(key, afterKey, selected)

        if self._subIndexes:
            view = self._valueMap.itsView
            for uuid, attr, name in self._subIndexes:
                indexed = getattr(view[uuid], attr)
                index = indexed.getIndex(name)
                if key in index:
                    index.moveKey(key, ignore, insertMissing)
                    indexed._setDirty(True)

    def moveKeys(self, keys, ignore=None, insertMissing=None):

        index = self._index
        skipList = index.skipList
        selection = set()
        inserts = []
        moves = []
        vals = {}

        if not isinstance(keys, set):
            keys = set(keys)

        for key in keys:
            if key in index:
                prevKey = skipList.previous(key)
                nextKey = skipList.next(key)
                if ((prevKey is None or
                     (prevKey not in keys and
                      self.compare(key, prevKey, vals) >= 0)) and
                    (nextKey is None or
                     (nextKey not in keys and
                      self.compare(key, nextKey, vals) <= 0))):
                    continue
            moves.append(key)

        if not moves:
            return

        for key in moves:
            removed, selected = index.removeKey(key)
            if removed:
                inserts.append(key)
                if selected:
                    selection.add(key)
            elif insertMissing is None:
                raise KeyError, key
            elif insertMissing:
                inserts.append(key)

        for key in inserts:
            afterKey = skipList.after(key, self.compare, vals)
            index.insertKey(key, afterKey, key in selection)

        if self._subIndexes:
            view = self._valueMap.itsView
            for uuid, attr, name in self._subIndexes:
                indexed = getattr(view[uuid], attr)
                index = indexed.getIndex(name)
                subKeys = [key for key in moves if key in index]
                if subKeys:
                    index.moveKeys(subKeys, ignore, insertMissing)
                    indexed._setDirty(True)

    # Used during merging.
    # Not notifications safe, removes the keys from sub indexes too.

    def removeKeys(self, keys):

        if self._index.removeKeys(keys):
            if self._subIndexes:
                view = self._valueMap.itsView
                for uuid, attr, name in self._subIndexes:
                    indexed = getattr(view[uuid], attr)
                    index = indexed.getIndex(name)
                    if index.removeKeys(keys):
                        indexed._setDirty(True)

            return True

        return False

    def findKey(self, mode, callable, *args):

        return self._index.skipList.find(mode, callable, *args)

    def _writeValue(self, itemWriter, record, version):

        self._index._writeValue(itemWriter, record, version)

        if hasattr(self, '_super'):
            uuid, attr, name = self._super
            record += (Record.BOOLEAN, True,
                       Record.UUID, uuid,
                       Record.SYMBOL, attr,
                       Record.SYMBOL, name)
        else:
            record += (Record.BOOLEAN, False)

        if self._subIndexes:
            record += (Record.SHORT, len(self._subIndexes))
            for uuid, attr, name in self._subIndexes:
                record += (Record.UUID, uuid,
                           Record.SYMBOL, attr,
                           Record.SYMBOL, name)
        else:
            record += (Record.SHORT, 0)

    def _readValue(self, itemReader, offset, data):

        offset = self._index._readValue(itemReader, offset, data)

        isSubIndex = data[offset]
        offset += 1

        if isSubIndex:
            # uuid, attr, name
            self._super = data[offset:offset+3]
            offset += 3

        count = data[offset]
        offset += 1

        if count > 0:
            self._subIndexes = set()
            for i in xrange(count):
                # uuid, attr, name
                self._subIndexes.add(data[offset:offset+3])
                offset += 3
        else:
            self._subIndexes = None

        return offset

    def getSuperIndex(self):
        
        if hasattr(self, '_super'):
            uuid, attr, name = self._super
            return getattr(self._valueMap.itsView[uuid], attr).getIndex(name)
            
        return None

    def addSubIndex(self, uuid, attr, name):

        if self._subIndexes is None:
            self._subIndexes = set([(uuid, attr, name)])
        else:
            self._subIndexes.add((uuid, attr, name))

    def removeSubIndex(self, uuid, attr, name):
        
        self._subIndexes.remove((uuid, attr, name))

    def _checkIndex(self, _index, logger, name, value, item, attribute, count,
                    repair):

        result = self._index._checkIndex(self, logger, name, value,
                                         item, attribute, count, repair)

        if hasattr(self, '_super'):
            uuid, attr, superName = self._super

            superItem = item.itsView.find(uuid)
            if superItem is None:
                logger.error("Item %s, owner of superindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, was not found", uuid, superName, name, value, attribute, item._repr_())
                return False

            superValue = getattr(superItem, attr, Nil)
            if superValue is Nil:
                logger.error("Attribute '%s' of %s, owner of superindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, was not found", attr, superItem._repr_(), superName, name, value, attribute, item._repr_())
                return False

            indexes = getattr(superValue, '_indexes', Nil)
            if indexes is Nil:
                logger.error("Value %s of attribute '%s' of %s, owner of superindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, is not of a type that can have indexes: %s", superValue, attr, superItem._repr_(), superName, name, value, attribute, item._repr_(), type(superValue))
                return False

            if indexes is None:
                index = None
            else:
                index = indexes.get(superName)

            if index is None:
                logger.error("Value %s of attribute '%s' of %s, owner of superindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, has no index named '%s'", superValue, attr, superItem._repr_(), superName, name, value, attribute, item._repr_(), superName)
                return False

            reasons = set()
            if not self._valueMap.isSubset(superValue, reasons):
                logger.error("To support a subindex, %s must be a subset of %s but %s", self._valueMap, superValue, ', '.join("%s.%s is not a subset of %s.%s" %(sub_i._repr_(), sub_a, sup_i._repr_(), sup_a) for (sub_i, sub_a), (sup_i, sup_a) in ((sub.itsOwner, sup.itsOwner) for sub, sup in reasons)))
                return False
        
        if self._subIndexes:
            for uuid, attr, subName in self._subIndexes:
                subItem = item.itsView.find(uuid)
                if subItem is None:
                    logger.error("Item %s, owner of subindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, was not found", uuid, subName, name, value, attribute, item._repr_())
                    result = False
                    continue

                subValue = getattr(subItem, attr, Nil)
                if subValue is Nil:
                    logger.error("Attribute '%s' of %s, owner of subindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, was not found", attr, subItem._repr_(), subName, name, value, attribute, item._repr_())
                    result = False
                    continue

                indexes = getattr(subValue, '_indexes', Nil)
                if indexes is Nil:
                    logger.error("Value %s of attribute '%s' of %s, owner of subindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, is not of a type that can have indexes: %s", subValue, attr, subItem._repr_(), subName, name, value, attribute, item._repr_(), type(subValue))
                    result = False
                    continue

                if indexes is None:
                    index = None
                else:
                    index = indexes.get(subName)
                if index is None:
                    logger.error("Value %s of attribute '%s' of %s, owner of subindex '%s' of index '%s' installed on value '%s' in attribute '%s' on %s, has no index named '%s'", subValue, attr, subItem._repr_(), subName, name, value, attribute, item._repr_(), subName)
                    result = False

        return result

    def _checkIterateIndex(self, logger, name, value, item, attribute, repair):

        size = len(self)
        prevKey = None
        result = True
        vals = {}

        compare = self.compare
        descending = self._descending
        if descending:
            word = 'lesser'
        else:
            word = 'greater'

        for key in self:
            size -= 1
            if size < 0:
                break
            if prevKey is not None:
                if descending:
                    sorted = compare(prevKey, key, vals) >= 0
                else:
                    sorted = compare(prevKey, key, vals) <= 0
                if not sorted:
                    logger.error("Sorted %s index '%s' installed on value '%s' of type %s in attribute '%s' on %s is not sorted properly: value for %s is %s than the value for %s", self.getIndexType(), name, value, type(value), attribute, item._repr_(), repr(prevKey), word, repr(key))
                    result = False

            prevKey = key

        return size, result


class AttributeIndex(SortedIndex):

    def __init__(self, valueMap, index, **kwds):

        super(AttributeIndex, self).__init__(valueMap, index, **kwds)

        if not kwds.get('loading', False):
            attributes = kwds.pop('attributes', None)
            if attributes is None:
                attributes = kwds.pop('attribute')
            if isinstance(attributes, basestring):
                self._attributes = attributes.split(',')
            else:
                self._attributes = attributes

    def getIndexType(self):

        return 'attribute'
    
    def getInitKeywords(self):

        kwds = super(AttributeIndex, self).getInitKeywords()
        kwds['attributes'] = self._attributes

        return kwds

    def compare(self, k0, k1, vals):

        valueMap = self._valueMap
        i0 = valueMap[k0]
        i1 = valueMap[k1]

        for attribute in self._attributes:
            v0 = getattr(i0, attribute, None)
            v1 = getattr(i1, attribute, None)

            if v0 is v1:
                continue

            if v0 is None:
                return 1

            if v1 is None:
                return -1

            if v0 == v1:
                continue

            if v0 > v1:
                return 1

            return -1

        return 0

    def _writeValue(self, itemWriter, record, version):

        super(AttributeIndex, self)._writeValue(itemWriter, record, version)
        record += (Record.SHORT, len(self._attributes))
        for attribute in self._attributes:
            record += (Record.SYMBOL, attribute)

    def _readValue(self, itemReader, offset, data):

        offset = super(AttributeIndex, self)._readValue(itemReader,
                                                        offset, data)
        len = data[offset]
        offset += 1

        self._attributes = data[offset:offset+len]
        offset += len

        return offset


class ValueIndex(AttributeIndex):

    def __init__(self, valueMap, index, **kwds):

        super(ValueIndex, self).__init__(valueMap, index, **kwds)

        if not kwds.get('loading', False):
            self._pairs = [(name, None) for name in self._attributes]

    def compare(self, k0, k1, vals):

        view = self._valueMap.itsView

        for v0, v1 in izip(view.findValues(k0, *self._pairs),
                           view.findValues(k1, *self._pairs)):
            if v0 is v1:
                continue

            if v0 is None:
                return 1

            if v1 is None:
                return -1

            if v0 == v1:
                continue

            if v0 > v1:
                return 1

            return -1

        return 0

    def getIndexType(self):

        return 'value'

    def _readValue(self, itemReader, offset, data):

        offset = super(ValueIndex, self)._readValue(itemReader, offset, data)
        self._pairs = [(name, None) for name in self._attributes]

        return offset
    

class StringIndex(AttributeIndex):

    def __init__(self, valueMap, index, **kwds):

        super(StringIndex, self).__init__(valueMap, index, **kwds)

        self._strength = None
        self._locale = None

        if not kwds.get('loading', False):
            self._strength = kwds.pop('strength', None)
            self._locale = kwds.pop('locale', None)
            self._init()

    def _init(self):

        if self._locale is not None:
            self._collator = Collator.createInstance(Locale(self._locale))
        else:
            self._collator = Collator.createInstance()

        if self._strength is not None:
            self._collator.setStrength(self._strength)

    def getIndexType(self):

        return 'string'
    
    def getInitKeywords(self):

        kwds = super(StringIndex, self).getInitKeywords()
        if self._strength is not None:
            kwds['strength'] = self._strength
        if self._locale is not None:
            kwds['locale'] = self._locale

        return kwds

    def compare(self, k0, k1, vals):

        valueMap = self._valueMap
        i0 = valueMap[k0]
        i1 = valueMap[k1]

        for attribute in self._attributes:
            v0 = getattr(i0, attribute, None)
            v1 = getattr(i1, attribute, None)

            if v0 is v1:
                continue

            if v0 is None:
                return 1

            if v1 is None:
                return -1

            res = self._collator.compare(v0, v1)
            if res == 0:
                continue

            return res

        return 0

    def _writeValue(self, itemWriter, record, version):

        super(StringIndex, self)._writeValue(itemWriter, record, version)
        record += (Record.INT, self._strength or -1,
                   Record.SYMBOL, self._locale)

    def _readValue(self, itemReader, offset, data):

        offset = super(StringIndex, self)._readValue(itemReader, offset, data)

        strength = data[offset]
        self._locale = data[offset + 1]

        if strength != -1:
            self._strength = strength

        self._init()

        return offset + 2


class CompareIndex(SortedIndex):

    def __init__(self, valueMap, index, **kwds):

        super(CompareIndex, self).__init__(valueMap, index, **kwds)

        if not kwds.get('loading', False):
            self._compare = kwds.pop('compare')

    def getIndexType(self):

        return 'compare'
    
    def getInitKeywords(self):

        kwds = super(CompareIndex, self).getInitKeywords()
        kwds['compare'] = self._compare

        return kwds

    def compare(self, k0, k1, vals):

        return getattr(self._valueMap[k0], self._compare)(self._valueMap[k1])

    def _writeValue(self, itemWriter, record, version):

        super(CompareIndex, self)._writeValue(itemWriter, record, version)
        record += (Record.SYMBOL, self._compare)

    def _readValue(self, itemReader, offset, data):

        offset = super(CompareIndex, self)._readValue(itemReader, offset, data)
        self._compare = data[offset]

        return offset + 1


class MethodIndex(SortedIndex):

    def __init__(self, valueMap, index, **kwds):

        super(MethodIndex, self).__init__(valueMap, index, **kwds)

        if not kwds.get('loading', False):
            item, methodName = kwds.pop('method')
            self._method = (item.itsUUID, methodName)

    def getIndexType(self):

        return 'method'
    
    def getInitKeywords(self):

        kwds = super(MethodIndex, self).getInitKeywords()
        kwds['method'] = self._method

        return kwds

    def compare(self, k0, k1, vals):

        uItem, methodName = self._method
        item = self._valueMap.itsView[uItem]
        if k0 not in vals:
            vals[k0] = getattr(item, methodName + '_init')(self, k0, vals)

        return getattr(item, methodName)(self, k0, k1, vals)

    def _writeValue(self, itemWriter, record, version):

        super(MethodIndex, self)._writeValue(itemWriter, record, version)

        uItem, methodName = self._method
        record += (Record.UUID, uItem,
                   Record.SYMBOL, methodName)

    def _readValue(self, itemReader, offset, data):

        offset = super(MethodIndex, self)._readValue(itemReader, offset, data)
        self._method = data[offset:offset+2]

        return offset + 2


class SubIndex(SortedIndex):

    def getIndexType(self):

        return 'subindex'
    
    def compare(self, k0, k1, vals):

        uuid, attr, name = self._super
        index = getattr(self._valueMap.itsView[uuid], attr).getIndex(name)

        # this should only happen during merge (moveKeys)
        if k0 not in index:
            index.insertKey(k0)
        if k1 not in index:
            index.insertKey(k1)

        skipList = index.skipList

        return skipList.position(k0) - skipList.position(k1)


__index_classes__ = { 'attribute': AttributeIndex,
                      'value': ValueIndex,
                      'string': StringIndex,
                      'compare': CompareIndex,
                      'method': MethodIndex,
                      'subindex': SubIndex }
