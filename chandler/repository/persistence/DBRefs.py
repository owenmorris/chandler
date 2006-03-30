
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.item.c import Nil
from chandlerdb.util.c import UUID
from repository.item.Children import Children
from repository.item.RefCollections import RefList
from repository.item.Indexes import NumericIndex
from repository.persistence.RepositoryError import MergeError
from repository.util.LinkedMap import LinkedMap, CLink


class PersistentRefs(object):

    def __init__(self, view):

        super(PersistentRefs, self).__init__()

        self.view = view
        self.store = view.store
        self._changedRefs = {}
        
    def _iterrefs(self, firstKey, lastKey):

        version = self._item._version
        nextKey = firstKey or self._firstKey
        view = self.view
        refIterator = None
        map = self._dict

        while nextKey != lastKey:
            key = nextKey
            link = map.get(key, None)
            if link is None:
                if refIterator is None:
                    if version == 0:
                        raise KeyError, key
                    refs = self.store._refs
                    refIterator = refs.refIterator(view, self.uuid, version)

                pKey, nKey, alias = refIterator.next(key)
                map[key] = link = CLink(self, key, pKey, nKey, alias)
                if alias is not None:
                    self._aliases[alias] = key

            nextKey = link._nextKey
            yield key

        if lastKey is not None:
            yield lastKey

    def _iteraliases(self, firstKey, lastKey):

        version = self._item._version
        nextKey = firstKey or self._firstKey
        view = self.view
        refIterator = None
        map = self._dict

        while nextKey is not None:
            key = nextKey
            link = map.get(key, None)
            if link is None:
                if refIterator is None:
                    if version == 0:
                        raise KeyError, key
                    refs = self.store._refs
                    refIterator = refs.refIterator(view, self.uuid, version)

                pKey, nextKey, alias = refIterator.next(key)
            else:
                nextKey = link._nextKey
                alias = link.alias

            if alias is not None:
                yield alias, key

            if key == lastKey:
                break

    def _iterChanges(self):

        return self._changedRefs.iterkeys()

    def _copy_(self, orig):

        self._changedRefs.clear()
        if isinstance(orig, PersistentRefs):
            self._changedRefs.update(orig._changedRefs)
        self._count = len(orig)

    def _setItem(self, item):

        if not self._flags & self.NEW:
            ref = self.store._refs.loadRef(self.view, self.uuid,
                                           self._item.itsVersion, self.uuid)
            if ref is not None:
                self._firstKey, self._lastKey, self._count = ref

    def _changeRef(self, key, link):

        if key is not None and not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (1, link.alias))
            if op != 0:
                # changed element: key, maybe old alias: alias
                self._changedRefs[key] = (0, alias)

    def _unloadRef(self, item):

        key = item._uuid

        if self.has_key(key, False):
            link = self._get(key, False)
            if link is not None:
                if link.alias is not None:
                    del self._aliases[link.alias]
                op, alias = self._changedRefs.get(key, (-1, link.alias))
                if op == 0:
                    link.value = key
                else:
                    self._remove(key)                   
            else:
                raise AssertionError, '%s: unloading non-loaded ref %s' %(self, item._repr_())

    def _removeRef_(self, key, link):

        if not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (0, link.alias))
            if op != 1:
                # deleted element: key, maybe old alias: alias
                self._changedRefs[key] = (1, alias)
        else:
            raise ValueError, '_removeRef_ during load'

    def _isRemoved(self, key):

        change = self._changedRefs.get(key, None)
        if change is not None:
            return change[0] == 1

        return False

    def _loadRef(self, key):

        if self._isRemoved(key):
            return None
        
        return self.store._refs.loadRef(self.view, self.uuid,
                                        self._item._version, key)

    def _writeRef(self, key, version, previous, next, alias):

        if key is None:
            raise ValueError, 'key is None'

        store = self.store
        return store._refs.c.saveRef(store.txn, self.uuid._uuid, version,
                                     key._uuid, previous, next, alias)

    def _deleteRef(self, key, version):

        return self.store._refs.deleteRef(self.uuid, version, key)

    def resolveAlias(self, alias, load=True):

        key = None
        if load:
            view = self.view
            key = self.store.readName(view, view.itsVersion, self.uuid, alias)
            if key is not None:
                op, oldAlias = self._changedRefs.get(key, (0, None))
                if oldAlias == alias:
                    key = None

        return key

    def _clearDirties(self):

        self._changedRefs.clear()

    def _check_(self):

        l = len(self)
        key = self.firstKey()

        while key:
            l -= 1
            link = self._get(key)
            key = link._nextKey
            
        if l != 0:
            return 1

        return 0

    def _mergeChanges(self, oldVersion, toVersion):

        moves = {}

        for (version, (collection, item),
             ref) in self.store._refs.iterHistory(self.view, self.uuid,
                                                  oldVersion, toVersion):

            if collection == self.uuid:     # the collection

                if item == self.uuid:       # the list head
                    pass

                elif ref is None:           # removed item
                    op, oldAlias = self._changedRefs.get(item, (-1, None))
                    if item in self:
                        del self[item]

                else:
                    previousKey, nextKey, alias = ref
                    op, oldAlias = self._changedRefs.get(item, (0, None))

                    if op == 1:
                        self._e_2_remove(item)

                    try:
                        link = self._get(item)
                        if link.alias != alias:
                            if oldAlias is not None:
                                self._e_1_renames(oldAlias, link.alias, alias)
                            else:
                                if alias is not None:
                                    key = self.resolveAlias(alias)
                                    if key is not None:
                                        self._e_2_renames(key, alias, item)
                                self.setAlias(item, alias)

                    except KeyError:
                        if alias is not None:
                            key = self.resolveAlias(alias)
                            if key is not None:
                                self._e_names(item, key, alias)
                        self._setFuture(item, alias)

                    if previousKey is None or self.has_key(previousKey):
                        self.place(item, previousKey)
                    else:
                        moves[previousKey] = item

        for previousKey, item in moves.iteritems():
            self.place(item, previousKey)

    def _e_1_remove(self, *args):
        raise MergeError, (type(self).__name__, self._item, 'modified element %s was removed in other view' %(args), MergeError.MOVE)

    def _e_2_remove(self, *args):
        raise MergeError, (type(self).__name__, self._item, 'removed element %s was modified in other view' %(args), MergeError.MOVE)

    def _e_1_renames(self, *args):
        raise MergeError, (type(self).__name__, self._item, 'element %s renamed to %s and %s' %(args), MergeError.RENAME)

    def _e_2_renames(self, *args):
        raise MergeError, (type(self).__name__, self._item, 'element %s named %s conflicts with element %s of same name' %(args), MergeError.NAME)

    def _e_names(self, *args):
        raise MergeError, (type(self).__name__, self._item, 'element %s conflicts with other element %s, both are named %s' %(args), MergeError.NAME)


