
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO

from struct import pack, unpack

from repository.item.Access import ACL, ACE
from repository.item.Item import Item
from chandlerdb.util.UUID import UUID, _uuid
from repository.persistence.Repository import Repository

from bsddb.db import DB
from bsddb.db import DB_CREATE, DB_BTREE, DB_THREAD, DB_DIRTY_READ
from bsddb.db import DBNotFoundError, DBLockDeadlockError


class DBContainer(object):

    def __init__(self, store, name, txn, **kwds):

        super(DBContainer, self).__init__()

        self.store = store
        self._db = DB(store.env)
        self._filename = name
        
        if kwds.get('ramdb', False):
            self._flags = 0
            name = None
            dbname = None
        else:
            self._flags = DB_DIRTY_READ
            dbname = kwds.get('dbname')

        if kwds.get('create', False):
            self._db.open(filename = name, dbname = dbname,
                          dbtype = DB_BTREE,
                          flags = DB_CREATE | DB_THREAD | self._flags,
                          txn = txn)
        else:
            self._db.open(filename = name, dbname = dbname, 
                          dbtype = DB_BTREE,
                          flags = DB_THREAD | self._flags,
                          txn = txn)

    def openIndex(self, name, dbname, txn, keyMethod, **kwds):

        if kwds.get('ramdb', False):
            name = None
            dbname = None

        index = DB(self.store.env)

        if kwds.get('create', False):
            index.open(filename = name, dbname = dbname,
                       dbtype = DB_BTREE,
                       flags = DB_CREATE | DB_THREAD | self._flags,
                       txn = txn)
        else:
            index.open(filename = name, dbname = dbname,
                       dbtype = DB_BTREE,
                       flags = DB_THREAD | self._flags,
                       txn = txn)

        self._db.associate(secondaryDB = index,
                           callback = keyMethod,
                           flags = 0,
                           txn = txn)

        return index

    def close(self):

        self._db.close()
        self._db = None

    def attachView(self, view):

        pass

    def detachView(self, view):

        pass

    def put(self, key, value):

        self._db.put(key, value, txn=self.store.txn)

    def delete(self, key):

        try:
            self._db.delete(key, txn=self.store.txn)
        except DBNotFoundError:
            pass

    def get(self, key):

        return self._db.get(key, txn=self.store.txn, flags=self._flags)

    def cursor(self, db=None):

        if db is None:
            db = self._db
            
        return db.cursor(txn=self.store.txn, flags=self._flags)

    def _logDL(self, n):

        self.store.repository.logger.info('detected deadlock: %d', n)

    def _readValue(self, value, offset):

        code = value[offset]
        offset += 1

        if code == '\0':
            return (1, None)

        if code == '\1':
            return (1, True)

        if code == '\2':
            return (1, False)

        if code == '\3':
            return (17, UUID(value[offset:offset+16]))

        if code == '\4':
            return (5, unpack('>l', value[offset:offset+4])[0])

        if code == '\5':
            l, = unpack('>H', value[offset:offset+2])
            offset += 2
            return (l + 3, value[offset:offset+l])

        raise ValueError, code

    def _writeUUID(self, buffer, value):

        if value is None:
            buffer.write('\0')
        else:
            buffer.write('\3')
            buffer.write(value._uuid)

    def _writeString(self, buffer, value):

        if value is None:
            buffer.write('\0')
        
        elif isinstance(value, str):
            buffer.write('\5')
            buffer.write(pack('>H', len(value)))
            buffer.write(value)

        elif isinstance(value, unicode):
            value = value.encode('utf-8')
            buffer.write('\5')
            buffer.write(pack('>H', len(value)))
            buffer.write(value)

        else:
            raise TypeError, type(value)

    def _writeBoolean(self, buffer, value):

        if value is True:
            buffer.write('\1')

        elif value is False:
            buffer.write('\2')
        
        else:
            raise TypeError, type(value)

    def _writeInteger(self, buffer, value):

        if value is None:
            buffer.write('\0')
        
        buffer.write('\4')
        buffer.write(pack('>l', value))

    def _writeValue(self, buffer, value):

        if value is None:
            buffer.write('\0')

        elif value is True or value is False:
            self._writeBoolean(buffer, value)

        elif isinstance(value, str) or isinstance(value, unicode):
            self._writeString(buffer, value)

        elif isinstance(value, int) or isinstance(value, long):
            self._writeInteger(buffer, value)

        elif isinstance(value, UUID):
            self._writeUUID(buffer, value)

        else:
            raise NotImplementedError, "value: %s, type: %s" %(value,
                                                               type(value))


