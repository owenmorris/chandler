
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from struct import pack, unpack
from itertools import izip

from chandlerdb.item.c import Nil
from chandlerdb.util.c import SkipList
from PyICU import Collator, Locale
  
from repository.util.RangeSet import RangeSet


class Index(dict):

    def __init__(self, **kwds):

        super(Index, self).__init__()
        self._count = 0

    def __iter__(self, firstKey=None, lastKey=None, backwards=False):

        if backwards:
            getFirstKey = self.getLastKey
            getNextKey = self.getPrevKey
        else:
            getFirstKey = self.getFirstKey
            getNextKey = self.getNextKey
            
        nextKey = firstKey or getFirstKey()

        while nextKey != lastKey:
            key = nextKey
            nextKey = getNextKey(nextKey)
            yield key

        if lastKey is not None:
            yield lastKey

    def clear(self):

        self._count = 0
        super(Index, self).clear()

    def insertKey(self, key, afterKey):
        self._count += 1

    def moveKey(self, key, afterKey):
        pass

    def removeKey(self, key):
        self._count -= 1

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

    def __len__(self):
        return self._count

    def getUUID(self):
        raise NotImplementedError, "%s.getUUID" %(type(self))

    def __repr__(self):
        return '<%s: %d>' %(type(self).__name__, self._count)

    def isPersistent(self):
        return False

    def _writeValue(self, itemWriter, buffer, version):
        pass

    def _readValue(self, itemReader, offset, data):
        return offset

    def _xmlValue(self, generator, version, attrs):

        generator.startElement('index', attrs)
        self._xmlValues(generator, version)
        generator.endElement('index')

    def _xmlValues(self, generator, version):
        raise NotImplementedError, "%s._xmlValues" %(type(self))

    def _needsReindexing(self):
        return False


class NumericIndex(Index):
    """
    This implementation of a numeric index is not persisted, it is
    reconstructed when the owning item is loaded. The persistence layer is
    responsible for providing persisted implementations.
    """

    def __init__(self, **kwds):

        super(NumericIndex, self).__init__(**kwds)
        self.skipList = SkipList(self)

        if not kwds.get('loading', False):
            if 'ranges' in kwds:
                self._ranges = RangeSet(kwds.pop('ranges'))
            else:
                self._ranges = None

    def _keyChanged(self, key):
        pass

    def setRanges(self, ranges):

        if ranges is None:
            self._ranges = None
        else:
            self._ranges = RangeSet(list(ranges))
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

    def getEntryValue(self, key):

        return self[key]._entryValue

    def setEntryValue(self, key, entryValue):

        self[key]._entryValue = entryValue
        self._keyChanged(key)

    def getKey(self, n):

        return self.skipList[n]

    def getPosition(self, key):

        return self.skipList.position(key)

    def getFirstKey(self):

        return self.skipList.first()

    def getNextKey(self, key):

        return self.skipList.next(key)

    def getPreviousKey(self, key):

        return self.skipList.previous(key)

    def getLastKey(self):

        return self.skipList.last()

    def getIndexType(self):

        return 'numeric'

    def getInitKeywords(self):

        if self._ranges is not None:
            return { 'ranges': self._ranges }

        return {}

    def insertKey(self, key, afterKey):

        skipList = self.skipList
        skipList.insert(key, afterKey)
        self._keyChanged(key)

        ranges = self._ranges
        if ranges is not None:
            ranges.onInsert(key, skipList.position(key))

        super(NumericIndex, self).insertKey(key, afterKey)
            
    def moveKey(self, key, afterKey):

        if key not in self:
            self.insertKey(key, afterKey)

        else:
            skipList = self.skipList
            ranges = self._ranges
            if ranges is not None:
                ranges.onRemove(key, skipList.position(key))

            skipList.move(key, afterKey)
            self._keyChanged(key)

            if ranges is not None:
                ranges.onInsert(key, skipList.position(key))

            super(NumericIndex, self).moveKey(key, afterKey)
            
    def removeKey(self, key):

        skipList = self.skipList

        ranges = self._ranges
        if ranges is not None:
            ranges.onRemove(key, skipList.position(key))

        skipList.remove(key)
        super(NumericIndex, self).removeKey(key)

    def clear(self):

        key = self.getFirstKey()
        while key is not None:
            next = self.getNextKey(key)
            self.removeKey(key)
            key = next

    def _writeValue(self, itemWriter, buffer, version):

        super(NumericIndex, self)._writeValue(itemWriter, buffer, version)

        if self._ranges is not None:
            ranges = self._ranges.ranges
            buffer.append(pack('>bi', 1, len(ranges)))
            buffer.extend((pack('>ii', *range) for range in ranges))
        else:
            buffer.append('\0')

    def _readValue(self, itemReader, offset, data):

        offset = super(NumericIndex, self)._readValue(itemReader, offset, data)

        if data[offset] == '\1':
            count, = unpack('>i', data[offset+1:offset+5])
            start = offset + 5
            offset = start + count * 8

            if count > 0:
                format = '>%di' %(count * 2)
                numbers = iter(unpack(format, data[start:offset]))
                ranges = [(a, b) for a, b in izip(numbers, numbers)]
            else:
                ranges = []

            self._ranges = RangeSet(ranges)

        else:
            offset += 1
            self._ranges = None

        return offset


