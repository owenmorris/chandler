
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from cStringIO import StringIO

from repository.item.Item import Item, Children
from repository.item.ItemRef import RefDict
from repository.item.Indexes import NumericIndex
from repository.persistence.RepositoryError import MergeError
from repository.util.UUID import UUID
from repository.util.LinkedMap import LinkedMap


class PersistentRefs(object):
    
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

    def _copy_(self, target):

        target._changedRefs.clear()
        target._changedRefs.update(self._changedRefs)

    def _setItem(self, item):

        if self._key is None:
            self._key = self._getRefs().prepareKey(item.itsUUID, self.uuid)
            self._value = StringIO()

        ref = self._getRefs().loadRef(self._key, self._item._version,
                                      self.uuid)
        if ref is not None:
            self._firstKey, self._lastKey, self._count = ref

    def _changeRef(self, key, link):

        if not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (1, link._alias))
            if op != 0:
                # changed element: key, maybe old alias: alias
                self._changedRefs[key] = (0, alias)

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

        view = self.view
        if view is not view.repository.view:
            raise RepositoryError, 'current thread is not owning thread'

        if self._isRemoved(key):
            return None
        
        return self._getRefs().loadRef(self._key, self._item._version, key)

    def _writeRef(self, key, version, previous, next, alias):

        self._getRefs().saveRef(self._key, self._value, version, key,
                                previous, next, alias)

    def _deleteRef(self, key, version):

        self._getRefs().deleteRef(self._key, self._value, version, key)

    def resolveAlias(self, alias, load=True):

        load = load and not self._item.isNew()
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

        def merge(version, (collection, child), ref):
            if collection == self.uuid:     # the children collection

                if child == self.uuid:      # the list head
                    pass

                elif ref is None:           # removed child
                    op, oldAlias = self._changedRefs.get(child, (-1, None))
                    if op == 0:
                        self._e_1_remove(child)
                    elif self.has_key(child):
                        del self[child]

                else:
                    previousKey, nextKey, alias = ref
                    op, oldAlias = self._changedRefs.get(child, (0, None))

                    if op == 1:
                        self._e_2_remove(child)

                    try:
                        link = self._get(child)
                        if link._alias != alias:
                            if oldAlias is not None:
                                self._e_1_renames(oldAlias, link._alias, alias)
                            else:
                                if alias is not None:
                                    key = self.resolveAlias(alias)
                                    if key is not None:
                                        self._e_2_renames(key, alias, child)
                                self.setAlias(child, alias)

                    except KeyError:
                        if alias is not None:
                            key = self.resolveAlias(alias)
                            if key is not None:
                                self._e_names(child, key, alias)
                        link = self.__setitem__(child, None, alias=alias)

                    if previousKey is None or self.has_key(previousKey):
                        self.place(child, previousKey)
                    else:
                        moves[previousKey] = child
                        
        self._getRefs().applyHistory(merge, self.uuid, oldVersion, toVersion)

        for previousKey, child in moves.iteritems():
            self.place(child, previousKey)