class RefContainer(DBContainer):
        
    def __init__(self, store, name, txn, **kwds):

        super(RefContainer, self).__init__(store, name, txn,
                                           dbname = 'data', **kwds)

        self._history = self.openIndex(name, 'history', txn,
                                       self._historyKey, **kwds)

    def close(self):

        self._history.close()
        self._history = None

        super(RefContainer, self).close()

    def prepareKey(self, uItem, uuid):

        buffer = cStringIO.StringIO()
        buffer.write(uItem._uuid)
        buffer.write(uuid._uuid)

        return buffer
            
    def _packKey(self, buffer, key, version=None):

        buffer.truncate(32)
        buffer.seek(0, 2)
        buffer.write(key._uuid)
        if version is not None:
            buffer.write(pack('>l', ~version))

        return buffer.getvalue()

    def saveRef(self, keyBuffer, buffer, version, key, previous, next, alias):

        buffer.truncate(0)
        buffer.seek(0)

        self._writeUUID(buffer, previous)
        self._writeUUID(buffer, next)
        self._writeValue(buffer, alias)
        self.put(self._packKey(keyBuffer, key, version), buffer.getvalue())

    def _historyKey(self, key, value):

        # uItem, uCol, uRef, ~version -> uItem, version, uCol, uRef
        return pack('>16sl32s', key, ~unpack('>l', key[48:52])[0], key[16:48])

    def applyHistory(self, fn, uuid, oldVersion, newVersion):

        store = self.store
        
        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor(self._history)

                try:
                    value = cursor.set_range(pack('>16sl', uuid._uuid,
                                                  oldVersion + 1),
                                             flags=self._flags)
                except DBNotFoundError:
                    return
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(16)
                        continue
                    else:
                        raise

                try:
                    while value is not None:
                        uItem, version, uCol, uRef = unpack('>16sl16s16s',
                                                            value[0])
                        if version > newVersion or uItem != uuid._uuid:
                            break

                        fn(version, (UUID(uCol), UUID(uRef)),
                           self._readRef(value[1]))

                        value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(17)
                        continue
                    else:
                        raise

                return

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)

    def deleteRef(self, keyBuffer, buffer, version, key):

        buffer.truncate(0)
        buffer.seek(0)

        self._writeUUID(buffer, None)
        self.put(self._packKey(keyBuffer, key, version), buffer.getvalue())

    def eraseRef(self, buffer, key):

        self.delete(self._packKey(buffer, key))

    def _readRef(self, value):

        if len(value) == 1:   # deleted ref
            return None

        else:
            offset = 0

            l, previous = self._readValue(value, offset)
            offset += l

            l, next = self._readValue(value, offset)
            offset += l

            l, alias = self._readValue(value, offset)
            offset += l

            return (previous, next, alias)

    def loadRef(self, buffer, version, key):

        cursorKey = self._packKey(buffer, key)
        store = self.store

        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor()

                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(1)
                        continue
                    else:
                        raise

                try:
                    while value is not None and value[0].startswith(cursorKey):
                        refVer = ~unpack('>l', value[0][48:52])[0]
                
                        if refVer <= version:
                            return self._readRef(value[1])
                        else:
                            value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(2)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)

    # has to run within the commit transaction or it may deadlock
    def deleteItem(self, item):

        cursor = None
            
        try:
            cursor = self.cursor()
            key = item._uuid._uuid

            try:
                value = cursor.set_range(key, flags=self._flags)
                while value is not None and value[0].startswith(key):
                    cursor.delete()
                    value = cursor.next()
            except DBNotFoundError:
                pass

        finally:
            if cursor is not None:
                cursor.close()


