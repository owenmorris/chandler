/* File : PyLucene.i */

%module PyLucene

%pythoncode %{

for fn in dir(_PyLucene):
    if fn.startswith("delete_"):
        setattr(_PyLucene, fn, lambda self: None)

%}

%{

#include <gcj/cni.h>
#include <java/lang/Object.h>
#include <java/lang/Thread.h>
#include <java/lang/ThreadGroup.h>
#include <java/lang/Runnable.h>
#include <java/lang/String.h>
#include <java/lang/Throwable.h>
#include <java/io/StringWriter.h>
#include <java/io/PrintWriter.h>
#include <java/io/Reader.h>
#include <java/io/File.h>

#ifdef _WITH_DB_DIRECTORY
#include "com/sleepycat/db/DbEnv.h"
#include "com/sleepycat/db/Db.h"
#include "com/sleepycat/db/DbTxn.h"
#endif

#include "org/apache/lucene/store/Directory.h"
#include "org/apache/lucene/store/FSDirectory.h"

#ifdef _WITH_DB_DIRECTORY
#include "org/apache/lucene/store/db/DbDirectory.h"
#endif

#include "org/apache/lucene/analysis/Analyzer.h"
#include "org/apache/lucene/analysis/standard/StandardAnalyzer.h"
#include "org/apache/lucene/document/Field.h"
#include "org/apache/lucene/document/Document.h"
#include "org/apache/lucene/index/IndexWriter.h"
#include "org/apache/lucene/index/IndexReader.h"
#include "org/apache/lucene/index/Term.h"
#include "org/apache/lucene/index/TermDocs.h"
#include "org/apache/lucene/index/TermEnum.h"
#include "org/apache/lucene/index/TermPositions.h"
#include "org/apache/lucene/queryParser/QueryParser.h"
#include "org/apache/lucene/search/Searcher.h"
#include "org/apache/lucene/search/Query.h"
#include "org/apache/lucene/search/Hits.h"
#include "org/apache/lucene/search/IndexSearcher.h"
#include "org/osafoundation/io/PythonReader.h"

#ifdef _WITH_DB_DIRECTORY

#include <db.h>

/* from Python's _bsddb.c */
typedef struct {
    PyObject_HEAD
    DB_ENV *db_env;
} DBEnvObject;

typedef struct {
    PyObject_HEAD
    DB *db;
} DBObject;

typedef struct {
    PyObject_HEAD
    DB_TXN *txn;
} DBTxnObject;

typedef ::com::sleepycat::db::DbEnv *jdbenv;
typedef ::com::sleepycat::db::Db *jdb;
typedef ::com::sleepycat::db::DbTxn *jdbtxn;

#endif

typedef ::java::io::Reader *jreader;


#ifndef WIN32

extern "C" {
    void *GC_start_routine(void *arg);
}

static java::lang::Thread *nextThread;

static void *run(void *pyThread)
{
    _Jv_AttachCurrentThread(nextThread);
    nextThread = new java::lang::Thread();
    
    return PyObject_CallMethod((PyObject *) pyThread, "run", NULL);
}

void *attachCurrentThread(PyObject *pyThread)
{
    struct start_info {
        void *(*start_routine)(void *);
        void *arg;
        unsigned int flags;
        unsigned int registered;
    } si;

    si.registered = 0;
    si.start_routine = run;
    si.arg = pyThread;
    si.flags = 0;

    return GC_start_routine(&si);
}

#else

void *attachCurrentThread(PyObject *pyThread)
{
    JvAttachCurrentThread(NULL, NULL);

    return PyObject_CallMethod((PyObject *) pyThread, "run", NULL);
}

#endif

%}

%typemap(in) jstring {

    if ($input == Py_None)
        $1 = NULL;
    else
        $1 = JvNewStringUTF(PyString_AsString($input));
}

