
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, re, cStringIO, xml.sax.saxutils

from xml.sax import parseString
from datetime import datetime
from struct import pack, unpack
from sys import exc_info

from model.util.UUID import UUID
from model.item.Item import Item
from model.item.ItemRef import ItemRef, ItemStub, RefDict, TransientRefDict
from model.persistence.Repository import OnDemandRepository, Store
from model.persistence.Repository import RepositoryError

from bsddb.db import DBEnv, DB, DBError
from bsddb.db import DB_CREATE, DB_BTREE, DB_TXN_NOWAIT
from bsddb.db import DB_RECOVER, DB_RECOVER_FATAL
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
        self._transaction = []
        
    def create(self, verbose=False, notxn=False):

        if not self.isOpen():
            super(XMLRepository, self).create(verbose)
            self._notxn = notxn
            self._create()
            self._status |= self.OPEN

    def _create(self):

        if not os.path.exists(self.dbHome):
            os.makedirs(self.dbHome)
        elif not os.path.isdir(self.dbHome):
            raise ValueError, "%s exists but is not a directory" %(self.dbHome)
        else:
            def purge(arg, path, names):
                for f in names:
                    if f.startswith('__') or f.startswith('log.'):
                        f = os.path.join(path, f)
                        if not os.path.isdir(f):
                            os.remove(f)
            os.path.walk(self.dbHome, purge, None)
        
        self._env = DBEnv()
        if self._notxn:
            self._env.open(self.dbHome, DB_CREATE | DB_INIT_MPOOL, 0)
        else:
            self._env.open(self.dbHome, self.OPEN_FLAGS, 0)

        self._openDb(True)

    def open(self, verbose=False, create=False, notxn=False):

        if not self.isOpen():
            super(XMLRepository, self).open(verbose)
            self._notxn = notxn
            self._env = DBEnv()

            try:
                if self._notxn:
                    self._env.open(self.dbHome, DB_INIT_MPOOL, 0)
                    self._openDb(False)

                else:
                    try:
                        before = datetime.now()
                        self._env.open(self.dbHome,
                                       DB_RECOVER | self.OPEN_FLAGS, 0)
                        after = datetime.now()
                        print 'opened db with recovery in %s' %(after - before)
                        self._openDb(False)

                    except DBRunRecoveryError:
                        before = datetime.now()
                        self._env.open(self.dbHome,
                                       DB_RECOVER_FATAL | self.OPEN_FLAGS, 0)
                        after = datetime.now()
                        print 'opened db with fatal recovery in %s' %(after -
                                                                      before)
                        self._openDb(False)

            except DBNoSuchFileError:
                if create:
                    self._create()
                else:
                    raise

            self._status |= self.OPEN

    def _openDb(self, create):

        try:
            if self._notxn:
                txn = None
            else:
                txn = self._env.txn_begin(None, DB_DIRTY_READ | DB_TXN_NOWAIT)
                
            self._refs = XMLRepository.refContainer(self._env, "__refs__",
                                                    txn, create)
            self._store = XMLRepository.xmlContainer(self._env, "__data__",
                                                     txn, create)
        finally:
            if txn:
                txn.commit()

    def close(self, purge=False):

        if self.isOpen():
            self._refs.close()
            self._store.close()
            self._env.close()
            self._env = None
            self._status &= ~self.OPEN

    def purge(self):
        pass

    def getRoots(self):
        'Return a list of the roots in the repository.'

        self._store.loadroots(self)
        return super(XMLRepository, self).getRoots()

    def commit(self, purge=False):

        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        before = datetime.now()
        count = 0
        
        try:
            if not self._notxn:
                txn = self._env.txn_begin(None, DB_DIRTY_READ | DB_TXN_NOWAIT)
                self._store.txnStarted(self._env, txn)
                self._refs.txnStarted(self._env, txn)
            else:
                txn = None

            if self._transaction:
                count = len(self._transaction)
                for item in self._transaction:
                    self._saveItem(item, container = self._store,
                                   verbose = self.verbose)
                    item.setDirty(False)
                del self._transaction[:]

        except DBError:
            if txn:
                txn.abort()
                self._store.txnEnded(self._env, txn)
                self._refs.txnEnded(self._env, txn)
            raise

        else:
            if txn:
                txn.commit()
                self._store.txnEnded(self._env, txn)
                self._refs.txnEnded(self._env, txn)
            after = datetime.now()
            print 'committed %d items in %s' %(count, after - before)

    def _saveItem(self, item, **args):

        container = args['container']
        uuid = item.getUUID()
        oldDoc = container.loadItem(uuid)
        if oldDoc is not None:
            container.deleteDocument(oldDoc)

        if item.isDeleted():
            if args.get('verbose'):
                print 'Removing', item.getItemPath()
            del self._deletedRegistry[uuid]
            self._refs.deleteItem(item)

        else:
            if args.get('verbose'):
                print 'Saving', item.getItemPath()

            out = cStringIO.StringIO()
            generator = xml.sax.saxutils.XMLGenerator(out, 'utf-8')
            generator.startDocument()
            item._saveItem(generator)
            generator.endDocument()

            doc = XmlDocument()
            doc.setContent(out.getvalue())
            out.close()
            container.putDocument(doc)
            
    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return XMLRefDict(self, item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)

    def addTransaction(self, item):

        if not self.isOpen():
            raise RepositoryError, 'Repository is not open'

        if not self.isLoading():
            self._transaction.append(item)
            return True
        
        return False

    OPEN_FLAGS = DB_CREATE | DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_TXN

    class xmlContainer(Store):

        def __init__(self, env, name, txn, create):

            super(XMLRepository.xmlContainer, self).__init__()
        
            self._xml = XmlContainer(env, name)
            self._txn = None
            self._filename = name
            
            if create:
                self._xml.open(txn, DB_CREATE | DB_DIRTY_READ)
                self._xml.addIndex(txn, "", "uuid",
                                   "node-attribute-equality-string")
                self._xml.addIndex(txn, "", "kind",
                                   "node-element-equality-string")
                self._xml.addIndex(txn, "", "container",
                                   "node-element-equality-string")
                self._xml.addIndex(txn, "", "name",
                                   "node-element-equality-string")
            else:
                self._xml.open(txn, DB_DIRTY_READ)

            self._ctx = XmlQueryContext()
            self._ctx.setReturnType(XmlQueryContext.ResultDocuments)
            self._ctx.setEvaluationType(XmlQueryContext.Lazy)
            self._updateCtx = XmlUpdateContext(self._xml)

        def txnStarted(self, env, txn):

            self._txn = txn

        def txnEnded(self, env, txn):

            self._txn = None

        def loadItem(self, uuid):

            self._ctx.setVariableValue("uuid", XmlValue(uuid.str64()))
            results = self._xml.queryWithXPath(self._txn,
                                               "/item[@uuid=$uuid]",
                                               self._ctx, DB_DIRTY_READ)
            try:
                return results.next(self._txn).asDocument()
            except StopIteration:
                return None
            
        def loadChild(self, uuid, name):

            self._ctx.setVariableValue("name", XmlValue(name.encode('utf-8')))
            self._ctx.setVariableValue("uuid", XmlValue(uuid.str64()))
            results = self._xml.queryWithXPath(self._txn,
                                               "/item[container=$uuid and name=$name]",
                                               self._ctx, DB_DIRTY_READ)
            try:
                return results.next(self._txn).asDocument()
            except StopIteration:
                return None

        def loadroots(self, repository):

            ctx = XmlQueryContext()
            ctx.setReturnType(XmlQueryContext.ResultDocuments)
            ctx.setEvaluationType(XmlQueryContext.Lazy)
            ctx.setVariableValue("uuid", XmlValue(repository.ROOT_ID.str64()))
            nameExp = re.compile("<name>(.*)</name>")
            results = self._xml.queryWithXPath(self._txn,
                                               "/item[container=$uuid]",
                                               ctx, DB_DIRTY_READ)
            try:
                while True:
                    xml = results.next(self._txn).asDocument()
                    xmlString = xml.getContent()
                    match = nameExp.match(xmlString, xmlString.index("<name>"))
                    name = match.group(1)

                    if not name in repository._roots:
                        repository._loadXML(xml)
            except StopIteration:
                pass

        def deleteDocument(self, doc):

            self._xml.deleteDocument(self._txn, doc, self._updateCtx)

        def putDocument(self, doc):

            self._xml.putDocument(self._txn, doc, self._updateCtx)

        def close(self):

            self._xml.close()
            self._xml = None

        def parseXML(self, xml, handler):

            parseString(xml.getContent(), handler)
            
        def getUUID(self, xml):

            xmlString = xml.getContent()
            index = xmlString.index('uuid=') + 6

            return UUID(xmlString[index:xmlString.index('"', index)])


    class refContainer(object):

        def __init__(self, env, name, txn, create):

            super(XMLRepository.refContainer, self).__init__()
        
            self._db = DB(env)
            self._txn = None
            self._filename = name
            
            if create:
                self._db.open(filename = name, dbtype = DB_BTREE,
                              flags = DB_CREATE | DB_DIRTY_READ,
                              txn = txn)
            else:
                self._db.open(filename = name, dbtype = DB_BTREE,
                              flags = DB_DIRTY_READ,
                              txn = txn)

        def txnStarted(self, env, txn):

            self._txn = txn
            
        def txnEnded(self, env, txn):

            self._txn = None
            
        def close(self):

            self._db.close()
            self._db = None

        def put(self, key, value):

            self._db.put(key, value, txn=self._txn)

        def delete(self, key):

            try:
                self._db.delete(key, txn=self._txn)
            except DBNotFoundError:
                pass

        def get(self, key):

            return self._db.get(key, txn=self._txn)

        def cursor(self):

            return self._db.cursor(txn=self._txn)

        def deleteItem(self, item):

            try:
                cursor = self._db.cursor(txn=self._txn)
                key = item.getUUID()._uuid

                try:
                    val = cursor.set_range(key)
                    while val is not None and val[0].startswith(key):
                        cursor.delete()
                        val = cursor.next()
                except DBNotFoundError:
                    pass

            finally:
                cursor.close()