class NamesContainer(DBContainer):

    def writeName(self, version, key, name, uuid):

        if name is None:
            raise ValueError, 'name is None'
        
        if isinstance(name, unicode):
            name = name.encode('utf-8')
            
        if uuid is None:
            uuid = key

        self.put(pack('>16sll', key._uuid, _uuid.hash(name), ~version),
                 uuid._uuid)

    def readName(self, version, key, name):

        if name is None:
            raise ValueError, 'name is None'
        
        if isinstance(name, unicode):
            name = name.encode('utf-8')

        cursorKey = pack('>16sl', key._uuid, _uuid.hash(name))
        store = self.store
        
        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor()
                
                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(8)
                        continue
                    else:
                        raise

                try:
                    while value is not None and value[0].startswith(cursorKey):
                        nameVer = ~unpack('>l', value[0][-4:])[0]
                
                        if nameVer <= version:
                            if value[1] == value[0][0:16]:    # deleted name
                                return None

                            return UUID(value[1])

                        else:
                            value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(9)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)

    def readNames(self, version, key):

        results = []
        cursorKey = key._uuid
        store = self.store
        
        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor()
                
                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return results
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(12)
                        continue
                    else:
                        raise

                currentHash = None
                
                try:
                    while value is not None and value[0].startswith(cursorKey):
                        nameHash, nameVer = unpack('>ll', value[0][-8:])
                
                        if nameHash != currentHash and ~nameVer <= version:
                            currentHash = nameHash

                            if value[1] != value[0][0:16]:    # !deleted name
                                results.append(UUID(value[1]))

                        value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(13)
                        continue
                    else:
                        raise

                return results

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)


class ACLContainer(DBContainer):

    def writeACL(self, version, key, name, acl):

        if name is None:
            key = pack('>16sll', key._uuid, 0, ~version)
        else:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            key = pack('>16sll', key._uuid, _uuid.hash(name), ~version)

        if acl is None:    # deleted acl
            value = pack('>l', 0)
        else:
            value = "".join([pack('>16sl', ace.pid._uuid, ace.perms)
                             for ace in acl])

        self.put(key, value)

    def readACL(self, version, key, name):

        if name is None:
            cursorKey = pack('>16sl', key._uuid, 0)
        else:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            cursorKey = pack('>16sl', key._uuid, _uuid.hash(name))

        store = self.store
        
        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor()
                
                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(10)
                        continue
                    else:
                        raise

                try:
                    while value is not None and value[0].startswith(cursorKey):
                        key, aces = value
                        aclVer = ~unpack('>l', key[-4:])[0]
                
                        if aclVer <= version:
                            if len(aces) == 4:    # deleted acl
                                return None

                            acl = ACL()
                            for i in xrange(0, len(aces), 20):
                                pid = UUID(aces[i:i+16])
                                perms = unpack('>l', aces[i+16:i+20])[0]
                                acl.append(ACE(pid, perms))

                            return acl
                        
                        else:
                            value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(11)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)


class IndexesContainer(DBContainer):

    def prepareKey(self, uuid):

        buffer = cStringIO.StringIO()
        buffer.write(uuid._uuid)

        return buffer
            
    def _packKey(self, buffer, key, version=None):

        buffer.truncate(16)
        buffer.seek(0, 2)
        buffer.write(key._uuid)
        if version is not None:
            buffer.write(pack('>l', ~version))

        return buffer.getvalue()

    def saveKey(self, keyBuffer, buffer, version, key, node):

        buffer.truncate(0)
        buffer.seek(0)

        if node is not None:
            level = node.getLevel()
            buffer.write(pack('b', node.getLevel()))
            buffer.write(pack('>l', node._entryValue))
            for lvl in xrange(1, level + 1):
                point = node.getPoint(lvl)
                self._writeUUID(buffer, point.prevKey)
                self._writeUUID(buffer, point.nextKey)
                buffer.write(pack('>l', point.dist))
        else:
            buffer.write('\0')
            
        self.put(self._packKey(keyBuffer, key, version), buffer.getvalue())

    def loadKey(self, index, keyBuffer, version, key):
        
        cursorKey = self._packKey(keyBuffer, key)
        store = self.store
        
        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor()

                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(14)
                        continue
                    else:
                        raise

                try:
                    while value is not None and value[0].startswith(cursorKey):
                        keyVer = ~unpack('>l', value[0][32:36])[0]
                
                        if keyVer <= version:
                            value = value[1]
                            level = unpack('b', value[0])[0]

                            if level == 0:
                                return None
                    
                            node = index._createNode(level)
                            node._entryValue = unpack('>l', value[1:5])[0]
                            offset = 5
                            
                            for lvl in xrange(1, level + 1):
                                point = node.getPoint(lvl)

                                l, prevKey = self._readValue(value, offset)
                                offset += l
                                l, nextKey = self._readValue(value, offset)
                                offset += l
                                dist = unpack('>l', value[offset:offset+4])[0]
                                offset += 4

                                point.prevKey = prevKey
                                point.nextKey = nextKey
                                point.dist = dist

                            return node
                        
                        else:
                            value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(15)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)


