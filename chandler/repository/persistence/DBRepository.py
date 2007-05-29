#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import sys, os, shutil, atexit, time, threading

from datetime import datetime, timedelta
from os.path import exists, abspath, normpath, join, dirname, basename, isdir

from chandlerdb.util import lock
from chandlerdb.util.c import Nil, Default, UUID, _hash, getPlatformName
from chandlerdb.item.c import CItem
from chandlerdb.item import Indexable
from chandlerdb.persistence.c import DBEnv, DB, Transaction, \
    DBNoSuchFileError, DBPermissionsError, DBInvalidArgError, \
    DBLockDeadlockError, DBVersionMismatchError, DBRunRecoveryError, \
    DB_VERSION_MAJOR, DB_VERSION_MINOR, DB_VERSION_PATCH

from repository.schema.TypeHandler import TypeHandler
from repository.persistence.Repository import \
    Repository, OnDemandRepository, Store, RepositoryThread
from repository.persistence.RepositoryError import *
from repository.persistence.DBRepositoryView import DBRepositoryView
from repository.persistence.DBContainer import \
    RefContainer, NamesContainer, ACLContainer, IndexesContainer, \
    ItemContainer, ValueContainer, VersionContainer, CommitsContainer
from repository.persistence.FileContainer import IndexContainer, LOBContainer
from repository.persistence.DBItemIO import \
    DBItemReader, DBItemPurger, DBValueReader, DBItemWriter, DBItemUndo

DB_VERSION = DB_VERSION_MAJOR << 16 | DB_VERSION_MINOR << 8 | DB_VERSION_PATCH


