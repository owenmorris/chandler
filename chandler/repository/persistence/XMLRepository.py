
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, re, xml.sax.saxutils

from xml.sax import parseString
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
        
    def create(self, verbose=False):

        if not self.isOpen():
            super(XMLRepository, self).create(verbose)
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

    def open(self, verbose=False, create=False, recover=False):

        if not self.isOpen():
            super(XMLRepository, self).open(verbose)
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

    def loadItem(self, view, uuid):

        txnStarted = False
        try:
            txnStarted = view._startTransaction()
            docId = self.store._versions.getDocId(view, uuid, view.version)
            if docId is not None:
                return self._xml.getDocument(view._txn, docId, DB_DIRTY_READ)
        finally:
            if txnStarted:
                view._abortTransaction()

        return None
            
    def loadChild(self, view, uuid, name):

        ctx = self.store.ctx
        ctx.setVariableValue("name", XmlValue(name.encode('utf-8')))
        ctx.setVariableValue("uuid", XmlValue(uuid.str64()))
        ctx.setVariableValue("version", XmlValue(float(view.version)))

        doc = None
        ver = 0
        txnStarted = False

        try:
            txnStarted = view._startTransaction()
            if self.version == "1.1.0":
                results = self._xml.queryWithXPath(view._txn,
                                                   "/item[container=$uuid and name=$name and number(@version)<=$version]",
                                                   ctx, DB_DIRTY_READ)
                try:
                    while True:
                        result = results.next(view._txn).asDocument()
                        dv = self.getDocVersion(result)
                        if dv > ver:
                            ver = dv
                            doc = result
                except StopIteration:
                    return doc

            if self.version == "1.1.1":
                for value in self._xml.queryWithXPathExpression(view._txn,
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
                view._abortTransaction()

    def loadRoots(self, view):

        ctx = XmlQueryContext()
        ctx.setReturnType(XmlQueryContext.ResultDocuments)
        ctx.setEvaluationType(XmlQueryContext.Lazy)
        ctx.setVariableValue("uuid", XmlValue(Repository.ROOT_ID.str64()))
        ctx.setVariableValue("version", XmlValue(float(view.version)))
        nameExp = re.compile("<name>(.*)</name>")
        roots = {}
        txnStarted = False

        try:
            txnStarted = view._startTransaction()
            if self.version == "1.1.0":
                results = self._xml.queryWithXPath(view._txn,
                                                   "/item[container=$uuid and number(@version)<=$version]",
                                                   ctx, DB_DIRTY_READ)
                try:
                    while True:
                        doc = results.next(view._txn).asDocument()
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
                for value in self._xml.queryWithXPath(view._txn,
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
                view._abortTransaction()

        for name, (ver, doc) in roots.iteritems():
            if not name in view._roots:
                view._loadDoc(doc)

    def deleteDocument(self, view, doc):

        self._xml.deleteDocument(view._txn, doc, self.store.updateCtx)

    def putDocument(self, view, doc):

        return self._xml.putDocument(view._txn, doc, self.store.updateCtx)

    def close(self):

        self._xml.close()
        self._xml = None

    def parseDoc(self, doc, handler):

        parseString(doc.getContent(), handler)
            
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

    def put(self, view, key, value):

        self._db.put(key, value, txn=view._txn)

    def delete(self, view, key):

        try:
            self._db.delete(key, txn=view._txn)
        except DBNotFoundError:
            pass

    def get(self, view, key):

        return self._db.get(key, txn=view._txn)

    def cursor(self, view):

        return self._db.cursor(txn=view._txn)


class RefContainer(DBContainer):

    # has to run within the commit() transaction
    def deleteItem(self, view, item):

        cursor = None
            
        try:
            cursor = self._db.cursor(txn=view._txn)
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

    def getVersion(self, view):

        return ~unpack('>l', self.get(view, Repository.ROOT_ID._uuid))[0]

    def setDocVersion(self, view, uuid, version, docId):

        self.put(view, "%s%s" %(uuid._uuid, pack('>l', ~version)),
                 pack('>l', docId))

    def getDocVersion(self, view, uuid):

        cursor = None
        txnStarted = False
        try:
            txnStarted = view._startTransaction()
            cursor = self.cursor(view)
                
            try:
                key = uuid._uuid
                value = cursor.set_range(key)
            except DBNotFoundError:
                return None
            else:
                if value[0].startswith(key):
                    return ~unpack('>l', value[0][16:20])[0]
                return None
        finally:
            if cursor:
                cursor.close()
            if txnStarted:
                view._abortTransaction()

    def getDocId(self, view, uuid, version):

        cursor = None
        txnStarted = False
        try:
            txnStarted = view._startTransaction()
            cursor = self.cursor(view)

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
                view._abortTransaction()

    def deleteVersion(self, view, uuid):

        self.delete(view, uuid._uuid)


class HistContainer(DBContainer):

    def writeVersion(self, view, uuid, version, docId):

        self.put(view, "%s%s" %(pack('>l', version), uuid._uuid),
                 pack('>l', docId))

    # has to run within the commit transaction
    def uuids(self, view, oldVersion, newVersion):

        cursor = self.cursor(view)

        try:
            value = cursor.set_range(pack('>l', oldVersion + 1))
        except DBNotFoundError:
            return

        while value is not None:
            version, = unpack('>l', value[0][0:4])
            if version > newVersion:
                break

            yield UUID(value[0][4:20])
            value = cursor.next()

        cursor.close()


class XMLStore(Store):

    def __init__(self, repository):

        super(XMLStore, self).__init__(repository)
        self._threaded = ThreadLocal()

    def open(self, create=False):

        txn = None
        
        try:
            txn = self.env.txn_begin(None, DB_DIRTY_READ)
                
            self._data = XMLContainer(self, "__data__", txn, create)
            self._refs = RefContainer(self, "__refs__", txn, create)
            self._versions = VerContainer(self, "__versions__", txn, create)
            self._history = HistContainer(self, "__history__", txn, create)
        finally:
            if txn:
                txn.commit()

    def close(self):

        self._data.close()
        self._refs.close()
        self._versions.close()
        self._history.close()

    def loadItem(self, view, uuid):

        return self._data.loadItem(view, uuid)
    
    def loadChild(self, view, uuid, name):

        return self._data.loadChild(view, uuid, name)

    def loadRoots(self, view):

        self._data.loadRoots(view)

    def parseDoc(self, doc, handler):

        self._data.parseDoc(doc, handler)

    def getDocUUID(self, doc):

        return self._data.getDocUUID(doc)

    def getDocVersion(self, doc):

        return self._data.getDocVersion(doc)

    def getVersion(self, view):

        return self._versions.getVersion(view)

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
