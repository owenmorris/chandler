
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.util.SkipList import SkipList


class Index(dict):

    def __init__(self, **kwds):

        super(Index, self).__init__()
        self._count = 0

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

    def _writeValue(self, itemWriter, buffer):
        pass

    def _readValue(self, itemReader, offset, data):
        return offset

    def _xmlValue(self, generator, version, attrs):

        generator.startElement('index', attrs)
        self._xmlValues(generator, version)
        generator.endElement('index')

    def _xmlValues(self, generator, version):
        raise NotImplementedError, "%s._xmlValues" %(type(self))


class NumericIndex(Index, SkipList):
    """
    This implementation of a numeric index is not persisted, it is
    reconstructed when the owning item is loaded. The persistence layer is
    responsible for providing persisted implementations.
    """

    class node(SkipList.node):

        __slots__ = ('_entryValue')

        def __init__(self, level, skipList):

            super(NumericIndex.node, self).__init__(level, skipList)
            self._entryValue = 0


    def __init__(self, **kwds):

        Index.__init__(self, **kwds)
        SkipList.__init__(self)

    def _createNode(self, level):

        return NumericIndex.node(level, self)

    def getEntryValue(self, key):

        return self[key]._entryValue

    def setEntryValue(self, key, entryValue):

        self[key]._entryValue = entryValue
        self._keyChanged(key)

    def getKey(self, n):

        return self.access(self, n)

    def getPosition(self, key):

        return self.position(self, key)

    def getFirstKey(self):

        return self.first(self)

    def getNextKey(self, key):

        return self.next(self, key)

    def getPreviousKey(self, key):

        return self.previous(self, key)

    def getLastKey(self):

        return self.last(self)

    def getIndexType(self):

        return 'numeric'

    def getInitKeywords(self):

        return {}

    def insertKey(self, key, afterKey):

        self.insert(self, key, afterKey)
        self._keyChanged(key)
        super(NumericIndex, self).insertKey(key, afterKey)
            
    def moveKey(self, key, afterKey):

        self.move(self, key, afterKey)
        self._keyChanged(key)
        super(NumericIndex, self).moveKey(key, afterKey)
            
    def removeKey(self, key):

        self.remove(self, key)
        super(NumericIndex, self).removeKey(key)

    def clear(self):

        key = self.getFirstKey()
        while key is not None:
            next = self.getNextKey(key)
            self.removeKey(key)
            key = next


class DelegatingIndex(object):

    def __init__(self, index, **kwds):
        self._index = index

    def __repr__(self):
        return '<%s: %d>' %(type(self).__name__, self._count)

    def __getattr__(self, name):
        return getattr(self._index, name)

    def _writeValue(self, itemWriter, buffer):
        self._index._writeValue(itemWriter, buffer)

    def _readValue(self, itemReader, offset, data):
        return self._index._readValue(itemReader, offset, data)


class SortedIndex(DelegatingIndex):

    def __init__(self, index, **kwds):
        
        super(SortedIndex, self).__init__(index, **kwds)

        if not kwds.get('loading', False):
            if 'descending' in kwds:
                self._descending = str(kwds['descending']) == 'True'
                del kwds['descending']
            else:
                self._descending = False

    def getInitKeywords(self):

        return {'descending': self._descending }

    def compare(self, k0, k1):

        raise NotImplementedError, '%s is abstract' % type(self)

    def afterKey(self, key):

        pos = lo = 0
        hi = len(self._index) - 1
        afterKey = None
        
        while lo <= hi:
            pos = (lo + hi) >> 1
            afterKey = self._index.getKey(pos)
            diff = self.compare(key, afterKey)

            if diff == 0:
                return afterKey

            if diff < 0:
                hi = pos - 1
            else:
                pos += 1
                lo = pos

        if pos == 0:
            return None

        return self._index.getKey(pos - 1)

    def insertKey(self, key, afterKey):

        self._index.insertKey(key, self.afterKey(key))

    def removeKey(self, key):

        self._index.removeKey(key)
            
    def moveKey(self, key, afterKey):

        self._index.removeKey(key)
        self._index.insertKey(key, self.afterKey(key))

    def setDescending(self, descending=True):

        self._descending = descending

    def getKey(self, n):

        if self._descending:
            return self._index.getKey(self._count - n - 1)
        else:
            return self._index.getKey(n)

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
        self._index._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer):

        super(SortedIndex, self)._writeValue(itemWriter, buffer)
        itemWriter.writeBoolean(buffer, self._descending)

    def _readValue(self, itemReader, offset, data):

        offset = super(SortedIndex, self)._readValue(itemReader, offset, data)
        offset, self._descending = itemReader.readBoolean(offset, data)

        return offset


class AttributeIndex(SortedIndex):

    def __init__(self, valueMap, index, **kwds):

        super(AttributeIndex, self).__init__(index, **kwds)
        self._valueMap = valueMap

        if not kwds.get('loading', False):
            self._attribute = kwds['attribute']
            del kwds['attribute']

    def getIndexType(self):

        return 'attribute'
    
    def getInitKeywords(self):

        kwds = super(AttributeIndex, self).getInitKeywords()
        kwds['attribute'] = self._attribute

        return kwds

    def compare(self, k0, k1):

        v0 = self._valueMap[k0].getAttributeValue(self._attribute)
        v1 = self._valueMap[k1].getAttributeValue(self._attribute)

        if v0 < v1:
            return -1
        if v0 > v1:
            return 1

        return 0

    def _xmlValues(self, generator, version, attrs, mode):

        attrs['attribute'] = self._attribute
        super(AttributeIndex, self)._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer):

        super(AttributeIndex, self)._writeValue(itemWriter, buffer)
        itemWriter.writeSymbol(buffer, self._attribute)

    def _readValue(self, itemReader, offset, data):

        offset = super(AttributeIndex, self)._readValue(itemReader,
                                                        offset, data)
        offset, self._attribute = itemReader.readSymbol(offset, data)

        return offset


class CompareIndex(SortedIndex):

    def __init__(self, valueMap, index, **kwds):

        super(CompareIndex, self).__init__(index, **kwds)
        self._valueMap = valueMap

        if not kwds.get('loading', False):
            self._compare = kwds['compare']
            del kwds['compare']

    def getIndexType(self):

        return 'compare'
    
    def getInitKeywords(self):

        kwds = super(AttributeIndex, self).getInitKeywords()
        kwds['compare'] = self._compare

        return kwds

    def compare(self, k0, k1):

        return getattr(self._valueMap[k0], self._compare)(self._valueMap[k1])

    def _xmlValues(self, generator, version, attrs, mode):

        attrs['compare'] = self._compare
        super(AttributeIndex, self)._xmlValues(generator, version, attrs, mode)

    def _writeValue(self, itemWriter, buffer):

        super(CompareIndex, self)._writeValue(itemWriter, buffer)
        itemWriter.writeSymbol(buffer, self._compare)

    def _readValue(self, itemReader, offset, data):

        offset = super(CompareIndex, self)._readValue(itemReader, offset, data)
        offset, self._compare = itemReader.readSymbol(offset, data)

        return offset
