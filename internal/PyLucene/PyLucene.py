# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyLucene

for fn in dir(_PyLucene):
    if fn.startswith("delete_"):
        setattr(_PyLucene, fn, lambda self: None)


class Object(object):
    def __repr__(self):
        return "<C java::lang::Object instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_Object(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __del__(self, destroy=_PyLucene.delete_Object):
        try:
            if self.thisown: destroy(self)
        except: pass

class ObjectPtr(Object):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Object
_PyLucene.Object_swigregister(ObjectPtr)

class Reader(Object):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C java::io::Reader instance at %s>" % (self.this,)

class ReaderPtr(Reader):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Reader
_PyLucene.Reader_swigregister(ReaderPtr)


attachCurrentThread = _PyLucene.attachCurrentThread
class Directory(Object):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C org::apache::lucene::store::Directory instance at %s>" % (self.this,)
    def __del__(self, destroy=_PyLucene.delete_Directory):
        try:
            if self.thisown: destroy(self)
        except: pass

class DirectoryPtr(Directory):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Directory
_PyLucene.Directory_swigregister(DirectoryPtr)

class DbDirectory(Directory):
    def __repr__(self):
        return "<C org::apache::lucene::store::db::DbDirectory instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_DbDirectory(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __del__(self, destroy=_PyLucene.delete_DbDirectory):
        try:
            if self.thisown: destroy(self)
        except: pass

class DbDirectoryPtr(DbDirectory):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = DbDirectory
_PyLucene.DbDirectory_swigregister(DbDirectoryPtr)

class Analyzer(Object):
    def __repr__(self):
        return "<C org::apache::lucene::analysis::Analyzer instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_Analyzer(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __del__(self, destroy=_PyLucene.delete_Analyzer):
        try:
            if self.thisown: destroy(self)
        except: pass

class AnalyzerPtr(Analyzer):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Analyzer
_PyLucene.Analyzer_swigregister(AnalyzerPtr)

class StandardAnalyzer(Analyzer):
    def __repr__(self):
        return "<C org::apache::lucene::analysis::standard::StandardAnalyzer instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_StandardAnalyzer(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __del__(self, destroy=_PyLucene.delete_StandardAnalyzer):
        try:
            if self.thisown: destroy(self)
        except: pass

class StandardAnalyzerPtr(StandardAnalyzer):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = StandardAnalyzer
_PyLucene.StandardAnalyzer_swigregister(StandardAnalyzerPtr)

class Field(Object):
    def __repr__(self):
        return "<C org::apache::lucene::document::Field instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_Field(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    Text = staticmethod(_PyLucene.Field_Text)
    UnIndexed = staticmethod(_PyLucene.Field_UnIndexed)
    UnStored = staticmethod(_PyLucene.Field_UnStored)
    def __del__(self, destroy=_PyLucene.delete_Field):
        try:
            if self.thisown: destroy(self)
        except: pass

class FieldPtr(Field):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Field
_PyLucene.Field_swigregister(FieldPtr)

Field_Text = _PyLucene.Field_Text

Field_UnIndexed = _PyLucene.Field_UnIndexed

Field_UnStored = _PyLucene.Field_UnStored

class Document(Object):
    def __repr__(self):
        return "<C org::apache::lucene::document::Document instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_Document(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def add(*args): return _PyLucene.Document_add(*args)
    def get(*args): return _PyLucene.Document_get(*args)
    def __del__(self, destroy=_PyLucene.delete_Document):
        try:
            if self.thisown: destroy(self)
        except: pass

class DocumentPtr(Document):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Document
_PyLucene.Document_swigregister(DocumentPtr)

class IndexWriter(Object):
    def __repr__(self):
        return "<C org::apache::lucene::index::IndexWriter instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_IndexWriter(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def close(*args): return _PyLucene.IndexWriter_close(*args)
    def addDocument(*args): return _PyLucene.IndexWriter_addDocument(*args)
    def optimize(*args): return _PyLucene.IndexWriter_optimize(*args)
    maxFieldLength = property(_PyLucene.IndexWriter_maxFieldLength_get, _PyLucene.IndexWriter_maxFieldLength_set)
    mergeFactor = property(_PyLucene.IndexWriter_mergeFactor_get, _PyLucene.IndexWriter_mergeFactor_set)
    minMergeDocs = property(_PyLucene.IndexWriter_minMergeDocs_get, _PyLucene.IndexWriter_minMergeDocs_set)
    maxMergeDocs = property(_PyLucene.IndexWriter_maxMergeDocs_get, _PyLucene.IndexWriter_maxMergeDocs_set)
    def __del__(self, destroy=_PyLucene.delete_IndexWriter):
        try:
            if self.thisown: destroy(self)
        except: pass

class IndexWriterPtr(IndexWriter):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = IndexWriter
_PyLucene.IndexWriter_swigregister(IndexWriterPtr)

class Query(Object):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C org::apache::lucene::search::Query instance at %s>" % (self.this,)
    def setBoost(*args): return _PyLucene.Query_setBoost(*args)
    def getBoost(*args): return _PyLucene.Query_getBoost(*args)
    def toString(*args): return _PyLucene.Query_toString(*args)

class QueryPtr(Query):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Query
_PyLucene.Query_swigregister(QueryPtr)

class Hits(Object):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C org::apache::lucene::search::Hits instance at %s>" % (self.this,)
    def length(*args): return _PyLucene.Hits_length(*args)
    def doc(*args): return _PyLucene.Hits_doc(*args)
    def score(*args): return _PyLucene.Hits_score(*args)
    def id(*args): return _PyLucene.Hits_id(*args)

class HitsPtr(Hits):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Hits
_PyLucene.Hits_swigregister(HitsPtr)

class Searcher(Object):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C org::apache::lucene::search::Searcher instance at %s>" % (self.this,)
    def search(*args): return _PyLucene.Searcher_search(*args)

class SearcherPtr(Searcher):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Searcher
_PyLucene.Searcher_swigregister(SearcherPtr)

class IndexSearcher(Searcher):
    def __repr__(self):
        return "<C org::apache::lucene::search::IndexSearcher instance at %s>" % (self.this,)
    def __init__(self, *args):
        newobj = _PyLucene.new_IndexSearcher(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def close(*args): return _PyLucene.IndexSearcher_close(*args)
    def __del__(self, destroy=_PyLucene.delete_IndexSearcher):
        try:
            if self.thisown: destroy(self)
        except: pass

class IndexSearcherPtr(IndexSearcher):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = IndexSearcher
_PyLucene.IndexSearcher_swigregister(IndexSearcherPtr)

class QueryParser(Object):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<C org::apache::lucene::queryParser::QueryParser instance at %s>" % (self.this,)
    parse = staticmethod(_PyLucene.QueryParser_parse)

class QueryParserPtr(QueryParser):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = QueryParser
_PyLucene.QueryParser_swigregister(QueryParserPtr)

QueryParser_parse = _PyLucene.QueryParser_parse


