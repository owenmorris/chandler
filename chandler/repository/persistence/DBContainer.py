
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import UUIDext, cStringIO

from struct import pack, unpack

from repository.item.Access import ACL, ACE
from repository.util.UUID import UUID
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
        else:
            self._flags = DB_DIRTY_READ
            
        if kwds.get('create', False):
            self._db.open(filename = name, dbtype = DB_BTREE,
                          flags = DB_CREATE | DB_THREAD | self._flags,
                          txn = txn)
        else:
            self._db.open(filename = name, dbtype = DB_BTREE,
                          flags = DB_THREAD | self._flags,
                          txn = txn)

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

    def cursor(self):

        return self._db.cursor(txn=self.store.txn, flags=self._flags)

    def _logDL(self, n):

        self.store.repository.logger.info('detected deadlock: %d', n)


class RefContainer(DBContainer):
        
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

    def _readValue(self, value, offset):

        code = value[offset]
        offset += 1

        if code == '\0':
            return (17, UUID(value[offset:offset+16]))

        if code == '\1':
            l, = unpack('>H', value[offset:offset+2])
            offset += 2
            return (l + 3, value[offset:offset+l])

        if code == '\2':
            return (1, None)

        raise ValueError, code

    def _writeValue(self, buffer, value):
        
        if isinstance(value, UUID):
            buffer.write('\0')
            buffer.write(value._uuid)

        elif isinstance(value, str):
            buffer.write('\1')
            buffer.write(pack('>H', len(value)))
            buffer.write(value)

        elif isinstance(value, unicode):
            value = value.encode('utf-8')
            buffer.write('\1')
            buffer.write(pack('>H', len(value)))
            buffer.write(value)

        elif value is None:
            buffer.write('\2')

        else:
            raise NotImplementedError, "value: %s, type: %s" %(value,
                                                               type(value))

    def saveRef(self, keyBuffer, buffer, version, key, previous, next, alias):

        buffer.truncate(0)
        buffer.seek(0)

        self._writeValue(buffer, previous)
        self._writeValue(buffer, next)
        self._writeValue(buffer, alias)
        self.put(self._packKey(keyBuffer, key, version), buffer.getvalue())

    def deleteRef(self, keyBuffer, buffer, version, key):

        buffer.truncate(0)
        buffer.seek(0)

        self._writeValue(buffer, None)
        self.put(self._packKey(keyBuffer, key, version), buffer.getvalue())

    def eraseRef(self, buffer, key):

        self.delete(self._packKey(buffer, key))

    def loadRef(self, buffer, version, key):

        cursorKey = self._packKey(buffer, key)

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store.startTransaction()
                cursor = self.cursor()

                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStarted:
                        self._logDL(1)
                        continue
                    else:
                        raise

                try:
                    while value is not None and value[0].startswith(cursorKey):
                        refVer = ~unpack('>l', value[0][48:52])[0]
                
                        if refVer <= version:
                            value = value[1]

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

                        else:
                            value = cursor.next()

                except DBLockDeadlockError:
                    if txnStarted:
                        self._logDL(2)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store.abortTransaction()

    # has to run within the commit() transaction
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