class XMLRefDict(RefDict):

    class _log(list):

        def append(self, value):
            if len(self) == 0 or value != self[-1]:
                super(XMLRefDict._log, self).append(value)


    def __init__(self, repository, item, name, otherName):
        
        self._log = XMLRefDict._log()
        self._item = None
        self._uuid = UUID()
        self._repository = repository
        self._deletedRefs = {}
        
        super(XMLRefDict, self).__init__(item, name, otherName)

    def _getRepository(self):

        return self._repository

    def _loadRef(self, key):

        if key in self._deletedRefs:
            return None

        self._key.truncate(32)
        self._key.seek(0, 2)
        self._key.write(key._uuid)

        value = self._repository._refs.get(self._key.getvalue())
        if value is None:
            return None

        self._value.truncate(0)
        self._value.seek(0)
        self._value.write(value)
        self._value.seek(0)
        uuid = UUID(self._value.read(16))
        previous = self._readValue()
        next = self._readValue()
        alias = self._readValue()
        
        return (key, uuid, previous, next, alias)

    def _changeRef(self, key):

        if not self._repository.isLoading():
            self._log.append((0, key))
        
        super(XMLRefDict, self)._changeRef(key)

    def _removeRef(self, key, _detach=False):

        if not self._repository.isLoading():
            self._log.append((1, key))
            self._deletedRefs[key] = key
        else:
            raise ValueError, 'detach during load'

        super(XMLRefDict, self)._removeRef(key, _detach)

    def _writeRef(self, key, uuid, previous, next, alias):

        self._key.truncate(32)
        self._key.seek(0, 2)
        self._key.write(key._uuid)

        self._value.truncate(0)
        self._value.seek(0)
        self._value.write(uuid._uuid)
        self._writeValue(previous)
        self._writeValue(next)
        self._writeValue(alias)
        value = self._value.getvalue()
            
        self._repository._refs.put(self._key.getvalue(), value)

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

        self._key.truncate(32)
        self._key.seek(0, 2)
        self._key.write(key._uuid)

        self._repository._refs.delete(self._key.getvalue())

    def _dbRefs(self):

        self._key.truncate(32)
        cursor = self._repository._refs.cursor()

        try:
            key = self._key.getvalue()
            val = cursor.set_range(key)
        except DBNotFoundError:
            val = None
            
        while val is not None and val[0].startswith(key):
            refName = UUID(val[0][32:])

            self._value.truncate(0)
            self._value.seek(0)
            self._value.write(val[1])
            self._value.seek(0)
            uuid = UUID(self._value.read(16))
            previous = self._readValue()
            next = self._readValue()
            alias = self._readValue()
            yield (refName, uuid, previous, next, alias)
                
            val = cursor.next()

        cursor.close()

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, 'Item is already set'
        
        self._item = item
        if item is not None:
            self._prepareKey(item._uuid, self._uuid)

    def _prepareKey(self, uItem, uuid):

        self._uuid = uuid

        self._key = cStringIO.StringIO()
        self._key.write(uItem._uuid)
        self._key.write(uuid._uuid)

        self._value = cStringIO.StringIO()
            
    def _xmlValues(self, generator, mode):

        if mode == 'save':
            for entry in self._log:
                try:
                    value = self._get(entry[1])
                except KeyError:
                    value = None
    
                if entry[0] == 0:
                    if value is not None:
                        ref = value._value
                        alias = value._alias
                        previous = value._previousKey
                        next = value._nextKey
    
                        uuid = ref.other(self._item).getUUID()
                        self._writeRef(entry[1], uuid, previous, next, alias)
                        
                elif entry[0] == 1:
                    self._eraseRef(entry[1])

                else:
                    raise ValueError, entry[0]
    
            del self._log[:]
            self._deletedRefs.clear()
            
            if len(self) > 0:
                generator.startElement('db', {})
                generator.characters(self._uuid.str64())
                generator.endElement('db')

        elif mode == 'serialize':
            super(XMLRefDict, self)._xmlValues(generator, mode)

        else:
            raise ValueError, mode
