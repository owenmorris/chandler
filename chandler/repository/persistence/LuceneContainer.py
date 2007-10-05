#   Copyright (c) 2004-2007 Open Source Applications Foundation
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
from heapq import heapify, heappop

from lucene import \
    Document, Field, RAMDirectory, StandardAnalyzer, \
    QueryParser, IndexReader, IndexWriter, IndexSearcher, Term, TermQuery, \
    JavaError, MatchAllDocsQuery, BooleanQuery, BooleanClause, Hit, \
    StringReader, PythonDirectory, PythonIndexOutput, PythonIndexInput, \
    PythonLock, PythonHitCollector, initVM, CLASSPATH, IOException
initVM(CLASSPATH)

from chandlerdb.util.c import UUID
from chandlerdb.persistence.c import DBLockDeadlockError, DBInvalidArgError

from repository.persistence.FileContainer import FileContainer, RepositoryError
from repository.persistence.DBContainer import VersionContainer


class DbLock(PythonLock):

    def __init__(self, name):
        super(DbLock, self).__init__()
        self.name = name
        self.locked = False
        
    def isLocked(self):
        return self.locked

    def obtain(self, timeout=None):
        self.locked = True
        return True

    def release(self):
        self.locked = False

class DbIndexOutput(PythonIndexOutput):

    def __init__(self, stream):
        super(DbIndexOutput, self).__init__()
        self.stream = stream
        self.isOpen = True

    def close(self):
        if self.isOpen:
            super(DbIndexOutput, self).close()
            self.isOpen = False
            self.stream.close()

    def length(self):
        return long(self.stream.length)

    def seekInternal(self, pos):
        self.stream.seek(pos)

    def flushBuffer(self, buffer):
        self.stream.write(buffer)
        self.stream.flush()

class DbIndexInput(PythonIndexInput):

    def __init__(self, stream, bufferSize, clone=False):
        if not clone:
            super(DbIndexInput, self).__init__(bufferSize)
        self.stream = stream
        self.isOpen = True

    def length(self):
        return long(self.stream.length)

    def clone(self):
        clone = DbIndexInput(self.stream.clone(), 0, True)
        return super(DbIndexInput, self).clone(clone)

    def close(self):
        if self.isOpen:
            self.isOpen = False
            self.stream.close()

    def readInternal(self, length, pos):
        self.stream.seek(pos)
        return self.stream.read(length)

    def seekInternal(self, pos):
        self.stream.seek(pos)

class DbDirectory(PythonDirectory):

    def __init__(self, fileContainer):
        super(DbDirectory, self).__init__()
        self.fileContainer = fileContainer
        self._streams = []

    def close(self):
        for stream in self._streams:
            stream.close()
        del self._streams[:]

    def createOutput(self, name):
        stream = self.fileContainer.createFile(name)
        stream = DbIndexOutput(stream)
        self._streams.append(stream)
        return stream

    def deleteFile(self, name):
        if self.fileContainer.fileExists(name):
            self.fileContainer.deleteFile(name)

    def fileExists(self, name):
        return self.fileContainer.fileExists(name)

    def fileLength(self, name):
        return long(self.fileContainer.fileLength(name))

    def fileModified(self, name):
        return self.fileContainer.fileModified(name)

    def list(self):
        return self.fileContainer.list()

    def makeLock(self, name):
        return DbLock(name)

    def openInput(self, name, bufferSize=0):
        try:
            stream = self.fileContainer.openFile(name)
        except RepositoryError:
            raise JavaError, IOException(name)
        stream = DbIndexInput(stream, bufferSize)
        self._streams.append(stream)
        return stream

    def touchFile(self, name):
        self.fileContainer.touchFile(name)


