
import Item


class ItemRef(object):
    'A wrapper around a bi-directional link between two items.'
    
    def __init__(self, item, other, name):

        super(ItemRef, self).__init__()

        self._attach(item, other, name)

    def __repr__(self):

        return ("<ItemRef: " + str(self._item) + " <--> " +
                str(self._other) + ">")

    def getItem(self):
        'Return the item this link was established from.'
        
        return self._item

    def getOther(self):
        'Return the opposite item this link was established from.'

        return self._other

    def _attach(self, item, other, name):

        self._item = item
        self._other = other

        if other is not None:
            if other.hasAttribute(name):
                old = other.getAttribute(name)
                if isinstance(old, RefDict):
                    old[item.refName()] = self
                    return
            
            other.setAttribute(name, self)

    def _detach(self, item, other, name):

        old = other.getAttribute(name)
        if isinstance(old, RefDict):
            old._removeRef(item.refName(name))
        else:
            other._removeRef(name)

    def _reattach(self, item, old, new, name):

        self._detach(item, old, name)
        self._attach(item, new, name)

    def other(self, item):
        'Return the other end of the link relative to item.'

        if self._item is item:
            return self._other
        elif self._other is item:
            return self._item
        else:
            return None


class RefDict(dict):

    def __init__(self, item, name, refs=None):

        super(RefDict, self).__init__()

        self._item = item
        self._name = name
        
        if refs is not None:
            self.update(refs)

    def update(self, dict):

        for pair in dict.iteritems():
            self[pair[0]] = pair[1]

    def __getitem__(self, key):

        value = super(RefDict, self).__getitem__(key)
        if isinstance(value, ItemRef):
            value = value.other(self._item)

        return value

    def __setitem__(self, key, value):

        old = super(RefDict, self).get(key)
        otherName = self._item._otherName(self._name)
        isItem = isinstance(value, Item.Item)

        if isinstance(old, ItemRef):
            if isItem:
                old._reattach(self._item, old.other(self._item),
                              value, otherName)
            else:
                old._detach(self._item, old.other(self._item), otherName)
        else:
            if isItem:
                value = ItemRef(self._item, value, otherName)
            
            super(RefDict, self).__setitem__(key, value)

    def __delitem__(self, key):

        value = super(RefDict, self).__getitem__(key)
        value._detach(self._item, value.other(self._item),
                      self._item._otherName(self._name))

    def _removeRef(self, key):

        super(RefDict, self).__delitem__(key)
