
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.item as ItemPackage

from repository.util.UUID import UUID
from repository.util.Path import Path
from repository.util.LinkedMap import LinkedMap
from repository.item.Indexes import NumericIndex, AttributeIndex, CompareIndex

class ItemRef(object):
    'A wrapper around a bi-directional link between two items.'
    
    def __init__(self, item, name, other, otherName,
                 otherCard=None, otherPersist=None, otherAlias=None,
                 setDirty=True):

        super(ItemRef, self).__init__()
        self.attach(item, name, other, otherName,
                    otherCard, otherPersist, otherAlias, setDirty)

    def _copy(self, references, item, copyItem, name, policy, copyFn):

        copyOther = copyFn(copyItem, self.other(item), policy)

        if copyOther is not None and name not in references:
            references[name] = ItemRef(copyItem, name, copyOther,
                                       copyItem._kind.getOtherName(name))

    def __repr__(self):

        return '<ItemRef: %s - %s>' %(self._item, self._other)

    def _clearDirties(self):
        pass

    def _setItem(self, item):
        pass

    def _isRefDict(self):
        return False
    
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
               otherCard=None, otherPersist=None, otherAlias=None,
               setDirty=True):

        assert item is not None, 'item is None'
        assert other is not None, 'other is None'

        self._item = item
        self._other = other

        if not isinstance(other, Stub):
            if other.hasAttributeValue(otherName):
                old = other.getAttributeValue(otherName)
                if isinstance(old, RefDict):
                    try:
                        sd = old._setFlag(old.SETDIRTY, setDirty)
                        old.__setitem__(item._uuid, self, alias=otherAlias)
                    finally:
                        old._setFlag(old.SETDIRTY, sd)
                    return
            else:
                if otherCard is None:
                    otherCard = other.getAttributeAspect(otherName,
                                                         'cardinality',
                                                         default='single')
                if otherCard != 'single':
                    old = other._refDict(otherName, name, otherPersist)
                    other._references[otherName] = old
                    try:
                        sd = old._setFlag(old.SETDIRTY, setDirty)
                        old.__setitem__(item._uuid, self, alias=otherAlias)
                    finally:
                        old._setFlag(old.SETDIRTY, sd)
                    return
            
            other.setAttributeValue(otherName, self,
                                    _attrDict=other._references,
                                    setDirty=setDirty)

    def detach(self, item, name, other, otherName):

        _attrDict = other._references
        old = other.getAttributeValue(otherName, _attrDict=_attrDict)
        
        if isinstance(old, RefDict):
            old._removeRef(item._uuid)
            other.setDirty(item.RDIRTY, otherName, _attrDict, True)
        else:
            other._removeRef(otherName)
            other.setDirty(item.VDIRTY, otherName, _attrDict, True)

    def reattach(self, item, name, old, new, otherName, setDirty=True):

        if old is not new:
            self.detach(item, name, old, otherName)
            self.attach(item, name, new, otherName)
            if setDirty:
                item.setDirty(item.VDIRTY, name, item._references)

    def _unload(self, item):

        # using direct compares instead of accessors to avoid re-loading
        
        if item is self._item:
            if self._other._isItem():
                self._item = UUIDStub(self._other, item._uuid)
        elif item is self._other:
            if self._item._isItem():
                self._other = UUIDStub(self._item, item._uuid)
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

        logger = item.itsView.logger
        
        try:
            other = self.other(item)
        except DanglingRefError, e:
            logger.error('DanglingRefError: %s', e)
            return False
        except ValueError, e:
            logger.error('ValueError: %s', e)
            return False
        else:
            if other.isStale():
                logger.error('Found stale item %s at %s of kind %s',
                             other, other.itsPath,
                             other._kind.itsPath)
                return False
            else:
                otherName = item._kind.getOtherName(name, default=None)
                if otherName is None:
                    logger.error('otherName is None for attribute %s.%s',
                                 item._kind.itsPath, name)
                    return False
                otherOtherName = other._kind.getOtherName(otherName,
                                                          default=None)
                if otherOtherName != name:
                    logger.error("otherName for attribute %s.%s, %s, does not match otherName for attribute %s.%s, %s",
                                 item._kind.itsPath, name, otherName,
                                 other._kind.itsPath, otherName,
                                 otherOtherName)
                    return False

        return True

    def _refCount(self):

        return 1

    def _xmlValue(self, name, item, generator, withSchema, version, attrs,
                  mode, previous=None, next=None, alias=None):

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
        attrs['type'] = 'uuid'

        addAttr(attrs, 'name', name)
        addAttr(attrs, 'previous', previous)
        addAttr(attrs, 'next', next)
        addAttr(attrs, 'alias', alias)

        if withSchema:
            otherName = item._kind.getOtherName(name)
            otherCard = other.getAttributeAspect(otherName, 'cardinality',
                                                 default='single')
            attrs['otherName'] = otherName
            if otherCard != 'single':
                attrs['otherCard'] = otherCard

        generator.startElement('ref', attrs)
        generator.characters(other._uuid.str64())
        generator.endElement('ref')


