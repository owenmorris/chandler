
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO

from datetime import datetime
from struct import pack

from bsddb.db import DBLockDeadlockError, DBNotFoundError
from bsddb.db import DB_DIRTY_READ, DB_LOCK_WRITE
from dbxml import XmlDocument, XmlValue

from repository.item.Item import Item
from repository.item.ItemRef import RefDict, TransientRefDict
from repository.persistence.Repository import Repository, RepositoryError
from repository.persistence.Repository import VersionConflictError
from repository.persistence.Repository import OnDemandRepositoryView
from repository.persistence.Repository import RepositoryNotifications
from repository.util.UUID import UUID
from repository.util.SAX import XMLGenerator
from repository.util.Lob import Text, Binary
from repository.util.Streams import ConcatenatedInputStream, NullInputStream


class XMLRepositoryView(OnDemandRepositoryView):

    def __init__(self, repository):

        super(XMLRepositoryView, self).__init__(repository)

        self._log = []
        self._notifications = RepositoryNotifications(repository)
        
    def getRoots(self, load=True):
        'Return a list of the roots in the repository.'

        if load:
            self.repository.store.loadRoots(self.version)
            
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

        for item in self._log:
            if item.isDeleted():
                del self._deletedRegistry[item.getUUID()]
                item._status &= ~Item.DELETED
            else:
                item.setDirty(0)
                item._unloadItem()

        del self._log[:]

    def queryItems(self, query, load=True):

        store = self.repository.store
        items = []
        
        for doc in store.queryItems(self.version, query):
            uuid = store.getDocUUID(doc)
            if not uuid in self._deletedRegistry:
                items.append(self.find(uuid, load=load and doc))

        return items


class XMLRepositoryLocalView(XMLRepositoryView):

    def __init__(self, repository):

        super(XMLRepositoryLocalView, self).__init__(repository)
        self._indexWriter = None
        
    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return XMLRefDict(self, item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)

    def getLobType(self, mode):

        if mode == 'text':
            return XMLText
        if mode == 'binary':
            return XMLBinary

        raise ValueError, mode

    def _startTransaction(self):

        return self.repository.store._startTransaction()

    def _commitTransaction(self):

        if self._indexWriter is not None:
            self.repository.store._index.optimizeIndex(self._indexWriter)
            self._indexWriter.close()
            self._indexWriter = None
            
        self.repository.store._commitTransaction()

    def _abortTransaction(self):

        if self._indexWriter is not None:
            self._indexWriter.close()
            self._indexWriter = None
            
        self.repository.store._abortTransaction()

    def _getIndexWriter(self):

        if self._indexWriter is None:
            store = self.repository.store
            if store.txn is None:
                raise RepositoryError, "Can't index outside transaction"
            self._indexWriter = store._index.getIndexWriter()

        return self._indexWriter

    def commit(self):

        repository = self.repository
        store = repository.store
        data = store._data
        versions = store._versions
        history = store._history
        env = repository._env

        self._notifications.clear()

        before = datetime.now()
        count = len(self._log)
        size = 0L
        txnStarted = False
        lock = None
        
        while True:
            try:
                txnStarted = self._startTransaction()

                newVersion = versions.getVersion()
                if count > 0:
                    lock = env.lock_get(env.lock_id(), self.ROOT_ID._uuid,
                                        DB_LOCK_WRITE)
                    newVersion += 1
                    versions.put(self.ROOT_ID._uuid, pack('>l', ~newVersion))

                    ood = {}
                    for item in self._log:
                        if not item.isNew():
                            uuid = item._uuid
                            version = versions.getDocVersion(uuid)
                            assert version is not None
                            if version > item._version:
                                ood[uuid] = item

                    if ood:
                        self._mergeItems(ood, self.version, newVersion,
                                         history)
                
                    for item in self._log:
                        size += self._saveItem(item, newVersion,
                                               data, versions, history)

            except DBLockDeadlockError:
                self.logger.info('restarting commit aborted by deadlock')
                if txnStarted:
                    self._abortTransaction()
                if lock:
                    env.lock_put(lock)
                    lock = None

                continue
            
            except:
                self.logger.exception('aborting transaction (%ld bytes)', size)
                if txnStarted:
                    self._abortTransaction()
                if lock:
                    env.lock_put(lock)
                    lock = None

                raise

            else:
                if self._log:
                    for item in self._log:
                        item._setSaved(newVersion)
                    del self._log[:]

                self.logger.debug('refreshing view from version %d to %d',
                                  self.version, newVersion)

                if newVersion > self.version:
                    try:
                        oldVersion = self.version
                        self.version = newVersion

                        def unload(uuid, version, (docId, dirty)):
                            item = self._registry.get(uuid)
                            if item is not None and item._version < newVersion:
                                if self.isDebug():
                                    self.logger.debug('unloading version %d of %s',
                                                      item._version,
                                                      item.getItemPath())
                                item._unloadItem()
                            
                        history.apply(unload, oldVersion, newVersion)

                    except:
                        if txnStarted:
                            self._abortTransaction()
                        raise
            
                if txnStarted:
                    self._commitTransaction()

                if lock:
                    env.lock_put(lock)

                self._notifications.dispatch()

                if count > 0:
                    self.logger.info('%s committed %d items (%ld bytes) in %s',
                                     self, count, size,
                                     datetime.now() - before)
                return

    def _saveItem(self, item, newVersion, data, versions, history):

        uuid = item._uuid
        isNew = item.isNew()
        isDeleted = item.isDeleted()
        
        if isDeleted:
            del self._deletedRegistry[uuid]
            if isNew:
                return 0

        if self.isDebug():
            self.logger.debug('saving version %d of %s',
                              newVersion, item.getItemPath())

        out = cStringIO.StringIO()
        generator = XMLGenerator(out, 'utf-8')
        generator.startDocument()
        item._saveItem(generator, newVersion)
        generator.endDocument()
        content = out.getvalue()
        out.close()
        size = len(content)

        doc = XmlDocument()
        doc.setContent(content)
        if isDeleted:
            doc.setMetaData('', '', 'deleted', XmlValue('True'))
        docId = data.putDocument(doc)

        if isDeleted:
            versions.setDocVersion(uuid, newVersion, 0)
            history.writeVersion(uuid, newVersion, 0, item.getDirty())
            self._notifications.changed(item, 'deleted')

        else:
            versions.setDocVersion(uuid, newVersion, docId)
            history.writeVersion(uuid, newVersion, docId, item.getDirty())

            if isNew:
                self._notifications.changed(item, 'added')
            else:
                self._notifications.changed(item, 'changed')

        return size

    def _mergeItems(self, items, oldVersion, newVersion, history):

        def check(uuid, version, (docId, dirty)):
            item = items.get(uuid)
            if item is not None:
                if item.getDirty() & dirty:
                    raise VersionConflictError, item

        history.apply(check, oldVersion, newVersion)

        for item in items.itervalues():
            self.logger.info('Item %s is out of date but is mergeable',
                             item.getItemPath())
        raise NotImplementedError, 'item merging not yet implemented'


