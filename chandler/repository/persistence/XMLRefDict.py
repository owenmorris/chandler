
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from cStringIO import StringIO

from repository.item.Item import Children
from repository.item.ItemRef import RefDict
from repository.item.Indexes import NumericIndex
from repository.persistence.RepositoryError import MergeError
from repository.util.UUID import UUID
from repository.util.LinkedMap import LinkedMap


class XMLRefDict(RefDict):

    def __init__(self, view, item, name, otherName, readOnly):
        
        self._item = None
        self._uuid = UUID()
        self.view = view
        self._changedRefs = {}
        
        super(XMLRefDict, self).__init__(item, name, otherName, readOnly)

    def _getRepository(self):

        return self.view

    def _getRefs(self):

        return self.view.repository.store._refs

    def _loadRef(self, key):

        view = self.view
        
        if view is not view.repository.view:
            raise RepositoryError, 'current thread is not owning thread'

        try:
            if self._changedRefs[key][0] == 1:
                return None
        except KeyError:
            pass

        return self._getRefs().loadRef(self._key, self._item._version, key)

    def _changeRef(self, key, alias=None, noMonitors=False):

        super(XMLRefDict, self)._changeRef(key, alias, noMonitors)

        if not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (1, alias))
            if op != 0:
                self._changedRefs[key] = (0, alias)
        
    def _removeRef(self, key, _detach=False):

        link = super(XMLRefDict, self)._removeRef(key, _detach)

        if not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (0, link._alias))
            if op != 1:
                self._changedRefs[key] = (1, alias)
        else:
            raise ValueError, 'detach during load'

    def _writeRef(self, key, version, previous, next, alias):

        self._getRefs().saveRef(self._key, self._value, version, key,
                                previous, next, alias)

    def _deleteRef(self, key, version):

        self._getRefs().deleteRef(self._key, self._value, version, key)

    def _eraseRef(self, key):

        self._getRefs().eraseRef(self._key, key)

    def resolveAlias(self, alias, load=True):

        load = load and not self._item.isNew()
        key = None
        
        if self._aliases:
            key = self._aliases.get(alias)

        if load and key is None:
            view = self.view
            key = view.repository.store.readName(view._version, self._uuid,
                                                 alias)
            if key is not None:
                op, oldAlias = self._changedRefs.get(key, (0, None))
                if oldAlias == alias:
                    key = None

        return key

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, 'Item is already set'
        
        self._item = item
        if item is not None:
            self._prepareBuffers(item._uuid, self._uuid)

    def _prepareBuffers(self, uItem, uuid):

        self._uuid = uuid
        self._key = self._getRefs().prepareKey(uItem, uuid)
        self._value = StringIO()

    def _xmlValues(self, generator, version, mode):

        if mode == 'save':
            store = self.view.repository.store
            for key, (op, oldAlias) in self._changedRefs.iteritems():
                try:
                    value = self._get(key, load=False)
                except KeyError:
                    value = None
    
                if op == 0:               # change
                    if value is not None:
                        ref = value._value
                        previous = value._previousKey
                        next = value._nextKey
                        alias = value._alias
    
                        self._writeRef(key, version, previous, next, alias)
                        if oldAlias is not None and oldAlias != alias:
                            store.writeName(version, self._uuid, oldAlias,
                                            None)
                        if alias is not None:
                            store.writeName(version, self._uuid, alias,
                                            key)
                        
                elif op == 1:             # remove
                    self._deleteRef(key, version)
                    if oldAlias is not None:
                        store.writeName(version, self._uuid, oldAlias,
                                        None)

                else:                     # error
                    raise ValueError, op

            if self._changedRefs:
                self.view._notifications.changed(self._item._uuid, self._name)

            if len(self) > 0:
                generator.startElement('db', {})
                generator.characters(self._uuid.str64())
                generator.endElement('db')

            if self._indexes:
                for name, index in self._indexes.iteritems():
                    attrs = { 'name': name, 'type': index.getIndexType() }
                    index._xmlValues(generator, version, attrs, mode)

        elif mode == 'serialize':
            super(XMLRefDict, self)._xmlValues(generator, version, mode)

        else:
            raise ValueError, mode

    def _clearDirties(self):

        self._changedRefs.clear()
        if self._indexes:
            for name, index in self._indexes.iteritems():
                index._clearDirties()

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
        

