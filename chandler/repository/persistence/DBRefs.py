
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from cStringIO import StringIO

from repository.item.Children import Children
from repository.item.RefCollections import RefList
from repository.item.Indexes import NumericIndex
from repository.persistence.RepositoryError import MergeError
from chandlerdb.util.uuid import UUID
from repository.util.LinkedMap import LinkedMap


class PersistentRefs(object):

    class link(LinkedMap.link):

        __slots__ = ()

        def getValue(self, linkedMap):

            value = self._value
            if value is not None and value._isUUID():
                self._value = value = linkedMap.view[value]

            return value

    def __init__(self, view):

        super(PersistentRefs, self).__init__()

        self.view = view
        self._changedRefs = {}
        self._key = None
        self._value = None
        self._count = 0
        
    def __len__(self):

        return self._count

    def _getRefs(self):

        return self.view.repository.store._refs

    def _copy_(self, orig):

        self._changedRefs.clear()
        if isinstance(orig, PersistentRefs):
            self._changedRefs.update(orig._changedRefs)
        self._count = len(orig)

    def _setItem(self, item):

        if self._key is None:
            self._key = self._getRefs().prepareKey(item.itsUUID, self.uuid)
            self._value = StringIO()

        ref = self._getRefs().loadRef(self._key, self._item._version,
                                      self.uuid)
        if ref is not None:
            self._firstKey, self._lastKey, self._count = ref

    def _changeRef(self, key, link):

        if key is not None and not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (1, link._alias))
            if op != 0:
                # changed element: key, maybe old alias: alias
                self._changedRefs[key] = (0, alias)

    def _unloadRef(self, item):

        key = item._uuid

        if self.has_key(key, load=False):
            link = self._get(key, load=False)
            if link is not None:
                if link._alias is not None:
                    del self._aliases[link._alias]
                op, alias = self._changedRefs.get(key, (-1, link._alias))
                if op == 0:
                    link.setValue(self, key)
                else:
                    self._remove(key)                   
            else:
                raise AssertionError, '%s: unloading non-loaded ref %s' %(self, item._repr_())

    def _removeRef(self, key, link):

        if not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (0, link._alias))
            if op != 1:
                # deleted element: key, maybe old alias: alias
                self._changedRefs[key] = (1, alias)
            self._count -= 1
        else:
            raise ValueError, '_removeRef during load'

    def _isRemoved(self, key):

        try:
            return self._changedRefs[key][0] == 1
        except KeyError:
            return False

    def _loadRef(self, key):

        if self._isRemoved(key):
            return None
        
        return self._getRefs().loadRef(self._key, self._item._version, key)

    def _writeRef(self, key, version, previous, next, alias):

        if key is None:
            raise ValueError, 'key is None'

        store = self.view.repository.store
        return store._refs.saveRef(store.txn, self._key.getvalue(), version,
                                   key, previous, next, alias)

    def _deleteRef(self, key, version):

        return self._getRefs().deleteRef(self._key, self._value, version, key)

    def resolveAlias(self, alias, load=True):

        key = None
        if load:
            view = self.view
            key = view.repository.store.readName(view._version,
                                                 self.uuid, alias)
            if key is not None:
                op, oldAlias = self._changedRefs.get(key, (0, None))
                if oldAlias == alias:
                    key = None

        return key

    def _clearDirties(self):

        self._changedRefs.clear()

    def _mergeChanges(self, oldVersion, toVersion):

        moves = {}

        def merge(version, (collection, item), ref):
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
                        if link._alias != alias:
                            if oldAlias is not None:
                                self._e_1_renames(oldAlias, link._alias, alias)
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

        self._getRefs().applyHistory(merge, self.uuid, oldVersion, toVersion)

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
        RefList.__init__(self, item, name, otherName, readOnly, new)

    def _makeLink(self, value):

        return PersistentRefs.link(value)

    def _getView(self):

        return self.view

    def __len__(self):

        return PersistentRefs.__len__(self)

    def resolveAlias(self, alias, load=True):

        key = RefList.resolveAlias(self, alias, load)
        if key is None and not self._flags & LinkedMap.NEW:
            key = PersistentRefs.resolveAlias(self, alias, load)

        return key
            
    def linkChanged(self, link, key):

        super(DBRefList, self).linkChanged(link, key)
        self._changeRef(key, link)
        
    def _removeRef(self, other):

        link = RefList._removeRef(self, other)
        PersistentRefs._removeRef(self, other._uuid, link)

    def _setItem(self, item):

        RefList._setItem(self, item)
        PersistentRefs._setItem(self, item)

    def _setRef(self, other, **kwds):

        loading = self.view.isLoading()
        super(DBRefList, self)._setRef(other, **kwds)

        if not loading:
            self._count += 1

    def _setFuture(self, key, alias):
        
        super(RefList, self).__setitem__(key, key, alias=alias)
        self._count += 1
    
    def _saveValues(self, version):

        store = self.view.repository.store

        item = self._item
        if not (self._flags & LinkedMap.NEW or
                item.isAttributeDirty(self._name, item._references) or
                len(self._changedRefs) == 0):
            raise AssertionError, '%s.%s not marked dirty' %(item._repr_(),
                                                             self._name)

        size = self._writeRef(self.uuid, version,
                              self._firstKey, self._lastKey, self._count)
            
        for key, (op, oldAlias) in self._changedRefs.iteritems():
            if op == 0:               # change
                link = self._get(key, load=False)

                previous = link._previousKey
                next = link._nextKey
                alias = link._alias
    
                size += self._writeRef(key, version, previous, next, alias)
                if (oldAlias is not None and
                    oldAlias != alias and
                    oldAlias not in self._aliases):
                    size += store.writeName(version, self.uuid, oldAlias, None)
                if alias is not None:
                    size += store.writeName(version, self.uuid, alias, key)
                        
            elif op == 1:             # remove
                size += self._deleteRef(key, version)
                if oldAlias is not None and oldAlias not in self._aliases:
                    size += store.writeName(version, self.uuid, oldAlias, None)

            else:                     # error
                raise ValueError, op

        return size
        
    def _clearDirties(self):

        self._flags &= ~LinkedMap.NEW

        PersistentRefs._clearDirties(self)
        if self._indexes:
            for name, index in self._indexes.iteritems():
                index._clearDirties()

    def _copy_(self, orig):

        RefList._copy_(self, orig)
        PersistentRefs._copy_(self, orig)

    def _clear_(self):

        RefList._clear_(self)
        PersistentRefs._setItem(self, self._item)

    def _mergeChanges(self, oldVersion, toVersion):

        if self._indexes is not None:
            raise MergeError, ('ref collections', self._item, 'merging ref collections with indexes is not yet implemented, overlapping attribute: %s' %(self._name), MergeError.BUG)

        target = self.view._createRefList(self._item, self._name,
                                          self._otherName, True, False, False,
                                          self.uuid)

        target._original = self

        target._copy_(self)
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
    
        self._key = self._getIndexes().prepareKey(self._uuid)
        self._value = StringIO()
        self._version = 0
        
    def _keyChanged(self, key):

        self._changedKeys[key] = self[key]

    def removeKey(self, key):

        super(DBNumericIndex, self).removeKey(key)
        self._changedKeys[key] = None

    def __getitem__(self, key):

        try:
            return super(DBNumericIndex, self).__getitem__(key)
        except KeyError:
            if self._loadKey(key):
                return super(DBNumericIndex, self).__getitem__(key)
            raise

    def __contains__(self, key):

        return self.has_key(key)

    def has_key(self, key):

        has = super(DBNumericIndex, self).has_key(key)
        if not has:
            node = self._loadKey(key)
            has = node is not None

        return has

    def get(self, key, default=None):

        node = super(DBNumericIndex, self).get(key, default)
        if node is default:
            node = self._loadKey(key)
            if node is None:
                node = default

        return node

    def isPersistent(self):

        return True

    def _restore(self, version):

        indexes = self._getIndexes()
        
        self._version = version
        head = indexes.loadKey(self, self._key, version, self._headKey)
        tail = indexes.loadKey(self, self._key, version, self._tailKey)

        if head is not None:
            self._head = head
        if tail is not None:
            self._tail = tail

    def _loadKey(self, key):

        node = None
        version = self._version

        if version > 0:
            try:
                if self._changedKeys[key] is None:   # removed key
                    return None
            except KeyError:
                pass

            node = self._getIndexes().loadKey(self, self._key, version, key)
            if node is not None:
                self[key] = node

        return node

    def _getIndexes(self):

        return self.view.repository.store._indexes

    def _writeValue(self, itemWriter, buffer, version):

        super(DBNumericIndex, self)._writeValue(itemWriter, buffer, version)

        itemWriter.writeInteger(buffer, self._count)
        itemWriter.writeUUID(buffer, self._uuid)
        itemWriter.writeUUID(buffer, self._headKey)
        itemWriter.writeUUID(buffer, self._tailKey)

    def _readValue(self, itemReader, offset, data):

        offset = super(DBNumericIndex, self)._readValue(itemReader,
                                                        offset, data)
        offset, self._count = itemReader.readInteger(offset, data)
        offset, self._uuid = itemReader.readUUID(offset, data)
        offset, self._headKey = itemReader.readUUID(offset, data)
        offset, self._tailKey = itemReader.readUUID(offset, data)

        self.__init()

        return offset

    def _saveValues(self, version):

        indexes = self._getIndexes()

        size = indexes.saveKey(self._key, self._value,
                               version, self._headKey, self._head)
        size += indexes.saveKey(self._key, self._value,
                                version, self._tailKey, self._tail)
        for key, node in self._changedKeys.iteritems():
            size += indexes.saveKey(self._key, self._value,
                                    version, key, node)

        self._version = version

        return size

    def _clearDirties(self):

        self._changedKeys.clear()
        

