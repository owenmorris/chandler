
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO, xml.sax.saxutils

from datetime import datetime
from struct import pack, unpack

from bsddb.db import DBLockDeadlockError, DBNotFoundError
from bsddb.db import DB_DIRTY_READ, DB_LOCK_WRITE
from dbxml import XmlQueryContext, XmlUpdateContext, XmlDocument

from repository.item.Item import Item
from repository.item.ItemRef import RefDict, TransientRefDict
from repository.persistence.Repository import Repository
from repository.persistence.Repository import OnDemandRepositoryView
from repository.util.UUID import UUID


class XMLRepositoryView(OnDemandRepositoryView):

    def __init__(self, repository):

        super(XMLRepositoryView, self).__init__(repository)

        self._log = []
        self.version = self.repository.call('_versions', 'getVersion', self)

    def _startTransaction(self):

        return False

    def _abortTransaction(self):

        return False

    def getRoots(self):
        'Return a list of the roots in the repository.'

        self.repository.call('_store', 'loadRoots', self)
        return super(XMLRepositoryView, self).getRoots()

    def logItem(self, item):
        
        if super(XMLRepositoryView, self).logItem(item):
            self._log.append(item)
            return True
        
        return False

    def dirlog(self):

        for item in self._log:
            print item.getItemPath()

    def cancel(self):

        self._abortTransaction()

        for item in self._log:
            if item.isDeleted():
                del self._deletedRegistry[item.getUUID()]
                item._status &= ~Item.DELETED
            else:
                item.setDirty(False)
                item._unloadItem()

        del self._log[:]


class XMLRepositoryLocalView(XMLRepositoryView):

    def __init__(self, repository):

        self._txn = None
        super(XMLRepositoryLocalView, self).__init__(repository)

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
            xpath = "/item[container=$uuid and name=$name and number(@version)<=$version]"
            self._containerExpr = xml.parseXPathExpression(None, xpath,
                                                           self.ctx)
            return self._containerExpr

    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return XMLRefDict(self, item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)

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

        while True:
            try:
                self._txn = repository._env.txn_begin(None, DB_DIRTY_READ)

                newVersion = versions.getVersion(self)
                if count > 0:
                    lock = env.lock_get(env.lock_id(),
                                        self.ROOT_ID._uuid,
                                        DB_LOCK_WRITE)
                    newVersion += 1
                    versions.put(self, self.ROOT_ID._uuid,
                                 pack('>l', ~newVersion))
                
                    store = repository._store
                    for item in self._log:
                        self._saveItem(item, newVersion,
                                       store, versions, history, verbose)

            except DBLockDeadlockError:
                print 'restarting commit aborted by deadlock'
                if self._txn:
                    self._txn.abort()
                    self._txn = None
                if lock:
                    env.lock_put(lock)
                    lock = None

                continue
            
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
                return

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


class XMLRepositoryClientView(XMLRepositoryView):
    pass


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

        while True:
            cursor = None
            txnStarted = False
            try:
                txnStarted = view._startTransaction()
                cursor = view.repository._refs.cursor(view)

                try:
                    cursorKey = self._packKey(key)
                    value = cursor.set_range(cursorKey)

                except DBLockDeadlockError:
                    print 'restarting _loadRef aborted by deadlock'
                    if cursor:
                        cursor.close()
                    if txnStarted:
                        view._abortTransaction()

                    continue

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

                    return None

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