class DBRepository(OnDemandRepository):
    """
    A Berkeley DB based repository.
    """

    def __init__(self, dbHome):
        """
        Construct an DBRepository giving it a DB container pathname
        """
        
        super(DBRepository, self).__init__(abspath(dbHome))

        self._openLock = None
        self._openFile = None

        if dbHome is not None:
            self._openDir = join(self.dbHome, '__open')
        else:
            self._openDir = None

        self._exclusiveLock = None
        self._env = None
        self._checkpointThread = None

        atexit.register(self.close)

    def _touchOpenFile(self):

        if self._openFile is None:
            self._openFile = join(self._openDir, UUID().str64())

        if not exists(self._openDir):
            os.mkdir(self._openDir)
            
        file(self._openFile, "w+").close()

    def _clearOpenDir(self):

        if exists(self._openDir):
            for name in os.listdir(self._openDir):
                path = join(self._openDir, name)
                if not isdir(path):
                    os.remove(path)

    def _enableCheckpoints(self, enabled=True):
        
        thread = self._checkpointThread
        if thread is not None:
            _enabled = thread.enabled
            thread.enabled = enabled
            return _enabled

        return False

    def create(self, **kwds):

        if not self.isOpen():
            super(DBRepository, self).create(**kwds)
            self._create(**kwds)
            self._status |= Repository.OPEN
            if kwds.get('ramdb', False):
                self._status |= Repository.RAMDB

            self._afterOpen(**kwds)

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
            self._env = self._createEnv(True, True, kwds)
            self._env.open(self.dbHome, DBEnv.DB_CREATE | flags, 0)
            
        else:
            dbHome = self.dbHome
            datadir = kwds.get('datadir')
            logdir = kwds.get('logdir')

            self.logger.info('creating repository in %s', dbHome)

            if not exists(dbHome):
                os.makedirs(dbHome)
            elif not isdir(dbHome):
                raise ValueError, "%s is not a directory" %(dbHome)
            else:
                self.delete(datadir, logdir)

            if datadir:
                datadir = join(dbHome, datadir)
                if not exists(datadir):
                    os.makedirs(datadir)
            if logdir:
                logdir = join(dbHome, logdir)
                if not exists(logdir):
                    os.makedirs(logdir)

            self._lockOpen()
            self._env = self._createEnv(True, True, kwds)
            self._env.open(dbHome, DBEnv.DB_CREATE | self.OPEN_FLAGS, 0)

        self.store = self._createStore()
        kwds['create'] = True
        self.store.open(**kwds)

    def _createStore(self):

        return DBStore(self)

    def _lockOpen(self):
        
        dbHome = self.dbHome
        lockFile = join(dirname(dbHome), ".%s.lock" %(basename(dbHome)))
        fd = lock.open(lockFile)
        if not lock.lock(fd, lock.LOCK_SH | lock.LOCK_NB):
            lock.close(fd)
            raise RepositoryOpenDeniedError

        self._openLock = fd
        return fd

    def _lockOpenExclusive(self):

        fd = self._openLock
        if fd is None:
            fd = self._lockOpen()
            opened = True
        else:
            opened = False

        if not lock.lock(fd, (lock.LOCK_UN | lock.LOCK_EX | lock.LOCK_NB)):
            if opened:
                self._lockClose()
            raise ExclusiveOpenDeniedError

        self._exclusiveLock = fd
        return fd

    def _lockClose(self):

        if self._openLock is not None:
            if self._exclusiveLock is not None:
                lock.lock(self._exclusiveLock, lock.LOCK_UN | lock.LOCK_SH)
                self._exclusiveLock = None
            
            lock.lock(self._openLock, lock.LOCK_UN)
            lock.close(self._openLock)
            self._openLock = None

    def _encrypt(self, env, create, kwds):

        try:
            password = kwds.get('password', None)
            if callable(password):
                again = self._status & Repository.BADPASSWD != 0
                env.set_encrypt(password(create, again), DBEnv.DB_ENCRYPT_AES)
            elif isinstance(password, str):
                env.set_encrypt(password, DBEnv.DB_ENCRYPT_AES)
            else:
                return False
            self._status |= Repository.ENCRYPTED
        except DBInvalidArgError:
            raise RepositoryPasswordError, False

        return True

    def _createEnv(self, configure, create, kwds):

        self._status &= ~Repository.CLOSED

        dbHome = self.dbHome
        ramdb = kwds.get('ramdb', False)
        locks = 32767
        cache = 0x4000000

        env = DBEnv()

        if not ramdb and kwds.get('mvcc', False):
            env.tx_max = 1024

        if configure and not ramdb:
            db_info = file(join(dbHome, 'DB_INFO'), 'w+b')
            try:
                db_info.write("%d.%d.%d\n" %(DB_VERSION_MAJOR,
                                             DB_VERSION_MINOR,
                                             DB_VERSION_PATCH))
                if 'password' in kwds and self._encrypt(env, create, kwds):
                    db_info.write('encrypted\n')
                else:
                    db_info.write('not encrypted\n')
                db_info.write('%s\n' %(getPlatformName()))
            finally:
                db_info.close()

            db_config = file(join(dbHome, 'DB_CONFIG'), 'w+b')

        elif not (configure or ramdb):
            try:
                db_info = file(join(dbHome, 'DB_INFO'))
                version = db_info.readline().strip()
                encrypted = db_info.readline().strip() == 'encrypted'
                platform = db_info.readline().strip()
                db_info.close()
            except Exception, e:
                raise RepositoryVersionError, ("Repository database version could not be determined", e)
            else:
                expected = "%d.%d.%d" %(DB_VERSION_MAJOR,
                                        DB_VERSION_MINOR,
                                        DB_VERSION_PATCH)
                if version != expected:
                    raise RepositoryDatabaseVersionError, (expected, version)

                if encrypted and not self._encrypt(env, create, kwds):
                    raise RepositoryPasswordError, True

                if platform != getPlatformName():
                    raise RepositoryPlatformError, (platform or 'unknown',
                                                    getPlatformName())

        if configure or ramdb:
            env.lk_detect = DBEnv.DB_LOCK_MAXWRITE
            env.lk_max_locks = locks
            env.lk_max_objects = locks
        if configure and not ramdb:
            db_config.write("set_lk_detect DB_LOCK_MAXWRITE\n")
            db_config.write("set_lk_max_locks %d\n" %(locks))
            db_config.write("set_lk_max_objects %d\n" %(locks))

        if configure and not ramdb:
            memorylog = kwds.get('memorylog', None)
            if memorylog:
                memorylog = int(memorylog) * 1048576
            if memorylog:
                env.set_flags(DBEnv.DB_LOG_INMEMORY, 1)
                env.lg_bsize = memorylog
                db_config.write("set_flags DB_LOG_INMEMORY\n")
                db_config.write("set_lg_bsize %d\n" %(env.lg_bsize))
            else:
                logdir = kwds.get('logdir', None)
                if logdir:
                    env.lg_dir = logdir
                    db_config.write("set_lg_dir %s\n" %(logdir))
                env.set_flags(DBEnv.DB_LOG_AUTOREMOVE, 1)
                db_config.write("set_flags DB_LOG_AUTOREMOVE\n")

            datadir = kwds.get('datadir', None)
            if datadir:
                env.set_data_dir(datadir)
                db_config.write("set_data_dir %s\n" %(datadir))

        if os.name == 'nt':
            if configure or ramdb:
                env.cachesize = (0, cache, 1)
            if configure and not ramdb:
                db_config.write("set_cachesize 0 %d 1\n" %(cache))

        elif os.name == 'posix':
            from commands import getstatusoutput

            status, osname = getstatusoutput('uname')
            if status == 0:

                if (DB_VERSION <= 0x04031d and osname == 'Linux' or
                    DB_VERSION >= 0x040410 and osname in ('Linux', 'Darwin')):
                    if configure or ramdb:
                        env.cachesize = (0, cache, 1)
                    if configure and not ramdb:
                        db_config.write("set_cachesize 0 %d 1\n" %(cache))

                if osname == 'Darwin':
                    if configure and not ramdb:
                        env.set_flags(DBEnv.DB_DSYNC_LOG, 1)
                        env.set_flags(DBEnv.DB_REGION_INIT, 1)
                        db_config.write("set_flags DB_DSYNC_LOG\n")
                        db_config.write("set_flags DB_REGION_INIT\n")

        if configure and not ramdb:
            db_config.close()

        return env

    def delete(self, datadir=None, logdir=None):

        dbHome = self.dbHome
        self._lockOpenExclusive()

        try:
            for name in os.listdir(dbHome):
                if (name.startswith('__db') or
                    name.startswith('log.') or
                    name.endswith('.db') or
                    name in ('DB_CONFIG', 'DB_INFO')):
                    path = join(dbHome, name)
                    if not isdir(path):
                        os.remove(path)
            if datadir:
                for name in os.listdir(join(dbHome, datadir)):
                    if name.endswith('.db'):
                        path = join(dbHome, datadir, name)
                        if not isdir(path):
                            os.remove(path)
            if logdir:
                for name in os.listdir(join(dbHome, logdir)):
                    if name.startswith('log.'):
                        path = join(dbHome, logdir, name)
                        if not isdir(path):
                            os.remove(path)
            self._clearOpenDir()

        finally:
            self._lockClose()

    def checkpoint(self):

        if not self.isOpen():
            raise RepositoryError, 'Repository is not open'

        if self._status & Repository.RAMDB == 0:
            env = self._env
            env.txn_checkpoint(0, 0, DBEnv.DB_FORCE)
            env.log_archive(DBEnv.DB_ARCH_REMOVE)

    def backup(self, dbHome=None, withLog=False):

        if not self.isOpen():
            raise RepositoryError, 'Repository is not open'

        if dbHome is None:
            dbHome = self.dbHome

        rev = 1
        while True:
            path = "%s.%03d" %(dbHome, rev)
            path = path.encode(sys.getfilesystemencoding())
            if exists(path):
                rev += 1
            else:
                dbHome = path
                break
        os.makedirs(dbHome)

        release = []
        enabled = None
        try:
            for view in self.getOpenViews():
                if view._acquireExclusive():
                    release.append(view)

            enabled = self._enableCheckpoints(False)
            self.checkpoint()

            for srcPath in self._env.log_archive(DBEnv.DB_ARCH_DATA |
                                                 DBEnv.DB_ARCH_ABS):
                x, db = os.path.split(srcPath)
                dstPath = join(dbHome, db)
                self.logger.info(dstPath)

                shutil.copy2(srcPath, dstPath)

            for srcPath in self._env.log_archive(DBEnv.DB_ARCH_LOG |
                                                 DBEnv.DB_ARCH_ABS):
                x, log = os.path.split(srcPath)
                dstPath = join(dbHome, log)
                self.logger.info(dstPath)

                shutil.copy2(srcPath, dstPath)

            if exists(join(self.dbHome, 'DB_CONFIG')):
                dstPath = join(dbHome, 'DB_CONFIG')
                self.logger.info(dstPath)
                inFile = file(join(self.dbHome, 'DB_CONFIG'), 'r')
                outFile = file(dstPath, 'w+b')
                for line in inFile:
                    if not (line.startswith('set_data_dir') or
                            line.startswith('set_lg_dir')):
                        outFile.write(line)
                outFile.close()
            
            if exists(join(self.dbHome, 'DB_INFO')):
                dstPath = join(dbHome, 'DB_INFO')
                self.logger.info(dstPath)
                shutil.copy2(join(self.dbHome, 'DB_INFO'), dstPath)

            if not withLog:
                env = None
                try:
                    env = DBEnv()
                    env.open(dbHome, (DBEnv.DB_RECOVER_FATAL | DBEnv.DB_CREATE |
                                      self.OPEN_FLAGS), 0)

                    if self._status & Repository.ENCRYPTED:
                        flags = DB.DB_ENCRYPT
                    else:
                        flags = 0
                    for db in env.log_archive(DBEnv.DB_ARCH_DATA):
                        env.lsn_reset(db, flags)

                    env.close()
                    env = None

                    for name in os.listdir(dbHome):
                        if (name.startswith('__db.') or
                            name.startswith('log.')):
                            os.remove(join(dbHome, name))

                finally:
                    if env is not None:
                        env.close()

        finally:
            for view in release:
                view._releaseExclusive()
            if enabled is not None:
                self._enableCheckpoints(enabled)

        return dbHome

    def restore(self, srcHome, datadir=None, logdir=None):

        if exists(srcHome):
            dbHome = self.dbHome
            withLogs = False

            if exists(dbHome):
                self.delete(datadir, logdir)
            if not exists(dbHome):
                os.mkdir(dbHome)

            if datadir:
                datadir = join(dbHome, datadir)
                if not exists(datadir):
                    os.mkdir(datadir)
            else:
                datadir = dbHome

            if logdir:
                logdir = join(dbHome, logdir)
                if not exists(logdir):
                    os.mkdir(logdir)
            else:
                logdir = dbHome

            if isdir(srcHome):
                for f in os.listdir(srcHome):
                    if f.endswith('.db'):
                        dstPath = join(datadir, f)
                    elif f.startswith('log.'):
                        withLogs = True
                        dstPath = join(logdir, f)
                    elif f in ('DB_CONFIG', 'DB_INFO'):
                        dstPath = join(dbHome, f)
                    else:
                        continue
                                      
                    srcPath = join(srcHome, f)
                    self.logger.info(srcPath)
                    shutil.copy2(srcPath, dstPath)

            elif srcHome.endswith('gz') or srcHome.endswith('bz2'):
                import tarfile

                if srcHome.endswith('gz'):
                    restoreFile = tarfile.open(srcHome, 'r:gz')
                else:
                    restoreFile = tarfile.open(srcHome, 'r:bz2')

                for member in restoreFile:
                    f = os.path.basename(member.name)
                    if f.endswith('.db'):
                        dstPath = datadir
                    elif f.startswith('log.'):
                        withLogs = True
                        dstPath = logdir
                    elif f in ('DB_CONFIG', 'DB_INFO'):
                        dstPath = dbHome
                    else:
                        continue

                    self.logger.info(join(srcHome, f))
                    data = restoreFile.extractfile(member).read()
                    outFile = file(os.path.join(dstPath, f), 'w+b')
                    outFile.write(data)
                    outFile.close()
                restoreFile.close()

            elif srcHome.endswith('zip'):
                import zipfile

                restoreFile = zipfile.ZipFile(srcHome, 'r')

                for member in restoreFile.infolist():
                    f = os.path.basename(member.filename)
                    if f.endswith('.db'):
                        dstPath = datadir
                    elif f.startswith('log.'):
                        withLogs = True
                        dstPath = logdir
                    elif f in ('DB_CONFIG', 'DB_INFO'):
                        dstPath = dbHome
                    else:
                        continue

                    self.logger.info(join(srcHome, f))
                    data = restoreFile.read(member.filename)
                    outFile = file(os.path.join(dstPath, f), 'w+b')
                    outFile.write(data)
                    outFile.close()
                restoreFile.close()

            else:
                raise ValueError, (srcHome, 'not a valid backup archive')

            if datadir != dbHome or logdir != dbHome:
                outFile = file(join(dbHome, 'DB_CONFIG'), 'a+b')
                if datadir != dbHome:
                    outFile.write('set_data_dir %s\n' %(datadir))
                if logdir != dbHome:
                    outFile.write('set_lg_dir %s\n' %(logdir))
                outFile.close()

            try:
                db_info = file(join(dbHome, 'DB_INFO'))
                version = db_info.readline().strip()
                encrypted = db_info.readline().strip()
                platform = db_info.readline().strip()
                db_info.close()
            except Exception, e:
                raise RepositoryVersionError, ("Restore repository database version could not be determined", e)

            if withLogs and (platform.rsplit('-', 1)[-1:] !=
                             getPlatformName().rsplit('-', 1)[-1:]):
                raise RepositoryPlatformError, (platform or 'unknown',
                                                getPlatformName())

            db_info = file(join(dbHome, 'DB_INFO'), 'w+b')
            db_info.write("%s\n" %(version))
            db_info.write("%s\n" %(encrypted))
            db_info.write("%s\n" %(getPlatformName()))
            db_info.close()

        else:
            raise RepositoryRestoreError, (srcHome, 'does not exist')

    def compact(self, toVersion=None, chunk=25000, fromUUID=None,
                progressFn=Nil):

        store = self.store
        if toVersion is None:
            toVersion = store.getVersion()            

        class _counter(object):
            class commit(Exception):
                pass
            def __init__(_self):
                _self.running = 0
                _self.current = (fromUUID, 0)
            def __getattr__(_self, name):
                if name.endswith('Count'):
                    return 0
                raise AttributeError, name
            def __setattr__(_self, name, value):
                _self.__dict__[name] = value
                if name.endswith('Count'):
                    _self.running += 1
                    if _self.running >= chunk:
                        raise _counter.commit, (name, value)
            def getCounts(_self):
                return (_self.itemCount, _self.valueCount, _self.refCount,
                        _self.indexCount, _self.nameCount, 
                        _self.lobCount, _self.blockCount, _self.documentCount)

        counter = _counter()

        self.logger.info("compact(): deleting old records past version %d",
                         toVersion)
        stage = "purging old records"
        if progressFn(stage, 0) is False:
            return counter.getCounts()

        cancelled = False
        while True:
            try:
                txnStatus = store.startTransaction(None, True)
                if txnStatus == 0:
                    raise AssertionError, 'no transaction started'
                txn = store.txn

                indexReader = Nil
                indexSearcher = Nil

                prevUUID = None
                nextVersion = None
                items = []

                def purge():
                    count = len(items)
                    if count == 0:
                        return
                    uItem, version, status, values = items[-1]
                    if count == 1 and status & CItem.DELETED == 0:
                        if counter.current != uItem:
                            return
                    purger = DBItemPurger(txn, store)
                    if status & CItem.DELETED == 0:
                        purger.purgeDocuments(txn, counter, uItem, version,
                                              indexSearcher, indexReader,
                                              version)
                        purger.purgeItem(txn, counter,
                                         uItem, version, status, values,
                                         version)
                        del items[-1]
                    else:
                        # gets at documents via a Lucene query, not by reaching
                        # through values. nextVersion prevents a reborn item's
                        # docs from being purged.
                        purger.purgeDocuments(txn, counter, uItem, version,
                                              indexSearcher, indexReader,
                                              nextVersion)
                    purger.purgeItems(txn, counter, items)

                try:
                    indexReader = store._index.getIndexReader()
                    indexSearcher = store._index.getIndexSearcher()
                        
                    for item in store._items.iterItems(None, True,
                                                       counter.current[0]):
                        uuid = item[0]
                        version = item[1]
                        if uuid == prevUUID:
                            if version <= toVersion:
                                items.append(item)
                            else:
                                nextVersion = version
                        else:
                            purge()
                            del items[:]
                            items.append(item)
                            prevUUID = uuid

                        if cancelled:
                            break

                    if not cancelled:
                        purge()

                finally:
                    indexReader.close()
                    indexSearcher.close()

                # even when cancelling, purge version records
                store._versions.purgeViewData(txn, counter, toVersion)

            except _counter.commit, e:
                uItem, version = counter.current
                name, value = e.args
                self.logger.info("compact(): %s %d, %s: %d",
                                 uItem, version, name, value)
                store.commitTransaction(None, txnStatus)
                counter.running = 0
                del items[:]
                percent = ord(uItem._uuid[0]) * 256 + ord(uItem._uuid[1])
                if progressFn(stage, 100 - (percent * 100) / 65536) is False:
                    cancelled = True
                continue

            except DBLockDeadlockError:
                self.logger.info('retrying compact() aborted by deadlock')
                store.abortTransaction(None, txnStatus)
                counter.running = 0
                del items[:]
                continue

            except:
                store.abortTransaction(None, txnStatus)
                raise

            else:
                store.commitTransaction(None, txnStatus)
                break

        counts = counter.getCounts()
        self.logger.info("compact(): reclaimed %d items, %d values, %d refs, %d index entries, %d names, %d lobs, %d blocks, %d lucene documents)", *counts)
        progressFn(stage, 100)

        store.compact(progressFn)

        return counts

    def undo(self, toVersion=None):

        store = self.store

        currentVersion = store.getVersion()
        if toVersion is None:
            toVersion = currentVersion - 1

        for version in xrange(currentVersion, toVersion, -1):
            while True:
                try:
                    txnStatus = store.startTransaction(None, True)
                    if txnStatus == 0:
                        raise AssertionError, 'no transaction started'
                    txn = store.txn

                    indexReader = store._index.getIndexReader()
                    indexSearcher = store._index.getIndexSearcher()

                    for args in store._items.iterHistory(None,
                                                         version - 1, version):
                        DBItemUndo(self, *args).undoItem(txn, indexReader,
                                                         indexSearcher)
                    indexReader.close()
                    indexSearcher.close()

                    indexVersion = store.getIndexVersion()
                    if indexVersion == version:
                        store.setIndexVersion(indexVersion - 1)

                    store._commits.purgeCommit(version)
                    store._versions.setVersion(version - 1)

                    store.commitTransaction(None, txnStatus)

                except DBLockDeadlockError:
                    self.logger.info('retrying undo aborted by deadlock')
                    store.abortTransaction(None, txnStatus)
                    continue
                except:
                    store.abortTransaction(None, txnStatus)
                    raise
                else:
                    break

    def open(self, **kwds):

        if kwds.get('ramdb', False):
            self.create(**kwds)

        elif not self.isOpen():

            super(DBRepository, self).open(**kwds)

            recover = kwds.get('recover', False)
            exclusive = kwds.get('exclusive', False)
            restore = kwds.get('restore', None)

            dbHome = self.dbHome
            datadir = kwds.get('datadir')
            logdir = kwds.get('logdir')
            configure = False

            self.logger.info('opening repository in %s', dbHome)

            if restore is not None:
                self.restore(restore, datadir, logdir)
                recover = True

            elif kwds.get('create', False) and not exists(dbHome):
                if datadir and exists(normpath(join(dbHome, datadir))):
                    os.makedirs(dbHome)
                    configure = True
                    recover = True
                else:
                    return self.create(**kwds)

            self._lockOpen()
            self._env = self._createEnv(configure, False, kwds)

            if not recover and exclusive:
                if exists(self._openDir) and os.listdir(self._openDir):
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
                            if exists(dbHome):
                                for name in os.listdir(dbHome):
                                    if name.startswith('__db.'):
                                        path = join(dbHome, name)
                                        try:
                                            os.remove(path)
                                        except Exception, e:
                                            self.logger.warning("Error removing %s: %s", path, e)
                            before = datetime.now()
                            flags = (DBEnv.DB_RECOVER_FATAL | DBEnv.DB_CREATE |
                                     self.OPEN_FLAGS)
                            self._env.open(dbHome, flags, 0)
                            after = datetime.now()
                            self.logger.info('opened db with recovery in %s',
                                             after - before)
                            self._clearOpenDir()
                        else:
                            before = datetime.now()
                            self._env.open(dbHome, self.OPEN_FLAGS, 0)
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
                    self._env.open(dbHome, self.OPEN_FLAGS, 0)
                    after = datetime.now()
                    self.logger.info('opened db in %s', after - before)

                self.store = self._createStore()
                kwds['create'] = False
                self.store.open(**kwds)

            except DBNoSuchFileError:
                kwds['create'] = recover
                if kwds.get('create', False):
                    self._create(**kwds)
                elif not exists(dbHome):
                    self._create(**kwds)
                else:
                    raise

            except DBInvalidArgError, e:
                if "no encryption key" in e.args[1]:
                    raise RepositoryPasswordError, True
                if "Invalid argument" in e.args[1] and not recover:
                    self._status |= Repository.CLOSED
                    raise RepositoryRunRecoveryError, recover
                raise

            except DBPermissionsError, e:
                if "Invalid password" in e.args[1]:
                    self._status |= Repository.BADPASSWD
                    raise RepositoryPasswordError, True
                if "Operation not permitted" in e.args[1]:
                    self._status |= Repository.BADPASSWD
                    raise RepositoryPasswordError, True
                raise

            except DBVersionMismatchError:
                expected = "%d.%d.%d" %(DB_VERSION_MAJOR,
                                        DB_VERSION_MINOR,
                                        DB_VERSION_PATCH)
                raise RepositoryDatabaseVersionError, (expected, 'undetermined')

            except (DBRunRecoveryError, MemoryError):
                self._status |= Repository.CLOSED
                raise RepositoryRunRecoveryError, recover

            self._status |= Repository.OPEN
            self._status &= ~Repository.BADPASSWD
            self._afterOpen(**kwds)

    def _afterOpen(self, **kwds):

        if (self._status & Repository.RAMDB) == 0:
            self._touchOpenFile()
            interval = kwds.get('checkpoints', 10)
            if interval:
                self._checkpointThread = DBCheckpointThread(self, interval)
                self._checkpointThread.start()

    def close(self):

        super(DBRepository, self).close()
        status = self._status
        
        if (status & Repository.CLOSED) == 0:
            
            #kludge fix for bug 8592
            sys.modules.setdefault('repository.persistence',None)
            
            before = datetime.now()

            self.stopIndexer()

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
                if exists(self._openFile):
                    os.remove(self._openFile)
                self._openFile = None

            self._status |= Repository.CLOSED
            after = datetime.now()

            self.logger.info('closed db in %s', after - before)

    def createView(self, name=None, version=None,
                   deferDelete=Default, pruneSize=Default, notify=Default,
                   mergeFn=None, mvcc=True):

        return DBRepositoryView(self, name, version,
                                deferDelete, pruneSize, notify, mergeFn, mvcc)

    def startIndexer(self, interval=60):

        if self._indexer is None:
            self._indexer = DBIndexerThread(self, interval)
            self._indexer.start()

    def stopIndexer(self):

        if self._indexer is not None:
            self._indexer.terminate()
            self._indexer = None

    def notifyIndexer(self, wait=False):

        if self._indexer is not None:
            self._indexer.notify(wait)

    openUUID = UUID('c54211ac-131a-11d9-8475-000393db837c')
    OPEN_FLAGS = (DBEnv.DB_INIT_MPOOL | DBEnv.DB_INIT_LOCK |
                  DBEnv.DB_INIT_TXN | DBEnv.DB_THREAD)


