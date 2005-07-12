
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from struct import pack, unpack
from cStringIO import StringIO
from time import time

from PyLucene import DbDirectory, IndexWriter, StandardAnalyzer
from PyLucene import IndexSearcher, QueryParser
from PyLucene import Document, Field

from chandlerdb.util.uuid import UUID
from repository.persistence.DBContainer import DBContainer
from repository.persistence.RepositoryError import RepositoryError


class FileContainer(DBContainer):

    def createFile(self, name):

        return OutputStream(self, name, True)

    def appendFile(self, name):

        return OutputStream(self, name, False)

    def deleteFile(self, name):

        File(self, name).delete()

    def fileExists(self, name):

        return File(self, name).exists()

    def fileLength(self, name):

        file = File(self, name)

        if file.exists():
            return file.getLength()

        raise RepositoryError, "File does not exist: %s" %(name)
    
    def fileModified(self, name):

        file = File(self, name)

        if file.exists():
            return file.getTimeModified()

        raise RepositoryError, "File does not exist: %s" %(name)

    def list(self):

        cursor = None
        results = []

        while True:
            try:
                cursor = self.openCursor()
            
                try:
                    value = cursor.set_range('', flags=self._flags,
                                             dlen=0, doff=0)
                except DBNotFoundError:
                    return results
                except DBLockDeadlockError:
                    self._logDL(7)
                    continue

                else:
                    while value is not None:
                        value = value[0]
                        length = unpack('>H', value[0:2])[0]
                        results.append(value[2:2+length])

                        while True:
                            try:
                                value = cursor.next()
                                break
                            except DBLockDeadlockError:
                                self._logDL(6)
                        
                    return results

            finally:
                self.closeCursor(cursor)

    def openFile(self, name):

        return InputStream(self, name)

    def renameFile(self, old, new):

        File(self, old).rename(new)

    def touchFile(self, name):

        file = File(self, name)
        length = 0
        
        if file.exists():
            length = file.getLength()

        file.modify(length, long(time() * 1000))


class BlockContainer(DBContainer):
    pass


class File(object):

    def __init__(self, container, name, create=False):

        super(File, self).__init__()

        self._container = container
        self.setName(name)

        if not self.exists():
            if not create:
                raise RepositoryError, "File does not exist: %s" %(name)

            self._uuid = UUID()
            self.length = 0
            
        elif create:
            self.length = 0

    def getName(self):

        return self.name

    def setName(self, name):

        if isinstance(name, unicode):
            name = name.encode('utf-8')

        self._key = "%s%s" %(pack('>H', len(name)), name)
        self.name = name

    def getKey(self):

        try:
            return self._uuid
        except AttributeError:
            raise RepositoryError, "Uninitialized file"

    def getLength(self):

        return self.length

    def getTimeModified(self):

        try:
            return self.timeModified
        except AttributeError:
            raise RepositoryError, "Uninitialized file"

    def exists(self):

        value = self._container.get(self._key)
        if value is None:
            return False
        
        zero, self.length, timeHi, timeLo, uuid = unpack('>LLLL16s', value)

        self.timeModified = timeHi << 32L | timeLo
        self._uuid = UUID(uuid)

        return True

    def modify(self, length, timeModified):

        timeHi = timeModified >> 32L
        timeLo = timeModified & 0xffffffffL
        uuid = self.getKey()._uuid
        
        data = pack('>LLLL16s', 0L, length, timeHi, timeLo, uuid)
        self._container.put(self._key, data)
        
        self.length = length
        self.timeModified = timeModified

    def delete(self):

        if not self.exists():
            raise RepositoryError, "File does not exist: %s" %(self.getName())

        cursor = None
        blocks = self._container.store._blocks
        
        try:
            cursor = blocks.openCursor()
            key = self.getKey()._uuid
            
            try:
                value = cursor.set_range(key, flags=self._flags,
                                         dlen=0, doff=0)
            except DBNotFoundError:
                pass
            else:
                while value is not None and value[0].startswith(key):
                    cursor.delete()
                    value = cursor.next()

            self._container.delete(self._key)

        finally:
            blocks.closeCursor(cursor)

    def rename(self, name):

        if not self.exists():
            raise RepositoryError, "File does not exist: %s" %(self.getName())

        newFile = File(self._container, name)

        if newFile.exists():
            newFile.delete()

        data = self._container.get(self._key)
        self._container.delete(self._key)
        self.setName(name)
        self._container.put(self._key, data)


class Block(object):

    def __init__(self, container, file):

        super(Block, self).__init__()

        self._container = container
        self._key = pack('>16sll', file.getKey()._uuid, 0L, 0L)
        self._data = None

    def getKey(self):

        return self._key

    def getData(self):

        return self._data

    def seek(self, position, write=False):

        key = pack('>16sll', self._key[0:16], 0L,
                   position >> OutputStream.BLOCK_SHIFT)

        if self._data is None or key != self._key:
            self._key = key
            data = self._container.get(self._key)

            if data is not None:
                if write:
                    self._data = StringIO()
                    self._data.write(data)
                else:
                    self._data = StringIO(data)
            else:
                self._data = StringIO()

        self._data.seek(position & OutputStream.BLOCK_MASK)

    def put(self):

        if self._data is not None:
            data = self._data.getvalue()
            self._data.close()
            self._container.put(self._key, data)


