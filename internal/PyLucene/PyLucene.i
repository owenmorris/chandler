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

#include "com/sleepycat/db/DbEnv.h"
#include "com/sleepycat/db/Db.h"
#include "com/sleepycat/db/DbTxn.h"

#include "org/apache/lucene/store/Directory.h"
#include "org/apache/lucene/store/FSDirectory.h"
#include "org/apache/lucene/store/db/DbDirectory.h"
#include "org/apache/lucene/analysis/Analyzer.h"
#include "org/apache/lucene/analysis/standard/StandardAnalyzer.h"
#include "org/apache/lucene/document/Field.h"
#include "org/apache/lucene/document/Document.h"
#include "org/apache/lucene/index/IndexWriter.h"
#include "org/apache/lucene/queryParser/QueryParser.h"
#include "org/apache/lucene/search/Searcher.h"
#include "org/apache/lucene/search/Query.h"
#include "org/apache/lucene/search/Hits.h"
#include "org/apache/lucene/search/IndexSearcher.h"
#include "org/osafoundation/io/PythonReader.h"

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

%typemap(in) jboolean {

    $1 = PyObject_IsTrue($input);
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

typedef int jint;
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
                namespace db {
                    class DbDirectory : public Directory {
                    public:
                        DbDirectory(jdbtxn, jdb, jdb, jint);
                    };
                }
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
