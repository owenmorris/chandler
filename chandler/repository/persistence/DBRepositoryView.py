
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from datetime import timedelta
from time import time

from bsddb.db import DBLockDeadlockError

from repository.item.Item import Item
from repository.item.RefCollections import TransientRefList
from repository.persistence.RepositoryError \
     import RepositoryError, MergeError, VersionConflictError
from repository.persistence.RepositoryView \
     import RepositoryView, OnDemandRepositoryView
from repository.persistence.Repository \
     import Repository, RepositoryNotifications
from repository.persistence.DBLob import DBLob
from repository.persistence.DBRefs import DBRefList, DBChildren
from repository.persistence.DBContainer import HashTuple
from repository.persistence.DBItemIO \
     import DBItemWriter, DBItemVMergeReader, DBItemRMergeReader


class DBRepositoryView(OnDemandRepositoryView):

    def openView(self):

        super(DBRepositoryView, self).openView()

        self._log = set()
        self._indexWriter = None

    def _logItem(self, item):
        
        if super(DBRepositoryView, self)._logItem(item):
            self._log.add(item)
            return True
        
        return False

    def _unsavedItems(self):

        return iter(self._log)

    def dirlog(self):

        for item in self._log:
            print item.itsPath

    def cancel(self):

        refCounted = self.isRefCounted()
        for item in self._log:
            if item.isDeleted():
                del self._deletedRegistry[item.itsUUID]
                item._status &= ~Item.DELETED
            else:
                item.setDirty(0)
                item._unloadItem(not item.isNew(), self)

        for item in self._log:
            if not item.isNew():
                self.logger.debug('reloading version %d of %s',
                                  self._version, item)
                self.find(item._uuid)

        self._log.clear()
        if self.isDirty():
            self._roots._clearDirties()
            self.setDirty(0)

        self.prune(10000)

    def queryItems(self, kind=None, attribute=None, load=True):

        store = self.repository.store
        items = []
        
        for itemReader in store.queryItems(self._version, kind, attribute):
            uuid = itemReader.getUUID()
            if not uuid in self._deletedRegistry:
                # load and itemReader, trick to pass reader directly to find
                item = self.find(uuid, load=load and itemReader)
                if item is not None:
                    items.append(item)

        return items

    def searchItems(self, query, load=True):

        store = self.repository.store
        results = []
        docs = store.searchItems(self._version, query)
        for uuid, (ver, attribute) in docs.iteritems():
            if not uuid in self._deletedRegistry:
                item = self.find(uuid, load=load)
                if item is not None:
                    results.append((item, attribute))

        return results

    def _createRefList(self, item, name, otherName,
                       persist, readOnly, new, uuid):

        if persist:
            return DBRefList(self, item, name, otherName, readOnly, new, uuid)
        else:
            return TransientRefList(item, name, otherName, readOnly)

    def _createChildren(self, parent, new):

        return DBChildren(self, parent, new)

    def _registerItem(self, item):

        super(DBRepositoryView, self)._registerItem(item)
        if item.isDirty():
            self._log.add(item)

    def _unregisterItem(self, item, reloadable):

        super(DBRepositoryView, self)._unregisterItem(item, reloadable)
        if item.isDirty():
            self._log.remove(item)

    def _getLobType(self):

        return DBLob

    def _startTransaction(self):

        return self.repository.store.startTransaction()

    def _commitTransaction(self, status):

        if self._indexWriter is not None:
            self.repository.store._index.optimizeIndex(self._indexWriter)
            self._indexWriter.close()
            self._indexWriter = None
            
        self.repository.store.commitTransaction(status)

    def _abortTransaction(self, status):

        if self._indexWriter is not None:
            self._indexWriter.close()
            self._indexWriter = None
            
        self.repository.store.abortTransaction(status)

    def _getIndexWriter(self):

        if self._indexWriter is None:
            store = self.repository.store
            if not store._ramdb and store.txn is None:
                raise RepositoryError, "Can't index outside transaction"
            self._indexWriter = store._index.getIndexWriter()

        return self._indexWriter

    def refresh(self, mergeFn=None, version=None):

        store = self.repository.store
        newVersion = version or store.getVersion()
        
        if newVersion > self._version:
            histNotifications = RepositoryNotifications()

            unloads = {}
            also = set()
            _log = self._log

            try:
                self._log = set()
                try:
                    self._mergeItems(self._version, newVersion,
                                     histNotifications, unloads, also, mergeFn)
                except:
                    for item in self._log:
                        item.setDirty(0)
                        item._unloadItem(True, self)
                    raise
                else:
                    # unload items unchanged until changed by merging
                    for item in self._log:
                        item.setDirty(0)
                        unloads[item._uuid] = item
            finally:
                self._log = _log

            # unload items changed only in the other view whose older version
            # got loaded as a side-effect of merging
            for uuid in also:
                item = self.find(uuid, False)
                if item is not None:
                    unloads[uuid] = item
                    
            self.logger.debug('refreshing view from version %d to %d',
                              self._version, newVersion)
            self._version = newVersion

            refCounted = self.isRefCounted()
            for item in unloads.itervalues():
                self.logger.debug('unloading version %d of %s',
                                  item._version, item)
                item._unloadItem(refCounted or item.isPinned(), self)
            for item in unloads.itervalues():
                if refCounted or item.isPinned():
                    self.logger.debug('reloading version %d of %s',
                                      newVersion, item)
                    self.find(item._uuid)

            before = time()
            count = len(histNotifications)
            histNotifications.dispatchHistory(self)
            duration = time() - before
            if duration > 1.0:
                self.logger.warning('%s %d notifications ran in %s',
                                    self, count, timedelta(seconds=duration))

            self.prune(10000)

        elif newVersion < self._version:
            if self._log:
                self.cancel()
            for item in [item for item in self._registry.itervalues()
                         if item._version > newVersion]:
                item._unloadItem(False, self)
            self._version = newVersion

    def commit(self, mergeFn=None):

        if self._status & RepositoryView.COMMITTING == 0:
            try:
                self._exclusive.acquire()
                self._status |= RepositoryView.COMMITTING
                
                store = self.repository.store
                before = time()

                size = 0L
                txnStatus = 0
                lock = None

                def finish(lock, txnStatus, commit):
                    if commit:
                        self._commitTransaction(txnStatus)
                    else:
                        self._abortTransaction(txnStatus)
                    if lock:
                        lock = store.releaseLock(lock)
                    return lock, 0
        
                notifications = RepositoryNotifications()

                while True:
                    try:
                        while True:
                            self.refresh(mergeFn)
                            lock = store.acquireLock()
                            newVersion = store.getVersion()
                            if newVersion > self._version:
                                lock = store.releaseLock(lock)
                            else:
                                break

                        count = len(self._log)
                        if count > 1000:
                            self.logger.info('%s committing %d items...',
                                             self, count)

                        txnStatus = self._startTransaction()

                        if count > 0:
                            newVersion += 1
                            store._values.setVersion(newVersion)
                            itemWriter = DBItemWriter(store)
                            for item in self._log:
                                size += self._saveItem(item, newVersion,
                                                       itemWriter,
                                                       notifications)
                            if self.isDirty():
                                size += self._roots._saveValues(newVersion)

                        lock, txnStatus = finish(lock, txnStatus, True)
                        break

                    except DBLockDeadlockError:
                        self.logger.info('retrying commit aborted by deadlock')
                        lock, txnStatus = finish(lock, txnStatus, False)
                        continue

                    except:
                        if txnStatus:
                            self.logger.exception('aborting transaction (%d kb)', size >> 10)
                        lock, txnStatus = finish(lock, txnStatus, False)
                        raise

                self._version = newVersion
                
                if self._log:
                    for item in self._log:
                        item._version = newVersion
                        item.setDirty(0, None)
                        item._status &= ~(Item.NEW | Item.MERGED)
                    self._log.clear()

                    if self.isDirty():
                        self._roots._clearDirties()
                        self.setDirty(0)

                after = time()

                if count > 0:
                    duration = after - before
                    try:
                        iSpeed = "%d items/s" % round(count / duration)
                        dSpeed = "%d kbytes/s" % round((size >> 10) / duration)
                    except ZeroDivisionError:
                        iSpeed = dSpeed = 'speed could not be measured'

                    self.logger.info('%s committed %d items (%d kbytes) in %s, %s (%s)', self, count, size >> 10, timedelta(seconds=duration), iSpeed, dSpeed)

                if len(notifications) > 0:
                    notifications.dispatchHistory(self)

            finally:
                self._status &= ~RepositoryView.COMMITTING
                self._exclusive.release()

    def _saveItem(self, item, newVersion, itemWriter, notifications):

        if self.isDebug():
            self.logger.debug('saving version %d of %s',
                              newVersion, item.itsPath)

        if item.isDeleted():
            del self._deletedRegistry[item._uuid]
            if item.isNew():
                return 0
            notifications.changed(item._uuid, 'deleted')
        elif item.isNew():
            notifications.changed(item._uuid, 'added')
        else:
            notifications.changed(item._uuid, 'changed')
                    
        return itemWriter.writeItem(item, newVersion)

    def mapChanges(self, callable, freshOnly=False):

        if freshOnly:
            if self._status & RepositoryView.FDIRTY:
                self._status &= ~RepositoryView.FDIRTY
            else:
                return

        for item in self._log:
            status = item._status
            if not freshOnly or freshOnly and status & Item.FDIRTY:
                if freshOnly:
                    status &= ~Item.FDIRTY
                    item._status = status

                if item.isDeleted():
                    callable(item, item._version, status, [], [])
                elif item.isNew():
                    callable(item, item._version, status,
                             item._values.keys(),
                             item._references.keys())
                else:
                    callable(item, item._version, status,
                             item._values._getDirties(), 
                             item._references._getDirties())
    
    def mapHistory(self, callable, fromVersion=0, toVersion=0):

        store = self.repository.store
        
        if fromVersion == 0:
            fromVersion = self._version
        if toVersion == 0:
            toVersion = store.getVersion()

        def call(uuid, version, status, parentId, dirties):
            item = self.find(uuid)
            if item is not None:
                values = []
                references = []
                kind = item._kind
                if kind is not None:
                    for name, attr, k in kind.iterAttributes():
                        if name in dirties:
                            if kind.getOtherName(name,
                                                 default=None) is not None:
                                references.append(name)
                            else:
                                values.append(name)
                callable(item, version, status, values, references)

        store._items.applyHistory(call, fromVersion, toVersion)

    def _mergeItems(self, oldVersion, toVersion, histNotifications,
                    unloads, also, mergeFn):

        merges = {}

        def check(uuid, version, status, parent, dirties):
            item = self.find(uuid, False)

            if item is not None:
                if item.isDirty():
                    oldDirty = status & Item.DIRTY
                    if uuid in merges:
                        od, x, d = merges[uuid]
                        merges[uuid] = (od | oldDirty, parent, d.union(dirties))
                    else:
                        merges[uuid] = (oldDirty, parent, set(dirties))

                elif item._version < version:
                    unloads[uuid] = item
            else:
                also.add(uuid)
                    
            if status & Item.DELETED:
                histNotifications.history(uuid, 'deleted')
            else:
                histNotifications.history(uuid, 'changed', dirties=dirties)

        self.store._items.applyHistory(check, oldVersion, toVersion)

        try:
            for uuid, (oldDirty, parent, dirties) in merges.iteritems():
            
                item = self.find(uuid, False)
                newDirty = item.getDirty()

                if newDirty & oldDirty & Item.NDIRTY:
                    item._status |= Item.NMERGED
                    self._mergeNDIRTY(item, parent, oldVersion, toVersion)
                    oldDirty &= ~Item.NDIRTY

                if newDirty & oldDirty & Item.CDIRTY:
                    item._status |= Item.CMERGED
                    item._children._mergeChanges(oldVersion, toVersion)
                    oldDirty &= ~Item.CDIRTY

                if newDirty & oldDirty & Item.RDIRTY:
                    item._status |= Item.RMERGED
                    self._mergeRDIRTY(item, dirties, oldVersion, toVersion)
                    oldDirty &= ~Item.RDIRTY

                if newDirty & oldDirty & Item.VDIRTY:
                    item._status |= Item.VMERGED
                    self._mergeVDIRTY(item, toVersion, dirties, mergeFn)
                    oldDirty &= ~Item.VDIRTY

                if newDirty & oldDirty == 0:
                    if oldDirty & Item.VDIRTY:
                        item._status |= Item.VMERGED
                        self._mergeVDIRTY(item, toVersion, dirties, mergeFn)
                        oldDirty &= ~Item.VDIRTY
                    if oldDirty & Item.RDIRTY:
                        item._status |= Item.RMERGED
                        self._mergeRDIRTY(item, dirties, oldVersion, toVersion)
                        oldDirty &= ~Item.RDIRTY

                if newDirty and oldDirty:
                    raise VersionConflictError, (item, newDirty, oldDirty)

        except VersionConflictError:
            for uuid in merges.iterkeys():
                item = self.find(uuid, False)
                if item._status & Item.MERGED:
                    item._revertMerge()

            raise

        else:
            for uuid in merges.iterkeys():
                item = self.find(uuid, False)
                if item._status & Item.MERGED:
                    item._commitMerge(toVersion)
                    self._i_merged(item)

    def _mergeNDIRTY(self, item, parentId, oldVersion, toVersion):

        newParentId = item.itsParent.itsUUID
        if parentId != newParentId:
            p = self.store._items.getItemParentId(oldVersion, item._uuid)
            if p != parentId and p != newParentId:
                self._e_1_rename(item, p, newParentId)
    
        refs = self.store._refs
        key = refs.prepareKey(parentId, parentId)
        p, n, name = refs.loadRef(key, toVersion, item._uuid)

        if name != item._name:
            self._e_2_rename(item, name)

    def _mergeRDIRTY(self, item, dirties, oldVersion, toVersion):

        dirties = HashTuple(dirties)
        store = self.repository.store
        args = store._items.loadItem(toVersion, item._uuid)
        DBItemRMergeReader(store, item, dirties,
                           oldVersion, *args).readItem(self, [])

    def _mergeVDIRTY(self, item, toVersion, dirties, mergeFn):

        dirties = HashTuple(dirties)
        store = self.repository.store
        args = store._items.loadItem(toVersion, item._uuid)
        DBItemVMergeReader(store, item, dirties,
                           mergeFn, *args).readItem(self, [])

    def _i_merged(self, item):

        self.logger.info('%s merged %s with newer versions, merge status: 0x%0.8x', self, item.itsPath, (item._status & Item.MERGED))

    def _e_1_rename(self, item, parentId, newParentId):

        raise MergeError, ('rename', item, 'item %s moved to %s and %s' %(item._uuid, parentId, newParentId), MergeError.MOVE)

    def _e_2_rename(self, item, name):

        raise MergeError, ('rename', item, 'item %s renamed to %s and %s' %(item._uuid, item._name, name), MergeError.RENAME)
