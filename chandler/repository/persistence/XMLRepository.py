
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, re, libxml2

from datetime import datetime
from threading import currentThread

from repository.util.UUID import UUID
from repository.util.ThreadLocal import ThreadLocal
from repository.persistence.Repository import Repository, RepositoryError
from repository.persistence.Repository import OnDemandRepository, Store
from repository.persistence.XMLRepositoryView import XMLRepositoryLocalView
from repository.persistence.XMLRepositoryView import XMLRepositoryClientView
from repository.persistence.DBContainer import DBContainer, RefContainer
from repository.persistence.DBContainer import VerContainer, HistContainer
from repository.persistence.FileContainer import FileContainer, BlockContainer
from repository.persistence.FileContainer import IndexContainer

from bsddb.db import DBEnv, DB, DBError
from bsddb.db import DB_CREATE, DB_BTREE, DB_THREAD
from bsddb.db import DB_RECOVER, DB_RECOVER_FATAL, DB_LOCK_MINLOCKS
from bsddb.db import DB_INIT_MPOOL, DB_INIT_LOCK, DB_INIT_TXN, DB_DIRTY_READ
from bsddb.db import DBRunRecoveryError, DBNoSuchFileError, DBNotFoundError
from bsddb.db import DBLockDeadlockError
from dbxml import XmlContainer, XmlValue
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
        
    def create(self):

        if not self.isOpen():
            super(XMLRepository, self).create()
            self._create()
            self._status |= self.OPEN

    def _create(self):

        if not os.path.exists(self.dbHome):
            os.makedirs(self.dbHome)
        elif not os.path.isdir(self.dbHome):
            raise ValueError, "%s exists but is not a directory" %(self.dbHome)
        else:
            self.delete()
        
        self._env = self._createEnv()
        self._env.open(self.dbHome, DB_CREATE | self.OPEN_FLAGS, 0)

        self.store = XMLStore(self)
        self.store.open(True)

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

    def open(self, create=False, recover=False):

        if not self.isOpen():
            super(XMLRepository, self).open()
            self._env = self._createEnv()
            
            try:
                if recover:
                    before = datetime.now()
                    self._env.open(self.dbHome,
                                   DB_RECOVER | DB_CREATE | self.OPEN_FLAGS, 0)
                    after = datetime.now()
                    print 'opened db with recovery in %s' %(after - before)
                else:
                    self._env.open(self.dbHome, self.OPEN_FLAGS, 0)

                self.store = XMLStore(self)
                self.store.open(False)

            except DBNoSuchFileError:
                if create:
                    self._create()
                else:
                    raise

            self._status |= self.OPEN

    def close(self, purge=False):

        super(XMLRepository, self).close(purge)

        if self.isOpen():
            self.store.close()
            self._env.close()
            self._env = None
            self._status &= ~self.OPEN

    def serverOpen(self):

        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        return (self.store, XMLRepositoryClientView)

    def _createView(self):

        return XMLRepositoryLocalView(self)


    OPEN_FLAGS = DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_TXN | DB_THREAD