class _noneRef(ItemRef):

    def __init__(self):
        super(_noneRef, self).__init__(None, None, None, None)

    def __repr__(self):
        return '<NoneRef>'

    def _copy(self, references, item, copyItem, name, policy, copyFn):
        return self

    def attach(self, item, name, other, otherName,
               otherCard=None, otherPersist=None, otherAlias=None,
               setDirty=True):
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
        return True

    def _refCount(self):
        return 0

    def _xmlValue(self, name, item, generator, withSchema, version, attrs,
                  mode, previous=None, next=None, alias=None):

        attrs['name'] = name
        attrs['type'] = 'none'

        generator.startElement('ref', attrs)
        generator.endElement('ref')

    def __new__(cls, *args, **kwds):

        try:
            return _noneRef._noneRef
        except AttributeError:
            _noneRef._noneRef = ItemRef.__new__(cls, *args, **kwds)
            return _noneRef._noneRef

    def __nonzero__(self):
        return False
    
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

    def _isItem(self):

        return False


class UUIDStub(Stub):

    def __init__(self, item, uuid):

        super(UUIDStub, self).__init__()

        self.item = item
        self.uuid = uuid

    def __repr__(self):

        return '<UUIDStub: %s>' %(self.uuid)

    def _loadItem(self):

        other = self.item.find(self.uuid)
        if other is None:
            raise DanglingRefError, '%s <-> %s' %(self.item, self.uuid)

        return other
    
    def _isItem(self):

        return False
    

class RefArgs(object):
    'A wrapper around arguments necessary to make and store an ItemRef'
    
    def __init__(self, attrName, refName, spec, otherName, otherCard,
                 valueDict, previous=None, next=None,
                 alias=None, otherAlias=None):

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
        self.otherAlias = otherAlias
        self.ref = None
        
    def attach(self, item, repository):

        if isinstance(self.spec, UUID):
            other = repository.find(self.spec, load=False)
        else:
            other = item.find(self.spec, load=False)

        if self.refName is None:
            if other is None:
                raise ValueError, "refName to %s is unspecified, %s should be loaded before %s" %(self.spec, self.spec, item.itsPath)
            else:
                self.refName = other._uuid

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
                               otherCard = self.otherCard,
                               otherAlias = self.otherAlias,
                               setDirty=False)
            repository._addStub(self.ref)

            vd = self.valueDict
            if vd._isRefDict():
                try:
                    setDirty = vd._setFlag(RefDict.SETDIRTY, False)
                    vd.__setitem__(self.refName, self.ref, 
                                   self.previous, self.next,
                                   self.alias, False)
                finally:
                    vd._setFlag(RefDict.SETDIRTY, setDirty)
            else:
                vd[self.refName] = self.ref

        return None

    def _attach(self, item, other):
        
        value = other._references.get(self.otherName)

        def setDict(vd):
            if vd._isRefDict():
                try:
                    sd = vd._setFlag(RefDict.SETDIRTY, False)
                    vd.__setitem__(self.refName, value,
                                   self.previous, self.next,
                                   self.alias, False)
                finally:
                    vd._setFlag(RefDict.SETDIRTY, sd)
            else:
                vd[self.refName] = value
        
        if value is None or value is NoneRef:
            if self.ref is not None:
                self.ref.attach(item, self.attrName,
                                other, self.otherName,
                                otherCard=self.otherCard,
                                otherAlias=self.otherAlias,
                                setDirty=False)
            else:
                value = ItemRef(item, self.attrName,
                                other, self.otherName,
                                otherCard=self.otherCard,
                                otherAlias=self.otherAlias,
                                setDirty=False)
                setDict(self.valueDict)

        elif isinstance(value, ItemRef):
            if isinstance(value._other, Stub):
                value._other = item
                setDict(self.valueDict)

            elif isinstance(value._item, Stub):
                value._item = item
                setDict(self.valueDict)

            else:
                return value

        elif isinstance(value, RefDict):
            otherRefName = item._uuid
            if value.has_key(otherRefName):
                value = value._getRef(otherRefName)
                if isinstance(value._other, Stub):
                    value._other = item
                    setDict(self.valueDict)

                elif isinstance(value._item, Stub):
                    value._item = item
                    setDict(self.valueDict)

                else:
                    return value

            else:
                if self.ref is not None:
                    self.ref.attach(item, self.attrName,
                                    other, self.otherName,
                                    otherCard=self.otherCard,
                                    otherAlias=self.otherAlias,
                                    setDirty=False)
                else:
                    value = ItemRef(item, self.attrName,
                                    other, self.otherName,
                                    otherCard=self.otherCard,
                                    otherAlias=self.otherAlias,
                                    setDirty=False)
                    setDict(self.valueDict)

        else:
            raise ValueError, value

        return None


