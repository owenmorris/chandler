
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.util.SkipList import SkipList


class Index(dict):

    def __init__(self, **kwds):

        super(Index, self).__init__()
        self._count = int(kwds.get('count', '0'))

    def clear(self):

        self._count = 0
        super(Index, self).clear()

    def insertKey(self, key, afterKey):
        self._count += 1

    def moveKey(self, key, afterKey):
        pass

    def removeKey(self, key):
        self._count -= 1

    def getKey(self, key):
        raise NotImplementedError, "%s.getKey" %(type(self))

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

    def __len__(self):
        return self._count

    def getUUID(self):
        raise NotImplementedError, "%s.getUUID" %(type(self))

    def __repr__(self):
        return '<%s: %d>' %(type(self).__name__, self._count)

    def isPersistent(self):
        return False

    def _xmlValues(self, generator, version, attrs, mode):

        attrs['type'] = self.getIndexType()
        generator.startElement('index', attrs)
        generator.endElement('index')


class NumericIndex(Index, SkipList):
    """
    This implementation of a numeric index is not persisted, it is
    reconstructed when the owning item is loaded.
    """

    def __init__(self, **kwds):

        Index.__init__(self, **kwds)
        SkipList.__init__(self)

    def getKey(self, n):

        return self.access(self, n)

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