class XMLContainer(object):

    def __init__(self, store, name, txn, create):

        super(XMLContainer, self).__init__()
        
        self.store = store
        self._xml = XmlContainer(store.env, name)
        self._filename = name
        self.version = "%d.%d.%d" %(self._xml.get_version_major(),
                                    self._xml.get_version_minor(),
                                    self._xml.get_version_patch())
            
        if create:
            self._xml.open(txn, DB_CREATE | DB_DIRTY_READ | DB_THREAD)
            self._xml.addIndex(txn, "", "uuid",
                               "node-attribute-equality-string")
            self._xml.addIndex(txn, "", "kind",
                               "node-element-equality-string")
            self._xml.addIndex(txn, "", "container",
                               "node-element-equality-string")
            self._xml.addIndex(txn, "", "name",
                               "node-element-equality-string")
            self._xml.addIndex(txn, "", "id",
                               "node-attribute-equality-string")
        else:
            self._xml.open(txn, DB_DIRTY_READ | DB_THREAD)

    def loadItem(self, version, uuid):

        store = self.store
        txnStarted = False
        try:
            txnStarted = store._startTransaction()
            docId = store._versions.getDocId(uuid, version)

            # None -> not found, 0 -> deleted
            if docId: 
                return self._xml.getDocument(store.txn, docId, DB_DIRTY_READ)

        finally:
            if txnStarted:
                store._abortTransaction()

        return None
            
    def loadChild(self, version, uuid, name):

        store = self.store
        ctx = store.ctx
        ctx.setVariableValue("name", XmlValue(name.encode('utf-8')))
        ctx.setVariableValue("uuid", XmlValue(uuid.str64()))
        ctx.setVariableValue("version", XmlValue(float(version)))

        doc = None
        ver = 0
        txnStarted = False

        try:
            txnStarted = store._startTransaction()
            if self.version == "1.2.0":
                for value in self._xml.queryWithXPath(store.txn,
                                                      self.store.containerExpr,
                                                      DB_DIRTY_READ):
                    result = value.asDocument()
                    dv = self.getDocVersion(result)
                    if dv > ver:
                        ver = dv
                        doc = result

                if doc is not None:
                    value = XmlValue()
                    if (doc.getMetaData('', 'deleted', value) and
                        value.asString() == 'True'):
                        doc = None

                return doc

            raise ValueError, "dbxml %s not supported" %(self.version)

        finally:
            if txnStarted:
                store._abortTransaction()

    def loadRoots(self, version):

        ctx = XmlQueryContext()
        ctx.setReturnType(XmlQueryContext.ResultDocuments)
        ctx.setEvaluationType(XmlQueryContext.Lazy)
        ctx.setVariableValue("uuid", XmlValue(Repository.ROOT_ID.str64()))
        ctx.setVariableValue("version", XmlValue(float(version)))
        nameExp = re.compile("<name>(.*)</name>")
        roots = {}
        store = self.store
        view = store.repository.view
        txnStarted = False

        try:
            txnStarted = store._startTransaction()
            if self.version == "1.2.0":
                for value in self._xml.queryWithXPath(store.txn,
                                                      "/item[container=$uuid and number(@version)<=$version]",
                                                      ctx, DB_DIRTY_READ):
                    doc = value.asDocument()
                    xml = doc.getContent()
                    match = nameExp.match(xml, xml.index("<name>"))
                    name = match.group(1)

                    if not name in view._roots:
                        ver = self.getDocVersion(doc)
                        if not name in roots or ver > roots[name][0]:
                            roots[name] = (ver, doc)
            else:
                raise ValueError, "dbxml %s not supported" %(self.version)

        finally:
            if txnStarted:
                store._abortTransaction()

        value = XmlValue()
        for name, (ver, doc) in roots.iteritems():
            if (doc.getMetaData('', 'deleted', value) and
                value.asString() == 'True'):
                continue
            if not name in view._roots:
                view._loadDoc(doc)

    def queryItems(self, version, query):

        store = self.store
        txnStarted = False

        docs = {}
        try:
            txnStarted = store._startTransaction()
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
                store._abortTransaction()

        results = []
        for uuid, (doc, ver) in docs.iteritems():
            # verify that match version is latest,
            # if not it is out of date for the view
            if store._versions.getDocVersion(uuid, version) == ver:
                results.append(doc)

        return results

    def deleteDocument(self, doc):

        self._xml.deleteDocument(self.store.txn, doc, self.store.updateCtx)

    def putDocument(self, doc):

        return self._xml.putDocument(self.store.txn, doc, self.store.updateCtx)

    def close(self):

        self._xml.close()
        self._xml = None

    def parseDoc(self, doc, handler):

        string = doc.getContent()
        ctx = libxml2.createPushParser(handler, string, len(string), "doc")
        ctx.parseChunk('', 0, 1)
            
    def getDocUUID(self, doc):

        xml = doc.getContent()
        index = xml.index('uuid=') + 6

        return UUID(xml[index:xml.index('"', index)])

    def getDocVersion(self, doc):

        xml = doc.getContent()
        index = xml.index('version=', xml.index('version=') + 9) + 9

        return long(xml[index:xml.index('"', index)])


class XMLStore(Store):

    def __init__(self, repository):

        self._threaded = ThreadLocal()
        super(XMLStore, self).__init__(repository)
        
    def open(self, create=False):

        txnStarted = False
        
        try:
            txnStarted = self._startTransaction()
            txn = self.txn
                
            self._data = XMLContainer(self, "__data__", txn, create)
            self._refs = RefContainer(self, "__refs__", txn, create)
            self._versions = VerContainer(self, "__versions__", txn, create)
            self._history = HistContainer(self, "__history__", txn, create)
            self._text = FileContainer(self, "__text__", txn, create)
            self._binary = FileContainer(self, "__binary__", txn, create)
            self._blocks = BlockContainer(self, "__blocks__", txn, create)
            self._index = IndexContainer(self, "__index__", txn, create)
        finally:
            if txnStarted:
                self._commitTransaction()

    def close(self):

        self._data.close()
        self._refs.close()
        self._versions.close()
        self._history.close()
        self._text.close()
        self._binary.close()
        self._index.close()
        self._blocks.close()

    def loadItem(self, version, uuid):

        return self._data.loadItem(version, uuid)
    
    def loadChild(self, version, uuid, name):

        return self._data.loadChild(version, uuid, name)

    def loadRoots(self, version):

        self._data.loadRoots(version)

    def loadRef(self, version, uItem, uuid, key):

        return self._refs.loadRef(version, key, "".join((uItem._uuid,
                                                         uuid._uuid,
                                                         key._uuid)))

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

    def _startTransaction(self):

        if self.txn is None:
            self.txn = self.repository._env.txn_begin(None, DB_DIRTY_READ)
            return True

        return False

    def _commitTransaction(self):

        if self.txn is not None:
            self.txn.commit()
            self.txn = None
            return True

        return False

    def _abortTransaction(self):

        if self.txn is not None:
            self.txn.abort()
            self.txn = None
            return True

        return False

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

    def _getContainerExpr(self):

        try:
            return self._threaded.containerExpr
        except AttributeError:
            xml = self._data._xml
            xpath = "/item[container=$uuid and name=$name and number(@version)<=$version]"
            containerExpr = xml.parseXPathExpression(None, xpath, self.ctx)
            self._threaded.containerExpr = containerExpr

            return containerExpr

    
    env = property(_getEnv)
    ctx = property(_getCtx)
    updateCtx = property(_getUpdateCtx)
    containerExpr = property(_getContainerExpr)
    txn = property(_getTxn, _setTxn)
