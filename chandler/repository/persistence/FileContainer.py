#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


from struct import pack, unpack
from cStringIO import StringIO
from time import time

from PyLucene import \
    Document, Field, RAMDirectory, DbDirectory, StandardAnalyzer, \
    QueryParser, IndexReader, IndexWriter, IndexSearcher, Term, TermQuery, \
    JavaError, MatchAllDocsQuery

from chandlerdb.util.c import UUID
from chandlerdb.persistence.c import DBLockDeadlockError, DBInvalidArgError

from repository.persistence.DBContainer import DBContainer, ValueContainer
from repository.persistence.RepositoryError import RepositoryError


class FileContainer(DBContainer):

    def createFile(self, name):

        return OutputStream(self, name, True)

    def appendFile(self, name):

        return OutputStream(self, name, False)

    def deleteFile(self, name):

        return File(self, name).delete()

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
                value = cursor.first(self._flags)

                while value is not None:
                    value = value[0]
                    length = unpack('>H', value[0:2])[0]
                    results.append(value[2:2+length])

                    while True:
                        try:
                            value = cursor.next(self._flags, None)
                            break
                        except DBLockDeadlockError:
                            self.store._logDL()
                        
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


class LOBContainer(FileContainer):

    def purgeLob(self, txn, uLob):
    
        count = self.deleteFile(uLob._uuid)
        self.delete(uLob._uuid, txn)

        return 1, count


class File(object):

    def __init__(self, container, name, create=False, value=None):

        super(File, self).__init__()

        self._container = container
        self.setName(name)

        if not self.exists():
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
        
        zero, self.length, self.timeModified, uuid = unpack('>LLQ16s', value)
        self._uuid = UUID(uuid)

        return True

    def modify(self, length, timeModified):

        data = pack('>LLQ16s', 0L, length, timeModified, self.getKey()._uuid)
        self._container.put(self._key, data)
        
        self.length = length
        self.timeModified = timeModified

    def delete(self):

        count = 0
        cursor = None
        blocks = self._container.store._blocks
        
        try:
            cursor = blocks.openCursor()
            key = self.getKey()._uuid
            
            value = cursor.set_range(key, blocks._flags, None)
            while value is not None and value[0].startswith(key):
                cursor.delete()
                count += 1
                value = cursor.next(blocks._flags, None)

            self._container.delete(self._key)

        finally:
            blocks.closeCursor(cursor)

        return count

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

    def getIndexVersion(self):

        value = self.get(ValueContainer.VERSION_KEY)
        if value is None:
            return 0
        else:
            return unpack('>l', value)[0]

    def setIndexVersion(self, version):

        self.put(ValueContainer.VERSION_KEY, pack('>l', version))
        
    def getDirectory(self):

        return DbDirectory(self.store.txn, self._db, self.store._blocks._db,
                           self._flags)

    def getIndexReader(self):

        return IndexReader.open(self.getDirectory())

    def getIndexSearcher(self):

        return IndexSearcher(self.getDirectory())

    def getIndexWriter(self):

        writer = IndexWriter(RAMDirectory(), StandardAnalyzer(), True)
        writer.setUseCompoundFile(False)

        return writer

    def commitIndexWriter(self, writer):

        try:
            writer.close()
            dbWriter = IndexWriter(self.getDirectory(),
                                   StandardAnalyzer(), False)
            dbWriter.setUseCompoundFile(False)
            dbWriter.addIndexes([writer.getDirectory()])
            dbWriter.close()
            dbWriter.getDirectory().close()
            writer.getDirectory().close()
        except JavaError, e:
            je = e.getJavaException()
            msg = je.getMessage()
            if msg is not None and msg.find("DB_LOCK_DEADLOCK") >= 0:
                raise DBLockDeadlockError, msg
            if je.getClass().getName() == 'java.lang.IllegalArgumentException':
                raise DBInvalidArgError, msg
            raise

    def abortIndexWriter(self, writer):

        writer.close()
        writer.getDirectory().close()

    def indexValue(self, indexWriter, value, uItem, uAttr, uValue, version):

        STORED = Field.Store.YES
        UN_STORED = Field.Store.NO
        TOKENIZED = Field.Index.TOKENIZED
        UN_INDEXED = Field.Index.NO
        UN_TOKENIZED = Field.Index.UN_TOKENIZED

        doc = Document()
        doc.add(Field("item", uItem.str64(), STORED, UN_TOKENIZED))
        doc.add(Field("attribute", uAttr.str64(), STORED, UN_INDEXED))
        doc.add(Field("value", uValue.str64(), STORED, UN_INDEXED))
        doc.add(Field("version", str(version), STORED, UN_INDEXED))
        doc.add(Field("contents", value, UN_STORED, TOKENIZED,
                      Field.TermVector.YES))

        indexWriter.addDocument(doc)

    def indexReader(self, indexWriter, reader, uItem, uAttr, uValue, version):

        STORED = Field.Store.YES
        UN_INDEXED = Field.Index.NO
        UN_TOKENIZED = Field.Index.UN_TOKENIZED

        doc = Document()
        doc.add(Field("item", uItem.str64(), STORED, UN_TOKENIZED))
        doc.add(Field("attribute", uAttr.str64(), STORED, UN_INDEXED))
        doc.add(Field("value", uValue.str64(), STORED, UN_INDEXED))
        doc.add(Field("version", str(version), STORED, UN_INDEXED))
        doc.add(Field("contents", reader, Field.TermVector.YES))

        indexWriter.addDocument(doc)

    def optimizeIndex(self, indexWriter):

        indexWriter.optimize()

    def searchDocuments(self, version, query=None, attribute=None):

        searcher = self.getIndexSearcher()

        if query is None:
            query = MatchAllDocsQuery()
        else:
            query = QueryParser("contents", StandardAnalyzer()).parse(query)

        docs = {}
        for i, doc in searcher.search(query):
            ver = long(doc['version'])
            if ver <= version:
                uItem = UUID(doc['item'])
                dv = docs.get(uItem, None)
                if dv is None or dv[0] < ver:
                    uAttr = UUID(doc['attribute'])
                    if attribute is None or attribute == uAttr:
                        docs[uItem] = (ver, uAttr, UUID(doc['value']))

        searcher.close()

        return docs

    def purgeDocuments(self, indexSearcher, indexReader, uItem, keeps):

        term = Term("item", uItem.str64())

        if keeps:
            count = 0
            prevs = {}

            for hit in indexSearcher.search(TermQuery(term)):
                id = hit.getId()
                doc = hit.getDocument()
                uAttr = UUID(doc['attribute'])

                if uAttr in keeps:
                    ver = long(doc['version'])
                    prev = prevs.get(uAttr)

                    if prev is None:
                        prevs[uAttr] = (id, ver)
                    elif ver > prev[1]:
                        indexReader.deleteDocument(prev[0])
                        count += 1
                        prevs[uAttr] = (id, ver)

                else:
                    indexReader.deleteDocument(id)
                    count += 1

        else:
            count = indexReader.deleteDocuments(term)

        return count

    def undoDocuments(self, indexSearcher, indexReader, uItem, version):

        term = Term("item", uItem.str64())

        for hit in indexSearcher.search(TermQuery(term)):
            if long(hit.getDocument()['version']) == version:
                indexReader.deleteDocument(hit.getId())
