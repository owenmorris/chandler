__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" KindShorthand - provide immutable dictionary access to a Kind """

class KindShorthand(object):
    def __init__(self, theKind):
        self.theKind = theKind

    def __len__(self):
        i = 0
        for n in self.theKind.iterItems():
            i += 1
        return i

    def __contains__(self, item):
        for n in self.theKind.iterItems():
            if n is item:
                return True
        return False

    def __getitem__(self, key):
        for n in self.theKind.iterItems():
            if self._itemName(n) == key:
                return n
        raise KeyError

    def __iter__(self):
        return self.theKind.iterItems()

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def has_key(self, key):
        for n in self.theKind.iterItems():
            if self._itemName(n) == key:
                return True
        return False

    def items(self):
        l = []
        for n in self.theKind.iterItems():
            l.append ((self._itemName(n), n))
        return l

    def keys(self):
        l = []
        for n in self.theKind.iterItems():
            l.append(self._itemName(n))
        return l

    def values(self):
        l = []
        for n in self.theKind.iterItems():
            l.append(n)
        return l

    def iteritems(self):
        for n in self.theKind.iterItems():
            yield (self._itemName(n), n)

    def iterkeys(self):
        for n in self.theKind.iterItems():
            yield self._itemName(n)

    def itervalues(self):
        for n in self.theKind.iterItems():
            yield n

    def _itemName(self, item):
        try:
            return item.about
        except AttributeError:
            pass
        try:
            return item.blockName
        except AttributeError:
            pass
        try:
            return item.displayName
        except AttributeError:
            pass
        try:
            return item.itsName
        except AttributeError:
            pass
        return "anonymous"
