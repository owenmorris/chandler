#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import with_statement

from threading import currentThread
from datetime import timedelta
from time import time, sleep

from chandlerdb.item.c import CItem
from chandlerdb.util.c import isuuid, Nil, Default, HashTuple
from chandlerdb.persistence.c import CView, DBLockDeadlockError

from repository.item.RefCollections import RefList
from repository.schema.Kind import Kind
from repository.persistence.RepositoryError \
     import RepositoryError, MergeError, VersionConflictError
from repository.persistence.RepositoryView \
     import RepositoryView, OnDemandRepositoryView
from repository.persistence.DBLob import DBLob
from repository.persistence.DBRefs import DBRefList, DBChildren, DBNumericIndex
from repository.persistence.DBItemIO import DBItemWriter


class DBRepositoryView(OnDemandRepositoryView):

    def openView(self, version=None, deferDelete=Default):

        self._log = set()
        self._indexWriter = None

        super(DBRepositoryView, self).openView(version, deferDelete)

    def _clear(self):

        self._log.clear()
        super(DBRepositoryView, self)._clear()

    def _logItem(self, item):

        if super(DBRepositoryView, self)._logItem(item):
            self._log.add(item)
            return True
        
        return False

    def dirtyItems(self):

        return iter(self._log)

    def hasDirtyItems(self):

        return len(self._log) > 0

    def dirlog(self):

        for item in self._log:
            print item.itsPath

    def cancel(self):

        for item in self._log:
            item.setDirty(0)
            item._unloadItem(not item.isNew(), self, False)

        self._instanceRegistry.update(self._deletedRegistry)
        self._log.update(self._deletedRegistry.itervalues())
        self._deletedRegistry.clear()

        self.cancelDelete()
        if self._deferDelete:
            self._status |= self.DEFERDEL

        for item in self._log:
            if not item.isNew():
                self.find(item.itsUUID)

        self._log.clear()

        if self.isDirty():
            self._roots._clearDirties()
            self.setDirty(0)

        if self.isCommitDeferred():
            self._deferredCommitCtx._data = None

        self.prune(self.pruneSize)

    def queryItems(self, kind=None, attribute=None):

        store = self.store
        
        for itemReader in store.queryItems(self, self._version,
                                           kind and kind.itsUUID,
                                           attribute and attribute.itsUUID):
            uuid = itemReader.getUUID()
            if uuid not in self._deletedRegistry:
                # load and itemReader, trick to pass reader directly to find
                item = self.find(uuid, itemReader)
                if item is not None:
                    yield item

    def queryItemKeys(self, kind=None, attribute=None):

        store = self.store
        
        for uuid in store.queryItemKeys(self, self._version,
                                        kind and kind.itsUUID,
                                        attribute and attribute.itsUUID):
            if uuid not in self._deletedRegistry:
                yield uuid

    def kindForKey(self, uuid):

        if uuid in self._registry:
            return self[uuid].itsKind

        uuid = self.store.kindForKey(self, self.itsVersion, uuid)
        if uuid is not None:
            return self[uuid]

        return None

    def _createRefList(self, item, name, otherName, dictKey,
                       readOnly, new, uuid):

        return DBRefList(self, item, name, otherName, dictKey,
                         readOnly, new, uuid)

    def _createChildren(self, parent, new):

        return DBChildren(self, parent, new)

    def _createNumericIndex(self, **kwds):

        return DBNumericIndex(self, **kwds)
    
    def _unregisterItem(self, item, reloadable):

        super(DBRepositoryView, self)._unregisterItem(item, reloadable)
        if self._log and item.isDirty():
            self._log.remove(item)

    def _getLobType(self):

        return DBLob

    def _startTransaction(self, nested=False, nomvcc=False):

        return self.store.startTransaction(self, nested, nomvcc)

    def _commitTransaction(self, status):

        if self._indexWriter is not None:
            self.store._index.commitIndexWriter(self._indexWriter)
            self._indexWriter = None
            
        self.store.commitTransaction(self, status)

    def _abortTransaction(self, status):

        if self._indexWriter is not None:
            try:
                self.store._index.abortIndexWriter(self._indexWriter)
            except:
                pass # ignorable exception
            self._indexWriter = None
            
        self.store.abortTransaction(self, status)

    def _getIndexWriter(self):

        if self._indexWriter is None:
            store = self.store
            if not store._ramdb and store.txn is None:
                raise RepositoryError, "Can't index outside transaction"
            self._indexWriter = store._index.getIndexWriter()

        return self._indexWriter

    def _dispatchHistory(self, history, refreshes, oldVersion, newVersion):

        refs = self.store._refs

        def dirtyNames():
            if kind is None:
                names = ()
            else:
                names = kind._nameTuple(dirties)
            if status & CItem.KDIRTY:
                names += ('itsKind',)
            return names

        for uItem, version, uKind, status, uParent, pKind, dirties in history:

            if not (pKind is None or pKind == DBItemWriter.NOITEM):
                kind = self.find(pKind)
                if kind is not None:
                    kind.extent._collectionChanged('refresh', 'collection',
                                                   'extent', uItem)

            kind = self.find(uKind)
            names = None
            if kind is not None:
                kind.extent._collectionChanged('refresh', 'collection',
                                               'extent', uItem)

                watchers = self.findValue(uItem, 'watchers', None, version)
                if watchers:
                    isNew = (status & CItem.NEW) != 0
                    for attribute, watchers in watchers.iteritems():
                        if watchers:
                            if names is None:
                                names = dirtyNames()
                            if isuuid(attribute):  # item watchers
                                for watcher in watchers:
                                    if watcher is not None:
                                        watcher('refresh', uItem, names)
                            elif isNew or attribute in names:
                                value = self.findValue(uItem, attribute, None,
                                                       version)
                                if isinstance(value, RefList):
                                    value = value.uuid
                                else:
                                    continue
                                for uRef in refs.iterHistory(self, value, version - 1, version, True):
                                    if uRef in refreshes:
                                        for watcher in watchers:
                                            if watcher is not None:
                                                watcher('refresh', 'collection', uItem, attribute, uRef)

                for name in kind._iterNotifyAttributes():
                    value = self.findValue(uItem, name, None, version)
                    if isinstance(value, RefList):
                        otherName = kind.getOtherName(name, None)
                        for uRef in value.iterkeys():
                            watchers = self.findValue(uRef, 'watchers', None, version)
                            if watchers:
                                watchers = watchers.get(otherName, None)
                                if watchers:
                                    for watcher in watchers:
                                        if watcher is not None:
                                            watcher('changed', 'notification', uRef, otherName, uItem)

            watchers = self._watchers
            if watchers and uItem in watchers:
                watchers = watchers[uItem].get(uItem)
                if watchers:
                    if names is None:
                        names = dirtyNames()
                    for watcher in watchers:
                        watcher('refresh', uItem, names)

    def refresh(self, mergeFn=None, version=None, notify=True):

        if not self._status & RepositoryView.REFRESHING:
            try:
                self._status |= RepositoryView.REFRESHING
                forwards = False
                while True:
                    txnStatus = 0
                    try:
                        txnStatus = self._startTransaction(False)
                        forwards = self._refresh(mergeFn, version, notify)
                    except DBLockDeadlockError:
                        self.logger.info('%s retrying refresh aborted by deadlock (thread: %s)', self, currentThread().getName())
                        self._abortTransaction(txnStatus)
                        sleep(1)
                        continue
                    except:
                        self.logger.exception('%s refresh aborted by error',
                                              self)
                        self._abortTransaction(txnStatus)
                        self.refreshErrors += 1
                        raise
                    else:
                        self._abortTransaction(txnStatus)
                        self.refreshErrors = 0
                        return self.itsVersion
            finally:
                self._status &= ~RepositoryView.REFRESHING
                if self._status & RepositoryView.COMMITREQ:
                    self._status &= ~RepositoryView.COMMITREQ
                    if forwards:
                        self.commit(mergeFn, notify)

        else:
            self.logger.warning('%s skipping recursive refresh', self)

    def _refresh(self, mergeFn=None, version=None, notify=True):

        store = self.store

        if not version:
            newVersion = store.getVersion()
        else:
            newVersion = min(long(version), store.getVersion())
        
        if newVersion > self.itsVersion:
            if notify:
                while self.itsVersion < newVersion:
                    self._refreshForwards(mergeFn, self.itsVersion + 1, True)
            else:
                self._refreshForwards(mergeFn, newVersion, False)

            if not self._status & RepositoryView.COMMITTING:
                self.prune(self.pruneSize)
            return True

        elif newVersion == self.itsVersion:
            if notify:
                self.dispatchQueuedNotifications()
            else:
                self.cancelQueuedNotifications()
            return True

        else:
            self.cancel()
            unloads = [item for item in self._registry.itervalues()
                       if item.itsVersion > newVersion]
            self._refreshItems(newVersion, unloads.__iter__)
            self.cancelQueuedNotifications()
            return False

    def _refreshItems(self, version, items):

        refCounted = self.isRefCounted()

        kinds = []
        for item in items():
            if item.isSchema():
                if isinstance(item, Kind):
                    kinds.append(item.itsUUID)
            item._unloadItem(refCounted or item.isPinned(), self, False)

        self._version = version

        if kinds:
            try:
                loading = self._setLoading(True)
                kinds = [kind for kind in (self.find(uuid) for uuid in kinds)
                         if kind is not None]
                for kind in kinds:
                    kind.flushCaches('unload')
            except:
                self._setLoading(loading, False)
                raise
            else:
                self._setLoading(loading, True)

            for kind in kinds:
                kind.flushCaches('reload')

        for item in items():
            if refCounted or item.isPinned():
                self.find(item.itsUUID)

    def _refreshForwards(self, mergeFn, newVersion, notify):

        mergeDeletes = []

        scan = True
        while scan:
            history = []
            schema_history = []
            refreshes = set()
            deletes = set()
            merges = {}
            unloads = {}
            dangling = []
            conflicts = []

            self._scanHistory(self.itsVersion,
                              newVersion, history, schema_history,
                              refreshes, merges, unloads, deletes)
            scan = False

            if merges:
                # if item is deleted in other view, resolve conflict by
                # deleting item locally (with mergeFn approval)
                for uItem in deletes:
                    if uItem in merges:
                        item = self.find(uItem)
                        if item is not None:
                            if not item.isDeferred():
                                if (mergeFn is None or
                                    not mergeFn(MergeError.DELETE, item,
                                                None, None)):
                                    self._e_2_delete(item, newVersion)
                            if not item.isDeleted():
                                item.delete(True)
                                if item.isDeferred():
                                    item._delete(self, True, None, False, True)
                                mergeDeletes.append(uItem)
                            scan = True

        oldVersion = self._version

        try:
            self._refreshItems(newVersion, unloads.itervalues)

            with self.notificationsDeferred():
                if merges:
                    self.logger.info('%s merging %d items...',
                                     self, len(merges))
                    newChanges = {}
                    changes = {}
                    indexChanges = {}

                    def _unload(keys):
                        for uItem in keys():
                            item = self.find(uItem)
                            if item is not None:
                                item.setDirty(0)
                                item._unloadItem(True, self, False)

                    try:
                        for uItem, (dirty, x, dirties) in merges.iteritems():
                            item = self.find(uItem, False)
                            newDirty = item.getDirty()
                            _newChanges = {}
                            _changes = {}
                            _indexChanges = {}
                            newChanges[uItem] = (newDirty, _newChanges)
                            changes[uItem] = (dirty, _changes)
                            self._collectChanges(item, newDirty,
                                                 dirty, HashTuple(dirties),
                                                 oldVersion, newVersion,
                                                 _newChanges, _changes,
                                                 _indexChanges)
                            if _indexChanges:
                                indexChanges[uItem] = _indexChanges
                    except:
                        self.cancelDeferredNotifications()
                        self._refreshItems(oldVersion, unloads.itervalues)
                        raise

                    try:
                        verify = (self._status & CView.VERIFY) != 0
                        if verify:
                            self._status &= ~CView.VERIFY

                        _unload(merges.iterkeys)

                        for uItem, (dirty, x, dirties) in merges.iteritems():
                            item = self.find(uItem)
                            newDirty, _newChanges = newChanges[uItem]
                            dirty, _changes = changes[uItem]
                            self._applyChanges(item, newDirty,
                                               dirty, HashTuple(dirties),
                                               oldVersion, newVersion,
                                               _newChanges, _changes, mergeFn,
                                               conflicts, indexChanges,
                                               dangling)
                        self._applyIndexChanges(indexChanges, deletes)

                        for uItem, name, uRef in dangling:
                            item = self.find(uItem)
                            if item is not None:
                                item._references._removeRef(name, uRef)

                    except:
                        if verify:
                            self._status |= CView.VERIFY
                        self.logger.exception('%s merge aborted by error', self)
                        self.cancelDeferredNotifications()
                        self.cancel()
                        raise

                    else:
                        if verify:
                            self._status |= CView.VERIFY

                # flush schema caches of changed kinds
                for (uItem, x, uKind, x, x, x, dirties) in schema_history:
                    kind = self[uKind]
                    if kind.isKindOf(kind.getKindKind()):
                        names = kind._nameTuple(dirties)
                        if 'superKinds' in names:
                            self[uItem].flushCaches('superKinds')
                        elif 'attributes' in names:
                            self[uItem].flushCaches('attributes')

                if merges:
                    try:
                        _changes = []
                        for uItem, name, newValue in conflicts:
                            item = self.find(uItem)
                            if item is not None:
                                if newValue is Nil:
                                    if hasattr(item, name):
                                        item.removeAttributeValue(name, None,
                                                                  None, True)
                                        _changes.append((item, 'remove', name))
                                else:
                                    item.setAttributeValue(name, newValue,
                                                           None, None, True,
                                                           True)
                                    _changes.append((item, 'set', name))
                        for item, op, name in _changes:
                            if not item.isStale():
                                item._fireChanges(op, name)
                    except:
                        self.logger.exception('%s merge aborted by error', self)
                        self.cancelDeferredNotifications()
                        self.cancel()
                        raise

            if notify or merges:
                before = time()
                self._dispatchHistory(history, refreshes,
                                      oldVersion, newVersion)
                count = self.dispatchQueuedNotifications()
                duration = time() - before
                if duration > 1.0:
                    self.logger.warning('%s %d notifications ran in %s',
                                        self, len(history) + count,
                                        timedelta(seconds=duration))
            else:
                self.cancelQueuedNotifications()

            if self._deferredDeletes:
                count = 0
                indices = []
                for defer in self._deferredDeletes:
                    if defer[0].isDeleted():  # during merge delete
                        indices.append(count)
                    else:
                        count += 1
                for i in indices:
                    del self._deferredDeletes[i]

            for uItem in mergeDeletes:
                del self._deletedRegistry[uItem]

        except:
            self._version = oldVersion
            raise

    def commit(self, mergeFn=None, notify=True, afterCommit=None):

        status = self._status

        if status & RepositoryView.COMMITTING:
            self.logger.warning('%s: skipping recursive commit', self)
        elif status & RepositoryView.DEFERCOMMIT:
            self._deferredCommitCtx._data = (mergeFn, notify, afterCommit)
        elif status & RepositoryView.REFRESHING:
            self._status |= RepositoryView.COMMITREQ
        elif self._log or self._deletedRegistry:
            try:
                release = False
                release = self._acquireExclusive()
                self._status |= RepositoryView.COMMITTING
                
                store = self.store
                before = time()

                size = 0L
                txnStatus = 0
                lock = None

                def finish(commit):
                    if txnStatus:
                        if commit:
                            self._commitTransaction(txnStatus)
                        else:
                            self._abortTransaction(txnStatus)
                            self._status &= ~RepositoryView.COMMITLOCK
                    return store.releaseLock(lock), 0
        
                while True:
                    try:
                        while True:
                            self.refresh(mergeFn, None, notify)
                            lock = store.acquireLock()
                            newVersion = store.getVersion()
                            if newVersion > self.itsVersion:
                                lock = store.releaseLock(lock)
                            else:
                                break

                        if self.isDeferringDelete():
                            self.effectDelete()

                        if self._deferDelete:
                            self._status |= RepositoryView.DEFERDEL

                        self._status |= RepositoryView.COMMITLOCK

                        count = len(self._log) + len(self._deletedRegistry)
                        if count > 500:
                            self.logger.info('%s committing %d items...',
                                             self, count)

                        if count > 0:
                            txnStatus = self._startTransaction(True)
                            if txnStatus == 0:
                                raise AssertionError, 'no transaction started'

                            newVersion = store.nextVersion()

                            itemWriter = DBItemWriter(store)
                            for item in self._log:
                                size += self._saveItem(item, newVersion,
                                                       itemWriter)
                            for item in self._deletedRegistry.itervalues():
                                size += self._saveItem(item, newVersion,
                                                       itemWriter)
                            if self.isDirty():
                                size += self._roots._saveValues(newVersion)

                        store.logCommit(self, newVersion, count)
                        lock, txnStatus = finish(True)
                        break

                    except DBLockDeadlockError:
                        self.logger.info('%s retrying commit aborted by deadlock (thread: %s)', self, currentThread().getName())
                        lock, txnStatus = finish(False)
                        sleep(1)
                        continue

                    except:
                        self.logger.exception('%s commit aborted by error',
                                              self)
                        lock, txnStatus = finish(False)
                        raise

                self._version = newVersion
                
                if self._log:
                    for item in self._log:
                        item._version = newVersion
                        item.setDirty(0, None)
                        item._status &= ~(CItem.NEW | CItem.MERGED)
                    self._log.clear()

                    if self.isDirty():
                        self._roots._clearDirties()
                        self.setDirty(0)

                if self._deletedRegistry:
                    self._deletedRegistry.clear()

                self._status &= ~RepositoryView.COMMITLOCK
                after = time()

                if count > 0:
                    duration = after - before
                    try:
                        iSpeed = "%d items/s" % round(count / duration)
                        dSpeed = "%d kbytes/s" % round((size >> 10) / duration)
                    except ZeroDivisionError:
                        iSpeed = dSpeed = 'speed could not be measured'

                    self.logger.info('%s committed %d items (%d kbytes) in %s, %s (%s)', self, count, size >> 10, timedelta(seconds=duration), iSpeed, dSpeed)

            finally:
                self._status &= ~RepositoryView.COMMITTING
                if release:
                    self._releaseExclusive()

        self.prune(self.pruneSize)

        if callable(afterCommit):
            afterCommit()

    def _saveItem(self, item, newVersion, itemWriter):

        if self.isDebug():
            self.logger.debug('saving version %d of %s',
                              newVersion, item.itsPath)

        if item.isDeleted() and item.isNew():
            return 0
                    
        return itemWriter.writeItem(item, newVersion)

    def mapChanges(self, freshOnly=False):

        if freshOnly:
            if self._status & RepositoryView.FDIRTY:
                self._status &= ~RepositoryView.FDIRTY
            else:
                return

        for item in list(self._log):   # self._log may change while looping
            status = item._status
            if not freshOnly or freshOnly and status & CItem.FDIRTY:
                if freshOnly:
                    status &= ~CItem.FDIRTY
                    item._status = status

                if item.isDeleted():
                    yield (item, item.itsVersion, status, [], [])
                elif item.isNew():
                    yield (item, item.itsVersion, status,
                           item._values.keys(),
                           item._references.keys())
                else:
                    yield (item, item.itsVersion, status,
                           item._values._getDirties(), 
                           item._references._getDirties())

    def mapChangedItems(self, freshOnly=False):

        if freshOnly:
            if self._status & RepositoryView.FDIRTY:
                self._status &= ~RepositoryView.FDIRTY
            else:
                return

        for item in list(self._log):   # self._log may change while looping
            if not freshOnly:
                yield item
            elif item.itsStatus & CItem.FDIRTY:
                item._status &= ~CItem.FDIRTY
                yield item
    
    def mapHistory(self, fromVersion=-1, toVersion=0, history=None):

        if history is None:
            store = self.store
            if fromVersion == -1:
                fromVersion = self._version
            if toVersion == 0:
                toVersion = store.getVersion()
            history = store._items.iterHistory(self, fromVersion, toVersion)

        for uItem, version, uKind, status, uParent, pKind, dirties in history:
            kind = self.find(uKind)
            if not (pKind is None or pKind == DBItemWriter.NOITEM):
                prevKind = self.find(pKind)
            else:
                prevKind = None
            values = []
            references = []
            if kind is not None:
                for name in kind._nameTuple(dirties):
                    if kind.getOtherName(name, None, None) is not None:
                        references.append(name)
                    else:
                        values.append(name)
            yield uItem, version, kind, status, values, references, prevKind

    def mapHistoryKeys(self, fromVersion=-1, toVersion=0):

        store = self.store
        if fromVersion == -1:
            fromVersion = self._version
        if toVersion == 0:
            toVersion = store.getVersion()

        return store._items.iterHistory(self, fromVersion, toVersion, True)

    def _scanHistory(self, oldVersion, toVersion,
                     history, schema_history,
                     refreshes, merges, unloads, deletes):

        for args in self.store._items.iterHistory(self, oldVersion, toVersion):
            uItem, version, uKind, status, uParent, prevKind, dirties = args

            history.append(args)
            refreshes.add(uItem)

            if status & CItem.DELETED:
                deletes.add(uItem)
            elif status & CItem.SCHEMA:
                schema_history.append(args)

            item = self.find(uItem, False)
            if item is not None:
                if item.isDirty():
                    oldDirty = status & CItem.DIRTY
                    if uItem in merges:
                        od, x, d = merges[uItem]
                        merges[uItem] = (od | oldDirty, uParent,
                                         d.union(dirties))
                    else:
                        merges[uItem] = (oldDirty, uParent, set(dirties))

                elif item.itsVersion < version:
                    unloads[uItem] = item

            elif uItem in self._deletedRegistry and uItem not in deletes:
                kind = self.find(uKind, False)
                if kind is None:
                    self._e_1_delete(uItem, uKind, oldVersion, version)
                else:
                    self._e_1_delete(uItem, kind, oldVersion, version)

    def _collectChanges(self, item, newDirty, dirty, dirties,
                        version, newVersion,
                        newChanges, changes, indexChanges):

        CDIRTY = CItem.CDIRTY
        NDIRTY = CItem.NDIRTY
        RDIRTY = CItem.RDIRTY
        VDIRTY = CItem.VDIRTY
        KDIRTY = CItem.KDIRTY

        if newDirty & CDIRTY:
            children = item._children
            newChanges[CDIRTY] = dict(children._iterChanges())
            if dirty & CDIRTY:
                changes[CDIRTY] = dict(children._iterHistory(version, newVersion))
            else:
                changes[CDIRTY] = {}

        if newDirty & NDIRTY:
            newChanges[NDIRTY] = (item.itsParent.itsUUID, item.itsName,
                                  item.isDeferred())

        if newDirty & RDIRTY:
            newChanges[RDIRTY] = _newChanges = {}
            changes[RDIRTY] = _changes = {}
            item._references._collectChanges(self, RDIRTY, dirties,
                                             _newChanges, _changes,
                                             indexChanges, version, newVersion)
                
        if newDirty & VDIRTY:
            newChanges[VDIRTY] = _newChanges = {}
            item._references._collectChanges(self, VDIRTY, dirties,
                                             _newChanges, None, indexChanges,
                                             version, newVersion)
            item._values._collectChanges(self, VDIRTY, dirties,
                                         _newChanges, None, indexChanges,
                                         version, newVersion)

        if newDirty & KDIRTY:
            newChanges[KDIRTY] = item.itsKind

    def _applyChanges(self, item, newDirty, dirty, dirties,
                      version, newVersion, newChanges, changes, mergeFn,
                      conflicts, indexChanges, dangling):

        CDIRTY = CItem.CDIRTY
        NDIRTY = CItem.NDIRTY
        RDIRTY = CItem.RDIRTY
        VDIRTY = CItem.VDIRTY
        KDIRTY = CItem.KDIRTY
        MERGED = CItem.MERGED

        def ask(reason, name, value):
            mergedValue = Default
            if mergeFn is not None:
                mergedValue = mergeFn(reason, item, name, value)
            if mergedValue is Default:
                if hasattr(type(item), 'onItemMerge'):
                    mergedValue = item.onItemMerge(reason, name, value)
                if mergedValue is Default:
                    self._e_1_overlap(reason, item, name)
            return mergedValue

        if newDirty & KDIRTY:
            if newChanges[KDIRTY] is item.itsKind:
                dirty &= ~KDIRTY
                newDirty &= ~KDIRTY
                self.logger.info('new %s was created in earlier transaction',
                                 item._repr_())

        if newDirty & CDIRTY:
            if changes is None:
                if item._children is None:
                    item._children = self._createChildren(item, True)
                item._children._applyChanges(newChanges[CDIRTY], (), None)
            else:
                item._children._applyChanges(newChanges[CDIRTY],
                                             changes[CDIRTY], None)
            dirty &= ~CDIRTY
            newDirty &= ~CDIRTY
            item._status |= (MERGED | CDIRTY)

        if newDirty & NDIRTY:
            newParent, newName, isDeferred = newChanges[NDIRTY]
            if dirty & NDIRTY:
                if newName != item.itsName:
                    newName = ask(MergeError.RENAME, 'itsName', newName)
                if newParent != item.itsParent.itsUUID:
                    newParent = ask(MergeError.MOVE, 'itsParent',
                                    self.find(newParent)).itsUUID
            if newName != item.itsName:
                item._name = newName
            if newParent != item.itsParent.itsUUID:
                item._parent = self[newParent]
            dirty &= ~NDIRTY
            newDirty &= ~NDIRTY
            if isDeferred:
                item._status |= (MERGED | CItem.DEFERRED | NDIRTY)
            else:
                item._status |= (MERGED | NDIRTY)

        if newDirty & RDIRTY:
            item._references._applyChanges(self, RDIRTY, dirties, ask,
                                           newChanges, changes, None, dangling)
            dirty &= ~RDIRTY
            newDirty &= ~RDIRTY
            item._status |= (MERGED | RDIRTY)

        if newDirty & VDIRTY:
            item._references._applyChanges(self, VDIRTY, dirties, ask,
                                           newChanges, None,
                                           conflicts, dangling)
            item._values._applyChanges(self, VDIRTY, dirties, ask, newChanges,
                                       conflicts, indexChanges)
            dirty &= ~VDIRTY
            newDirty &= ~VDIRTY
            item._status |= (MERGED | VDIRTY)

        if dirty and newDirty:
            raise VersionConflictError, (item, newDirty, dirty)

        if self.isDebug():
            self.logger.debug('%s merged %s with newer versions, merge status: 0x%0.8x', self, item._repr_(), (item._status & MERGED))

    def _applyIndexChanges(self, indexChanges, deletes):

        for uItem, _indexChanges in indexChanges.iteritems():
            item = self.find(uItem, False)
            if item is None and uItem not in deletes:
                raise AssertionError, (uItem, "item not found")
            for attr, __indexChanges in _indexChanges.iteritems():
                value = getattr(item, attr)
                for name, ___indexChanges in __indexChanges.iteritems():
                    value._applyIndexChanges(self, indexChanges, name,
                                             ___indexChanges, deletes)
                value._setDirty(True)

    def _e_1_delete(self, uItem, uKind, oldVersion, newVersion):

        raise MergeError, ('delete', uItem, 'item %s was deleted in this version (%d) but has later changes in version (%d) where it is of kind %s' %(uItem, oldVersion, newVersion, uKind), MergeError.CHANGE)

    def _e_2_delete(self, item, version):

        raise MergeError, ('delete', item, 'item %s was changed in this view but was deleted in version (%d)' %(item._repr_(), version), MergeError.DELETE)

    def _e_1_name(self, list, key, newName, name):
        raise MergeError, ('name', type(self).__name__, 'element %s renamed to %s and %s' %(key, newName, name), MergeError.RENAME)

    def _e_2_name(self, list, key, newKey, name):
        raise MergeError, ('name', type(list).__name__, 'element %s named %s conflicts with element %s of same name' %(newKey, name, key), MergeError.NAME)

    def _e_2_move(self, list, key):
        raise MergeError, ('move', type(list).__name__, 'removed element %s was modified in other view' %(key), MergeError.MOVE)

    def _e_1_overlap(self, code, item, name):
        
        raise MergeError, ('callback', item, 'merging values for %s on %s failed because no merge callback was defined or because the merge callback(s) punted' %(name, item._repr_()), code)

    def _e_2_overlap(self, code, item, name):

        raise MergeError, ('bug', item, 'merging refs is not implemented, attribute: %s' %(name), code)

    def _e_3_overlap(self, code, item, name):

        raise MergeError, ('bug', item, 'this merge not implemented, attribute: %s' %(name), code)