class DelegatingIndex(object):

    def __init__(self, index, **kwds):
        self._index = index

    def __repr__(self):
        return '<%s: %d>' %(type(self).__name__, self._count)

    def __len__(self):
        return len(self._index)

    def __iter__(self, firstKey=None, lastKey=None, backwards=False):
        return self._index.__iter__(firstKey, lastKey, backwards)

    def __getattr__(self, name):
        return getattr(self._index, name)

    def __contains__(self, key):
        return key in self._index

    def has_key(self, key):
        return key in self._index

    def _writeValue(self, itemWriter, buffer, version):
        self._index._writeValue(itemWriter, buffer, version)

    def _readValue(self, itemReader, offset, data):
        return self._index._readValue(itemReader, offset, data)


class SortedIndex(DelegatingIndex):

    def __init__(self, valueMap, index, **kwds):
        
        super(SortedIndex, self).__init__(index, **kwds)

        self._valueMap = valueMap
        self._subIndexes = None

        if not kwds.get('loading', False):
            self._descending = str(kwds.pop('descending', 'False')) == 'True'

    def __iter__(self, firstKey=None, lastKey=None, backwards=False):

        if self._descending:
            backwards = not backwards

        return self._index.__iter__(firstKey, lastKey, backwards)

    def getInitKeywords(self):

        if self._subIndexes:
            return { 'descending': self._descending,
                     'subindexes': self._subIndexes }
        else:
            return { 'descending': self._descending }

    def compare(self, k0, k1):

        raise NotImplementedError, '%s is abstract' % type(self)

    def insertKey(self, key, afterKey=None):

        index = self._index
        index.insertKey(key, index.skipList.after(key, self.compare))

    def removeKey(self, key):

        self._index.removeKey(key)
            
    def moveKey(self, key, afterKey):

        index = self._index
        if key in index:
            index.removeKey(key)
        index.insertKey(key, index.skipList.after(key, self.compare))

        if self._subIndexes:
            view = self._valueMap._getView()
            for uuid, attr, name in self._subIndexes:
                indexed = getattr(view[uuid], attr)
                index = indexed.getIndex(name)
                if key in index:
                    index.moveKey(key, None)
                    indexed._setDirty(True)

    def setDescending(self, descending=True):

        wasDescending = self._descending
        self._descending = descending

        return wasDescending

    def isDescending(self):

        return self._descending

    def getKey(self, n):

        if self._descending:
            return self._index.skipList[self._count - n - 1]
        else:
            return self._index.skipList[n]

    def findKey(self, mode, callable, *args):

        return self._index.skipList.find(mode, callable, *args)

    def getPosition(self, key):

        if self._descending:
            return self._count - self._index.getPosition(key) - 1
        else:
            return self._index.getPosition(key)

    def getFirstKey(self):

        if self._descending:
            return self._index.getLastKey()
        else:
            return self._index.getFirstKey()

    def getNextKey(self, key):

        if self._descending:
            return self._index.getPreviousKey(key)
        else:
            return self._index.getNextKey(key)

    def getPreviousKey(self, key):

        if self._descending:
            return self._index.getNextKey(key)
        else:
            return self._index.getPreviousKey(key)

    def getLastKey(self):

        if self._descending:
            return self._index.getFirstKey()
        else:
            return self._index.getLastKey()

    def _xmlValues(self, generator, version, attrs, mode):

        if self._descending:
            attrs['descending'] = 'True'
        if self._subIndexes:
            attrs['subindexes'] = ','.join(["(%s,%s,%s)" %(uuid.str64(), attr, name) for uuid, attr, name in self._subIndexes])

        self._index._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer, version):

        super(SortedIndex, self)._writeValue(itemWriter, buffer, version)
        itemWriter.writeBoolean(buffer, self._descending)
        if self._subIndexes:
            itemWriter.writeShort(buffer, len(self._subIndexes))
            for uuid, attr, name in self._subIndexes:
                itemWriter.writeUUID(buffer, uuid)
                itemWriter.writeSymbol(buffer, attr)
                itemWriter.writeSymbol(buffer, name)
        else:
            itemWriter.writeShort(buffer, 0)

    def _readValue(self, itemReader, offset, data):

        offset = super(SortedIndex, self)._readValue(itemReader, offset, data)
        offset, self._descending = itemReader.readBoolean(offset, data)
        offset, count = itemReader.readShort(offset, data)

        if count > 0:
            self._subIndexes = set()
            for i in xrange(count):
                offset, uuid = itemReader.readUUID(offset, data)
                offset, attr = itemReader.readSymbol(offset, data)
                offset, name = itemReader.readSymbol(offset, data)
                self._subIndexes.add((uuid, attr, name))
        else:
            self._subIndexes = None

        return offset

    def addSubIndex(self, uuid, attr, name):

        if self._subIndexes is None:
            self._subIndexes = set([(uuid, attr, name)])
        else:
            self._subIndexes.add((uuid, attr, name))

    def removeSubIndex(self, uuid, attr, name):
        
        self._subIndexes.remove((uuid, attr, name))

    def _needsReindexing(self):
        return True


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

    def compare(self, k0, k1):

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

    def _xmlValues(self, generator, version, attrs, mode):

        attrs['attributes'] = ','.join(self._attributes)
        super(AttributeIndex, self)._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer, version):

        super(AttributeIndex, self)._writeValue(itemWriter, buffer, version)
        itemWriter.writeShort(buffer, len(self._attributes))
        for attribute in self._attributes:
            itemWriter.writeSymbol(buffer, attribute)

    def _readValue(self, itemReader, offset, data):

        offset = super(AttributeIndex, self)._readValue(itemReader,
                                                        offset, data)
        offset, len = itemReader.readShort(offset, data)
        self._attributes = []
        for i in xrange(len):
            offset, attribute = itemReader.readSymbol(offset, data)
            self._attributes.append(attribute)

        return offset