class OutputStream(object):

    BLOCK_SHIFT = 14L
    BLOCK_LEN = 1L << BLOCK_SHIFT
    BLOCK_MASK = BLOCK_LEN - 1L

    def __init__(self, container, name, create=False):

        super(OutputStream, self).__init__()

        self._container = container
        self._file = File(container, name, create)
        self._block = Block(container.store._blocks, self._file)
        self.length = self._file.getLength()
        self.position = 0

        self.seek(self.length);

    def close(self):

        if self.length > 0:
            self._block.put()

        self._file.modify(self.length, long(time() * 1000))

    def write(self, buffer, length = -1):

        blockPos = self.position & OutputStream.BLOCK_MASK
        offset = 0
        if length < 0:
            length = len(buffer)

        while blockPos + length >= OutputStream.BLOCK_LEN:
            blockLen = OutputStream.BLOCK_LEN - blockPos

            self._block.getData().write(buffer[offset:offset+blockLen])
            self._block.put()

            length -= blockLen
            offset += blockLen
            self.position += blockLen

            self._block.seek(self.position, True)
            blockPos = 0

        if length > 0:
            if offset == 0 and length == len(buffer):
                self._block.getData().write(buffer)
            else:
                self._block.getData().write(buffer[offset:offset+length])
            self.position += length

        if self.position > self.length:
            self.length = self.position

    def seek(self, pos):

        if pos > self.length:
            raise RepositoryError, "Seeking past end of file"

        if ((pos >> OutputStream.BLOCK_SHIFT) !=
            (self.position >> OutputStream.BLOCK_SHIFT)):
            self._block.put()

        self._block.seek(pos, True)
        self.position = pos

    def length(self):
        return self.length

    def flush(self):
        pass


class InputStream(object):

    def __init__(self, container, name):

        super(InputStream, self).__init__()

        self._container = container
        self._file = File(container, name)

        if not self._file.exists():
            raise RepositoryError, "File does not exist: %s" %(name)

        self.length = self._file.getLength()
        self._block = Block(container.store._blocks, self._file)

        self.seek(0L)
        
    def close(self):
        pass

    def read(self, length = -1):

        blockPos = self.position & OutputStream.BLOCK_MASK
        offset = 0
        buffer = None
        data = ''

        if length < 0:
            length = self.length - self.position

        if self.position + length > self.length:
            length = self.length - self.position

        while blockPos + length >= OutputStream.BLOCK_LEN:
            blockLen = OutputStream.BLOCK_LEN - blockPos

            if buffer is None:
                buffer = StringIO()

            buffer.write(self._block.getData().read(blockLen))

            length -= blockLen
            offset += blockLen
            self.position += blockLen

            self._block.seek(self.position)
            blockPos = 0

        if length > 0:
            data = self._block.getData().read(length)
            if buffer is not None:
                buffer.write(data)
            self.position += length

        if buffer is not None:
            data = buffer.getvalue()
            buffer.close()

        return data

    def seek(self, pos):

        if pos > self.length:
            raise RepositoryError, "seeking past end of file"

        self._block.seek(pos)
        self.position = pos


class IndexContainer(FileContainer):

    def open(self, name, txn, **kwds):

        super(IndexContainer, self).open(name, txn, **kwds)

        if kwds.get('create', False):
            directory = DbDirectory(txn, self._db, self.store._blocks._db,
                                    self._flags)
            indexWriter = IndexWriter(directory, StandardAnalyzer(), True)
            indexWriter.close()

    def getIndexWriter(self):

        writer = IndexWriter(DbDirectory(self.store.txn,
                                         self._db, self.store._blocks._db,
                                         self._flags),
                             StandardAnalyzer(), False)
        writer.setUseCompoundFile(False)

        return writer

    def indexDocument(self, indexWriter, reader,
                      uuid, owner, attribute, version):

        doc = Document()
        doc.add(Field("uuid", uuid.str16(), True, False, False))
        doc.add(Field("owner", owner.str16(), True, False, False))
        doc.add(Field("attribute", attribute, True, False, False))
        doc.add(Field("version", str(version), True, False, False))
        doc.add(Field.Text("contents", reader))

        indexWriter.addDocument(doc)

    def optimizeIndex(self, indexWriter):

        indexWriter.optimize()

    def searchDocuments(self, version, query):

        directory = DbDirectory(self.store.txn,
                                self._db, self.store._blocks._db,
                                self._flags)
        searcher = IndexSearcher(directory)
        query = QueryParser.parse(query, "contents", StandardAnalyzer())

        docs = {}
        for i, doc in searcher.search(query):
            ver = long(doc['version'])
            if ver <= version:
                uuid = UUID(doc['owner'])
                dv = docs.get(uuid, None)
                if dv is None or dv[0] < ver:
                    docs[uuid] = (ver, doc['attribute'])

        searcher.close()

        return docs
