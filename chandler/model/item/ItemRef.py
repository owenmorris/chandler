
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import model.item.Item

from model.util.UUID import UUID
from model.util.Path import Path
from model.util.LinkedMap import LinkedMap


class ItemRef(object):
    'A wrapper around a bi-directional link between two items.'
    
    def __init__(self, item, name, other, otherName, otherCard=None):

        super(ItemRef, self).__init__()
        self.attach(item, name, other, otherName, otherCard)

    def __repr__(self):

        return '<ItemRef: %s>' %(self._other)

    def _getItem(self):

        return self._item

    def _setItem(self, item):
        pass

    def getItem(self):
        'Return the item this link was established from.'
        
        return self._item

    def getOther(self):
        'Return the opposite item this link was established from.'

        other = self._other._loadItem()

        if other is not None:
            self._other = other
            return other

        raise DanglingRefError, '%s <-> %s' %(self._item, self._other)

    def attach(self, item, name, other, otherName, otherCard=None):

        assert item is not None, 'item is None'
        assert other is not None, 'other is None'

        self._item = item
        self._other = other

        if type(other) is not ItemStub:
            if other.hasAttributeValue(otherName):
                old = other.getAttributeValue(otherName)
                if isinstance(old, RefDict):
                    refName = item.refName(otherName)
                    old[refName] = self
                    return
            else:
                if otherCard is None:
                    otherCard = other.getAttributeAspect(otherName,
                                                         'cardinality',
                                                         'single')
                if otherCard != 'single':
                    old = other._refDict(otherName, name)
                    other._references[otherName] = old
                    old[item.refName(otherName)] = self
                    return
            
            other.setAttributeValue(otherName, self,
                                    _attrDict=other._references)

    def detach(self, item, name, other, otherName):

        old = other.getAttributeValue(otherName, _attrDict=other._references)

        if isinstance(old, RefDict):
            old._removeRef(item.refName(otherName))
        else:
            other._removeRef(otherName)

    def reattach(self, item, name, old, new, otherName):

        self.detach(item, name, old, otherName)
        self.attach(item, name, new, otherName)

    def other(self, item):
        'Return the other end of the ref relative to item.'

        if self.getItem() is item:
            return self.getOther()
        elif self.getOther() is item:
            return self.getItem()
        else:
            raise ValueError, "%s doesn't reference %s" %(self, item)

    def _endpoints(self, item, name, other, otherName):

        if self._item is item:
            if self._other is other:
                return (item, name, other, otherName)
            return (item, name, None, otherName)
        elif self._other is item:
            if self._item is other:
                return (other, otherName, item, name)
            return (other, otherName, None, name)

        return (None, name, None, otherName)

    def _refCount(self):

        return 1

    def _xmlValue(self, name, item, generator, withSchema, mode):

        other = self.other(item)
        attrs = { 'type': 'uuid' }

        if isinstance(name, UUID):
            attrs['nameType'] = "uuid"
            attrs['name'] = name.str64()
        elif isinstance(name, str) or isinstance(name, unicode):
            attrs['name'] = str(name)
        else:
            raise NotImplementedError, "refName: %s, type: %s" %(name,
                                                                 type(name))

        if withSchema:
            otherName = item._otherName(name)
            attrs['otherName'] = otherName
            attrs['otherCard'] = other.getAttributeAspect(otherName,
                                                          'cardinality',
                                                          'single')

        generator.startElement('ref', attrs)
        generator.characters(other.getUUID().str64())
        generator.endElement('ref')


class ItemStub(object):
    
    def __init__(self, item, args):

        super(ItemStub, self).__init__()

        self.item = item
        self.args = args

    def __repr__(self):

        return '<ItemStub: %s>' %(self.args.spec)

    def _loadItem(self):

        other = self.item.find(self.args.spec)
        if other is not None:
            self.args._attach(self.item, other)

        return other
    

class RefArgs(object):
    'A wrapper around arguments necessary to make and store an ItemRef'
    
    def __init__(self, attrName, refName, spec, otherName, otherCard,
                 valueDict, previous=None, next=None):

        super(RefArgs, self).__init__()
        
        self.attrName = attrName
        self.refName = refName
        self.spec = spec
        self.otherName = otherName
        self.otherCard = otherCard
        self.valueDict = valueDict
        self.previous = previous
        self.next = next
        self.ref = None
        
    def attach(self, item, repository):

        if isinstance(self.spec, UUID):
            other = repository.find(self.spec, load=False)
        else:
            other = item.find(self.spec, load=False)
            
        if self.refName is None:
            if other is None:
                raise ValueError, "refName to %s is unspecified, %s should be loaded before %s" %(self.spec, self.spec, item.getItemPath())
            else:
                self.refName = other.refName(self.attrName)

        if other is not None:
            self._attach(item, other)

        else:
            self.ref = ItemRef(item, self.attrName,
                               ItemStub(item, self), self.otherName,
                               self.otherCard)
            repository._addStub(self.ref)
            self.valueDict.__setitem__(self.refName, self.ref, 
                                       self.previous, self.next)

    def _attach(self, item, other):
        
        value = other._references.get(self.otherName)
        
        if value is None:
            if self.ref is not None:
                self.ref.attach(item, self.attrName,
                                other, self.otherName, self.otherCard)
            else:
                self.ref = ItemRef(item, self.attrName,
                                   other, self.otherName, self.otherCard)
                self.valueDict.__setitem__(self.refName, self.ref, 
                                           self.previous, self.next)

        elif isinstance(value, ItemRef):
            if isinstance(value._other, ItemStub):
                value._other = item
                self.valueDict.__setitem__(self.refName, value,
                                           self.previous, self.next)

        elif isinstance(value, RefDict):
            otherRefName = item.refName(self.otherName)
            if value.has_key(otherRefName):
                value = value._getRef(otherRefName)
                if isinstance(value._other, ItemStub):
                    value._other = item
                    self.valueDict.__setitem__(self.refName, value,
                                               self.previous, self.next)
            else:
                if self.ref is not None:
                    self.ref.attach(item, self.attrName,
                                    other, self.otherName, self.otherCard)
                else:
                    self.ref = ItemRef(item, self.attrName,
                                       other, self.otherName, self.otherCard)
                    self.valueDict.__setitem__(self.refName, self.ref,
                                               self.previous, self.next)

        else:
            raise ValueError, value


