
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, re, cStringIO, xml.sax.saxutils

from xml.sax import parseString
from datetime import datetime
from struct import pack, unpack
from sys import exc_info
from threading import currentThread

from repository.util.UUID import UUID
from repository.item.Item import Item
from repository.item.ItemRef import ItemRef, ItemStub
from repository.item.ItemRef import RefDict, TransientRefDict
from repository.persistence.Repository import Repository, RepositoryError
from repository.persistence.Repository import OnDemandRepository, Store
from repository.persistence.Repository import OnDemandRepositoryView

from bsddb.db import DBEnv, DB, DBError
from bsddb.db import DB_CREATE, DB_BTREE, DB_LOCK_WRITE, DB_THREAD
from bsddb.db import DB_RECOVER, DB_RECOVER_FATAL, DB_LOCK_YOUNGEST
from bsddb.db import DB_INIT_MPOOL, DB_INIT_LOCK, DB_INIT_TXN, DB_DIRTY_READ
from bsddb.db import DBRunRecoveryError, DBNoSuchFileError, DBNotFoundError
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
        self._ctx = XmlQueryContext()
        
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

        self._openDb(True)

    def _createEnv(self):

        env = DBEnv()
        env.set_lk_detect(DB_LOCK_YOUNGEST)

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

                self._openDb(False)

            except DBNoSuchFileError:
                if create:
                    self._create()
                else:
                    raise

            self._status |= self.OPEN

    def _openDb(self, create):

        txn = None
        
        try:
            txn = self._env.txn_begin(None, DB_DIRTY_READ)
                
            self._refs = XMLRepository.refContainer(self, "__refs__",
                                                    txn, create)
            self._versions = XMLRepository.verContainer(self, "__versions__",
                                                        txn, create)
            self._history = XMLRepository.histContainer(self, "__history__",
                                                        txn, create)
            self._store = XMLRepository.xmlContainer(self, "__data__",
                                                     txn, create)
        finally:
            if txn is not None:
                txn.commit()

    def close(self, purge=False):

        if self.isOpen():
            self._refs.close()
            self._versions.close()
            self._history.close()
            self._store.close()
            self._env.close()
            self._env = None
            self._status &= ~self.OPEN

    def _createView(self):

        return XMLRepositoryView(self)

    OPEN_FLAGS = DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_TXN | DB_THREAD

    class xmlContainer(Store):

        def __init__(self, repository, name, txn, create):

            super(XMLRepository.xmlContainer, self).__init__()
        
            self.repository = repository
            self._xml = XmlContainer(repository._env, name)
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
            else:
                self._xml.open(txn, DB_DIRTY_READ | DB_THREAD)

        def loadItem(self, view, uuid):

            txnStarted = False
            try:
                txnStarted = view._startTransaction()
                docId = view.repository._versions.getDocId(view, uuid,
                                                           view.version)
                if docId is not None:
                    return self._xml.getDocument(view._txn, docId,
                                                 DB_DIRTY_READ)
            finally:
                if txnStarted:
                    view._abortTransaction()

            return None
            
        def loadChild(self, view, uuid, name):

            view.ctx.setVariableValue("name", XmlValue(name.encode('utf-8')))
            view.ctx.setVariableValue("uuid", XmlValue(uuid.str64()))
            view.ctx.setVariableValue("version", XmlValue(float(view.version)))

            doc = None
            ver = 0
            txnStarted = False

            try:
                txnStarted = view._startTransaction()
                if self.version == "1.1.0":
                    results = self._xml.queryWithXPath(view._txn,
                                                       "/item[container=$uuid and name=$name and number(@version)<=$version]",
                                                       view.ctx, DB_DIRTY_READ)
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
                                                                    view.containerExpr,
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

            self._xml.deleteDocument(view._txn, doc, view.updateCtx)

        def putDocument(self, view, doc):

            return self._xml.putDocument(view._txn, doc, view.updateCtx)

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

    class dbContainer(object):

        def __init__(self, repository, name, txn, create):

            super(XMLRepository.dbContainer, self).__init__()

            self.repository = repository
            self._db = DB(repository._env)
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

    class refContainer(dbContainer):

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

    class verContainer(dbContainer):

        def __init__(self, repository, name, txn, create):

            super(XMLRepository.verContainer, self).__init__(repository, name,
                                                             txn, create)
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

    class histContainer(dbContainer):

        def __init__(self, repository, name, txn, create):

            super(XMLRepository.histContainer, self).__init__(repository, name,
                                                              txn, create)
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


class XMLRepositoryView(OnDemandRepositoryView):

    def __init__(self, repository):

        super(XMLRepositoryView, self).__init__(repository)

        self._log = []
        self._txn = None
        self.version = repository._versions.getVersion(self)

    def _getCtx(self):

        try:
            return self._ctx

        except AttributeError:
            self._ctx = XmlQueryContext()
            self._ctx.setReturnType(XmlQueryContext.ResultDocuments)
            self._ctx.setEvaluationType(XmlQueryContext.Lazy)

            return self._ctx

    def _getUpdateCtx(self):

        try:
            return self._updateCtx

        except AttributeError:
            self._updateCtx = XmlUpdateContext(self.repository._store._xml)

            return self._updateCtx

    def _getUUIDExpr(self):

        try:
            return self._uuidExpr
        except AttributeError:
            xml = self.repository._store._xml
            xpath = "/item[@uuid=$uuid]"
            self._uuidExpr = xml.parseXPathExpression(None, xpath,
                                                      self.ctx)
            return self._uuidExpr

    def _getContainerExpr(self):

        try:
            return self._containerExpr
        except AttributeError:
            xml = self.repository._store._xml