class XMLRepositoryClientView(XMLRepositoryView):

    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return XMLClientRefDict(self, item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)


class XMLRefDict(RefDict):

    class _log(list):

        def append(self, value):
            if len(self) == 0 or value != self[-1]:
                super(XMLRefDict._log, self).append(value)


    def __init__(self, view, item, name, otherName):
        
        self._log = XMLRefDict._log()
        self._item = None
        self._uuid = UUID()
        self.view = view
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

        return self._loadRef_(key)

    def _loadRef_(self, key):

        version = self._item._version
        cursorKey = self._packKey(key)

        return self.view.repository.store._refs.loadRef(version, key,
                                                        cursorKey)

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
            
        self.view.repository.store._refs.put(self._packKey(key, version),
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

    def _eraseRef(self, key):

        self.view.repository.store._refs.delete(self._packKey(key))

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

                else:
                    raise ValueError, entry[0]

            if self._log:
                self.view._notifications.changed(self._item, self._name)

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
            super(XMLRefDict, self)._xmlValues(generator, version, mode)

        else:
            raise ValueError, mode


class XMLClientRefDict(XMLRefDict):

    def _prepareKey(self, uItem, uuid):

        self._uItem = uItem
        self._uuid = uuid
            
    def _loadRef_(self, key):

        return self.view.repository.store.loadRef(self._item._version,
                                                  self._uItem, self._uuid, key)

    def _writeRef(self, key, version, uuid, previous, next, alias):
        raise NotImplementedError, "XMLClientRefDict._writeRef"


class XMLText(Text):

    def __init__(self, view, *args, **kwds):

        super(XMLText, self).__init__(*args, **kwds)

        self._uuid = None
        self._view = view
        self._version = 0
        self._indexed = False
        self._dirty = False
        
    def _xmlValue(self, view, generator):

        uuid = self.getUUID()
        store = view.repository.store
        
        if self._dirty:
            if self._append:
                out = store._text.appendFile(self._makeKey())
            else:
                self._version += 1
                out = store._text.createFile(self._makeKey())
            out.write(self._data)
            out.close()
            self._data = ''

            if self._indexed:
                store._index.indexDocument(view._getIndexWriter(),
                                           self.getReader(),
                                           self.getUUID(),
                                           self.getVersion())

        attrs = {}
        attrs['version'] = str(self._version)
        attrs['mimetype'] = self.mimetype
        attrs['encoding'] = self.encoding
        if self._compression:
            attrs['compression'] = self._compression
        attrs['type'] = 'uuid'
        if self._indexed:
            attrs['indexed'] = 'True'
        
        generator.startElement('text', attrs)
        generator.characters(uuid.str64())
        generator.endElement('text')

    def getUUID(self):

        if self._uuid is None:
            self._uuid = UUID()
            self._dirty = True

        return self._uuid

    def getVersion(self):

        return self._version

    def _makeKey(self):

        return pack('>16sl', self.getUUID()._uuid, ~self._version)

    def _textEnd(self, data, attrs):

        self.mimetype = attrs.get('mimetype', 'text/plain')
        self._compression = attrs.get('compression', None)
        self._version = long(attrs.get('version', '0'))
        self._indexed = attrs.get('indexed', 'False') == 'True'

        if attrs.has_key('encoding'):
            self._encoding = attrs['encoding']

        if attrs.get('type', 'text') == 'text':
            writer = self.getWriter()
            writer.write(data)
            writer.close()
        else:
            self._uuid = UUID(data)

    def _setData(self, data):

        super(XMLText, self)._setData(data)
        self._dirty = True

    def _getInputStream(self):

        if self._data:
            dataIn = super(XMLText, self)._getInputStream()
        else:
            dataIn = None

        text = self._view.repository.store._text
        key = self._makeKey()
        
        if dataIn is not None:
            if self._append:
                if text.fileExists(key):
                    return ConcatenatedInputStream(text.openFile(key), dataIn)
                else:
                    return dataIn
            else:
                return dataIn
        elif text.fileExists(key):
            return text.openFile(key)
        else:
            return NullInputStream()
        

class XMLBinary(Binary):

    def __init__(self, view, *args, **kwds):

        super(XMLBinary, self).__init__(*args, **kwds)

        self._uuid = None
        self._view = view
        self._version = 0
        self._dirty = False
        
    def _xmlValue(self, view, generator):

        uuid = self.getUUID()

        if self._dirty:
            if self._append:
                out = view.repository.store._binary.appendFile(self._makeKey())
            else:
                self._version += 1
                out = view.repository.store._binary.createFile(self._makeKey())
            out.write(self._data)
            out.close()

        attrs = {}
        attrs['version'] = str(self._version)
        attrs['mimetype'] = self.mimetype
        if self._compression:
            attrs['compression'] = self._compression
        attrs['type'] = 'uuid'
        
        generator.startElement('binary', attrs)
        generator.characters(uuid.str64())
        generator.endElement('binary')

    def getUUID(self):

        if self._uuid is None:
            self._uuid = UUID()
            self._dirty = True

        return self._uuid

    def getVersion(self):

        return self._version

    def _makeKey(self):

        return pack('>16sl', self._uuid._uuid, ~self._version)

    def _binaryEnd(self, data, attrs):

        self.mimetype = attrs.get('mimetype', 'text/plain')
        self._compression = attrs.get('compression', None)
        self._version = long(attrs.get('version', '0'))

        if attrs.get('type', 'binary') == 'binary':
            writer = self.getWriter()
            writer.write(data)
            writer.close()
        else:
            self._uuid = UUID(data)

    def _setData(self, data):

        super(XMLBinary, self)._setData(data)
        self._dirty = True

    def _getInputStream(self):

        if self._data:
            dataIn = super(XMLBinary, self)._getInputStream()
        else:
            dataIn = None

        binary = self._view.repository.store._binary
        key = self._makeKey()
        
        if dataIn is not None:
            if self._append:
                if binary.fileExists(key):
                    return ConcatenatedInputStream(binary.openFile(key),
                                                   dataIn)
                else:
                    return dataIn
            else:
                return dataIn
        elif binary.fileExists(key):
            return binary.openFile(key)
        else:
            return NullInputStream()
