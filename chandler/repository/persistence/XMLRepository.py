
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, re, libxml2, cStringIO

from datetime import datetime
from threading import currentThread
from struct import pack

from repository.item.Item import Item
from repository.util.UUID import UUID
from repository.util.ThreadLocal import ThreadLocal
from repository.util.SAX import XMLGenerator
from repository.persistence.Repository import Repository
from repository.persistence.Repository import OnDemandRepository, Store
from repository.persistence.RepositoryError import RepositoryError
from repository.persistence.XMLRepositoryView import XMLRepositoryView
from repository.persistence.DBContainer import DBContainer, RefContainer
from repository.persistence.DBContainer import VerContainer, HistContainer
from repository.persistence.DBContainer import NamesContainer, ACLContainer
from repository.persistence.FileContainer import FileContainer, BlockContainer
from repository.persistence.FileContainer import IndexContainer
from repository.remote.CloudFilter import CloudFilter

from bsddb.db import DBEnv, DB, DBError
from bsddb.db import DB_CREATE, DB_BTREE, DB_THREAD, DB_LOCK_WRITE
from bsddb.db import DB_RECOVER, DB_RECOVER_FATAL, DB_PRIVATE, DB_LOCK_MINLOCKS
from bsddb.db import DB_INIT_MPOOL, DB_INIT_LOCK, DB_INIT_TXN, DB_DIRTY_READ
from bsddb.db import DBRunRecoveryError, DBNoSuchFileError, DBNotFoundError
from bsddb.db import DBLockDeadlockError
from dbxml import XmlContainer, XmlDocument, XmlValue
from dbxml import XmlQueryContext, XmlUpdateContext


class XMLRepository(OnDemandRepository):
    """A Berkeley DBXML based repository.

    This simple repository implementation saves all items in separate XML
    item files in a given directory. It can then load them back to restore
    the same exact item hierarchy."""

    def __init__(self, dbHome):
        'Construct an XMLRepository giving it a DBXML container pathname'
        
        super(XMLRepository, self).__init__(dbHome)
        self._env = None
        
    def create(self, **kwds):

        if not self.isOpen():
            super(XMLRepository, self).create(**kwds)
            self._create(**kwds)
            self._status |= self.OPEN

    def _create(self, **kwds):

        ramdb = kwds.get('ramdb', False)

        if not ramdb:
            if not os.path.exists(self.dbHome):
                os.makedirs(self.dbHome)
            elif not os.path.isdir(self.dbHome):
                raise ValueError, "%s is not a directory" %(self.dbHome)
            else:
                self.delete()

        self._env = self._createEnv()

        if ramdb:
            flags = DB_INIT_MPOOL | DB_PRIVATE | DB_THREAD
        else:
            flags = self.OPEN_FLAGS
        self._env.open(self.dbHome, DB_CREATE | flags, 0)

        self.store = self._createStore()
        kwds['create'] = True
        self.store.open(**kwds)

    def _createStore(self):

        return XMLStore(self)

    def _createEnv(self):

        env = DBEnv()
        env.set_lk_detect(DB_LOCK_MINLOCKS)
        env.set_lk_max_locks(32767)
        env.set_lk_max_objects(32767)

        return env

    def delete(self):

        def purge(arg, path, names):
            for f in names:
                if f.startswith('__') or f.startswith('log.'):
                    f = os.path.join(path, f)
                    if not os.path.isdir(f):
                        os.remove(f)
        os.path.walk(self.dbHome, purge, None)

    def open(self, **kwds):

        if kwds.get('ramdb', False):
            self.create(**kwds)

        elif not self.isOpen():
            fromPath = kwds.get('fromPath', None)
            if fromPath is not None:
                self.delete()
                if not os.path.exists(self.dbHome):
                    os.mkdir(self.dbHome)
                import shutil
                for f in os.listdir(fromPath):
                    if f.startswith('__') or f.startswith('log.'):
                        shutil.copy2(os.path.join(fromPath,f), self.dbHome)

            super(XMLRepository, self).open(**kwds)
            self._env = self._createEnv()

            try:
                if kwds.get('recover', False):
                    before = datetime.now()
                    self._env.open(self.dbHome,
                                   DB_RECOVER | DB_CREATE | self.OPEN_FLAGS, 0)
                    after = datetime.now()
                    self.logger.info('opened db with recovery in %s',
                                     after - before)
                else:
                    self._env.open(self.dbHome, self.OPEN_FLAGS, 0)

                self.store = self._createStore()
                kwds['create'] = False
                self.store.open(**kwds)

            except DBNoSuchFileError:
                if kwds.get('create', False):
                    self._create(**kwds)
                else:
                    raise

            self._status |= self.OPEN

    def close(self):

        super(XMLRepository, self).close()

        if self.isOpen():
            self.store.close()
            self._env.close()
            self._env = None
            self._status &= ~self.OPEN

    def createView(self, name=None):

        return XMLRepositoryView(self, name)


    OPEN_FLAGS = DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_TXN | DB_THREAD


