
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO


class LinkedMap(dict):

    class link(object):

        def __init__(self, value):

            super(LinkedMap.link, self).__init__(self)

            self._previousKey = self._nextKey = None
            self._value = value

        def __repr__(self):

            return self._value.__repr__()
        
        def _setNext(self, nextKey, key, linkedMap):

            if nextKey is None:
                linkedMap._lastKey = key

            self._nextKey = nextKey
            linkedMap.linkChanged(self)

        def _setPrevious(self, previousKey, key, linkedMap):

            if previousKey is None:
                linkedMap._firstKey = key
                
            self._previousKey = previousKey
            linkedMap.linkChanged(self)


    def __init__(self, dictionary=None):

        super(LinkedMap, self).__init__()
        self._firstKey = self._lastKey = None

        if dictionary is not None:
            self.update(dictionary)

    def __repr__(self):

        buffer = cStringIO.StringIO()
        try:
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
            buffer.close()

    def linkChanged(self, link):
        pass

    def update(self, dictionary):

        for key, value in dictionary.iteritems():
            self[key] = value

    def _get(self, key):

        try:
            return super(LinkedMap, self).__getitem__(key)
        except KeyError:
            if self._load(key):
                return super(LinkedMap, self).__getitem__(key)
            raise

    def _load(self, key):

        return False

    def _makeLink(self, value):

        return LinkedMap.link(value)

    def __getitem__(self, key):

        return self._get(key)._value

    def __setitem__(self, key, value, previousKey=None, nextKey=None):

        link = self._makeLink(value)

        if previousKey is None and nextKey is None:
            previousKey = self._lastKey
            if previousKey is not None and previousKey != key:
                self._get(previousKey)._setNext(key, previousKey, self)

        if previousKey is None or previousKey != key:
            link._setPrevious(previousKey, key, self)
        if nextKey is None or nextKey != key:
            link._setNext(nextKey, key, self)

        return super(LinkedMap, self).__setitem__(key, link)

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

        value = self._get(key)

        if value._previousKey is not None:
            self._get(value._previousKey)._setNext(value._nextKey,
                                                   value._previousKey, self)
        else:
            self._firstKey = value._nextKey
            
        if value._nextKey is not None:
            self._get(value._nextKey)._setPrevious(value._previousKey,
                                                   value._nextKey, self)
        else:
            self._lastKey = value._previousKey
                
        super(LinkedMap, self).__delitem__(key)

    def get(self, key, default=None):

        link = super(LinkedMap, self).get(key, default)

        if link is not default:
            return link._value

        return default

    def first(self):
        "Return the value mapped to the first key."

        if self._firstKey is not None:
            return self[self._firstKey]

        return None

    def last(self):
        "Return the value mapped to the last key."

        if self._lastKey is not None:
            return self[self._lastKey]

        return None
        
    def next(self, key):
        "Return the value mapped to the next key relative to key."

        nextKey = self._get(key)._nextKey
        if nextKey is not None:
            return self[nextKey]

        return None

    def previous(self, key):
        "Return the value mapped to the previous key relative to key."

        previousKey = self._get(key)._previousKey
        if previousKey is not None:
            return self[previousKey]

        return None

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

        keys = []
        for key in self.iterkeys():
            keys.append(key)

        return keys

    def _keys(self):

        return super(LinkedMap, self).keys()

    def values(self):

        values = []
        for item in self:
            values.append(item)

        return values

    def _values(self):

        values = []
        for key in self._iterkeys():
            values.append(self._get(key))

        return values

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

        items = []
        for key in self.iterkeys():
            items.append((key, self[key]))

    def _items(self):

        items = []
        for key in self._iterkeys():
            items.append((key, self._get(key)))