#            xpath = "/item[container=$uuid and name=$name]"
            xpath = "/item[container=$uuid and name=$name and number(@version)<=$version]"
            self._containerExpr = xml.parseXPathExpression(None, xpath,
                                                           self.ctx)
            return self._containerExpr

    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return XMLRefDict(self, item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)

    def getRoots(self):
        'Return a list of the roots in the repository.'

        self.repository._store.loadRoots(self)
        return super(XMLRepositoryView, self).getRoots()

    def logItem(self, item):
        
        if super(XMLRepositoryView, self).logItem(item):
            self._log.append(item)
            return True
        
        return False

    def dirlog(self):

        for item in self._log:
            print item.getItemPath()

    def _startTransaction(self):

        if self._txn is None:
            self._txn = self.repository._env.txn_begin(None, DB_DIRTY_READ)
            return True

        return False

    def _abortTransaction(self):

        if self._txn is not None:
            self._txn.abort()
            self._txn = None
            return True

        return False

    def commit(self):

        repository = self.repository
        verbose = repository.verbose
        versions = repository._versions
        env = repository._env
        history = repository._history

        before = datetime.now()
        count = len(self._log)
        lock = None
        
        try:
            self._txn = repository._env.txn_begin(None, DB_DIRTY_READ)

            newVersion = versions.getVersion(self)
            if count > 0:
                lock = env.lock_get(env.lock_id(), Repository.ROOT_ID._uuid,
                                    DB_LOCK_WRITE)
                newVersion += 1
                versions.put(self, Repository.ROOT_ID._uuid,
                             pack('>l', ~newVersion))
            
                store = repository._store
                for item in self._log:
                    self._saveItem(item, newVersion, store, versions, history,
                                   verbose)

        except:
            if self._txn:
                self._txn.abort()
                self._txn = None
            if lock:
                env.lock_put(lock)

            raise

        else:
            if self._log:
                for item in self._log:
                    item._setSaved(newVersion)
                del self._log[:]

            if verbose:
                print 'refreshing view from version %d to %d' %(self.version,
                                                                newVersion)

            if newVersion > self.version:
                try:
                    oldVersion = self.version
                    self.version = newVersion

                    for uuid in history.uuids(self, oldVersion, newVersion):
                        item = self._registry.get(uuid)
                        if item is not None and item._version < newVersion:
                            if verbose:
                                print 'unloading version %d of %s' %(item._version,
                                                                     item.getItemPath())
                            item._unloadItem()
                except:
                    if self._txn:
                        self._txn.abort()
                        self._txn = None
                    raise
            
            if self._txn:
                self._txn.commit()
                self._txn = None

            if lock:
                env.lock_put(lock)

            if count > 0:
                print 'committed %d items in %s' %(count,
                                                   datetime.now() - before)

    def cancel(self):

        for item in self._log:
            if item.isDeleted():
                del self._deletedRegistry[item.getUUID()]
                item._status &= ~Item.DELETED
            else:
                item.setDirty(False)
                item._unloadItem()

        del self._log[:]

    def _saveItem(self, item, newVersion, store, versions, history, verbose):

        uuid = item.getUUID()
        if item.isNew():
            version = None

        else:
            version = versions.getDocVersion(self, uuid)
            if version is None:
                raise ValueError, 'no version for %s' %(item.getItemPath())
            elif version > item._version:
                raise ValueError, '%s is out of date' %(item.getItemPath())

        if item.isDeleted():

            del self._deletedRegistry[uuid]
            if version is not None:
                if verbose:
                    print 'Removing version %d of %s' %(item._version,
                                                        item.getItemPath())
                versions.setDocVersion(self, uuid, newVersion, 0)
                history.writeVersion(self, uuid, newVersion, 0)

        else:
            if verbose:
                print 'Saving version %d of %s' %(item._version,
                                                  item.getItemPath())

            out = cStringIO.StringIO()
            generator = xml.sax.saxutils.XMLGenerator(out, 'utf-8')
            generator.startDocument()
            item._saveItem(generator, newVersion)
            generator.endDocument()

            doc = XmlDocument()
            doc.setContent(out.getvalue())
            out.close()
            docId = store.putDocument(self, doc)
            versions.setDocVersion(self, uuid, newVersion, docId)
            history.writeVersion(self, uuid, newVersion, docId)
            
    ctx = property(_getCtx)
    updateCtx = property(_getUpdateCtx)
    uuidExpr = property(_getUUIDExpr)
    containerExpr = property(_getContainerExpr)
    