class XMLChildren(Children):

    def __init__(self, view, item):

        super(XMLChildren, self).__init__(item)

        self.view = view
        
        self._uuid = item.itsUUID
        self._changedRefs = {}
        self._key = self._getRefs().prepareKey(self._uuid, self._uuid)
        self._value = StringIO()

        ref = self._getRefs().loadRef(self._key, self._item._version,
                                      self._uuid)
        if ref is not None:
            self._firstKey, self._lastKey, alias = ref

    def resolveAlias(self, alias, load=True):

        load = load and not self._item.isNew()
        key = None
        
        if self._aliases:
            key = self._aliases.get(alias)

        if load and key is None:
            view = self.view
            key = view.repository.store.readName(view._version,
                                                 self._uuid, alias)
            if key is not None:
                op, oldAlias = self._changedRefs.get(key, (0, None))
                if oldAlias == alias:
                    key = None

        return key

    def _load(self, key):

        if self.view._loadItem(key) is not None:
            return True

        return False

    def linkChanged(self, link, key):

        super(XMLChildren, self).linkChanged(link, key)
        
        if not self.view.isLoading():
            op, alias = self._changedRefs.get(key, (1, link._alias))
            if op != 0:
                # changed element: key, maybe old alias: alias
                self._changedRefs[key] = (0, alias)

    def __delitem__(self, key):

        link = super(XMLChildren, self).__delitem__(key)
        op, alias = self._changedRefs.get(key, (0, link._alias))
        if op != 1:
            # deleted element: key, maybe old alias: alias
            self._changedRefs[key] = (1, alias)

    def __setitem__(self, key, value,
                    previousKey=None, nextKey=None, alias=None):

        if previousKey is None and nextKey is None and self.view.isLoading():
            ref = self._getRefs().loadRef(self._key, self._item._version, key)
            if ref is not None:
                previousKey, nextKey, refAlias = ref
                assert alias == refAlias

        super(XMLChildren, self).__setitem__(key, value,
                                             previousKey, nextKey, alias)

    def _getRefs(self):

        return self.view.repository.store._refs

    def _writeRef(self, key, version, previous, next, alias):

        self._getRefs().saveRef(self._key, self._value, version, key,
                                previous, next, alias)

    def _deleteRef(self, key, version):

        self._getRefs().deleteRef(self._key, self._value, version, key)

    def _saveValues(self, version):

        store = self.view.repository.store

        if '_mergeList' in self.__dict__:
            children = self._mergeList
        else:
            children = self

        for key, (op, oldAlias) in children._changedRefs.iteritems():
            try:
                link = children._get(key, load=False)
            except KeyError:
                link = None
    
            if op == 0:               # change
                if link is not None:
                    previous = link._previousKey
                    next = link._nextKey
                    alias = link._alias
                    
                    self._writeRef(key, version, previous, next, alias)
                    if oldAlias is not None and oldAlias != alias:
                        store.writeName(version, self._uuid, oldAlias, None)
                    if alias is not None:
                        store.writeName(version, self._uuid, alias, key)

                elif key is None:
                    self._writeRef(self._uuid, version,
                                   self._firstKey, self._lastKey, None)
                        
            elif op == 1:             # remove
                self._deleteRef(key, version)
                if oldAlias is not None:
                    store.writeName(version, self._uuid, oldAlias, None)

            else:                     # error
                raise ValueError, op

    def _clearDirties(self):

        self._changedRefs.clear()
        try:
            del self._mergeList
        except AttributeError:
            pass

    def _mergeChanges(self, oldVersion, toVersion):

        self._mergeList = MergeList(self.view, self._item, oldVersion)
        self._mergeList.collectHistory(toVersion)
        self._mergeList.applyChanges(self, self._changedRefs)
                        
        self.view.logger.info('%s merged children of %s with newer versions',
                              self.view, self._item.itsPath)


