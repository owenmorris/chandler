
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
    
    def __init__(self, item, name, other, otherName,
                 otherCard=None, otherPersist=None):

        super(ItemRef, self).__init__()
        self.attach(item, name, other, otherName, otherCard, otherPersist)

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

    def attach(self, item, name, other, otherName,
               otherCard=None, otherPersist=None):

        assert item is not None, 'item is None'
        assert other is not None, 'other is None'

        self._item = item
        self._other = other

        if type(other) is not ItemStub:
            if other.hasAttributeValue(otherName):
                old = other.getAttributeValue(otherName)
                if isinstance(old, RefDict):
                    old[item._refName(otherName)] = self
                    return
            else:
                if otherCard is None:
                    otherCard = other.getAttributeAspect(otherName,
                                                         'cardinality',
                                                         'single')
                if otherCard != 'single':
                    old = other._refDict(otherName, name, otherPersist)
                    other._references[otherName] = old
                    old[item._refName(otherName)] = self
                    return
            
            other.setAttributeValue(otherName, self,
                                    _attrDict=other._references)

    def detach(self, item, name, other, otherName):

        old = other.getAttributeValue(otherName, _attrDict=other._references)

        if isinstance(old, RefDict):
            old._removeRef(item._refName(otherName))
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

    def _xmlValue(self, name, item, generator, withSchema, mode,
                  previous=None, next=None):

        def addAttr(attrs, attr, value):

            if value is not None:
                if isinstance(value, UUID):
                    attrs[attr + 'Type'] = 'uuid'
                    attrs[attr] = value.str64()
                elif isinstance(attr, str) or isinstance(attr, unicode):
                    attrs[attr] = value.encode('utf-8')
                else:
                    raise NotImplementedError, "%s, type: %s" %(value,
                                                                type(value))

        other = self.other(item)
        attrs = { 'type': 'uuid' }

        addAttr(attrs, 'name', name)
        addAttr(attrs, 'previous', previous)
        addAttr(attrs, 'next', next)

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
                 valueDict, previous=None, next=None, alias=None):

        super(RefArgs, self).__init__()
        
        self.attrName = attrName
        self.refName = refName
        self.spec = spec
        self.otherName = otherName
        self.otherCard = otherCard
        self.valueDict = valueDict
        self.previous = previous
        self.next = next
        self.alias = alias
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
                self.refName = other._refName(self.attrName)

        if other is not None:
            if not other._isAttaching():
                try:
                    item._setAttaching()
                    self._attach(item, other)
                finally:
                    item._setAttaching(False)
        else:
            self.ref = ItemRef(item, self.attrName,
                               ItemStub(item, self), self.otherName,
                               self.otherCard)
            repository._addStub(self.ref)
            self.valueDict.__setitem__(self.refName, self.ref, 
                                       self.previous, self.next, self.alias,
                                       False)

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
                                           self.previous, self.next,
                                           self.alias)

        elif isinstance(value, ItemRef):
            if isinstance(value._other, ItemStub):
                value._other = item
                self.valueDict.__setitem__(self.refName, value,
                                           self.previous, self.next,
                                           self.alias)

        elif isinstance(value, RefDict):
            otherRefName = item._refName(self.otherName)
            if value.has_key(otherRefName):
                value = value._getRef(otherRefName)
                if isinstance(value._other, ItemStub):
                    value._other = item
                    self.valueDict.__setitem__(self.refName, value,
                                               self.previous, self.next,
                                               self.alias)
            else:
                if self.ref is not None:
                    self.ref.attach(item, self.attrName,
                                    other, self.otherName, self.otherCard)
                else:
                    self.ref = ItemRef(item, self.attrName,
                                       other, self.otherName, self.otherCard)
                    self.valueDict.__setitem__(self.refName, self.ref,
                                               self.previous, self.next,
                                               self.alias)

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

    class link(LinkedMap.link):

        def __init__(self, value):

            super(RefDict.link, self).__init__(value)
            self._alias = None

    def __init__(self, item, name, otherName):

        self._name = name
        self._otherName = otherName
        self._setItem(item)
        self._count = 0
        self._aliases = None
        
        super(RefDict, self).__init__()

    def _makeLink(self, value):

        return RefDict.link(value)

    def _setItem(self, item):

        self._item = item

    def _getItem(self):

        return self._item

    def _getRepository(self):

        return self._item.getRepository()

    def _isTransient(self):

        return False

    def __len__(self):

        return self._count

    def __repr__(self):

        return '<%s: %s.%s.%s>' %(type(self).__name__,
                                  self._getItem().getItemPath(),
                                  self._name, self._otherName)

    def __contains__(self, obj):

        if isinstance(obj, model.item.Item.Item):
            return self.has_key(obj._refName(self._name))

        return self.has_key(obj)

    def extend(self, valueList):

        for value in valueList:
            self.append(value)

    def append(self, item, alias=None):

        self.__setitem__(item._refName(self._name), item, alias=alias)

    def clear(self):

        for key in self.keys():
            del self[key]

    def dir(self):

        for item in self:
            print item

    def __getitem__(self, key):

        return self._getRef(key).other(self._getItem())

    def __setitem__(self, key, value,
                    previousKey=None, nextKey=None, alias=None,
                    load=True):

        loading = self._getRepository().isLoading()
        self._changeRef(key)

        if loading and previousKey is None and nextKey is None:
            ref = self._loadRef(key)
            if ref is not None:
                previousKey = ref[2]
                nextKey = ref[3]
                alias = ref[4]
        
        old = super(RefDict, self).get(key, None, load)
        if old is not None:
            item = self._getItem()
            if type(value) is ItemRef:
                old.detach(item, self._name,
                           old.other(item), self._otherName)
            else:
                if value is not old.other(item):
                    print 'Warning: reattaching %s for %s on %s' %(value,
                                                                   old.other(item),
                                                                   self._name)
                    old.reattach(item, self._name,
                                 old.other(item), value, self._otherName)
                return old

        if type(value) is not ItemRef:
            value = ItemRef(self._getItem(), self._name,
                            value, self._otherName)

        link = super(RefDict, self).__setitem__(key, value,
                                                previousKey, nextKey)
        if alias:
            link._alias = alias
            if self._aliases is None:
                self._aliases = {}
            self._aliases[alias] = key
            
        if not loading:
            self._count += 1

        return value

    def placeItem(self, item, after):
        """Place an item in this collection after another one.

        Both items must already belong to the collection. To place an item
        first,  pass None for 'after'."""
        
        key = item._refName(self._name)
        if after is not None:
            afterKey = after._refName(self._name)
        else:
            afterKey = None

        super(RefDict, self).place(key, afterKey)

    def removeItem(self, item):
        "Remove a referenced item from this reference collection."
        
        del self[item._refName(self._name)]
            
    def __delitem__(self, key):

        self._removeRef(key, True)

    def _removeRef(self, key, _detach=False):

        value = self._getRef(key)

        if _detach:
            value.detach(self._item, self._name,
                         value.other(self._item), self._otherName)

        link = super(RefDict, self).__delitem__(key)
        if link._alias:
            del self._aliases[link._alias]
            
        self._count -= 1

    def _load(self, key):

        repository = self._item.getRepository()

        try:
            loading = repository.setLoading()
            ref = self._loadRef(key)
            if ref is not None:
                args = RefArgs(self._name, ref[0], ref[1],
                               self._otherName, None, self,
                               ref[2], ref[3], ref[4])
                args.attach(self._item, self._item.getRepository())
                
                return True
        finally:
            repository.setLoading(loading)

        return False

    def _loadRef(self, key):

        return None

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

    def getByAlias(self, alias):
        'Get the item referenced through the alias.'
        
        return self[self._aliases[alias]]

    def resolveAlias(self, alias):
        """Resolve the alias to its corresponding reference key.

        Returns None if alias does not exist."""
        
        if self._aliases:
            return self._aliases.get(alias)

        return None

    def _refCount(self):

        return len(self)

    def _xmlValue(self, name, item, generator, withSchema, mode):

        def addAttr(attrs, attr, value):

            if value is not None:
                if isinstance(value, UUID):
                    attrs[attr + 'Type'] = 'uuid'
                    attrs[attr] = value.str64()
                elif isinstance(attr, str) or isinstance(attr, unicode):
                    attrs[attr] = value.encode('utf-8')
                else:
                    raise NotImplementedError, "%s, type: %s" %(value,
                                                                type(value))

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

            addAttr(attrs, 'first', self._firstKey)
            addAttr(attrs, 'last', self._lastKey)
            attrs['count'] = str(self._count)

            generator.startElement('ref', attrs)
            if self._aliases:
                for key, value in self._aliases.iteritems():
                    generator.startElement('alias', { 'name': key })
                    generator.characters(value.str64())
                    generator.endElement('alias')
            self._xmlValues(generator, mode)
            generator.endElement('ref')

    def _xmlValues(self, generator, mode):

        for key in self.iterkeys():
            link = self._get(key)
            link._value._xmlValue(key, self._item,
                                  generator, False, mode,
                                  previous=link._previousKey,
                                  next=link._nextKey)

    def copy(self):

        raise NotImplementedError, 'RefDict.copy is not supported'

    def first(self):

        firstKey = self.firstKey()
        if firstKey is not None:
            return self[firstKey]

        return None

    def last(self):

        lastKey = self.lastKey()
        if lastKey is not None:
            return self[lastKey]

        return None

    def next(self, previous):
        """Return the next referenced item relative to previous.

        Returns None if previous is the last referenced item in the
        collection."""

        nextKey = self.nextKey(previous._refName(self._name))
        if nextKey is not None:
            return self[nextKey]

        return None

    def previous(self, next):
        """Return the previous referenced item relative to next.

        Returns None if next is the first referenced item in the
        collection."""

        previousKey = self.previousKey(next._refName(self._name))
        if previousKey is not None:
            return self[previousKey]

        return None


class TransientRefDict(RefDict):

    def linkChanged(self, link, key):
        pass
    
    def _changeRef(self, key):
        pass

    def _load(self, key):
        return False
    
    def _isTransient(self):
        return True


class DanglingRefError(ValueError):
    pass