class XMLRefDict(RefDict, PersistentRefs):

    def __init__(self, view, item, name, otherName, readOnly, uuid):

        self.uuid = uuid or UUID()

        PersistentRefs.__init__(self, view)
        RefDict.__init__(self, item, name, otherName, readOnly)

    def _getRepository(self):

        return self.view

    def __len__(self):

        return PersistentRefs.__len__(self)

    def resolveAlias(self, alias, load=True):

        return (RefDict.resolveAlias(self, alias, load) or
                PersistentRefs.resolveAlias(self, alias, load))
            
    def linkChanged(self, link, key):

        super(XMLRefDict, self).linkChanged(link, key)
        self._changeRef(key, link)
        
    def _removeRef(self, key, _detach=False):

        link = RefDict._removeRef(self, key, _detach)
        PersistentRefs._removeRef(self, key, link)

    def _setItem(self, item):

        RefDict._setItem(self, item)
        PersistentRefs._setItem(self, item)

    def __setitem__(self, key, value,
                    previousKey=None, nextKey=None, alias=None,
                    load=True):

        loading = self.view.isLoading()
        if loading and previousKey is None and nextKey is None:
            ref = self._loadRef(key)
            if ref is not None:
                previousKey, nextKey, refAlias = ref
                if alias is not None:
                    assert alias == refAlias

        value = super(XMLRefDict, self).__setitem__(key, value,
                                                    previousKey, nextKey, alias,
                                                    load)

        if not loading and value is not None:
            self._count += 1

    def _xmlValue(self, name, item, generator, withSchema,
                  version, attrs, mode):

        if mode == 'save':
            attrs['uuid'] = self.uuid.str64()

        super(XMLRefDict, self)._xmlValue(name, item, generator, withSchema,
                                          version, attrs, mode)
        
    def _xmlValues(self, generator, version, mode):

        if mode == 'save':
            store = self.view.repository.store

            item = self._item
            if not (item.isNew() or
                    item.isAttributeDirty(self._name, item._references) or
                    len(self._changedRefs) == 0):
                raise AssertionError, '%s.%s not marked dirty' %(Item.__repr__(item), self._name)

            for key, (op, oldAlias) in self._changedRefs.iteritems():

                if op == 0:               # change
                    if key is not None:
                        link = self._get(key, load=False)
                        ref = link._value
                        previous = link._previousKey
                        next = link._nextKey
                        alias = link._alias
    
                        self._writeRef(key, version, previous, next, alias)
                        if oldAlias is not None and oldAlias != alias:
                            store.writeName(version, self.uuid, oldAlias,
                                            None)
                        if alias is not None:
                            store.writeName(version, self.uuid, alias,
                                            key)

                    else:
                        self._writeRef(self.uuid, version,
                                       self._firstKey, self._lastKey,
                                       self._count)
                        
                elif op == 1:             # remove
                    self._deleteRef(key, version)
                    if oldAlias is not None:
                        store.writeName(version, self.uuid, oldAlias,
                                        None)

                else:                     # error
                    raise ValueError, op

            if self._changedRefs:
                self.view._notifications.changed(self._item._uuid, self._name)

            if self._indexes:
                for name, index in self._indexes.iteritems():
                    attrs = { 'name': name, 'type': index.getIndexType() }
                    index._xmlValues(generator, version, attrs, mode)

        elif mode == 'serialize':
            super(XMLRefDict, self)._xmlValues(generator, version, mode)

        else:
            raise ValueError, mode

    def _clearDirties(self):

        PersistentRefs._clearDirties(self)
        if self._indexes:
            for name, index in self._indexes.iteritems():
                index._clearDirties()

    def _commitMerge(self):

        self._clear_()
        PersistentRefs._setItem(self, self._item)

    def _createIndex(self, indexType, **kwds):

        if indexType == 'numeric':
            return XMLNumericIndex(self._getRepository(), **kwds)

        return super(XMLRefDict, self)._createIndex(indexType, **kwds)


class XMLNumericIndex(NumericIndex):

    def __init__(self, view, **kwds):

        self.view = view
        self._changedKeys = {}
        
        if 'uuid' in kwds:
            self._uuid = UUID(kwds['uuid'])
            self._headKey = UUID(kwds['head'])
            self._tailKey = UUID(kwds['tail'])
        else:
            self._uuid = UUID()
            self._headKey = UUID()
            self._tailKey = UUID()

        self._key = self._getIndexes().prepareKey(self._uuid)
        self._value = StringIO()
        self._version = 0
        
        super(XMLNumericIndex, self).__init__(**kwds)

    def _keyChanged(self, key):

        self._changedKeys[key] = self[key]

    def removeKey(self, key):

        super(XMLNumericIndex, self).removeKey(key)
        self._changedKeys[key] = None

    def __getitem__(self, key):

        try:
            return super(XMLNumericIndex, self).__getitem__(key)
        except KeyError:
            if self._loadKey(key):
                return super(XMLNumericIndex, self).__getitem__(key)
            raise

    def __contains__(self, key):

        return self.has_key(key)

    def has_key(self, key):

        has = super(XMLNumericIndex, self).has_key(key)
        if not has:
            node = self._loadKey(key)
            has = node is not None

        return has

    def get(self, key, default=None):

        node = super(XMLNumericIndex, self).get(key, default)
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

    def _xmlValues(self, generator, version, attrs, mode):

        attrs['count'] = str(len(self))
        attrs['uuid'] = self._uuid.str64()
        attrs['head'] = self._headKey.str64()
        attrs['tail'] = self._tailKey.str64()

        super(XMLNumericIndex, self)._xmlValues(generator, version, attrs,
                                                mode)

        if mode == 'save':
            indexes = self._getIndexes()

            indexes.saveKey(self._key, self._value,
                            version, self._headKey, self._head)
            indexes.saveKey(self._key, self._value,
                            version, self._tailKey, self._tail)
            for key, node in self._changedKeys.iteritems():
                indexes.saveKey(self._key, self._value,
                                version, key, node)

            self._version = version
            
        elif mode == 'serialize':
            raise NotImplementedError, 'serialize'

        else:
            raise ValueError, mode

    def _clearDirties(self):

        self._changedKeys.clear()
        