%typemap(out) jstring {

    if (!$1)
        $result = Py_None;
    else
    {
        jint len = JvGetStringUTFLength($1);
        char buf[len + 1];

        JvGetStringUTFRegion($1, 0, len, buf);
        buf[len] = '\0';
    
        $result = Py_BuildValue("s#", buf, len);
    }
}

%typemap(in) jboolean {

    $1 = PyObject_IsTrue($input);
}

%typemap(out) jboolean {

    $result = PyBool_FromLong((long) $1);
}

%typemap(in) jreader {

    if ($input == Py_None)
        $1 = NULL;
    else
    {
        jlong ptr;

        *(PyObject **) &ptr = (PyObject *) $input;
        $1 = new org::osafoundation::io::PythonReader(ptr);
    }
}

#ifdef _WITH_DB_DIRECTORY

%typemap(in) jdbenv {

    if ($input == Py_None)
        $1 = NULL;
    else
    {
        jlong ptr;

        *(DB_ENV **) &ptr = ((DBEnvObject *) $input)->db_env;
        $1 = new ::com::sleepycat::db::DbEnv(ptr, 0);
    }
}

%typemap(in) jdb {

    if ($input == Py_None)
        $1 = NULL;
    else
    {
        jlong ptr;

        *(DB **) &ptr = ((DBObject *) $input)->db;
        $1 = new ::com::sleepycat::db::Db(ptr, 0);
    }
}

%typemap(in) jdbtxn {

    if ($input == Py_None)
        $1 = NULL;
    else
    {
        jlong ptr;

        *(DB_TXN **) &ptr = ((DBTxnObject *) $input)->txn;
        $1 = new com::sleepycat::db::DbTxn(ptr, 0);
    }
}

#endif

typedef long jint;
typedef long long jlong;
typedef char jbyte;
typedef float jfloat;


%exception {

    try {
        $action
        if (PyErr_Occurred())
            return NULL;
    } catch (java::lang::Throwable *e) {
        java::io::StringWriter *buffer = new java::io::StringWriter();
	java::io::PrintWriter *writer = new java::io::PrintWriter(buffer);

	e->printStackTrace(writer);
	writer->close();

        jstring message = buffer->toString();
        jint len = JvGetStringUTFLength(message);
        char buf[len + 1];

        JvGetStringUTFRegion(message, 0, len, buf);
	buf[len] = '\0';
        PyErr_SetString(PyExc_ValueError, buf);
    
        return NULL;
    }
}

namespace java {
    namespace lang {
        class Object {
            virtual jstring toString();
        };
    }
    namespace io {
%nodefault;
        class Reader : public ::java::lang::Object {
        };
%makedefault;
    }
}

void *attachCurrentThread(PyObject *pyThread);

namespace org {
    namespace apache {
        namespace lucene {
            namespace store {
                class Directory : public ::java::lang::Object {
                    Directory();
                };
%nodefault;
                class FSDirectory : public Directory {
                public:
                    static FSDirectory *getDirectory(jstring, jboolean);
                };
%makedefault;
#ifdef _WITH_DB_DIRECTORY
                namespace db {
                    class DbDirectory : public Directory {
                    public:
                        DbDirectory(jdbtxn, jdb, jdb, jint);
                    };
                }
#endif
            }
            namespace analysis {
                class Analyzer : public ::java::lang::Object {
                };
                namespace standard {
                    class StandardAnalyzer : public Analyzer {
                    public:
                        StandardAnalyzer();
                    };
                }
            }

            namespace document {
                class Field : public ::java::lang::Object {
                public:
                    Field(jstring, jstring, jboolean, jboolean, jboolean);
                    static Field *Text(jstring, jreader);
                    static Field *UnIndexed(jstring, jstring);
                    static Field *UnStored(jstring, jstring);
                };
                class Document : public ::java::lang::Object {
                public:
                    Document();
                    void add(Field *);
                    jstring get(jstring);
                };
            }