class XMLRefDict(RefDict):

    class _log(list):

        def append(self, value):
            if len(self) == 0 or value != self[-1]:
                super(XMLRefDict._log, self).append(value)


    def __init__(self, repository, item, name, otherName):
        
        self._log = XMLRefDict._log()
        self._item = None
        self._uuid = UUID()
        self.view = repository
        self._deletedRefs = {}
        
        super(XMLRefDict, self).__init__(item, name, otherName)

    def _getRepository(self):

        return self.view

    def _loadRef(self, key):

        view = self.view

        if view is not view.repository.view:
            raise RepositoryError, 'current thread is not owning thread'

        if key in self._deletedRefs:
            return None

        cursor = None
        txnStarted = False
        try:
            txnStarted = view._startTransaction()
            cursor = view.repository._refs.cursor(view)

            try:
                cursorKey = self._packKey(key)
                value = cursor.set_range(cursorKey)
            except DBNotFoundError:
                return None
            else:
                version = self._item._version
                while value is not None and value[0].startswith(cursorKey):
                    refVer = ~unpack('>l', value[0][48:52])[0]

                    if refVer <= version:
                        self._value.truncate(0)
                        self._value.seek(0)
                        self._value.write(value[1])
                        self._value.seek(0)
                        uuid = self._readValue()

                        if uuid is None:
                            return None

                        else:
                            previous = self._readValue()
                            next = self._readValue()
                            alias = self._readValue()
        
                            return (key, uuid, previous, next, alias)

                    else:
                        value = cursor.next()

        finally:
            if cursor:
                cursor.close()
            if txnStarted:
                view._abortTransaction()

    def _changeRef(self, key):

        if not self.view.isLoading():
            self._log.append((0, key))
        
        super(XMLRefDict, self)._changeRef(key)

    def _removeRef(self, key, _detach=False):

        if not self.view.isLoading():
            self._log.append((1, key))
            self._deletedRefs[key] = key
        else:
            raise ValueError, 'detach during load'

        super(XMLRefDict, self)._removeRef(key, _detach)

    def _writeRef(self, key, version, uuid, previous, next, alias):

        self._value.truncate(0)
        self._value.seek(0)
        if uuid is not None:
            self._writeValue(uuid)
            self._writeValue(previous)
            self._writeValue(next)
            self._writeValue(alias)
        else:
            self._writeValue(None)
        value = self._value.getvalue()
            
        self.view.repository._refs.put(self.view, self._packKey(key, version),
                                       value)

    def _writeValue(self, value):
        
        if isinstance(value, UUID):
            self._value.write('\0')
            self._value.write(value._uuid)

        elif isinstance(value, str) or isinstance(value, unicode):
            self._value.write('\1')
            self._value.write(pack('>H', len(value)))
            self._value.write(value)

        elif value is None:
            self._value.write('\2')

        else:
            raise NotImplementedError, "value: %s, type: %s" %(value,
                                                               type(value))

    def _readValue(self):

        code = self._value.read(1)

        if code == '\0':
            return UUID(self._value.read(16))

        if code == '\1':
            len, = unpack('>H', self._value.read(2))
            return self._value.read(len)

        if code == '\2':
            return None

        raise ValueError, code

    def _eraseRef(self, key):

        self.view.repository._refs.delete(self.view, self._packKey(key))

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, 'Item is already set'
        
        self._item = item
        if item is not None:
            self._prepareKey(item._uuid, self._uuid)

    def _packKey(self, key, version=None):

        self._key.truncate(32)
        self._key.seek(0, 2)
        self._key.write(key._uuid)
        if version is not None:
            self._key.write(pack('>l', ~version))

        return self._key.getvalue()

    def _prepareKey(self, uItem, uuid):

        self._uuid = uuid

        self._key = cStringIO.StringIO()
        self._key.write(uItem._uuid)
        self._key.write(uuid._uuid)

        self._value = cStringIO.StringIO()
            
    def _xmlValues(self, generator, version, mode):

        if mode == 'save':
            for entry in self._log:
                try:
                    value = self._get(entry[1])
                except KeyError:
                    value = None
    
                if entry[0] == 0:
                    if value is not None:
                        ref = value._value
                        previous = value._previousKey
                        next = value._nextKey
                        alias = value._alias
    
                        uuid = ref.other(self._item).getUUID()
                        self._writeRef(entry[1], version,
                                       uuid, previous, next, alias)
                        
                elif entry[0] == 1:
                    self._writeRef(entry[1], version, None, None, None, None)
#                    self._eraseRef(entry[1])

                else:
                    raise ValueError, entry[0]
    
            del self._log[:]
            self._deletedRefs.clear()
            
            if len(self) > 0:
                if self._aliases:
                    for key, value in self._aliases.iteritems():
                        generator.startElement('alias', { 'name': key })
                        generator.characters(value.str64())
                        generator.endElement('alias')
                generator.startElement('db', {})
                generator.characters(self._uuid.str64())
                generator.endElement('db')

        elif mode == 'serialize':
            super(XMLRefDict, self)._xmlValues(generator, mode)

        else:
            raise ValueError, mode
