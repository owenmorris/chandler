
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, shutil, atexit, cStringIO

from threading import Thread, Lock, Condition, local, currentThread
from datetime import datetime
from struct import pack

from chandlerdb.util import lock
from chandlerdb.util.c import UUID
from chandlerdb.persistence.c import DBEnv, \
    DBNoSuchFileError, DBPermissionsError, DBInvalidArgError, \
    DBLockDeadlockError, \
    DB_VERSION_MAJOR, DB_VERSION_MINOR, DB_VERSION_PATCH

from repository.item.Item import Item
from repository.util.SAX import XMLGenerator
from repository.persistence.Repository import \
    Repository, OnDemandRepository, Store
from repository.persistence.RepositoryError import *
from repository.persistence.DBRepositoryView import DBRepositoryView
from repository.persistence.DBContainer import \
    DBContainer, RefContainer, NamesContainer, ACLContainer, IndexesContainer, \
    ItemContainer, ValueContainer
from repository.persistence.FileContainer import \
    FileContainer, BlockContainer, IndexContainer, LOBContainer
from repository.persistence.DBItemIO import DBItemReader, DBItemPurger
from repository.remote.CloudFilter import CloudFilter

DB_VERSION = DB_VERSION_MAJOR << 16 | DB_VERSION_MINOR << 8 | DB_VERSION_PATCH