class DBRefList(RefList, PersistentRefs):

    def __init__(self, view, item, name, otherName, readOnly, new, uuid):

        self.uuid = uuid or UUID()

        PersistentRefs.__init__(self, view)
        RefList.__init__(self, item, name, otherName, readOnly,
                         (new and LinkedMap.NEW or 0) | LinkedMap.LOAD)

    def iterkeys(self, firstKey=None, lastKey=None):

        return self._iterrefs(firstKey, lastKey)

    def iteraliases(self, firstKey=None, lastKey=None):

        return self._iteraliases(firstKey, lastKey)

    def iterChanges(self):

        return self._iterChanges()

    def _getView(self):

        return self.view

    def resolveAlias(self, alias, load=True):

        key = RefList.resolveAlias(self, alias, load)
        if key is None and load and not self._flags & LinkedMap.NEW:
            key = PersistentRefs.resolveAlias(self, alias, load)

        return key
            
    def linkChanged(self, link, key):

        self._changeRef(key, link)
        
    def _removeRef_(self, other):

        link = RefList._removeRef_(self, other)
        PersistentRefs._removeRef_(self, other._uuid, link)

    def _setOwner(self, item, name):

        RefList._setOwner(self, item, name)
        PersistentRefs._setItem(self, item)

    def _setFuture(self, key, alias):
        
        self[key] = CLink(self, key, None, None, alias)
    
    def _saveValues(self, version):

        store = self.store
        uuid = self.uuid
        item = self._item
        aliases = self._aliases

        if __debug__:
            if not (self._flags & LinkedMap.NEW or
                    item.isAttributeDirty(self._name, item._references) or
                    len(self._changedRefs) == 0):
                raise AssertionError, '%s.%s not marked dirty' %(item._repr_(),
                                                                 self._name)

        size = self._writeRef(uuid, version,
                              self._firstKey, self._lastKey, self._count)
            
        for key, (op, oldAlias) in self._changedRefs.iteritems():
            if op == 0:               # change
                link = self._get(key, False)

                previous = link._previousKey
                next = link._nextKey
                alias = link.alias
    
                size += self._writeRef(key, version, previous, next, alias)
                if (oldAlias is not None and
                    oldAlias != alias and
                    oldAlias not in aliases):
                    size += store.writeName(version, uuid, oldAlias, None)
                if alias is not None:
                    size += store.writeName(version, uuid, alias, key)
                        
            elif op == 1:             # remove
                size += self._deleteRef(key, version)
                if oldAlias is not None and oldAlias not in aliases:
                    size += store.writeName(version, uuid, oldAlias, None)

            else:                     # error
                raise ValueError, op

        return size
        
    def _clearDirties(self):

        self._flags &= ~LinkedMap.NEW

        PersistentRefs._clearDirties(self)
        self._clearIndexDirties()

    def _copy_(self, orig):

        RefList._copy_(self, orig)
        PersistentRefs._copy_(self, orig)

    def _clear_(self):

        RefList._clear_(self)
        PersistentRefs._setItem(self, self._item)

    def _mergeChanges(self, oldVersion, toVersion):

        target = self.view._createRefList(self._item, self._name,
                                          self._otherName, True, False, False,
                                          self.uuid)

        target._original = self
        target._copy_(self)
        target._indexes = self._indexes
        target._invalidateIndexes()

        self._item._references[self._name] = target

        try:
            sd = self._setFlag(RefList.SETDIRTY, False)
            PersistentRefs._mergeChanges(target, oldVersion, toVersion)
        finally:
            self._setFlag(RefList.SETDIRTY, sd)


