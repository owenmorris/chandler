
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, re, libxml2

from datetime import datetime
from struct import pack, unpack
from threading import currentThread

from repository.util.UUID import UUID
from repository.util.ThreadLocal import ThreadLocal
from repository.persistence.Repository import Repository, RepositoryError
from repository.persistence.Repository import OnDemandRepository, Store
from repository.persistence.XMLRepositoryView import XMLRepositoryLocalView
from repository.persistence.XMLRepositoryView import XMLRepositoryClientView

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
            if docId is not None:
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
            if self.version == "1.1.0":
                results = self._xml.queryWithXPath(store.txn,
                                                   "/item[container=$uuid and name=$name and number(@version)<=$version]",
                                                   ctx, DB_DIRTY_READ)
                try:
                    while True:
                        result = results.next(store.txn).asDocument()
                        dv = self.getDocVersion(result)
                        if dv > ver:
                            ver = dv
                            doc = result
                except StopIteration:
                    return doc

            if self.version == "1.1.1":
                for value in self._xml.queryWithXPathExpression(store.txn,
                                                                self.store.containerExpr,
                                                                DB_DIRTY_READ):
                    result = value.asDocument()
                    dv = self.getDocVersion(result)
                    if dv > ver:
                        ver = dv
                        doc = result

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
            if self.version == "1.1.0":
                results = self._xml.queryWithXPath(store.txn,
                                                   "/item[container=$uuid and number(@version)<=$version]",
                                                   ctx, DB_DIRTY_READ)
                try:
                    while True:
                        doc = results.next(store.txn).asDocument()
                        xml = doc.getContent()
                        match = nameExp.match(xml, xml.index("<name>"))
                        name = match.group(1)

                        if not name in view._roots:
                            ver = self.getDocVersion(doc)
                            if not name in roots or ver > roots[name][0]:
                                roots[name] = (ver, doc)
                except StopIteration:
                    pass

            elif self.version == "1.1.1":
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

        for name, (ver, doc) in roots.iteritems():
            if not name in view._roots:
                view._loadDoc(doc)

    def queryItems(self, version, query):

        store = self.store
        txnStarted = False

        docs = {}
        try:
            txnStarted = store._startTransaction()
            for value in self._xml.queryWithXPath(store.txn, query, store.ctx,
                                                  DB_DIRTY_READ):
                doc = value.asDocument()
                ver = self.getDocVersion(doc)
                if ver <= version:
                    uuid = self.getDocUUID(doc)
                    dv = docs.get(uuid, None)
                    if dv is not None and dv[1] < ver or dv is None:
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


class DBContainer(object):

    def __init__(self, store, name, txn, create):

        super(DBContainer, self).__init__()

        self.store = store
        self._db = DB(store.env)
        self._filename = name
            
        if create:
            self._db.open(filename = name, dbtype = DB_BTREE,
                          flags = DB_CREATE | DB_DIRTY_READ | DB_THREAD,
                          txn = txn)
        else:
            self._db.open(filename = name, dbtype = DB_BTREE,
                          flags = DB_DIRTY_READ | DB_THREAD,
                          txn = txn)

    def close(self):

        self._db.close()
        self._db = None

    def put(self, key, value):

        self._db.put(key, value, txn=self.store.txn)

    def delete(self, key):

        try:
            self._db.delete(key, txn=self.store.txn)
        except DBNotFoundError:
            pass

    def get(self, key):

        return self._db.get(key, txn=self.store.txn)

    def cursor(self):

        return self._db.cursor(txn=self.store.txn)


