
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.item.Item

from repository.util.UUID import UUID
from repository.util.Path import Path
from repository.util.LinkedMap import LinkedMap


class ItemRef(object):
    'A wrapper around a bi-directional link between two items.'
    
    def __init__(self, item, name, other, otherName,
                 otherCard=None, otherPersist=None):

        super(ItemRef, self).__init__()
        self.attach(item, name, other, otherName, otherCard, otherPersist)

    def __repr__(self):

        return '<ItemRef: %s - %s>' %(self._item, self._other)

    def _setItem(self, item):
        pass

    def getItem(self):
        'Return the item this link was established from.'
        
        item = self._item._loadItem()

        if item is not None:
            self._item = item
            return item

        raise DanglingRefError, '%s <-> %s' %(self._item, self._other)

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

        if not isinstance(other, Stub):
            if other.hasAttributeValue(otherName):
                old = other.getAttributeValue(otherName)
                if isinstance(old, RefDict):
                    old[item._refName(otherName)] = self
                    return
            else:
                if otherCard is None:
                    otherCard = other.getAttributeAspect(otherName,
                                                         'cardinality',
                                                         default='single')
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

        other.setDirty(attribute=otherName)

    def reattach(self, item, name, old, new, otherName):

        self.detach(item, name, old, otherName)
        self.attach(item, name, new, otherName)

    def _unload(self, item):

        if item is self.getItem():
            self._item = UUIDStub(self.getOther(), item)
        elif item is self.getOther():
            self._other = UUIDStub(self.getItem(), item)
        else:
            raise ValueError, "%s doesn't reference %s" %(self, item)

    def other(self, item):
        'Return the other end of the ref relative to item.'

        if self.getItem() is item:
            return self.getOther()
        elif self.getOther() is item:
            return self.getItem()
        else:
            raise ValueError, "%s doesn't reference %s" %(self, item)

    def check(self, item, name):

        logger = item.getRepository().logger
        
        try:
            other = self.other(item)
        except DanglingRefError, e:
            logger.error('DanglingRefError: %s', e)
        except ValueError, e:
            logger.error('ValueError: %s', e)
        else:
            if other.isStale():
                logger.error('Found stale item %s at %s of kind %s',
                             other, other.getItemPath(),
                             other._kind.getItemPath())
            else:
                otherName = item.getAttributeAspect(name, 'otherName',
                                                    default=None)
                otherOtherName = other.getAttributeAspect(otherName,
                                                          'otherName',
                                                          default=None)
                if otherOtherName != name:
                    logger.error("otherName for attribute %s.%s, %s, does not match otherName for attribute %s.%s, %s",
                                 item._kind.getItemPath(), name, otherName,
                                 other._item._kind.getItemPath(), otherName,
                                 otherOtherName)

        return True

    def _refCount(self):

        return 1

    def _xmlValue(self, name, item, generator, withSchema, version, mode,
                  previous=None, next=None, alias=None):

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
        addAttr(attrs, 'alias', alias)

        if withSchema:
            attrs['otherName'] = item._otherName(name)

        generator.startElement('ref', attrs)
        generator.characters(other.getUUID().str64())
        generator.endElement('ref')


class _noneRef(ItemRef):

    def __init__(self):
        super(_noneRef, self).__init__(None, None, None, None)

    def __repr__(self):
        return '<NoneRef>'

    def attach(self, item, name, other, otherName,
               otherCard=None, otherPersist=None):
        pass

    def detach(self, item, name, other, otherName):
        pass
    
    def reattach(self, item, name, old, new, otherName):
        item.name = ItemRef(item, name, new, otherName)
    
    def getItem(self):
        return None

    def getOther(self):
        return None

    def _unload(self, item):
        pass

    def other(self, item):
        return None

    def check(self, item, name):
        pass

    def _refCount(self):
        return 0

    def _xmlValue(self, name, item, generator, withSchema, version, mode,
                  previous=None, next=None, alias=None):

        generator.startElement('ref', {'name': name, 'type': 'none'})
        generator.endElement('ref')

    def __new__(cls, *args, **kwds):

        try:
            return _noneRef._noneRef
        except AttributeError:
            _noneRef._noneRef = ItemRef.__new__(cls, *args, **kwds)
            return _noneRef._noneRef

NoneRef = _noneRef()


class Stub(object):
    pass


class ItemStub(Stub):
    
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