class DBNumericIndex(NumericIndex):

    def __init__(self, view, **kwds):

        super(DBNumericIndex, self).__init__(**kwds)

        self.view = view
        self._changedKeys = {}

        if not kwds.get('loading', False):

            if 'uuid' in kwds:
                self._uuid = UUID(kwds['uuid'])
                self._headKey = UUID(kwds['head'])
                self._tailKey = UUID(kwds['tail'])
            else:
                self._uuid = UUID()
                self._headKey = UUID()
                self._tailKey = UUID()

            self.__init()

    def __init(self):
    
        self._key = self._uuid._uuid
        self._version = 0

    def _keyChanged(self, key):

        self._changedKeys[key] = self[key]

    def removeKey(self, key):

        super(DBNumericIndex, self).removeKey(key)
        self._changedKeys[key] = None

    def __getitem__(self, key):

        node = super(DBNumericIndex, self).get(key, Nil)
        if node is Nil:
            node = self._loadKey(key)
            if node is None:
                raise KeyError, key

        return node

    def get(self, key, default=None):

        node = super(DBNumericIndex, self).get(key, Nil)
        if node is Nil:
            node = self._loadKey(key)
            if node is None:
                node = default

        return node

    def __contains__(self, key):

        contains = super(DBNumericIndex, self).__contains__(key)
        if not contains:
            node = self._loadKey(key)
            contains = node is not None

        return contains

    def has_key(self, key):

        has = super(DBNumericIndex, self).has_key(key)
        if not has:
            node = self._loadKey(key)
            has = node is not None

        return has

    def isPersistent(self):

        return True

    def _restore(self, version):

        indexes = self.view.store._indexes
        
        view = self.view
        self._version = version
        head = indexes.loadKey(view, self._key, version, self._headKey)
        tail = indexes.loadKey(view, self._key, version, self._tailKey)

        if head is not None:
            self.skipList._head = head
        if tail is not None:
            self.skipList._tail = tail

    def _loadKey(self, key):

        if not self._valid:
            return None

        node = None
        version = self._version

        if version > 0:
            if self._changedKeys.get(key, Nil) is None:   # removed key
                return None

            view = self.view
            node = view.store._indexes.loadKey(view, self._key, version, key)
            if node is not None:
                self[key] = node

        return node

    def __iter__(self, firstKey=None, lastKey=None, backwards=False):

        version = self._version
        view = self.view

        if firstKey is None:
            if backwards:
                nextKey = self.getLastKey()
            else:
                nextKey = self.getFirstKey()
        else:
            nextKey = firstKey

        sup = super(DBNumericIndex, self)
        nodeIterator = None

        while nextKey != lastKey:
            key = nextKey
            node = sup.get(key, None)
            if node is None:
                if nodeIterator is None:
                    if version == 0:
                        raise KeyError, key
                    indexes = view.store._indexes
                    nodeIterator = indexes.nodeIterator(view, self._key,
                                                        version)
                node = nodeIterator.next(key)
                self[key] = node

            if backwards:
                nextKey = node[1].prevKey
            else:
                nextKey = node[1].nextKey
            yield key

        if lastKey is not None:
            yield lastKey

    def _writeValue(self, itemWriter, buffer, version):

        super(DBNumericIndex, self)._writeValue(itemWriter, buffer, version)

        itemWriter.writeInteger(buffer, self._count)
        itemWriter.writeIndex(buffer, self._uuid)
        itemWriter.writeUUID(buffer, self._headKey)
        itemWriter.writeUUID(buffer, self._tailKey)

    def _readValue(self, itemReader, offset, data):

        offset = super(DBNumericIndex, self)._readValue(itemReader,
                                                        offset, data)
        offset, self._count = itemReader.readInteger(offset, data)
        offset, self._uuid = itemReader.readIndex(offset, data)
        offset, self._headKey = itemReader.readUUID(offset, data)
        offset, self._tailKey = itemReader.readUUID(offset, data)

        self.__init()

        return offset

    def _saveValues(self, version):

        indexes = self.view.store._indexes

        size = indexes.saveKey(self._key, version, self._headKey,
                               self.skipList._head)
        size += indexes.saveKey(self._key, version, self._tailKey,
                                self.skipList._tail)
        for key, node in self._changedKeys.iteritems():
            size += indexes.saveKey(self._key, version, key, node)

        self._version = version

        return size

    def _clear_(self):

        super(DBNumericIndex, self)._clear_()
        self._clearDirties()

    def _clearDirties(self):

        self._changedKeys.clear()
        