class XMLChildren(Children, PersistentRefs):

    def __init__(self, view, item):

        self.uuid = item.itsUUID

        PersistentRefs.__init__(self, view)
        Children.__init__(self, item)

    def __len__(self):

        return PersistentRefs.__len__(self)

    def _setItem(self, item):

        Children._setItem(self, item)
        PersistentRefs._setItem(self, item)

    def _load(self, key):

        return not self._isRemoved(key) and self.view._loadItem(key) is not None

    def resolveAlias(self, alias, load=True):

        return (Children.resolveAlias(self, alias, load) or
                PersistentRefs.resolveAlias(self, alias, load))
            
    def linkChanged(self, link, key):

        super(XMLChildren, self).linkChanged(link, key)
        self._changeRef(key, link)

    def __delitem__(self, key):

        link = super(XMLChildren, self).__delitem__(key)
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

        super(XMLChildren, self).__setitem__(key, value,
                                             previousKey, nextKey, alias)

        if not loading:
            self._count += 1

    def _saveValues(self, version):

        store = self.view.repository.store
        unloads = []
        
        for key, (op, oldAlias) in self._changedRefs.iteritems():
    
            if op == 0:               # change
                if key is not None:
                    link = self._get(key, load=False)
                    previous = link._previousKey
                    next = link._nextKey
                    alias = link._alias
                    
                    self._writeRef(key, version, previous, next, alias)
                    if oldAlias is not None and oldAlias != alias:
                        store.writeName(version, self.uuid, oldAlias, None)
                    if alias is not None:
                        store.writeName(version, self.uuid, alias, key)

                    if link._value is None:
                        unloads.append((key, link._alias))

                else:
                    self._writeRef(self.uuid, version,
                                   self._firstKey, self._lastKey, self._count)
                        
            elif op == 1:             # remove
                self._deleteRef(key, version)
                if oldAlias is not None:
                    store.writeName(version, self.uuid, oldAlias, None)

            else:                     # error
                raise ValueError, op

        for key, alias in unloads:
            self._remove(key)
            if alias is not None:
                del self._aliases[alias]

    def _clearDirties(self):

        PersistentRefs._clearDirties(self)

    def _copy_(self, target):

        Children._copy_(self, target)
        PersistentRefs._copy_(self, target)
        target._original = self

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

        target = self.view._createChildren(self._item)
        self._copy_(target)
        self._item._setChildren(target)

        PersistentRefs._mergeChanges(target, oldVersion, toVersion)

    def _e_1_remove(self, *args):
        raise MergeError, ('children', self._item, 'modified child %s was removed in other view' %(args), MergeError.MOVE)

    def _e_2_remove(self, *args):
        raise MergeError, ('children', self._item, 'removed child %s was modified in other view' %(args), MergeError.MOVE)

    def _e_1_renames(self, *args):
        raise MergeError, ('children', self._item, 'child %s renamed to %s and %s' %(args), MergeError.RENAME)

    def _e_2_renames(self, *args):
        raise MergeError, ('children', self._item, 'child %s named %s conflicts with child %s of same name' %(args), MergeError.NAME)

    def _e_names(self, *args):
        raise MergeError, ('children', self._item, 'child %s conflicts with other child %s, both are named %s' %(args), MergeError.NAME)