            namespace index {
                class IndexWriter : public ::java::lang::Object {
                public:
                    IndexWriter(::org::apache::lucene::store::Directory *, ::org::apache::lucene::analysis::Analyzer *, jboolean);
                    virtual void close();
                    virtual void addDocument(::org::apache::lucene::document::Document *);
                    virtual void optimize();
                    jint maxFieldLength;
                    jint mergeFactor;
                    jint minMergeDocs;
                    jint maxMergeDocs;
                };
                class Term : public ::java::lang::Object {
                public:
                    Term(jstring, jstring);
                    jstring field();
                    jstring text();
                    jint compareTo(Term *);
                    jstring toString();
                };
%nodefault;
                class TermEnum : public ::java::lang::Object {
                public:
                    virtual jboolean next();
                    virtual Term *term();
                    virtual jint docFreq();
                    virtual void close();
                };
                class TermDocs : public ::java::lang::Object {
                public:
                    virtual void seek(Term *);
                    virtual void seek(TermEnum *);
                    virtual jint doc();
                    virtual jint freq();
                    virtual jboolean next();
                    virtual jboolean skipTo(jint);
                    virtual void close();
                };
                class TermPositions : public TermDocs {
                public:
                    virtual jint nextPosition();
                };
		class IndexReader : public ::java::lang::Object {
		public:
		    static IndexReader *open(jstring);
                    static IndexReader *open(::org::apache::lucene::store::Directory *);
                    static jlong lastModified(jstring);
                    static jlong lastModified(::org::apache::lucene::store::Directory *);
                    static jlong getCurrentVersion(jstring);
                    static jlong getCurrentVersion(::org::apache::lucene::store::Directory *);
                    static jboolean indexExists(jstring);
                    static jboolean indexExists(::org::apache::lucene::store::Directory *);
                    virtual jint numDocs();
                    virtual jint maxDoc();
                    virtual ::org::apache::lucene::document::Document *document (jint);
                    virtual jboolean isDeleted(jint);
                    virtual jboolean hasDeletions();
                    virtual void setNorm(jint, jstring, jbyte);
                    virtual void setNorm(jint, jstring, jfloat);
                    virtual TermEnum *terms();
                    virtual TermEnum *terms(Term *);
                    virtual jint docFreq(Term *);
                    virtual TermDocs *termDocs(Term *);
                    virtual TermDocs *termDocs();
                    virtual TermPositions *termPositions(Term *);
                    virtual TermPositions *termPositions();
%rename(deleteTerm) delete$;
//                    void delete$(jint);
//                    jint delete$(Term *);
                    virtual void undeleteAll();
                    void close();
                    static jboolean isLocked(::org::apache::lucene::store::Directory *);
                    static jboolean isLocked(jstring);
                    static void unlock(::org::apache::lucene::store::Directory *);
                };
%makedefault;
            }

	    namespace search {
%nodefault;
                class Query : public ::java::lang::Object {
                public:
                    virtual void setBoost(jfloat);
                    virtual jfloat getBoost();
                    virtual jstring toString();
                };
                class Hits : public ::java::lang::Object {
                public:
                    jint length();
                    ::org::apache::lucene::document::Document *doc(jint);
                    jfloat score(jint);
                    jint id(jint);
                };
                class Searcher : public ::java::lang::Object {
                public:
                    Hits *search(Query *);
                };
%makedefault;
                class IndexSearcher : public Searcher {
                public:
                    IndexSearcher(::org::apache::lucene::store::Directory *);
                    virtual void close();
                };
            }

            namespace queryParser {
%nodefault;
                class QueryParser : public ::java::lang::Object {
                public:
                    static ::org::apache::lucene::search::Query *parse(jstring, jstring, ::org::apache::lucene::analysis::Analyzer *);
                };
%makedefault;
            }
        }
    }
}

%init %{
    JvCreateJavaVM(NULL);
    JvAttachCurrentThread(NULL, NULL);
#ifndef WIN32
    nextThread = new java::lang::Thread();
#endif
    JvInitClass(&org::apache::lucene::document::Field::class$);
    JvInitClass(&org::apache::lucene::queryParser::QueryParser::class$);
%}