class DBTransaction(Transaction):

    def start(self, store, _txn, _mvcc):

        if store._ramdb:
            return None
        elif _mvcc and store._mvcc:
            self._mvcc = True
            flags = DBEnv.DB_TXN_SNAPSHOT | DB.DB_READ_UNCOMMITTED
            return store.repository._env.txn_begin(_txn, flags)
        else:
            flags = DB.DB_READ_UNCOMMITTED
            return store.repository._env.txn_begin(_txn, flags)


class DBStore(Store):

    def __init__(self, repository):

        super(DBStore, self).__init__(repository)

        self._versions = VersionContainer(self)
        self._values = ValueContainer(self)
        self._items = ItemContainer(self)
        self._refs = RefContainer(self)
        self._names = NamesContainer(self)
        self._lobs = LOBContainer(self)
        self._index = IndexContainer(self)
        self._acls = ACLContainer(self)
        self._indexes = IndexesContainer(self)
        self._commits = CommitsContainer(self)

    def open(self, **kwds):

        if kwds.get('ramdb', False):
            self._ramdb = True
            self._mvcc = False
        else:
            self._ramdb = False
            self._mvcc = kwds.get('mvcc', False)
            if self._mvcc:
                self.repository.logger.info('mvcc is enabled')

        txnStatus = 0
        try:
            txnStatus = self.startTransaction(None)
            txn = self.txn

            self._versions.open("__versions.db", txn, **kwds)
            self._values.open("__values.db", txn, **kwds)
            self._items.open("__items.db", txn, **kwds)
            self._refs.open("__refs.db", txn, **kwds)
            self._names.open("__names.db", txn, **kwds)
            self._lobs.open("__lobs.db", txn, **kwds)
            self._index.open("__index.db", txn, **kwds)
            self._acls.open("__acls.db", txn, **kwds)
            self._indexes.open("__indexes.db", txn, **kwds)
            self._commits.open("__commits.db", txn, **kwds)
        except DBNoSuchFileError:
            self.abortTransaction(None, txnStatus)
            raise
        except RepositoryVersionError:
            self.abortTransaction(None, txnStatus)
            raise
        else:
            self.commitTransaction(None, txnStatus)

    def close(self):

        self._versions.close()
        self._values.close()
        self._items.close()
        self._refs.close()
        self._names.close()
        self._lobs.close()
        self._index.close()
        self._acls.close()
        self._indexes.close()
        self._commits.close()

    def attachView(self, view):

        self._versions.attachView(view)
        self._values.attachView(view)
        self._items.attachView(view)
        self._refs.attachView(view)
        self._names.attachView(view)
        self._lobs.attachView(view)
        self._index.attachView(view)
        self._acls.attachView(view)
        self._indexes.attachView(view)
        self._commits.attachView(view)

    def detachView(self, view):

        self._versions.detachView(view)
        self._values.detachView(view)
        self._items.detachView(view)
        self._refs.detachView(view)
        self._names.detachView(view)
        self._lobs.detachView(view)
        self._index.detachView(view)
        self._acls.detachView(view)
        self._indexes.detachView(view)
        self._commits.detachView(view)

    def compact(self, progressFn=Nil):

        stage = "compacting databases"

        if progressFn(stage, 0) is False:
            return
        self._versions.compact()

        if progressFn(stage, 10) is False:
            return
        self._values.compact()

        if progressFn(stage, 20) is False:
            return
        self._items.compact()

        if progressFn(stage, 30) is False:
            return
        self._refs.compact()

        if progressFn(stage, 40) is False:
            return
        self._names.compact()

        if progressFn(stage, 50) is False:
            return
        self._lobs.compact()

        if progressFn(stage, 60) is False:
            return
        self._index.compact()

        if progressFn(stage, 70) is False:
            return
        self._acls.compact()

        if progressFn(stage, 80) is False:
            return
        self._indexes.compact()

        if progressFn(stage, 90) is False:
            return
        self._commits.compact()
        
    def loadItem(self, view, version, uuid):

        version, item = self._items.c.findItem(view, version, uuid,
                                               ItemContainer.NO_DIRTIES_TYPES)
        if item is None:
            return None

        itemReader = DBItemReader(self, uuid, version, item)
        if itemReader.isDeleted():
            return None

        return itemReader

    def loadItemName(self, view, version, uuid):

        return self._items.getItemName(view, version, uuid)

    def loadValue(self, view, version, uItem, name):

        status, uValue = self._items.findValue(view, version, uItem,
                                               _hash(name))
        if uValue in (Nil, Default):
            return None, uValue

        return DBValueReader(self, uItem, status, version), uValue
    
    def loadValues(self, view, version, uItem, names=None):

        hashes = [_hash(name) for name in names] if names is not None else None
        status, uValues = self._items.findValues(view, version, uItem, hashes)
        if status is None:
            return None, uValues

        return DBValueReader(self, uItem, status, version), uValues
    
    def hasValue(self, view, version, uItem, name):

        status, uValue = self._items.findValue(view, version, uItem,
                                               _hash(name))
        return uValue not in (Nil, Default)
    
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

    def loadACL(self, view, version, uuid, name):

        return self._acls.readACL(view, version, uuid, name)

    def saveACL(self, version, uuid, name, acl):

        return self._acls.writeACL(version, uuid, name, acl)

    def queryItems(self, view, version, kind=None, attribute=None):

        if kind is not None:
            items = self._items
            for uItem, vItem, item in items.kindQuery(view, version, kind):
                if items.getItemVersion(view, version, uItem) == vItem:
                    yield DBItemReader(self, uItem, vItem, item)

        elif attribute is not None:
            raise NotImplementedError, 'attribute query'

        else:
            raise ValueError, 'one of kind or value must be set'

    def queryItemKeys(self, view, version, kind=None, attribute=None):

        if kind is not None:
            items = self._items
            itemFinder = items._itemFinder(view)
            for uItem, vItem in items.kindQuery(view, version, kind, True):
                if itemFinder.getVersion(version, uItem) == vItem:
                    yield uItem

        elif attribute is not None:
            raise NotImplementedError, 'attribute query'

        else:
            raise ValueError, 'one of kind or value must be set'

    def kindForKey(self, view, version, uuid):

        uuid = self._items.getItemKindId(view, version, uuid)
        if uuid == DBItemWriter.NOITEM:
            uuid = None

        return uuid

    def searchItems(self, view, query, uAttr=None):
        
        iterator = self._index.searchDocuments(view, view.itsVersion,
                                               query, uAttr)
        for uItem, uAttr in iterator:
            yield uItem, uAttr

    def iterItems(self, view, backwards=False):

        return self._items.iterItems(view, backwards)

    def iterItemVersions(self, view, uuid, fromVersion=1, toVersion=0,
                         backwards=False):

        return self._items.iterVersions(view, uuid, fromVersion, toVersion,
                                        backwards)

    def getItemVersion(self, view, version, uuid):

        return self._items.getItemVersion(view, version, uuid)

    def getVersion(self):

        return self._versions.getVersion()

    def nextVersion(self):

        return self._versions.nextVersion()

    def getSchemaInfo(self):

        return self._versions.getSchemaInfo()

    def getIndexVersion(self):

        return self._index.getIndexVersion()

    def setIndexVersion(self, version):

        return self._index.setIndexVersion(version)

    def saveViewData(self, version, view):

        return self._versions.saveViewData(version,
                                           view._status & view.SAVEMASK,
                                           view._newIndexes)

    def getViewData(self, version):

        return self._versions.getViewData(version)

    def logCommit(self, view, version, commitSize):

        self._commits.logCommit(view, version, commitSize)

    def iterCommits(self, view, fromVersion=1, toVersion=0):

        return self._commits.iterCommits(view, fromVersion, toVersion)

    def getCommit(self, version):

        return self._commits.getCommit(version)

    def startTransaction(self, view, nested=False, readOnly=True):

        locals = self._threaded
        txn = locals.get('txn')
        mvcc = readOnly and (view._mvcc if view is not None else True)

        if txn is None:
            status = Transaction.TXN_STARTED
            locals['txn'] = DBTransaction(self, None, status, mvcc)
        elif nested:
            self.repository.logger.warning("%s: nesting transaction", view)
            txns = locals.get('txns')
            if txns is None:
                locals['txns'] = [txn]
            else:
                locals['txns'].append(txn)
            status = Transaction.TXN_STARTED | Transaction.TXN_NESTED
            locals['txn'] = DBTransaction(self, txn._txn, status, mvcc)
        else:
            status = 0
            txn._count += 1

        return status

    def commitTransaction(self, view, status):

        locals = self._threaded
        txn = locals['txn']

        if txn is not None:
            if txn.commit():
                status = txn._status
                if status & Transaction.TXN_NESTED:
                    locals['txn'] = locals['txns'].pop()
                else:
                    locals['txn'] = None

        return status

    def abortTransaction(self, view, status):

        locals = self._threaded
        txn = locals['txn']

        if txn is not None:
            if txn.abort():
                status = txn._status
                if status & Transaction.TXN_NESTED:
                    locals['txn'] = locals['txns'].pop()
                else:
                    locals['txn'] = None

        return status

    def _getEnv(self):

        return self.repository._env

    def _getLockId(self):

        lockId = self._threaded.get('lockId')
        if lockId is None:
            lockId = self.repository._env.lock_id()
            self._threaded['lockId'] = lockId
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

    def _logDL(self):

        frame = sys._getframe(1)
        self.repository.logger.warning("Thread '%s' db deadlock detected at %s, line %d", threading.currentThread().getName(), frame.f_code.co_filename, frame.f_lineno)
        time.sleep(1)

    env = property(_getEnv)