class DBChildren(Children, PersistentRefs):

    def __init__(self, view, item, new=True):

        self.uuid = item.itsUUID

        PersistentRefs.__init__(self, view)
        Children.__init__(self, item, new)

    def _makeLink(self, value):

        return PersistentRefs.link(value)

    def __len__(self):

        return PersistentRefs.__len__(self)

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
                        self.__setitem__(key, child, alias=child._name)
                    finally:
                        self.view._setLoading(loading, True)
                return True

        return False

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
        self._removeRef(key, link)

    def __setitem__(self, key, value,
                    previousKey=None, nextKey=None, alias=None):

        loading = self.view.isLoading()
        if loading and previousKey is None and nextKey is None:
            ref = self._loadRef(key)
            if ref is not None:
                previousKey, nextKey, refAlias = ref
                if alias is not None:
                    assert alias == refAlias

        super(DBChildren, self).__setitem__(key, value,
                                            previousKey, nextKey, alias)

        if not loading:
            self._count += 1

    def _setFuture(self, key, alias):
        
        self.__setitem__(key, None, alias=alias)
    
    def _saveValues(self, version):

        store = self.view.repository.store
        unloads = []
        
        size = self._writeRef(self.uuid, version,
                              self._firstKey, self._lastKey, self._count)
        
        for key, (op, oldAlias) in self._changedRefs.iteritems():
    
            if op == 0:               # change
                link = self._get(key, load=False)
                previous = link._previousKey
                next = link._nextKey
                alias = link._alias
                    
                size += self._writeRef(key, version, previous, next, alias)
                if (oldAlias is not None and
                    oldAlias != alias and
                    oldAlias not in self._aliases):
                    size += store.writeName(version, self.uuid, oldAlias, None)
                if alias is not None:
                    size += store.writeName(version, self.uuid, alias, key)

                if link.getValue(self) is None:
                    unloads.append((key, link._alias))

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