class Values(dict):

    def __init__(self, item):

        super(Values, self).__init__()
        self._setItem(item)

    def _setItem(self, item):

        self._item = item

    def _getItem(self):

        return self._item

    def __setitem__(self, key, value):

        if self._item is not None:
            self._item.setDirty()

        super(Values, self).__setitem__(key, value)

    def __delitem__(self, key):

        if self._item is not None:
            self._item.setDirty()

        super(Values, self).__delitem__(key)


class References(Values):

    def _setItem(self, item):

        for ref in self.itervalues():
            ref._setItem(item)

        self._item = item

    def __setitem__(self, key, value, *args):

        super(References, self).__setitem__(key, value)


class RefDict(LinkedMap):

    def __init__(self, item, name, otherName):

        self._name = name
        self._otherName = otherName
        self._setItem(item)

        super(RefDict, self).__init__()

    def _setItem(self, item):

        self._item = item

    def _getItem(self):

        return self._item

    def __repr__(self):

        return '<%s: %s.%s.%s>' %(type(self).__name__,
                                  self._getItem().getItemPath(),
                                  self._name, self._otherName)

    def __contains__(self, obj):

        if isinstance(obj, model.item.Item.Item):
            return self.has_key(obj.refName(self._name))

        return self.has_key(obj)

    def extend(self, valueList):

        for value in valueList:
            self.append(value)

    def append(self, value):

        self[value.refName(self._name)] = value

    def clear(self):

        for key in self.keys():
            del self[key]

    def dir(self):

        for item in self:
            print item

    def __getitem__(self, key):

        return self._getRef(key).other(self._getItem())

    def __setitem__(self, key, value, previousKey=None, nextKey=None):

        self._changeRef(key)
        
        old = super(RefDict, self).get(key)
        if old is not None:
            item = self._getItem()
            if type(value) is ItemRef:
                old.detach(item, self._name,
                           old.other(item), self._otherName)
            else:
                old.reattach(item, self._name,
                             old.other(item), value, self._otherName)
                return old

        if type(value) is not ItemRef:
            value = ItemRef(self._getItem(), self._name,
                            value, self._otherName)

        super(RefDict, self).__setitem__(key, value, previousKey, nextKey)

    def placeItem(self, item, after):
        """Place an item in this collection after another one.

        Both items must already belong to the collection. To place an item
        first,  pass None for 'after'."""
        
        key = item.refName(self._name)
        if after is not None:
            afterKey = after.refName(self._name)
        else:
            afterKey = None

        super(RefDict, self).place(key, afterKey)
            
    def __delitem__(self, key):

        self._removeRef(key, True)

    def _removeRef(self, key, _detach=False):

        value = self._getRef(key)

        if _detach:
            value.detach(self._item, self._name,
                         value.other(self._item), self._otherName)

        super(RefDict, self).__delitem__(key)

    def linkChanged(self, link, key):

        if key is not None:
            self._changeRef(key)

    def _changeRef(self, key):

        self._item.setDirty()

    def _getRef(self, key, load=True):

        return super(RefDict, self).__getitem__(key, load)

    def get(self, key, default=None, load=True):

        value = super(RefDict, self).get(key, default, load)
        if value is not default:
            return value.other(self._item)

        return default

    def _refCount(self):

        return len(self)

    def _xmlValue(self, name, item, generator, withSchema, mode):

        if len(self) > 0:

            if withSchema:
                for other in self:
                    break

            attrs = { 'name': name }
            if withSchema:
                otherName = item._otherName(name)
                otherCard = other.getAttributeAspect(otherName, 'cardinality',
                                                     'single')
                attrs['cardinality'] = 'list'
                attrs['otherName'] = otherName
                attrs['otherCard'] = otherCard

            generator.startElement('ref', attrs)
            self._xmlValues(generator, mode)
            generator.endElement('ref')

    def _xmlValues(self, generator, mode):

        for key in self.iterkeys():
            self._getRef(key)._xmlValue(key, self._item,
                                        generator, False, mode)

    def copy(self):

        raise NotImplementedError, 'RefDict.copy is not supported'

    def next(self, previous):
        """Return the next referenced item relative to previous.

        Returns None if previous is the last referenced item in the
        collection."""

        return super(RefDict, self).next(previous.refName(self._name))

    def previous(self, next):
        """Return the previous referenced item relative to next.

        Returns None if next is the first referenced item in the
        collection."""

        return super(RefDict, self).previous(next.refName(self._name))


class DanglingRefError(ValueError):
    pass
