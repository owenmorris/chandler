
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import UUIDext

from struct import pack, unpack

from repository.util.UUID import UUID
from repository.persistence.Repository import Repository

from bsddb.db import DB
from bsddb.db import DB_CREATE, DB_BTREE, DB_THREAD, DB_DIRTY_READ
from bsddb.db import DBNotFoundError, DBLockDeadlockError


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

        return self._db.get(key, txn=self.store.txn, flags=DB_DIRTY_READ)

    def cursor(self):

        return self._db.cursor(txn=self.store.txn, flags=DB_DIRTY_READ)

    def _logDL(self, n):

        self.store.repository.logger.info('detected deadlock: %d', n)


class RefContainer(DBContainer):
        
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

    def loadRef(self, version, key, cursorKey):

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store._startTransaction()
                cursor = self.cursor()

                try:
                    value = cursor.set_range(cursorKey, flags=DB_DIRTY_READ)
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
                    self.store._abortTransaction()
        
    # has to run within the commit() transaction
    def deleteItem(self, item):

        cursor = None
            
        try:
            cursor = self.cursor()
            key = item._uuid._uuid

            try:
                value = cursor.set_range(key, flags=DB_DIRTY_READ)
                while value is not None and value[0].startswith(key):
                    cursor.delete()
                    value = cursor.next()
            except DBNotFoundError:
                pass

        finally:
            if cursor is not None:
                cursor.close()


class VerContainer(DBContainer):

    def __init__(self, store, name, txn, create):

        super(VerContainer, self).__init__(store, name, txn, create)
        if create:
            self._db.put(Repository.itsUUID._uuid, pack('>l', ~0), txn)

    def getVersion(self):

        return ~unpack('>l', self.get(Repository.itsUUID._uuid))[0]

    def setDocVersion(self, uuid, version, docId):

        self.put(pack('>16sl', uuid._uuid, ~version), pack('>l', docId))

    def getDocVersion(self, uuid, version=0):

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store._startTransaction()
                cursor = self.cursor()
                
                try:
                    key = uuid._uuid
                    value = cursor.set_range(key, flags=DB_DIRTY_READ)
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
                    self.store._abortTransaction()

    def getDocId(self, uuid, version):

        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store._startTransaction()
                cursor = self.cursor()

                try:
                    key = uuid._uuid
                    value = cursor.set_range(key, flags=DB_DIRTY_READ)
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
                    self.store._abortTransaction()

    def deleteVersion(self, uuid):

        self.delete(uuid._uuid)


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
                                         flags=DB_DIRTY_READ)
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

    def writeName(self, key, name, version, uuid):

        if isinstance(name, unicode):
            name = name.encode('utf-8')
            
        if uuid is None:
            uuid = key

        self.put(pack('>16sll', key._uuid, UUIDext.hash(name), ~version),
                 uuid._uuid)

    def readName(self, key, name, version):

        if isinstance(name, unicode):
            name = name.encode('utf-8')

        cursorKey = pack('>16sl', key._uuid, UUIDext.hash(name))
            
        while True:
            txnStarted = False
            cursor = None

            try:
                txnStarted = self.store._startTransaction()
                cursor = self.cursor()
                
                try:
                    value = cursor.set_range(cursorKey, flags=DB_DIRTY_READ)
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
                            if value[1] == value[0][0:16]:    # removed name
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
                    self.store._abortTransaction()