class ItemContainer(DBContainer):

    def __init__(self, store, name, txn, **kwds):

        super(ItemContainer, self).__init__(store, name, txn,
                                            dbname = 'data', **kwds)

        self._index = self.openIndex(name, 'index', txn, 
                                     self._indexKey, **kwds)
        self._versions = self.openIndex(name, 'versions', txn,
                                        self._versionKey, **kwds)

    def close(self):

        self._index.close()
        self._index = None
        self._versions.close()
        self._versions = None

        super(ItemContainer, self).close()

    def _indexKey(self, key, value):

        # uItem, ~version -> uKind, uItem, ~version
        return pack('>16s20s', value[0:16], key)

    def _versionKey(self, key, value):

        # uItem, ~version -> version, uItem
        uuid, version = unpack('>16sl', key)

        return pack('>l16s', ~version, uuid)

    def saveItem(self, buffer, uItem, version, uKind, status,
                 uParent, name, moduleName, className,
                 values, dirtyValues, dirtyRefs):

        buffer.truncate(0)
        buffer.seek(0)

        buffer.write(uKind._uuid)
        buffer.write(pack('>l', status))
        buffer.write(uParent._uuid)

        self._writeString(buffer, name)
        self._writeString(buffer, moduleName)
        self._writeString(buffer, className)

        buffer.write(pack('>l', len(values)))
        for uValue in values:
            buffer.write(uValue._uuid)

        count = 0
        for name in dirtyValues:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            buffer.write(pack('>l', _uuid.hash(name)))
            count += 1
        for name in dirtyRefs:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            buffer.write(pack('>l', _uuid.hash(name)))
            count += 1
        buffer.write(pack('>l', count))

        self.put(pack('>16sl', uItem._uuid, ~version), buffer.getvalue())

    def _readItem(self, itemVer, value):

        uKind = UUID(value[0:16])
        status, = unpack('>l', value[16:20])
        uParent = UUID(value[20:36])
        
        offset = 36
        l, name = self._readValue(value, offset)
        offset += l
        l, moduleName = self._readValue(value, offset)
        offset += l
        l, className = self._readValue(value, offset)
        offset += l

        count, = unpack('>l', value[offset:offset+4])
        offset += 4
        values = []
        for i in xrange(count):
            values.append(UUID(value[offset:offset+16]))
            offset += 16

        return (itemVer, uKind, status, uParent, name,
                moduleName, className, values)

    def _findItem(self, version, uuid):

        key = uuid._uuid
        store = self.store

        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor()

                try:
                    value = cursor.set_range(key, flags=self._flags)
                except DBNotFoundError:
                    return None, None
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(20)
                        continue
                    else:
                        raise

                try:
                    while value is not None and value[0].startswith(key):
                        itemVer = ~unpack('>l', value[0][16:20])[0]
                
                        if itemVer <= version:
                            return itemVer, value[1]
                        else:
                            value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(21)
                        continue
                    else:
                        raise

                return None, None

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)

    def loadItem(self, version, uuid):

        version, item = self._findItem(version, uuid)
        if item is not None:
            return self._readItem(version, item)

        return None

    def getItemParentId(self, version, uuid):

        version, item = self._findItem(version, uuid)
        if item is not None:
            return UUID(item[20:36])

        return None

    def getItemVersion(self, version, uuid):

        version, item = self._findItem(version, uuid)
        if item is not None:
            return version

        return None

    def kindQuery(self, version, uuid, fn):

        store = self.store
        
        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor(self._index)

                try:
                    value = cursor.set_range(uuid._uuid,
                                             flags=self._flags)
                except DBNotFoundError:
                    return
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(22)
                        continue
                    else:
                        raise

                try:
                    lastItem = None
                    while value is not None:
                        uKind, uItem, vItem = unpack('>16s16sl', value[0])
                        if uKind != uuid._uuid:
                            break

                        vItem = ~vItem
                        if vItem <= version and uItem != lastItem:
                            args = self._readItem(vItem, value[1])
                            if not fn(UUID(uItem), *args):
                                break
                            else:
                                lastItem = uItem

                        value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(23)
                        continue
                    else:
                        raise

                return

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)

    def applyHistory(self, fn, oldVersion, newVersion):

        store = self.store
        
        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction()
                cursor = self.cursor(self._versions)

                try:
                    value = cursor.set_range(pack('>l', oldVersion + 1),
                                             flags=self._flags)
                except DBNotFoundError:
                    return
                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(18)
                        continue
                    else:
                        raise

                try:
                    while value is not None:
                        version, uuid = unpack('>l16s', value[0])
                        if version > newVersion:
                            break

                        value = value[1]
                        status, parentId = unpack('>l16s', value[16:36])

                        if status & Item.DELETED:
                            dirties = HashTuple()
                        else:
                            pos = -(unpack('>l', value[-4:])[0] + 1) << 2
                            value = value[pos:-4]
                            dirties = unpack('>%dl' %(len(value) >> 2), value)
                            dirties = HashTuple(dirties)

                        fn(UUID(uuid), version, status, UUID(parentId), dirties)

                        value = cursor.next()

                except DBLockDeadlockError:
                    if txnStatus & store.TXNSTARTED:
                        self._logDL(19)
                        continue
                    else:
                        raise

                return

            finally:
                if cursor is not None:
                    cursor.close()
                store.abortTransaction(txnStatus)


