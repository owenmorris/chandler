
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from datetime import timedelta
from time import time

from bsddb.db import DBLockDeadlockError

from repository.item.Item import Item
from repository.item.RefCollections import TransientRefList
from repository.item.ItemHandler import MergeHandler
from repository.persistence.RepositoryError import RepositoryError, MergeError
from repository.persistence.RepositoryError import VersionConflictError
from repository.persistence.RepositoryView import RepositoryView
from repository.persistence.RepositoryView import OnDemandRepositoryView
from repository.persistence.Repository import Repository
from repository.persistence.Repository import RepositoryNotifications
from repository.persistence.XMLLob import XMLText, XMLBinary
from repository.persistence.XMLRefs import XMLRefList, XMLChildren
from repository.persistence.DBContainer import HashTuple
from repository.persistence.DBGenerator import DBGenerator

timing = False
if timing: import tools.timing

class XMLRepositoryView(OnDemandRepositoryView):

    def openView(self):

        super(XMLRepositoryView, self).openView()

        self._log = []
        self._notifications = RepositoryNotifications()
        self._indexWriter = None

    def _logItem(self, item):
        
        if super(XMLRepositoryView, self)._logItem(item):
            self._log.append(item)
            return True
        
        return False

    def _newItems(self):

        for item in self._log:
            if item.isNew():
                yield item

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
                item._unloadItem(not item.isNew())

        for item in self._log:
            if not item.isNew():
                self.logger.debug('reloading version %d of %s',
                                  self._version, item)
                self.find(item._uuid)

        del self._log[:]
        if self.isDirty():
            self._roots._clearDirties()
            self.setDirty(0)

        self.prune(10000)

    def queryItems(self, kind=None, attribute=None, load=True):

        store = self.repository.store
        items = []
        
        for doc in store.queryItems(self._version, kind, attribute):
            uuid = store.getDocUUID(doc)
            if not uuid in self._deletedRegistry:
                # load and doc, trick to pass doc directly to find
                item = self.find(uuid, load=load and doc)
                if item is not None:
                    items.append(item)

        return items

    def searchItems(self, query, load=True):

        store = self.repository.store
        results = []
        docs = store.searchItems(self._version, query)
        for (uuid, (ver, attribute)) in docs.iteritems():
            if not uuid in self._deletedRegistry:
                item = self.find(uuid, load=load)
                if item is not None:
                    results.append((item, attribute))

        return results

    def _createRefList(self, item, name, otherName,
                       persist, readOnly, new, uuid):

        if persist:
            return XMLRefList(self, item, name, otherName, readOnly, new, uuid)
        else:
            return TransientRefList(item, name, otherName, readOnly)

    def _createChildren(self, parent, new):

        return XMLChildren(self, parent, new)

    def _getLobType(self, mode):

        if mode == 'text':
            return XMLText
        if mode == 'binary':
            return XMLBinary

        raise ValueError, mode

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

    def refresh(self, mergeFn=None):

        store = self.repository.store
        newVersion = store.getVersion()
        
        if newVersion > self._version:
            histNotifications = RepositoryNotifications()
            unloads = {}
            self._mergeItems(self._version, newVersion,
                             histNotifications, unloads, mergeFn)
                    
            self.logger.debug('refreshing view from version %d to %d',
                              self._version, newVersion)
            self._version = newVersion

            refCounted = self.isRefCounted()
            for item in unloads.itervalues():
                self.logger.debug('unloading version %d of %s',
                                  item._version, item)
                item._unloadItem(refCounted or item.isPinned())
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

    def commit(self, mergeFn=None):

        if self._status & RepositoryView.COMMITTING == 0:
            if timing: tools.timing.begin("Repository commit")

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
        
                self._notifications.clear()
        
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
                        txnStatus = self._startTransaction()

                        if count > 0:
                            newVersion += 1
                            store._values.setVersion(newVersion)

                            for item in self._log:
                                size += self._saveItem(item, newVersion, store)
                            if self.isDirty():
                                self._roots._saveValues(newVersion)

                        lock, txnStatus = finish(lock, txnStatus, True)
                        break

                    except DBLockDeadlockError:
                        self.logger.info('retrying commit aborted by deadlock')
                        lock, txnStatus = finish(lock, txnStatus, False)
                        continue

                    except:
                        if txnStatus:
                            self.logger.exception('aborting transaction (%ld bytes)', size)
                        lock, txnStatus = finish(lock, txnStatus, False)
                        raise

                self._version = newVersion
                
                if self._log:
                    for item in self._log:
                        item._version = newVersion
                        item.setDirty(0, None)
                        item._status &= ~(Item.NEW | Item.MERGED)
                    del self._log[:]

                    if self.isDirty():
                        self._roots._clearDirties()
                        self.setDirty(0)

                after = time()

                if count > 0:
                    duration = after - before
                    try:
                        speed = ", %d/s" % round(count / duration)
                    except ZeroDivisionError:
                        speed = ' (speed could not be measured)'
                    self.logger.info('%s committed %d items in %s%s',
                                     self, count,
                                     timedelta(seconds=duration), speed)

                if len(self._notifications) > 0:
                    histNotifications = RepositoryNotifications()
                    for uuid, changes in self._notifications.iteritems():
                        histNotifications[uuid] = changes[-1]
                    histNotifications.dispatchHistory(self)

            finally:
                self._status &= ~RepositoryView.COMMITTING
                self._exclusive.release()

            if timing: tools.timing.end("Repository commit")

    def _saveItem(self, item, newVersion, store):

        uuid = item._uuid
        isNew = item.isNew()
        isDeleted = item.isDeleted()
        isDebug = self.isDebug()
        
        if isDeleted:
            del self._deletedRegistry[uuid]
            if isNew:
                return 0

        if isDebug:
            self.logger.debug('saving version %d of %s',
                              newVersion, item.itsPath)

        generator = DBGenerator(store, uuid, newVersion,
                                item._status & Item.SAVEMASK,
                                item._values._getDirties(),
                                item._references._getDirties())
        generator.startDocument()
        item._saveItem(generator, newVersion)
        generator.endDocument()

        if item._status & item.ADIRTY:
            for name, acl in item._acls.iteritems():
                store.saveACL(newVersion, uuid, name, acl)

        if isDeleted:
            parent = item.itsParent.itsUUID
            self._notifications.changed(uuid, 'deleted', parent=parent)
        elif isNew:
            self._notifications.changed(uuid, 'added')
        else:
            self._notifications.changed(uuid, 'changed')
                    
        return 0

    def mapChanges(self, callable):

        for item in self._log:
            if item.isDeleted():
                callable(item, item._version, item._status, [], [])
            elif item.isNew():
                callable(item, item._version, item._status,
                         item._values.keys(),
                         item._references.keys())
            else:
                callable(item, item._version, item._status,
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

    def _mergeItems(self, oldVersion, toVersion, histNotifications, unloads,
                    mergeFn):

        merges = {}

        def union(l0, l1):
            for i in l1:
                if not i in l0:
                    l0.append(i)

        def check(uuid, version, status, parent, dirties):
            item = self.find(uuid, False)

            if item is not None:
                if item.isDirty():
                    oldDirty = status & Item.DIRTY
                    if uuid in merges:
                        x, od, x, d = merges[uuid]
                        merges[uuid] = (od | oldDirty, parent,
                                        union(d, dirties))
                    else:
                        merges[uuid] = (oldDirty, parent,
                                        list(dirties))

                elif item._version < version:
                    unloads[uuid] = item
                    
            if status & Item.DELETED:
                histNotifications.history(uuid, 'deleted', parent=parent)
            else:
                histNotifications.history(uuid, 'changed', dirties=dirties)

        self.store._items.applyHistory(check, oldVersion, toVersion)

        try:
            for uuid, (oldDirty, parent, dirties) in merges.iteritems():
            
                item = self.find(uuid, False)
                newDirty = item.getDirty()

                if newDirty & oldDirty & Item.NDIRTY:
                    self._mergeNDIRTY(item, parent, oldVersion, toVersion)
                    oldDirty &= ~Item.NDIRTY
                    item._status |= Item.NMERGED

                if newDirty & oldDirty & Item.CDIRTY:
                    item._children._mergeChanges(oldVersion, toVersion)
                    oldDirty &= ~Item.CDIRTY
                    item._status |= Item.CMERGED

                if newDirty & oldDirty & Item.RDIRTY:
                    self._mergeRDIRTY(item, dirties, oldVersion, toVersion)
                    oldDirty &= ~Item.RDIRTY
                    item._status |= Item.RMERGED

                if newDirty & oldDirty & Item.VDIRTY:
                    self._mergeVDIRTY(item, toVersion, dirties, mergeFn)
                    oldDirty &= ~Item.VDIRTY
                    item._status |= Item.VMERGED

                if newDirty & oldDirty == 0:
                    if oldDirty & Item.VDIRTY:
                        self._mergeVDIRTY(item, toVersion, None, mergeFn)
                        oldDirty &= ~Item.VDIRTY
                        item._status |= Item.VMERGED
                    if oldDirty & Item.RDIRTY:
                        self._mergeRDIRTY(item, dirties, oldVersion, toVersion)
                        oldDirty &= ~Item.RDIRTY
                        item._status |= Item.RMERGED

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
        merged = []
        for name in item._references._getDirties():
            if name in dirties:
                item._references[name]._mergeChanges(oldVersion, toVersion)
                merged.append(dirties.hash(name))
        if merged:
            dirties = HashTuple(filter(lambda hash: hash not in merged,
                                       dirties))
        item._references._dirties = dirties

    def _mergeVDIRTY(self, item, toVersion, dirties, mergeFn):

        if dirties is not None:
            dirties = HashTuple(dirties)
            overlaps = []
            values = item._values
            references = item._references
            overlaps.extend([name for name in values._getDirties()
                             if name in dirties])
            overlaps.extend([name for name in references._getDirties()
                             if name in dirties and
                             not references._isRefList(name)])
            if overlaps:
                self._e_2_overlap(item, overlaps[0])

        store = self.repository.store
        mergeHandler = MergeHandler(self, item, dirties)
        doc = store.loadItem(toVersion, item._uuid)
        store.parseDoc(doc, mergeHandler)
        if mergeHandler.errorOccurred():
            raise mergeHandler.saxError()

    def _i_merged(self, item):

        self.logger.info('%s merged %s with newer versions, merge status: 0x%0.4x', self, item.itsPath, (item._status & Item.MERGED) >> 16)

    def _e_1_rename(self, item, parentId, newParentId):

        raise MergeError, ('rename', item, 'item %s moved to %s and %s' %(item._uuid, parentId, newParentId), MergeError.MOVE)

    def _e_2_rename(self, item, name):

        raise MergeError, ('rename', item, 'item %s renamed to %s and %s' %(item._uuid, item._name, name), MergeError.RENAME)

    def _e_2_overlap(self, item, name):
        
        raise MergeError, ('values', item, 'merging values is not yet implemented, overlapping attribute: %s' %(name), MergeError.BUG)

    def _e_2v_overlap(self, item, name):
        
        raise MergeError, ('values', item, "literal value attribute '%s' changed in both views" %(name), MergeError.VALUE)