class DBChildren(Children, PersistentRefs):

    def __init__(self, view, item, new=True):

        self.uuid = item.itsUUID

        PersistentRefs.__init__(self, view)
        Children.__init__(self, item,
                          (new and LinkedMap.NEW or 0) | LinkedMap.LOAD)

    def iterkeys(self, firstKey=None, lastKey=None):

        return self._iterrefs(firstKey, lastKey)

    def _setItem(self, item):

        Children._setItem(self, item)
        PersistentRefs._setItem(self, item)

    def _load(self, key):

        if self._flags & LinkedMap.NEW:
            return False

        if not self._isRemoved(key):
            child = self.view.find(key)
            if child is not None:
                if not self._contains_(key):
                    try:
                        loading = self.view._setLoading(True)
                        self._loadChild(key, child)
                    finally:
                        self.view._setLoading(loading, True)
                return True

        return False

    def _loadChild(self, key, child):

        if key not in self._dict: # setFuture() may have put it here already
            previousKey, nextKey, alias = self._loadRef(key)
            self._dict[key] = CLink(self, child, previousKey, nextKey, alias)
            if alias is not None:
                self._aliases[alias] = key
        else:
            self._dict[key]._value = child

    def resolveAlias(self, alias, load=True):

        key = Children.resolveAlias(self, alias, load)
        if key is None and not self._flags & LinkedMap.NEW:
            key = PersistentRefs.resolveAlias(self, alias, load)

        return key
            
    def linkChanged(self, link, key):

        super(DBChildren, self).linkChanged(link, key)
        self._changeRef(key, link)

    def _unloadChild(self, child):

        self._unloadRef(child)
    
    def __delitem__(self, key):

        link = super(DBChildren, self).__delitem__(key)
        self._removeRef_(key, link)

    def _append(self, child):

        loading = self.view.isLoading()
        if loading:
            self._loadChild(child.itsUUID, child)
        else:
            self[child.itsUUID] = CLink(self, child, None, None, child.itsName)

    def _setFuture(self, key, alias):
        
        self[key] = CLink(self, None, None, None, alias)
    
    def _saveValues(self, version):

        store = self.store
        unloads = []
        
        size = self._writeRef(self.uuid, version,
                              self._firstKey, self._lastKey, self._count)
        
        for key, (op, oldAlias) in self._changedRefs.iteritems():
    
            if op == 0:               # change
                link = self._get(key, False)
                previous = link._previousKey
                next = link._nextKey
                alias = link.alias
                    
                size += self._writeRef(key, version, previous, next, alias)
                if (oldAlias is not None and
                    oldAlias != alias and
                    oldAlias not in self._aliases):
                    size += store.writeName(version, self.uuid, oldAlias, None)
                if alias is not None:
                    size += store.writeName(version, self.uuid, alias, key)

                if link.value is None:
                    unloads.append((key, link.alias))

            elif op == 1:             # remove
                size += self._deleteRef(key, version)
                if oldAlias is not None and oldAlias not in self._aliases:
                    size += store.writeName(version, self.uuid, oldAlias, None)

            else:                     # error
                raise ValueError, op

        for key, alias in unloads:
            self._remove(key)
            if alias is not None:
                del self._aliases[alias]

        return size

    def _clearDirties(self):

        self._flags &= ~LinkedMap.NEW
        PersistentRefs._clearDirties(self)

    def _copy_(self, orig):

        Children._copy_(self, orig)
        PersistentRefs._copy_(self, orig)

    def _clear_(self):

        Children._clear_(self)
        PersistentRefs._setItem(self, self._item)

    def _commitMerge(self):

        try:
            del self._original
        except AttributeError:
            pass

    def _revertMerge(self):

        try:
            self._item._setChildren(self._original)
        except AttributeError:
            pass
    
    def _mergeChanges(self, oldVersion, toVersion):

        target = self.view._createChildren(self._item, False)
        target._original = self
        target._copy_(self)
        self._item._setChildren(target)

        PersistentRefs._mergeChanges(target, oldVersion, toVersion)
