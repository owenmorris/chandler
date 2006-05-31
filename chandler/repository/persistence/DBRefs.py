
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.item.c import Nil
from chandlerdb.util.c import UUID, CLink
from repository.item.Children import Children
from repository.item.RefCollections import RefList
from repository.item.Indexes import NumericIndex
from repository.persistence.RepositoryError import MergeError
from repository.util.LinkedMap import LinkedMap


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

                ref = refIterator.next(key)
                if ref is None:
                    refIterator.close()
                    raise KeyError, ('refIterator', key)
                pKey, nKey, alias = ref
                map[key] = link = CLink(self, key, pKey, nKey, alias)
                if alias is not None:
                    self._aliases[alias] = key

            nextKey = link._nextKey
            yield key

        if lastKey is not None:
            yield lastKey

        if refIterator is not None:
            refIterator.close()

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

                ref = refIterator.next(key)
                if ref is None:
                    refIterator.close()
                    raise KeyError, ('refIterator', key)
                pKey, nextKey, alias = ref
            else:
                nextKey = link._nextKey
                alias = link.alias

            if alias is not None:
                yield alias, key

            if key == lastKey:
                break

        if refIterator is not None:
            refIterator.close()

    def _iterChanges(self):

        uuid = self.uuid
        for key, (op, oldAlias) in self._changedRefs.iteritems():
            if key != uuid:
                if op == 0:
                    link = self._get(key)
                    assert oldAlias != link.alias
                    yield key, (op, link._previousKey, link._nextKey,
                                link.alias, oldAlias)
                else:
                    yield key, (op, None, None, None, None)

    def _iterHistory(self, fromVersion, toVersion):

        uuid = self.uuid
        oldAliases = {}
        for (version, (collection, key),
             ref) in self.store._refs.iterHistory(self.view, uuid,
                                                  fromVersion, toVersion):
            if key != uuid:
                if ref is None:
                    yield key, (1, None, None, None, None)
                else:
                    alias = ref[2]
                    oldAlias = oldAliases.get(key, Nil)
                    if oldAlias != alias:
                        oldAliases[key] = alias
                    yield key, (0, ref[0], ref[1], alias, oldAlias)

    def _setItem(self, item):

        if not self._flags & self.NEW:
            ref = self.store._refs.loadRef(self.view, self.uuid,
                                           self._item.itsVersion, self.uuid)
            if ref is not None:
                self._firstKey, self._lastKey, self._count = ref

    def _changeRef(self, key, link, oldAlias=Nil):

        if key is not None and not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (1, Nil))
            if op != 0:
                if oldAlias is not Nil:
                    if alias is Nil:
                        alias = oldAlias
                    elif alias == oldAlias:
                        alias = Nil
                self._changedRefs[key] = (0, alias)

    def _unloadRef(self, item):

        key = item.itsUUID

        if self.has_key(key, False):
            link = self._get(key, False)
            if link is not None:
                op, alias = self._changedRefs.get(key, (-1, link.alias))
                if op == 0:
                    link.value = key
                else:
                    self._remove(key)                   
                    if link.alias is not None:
                        del self._aliases[link.alias]
            else:
                raise AssertionError, '%s: unloading non-loaded ref %s' %(self, item._repr_())

    def _removeRef_(self, key, link):

        if not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (-1, Nil))
            if op == -1:
                if link.alias is None:
                    alias = Nil
                else:
                    alias = link.alias
                self._changedRefs[key] = (1, alias)
            elif op == 0:
                if alias is Nil and link.alias is not None:
                    alias = link.alias
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
            key = self.store._names.readName(view, view.itsVersion,
                                             self.uuid, alias)
            if key is not None:
                op, oldAlias = self._changedRefs.get(key, (0, Nil))
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

    def _applyChanges(self, changes, history):

        moves = {}
        done = set()

        def place(k, pK):
            self.place(k, pK)
            nK = changes[k][2]
            while nK in done and self.place(nK, k):
                k = nK
                nK = changes[k][2]

        for key, (op, prevKey, nextKey, alias, oldAlias) in changes.iteritems():
            if key in history:
                merge = True
                hOp, hPrevKey, hNextKey, hAlias, hOldAlias = history[key]
            else:
                merge = False

            if op == 1:
                #if key in history:
                #    self.view._e_2_move(self, key)
                if key in self:
                    self._removeRef(key)
            else:
                if alias is not None:
                    resolvedKey = self.resolveAlias(alias)
                    if resolvedKey not in (None, key):
                        self.view._e_2_name(self, resolvedKey, key, alias)

                if key in self:
                    link = self._get(key)
                    if oldAlias is not Nil:
                        if link.alias != alias:
                            if merge and hOldAlias not in (Nil, hAlias):
                                self.view._e_1_name(self, key, alias, hAlias)
                            self.setAlias(key, alias)
                elif merge is True and hOp == 1:
                    # conflict: the ref was removed, resolve in favor of history
                    continue
                else:
                    self._setRef(key, alias)
                    link = self._get(key)

                if link._previousKey != prevKey:
                    if prevKey is None or prevKey in self:
                        place(key, prevKey)
                    else:
                        moves[prevKey] = key

                done.add(key)

        for prevKey, key in moves.iteritems():
            if prevKey in self:
                place(key, prevKey)
                


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

    def _getView(self):

        return self.view

    def resolveAlias(self, alias, load=True):

        key = RefList.resolveAlias(self, alias, load)
        if key is None and load and not self._flags & LinkedMap.NEW:
            key = PersistentRefs.resolveAlias(self, alias, load)

        return key
            
    def linkChanged(self, link, key, oldAlias=Nil):

        self._changeRef(key, link, oldAlias)
        
    def _removeRef_(self, other):

        link = RefList._removeRef_(self, other)
        PersistentRefs._removeRef_(self, other.itsUUID, link)

    def _setOwner(self, item, name):

        RefList._setOwner(self, item, name)
        PersistentRefs._setItem(self, item)

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
        nilNone = (Nil, None)
            
        for key, (op, oldAlias) in self._changedRefs.iteritems():
            if op == 0:               # change
                link = self._get(key, False)

                previous = link._previousKey
                next = link._nextKey
                alias = link.alias
    
                size += self._writeRef(key, version, previous, next, alias)
                if (oldAlias not in nilNone and
                    oldAlias != alias and
                    oldAlias not in aliases):
                    size += store.writeName(version, uuid, oldAlias, None)
                if alias is not None:
                    size += store.writeName(version, uuid, alias, key)
                        
            elif op == 1:             # remove
                size += self._deleteRef(key, version)
                if oldAlias not in nilNone and oldAlias not in aliases:
                    size += store.writeName(version, uuid, oldAlias, None)

            else:                     # error
                raise ValueError, op

        return size
        
    def _clearDirties(self):

        self._flags &= ~LinkedMap.NEW

        PersistentRefs._clearDirties(self)
        self._clearIndexDirties()


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

    def _iterChanges(self):

        uuids = (self._uuid, self._headKey, self._tailKey)
        for key, node in self._changedKeys.iteritems():
            if key not in uuids:
                if node is None:
                    yield key, None
                else:
                    yield key, key

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
                        if not self._loadChild(key, child):
                            return False
                    finally:
                        self.view._setLoading(loading, True)
                return True

        return False

    def _loadChild(self, key, child):

        if not self._contains_(key):
            ref = self._loadRef(key)
            if ref is None:  # during merge it may not be there
                return False
            prevKey, nextKey, alias = ref
            self._dict[key] = CLink(self, child, prevKey, nextKey, alias)
            if alias is not None:
                self._aliases[alias] = key
        else:
            self._dict[key]._value = child

        return True

    def resolveAlias(self, alias, load=True):

        key = Children.resolveAlias(self, alias, load)
        if key is None and not self._flags & LinkedMap.NEW:
            key = PersistentRefs.resolveAlias(self, alias, load)

        return key
            
    def linkChanged(self, link, key, oldAlias=Nil):

        super(DBChildren, self).linkChanged(link, key, oldAlias)
        self._changeRef(key, link, oldAlias)

    def _unloadChild(self, child):

        self._unloadRef(child)
    
    def __delitem__(self, key):

        self._removeRef_(key)

    def _removeRef(self, key):
        
        self._removeRef_(key)

    def _removeRef_(self, key):
        
        link = super(DBChildren, self).__delitem__(key)
        PersistentRefs._removeRef_(self, key, link)

    def _setRef(self, key, alias=None):
        
        link = CLink(self, key, None, None, alias)
        self[key] = link

    def _append(self, child):

        loading = self.view.isLoading()
        if loading:
            self._loadChild(child.itsUUID, child)
        else:
            self[child.itsUUID] = CLink(self, child, None, None, child.itsName)

    def _saveValues(self, version):

        store = self.store
        unloads = []
        
        size = self._writeRef(self.uuid, version,
                              self._firstKey, self._lastKey, self._count)
        nilNone = (Nil, None)
        for key, (op, oldAlias) in self._changedRefs.iteritems():
    
            if op == 0:               # change
                link = self._get(key, False)
                previous = link._previousKey
                next = link._nextKey
                alias = link.alias
                    
                size += self._writeRef(key, version, previous, next, alias)
                if (oldAlias not in nilNone and
                    oldAlias != alias and
                    oldAlias not in self._aliases):
                    size += store.writeName(version, self.uuid, oldAlias, None)
                if alias is not None:
                    size += store.writeName(version, self.uuid, alias, key)

                if link.value is None:
                    unloads.append((key, link.alias))

            elif op == 1:             # remove
                size += self._deleteRef(key, version)
                if oldAlias not in nilNone and oldAlias not in self._aliases:
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