class RefDict(LinkedMap):
    """
    This class implements a collection of bi-directional item references, a
    ref collection. A ref collection is a double-linked list mapping UUIDs
    to item references with predictable order. In addition to the UUID-based
    keys used by the implementation, an optional second set of keys, called
    aliases, can be used to name and access the references contained by a
    ref collection. A ref collection can be iterated over its referenced
    items.
    """
    
    def __init__(self, item, name, otherName, readOnly=False):
        """
        The constructor for this class. A RefDict should not be instantiated
        directly but created through the item and attribute it is going to
        be used with instead, as for example with: C{item.name = []}.
        """
        
        self._name = name
        self._otherName = otherName
        self._item = None
        if item is not None:
            self._setItem(item)
        self._indexes = None

        self._flags = RefDict.SETDIRTY
        if readOnly:
            self._flags |= RefDict.READONLY
        
        super(RefDict, self).__init__()

    def _isRefDict(self):

        return True
    
    def _setFlag(self, flag, on):

        old = self._flags & flag != 0
        if on:
            self._flags |= flag
        else:
            self._flags &= ~flag

        return old

    def _getFlag(self, flag):

        return self._flags & flag != 0

    def _setDirty(self, noMonitors=False):

        if self._getFlag(RefDict.SETDIRTY):
            item = self._item
            item.setDirty(item.RDIRTY, self._name, item._references, noMonitors)

    def _copy(self, references, item, copyItem, name, policy, copyFn):

        try:
            refDict = references[name]
        except KeyError:
            refDict = copyItem._refDict(name)
            references[name] = refDict

        for key in self.iterkeys():
            link = self._get(key)
            copyOther = copyFn(copyItem, link._value.other(item), policy)
            if copyOther is not None and copyOther not in refDict:
                refDict.append(copyOther, link._alias)

        return refDict

    def _makeLink(self, value):

        return RefDict.link(value)

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise AssertionError, 'Item is already set'
        
        self._item = item

    def _getItem(self):

        return self._item

    def _getRepository(self):

        return self._item.itsView

    def _isTransient(self):

        return False

    def __repr__(self):

        return '<%s: %s.%s.%s>' %(type(self).__name__,
                                  self._getItem().itsPath,
                                  self._name, self._otherName)

    def __contains__(self, obj):
        """
        The C{in} operator works both with C{Item} values or C{UUID} keys.

        To verify if there is a value for an alias, use the
        L{resolveAlias} method instead.

        @param obj: the item or uuid sought
        @type obj: an C{Item} instance, C{UUID} instance or C{None}
        @return: C{False} if C{obj} is C{None} or is not this collection,
        C{True} otherwise.
        """

        if obj is None:
            return False
        
        load = not self._item.isNew()
        if isinstance(obj, ItemPackage.Item.Item):
            return self.has_key(obj._uuid, load)

        return self.has_key(obj, load)

    def addIndex(self, indexName, indexType, **kwds):
        """
        Add an index to this ref collection.

        A ref collection index provides positional access into the
        collection and maintains a key order which is be determined by the
        sequence of collection mutation operations or by constraints
        on values.

        A ref collection may have any number of indexes. Each index has a
        name which is used with the L{placeItem}, L{getByIndex},
        L{getIndexEntryValue}, L{setIndexEntryValue}, L{resolveIndex},
        L{first}, L{last}, L{next}, L{previous} methods.

        Because the implementation of an index depends on the persistence
        layer, the type of index is chosen with the C{indexType} parameter
        which can have one of the following values:

            - C{numeric}: a simple index reflecting the sequence of mutation
              operations.

            - C{attribute}: an index sorted on the value of an attribute
              of items in the collection. The name of the attribute is
              provided via the C{attribute} keyword.

            - C{compare}: an index sorted on the return value of a method
              invoked on items in the collection. The method is a comparison
              method whose name is provided with the C{compare} keyword, and
              it is invoked on C{i0}, with the other item being compared,
              C{i1}, and is expected to return a positive number if, in the
              context of this index, C{i0 > i1}, a negative number if C{i0 <
              i1}, or zero if C{i0 == i1}.

        @param indexName: the name of the index
        @type indexName: a string
        @param indexType: the type of index
        @type indexType: a string
        """

        if self._indexes is not None:
            if indexName in self._indexes:
                raise IndexAlreadyExists, (self, indexName)
        else:
            self._indexes = {}

        index = self._createIndex(indexType, **kwds)
        self._indexes[indexName] = index

        if not self._getRepository().isLoading():
            self.fillIndex(index)
            self._setDirty(noMonitors=True)

            if indexType == 'attribute':
                from repository.item.Monitors import Monitors
                Monitors.attach(self._item, '_reIndex',
                                'set', kwds['attribute'], self._name, indexName)

    def _createIndex(self, indexType, **kwds):

        if indexType == 'numeric':
            return NumericIndex(**kwds)

        if indexType == 'attribute':
            return AttributeIndex(self, self._createIndex('numeric', **kwds),
                                  **kwds)

        if indexType == 'compare':
            return CompareIndex(self, self._createIndex('numeric', **kwds),
                                **kwds)

        raise NotImplementedError, "indexType: %s" %(indexType)

    def removeIndex(self, indexName):

        if self._indexes is None or indexName not in self._indexes:
            raise NoSuchIndexError, (self, indexName)

        del self._indexes[indexName]
        self._setDirty(noMonitors=True)

    def fillIndex(self, index):

        for key in self.iterkeys():
            link = self._get(key)
            index.insertKey(key, link._previousKey)

    def _restoreIndexes(self):

        for index in self._indexes.itervalues():
            if index.isPersistent():
                index._restore(self._item._version)
            else:
                self.fillIndex(index)

    def extend(self, valueList):
        """
        As with regular python lists, this method appends all items in the
        list to this ref collection.
        """
        
        try:
            sd = self._setFlag(RefDict.SETDIRTY, False)
            for value in valueList:
                self.append(value, None)
        finally:
            self._setFlag(RefDict.SETDIRTY, sd)

        self._setDirty()

    def update(self, dictionary, setAliases=False):
        """
        As with regular python dictionary, this method appends all items in
        the dictionary to this ref collection.

        @param setAliases: if C{True}, the keys in the dictionary are used
        as aliases for the references added to this ref collection. The keys
        should be strings.
        @type setAliases: boolean
        """

        try:
            sd = self._setFlag(RefDict.SETDIRTY, False)
            if setAliases:
                for alias, value in dictionary.iteritems():
                    self.append(value, alias)
            else:
                for value in dictionary.itervalues():
                    self.append(value, None)
        finally:
            self._setFlag(RefDict.SETDIRTY, sd)

        self._setDirty()

    def append(self, item, alias=None):
        """
        Append an item to this ref collection.

        @param alias: if this optional argument is specified it becomes an
        alias with which the item can be looked up using the L{getByAlias}
        or L{resolveAlias} methods.
        @type alias: a string
        """

        self.__setitem__(item._uuid, item, alias=alias)

    def clear(self):
        """
        Remove all references from this ref collection.
        """

        try:
            sd = self._setFlag(RefDict.SETDIRTY, False)
            key = self.firstKey()
            while key is not None:
                del self[key]
                key = self.firstKey()
        finally:
            self._setFlag(RefDict.SETDIRTY, sd)

        self._setDirty()
            
    def dir(self):
        """
        Debugging: print all items referenced in this ref collection.
        """

        for item in self:
            print item

    def __getitem__(self, key):

        return self._getRef(key).other(self._getItem())

    def __setitem__(self, key, value,
                    previousKey=None, nextKey=None, alias=None,
                    load=True):

        loading = self._getRepository().isLoading()
        
        old = super(RefDict, self).get(key, None, load)
        if not loading:
            if old is not None:
                self.linkChanged(self._get(key), key)
            else:
                self._setDirty()

        if old is not None:
            item = self._getItem()
            if type(value) is ItemRef:
                if value is not old:
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
                return None   # no value was set, only reattached

        if type(value) is not ItemRef:
            value = ItemRef(self._getItem(), self._name,
                            value, self._otherName)

        link = super(RefDict, self).__setitem__(key, value,
                                                previousKey, nextKey, alias)

        if not loading:
            if self._indexes:
                for index in self._indexes.itervalues():
                    index.insertKey(key, link._previousKey)

        return value

    def placeItem(self, item, after, indexName=None):
        """
        Place an item in this collection after another one.

        Both items must already belong to the collection. To place an item
        first, pass C{None} for C{after}.

        @param item: the item to place, must belong to the collection.
        @type item: an C{Item} instance
        @param after: the item to place C{item} after or C{None} if C{item} is
        to be first in this ref collection.
        @type after: an C{Item} instance
        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        """
        
        key = item._uuid
        if after is not None:
            afterKey = after._uuid
        else:
            afterKey = None

        if indexName is None:
            super(RefDict, self).place(key, afterKey)
        else:
            self._index(indexName).moveKey(key, afterKey)
            self._setDirty()

    def remove(self, item):
        """
        Remove a referenced item from this reference collection.

        @param item: the item whose reference to remove.
        @type item: an C{Item} instance
        """
        
        del self[item._uuid]
            
    def __delitem__(self, key):

        self._removeRef(key, True)

    def _removeRef(self, key, _detach=False):

        if self._flags & RefDict.READONLY:
            raise AttributeError, 'Value for %s on %s is read-only' %(self._name, self._item.itsPath)

        if self._indexes:
            for index in self._indexes.itervalues():
                index.removeKey(key)

        if _detach:
            value = self._getRef(key)
            value.detach(self._item, self._name,
                         value.other(self._item), self._otherName)

        return super(RefDict, self).__delitem__(key)

    def _load(self, key):

        repository = self._item.itsView
        loading = None
        
        try:
            loading = repository._setLoading()
            ref = self._loadRef(key)
            if ref is not None:
                args = RefArgs(self._name, key, key,
                               self._otherName, None, self,
                               ref[0], ref[1], ref[2])
                value = args.attach(self._item, repository)
                if value is not None:
                    self.__setitem__(args.refName, value, args.previous,
                                     args.next, args.alias, False)
                    
                return True
        finally:
            if loading is not None:
                repository._setLoading(loading)

        return False

    def _unload(self, item):

        for link in self._itervalues():
            link._value._unload(item)

    def linkChanged(self, link, key):

        if self._flags & RefDict.READONLY:
            raise AttributeError, 'Value for %s on %s is read-only' %(self._name, self._item.itsPath)

        if key is not None:
            self._setDirty(noMonitors=True)

    def _getRef(self, key, load=True):

        load = load and not self._item.isNew()
        return super(RefDict, self).__getitem__(key, load)

    def get(self, key, default=None, load=True):
        """
        Get the item referenced at C{key}.

        To get an item through its alias, use L{getByAlias} instead.

        @param key: the UUID of the item referenced.
        @type key: L{UUID<repository.util.UUID.UUID>}
        @param default: the default value to return if there is no reference
        for C{key} in this ref collection, C{None} by default.
        @type default: anything
        @param load: if the reference exists but hasn't been loaded yet,
        this method will return C{default} if this parameter is C{False}.
        @type load: boolean
        @return: an C{Item} instance or C{default}
        """

        load = load and not self._item.isNew()
        value = super(RefDict, self).get(key, default, load)
        if value is not default:
            return value.other(self._item)

        return default

    def getAlias(self, item):
        """
        Get the alias this item is keyed on in this collection.

        @param item: an item in the collection
        @type item: an L{Item<repository.item.Item.Item>} instance
        @return: the alias string or None if the item is not aliased
        """

        return self._get(item._uuid)._alias

    def getByIndex(self, indexName, position):
        """
        Get the item through its position in an index.

        C{position} is 0-based and may be negative to begin search from end
        going backwards with C{-1} being the index of the last element.

        C{IndexError} is raised if C{position} is out of range.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param position: the position of the item in the index
        @type position: integer
        @return: an C{Item} instance
        """

        return self[self._index(indexName).getKey(position)]

    def resolveIndex(self, indexName, position):

        return self._index(indexName).getKey(position)

    def getIndexPosition(self, indexName, item):
        """
        Return the position of an item in an index of this collection.

        Raises C{NoSuchItemError} if the item is not in this collection.

        @param indexName: the name of the index to search
        @type indexName: a string
        @param item: the item sought
        @type item: an C{Item} instance
        @return: the 0-based position of the item in the index.
        """

        if item in self:
            return self._index(indexName).getPosition(item._uuid)
        else:
            raise NoSuchItemError, (self, item)

    def getIndexEntryValue(self, indexName, item):
        """
        Get an index entry value.

        Each entry in a index may store one integer value. This value is
        initialized to zero.

        @param indexName: the name of the index
        @type indexName: a string
        @param item: the item's whose index entry is to be set
        @type item: an L{Item<repository.item.Item.Item>} instance
        @return: the index entry value
        """
        
        return self._index(indexName).getEntryValue(item._uuid)

    def setIndexEntryValue(self, indexName, item, value):
        """
        Set an index entry value.

        Each index entry may store one integer value.

        @param indexName: the name of the index
        @type indexName: a string
        @param item: the item whose index entry is to be set
        @type item: an L{Item<repository.item.Item.Item>} instance
        @param value: the value to set
        @type value: int
        """

        self._index(indexName).setEntryValue(item._uuid, value)
        self._setDirty()

    def _refCount(self):

        return len(self)

    def _xmlValue(self, name, item, generator, withSchema, version, attrs,
                  mode):

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

        attrs['name'] = name
        
        if withSchema:
            attrs['cardinality'] = 'list'
            attrs['otherName'] = item._kind.getOtherName(name)

        generator.startElement('ref', attrs)
        self._xmlValues(generator, version, mode)
        generator.endElement('ref')

    def _xmlValues(self, generator, version, mode):

        for key in self.iterkeys():
            link = self._get(key)
            link._value._xmlValue(key, self._item,
                                  generator, False, version, {}, mode,
                                  previous=link._previousKey,
                                  next=link._nextKey,
                                  alias=link._alias)
        if self._indexes:
            for name, index in self._indexes.iteritems():
                attrs = { 'name': name, 'type': index.getIndexType() }
                index._xmlValues(generator, version, attrs, mode)

    def copy(self):
        """
        This method is not directly supported on this class.

        To copy a ref collection into another one, call L{extend} with this
        collection on the target collection.
        """
        
        raise NotImplementedError, 'RefDict.copy is not supported'

    def first(self, indexName=None):
        """
        Get the first item referenced in this ref collection.

        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if empty.
        """

        if indexName is None:
            firstKey = self.firstKey()
        else:
            firstKey = self._index(indexName).getFirstKey()
            
        if firstKey is not None:
            return self[firstKey]

        return None

    def last(self, indexName=None):
        """
        Get the last item referenced in this ref collection.

        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if empty.
        """

        if indexName is None:
            lastKey = self.lastKey()
        else:
            lastKey = self._index(indexName).getLastKey()
            
        if lastKey is not None:
            return self[lastKey]

        return None

    def next(self, previous, indexName=None):
        """
        Get the next referenced item relative to previous.

        @param previous: the previous item relative to the item sought.
        @type previous: a C{Item} instance
        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if C{previous} is the last
        referenced item in the collection.
        """

        key = previous._uuid

        try:
            if indexName is None:
                nextKey = self.nextKey(key)
            else:
                nextKey = self._index(indexName).getNextKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                raise ValueError, '%s not in collection %s' %(previous, self)

        if nextKey is not None:
            return self[nextKey]

        return None

    def previous(self, next, indexName=None):
        """
        Get the previous referenced item relative to next.

        @param next: the next item relative to the item sought.
        @type next: a C{Item} instance
        @param indexName: the name of an index to use instead of the
        collection's default intrinsic order
        @type indexName: a string
        @return: an C{Item} instance or C{None} if next is the first
        referenced item in the collection.
        """

        key = next._uuid

        try:
            if indexName is None:
                previousKey = self.previousKey(key)
            else:
                previousKey = self._index(indexName).getPreviousKey(key)
        except KeyError:
            if key in self:
                raise
            else:
                raise ValueError, '%s not in collection %s' %(next, self)

        if previousKey is not None:
            return self[previousKey]

        return None

    def iterkeys(self, indexName=None):

        if indexName is None:
            for key in super(RefDict, self).iterkeys():
                yield key

        else:
            index = self._index(indexName)
            nextKey = index.getFirstKey()
            while nextKey is not None:
                key = nextKey
                nextKey = index.getNextKey(nextKey)
                yield key

    def itervalues(self, indexName=None):

        if indexName is None:
            for value in super(RefDict, self).itervalues():
                yield value

        else:
            for key in self.iterkeys(indexName):
                yield self[key]

    def iteritems(self, indexName=None):

        for key in self.iterkeys(indexName):
            yield (key, self[key])

    def setDescending(self, indexName, descending=True):

        self._index(indexName).setDescending(descending)
        self._setDirty(noMonitors=True)

    def _index(self, indexName):

        if self._indexes is None:
            raise NoSuchIndexError, (self, indexName)

        try:
            return self._indexes[indexName]
        except KeyError:
            raise NoSuchIndexError, (self, indexName)

    def check(self, item, name):
        """
        Debugging: verify this ref collection for consistency.

        Consistency errors are logged.

        @return: C{True} if no errors were found, {False} otherwise.
        """

        l = len(self)
        logger = self._getRepository().logger
        
        key = self.firstKey()
        while key:
            try:
                other = self[key]
            except DanglingRefError, e:
                logger.error('DanglingRefError on %s.%s: %s',
                             self._item.itsPath, self._name, e)
                return False
            except KeyError, e:
                logger.error('KeyError on %s.%s: %s',
                             self._item.itsPath, self._name, e)
                return False
            else:
                if other.isStale():
                    logger.error('Found stale item %s at %s of kind %s',
                                 other, other.itsPath,
                                 other._kind.itsPath)
                    return False
                else:
                    name = other.getAttributeAspect(self._otherName,
                                                    'otherName', default=None)
                    if name != self._name:
                        logger.error("OtherName for attribute %s.%s, %s, does not match otherName for attribute %s.%s, %s",
                                     other._kind.itsPath,
                                     self._otherName, name,
                                     self._item._kind.itsPath,
                                     self._name, self._otherName)
                        return False
                        
            l -= 1
            key = self.nextKey(key)
            
        if l != 0:
            logger.error("Iterator on %s.%s doesn't match length (%d left for %d total)",
                         self._item.itsPath, self._name, l, len(self))
            return False

        return True

    def _clearDirties(self):
        pass

    SETDIRTY = 0x0001
    READONLY = 0x0002


class TransientRefDict(RefDict):
    """
    A ref collection class for transient attributes.
    """

    def linkChanged(self, link, key):
        pass
    
    def check(self, item, name):
        return True

    def _load(self, key):
        return False
    
    def _isTransient(self):
        return True


class DanglingRefError(ValueError):
    pass

class IndexError:

    def getCollection(self):
        return self.args[0]

    def getIndexName(self):
        return self.args[1]

    def __str__(self):
        return self.__doc__ %(self.getIndexName(), self.getCollection())
    
class NoSuchIndexError(IndexError, KeyError):
    "No index named '%s' on %s"

class IndexAlreadyExists(IndexError, KeyError):
    "An index named '%s' already exists on %s"

class NoSuchItemError(IndexError, ValueError):
    "No item %s in %s"