class RefContainer(DBContainer):

    def loadRef(self, version, key, cursorKey):

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store._startTransaction()
                cursor = self.cursor()

                try:
                    value = cursor.set_range(cursorKey)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    print 'restarting loadRef aborted by deadlock'
                    continue

                while value is not None and value[0].startswith(cursorKey):
                    refVer = ~unpack('>l', value[0][48:52])[0]
                
                    if refVer <= version:
                        value = value[1]
                        offset = 0

                        len, uuid = self._readValue(value, offset)
                        offset += len
                    
                        if uuid is None:
                            return None

                        else:
                            len, previous = self._readValue(value, offset)
                            offset += len

                            len, next = self._readValue(value, offset)
                            offset += len

                            len, alias = self._readValue(value, offset)
                            offset += len

                            return (key, uuid, previous, next, alias)

                    else:
                        value = cursor.next()

                return None

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store._abortTransaction()
        
    def _readValue(self, value, offset):

        code = value[offset]
        offset += 1

        if code == '\0':
            return (17, UUID(value[offset:offset+16]))

        if code == '\1':
            len, = unpack('>H', value[offset:offset+2])
            offset += 2
            return (len + 3, value[offset:offset+len])

        if code == '\2':
            return (1, None)

        raise ValueError, code

    # has to run within the commit() transaction
    def deleteItem(self, item):

        cursor = None
            
        try:
            cursor = self._db.cursor(txn=self.store.txn)
            key = item.getUUID()._uuid

            try:
                val = cursor.set_range(key)
                while val is not None and val[0].startswith(key):
                    cursor.delete()
                    val = cursor.next()
            except DBNotFoundError:
                pass

        finally:
            if cursor is not None:
                cursor.close()


class VerContainer(DBContainer):

    def __init__(self, store, name, txn, create):

        super(VerContainer, self).__init__(store, name, txn, create)
        if create:
            self._db.put(Repository.ROOT_ID._uuid, pack('>l', ~0), txn)

    def getVersion(self):

        return ~unpack('>l', self.get(Repository.ROOT_ID._uuid))[0]

    def setDocVersion(self, uuid, version, docId):

        self.put(pack('>16sl', uuid._uuid, ~version), pack('>l', docId))

    def getDocVersion(self, uuid, version=0):

        cursor = None
        txnStarted = False
        try:
            txnStarted = self.store._startTransaction()
            cursor = self.cursor()
                
            try:
                key = uuid._uuid
                value = cursor.set_range(key)
            except DBNotFoundError:
                return None

            while True:
                if value[0].startswith(key):
                    docVersion = ~unpack('>l', value[0][16:20])[0]
                    if version == 0 or docVersion <= version:
                        return docVersion
                else:
                    return None

                value = cursor.next()

        finally:
            if cursor:
                cursor.close()
            if txnStarted:
                self.store._abortTransaction()

    def getDocId(self, uuid, version):

        cursor = None
        txnStarted = False
        try:
            txnStarted = self.store._startTransaction()
            cursor = self.cursor()

            try:
                key = uuid._uuid
                value = cursor.set_range(key)
            except DBNotFoundError:
                return None

            else:
                while value is not None and value[0].startswith(key):
                    docVersion = ~unpack('>l', value[0][16:20])[0]

                    if docVersion <= version:
                        return unpack('>l', value[1])[0]
                        
                    value = cursor.next()
                        
                return None

        finally:
            if cursor:
                cursor.close()
            if txnStarted:
                self.store._abortTransaction()

    def deleteVersion(self, uuid):

        self.delete(uuid._uuid)


class HistContainer(DBContainer):

    def writeVersion(self, uuid, version, docId, dirty):

        self.put(pack('>l16s', version, uuid._uuid), pack('>li', docId, dirty))

    # has to run within the commit transaction
    def apply(self, fn, oldVersion, newVersion):

        cursor = self.cursor()

        try:
            value = cursor.set_range(pack('>l', oldVersion + 1))
        except DBNotFoundError:
            return

        try:
            while value is not None:
                version, uuid = unpack('>l16s', value[0])
                if version > newVersion:
                    break

                fn(UUID(uuid), version, unpack('>li', value[1]))
                value = cursor.next()
        finally:
            cursor.close()



class TextContainer(DBContainer):
    pass


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
            self._text = TextContainer(self, "__text__", txn, create)
        finally:
            if txnStarted:
                self._commitTransaction()

    def close(self):

        self._data.close()
        self._refs.close()
        self._versions.close()
        self._history.close()
        self._text.close()

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