class XMLContainer(object):

    def __init__(self, store, name, txn, **kwds):

        super(XMLContainer, self).__init__()
        
        self.store = store
        self._filename = name

        if kwds.get('ramdb', False):
            name = ''

        self._xml = XmlContainer(store.env, name)
        self.version = "%d.%d.%d" %(self._xml.get_version_major(),
                                    self._xml.get_version_minor(),
                                    self._xml.get_version_patch())
            
        if kwds.get('create', False):
            self._xml.open(txn, DB_CREATE | DB_DIRTY_READ | DB_THREAD)
            self._xml.addIndex(txn, "", "kind",
                               "node-element-equality-string")
            self._xml.addIndex(txn, "", "id",
                               "node-attribute-equality-string")
        else:
            self._xml.open(txn, DB_DIRTY_READ | DB_THREAD)

    def attachView(self, view):
        pass

    def detachView(self, view):
        pass

    def loadItem(self, version, uuid):

        store = self.store
        txnStarted = False
        try:
            txnStarted = store.startTransaction()
            docId = store._versions.getDocId(uuid, version)

            # None -> not found, 0 -> deleted
            if docId: 
                return self.getDocument(docId)

        finally:
            if txnStarted:
                store.abortTransaction()

        return None
            
    def loadChild(self, version, uuid, name):

        uuid = self.store.readName(version, uuid, name)
        if uuid is None:
            return None

        return self.loadItem(version, uuid)

    def queryItems(self, version, query):

        store = self.store
        txnStarted = False

        docs = {}
        try:
            txnStarted = store.startTransaction()
            for value in self._xml.queryWithXPath(store.txn,
                                                  query, store.ctx,
                                                  DB_DIRTY_READ):
                doc = value.asDocument()
                ver = self.getDocVersion(doc)
                if ver <= version:
                    uuid = self.getDocUUID(doc)
                    dv = docs.get(uuid, None)
                    if dv is None or dv is not None and dv[1] < ver:
                        docs[uuid] = (doc, ver)

        finally:
            if txnStarted:
                store.abortTransaction()

        results = []
        for uuid, (doc, ver) in docs.iteritems():
            # verify that match version is latest,
            # if not it is out of date for the view
            if store._versions.getDocVersion(uuid, version) == ver:
                results.append(doc)

        return results

    def deleteDocument(self, doc):

        self._xml.deleteDocument(self.store.txn, doc, self.store.updateCtx)

    def getDocument(self, docId):

        return self._xml.getDocument(self.store.txn, docId, DB_DIRTY_READ)

    def putDocument(self, doc):

        return self._xml.putDocument(self.store.txn, doc, self.store.updateCtx)

    def close(self):

        self._xml.close()
        self._xml = None

    def parseDoc(self, doc, handler):

        string = doc.getContent()
        ctx = libxml2.createPushParser(handler, string, len(string), "doc")
        ctx.parseChunk('', 0, 1)
        if handler.errorOccurred():
            raise handler.saxError()
            
    def getDocUUID(self, doc):

        xml = doc.getContent()
        index = xml.index('uuid=') + 6

        return UUID(xml[index:xml.index('"', index)])

    def getDocVersion(self, doc):

        xml = doc.getContent()
        index = xml.index('version=', xml.index('version=') + 9) + 9

        return long(xml[index:xml.index('"', index)])

    nameExp = re.compile("<name>(.*)</name>")
    