class DBRepository(OnDemandRepository):
    """
    A Berkeley DB based repository.
    """

    def __init__(self, dbHome):
        """
        Construct an DBRepository giving it a DB container pathname
        """
        
        super(DBRepository, self).__init__(dbHome)

        self._openLock = None
        self._openFile = None

        if dbHome is not None:
            self._openDir = os.path.join(self.dbHome, '__open')
        else:
            self._openDir = None

        self._exclusiveLock = None
        self._env = None
        self._checkpointThread = None

        atexit.register(self.close)

    def _touchOpenFile(self):

        if self._openFile is None:
            self._openFile = os.path.join(self._openDir, UUID().str64())

        if not os.path.exists(self._openDir):
            os.mkdir(self._openDir)
            
        file(self._openFile, "w+").close()

    def _clearOpenDir(self):

        if os.path.exists(self._openDir):
            for name in os.listdir(self._openDir):
                path = os.path.join(self._openDir, name)
                if not os.path.isdir(path):
                    os.remove(path)
            
    def create(self, **kwds):

        if not self.isOpen():
            super(DBRepository, self).create(**kwds)
            self._create(**kwds)
            self._status |= Repository.OPEN
            if kwds.get('ramdb', False):
                self._status |= Repository.RAMDB

            self._afterOpen()

    def _create(self, **kwds):

        if self._env is not None:
            try:
                self._env.close()
                self._env = None
            except:
                self._env = None

        if self._openLock is not None:
            try:
                self._lockClose()
            except:
                self._openLock = None

        if kwds.get('ramdb', False):
            flags = DBEnv.DB_INIT_MPOOL | DBEnv.DB_PRIVATE | DBEnv.DB_THREAD
            self._env = self._createEnv(True, kwds)
            self._env.open(self.dbHome, DBEnv.DB_CREATE | flags, 0)
            
        else:
            if not os.path.exists(self.dbHome):
                os.makedirs(self.dbHome)
            elif not os.path.isdir(self.dbHome):
                raise ValueError, "%s is not a directory" %(self.dbHome)
            else:
                self.delete()

            self._lockOpen()
            self._env = self._createEnv(True, kwds)
            self._env.open(self.dbHome, DBEnv.DB_CREATE | self.OPEN_FLAGS, 0)

        self.store = self._createStore()
        kwds['create'] = True
        self.store.open(**kwds)

    def _createStore(self):

        return DBStore(self)

    def _lockOpen(self):
        
        lockFile = os.path.join(os.path.dirname(self.dbHome),
                                ".%s.lock" %(os.path.basename(self.dbHome)))
        fd = lock.open(lockFile)
        if not lock.lock(fd, lock.LOCK_SH | lock.LOCK_NB):
            lock.close(fd)
            raise RepositoryOpenDeniedError

        self._openLock = fd

    def _lockClose(self):

        if self._openLock is not None:
            if self._exclusiveLock is not None:
                lock.lock(self._exclusiveLock, lock.LOCK_UN | lock.LOCK_SH)
                self._exclusiveLock = None
            
            lock.lock(self._openLock, lock.LOCK_UN)
            lock.close(self._openLock)
            self._openLock = None

    def _createEnv(self, create, kwds):

        self._status &= ~Repository.CLOSED

        ramdb = kwds.get('ramdb', False)
        locks = 32767
        cache = 0x4000000
        
        if create and not ramdb:
            db_version = file(os.path.join(self.dbHome, 'DB_VERSION'), 'w+b')
            db_version.write("%d.%d.%d\n" %(DB_VERSION_MAJOR,
                                            DB_VERSION_MINOR,
                                            DB_VERSION_PATCH))
            db_version.close()
            db_config = file(os.path.join(self.dbHome, 'DB_CONFIG'), 'w+b')

        elif not (create or ramdb):
            try:
                db_version = file(os.path.join(self.dbHome, 'DB_VERSION'))
                version = db_version.readline().strip()
                db_version.close()
            except Exception, e:
                raise RepositoryVersionError, ("Repository database version could not be determined", e)
            else:
                expected = "%d.%d.%d" %(DB_VERSION_MAJOR,
                                        DB_VERSION_MINOR,
                                        DB_VERSION_PATCH)
                if version != expected:
                    raise RepositoryDatabaseVersionError, (version, expected)

        env = DBEnv()

        if 'password' in kwds:
            env.set_encrypt(kwds['password'], DBEnv.DB_ENCRYPT_AES)

        if create or ramdb:
            env.lk_detect = DBEnv.DB_LOCK_MINLOCKS
            env.lk_max_locks = locks
            env.lk_max_objects = locks
        if create and not ramdb:
            db_config.write("set_lk_detect DB_LOCK_MINLOCKS\n")
            db_config.write("set_lk_max_locks %d\n" %(locks))
            db_config.write("set_lk_max_objects %d\n" %(locks))

        if create and not ramdb:
            env.set_flags(DBEnv.DB_LOG_AUTOREMOVE, 1)
            db_config.write("set_flags DB_LOG_AUTOREMOVE\n")

        if os.name == 'nt':
            if create or ramdb:
                env.cachesize = (0, cache, 1)
            if create and not ramdb:
                db_config.write("set_cachesize 0 %d 1\n" %(cache))

        elif os.name == 'posix':
            from commands import getstatusoutput

            status, osname = getstatusoutput('uname')
            if status == 0:

                if (DB_VERSION <= 0x04031d and osname == 'Linux' or
                    DB_VERSION >= 0x040410 and osname in ('Linux', 'Darwin')):
                    if create or ramdb:
                        env.cachesize = (0, cache, 1)
                    if create and not ramdb:
                        db_config.write("set_cachesize 0 %d 1\n" %(cache))

                if osname == 'Darwin':
                    if create and not ramdb:
                        env.set_flags(DBEnv.DB_DSYNC_LOG, 1)
                        db_config.write("set_flags DB_DSYNC_LOG\n")

        if create and not ramdb:
            db_config.close()

        return env

    def delete(self):

        for name in os.listdir(self.dbHome):
            if (name.startswith('__') or
                name.startswith('log.') or
                name in ('DB_CONFIG', 'DB_VERSION')):
                path = os.path.join(self.dbHome, name)
                if not os.path.isdir(path):
                    os.remove(path)

        self._clearOpenDir()

    def checkpoint(self):

        if not self.isOpen():
            raise RepositoryError, 'Repository is not open'

        env = self._env
        env.txn_checkpoint(0, 0, DBEnv.DB_FORCE)
        env.log_archive(DBEnv.DB_ARCH_REMOVE)

    def backup(self, dbHome=None):

        if not self.isOpen():
            raise RepositoryError, 'Repository is not open'

        if dbHome is None:
            dbHome = self.dbHome

        rev = 1
        while True:
            path = "%s.%03d" %(dbHome, rev)
            if os.path.exists(path):
                rev += 1
            else:
                dbHome = path
                break
        os.makedirs(dbHome)

        env = self._env
        store = self.store

        try:
            for view in self.getOpenViews():
                view._acquireExclusive()

            self.checkpoint()

            for db in env.log_archive(DBEnv.DB_ARCH_DATA):
                path = os.path.join(dbHome, db)
                self.logger.info(path)
                shutil.copy2(os.path.join(self.dbHome, db), path)

            for log in env.log_archive(DBEnv.DB_ARCH_LOG):
                path = os.path.join(dbHome, log)
                self.logger.info(path)
                shutil.copy2(os.path.join(self.dbHome, log), path)

            if os.path.exists(os.path.join(self.dbHome, 'DB_CONFIG')):
                path = os.path.join(dbHome, 'DB_CONFIG')
                self.logger.info(path)
                shutil.copy2(os.path.join(self.dbHome, 'DB_CONFIG'), path)
            
            if os.path.exists(os.path.join(self.dbHome, 'DB_VERSION')):
                path = os.path.join(dbHome, 'DB_VERSION')
                self.logger.info(path)
                shutil.copy2(os.path.join(self.dbHome, 'DB_VERSION'), path)
            
        finally:
            for view in self.getOpenViews():
                view._releaseExclusive()

        return dbHome

    def compact(self):

        store = self.store

        itemCount = 0
        refCount = valueCount = 0
        lobCount = blockCount = nameCount = indexCount = 0
        documentCount = 0

        while True:
            try:
                txnStatus = store.startTransaction(None, True)
                if txnStatus == 0:
                    raise AssertionError, 'no transaction started'
                txn = store.txn

                indexReader = store._index.getIndexReader()
                indexSearcher = store._index.getIndexSearcher()

                prevUUID, keepValues, purger = None, (), None

                for uuid, version, status, values in store.iterItems(None):
                    if uuid == prevUUID:
                        if purger is None:
                            purger = DBItemPurger(txn, store, uuid, keepValues,
                                                  indexSearcher, indexReader,
                                                  status)
                        purger.purgeItem(txn, values, version, status)
                    else:
                        if purger is not None:
                            itemCount += purger.itemCount
                            refCount += purger.refCount
                            valueCount += purger.valueCount
                            lobCount += purger.lobCount
                            blockCount += purger.blockCount
                            nameCount += purger.nameCount
                            indexCount += purger.indexCount
                            documentCount += purger.documentCount
                            
                        if status & Item.DELETED:
                            purger = DBItemPurger(txn, store, uuid, (),
                                                  indexSearcher, indexReader,
                                                  status)
                            purger.purgeItem(txn, values, version, status)
                        else:
                            purger = None

                        prevUUID, keepValues = uuid, values

                indexReader.close()
                indexSearcher.close()

                store.compact()

            except DBLockDeadlockError:
                self.logger.info('retrying compact aborted by deadlock')
                store.abortTransaction(None, txnStatus)
                continue
            except:
                store.abortTransaction(None, txnStatus)
                raise
            else:
                store.commitTransaction(None, txnStatus)
                break

        return (itemCount, valueCount, refCount, lobCount, blockCount,
                nameCount, indexCount, documentCount)

    def open(self, **kwds):

        if kwds.get('ramdb', False):
            self.create(**kwds)

        elif not self.isOpen():

            super(DBRepository, self).open(**kwds)

            recover = kwds.get('recover', False)
            exclusive = kwds.get('exclusive', False)
            restore = kwds.get('restore', None)

            if restore is not None and os.path.isdir(restore):
                if os.path.exists(self.dbHome):
                    self.delete()
                if not os.path.exists(self.dbHome):
                    os.mkdir(self.dbHome)
                for f in os.listdir(restore):
                    if (f.endswith('.db') or
                        f.startswith('log.') or
                        f in ('DB_CONFIG', 'DB_VERSION')):
                        path = os.path.join(restore, f)
                        if not os.path.isdir(path):
                            self.logger.info(path)
                            shutil.copy2(path, os.path.join(self.dbHome, f))
                recover = True

            self._lockOpen()
            self._env = self._createEnv(False, kwds)

            if not recover:
                if os.path.exists(self._openDir) and os.listdir(self._openDir):
                    recover = True

            try:
                if recover or exclusive:
                    try:
                        locked = False
                        fd = self._openLock

                        locked = lock.lock(fd, (lock.LOCK_UN |
                                                lock.LOCK_EX | lock.LOCK_NB))
                        if not locked:
                            if exclusive:
                                raise ExclusiveOpenDeniedError
                            recover = False
                            self.logger.info('unable to obtain exclusive access to open with recovery, downgrading to regular open')

                        if recover:
                            before = datetime.now()
                            flags = (DBEnv.DB_RECOVER_FATAL | DBEnv.DB_CREATE |
                                     self.OPEN_FLAGS)
                            self._env.open(self.dbHome, flags, 0)
                            after = datetime.now()
                            self.logger.info('opened db with recovery in %s',
                                             after - before)
                            self._clearOpenDir()
                        else:
                            before = datetime.now()
                            self._env.open(self.dbHome, self.OPEN_FLAGS, 0)
                            after = datetime.now()
                            self.logger.info('opened db in %s', after - before)

                    finally:
                        if locked:
                            if exclusive:
                                self._exclusiveLock = fd
                            else:
                                lock.lock(fd, lock.LOCK_UN | lock.LOCK_SH)
                else:
                    before = datetime.now()
                    self._env.open(self.dbHome, self.OPEN_FLAGS, 0)
                    after = datetime.now()
                    self.logger.info('opened db in %s', after - before)

                self.store = self._createStore()
                kwds['create'] = False
                self.store.open(**kwds)

            except DBNoSuchFileError:
                kwds['create'] = recover
                if kwds.get('create', False):
                    self._create(**kwds)
                elif not os.path.exists(self.dbHome):
                    self._create(**kwds)
                else:
                    raise

            except DBInvalidArgError, e:
                if "no encryption key" in e.args[1]:
                    raise RepositoryPasswordError, e.args[1]
                raise

            except DBPermissionsError, e:
                if "Invalid password" in e.args[1]:
                    raise RepositoryPasswordError, e.args[1]
                raise

            self._status |= Repository.OPEN
            self._afterOpen()

    def _afterOpen(self):

        if (self._status & Repository.RAMDB) == 0:
            self._touchOpenFile()
            self._checkpointThread = DBCheckpointThread(self)
            self._checkpointThread.start()

    def close(self):

        super(DBRepository, self).close()
        status = self._status
        
        if (status & Repository.CLOSED) == 0:

            ramdb = status & Repository.RAMDB
            if not ramdb:
                if self._checkpointThread is not None:
                    self._checkpointThread.terminate()
                    self._checkpointThread = None

            self._status &= ~Repository.OPEN
            if self.store is not None:
                self.store.close()
            if self._env is not None:
                self._env.close()
                self._env = None
            self._lockClose()

            if ramdb:
                self._status &= ~Repository.RAMDB
            elif self._openFile is not None:
                os.remove(self._openFile)
                self._openFile = None

            self._status |= Repository.CLOSED

    def createView(self, name=None, version=None):

        return DBRepositoryView(self, name, version)

    openUUID = UUID('c54211ac-131a-11d9-8475-000393db837c')
    OPEN_FLAGS = (DBEnv.DB_INIT_MPOOL | DBEnv.DB_INIT_LOCK |
                  DBEnv.DB_INIT_TXN | DBEnv.DB_THREAD)