class DBCheckpointThread(threading.Thread):

    def __init__(self, repository, interval=10):  # minutes

        super(DBCheckpointThread, self).__init__()

        self._repository = repository
        self._condition = threading.Condition(threading.Lock())
        self._alive = True

        self.enabled = True
        self.interval = interval * 60.0

        self.setDaemon(True)

    def run(self):

        repository = self._repository
        store = repository.store
        condition = self._condition
        lock = None

        repository.logger.info("%s: checkpointing every %d minutes",
                               repository, self.interval / 60)
        last = time.time()

        def checkpoint(before):
            try:
                lock = store.acquireLock()
                repository.checkpoint()
                after = time.time()
                duration = after - before
                repository.logger.info('%s: %s, completed checkpoint in %s',
                                       repository, datetime.now(),
                                       timedelta(seconds=duration))
            finally:
                lock = store.releaseLock(lock)
            return after

        while self._alive:
            condition.acquire()
            if self._alive:
                condition.wait(60.0) # seconds
            condition.release()

            if not (self._alive and self.isAlive()):
                break

            if self.enabled:
                before = time.time()
                if before - last > self.interval:
                    last = checkpoint(before)
                elif len(repository._env.log_archive(DBEnv.DB_ARCH_LOG)) >= 8:
                    last = checkpoint(before)

    def terminate(self):
        
        if self._alive and self.isAlive():
            condition = self._condition

            condition.acquire()
            self._alive = False
            condition.notify()
            condition.release()

            self._repository.checkpoint()
            self.join()