class ValueIndex(AttributeIndex):

    def compare(self, k0, k1):

        view = self._valueMap._getView()

        for attribute in self._attributes:
            v0 = view.findValue(k0, attribute, None)
            v1 = view.findValue(k1, attribute, None)

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

    def compare(self, k0, k1):

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

    def _xmlValues(self, generator, version, attrs, mode):

        if self._strength is not None:
            attrs['strength'] = self._strength
        if self._locale is not None:
            attrs['locale'] = self._locale

        super(StringIndex, self)._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer, version):

        super(StringIndex, self)._writeValue(itemWriter, buffer, version)
        itemWriter.writeInteger(buffer, self._strength or -1)
        itemWriter.writeSymbol(buffer, self._locale or '')

    def _readValue(self, itemReader, offset, data):

        offset = super(StringIndex, self)._readValue(itemReader, offset, data)
        offset, strength = itemReader.readInteger(offset, data)
        offset, locale = itemReader.readSymbol(offset, data)

        if strength != -1:
            self._strength = strength
        if locale != '':
            self._locale = locale

        self._init()

        return offset


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

    def compare(self, k0, k1):

        return getattr(self._valueMap[k0], self._compare)(self._valueMap[k1])

    def _xmlValues(self, generator, version, attrs, mode):

        attrs['compare'] = self._compare
        super(CompareIndex, self)._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer, version):

        super(CompareIndex, self)._writeValue(itemWriter, buffer, version)
        itemWriter.writeSymbol(buffer, self._compare)

    def _readValue(self, itemReader, offset, data):

        offset = super(CompareIndex, self)._readValue(itemReader, offset, data)
        offset, self._compare = itemReader.readSymbol(offset, data)

        return offset


class SubIndex(SortedIndex):

    def __init__(self, valueMap, index, **kwds):

        super(SubIndex, self).__init__(valueMap, index, **kwds)

        if not kwds.get('loading', False):
            item, attr, name = kwds.pop('superindex')
            self._super = (item.itsUUID, attr, name)

    def getIndexType(self):

        return 'subindex'
    
    def getInitKeywords(self):

        kwds = super(SubIndex, self).getInitKeywords()
        kwds['superindex'] = self._super

        return kwds

    def compare(self, k0, k1):

        uuid, attr, name = self._super
        index = getattr(self._valueMap._getView()[uuid], attr).getIndex(name)

        return index.getPosition(k0) - index.getPosition(k1)

    def _xmlValues(self, generator, version, attrs, mode):

        uuid, attr, name = self._super
        attrs['superindex'] = "%s,%s,%s" %(uuid.str64(), attr, name)
        super(SubIndex, self)._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer, version):

        super(SubIndex, self)._writeValue(itemWriter, buffer, version)

        uuid, attr, name = self._super
        itemWriter.writeUUID(buffer, uuid)
        itemWriter.writeSymbol(buffer, attr)
        itemWriter.writeSymbol(buffer, name)

    def _readValue(self, itemReader, offset, data):

        offset = super(SubIndex, self)._readValue(itemReader, offset, data)

        offset, uuid = itemReader.readUUID(offset, data)
        offset, attr = itemReader.readSymbol(offset, data)
        offset, name = itemReader.readSymbol(offset, data)

        self._super = (uuid, attr, name)

        return offset