class ValueContainer(DBContainer):

    def __init__(self, store, name, txn, **kwds):

        super(ValueContainer, self).__init__(store, name, txn,
                                             dbname = 'data', **kwds)

        if kwds.get('ramdb', False):
            name = None
            dbname = None
        else:
            dbname = 'index'

        self._index = DB(store.env)

        if kwds.get('create', False):
            self._index.open(filename = name, dbname = dbname,
                             dbtype = DB_BTREE,
                             flags = DB_CREATE | DB_THREAD | self._flags,
                             txn = txn)
        else:
            self._index.open(filename = name, dbname = dbname,
                             dbtype = DB_BTREE,
                             flags = DB_THREAD | self._flags,
                             txn = txn)

        self._db.associate(secondaryDB = self._index,
                           callback = self._indexKey,
                           flags = 0,
                           txn = txn)

        if kwds.get('create', False):
            self.setVersion(0)

    def close(self):

        self._index.close()
        self._index = None

        super(ValueContainer, self).close()

    def _indexKey(self, key, value):

        # uValue -> uAttr, uValue
        return pack('>16s16s', value[0:16], key)

    def saveValue(self, buffer, uItem, version, uAttr, uValue, value):

        buffer.truncate(0)
        buffer.seek(0)

        buffer.write(uAttr._uuid)
        buffer.write(uItem._uuid)
        buffer.write(pack('>l', ~version))
        buffer.write(value)

        self.put(uValue._uuid, buffer.getvalue())

    def loadValue(self, uValue):

        value = self.get(uValue._uuid)
        if value is not None:
            return value[36:]

        return None

    def getVersionInfo(self, uuid):

        value = self.get(uuid._uuid)
        if value is None:
            return None

        uuid, version = unpack('>16sl', value)

        return UUID(uuid), version
        
    def getVersion(self, uuid=None):

        if uuid is None:
            uuid = Repository.itsUUID

        value = self.get(uuid._uuid)
        if value is None:
            return None

        return unpack('>l', value[16:])[0]
        
    def setVersion(self, version, uuid=None):
        
        if uuid is None:
            uuid = Repository.itsUUID

        if version != 0:
            versionId = self.get(uuid._uuid)[0:16]
        else:
            versionId = UUID()._uuid

        self.put(uuid._uuid, pack('>16sl', versionId, version))

    def setVersionId(self, versionId, uuid):

        version = self.getVersion(uuid)
        self.put(uuid._uuid, pack('>16sl', versionId._uuid, version))


class HashTuple(tuple):

    def __contains__(self, name):

        if isinstance(name, unicode):
            name = name.encode('utf-8')

        return super(HashTuple, self).__contains__(_uuid.hash(name))