class VerContainer(DBContainer):

    def __init__(self, store, name, txn, **kwds):

        super(VerContainer, self).__init__(store, name, txn, **kwds)
        if kwds.get('create', False):
            self._db.put(Repository.itsUUID._uuid, pack('>l', 0), txn)
            self._db.put(self.itsUUID._uuid, UUID()._uuid, txn)

    def getVersion(self, versionId=None):

        if versionId is None:
            versionId = Repository.itsUUID
            
        return unpack('>l', self.get(versionId._uuid))[0]

    def setVersion(self, version, versionId=None):
        
        if versionId is None:
            versionId = Repository.itsUUID
            
        self.put(versionId._uuid, pack('>l', version))

    def getVersionId(self, uuid=None):

        if uuid is None:
            uuid = self.itsUUID

        return UUID(self.get(uuid._uuid))

    def setVersionId(self, versionId, uuid):

        self.put(uuid._uuid, versionId._uuid)

    def setDocVersion(self, uuid, version, docId):

        self.put(pack('>16sl', uuid._uuid, ~version), pack('>l', docId))

    def getDocVersion(self, uuid, version=0):

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store.startTransaction()
                cursor = self.cursor()
                
                try:
                    key = uuid._uuid
                    value = cursor.set_range(key, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStarted:
                        self._logDL(6)
                        continue
                    else:
                        raise

                try:
                    while True:
                        if value[0].startswith(key):
                            docVersion = ~unpack('>l', value[0][16:20])[0]
                            if version == 0 or docVersion <= version:
                                return docVersion
                        else:
                            return None

                        value = cursor.next()

                except DBLockDeadlockError:
                    if txnStarted:
                        self._logDL(4)
                        continue
                    else:
                        raise

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store.abortTransaction()

    def getDocId(self, uuid, version):

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store.startTransaction()
                cursor = self.cursor()

                try:
                    key = uuid._uuid
                    value = cursor.set_range(key, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStarted:
                        self._logDL(7)
                        continue
                    else:
                        raise

                try:
                    while value is not None and value[0].startswith(key):
                        docVersion = ~unpack('>l', value[0][16:20])[0]

                        if docVersion <= version:
                            return unpack('>l', value[1])[0]
                        
                        value = cursor.next()

                except DBLockDeadlockError:
                    if txnStarted:
                        self._logDL(5)
                        continue
                    else:
                        raise
                        
                return None

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store.abortTransaction()

    def deleteVersion(self, uuid):

        self.delete(uuid._uuid)

    itsUUID = UUID('00e956cc-a609-11d8-fae2-000393db837c')


class HistContainer(DBContainer):

    def writeVersion(self, uuid, version, docId, status, parentId=None):

        if parentId is not None:
            value = pack('>li16s', docId, status, parentId._uuid)
        else:
            value = pack('>li', docId, status)
            
        self.put(pack('>l16s', version, uuid._uuid), value)

    # has to run within the commit transaction
    def apply(self, fn, oldVersion, newVersion):

        try:
            cursor = self.cursor()

            try:
                value = cursor.set_range(pack('>l', oldVersion + 1),
                                         flags=self._flags)
            except DBNotFoundError:
                return

            while value is not None:
                version, uuid = unpack('>l16s', value[0])
                if version > newVersion:
                    break

                if len(value[1]) == 24:
                    docId, status, parentId = unpack('>li16s', value[1])
                    parentId = UUID(parentId)
                else:
                    docId, status = unpack('>li', value[1])
                    parentId = None

                fn(UUID(uuid), version, docId, status, parentId)

                value = cursor.next()

        finally:
            cursor.close()


class NamesContainer(DBContainer):

    def writeName(self, version, key, name, uuid):

        if isinstance(name, unicode):
            name = name.encode('utf-8')
            
        if uuid is None:
            uuid = key

        self.put(pack('>16sll', key._uuid, UUIDext.hash(name), ~version),
                 uuid._uuid)

    def readName(self, version, key, name):

        if isinstance(name, unicode):
            name = name.encode('utf-8')

        cursorKey = pack('>16sl', key._uuid, UUIDext.hash(name))
            
        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store.startTransaction()
                cursor = self.cursor()
                
                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStarted:
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
                    if txnStarted:
                        self._logDL(9)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store.abortTransaction()

    def readNames(self, version, key):

        results = []
        cursorKey = key._uuid
            
        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store.startTransaction()
                cursor = self.cursor()
                
                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return results
                except DBLockDeadlockError:
                    if txnStarted:
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
                    if txnStarted:
                        self._logDL(13)
                        continue
                    else:
                        raise

                return results

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store.abortTransaction()


class ACLContainer(DBContainer):

    def writeACL(self, version, key, name, acl):

        if name is None:
            key = pack('>16sll', key._uuid, 0, ~version)
        else:
            if isinstance(name, unicode):
                name = name.encode('utf-8')
            key = pack('>16sll', key._uuid, UUIDext.hash(name), ~version)

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
            cursorKey = pack('>16sl', key._uuid, UUIDext.hash(name))

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store.startTransaction()
                cursor = self.cursor()
                
                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStarted:
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
                    if txnStarted:
                        self._logDL(11)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store.abortTransaction()


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

    def _readValue(self, value, offset):

        code = value[offset]
        offset += 1

        if code == '\0':
            return (17, UUID(value[offset:offset+16]))

        if code == '\1':
            return (1, None)

        raise ValueError, code

    def _writeValue(self, buffer, value):
        
        if isinstance(value, UUID):
            buffer.write('\0')
            buffer.write(value._uuid)

        elif value is None:
            buffer.write('\1')

        else:
            raise TypeError, "value: %s, type: %s" %(value, type(value))

    def saveKey(self, keyBuffer, buffer, version, key, node):

        buffer.truncate(0)
        buffer.seek(0)

        if node is not None:
            level = node.getLevel()
            buffer.write(pack('b', node.getLevel()))
            buffer.write(pack('>l', node._entryValue))
            for lvl in xrange(1, level + 1):
                point = node.getPoint(lvl)
                self._writeValue(buffer, point.prevKey)
                self._writeValue(buffer, point.nextKey)
                buffer.write(pack('>l', point.dist))
        else:
            buffer.write('\0')
            
        self.put(self._packKey(keyBuffer, key, version), buffer.getvalue())

    def loadKey(self, index, keyBuffer, version, key):
        
        cursorKey = self._packKey(keyBuffer, key)

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store.startTransaction()
                cursor = self.cursor()

                try:
                    value = cursor.set_range(cursorKey, flags=self._flags)
                except DBNotFoundError:
                    return None
                except DBLockDeadlockError:
                    if txnStarted:
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
                    if txnStarted:
                        self._logDL(15)
                        continue
                    else:
                        raise

                return None

            finally:
                if cursor:
                    cursor.close()
                if txnStarted:
                    self.store.abortTransaction()