class DBTxn(object):

    def __init__(self, store, _txn, status):

        if store._ramdb:
            self._txn = None
        else:
            self._txn = store.repository._env.txn_begin(_txn)
            
        self._status = status
        self._count = 1

    def abort(self, status):

        assert self._count

        self._count -= 1
        if self._count == 0:
#            if status & DBStore.TXN_STARTED == 0:
#                print 'out of order abort'
            if self._txn is not None:
                self._txn.abort()
                self._txn = None
            return True

        return False

    def commit(self, status):
        
        assert self._count

        self._count -= 1
        if self._count == 0:
#            if status & DBStore.TXN_STARTED == 0:
#                print 'out of order commit'
            if self._txn is not None:
                self._txn.commit()
                self._txn = None
            return True

        return False
        

class DBStore(Store):

    def __init__(self, repository):

        self._threaded = local()

        self._items = ItemContainer(self)
        self._values = ValueContainer(self)
        self._refs = RefContainer(self)
        self._names = NamesContainer(self)
        self._lobs = LOBContainer(self)
        self._blocks = BlockContainer(self)
        self._index = IndexContainer(self)
        self._acls = ACLContainer(self)
        self._indexes = IndexesContainer(self)

        super(DBStore, self).__init__(repository)

    def open(self, **kwds):

        self._ramdb = kwds.get('ramdb', False)
        txnStatus = 0
        
        try:
            txnStatus = self.startTransaction(None)
            txn = self.txn

            if (not self._ramdb and
                os.path.exists(os.path.join(self.repository.dbHome,
                                            "__values__"))):
                self._values.open("__values__", txn, **kwds)
                raise AssertionError, "opening __values__ should have failed"

            self._items.open("__items.db", txn, **kwds)
            self._values.open("__values.db", txn, **kwds)
            self._refs.open("__refs.db", txn, **kwds)
            self._names.open("__names.db", txn, **kwds)
            self._lobs.open("__lobs.db", txn, **kwds)
            self._blocks.open("__blocks.db", txn, **kwds)
            self._index.open("__index.db", txn, **kwds)
            self._acls.open("__acls.db", txn, **kwds)
            self._indexes.open("__indexes.db", txn, **kwds)
        except DBNoSuchFileError:
            self.abortTransaction(None, txnStatus)
            raise
        except RepositoryVersionError:
            self.abortTransaction(None, txnStatus)
            raise
        else:
            self.commitTransaction(None, txnStatus)

    def close(self):

        self._items.close()
        self._values.close()
        self._refs.close()
        self._names.close()
        self._lobs.close()
        self._blocks.close()
        self._index.close()
        self._acls.close()
        self._indexes.close()

    def attachView(self, view):

        self._items.attachView(view)
        self._values.attachView(view)
        self._refs.attachView(view)
        self._names.attachView(view)
        self._lobs.attachView(view)
        self._blocks.attachView(view)
        self._index.attachView(view)
        self._acls.attachView(view)
        self._indexes.attachView(view)

    def detachView(self, view):

        self._items.detachView(view)
        self._values.detachView(view)
        self._refs.detachView(view)
        self._names.detachView(view)
        self._lobs.detachView(view)
        self._blocks.detachView(view)
        self._index.detachView(view)
        self._acls.detachView(view)
        self._indexes.detachView(view)

    def compact(self):

        txn = self.txn

        self._items.compact(txn)
        self._values.compact(txn)
        self._refs.compact(txn)
        self._names.compact(txn)
        self._lobs.compact(txn)
        self._blocks.compact(txn)
        self._index.compact(txn)
        self._acls.compact(txn)
        self._indexes.compact(txn)

    def loadItem(self, view, version, uuid):

        args = self._items.loadItem(view, version, uuid)
        if args is None:
            return None

        itemReader = DBItemReader(self, uuid, *args)
        if itemReader.isDeleted():
            return None

        return itemReader
    
    def loadRef(self, view, version, uItem, uuid, key):

        return self._refs.loadRef(view, uItem._uuid + uuid._uuid, version, key)

    def loadRefs(self, view, version, uItem, uuid, firstKey):

        refs = []
        iterator = self._refs.refIterator(view, uItem._uuid + uuid._uuid,
                                          version)
        key = firstKey
        while key is not None:
            ref = iterator.next(key)
            refs.append(ref)
            key = ref[1]

        return refs

    def readName(self, view, version, key, name):

        return self._names.readName(view, version, key, name)

    def readNames(self, view, version, key):

        return self._names.readNames(view, version, key)

    def writeName(self, version, key, name, uuid):

        return self._names.writeName(version, key, name, uuid)

    def loadACL(self, view, version, uuid, name):

        return self._acls.readACL(view, version, uuid, name)

    def saveACL(self, version, uuid, name, acl):

        return self._acls.writeACL(version, uuid, name, acl)

    def queryItems(self, view, version, kind=None, attribute=None):

        if kind is not None:
            items = self._items
            for uuid, args in items.kindQuery(view, version, kind):
                if items.getItemVersion(view, version, uuid) == args[0]:
                    yield DBItemReader(self, uuid, *args)

        elif attribute is not None:
            raise NotImplementedError, 'attribute query'

        else:
            raise ValueError, 'one of kind or value must be set'

    def queryItemKeys(self, view, version, kind=None, attribute=None):

        if kind is not None:
            items = self._items
            itemFinder = items._itemFinder(view)
            for uuid, ver in items.kindQuery(view, version, kind, True):
                if itemFinder.getVersion(version, uuid) == ver:
                    yield uuid

        elif attribute is not None:
            raise NotImplementedError, 'attribute query'

        else:
            raise ValueError, 'one of kind or value must be set'

    def kindForKey(self, view, version, uuid):

        return self._items.getItemKindId(view, version, uuid)

    def searchItems(self, view, version, query, attribute=None):

        return self._index.searchDocuments(version, query, attribute)

    def iterItems(self, view):

        return self._items.iterItems(view)

    def getItemVersion(self, view, version, uuid):

        return self._items.getItemVersion(view, version, uuid)

    def getVersion(self):

        return self._values.getVersion()

    def nextVersion(self):

        return self._values.nextVersion()

    def getVersionInfo(self):

        return self._values.getVersionInfo(self.repository.itsUUID)

    def startTransaction(self, view, nested=False):

        status = 0
        locals = self._threaded
        txn = getattr(locals, 'txn', None)

        if view is not None and txn is None and view._acquireExclusive():
            status = DBStore.EXCLUSIVE

        if txn is None:
            status |= DBStore.TXN_STARTED
            locals.txn = DBTxn(self, None, status)
        elif nested:
            try:
                locals.txns.append(txn)
            except AttributeError:
                locals.txns = [txn]
            status |= DBStore.TXN_STARTED | DBStore.TXN_NESTED
            locals.txn = DBTxn(self, txn._txn, status)
        else:
            txn._count += 1

        return status

    def commitTransaction(self, view, status):

        locals = self._threaded
        txn = locals.txn

        try:
            if txn is not None:
                if txn.commit(status):
                    status = txn._status
                    if status & DBStore.TXN_NESTED:
                        locals.txn = locals.txns.pop()
                    else:
                        locals.txn = None
                elif status & DBStore.EXCLUSIVE:
                    txn._status |= DBStore.EXCLUSIVE
                    status &= ~DBStore.EXCLUSIVE
        finally:
            if status & DBStore.EXCLUSIVE:
                view._releaseExclusive()

        return status

    def abortTransaction(self, view, status):

        locals = self._threaded
        txn = locals.txn

        try:
            if txn is not None:
                if txn.abort(status):
                    status = txn._status
                    if status & DBStore.TXN_NESTED:
                        locals.txn = locals.txns.pop()
                    else:
                        locals.txn = None
                elif status & DBStore.EXCLUSIVE:
                    txn._status |= DBStore.EXCLUSIVE
                    status &= ~DBStore.EXCLUSIVE
        finally:
            if status & DBStore.EXCLUSIVE:
                view._releaseExclusive()

        return status

    def _getTxn(self):

        txn = getattr(self._threaded, 'txn', None)
        if txn is None:
            return None

        return txn._txn

    def _getEnv(self):

        return self.repository._env

    def _getLockId(self):

        lockId = getattr(self._threaded, 'lockId', None)
        if lockId is None:
            lockId = self.repository._env.lock_id()
            self._threaded.lockId = lockId
        return lockId

    def acquireLock(self):

        if not self._ramdb:
            repository = self.repository
            return repository._env.lock_get(self._getLockId(),
                                            repository.itsUUID._uuid,
                                            DBEnv.DB_LOCK_WRITE)
        return None

    def releaseLock(self, lock):

        if lock is not None:
            self.repository._env.lock_put(lock)
        return None

    def serveItem(self, version, uuid, cloudAlias):

        v, versionId = self._values.getVersionInfo()
        if version == 0:
            version = v
        
        doc = self.loadItem(None, version, uuid)
        if doc is None:
            return None
                
        xml = doc.getContent()
        out = cStringIO.StringIO()
        generator = XMLGenerator(out)

        try:
            attrs = { 'version': str(version),
                      'versionId': versionId.str64() }
            generator.startElement('items', attrs)
            filter = CloudFilter(None, cloudAlias, self, uuid, version,
                                 generator)
            filter.parse(xml, {})
            generator.endElement('items')
        
            return out.getvalue()
        finally:
            out.close()

    def serveChild(self, version, uuid, name, cloudAlias):

        if version == 0:
            version = self._values.getVersion()
        
        uuid = self.readName(None, version, uuid, name)
        if uuid is None:
            return None

        return self.serveItem(version, uuid, cloudAlias)

    TXN_STARTED = 0x0001
    TXN_NESTED  = 0x0002
    EXCLUSIVE   = 0x0004

    env = property(_getEnv)
    txn = property(_getTxn)


class DBCheckpointThread(Thread):

    def __init__(self, repository):

        super(DBCheckpointThread, self).__init__()

        self._repository = repository
        self._condition = Condition(Lock())
        self._alive = True

        self.setDaemon(True)

    def run(self):

        repository = self._repository
        condition = self._condition

        while self._alive:
            condition.acquire()
            condition.wait(600.0)
            condition.release()

            if not (self._alive and self.isAlive()):
                break

            try:
                for view in repository.getOpenViews():
                    view._acquireExclusive()

                repository.checkpoint()
                repository.logger.info('%s: %s, completed checkpoint',
                                       repository, datetime.now())
            finally:
                for view in repository.getOpenViews():
                    view._releaseExclusive()

    def terminate(self):
        
        if self._alive and self.isAlive():
            condition = self._condition

            condition.acquire()
            self._alive = False
            condition.notify()
            condition.release()

            self._repository.checkpoint()
            self.join()