class UUIDStub(Stub):

    def __init__(self, item, other):

        super(UUIDStub, self).__init__()

        self.item = item
        self.uuid = other.getUUID()

    def __repr__(self):

        return '<UUIDStub: %s>' %(self.uuid)

    def _loadItem(self):

        other = self.item.find(self.uuid)
        if other is None:
            raise DanglingRefError, '%s <-> %s' %(self.item, self.uuid)

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
                    return self._attach(item, other)
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

        return None

    def _attach(self, item, other):
        
        value = other._references.get(self.otherName)
        
        if value is None or value is NoneRef:
            if self.ref is not None:
                self.ref.attach(item, self.attrName,
                                other, self.otherName, self.otherCard)
            else:
                value = ItemRef(item, self.attrName,
                                other, self.otherName, self.otherCard)
                self.valueDict.__setitem__(self.refName, value,
                                           self.previous, self.next,
                                           self.alias, False)

        elif isinstance(value, ItemRef):
            if isinstance(value._other, Stub):
                value._other = item
                self.valueDict.__setitem__(self.refName, value,
                                           self.previous, self.next,
                                           self.alias, False)

            elif isinstance(value._item, Stub):
                value._item = item
                self.valueDict.__setitem__(self.refName, value,
                                           self.previous, self.next,
                                           self.alias, False)
            else:
                return value

        elif isinstance(value, RefDict):
            otherRefName = item._refName(self.otherName)
            if value.has_key(otherRefName):
                value = value._getRef(otherRefName)
                if isinstance(value._other, Stub):
                    value._other = item
                    self.valueDict.__setitem__(self.refName, value,
                                               self.previous, self.next,
                                               self.alias, False)

                elif isinstance(value._item, Stub):
                    value._item = item
                    self.valueDict.__setitem__(self.refName, value,
                                               self.previous, self.next,
                                               self.alias, False)
                else:
                    return value

            else:
                if self.ref is not None:
                    self.ref.attach(item, self.attrName,
                                    other, self.otherName, self.otherCard)
                else:
                    value = ItemRef(item, self.attrName,
                                    other, self.otherName, self.otherCard)
                    self.valueDict.__setitem__(self.refName, value,
                                               self.previous, self.next,
                                               self.alias, False)

        else:
            raise ValueError, value

        return None


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
            self._item.setDirty(attribute=key)

        super(Values, self).__setitem__(key, value)

    def __delitem__(self, key):

        if self._item is not None:
            self._item.setDirty(attribute=key)

        super(Values, self).__delitem__(key)

    def _unload(self):

        self.clear()
        

class References(Values):

    def _setItem(self, item):

        for value in self.itervalues():
            value._setItem(item)

        self._item = item

    def __setitem__(self, key, value, *args):

        super(References, self).__setitem__(key, value)

    def _unload(self):

        for value in self.itervalues():
            value._unload(self._item)


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

        if isinstance(obj, repository.item.Item.Item):
            return self.has_key(obj._refName(self._name))

        return self.has_key(obj)

    def extend(self, valueList):

        for value in valueList:
            self.append(value)

    def update(self, dictionary):

        for value in dictionary.itervalues():
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
        if not loading:
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
                    self._getRepository().logger.warning('Warning: reattaching %s for %s on %s',
                                                         value,
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
        loading = None
        
        try:
            loading = repository.setLoading()
            ref = self._loadRef(key)
            if ref is not None:
                args = RefArgs(self._name, ref[0], ref[1],
                               self._otherName, None, self,
                               ref[2], ref[3], ref[4])
                value = args.attach(self._item, self._item.getRepository())
                if value is not None:
                    self.__setitem__(args.refName, value, args.previous,
                                     args.next, args.alias, False)
                    
                return True
        finally:
            if loading is not None:
                repository.setLoading(loading)

        return False

    def _unload(self, item):

        for link in self._itervalues():
            link._value._unload(item)

    def _loadRef(self, key):

        return None

    def linkChanged(self, link, key):

        if key is not None:
            self._changeRef(key)

    def _changeRef(self, key):

        self._item.setDirty(attribute=self._name)

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

    def _xmlValue(self, name, item, generator, withSchema, version, mode):

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

        attrs = { 'name': name }
        
        if withSchema:
            attrs['cardinality'] = 'list'
            attrs['otherName'] = item._otherName(name)

        addAttr(attrs, 'first', self._firstKey)
        addAttr(attrs, 'last', self._lastKey)
        attrs['count'] = str(self._count)

        generator.startElement('ref', attrs)
        self._xmlValues(generator, version, mode)
        generator.endElement('ref')

    def _xmlValues(self, generator, version, mode):

        for key in self.iterkeys():
            link = self._get(key)
            link._value._xmlValue(key, self._item,
                                  generator, False, version, mode,
                                  previous=link._previousKey,
                                  next=link._nextKey,
                                  alias=link._alias)

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

    def check(self, item, name):

        l = len(self)
        logger = self._getRepository().logger
        
        key = self.firstKey()
        while key:
            try:
                other = self[key]
            except DanglingRefError, e:
                logger.error('DanglingRefError on %s.%s: %s',
                             self._item.getItemPath(), self._name, e)
            except KeyError, e:
                logger.error('KeyError on %s.%s: %s',
                             self._item.getItemPath(), self._name, e)
            else:
                if other.isStale():
                    logger.error('Found stale item %s at %s of kind %s',
                                 other, other.getItemPath(),
                                 other._kind.getItemPath())
                else:
                    name = other.getAttributeAspect(self._otherName, 'otherName', default=None)
                    if name != self._name:
                        logger.error("OtherName for attribute %s.%s, %s, does not match otherName for attribute %s.%s, %s",
                                     other._kind.getItemPath(),
                                     self._otherName, name,
                                     self._item._kind.getItemPath(),
                                     self._name, self._otherName)
                        
            l -= 1
            key = self.nextKey(key)
            
        if l != 0:
            logger.error("Iterator on %s.%s doesn't match length (%d left for %d total)",
                         self._item.getItemPath(), self._name, l, len(self))

        return True


class TransientRefDict(RefDict):

    def linkChanged(self, link, key):
        pass
    
    def _changeRef(self, key):
        pass

    def check(self, item, name):
        return True

    def _load(self, key):
        return False
    
    def _isTransient(self):
        return True


class DanglingRefError(ValueError):
    pass