class DBIndexerThread(RepositoryThread):

    def __init__(self, repository, interval=60):

        super(DBIndexerThread, self).__init__(name='__indexer__')

        self._repository = repository
        self._condition = threading.Condition(threading.Lock())
        self._alive = True
        self.interval = interval

        self.setDaemon(True)

    def run(self):

        repository = self._repository
        store = repository.store
        condition = self._condition
        view = None

        while self._alive:
            condition.acquire()
            if self._alive:
                condition.wait(self.interval)
            condition.release()

            try:
                if not (self._alive and self.isAlive()):
                    break

                while True:
                    txnStatus = 0
                    try:
                        txnStatus = store.startTransaction(None)
                        latestVersion = store.getVersion()
                        indexVersion = store.getIndexVersion()
                    except DBLockDeadlockError:
                        store.abortTransaction(None, txnStatus)
                        store._logDL()
                        continue
                    except:
                        store.abortTransaction(None, txnStatus)
                        raise
                    else:
                        store.abortTransaction(None, txnStatus)
                        break

                if indexVersion < latestVersion:
                    if view is None:
                        view = repository.createView("Lucene", pruneSize=400,
                                                     notify=False)
                    while indexVersion < latestVersion:
                        view.refresh(version=indexVersion + 1)
                        self._indexVersion(view, indexVersion + 1, store)
                        indexVersion += 1
            finally:
                condition.acquire()
                condition.notifyAll()
                condition.release()

        if view is not None:
            view.closeView()

    def _indexVersion(self, view, version, store):

        items = store._items

        while True:
            count = 0
            before = datetime.now()
            txnStatus = None
            lock = None

            try:
                lock = store.acquireLock()

                try:
                    txnStatus = view._startTransaction(False, False)
                    status, newIndexes = store.getViewData(version)
                    if status & view.TOINDEX:
                        for (uItem, ver, uKind, status, uParent, pKind,
                             dirties) in items.iterHistory(view, version - 1,
                                                           version):
                            if status & CItem.TOINDEX:
                                if status & CItem.NEW:
                                    dirties = None
                                else:
                                    dirties = list(dirties)
                                self._indexItem(view, ver, store,
                                                uItem, dirties)
                                count += 1

                    store.setIndexVersion(version)
                    view._commitTransaction(txnStatus)

                except DBLockDeadlockError:
                    view._abortTransaction(txnStatus)
                    store._logDL()
                    continue
                except DBInvalidArgError:
                    view._abortTransaction(txnStatus)
                    store._logDL()
                    continue
                except Exception:
                    if txnStatus is not None:
                        view._abortTransaction(txnStatus)
                    raise
                else:
                    if count:
                        after = datetime.now()
                        store.repository.logger.info("%s indexed %d items in %s", view, count, after - before)
                    return

            finally:
                lock = store.releaseLock(lock)

    def _indexItem(self, view, version, store, uItem, dirties):

        status, uValues = store._items.findValues(view, version, uItem,
                                                  dirties, True)
        reader = DBValueReader(store, uItem, status, version)

        for uValue in uValues:
            if uValue is not None:
                uAttr, value = reader.readValue(view, uValue, True)
                if value is not Nil:
                    if isinstance(value, Indexable):
                        value.indexValue(view, uItem, uAttr, uValue, version)
                    else:
                        attrType = getattr(view[uAttr], 'type', None)
                        if attrType is None:
                            valueType = TypeHandler.typeHandler(view, value)
                        elif attrType.isAlias():
                            valueType = attrType.type(value)
                        else:
                            valueType = attrType
                        store._index.indexValue(view._getIndexWriter(),
                                                valueType.makeUnicode(value),
                                                uItem, uAttr, uValue, version)

    def notify(self, wait=False):

        if self._alive and self.isAlive():
            condition = self._condition

            condition.acquire()
            condition.notify()
            if wait:
                condition.wait()
            condition.release()

    def terminate(self):
        
        if self._alive and self.isAlive():
            condition = self._condition

            condition.acquire()
            self._alive = False
            condition.notify()
            condition.release()

            self.join()