class MergeList(LinkedMap):

    def __init__(self, view, item, version):

        super(MergeList, self).__init__()

        self.view = view
        self.item = item
        self.uuid = item._uuid
        self.version = version

        self._changedRefs = {}
        self._key = self._getRefs().prepareKey(self.uuid, self.uuid)
        self._aliases = {}
        
        ref = self._getRefs().loadRef(self._key, version, self.uuid)
        if ref is not None:
            self._firstKey, self._lastKey, alias = ref

    def _getRefs(self):

        return self.view.repository.store._refs

    def collectHistory(self, toVersion):

        def collect(version, (collection, child), ref):
            if collection == self.uuid:     # the children collection

                if child == self.uuid:      # the list head
                    self._firstKey, self._lastKey, alias = ref

                elif ref is None:           # deleted child
                    link = self._makeLink(None)
                    self._insert(child, link)

                else:
                    link = self._makeLink(child)
                    link._previousKey, link._nextKey, link._alias = ref
                    self._insert(child, link)
                    if link._alias is not None:
                        self._aliases[link._alias] = child
                        
        self._getRefs().applyHistory(collect, self.uuid,
                                     self.version, toVersion)

    def applyChanges(self, children, changes):

        key = self._insertKey = self._firstKey
        while key in self:
            self._insertKey = key
            key = self._get(key)._nextKey

        for child in changes.keys():
            if child in changes:
                if child is not None:           # not the list head
                    op, oldAlias = changes[child]
                    if op == 0:                 # insert or change
                        self.applyChange(children, changes, child, oldAlias)
                    elif op == 1:               # delete
                        raise NotImplementedError

        children._firstKey = self._firstKey
        children._lastKey = self._lastKey

    def applyChange(self, children, changes, child, oldAlias):

        link = children._get(child)
        prev = prevKey = link._previousKey
        exists = child in self

        if exists:
            alias = self._get(child)._alias
            if oldAlias is not None:
                if oldAlias != alias and link._alias != alias:
                    raise MergeError, ('merging children', self.item, 'child %s renamed to %s and %s' %(oldAlias, link._alias, alias), MergeError.RENAME)

        if link._alias in self._aliases:
            alias = link._alias
            if exists and self._aliases[alias] != child or not exists:
                raise MergeError, ('merging children', self.item, 'child %s conflicts with other child %s, both are named %s' %(child, self._aliases[alias], alias), MergeError.RENAME)

        if prev is None:
            if exists:
                prevKey = self._firstKey
            else:
                prev = prevKey = self._insertKey
        else:
            key = prevKey
            while key in self:
                prev = prevKey = key
                key = self._get(key)._nextKey

        if prevKey is not None and prevKey not in self:
            op, oa = changes.get(prevKey, (0, None))
            if op != 0:
                raise ValueError, op
            self.applyChange(children, changes, prevKey, oa)

        current = self.placeChange(child, prev, link._alias)

        link._previousKey = current._previousKey
        if exists:
            link._nextKey = current._nextKey

        if oldAlias is not None:
            self._changedRefs[child] = (0, oldAlias)

        try:
            del changes[child]
        except KeyError:
            pass

    def placeChange(self, key, afterKey, alias):

        if key == afterKey:
            raise ValueError, 'key == afterKey'

        try:
            current = self._get(key, False)
            exists = True
        except KeyError:
            current = self._makeLink(key)
            current._alias = alias
            self._insert(key, current)
            exists = False

        if exists:
            if current._previousKey == afterKey:
                return current
            if current._previousKey is not None:
                previous = self._get(current._previousKey)
            else:
                previous = None
            if current._nextKey is not None:
                next = self._get(current._nextKey)
            else:
                next = None

        if afterKey is None:
            after = None
            afterNextKey = self._firstKey
        else:
            after = self._get(afterKey)
            afterNextKey = after._nextKey

        if exists:
            if previous is not None:
                previous._setNext(current._nextKey, current._previousKey, self)
            if next is not None:
                next._setPrevious(current._previousKey, current._nextKey, self)

        current._setNext(afterNextKey, key, self)
        if afterNextKey is not None:
            self._get(afterNextKey)._setPrevious(key, afterNextKey, self)
        if after is not None:
            after._setNext(key, afterKey, self)

        current._setPrevious(afterKey, key, self)

        return current
            
    def linkChanged(self, link, key):

        op, alias = self._changedRefs.get(key, (1, link._alias))
        if op != 0:
            self._changedRefs[key] = (0, alias)

    def _load(self, key):

        raise MergeError, ('merging children', self.item,
                           'of a bug: _load should not be called.',
                           MergeError.BUG)