class IndexContainer(FileContainer):

    BLOCK_SHIFT = 15
    BLOCK_LEN = 1 << BLOCK_SHIFT
    BLOCK_MASK = BLOCK_LEN - 1

    def open(self, name, txn, **kwds):

        super(IndexContainer, self).open(name, txn, **kwds)

        if kwds.get('create', False):
            directory = self.getDirectory()
            indexWriter = IndexWriter(directory, StandardAnalyzer(), True)
            indexWriter.close()
            directory.close()

    def getIndexVersion(self):

        value = self.get(VersionContainer.VERSION_KEY, self._blocks)
        if value is None:
            return 0
        else:
            return unpack('>l', value)[0]

    def setIndexVersion(self, version):

        self.put(VersionContainer.VERSION_KEY, pack('>l', version),
                 self._blocks)
        
    def getDirectory(self):

        return DbDirectory(self)

    def getIndexReader(self):

        return IndexReader.open(self.getDirectory())

    def getIndexSearcher(self):

        return IndexSearcher(self.getDirectory())

    def getIndexWriter(self):

        writer = IndexWriter(RAMDirectory(), StandardAnalyzer(), True)
        writer.setUseCompoundFile(False)

        return writer

    def commitIndexWriter(self, writer):

        directory = writer.getDirectory()
        writer.close()
        dbDirectory = self.getDirectory()
        dbWriter = IndexWriter(dbDirectory, StandardAnalyzer(), False)
        dbWriter.setUseCompoundFile(False)
        dbWriter.addIndexes([directory])
        directory.close()
        dbWriter.close()
        dbDirectory.close()

    def abortIndexWriter(self, writer):

        directory = writer.getDirectory()
        writer.close()
        directory.close()

    def indexValue(self, indexWriter, value, uItem, uAttr, uValue, version):

        STORED = Field.Store.YES
        UN_STORED = Field.Store.NO
        TOKENIZED = Field.Index.TOKENIZED
        UN_INDEXED = Field.Index.NO
        UN_TOKENIZED = Field.Index.UN_TOKENIZED

        doc = Document()
        doc.add(Field("item", uItem.str64(), STORED, UN_TOKENIZED))
        doc.add(Field("attribute", uAttr.str64(), STORED, UN_TOKENIZED))
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
        doc.add(Field("attribute", uAttr.str64(), STORED, UN_TOKENIZED))
        doc.add(Field("value", uValue.str64(), STORED, UN_INDEXED))
        doc.add(Field("version", str(version), STORED, UN_INDEXED))
        reader = StringReader(reader.read())
        doc.add(Field("contents", reader, Field.TermVector.YES))

        indexWriter.addDocument(doc)

    def optimizeIndex(self, indexWriter):

        indexWriter.optimize()

    def searchDocuments(self, view, version, query=None, attribute=None):

        store = self.store

        if query is None:
            query = MatchAllDocsQuery()
        else:
            query = QueryParser("contents", StandardAnalyzer()).parse(query)
        
        if attribute:
            combinedQuery = BooleanQuery()
            combinedQuery.add(query, BooleanClause.Occur.MUST)
            combinedQuery.add(TermQuery(Term("attribute", attribute.str64())),
                              BooleanClause.Occur.MUST)
            query = combinedQuery

        class _collector(PythonHitCollector):

            def __init__(_self):

                super(_collector, _self).__init__()
                _self.hits=[]

            def collect(_self, id, score):

                _self.hits.append((-score, id))
        
        class _iterator(object):

            def __init__(_self):

                _self.txnStatus = 0
                _self.searcher = None
                _self.collector = None

            def __del__(_self):

                try:
                    if _self.searcher is not None:
                        _self.searcher.close()
                    store.abortTransaction(view, _self.txnStatus)
                except:
                    store.repository.logger.exception("in __del__")

                _self.txnStatus = 0
                _self.searcher = None
                _self.collector = None

            def __iter__(_self):

                _self.txnStatus = store.startTransaction(view)
                _self.searcher = searcher = self.getIndexSearcher()
                _self.collector = _collector()

                searcher.search(query, _self.collector)
                hits = _self.collector.hits

                if hits:
                    heapify(hits)
                    while hits:
                        score, id = heappop(hits)
                        doc = searcher.doc(id)
                        uItem = UUID(doc['item'])
                        
                        if long(doc['version']) <= version:
                            if store._items.isValue(view, version, uItem,
                                                    UUID(doc['value'])):
                                yield uItem, UUID(doc['attribute'])

        return _iterator()

    def purgeDocuments(self, txn, counter, indexSearcher, indexReader,
                       uItem, toVersion=None):

        term = Term("item", uItem.str64())

        if toVersion is None:
            counter.documentCount += indexReader.deleteDocuments(term)

        else:
            x, keep = self.store._items.findValues(None, toVersion,
                                                   uItem, None, True)
            keep = set(keep)

            for hit in indexSearcher.search(TermQuery(term)):
                hit = Hit.cast_(hit)

                doc = hit.getDocument()
                ver = long(doc['version'])
                if ver <= toVersion and UUID(doc['value']) not in keep:
                    indexReader.deleteDocument(hit.getId())
                    counter.documentCount += 1

    def undoDocuments(self, indexSearcher, indexReader, uItem, version):

        term = Term("item", uItem.str64())

        for hit in indexSearcher.search(TermQuery(term)):
            hit = Hit.cast_(hit)
            if long(hit.getDocument()['version']) == version:
                indexReader.deleteDocument(hit.getId())
