
import unittest, os, shutil
from PyLucene import *
from StringIO import StringIO

class InputStreamReader(object):

    def __init__(self, inputStream, encoding):

        super(InputStreamReader, self).__init__()
        self.inputStream = inputStream
        self.encoding = encoding

    def read(self, length = -1):

        text = self.inputStream.read(length)
        text = unicode(text, self.encoding)

        return text

    def close(self):

        self.inputStream.close()

class StringReader(object):

    def __init__(self, unicodeText):

        super(StringReader, self).__init__()
        self.unicodeText = unicodeText

    def read(self, length = -1):

        text = self.unicodeText
        if text is None:
            return ''
        
        if length == -1 or length >= len(text):
            self.unicodeText = None
            return text

        text = text[0:length]
        self.unicodeText = self.unicodeText[length:]

        return text

    def close(self):
        pass


class Test_PyLuceneBase:

    def getAnalyzer(self):
        return StandardAnalyzer()

    def getStore(self):
        raise NotImplemented

    def getWriter(self, store, analyzer, create_flag=0):
        return IndexWriter(store, analyzer, bool(create_flag))

    def test_indexDocument(self):
        store = self.getStore()        
        analyzer = self.getAnalyzer()
        writer = self.getWriter(store, analyzer, True)
        # initialize first, not sure if it matters
        writer.close()

        writer = self.getWriter(store, analyzer, True)
        doc = Document()
        doc.add(Field("title", "value of testing", True, True, True))
        doc.add(Field("docid", str(1), False, True, False))
        doc.add(Field("owner", "unittester", True, True, False))
        doc.add(Field.UnIndexed("search_name", "wisdom"))
        doc.add(Field.UnStored("meta_words", "rabbits are beautiful"))
        
        writer.addDocument(doc)
        writer.close()

        return store

    def test_indexDocumentWithText(self):
        store = self.getStore()        
        analyzer = self.getAnalyzer()
        writer = self.getWriter(store, analyzer, True)
        # initialize first, not sure if it matters
        writer.close()

        writer = self.getWriter(store, analyzer, True)
        doc = Document()
        doc.add(Field("title", "value of testing", True, True, True))
        doc.add(Field("docid", str(1), False, True, False))
        doc.add(Field("owner", "unittester", True, True, False))
        doc.add(Field.UnIndexed("search_name", "wisdom"))
        doc.add(Field.UnStored("meta_words", "rabbits are beautiful"))

        body_text = "hello world"*20
        body_stream = StringIO(body_text)
        body_reader = InputStreamReader( body_stream, "utf-8")
        doc.add(Field.Text("content", body_reader))

        writer.addDocument(doc)
        writer.close()

    def test_indexDocumentWithUnicodeText(self):
        store = self.getStore()        
        analyzer = self.getAnalyzer()
        writer = self.getWriter(store, analyzer, True)
        # initialize first, not sure if it matters
        writer.close()

        writer = self.getWriter(store, analyzer, True)
        doc = Document()
        doc.add(Field("title", "value of testing", True, True, True))
        doc.add(Field("docid", str(1), False, True, False))
        doc.add(Field("owner", "unittester", True, True, False))
        doc.add(Field.UnIndexed("search_name", "wisdom"))
        doc.add(Field.UnStored("meta_words", "rabbits are beautiful"))

        # using a unicode body cause problems, which seems very odd
        # since the python type is the same regardless affter doing
        # the encode
        body_text = u"hello world"*20
        body_reader = StringReader( body_text )
        doc.add(Field.Text("content", body_reader))

        writer.addDocument(doc)
        writer.close()        

    def test_searchDocuments(self):
        store = self.test_indexDocument()
        searcher = IndexSearcher( store )
        query = QueryParser.parse("value", "title", self.getAnalyzer() )
        hits = searcher.search(query)
        len = hits.length()
        self.assertEqual( len, 1)

class Test_PyLuceneWithFSStore(unittest.TestCase, Test_PyLuceneBase):

    STORE_DIR = "testrepo"

    def setUp(self):
        if not os.path.exists( self.STORE_DIR):
            os.mkdir( self.STORE_DIR )

    def tearDown(self):
        if os.path.exists( self.STORE_DIR ):
            shutil.rmtree( self.STORE_DIR )

    def getStore(self):
        return FSDirectory.getDirectory( self.STORE_DIR, True)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test_PyLuceneWithFSStore))
    return suite


if __name__ == '__main__':
    unittest.main()