class XMLStore(Store):

    def __init__(self, repository):

        self._threaded = ThreadLocal()
        super(XMLStore, self).__init__(repository)
        
    def open(self, **kwds):

        self._ramdb = kwds.get('ramdb', False)
        txnStarted = False
        
        try:
            txnStarted = self.startTransaction()
            txn = self.txn
                
            self._data = XMLContainer(self, "__data__", txn, **kwds)
            self._refs = RefContainer(self, "__refs__", txn, **kwds)
            self._names = NamesContainer(self, "__names__", txn, **kwds)
            self._versions = VerContainer(self, "__versions__", txn, **kwds)
            self._history = HistContainer(self, "__history__", txn, **kwds)
            self._text = FileContainer(self, "__text__", txn, **kwds)
            self._binary = FileContainer(self, "__binary__", txn, **kwds)
            self._blocks = BlockContainer(self, "__blocks__", txn, **kwds)
            self._index = IndexContainer(self, "__index__", txn, **kwds)
            self._acls = ACLContainer(self, "__acls__", txn, **kwds)
        finally:
            if txnStarted:
                self.commitTransaction()

    def close(self):

        self._data.close()
        self._refs.close()
        self._names.close()
        self._versions.close()
        self._history.close()
        self._text.close()
        self._binary.close()
        self._blocks.close()
        self._index.close()
        self._acls.close()

    def attachView(self, view):

        self._data.attachView(view)
        self._refs.attachView(view)
        self._names.attachView(view)
        self._versions.attachView(view)
        self._history.attachView(view)
        self._text.attachView(view)
        self._binary.attachView(view)
        self._blocks.attachView(view)
        self._index.attachView(view)
        self._acls.attachView(view)

    def detachView(self, view):

        self._data.detachView(view)
        self._refs.detachView(view)
        self._names.detachView(view)
        self._versions.detachView(view)
        self._history.detachView(view)
        self._text.detachView(view)
        self._binary.detachView(view)
        self._blocks.detachView(view)
        self._index.detachView(view)
        self._acls.detachView(view)

    def loadItem(self, version, uuid):

        return self._data.loadItem(version, uuid)
    
    def loadChild(self, version, uuid, name):

        return self._data.loadChild(version, uuid, name)

    def loadRef(self, version, uItem, uuid, key):

        buffer = self._refs.prepareKey(uItem, uuid)
        try:
            return self._refs.loadRef(buffer, version, key)
        finally:
            buffer.close()

    def loadRefs(self, version, uItem, uuid, firstKey):

        refs = []

        buffer = self._refs.prepareKey(uItem, uuid)
        txnStarted = False
        try:
            txnStarted = self.startTransaction()
            key = firstKey
            while key is not None:
                ref = self._refs.loadRef(buffer, version, key)
                assert ref is not None

                refs.append(ref)
                key = ref[3]
        finally:
            if txnStarted:
                self.abortTransaction()
            buffer.close()

        return refs

    def readName(self, version, key, name):

        return self._names.readName(version, key, name)

    def readNames(self, version, key):

        return self._names.readNames(version, key)

    def writeName(self, version, key, name, uuid):

        return self._names.writeName(version, key, name, uuid)

    def loadACL(self, version, uuid, name):

        return self._acls.readACL(version, uuid, name)

    def saveACL(self, version, uuid, name, acl):

        return self._acls.writeACL(version, uuid, name, acl)

    def queryItems(self, version, query):

        return self._data.queryItems(version, query)

    def searchItems(self, version, query):

        return self._index.searchDocuments(version, query)

    def parseDoc(self, doc, handler):

        self._data.parseDoc(doc, handler)

    def getDocUUID(self, doc):

        return self._data.getDocUUID(doc)

    def getDocVersion(self, doc):

        return self._data.getDocVersion(doc)

    def getDocContent(self, doc):

        return doc.getContent()

    def getVersion(self):

        return self._versions.getVersion()

    def getVersionInfo(self):

        return (self._versions.getVersionId(), self._versions.getVersion())

    def startTransaction(self):

        if not self._ramdb:
            if self.txn is None:
                self.txn = self.repository._env.txn_begin(None, DB_DIRTY_READ)
                return True
        else:
            self.txn = None

        return False

    def commitTransaction(self):

        if self.txn is not None:
            self.txn.commit()
            self.txn = None
            return True

        return False

    def abortTransaction(self):

        if self.txn is not None:
            self.txn.abort()
            self.txn = None
            return True

        return False

    def lobName(self, uuid, version):

        return pack('>16sl', uuid._uuid, ~version)

    def _getTxn(self):

        try:
            return self._threaded.txn
        except AttributeError:
            self._threaded.txn = None
            return None

    def _setTxn(self, txn):

        self._threaded.txn = txn
        return txn

    def _getEnv(self):

        return self.repository._env

    def _getCtx(self):

        try:
            return self._threaded.ctx

        except AttributeError:
            ctx = XmlQueryContext()
            ctx.setReturnType(XmlQueryContext.ResultDocuments)
            ctx.setEvaluationType(XmlQueryContext.Lazy)
            self._threaded.ctx = ctx
            
            return ctx

    def _getUpdateCtx(self):

        try:
            return self._threaded.updateCtx

        except AttributeError:
            updateCtx = XmlUpdateContext(self._data._xml)
            self._threaded.updateCtx = updateCtx

            return updateCtx

    def _getLockId(self):

        try:
            return self._threaded.lockId
        except AttributeError:
            lockId = self.repository._env.lock_id()
            self._threaded.lockId = lockId

            return lockId

    def acquireLock(self):

        if not self._ramdb:
            repository = self.repository
            return repository._env.lock_get(self.lockId,
                                            repository.itsUUID._uuid,
                                            DB_LOCK_WRITE)

        return None

    def releaseLock(self, lock):

        if lock is not None:
            self.repository._env.lock_put(lock)
        return None

    def saveItem(self, xml, uuid, version, currPN, origPN, status):
        
        doc = XmlDocument()
        doc.setContent(xml)
        if status & Item.DELETED:
            doc.setMetaData('', '', 'deleted', XmlValue('True'))

        try:
            docId = self._data.putDocument(doc)
        except:
            self.repository.logger.exception("putDocument failed, xml is: %s",
                                             xml)
            raise

        if status & Item.DELETED:
            parent, name = origPN
            self._versions.setDocVersion(uuid, version, 0)
            self._history.writeVersion(uuid, version, 0, status, parent)
            self.writeName(version, parent, name, None)

        else:
            self._versions.setDocVersion(uuid, version, docId)
            self._history.writeVersion(uuid, version, docId, status)

            if origPN is not None:
                parent, name = origPN
                self.writeName(version, parent, name, None)

            parent, name = currPN
            self.writeName(version, parent, name, uuid)

    def serveItem(self, version, uuid):

        if version == 0:
            version = self._versions.getVersion()
        
        doc = self.loadItem(version, uuid)
        if doc is None:
            return None
                
        xml = doc.getContent()
        out = cStringIO.StringIO()
        generator = XMLGenerator(out)

        try:
            attrs = { 'version': str(version),
                      'versionId': self._versions.getVersionId().str64() }
            generator.startElement('items', attrs)
            filter = CloudFilter(None, self, uuid, version, generator)
            filter.parse(xml, {})
            generator.endElement('items')
        
            return out.getvalue()
        finally:
            out.close()

    def serveChild(self, version, uuid, name):

        if version == 0:
            version = self._versions.getVersion()
        
        uuid = self.readName(version, uuid, name)
        if uuid is None:
            return None

        return self.serveItem(version, uuid)

    env = property(_getEnv)
    ctx = property(_getCtx)
    updateCtx = property(_getUpdateCtx)
    txn = property(_getTxn, _setTxn)
    lockId = property(_getLockId)
