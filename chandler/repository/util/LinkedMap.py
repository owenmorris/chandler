
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO


class LinkedMap(dict):

    class link(object):

        def __init__(self, value):

            super(LinkedMap.link, self).__init__()

            self._previousKey = self._nextKey = None
            self._value = value

        def __repr__(self):

            return "<link: %s>" %(self._value.__repr__())
        
        def _setNext(self, nextKey, key, linkedMap):

            if nextKey is None:
                linkedMap._lastKey = key
                linkedMap.linkChanged(self, None)

            self._nextKey = nextKey
            linkedMap.linkChanged(self, key)

        def _setPrevious(self, previousKey, key, linkedMap):

            if previousKey is None:
                linkedMap._firstKey = key
                linkedMap.linkChanged(self, None)
                
            self._previousKey = previousKey
            linkedMap.linkChanged(self, key)


    def __init__(self, dictionary=None):

        super(LinkedMap, self).__init__()
        self._firstKey = self._lastKey = None

        if dictionary is not None:
            self.update(dictionary)

    def __repr__(self):

        buffer = None
        
        try:
            buffer = cStringIO.StringIO()
            buffer.write('{')
            for key, value in self.iteritems():
                buffer.write(key.__repr__())
                buffer.write(': ')
                buffer.write(value.__repr__())
                if key != self._lastKey:
                    buffer.write(', ')
            buffer.write('}')
            return buffer.getvalue()

        finally:
            if buffer is not None:
                buffer.close()

    def linkChanged(self, link, key):
        pass

    def update(self, dictionary):

        for key, value in dictionary.iteritems():
            self[key] = value

    def _get(self, key, load=True):

        try:
            return super(LinkedMap, self).__getitem__(key)
        except KeyError:
            if load and self._load(key):
                return super(LinkedMap, self).__getitem__(key)
            raise

    def _load(self, key):

        return False

    def _unload(self, key):

        super(LinkedMap, self).__delitem__(key)

    def _makeLink(self, value):

        return LinkedMap.link(value)

    def __getitem__(self, key, load=True):

        return self._get(key, load)._value

    def __setitem__(self, key, value, previousKey=None, nextKey=None):

        link = super(LinkedMap, self).get(key)

        if link is not None:
            link._value = value
            self.linkChanged(link, key)

        else:
            link = self._makeLink(value)

            if previousKey is None and nextKey is None:
                previousKey = self._lastKey
                if previousKey is not None and previousKey != key:
                    self._get(previousKey)._setNext(key, previousKey, self)

            if previousKey is None or previousKey != key:
                link._setPrevious(previousKey, key, self)
            if nextKey is None or nextKey != key:
                link._setNext(nextKey, key, self)

            super(LinkedMap, self).__setitem__(key, link)

        return link

    def place(self, key, afterKey=None):
        "Move a key in this collection after another one."

        if self.has_key(key):
            current = self._get(key)
            if current._previousKey is not None:
                previous = self._get(current._previousKey)
            else:
                previous = None
            if current._nextKey is not None:
                next = self._get(current._nextKey)
            else:
                next = None
        else:
            raise ValueError, "No value for key %s" %(key)

        if afterKey is not None:
            if self.has_key(afterKey):
                after = self._get(afterKey)
                afterNextKey = after._nextKey
            else:
                raise ValueError, "No value for %s" %(afterKey)
        else:
            after = None
            afterKey = None
            afterNextKey = self._firstKey

        if key == afterKey:
            return

        if previous is not None:
            previous._setNext(current._nextKey, current._previousKey, self)
        if next is not None:
            next._setPrevious(current._previousKey, current._nextKey, self)

        current._setNext(afterNextKey, key, self)
        if afterNextKey is not None:
            self._get(afterNextKey)._setPrevious(key, afterNextKey, self)
        if after is not None:
            after._setNext(key, afterKey, self)

        current._setPrevious(afterKey, key, self)
            
    def __delitem__(self, key):

        link = self._get(key)

        if link._previousKey is not None:
            self._get(link._previousKey)._setNext(link._nextKey,
                                                  link._previousKey, self)
        else:
            self._firstKey = link._nextKey
            
        if link._nextKey is not None:
            self._get(link._nextKey)._setPrevious(link._previousKey,
                                                  link._nextKey, self)
        else:
            self._lastKey = link._previousKey
                
        super(LinkedMap, self).__delitem__(key)

        return link

    def has_key(self, key, load=True):

        has = super(LinkedMap, self).has_key(key)
        if not has and load and self._load(key):
            has = super(LinkedMap, self).has_key(key)

        return has

    def get(self, key, default=None, load=True):

        link = super(LinkedMap, self).get(key, default)
        if link is default and load and self._load(key):
            link = super(LinkedMap, self).get(key, default)
            
        if link is not default:
            return link._value

        return default

    def firstKey(self):
        "Return the first key of this mapping."

        return self._firstKey

    def lastKey(self):
        "Return the last key of this mapping."

        return self._lastKey
        
    def nextKey(self, key):
        "Return the next key relative to key."

        return self._get(key)._nextKey

    def previousKey(self, key):
        "Return the previous key relative to key."

        return self._get(key)._previousKey

    def __iter__(self):

        for key in self.iterkeys():
            yield self[key]

    def iterkeys(self):

        nextKey = self._firstKey
        while nextKey is not None:
            key = nextKey
            nextKey = self._get(nextKey)._nextKey

            yield key

    def _iterkeys(self):

        return super(LinkedMap, self).iterkeys()

    def keys(self):

        return [key for key in self.iterkeys()]

    def _keys(self):

        return super(LinkedMap, self).keys()

    def values(self):

        return [item for item in self]

    def _values(self):

        return [self._get(key) for key in self._iterkeys()]

    def itervalues(self):

        for value in self:
            yield value

    def _itervalues(self):

        for key in self._iterkeys():
            yield self._get(key)

    def iteritems(self):

        for key in self.iterkeys():
            yield (key, self[key])

    def _iteritems(self):

        for key in self._iterkeys():
            yield (key, self._get(key))

    def items(self):

        return [(key, self[key]) for key in self.iterkeys()]

    def _items(self):

        return [(key, self._get(key)) for key in self._iterkeys()]
