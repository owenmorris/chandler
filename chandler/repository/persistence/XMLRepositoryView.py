
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from datetime import datetime
from struct import pack
from cStringIO import StringIO

from bsddb.db import DBLockDeadlockError, DBNotFoundError

from repository.item.Item import Item
from repository.item.ItemRef import TransientRefDict
from repository.persistence.RepositoryError import RepositoryError, MergeError
from repository.persistence.RepositoryError import VersionConflictError
from repository.persistence.RepositoryView import RepositoryView
from repository.persistence.RepositoryView import OnDemandRepositoryView
from repository.persistence.Repository import Repository
from repository.persistence.Repository import RepositoryNotifications
from repository.persistence.XMLLob import XMLText, XMLBinary
from repository.persistence.XMLRefDict import XMLRefDict, XMLChildren
from repository.util.SAX import XMLGenerator

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

        for item in self._log:
            if item.isDeleted():
                del self._deletedRegistry[item.itsUUID]
                item._status &= ~Item.DELETED
            else:
                item.setDirty(0, None)
                item._unloadItem()

        for item in self._log:
            if not item.isNew():
                self.logger.debug('reloading version %d of %s',
                                  self._version, item)
                self._loadItem(item._uuid, instance=item)

        del self._log[:]
        if self.isDirty():
            self._roots._clearDirties()
            self.setDirty(0, None)

        self.prune(10000)

    def queryItems(self, query, load=True):

        store = self.repository.store
        items = []
        
        for doc in store.queryItems(self._version, query):
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

    def _createRefDict(self, item, name, otherName, persist, readOnly):

        if persist:
            return XMLRefDict(self, item, name, otherName, readOnly)
        else:
            return TransientRefDict(item, name, otherName, readOnly)

    def _createChildren(self, parent):

        return XMLChildren(self, parent)

    def _getLobType(self, mode):

        if mode == 'text':
            return XMLText
        if mode == 'binary':
            return XMLBinary

        raise ValueError, mode

    def _startTransaction(self):

        return self.repository.store.startTransaction()

    def _commitTransaction(self):

        if self._indexWriter is not None:
            self.repository.store._index.optimizeIndex(self._indexWriter)
            self._indexWriter.close()
            self._indexWriter = None
            
        self.repository.store.commitTransaction()

    def _abortTransaction(self):

        if self._indexWriter is not None:
            self._indexWriter.close()
            self._indexWriter = None
            
        self.repository.store.abortTransaction()

    def _getIndexWriter(self):

        if self._indexWriter is None:
            store = self.repository.store
            if not store._ramdb and store.txn is None:
                raise RepositoryError, "Can't index outside transaction"
            self._indexWriter = store._index.getIndexWriter()

        return self._indexWriter

    def refresh(self):

        history = self.repository.store._history
        newVersion = history.getVersion()

        if newVersion > self._version:
            histNotifications = RepositoryNotifications()
            unloads = {}
            self._mergeItems(history, self._version, newVersion,
                             histNotifications, unloads)
                    
            self.logger.debug('refreshing view from version %d to %d',
                              self._version, newVersion)
            self._version = newVersion

            for item in unloads.itervalues():
                self.logger.debug('unloading version %d of %s',
                                  item._version, item)
                item._unloadItem()
            for item in unloads.itervalues():
                if item._status & Item.PINNED:
                    self.logger.debug('reloading version %d of %s',
                                      newVersion, item)
                    self._loadItem(item._uuid, instance=item)

            before = datetime.now()
            count = len(histNotifications)
            histNotifications.dispatchHistory(self)
            delta = datetime.now() - before
            if delta.seconds > 1:
                self.logger.warning('%s %d notifications ran in %s',
                                    self, count, delta)

        self.prune(10000)

    def commit(self):

        if self._status & RepositoryView.COMMITTING == 0:
            if timing: tools.timing.begin("Repository commit")
            
            try:
                self._status |= RepositoryView.COMMITTING

                store = self.repository.store
                history = store._history
                before = datetime.now()

                size = 0L
                txnStarted = False
                lock = None

                def finish(lock, txnStarted, commit):
                    if txnStarted:
                        if commit:
                            self._commitTransaction()
                        else:
                            self._abortTransaction()
                    if lock:
                        lock = store.releaseLock(lock)
                    return lock, False
        
                self._notifications.clear()
        
                while True:
                    try:
                        while True:
                            self.refresh()
                            lock = store.acquireLock()
                            newVersion = history.getVersion()
                            if newVersion > self._version:
                                lock = store.releaseLock(lock)
                            else:
                                break
                    
                        count = len(self._log)
                        txnStarted = self._startTransaction()

                        if count > 0:
                            newVersion += 1
                            history.setVersion(newVersion)

                            for item in self._log:
                                size += self._saveItem(item, newVersion, store)
                            if self.isDirty():
                                self._roots._saveValues(newVersion)

                        lock, txnStarted = finish(lock, txnStarted, True)
                        break

                    except DBLockDeadlockError:
                        self.logger.info('retrying commit aborted by deadlock')
                        lock, txnStarted = finish(lock, txnStarted, False)
                        continue
            
                    except:
                        self.logger.exception('aborting transaction (%ld bytes)', size)
                        lock, txnStarted = finish(lock, txnStarted, False)
                        raise

                self._version = newVersion
                
                if len(self._notifications) > 0:
                    histNotifications = RepositoryNotifications()
                    for uuid, changes in self._notifications.iteritems():
                        histNotifications[uuid] = changes[-1]
                    histNotifications.dispatchHistory(self)

                if self._log:
                    for item in self._log:
                        item._version = newVersion
                        item.setDirty(0, None)
                        item._status &= ~(Item.NEW | Item.SAVED)
                    del self._log[:]

                    if self.isDirty():
                        self._roots._clearDirties()
                        self.setDirty(0, None)

                after = datetime.now()
                if count > 0:
                    self.logger.info('%s committed %d items (%ld bytes) in %s',
                                     self, count, size, after - before)

            finally:
                self._status &= ~RepositoryView.COMMITTING

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

        out = StringIO()
        generator = XMLGenerator(out, 'utf-8')
        generator.startDocument()
        item._saveItem(generator, newVersion, None)
        generator.endDocument()
        xml = out.getvalue()
        out.close()

        parent = item.itsParent.itsUUID
        store.saveItem(xml, uuid, newVersion, parent,
                       item._status & Item.SAVEMASK,
                       item._values._getDirties(),
                       item._references._getDirties())

        if item._status & item.ADIRTY:
            for name, acl in item._acls.iteritems():
                store.saveACL(newVersion, uuid, name, acl)

        if isDeleted:
            self._notifications.changed(uuid, 'deleted', parent=parent)
        elif isNew:
            self._notifications.changed(uuid, 'added')
        else:
            self._notifications.changed(uuid, 'changed')
                    
        return len(xml)

    def _mergeItems(self, history, oldVersion, toVersion,
                    histNotifications, unloads):

        merges = {}

        def check(uuid, version, docId, status, parentId, dirties):
            item = self.find(uuid, False)

            if item is not None:
                if item.isDirty():
                    oldDirty = status & Item.DIRTY
                    if uuid in merges:
                        merges[uuid] = (merges[uuid][0] | oldDirty, parentId)
                    else:
                        merges[uuid] = (oldDirty, parentId)
                else:
                    if item._version < toVersion:
                        unloads[uuid] = item
                    
            if status & Item.DELETED:
                histNotifications.history(uuid, 'deleted', parent=parent)
            else:
                histNotifications.history(uuid, 'changed', dirties=dirties)

        history.apply(check, oldVersion, toVersion)

        for uuid, (oldDirty, parentId) in merges.iteritems():
            
            item = self.find(uuid, False)
            newDirty = item.getDirty()

            if newDirty & oldDirty & Item.NDIRTY:
                self._mergeNDIRTY(item, parentId, oldVersion, toVersion)
                oldDirty &= ~Item.NDIRTY

            # @@@ Per Andi, commenting these out to prevent infinite recursion
            # Instead, we'll get a VersionConflictError
            # if newDirty & oldDirty & Item.CDIRTY:
            #     # item._children._mergeChanges(oldVersion, toVersion)
            #    oldDirty &= ~Item.CDIRTY

            if newDirty and oldDirty:
                raise VersionConflictError, (item, newDirty, oldDirty)

    def _mergeNDIRTY(self, item, parentId, oldVersion, toVersion):

        newParentId = item.itsParent.itsUUID
        if parentId != newParentId:
            s, d, p, v = self.store._history.getDocRecord(item._uuid,
                                                          oldVersion)
            if p != parentId and p != newParentId:
                raise MergeError, ('rename', item, 'item %s moved to %s and %s' %(item._uuid, p, newParentId), MergeError.MOVE)
    
        refs = self.store._refs
        key = refs.prepareKey(parentId, parentId)
        p, n, name = refs.loadRef(key, toVersion, item._uuid)

        if name != item._name:
            raise MergeError, ('rename', item, 'item %s renamed to %s and %s' %(item._uuid, item._name, name), MergeError.RENAME)
