
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

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
                    old[item.refName(name)] = self
                    return
            elif other.getAttrAspect(name, 'Cardinality', 'single') == 'dict':
                old = RefDict(other, other._otherName(name))
                other._attributes[name] = old
                old[item.refName(name)] = self
                return
            
            other.setAttribute(name, self)

    def _detach(self, item, other, name):

        if other is not None:
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

    def __init__(self, item, otherName, initialDict=None):

        super(RefDict, self).__init__()

        self._item = item
        self._otherName = otherName
        
        if initialDict is not None:
            self.update(initialDict)

    def update(self, valueDict):

        for value in valueDict.iteritems():
            self[value[0]] = value[1]

    def __getitem__(self, key):

        value = super(RefDict, self).__getitem__(key)
        if isinstance(value, ItemRef):
            value = value.other(self._item)

        return value

    def __setitem__(self, key, value):

        old = super(RefDict, self).get(key)
        isItem = isinstance(value, Item.Item)

        if isinstance(old, ItemRef):
            if isItem:
                old._reattach(self._item, old.other(self._item),
                              value, self._otherName)
            else:
                old._detach(self._item, old.other(self._item),
                            self._otherName)
        else:
            if isItem:
                value = ItemRef(self._item, value, self._otherName)
            
            super(RefDict, self).__setitem__(key, value)

    def __delitem__(self, key):

        value = super(RefDict, self).__getitem__(key)
        value._detach(self._item, value.other(self._item), self._otherName)

    def _removeRef(self, key):

        super(RefDict, self).__delitem__(key)

    def _getRef(self, key):

        return super(RefDict, self).get(key)

    def get(self, key, default=None):

        value = super(RefDict, self).get(key, default)
        if value is not default:
            value = value.other(self._item)

        return value

class RefList(list):

    def __init__(self, item, otherName, initialList=None):

        super(RefList, self).__init__()

        self._item = item
        self._otherName = otherName
        
        if initialList is not None:
            self.extend(initialList)

    def extend(self, valueList):

        for value in valueList:
            self.append(value)

    def append(self, value):

        if not self.__contains__(value):
            super(RefList, self).append(value)

    def __contains__(self, value):

        if isinstance(value, Item):
            for ref in self:
                if ref.other(self._item) is value:
                    return True
        elif isinstance(value, ItemRef):
            for ref in self:
                if ref is value:
                    return True

        return False

    def __getitem__(self, key):

        value = super(RefList, self).__getitem__(key)
        if isinstance(value, ItemRef):
            value = value.other(self._item)

        return value

    def __setitem__(self, key, value):

        old = super(RefList, self).get(key)
        isItem = isinstance(value, Item.Item)

        if isinstance(old, ItemRef):
            if isItem:
                old._reattach(self._item, old.other(self._item),
                              value, self._otherName)
            else:
                old._detach(self._item, old.other(self._item),
                            self._otherName)
        else:
            if isItem:
                value = ItemRef(self._item, value, self._otherName)
            
            super(RefList, self).__setitem__(key, value)

    def __delitem__(self, key):

        value = super(RefList, self).__getitem__(key)
        value._detach(self._item, value.other(self._item), self._otherName)

    def _removeRef(self, key):

        super(RefList, self).__delitem__(key)

    def _getRef(self, key):

        return super(RefList, self).get(key)

    def get(self, key, default=None):

        value = super(RefList, self).get(key, default)
        if value is not default:
            value = value.other(self._item)

        return value

