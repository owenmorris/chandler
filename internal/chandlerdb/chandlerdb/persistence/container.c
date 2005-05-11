
/*
 * The container C type
 */

#if defined(_MSC_VER)
#include <winsock2.h>
#include <malloc.h>
#elif defined(__MACH__)
#include <arpa/inet.h>
#elif defined(linux)
#include <netinet/in.h>
#else
#error system is not linux, os x or winnt
#endif

#include <db.h>
#include <Python.h>
#include "structmember.h"

#include "../util/uuid.h"


#define LOAD_EXC(m, name) \
    PyExc_##name = PyObject_GetAttrString(m, #name)

#define LOAD_FN(m, name) \
    { PyObject *cobj = PyObject_GetAttrString(m, #name); \
      name = (name##_fn) PyCObject_AsVoidPtr(cobj); \
      Py_DECREF(cobj); }


typedef struct {
    PyObject_HEAD
    PyObject *db;
} t_container;

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

typedef enum {
    vt_UNKNOWN,
    vt_NONE,
    vt_BOOL,
    vt_UUID,
    vt_STRING,
    vt_UNICODE,
    vt_INT,
    vt_LONG
} valueType;

static void t_container_dealloc(t_container *self);
static PyObject *t_container_new(PyTypeObject *type,
                                 PyObject *args, PyObject *kwds);
static int t_container_init(t_container *self, PyObject *args, PyObject *kwds);

static PyUUID_Check_fn PyUUID_Check;
static PyUUID_Make16_fn PyUUID_Make16;

static PyMemberDef t_container_members[] = {
    { "db", T_OBJECT, offsetof(t_container, db), READONLY, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_container_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyMethodDef container_funcs[] = {
    { NULL, NULL, 0, NULL }
};

static PyTypeObject ContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.container.CContainer",       /* tp_name */
    sizeof(t_container),                                 /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_container_dealloc,                     /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    0,                                                   /* tp_repr */
    0,                                                   /* tp_as_number */
    0,                                                   /* tp_as_sequence */
    0,                                                   /* tp_as_mapping */
    0,                                                   /* tp_hash  */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    0,                                                   /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,            /* tp_flags */
    "C Container type",                                  /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_container_methods,                                 /* tp_methods */
    t_container_members,                                 /* tp_members */
    0,                                                   /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_container_init,                          /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_container_new,                            /* tp_new */
};


static void t_container_dealloc(t_container *self)
{
    Py_XDECREF(self->db);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_container_new(PyTypeObject *type,
                                 PyObject *args, PyObject *kwds)
{
    t_container *self = (t_container *) type->tp_alloc(type, 0);

    return (PyObject *) self;
}

static int t_container_init(t_container *self, PyObject *args, PyObject *kwds)
{
    PyObject *db;

    if (!PyArg_ParseTuple(args, "O", &db))
        return -1;

    Py_INCREF(db);
    self->db = db;

    return 0;
}

static PyObject *PyExc_DBLockDeadlockError;
static PyObject *PyExc_DBLockNotGrantedError;
static PyObject *PyExc_DBAccessError;
static PyObject *PyExc_DBInvalidArgError;
static PyObject *PyExc_DBNoSpaceError;
static PyObject *PyExc_DBError;

static PyObject *raiseDBError(int err)
{
    PyObject *tuple, *obj = NULL;

    switch (err) {
      case DB_LOCK_DEADLOCK:
        obj = PyExc_DBLockDeadlockError;
        break;
      case DB_LOCK_NOTGRANTED:
        obj = PyExc_DBLockNotGrantedError;
        break;
      case EACCES:
        obj = PyExc_DBAccessError;
        break;
      case EINVAL:
        obj = PyExc_DBInvalidArgError;
        break;
      case ENOSPC:
        obj = PyExc_DBNoSpaceError;
        break;
      default:
        obj = PyExc_DBError;
        break;
    }

    tuple = Py_BuildValue("(is)", err, db_strerror(err));
    PyErr_SetObject(obj, tuple);
    Py_DECREF(tuple);

    return NULL;
}

static int _size_valueType(PyObject *value, valueType *vt)
{
    if (value == Py_None)
    {
        *vt = vt_NONE;
        return 1;
    }

    if (value == Py_True || value == Py_False)
    {
        *vt = vt_BOOL;
        return 1;
    }

    if (PyUUID_Check(value))
    {
        *vt = vt_UUID;
        return 17;
    }

    if (PyString_CheckExact(value))
    {
        *vt = vt_STRING;
        return PyString_GET_SIZE(value) + 3;
    }

    if (PyUnicode_CheckExact(value))
    {
        *vt = vt_UNICODE;
        return (PyUnicode_GET_DATA_SIZE(value) * 5) / 4 + 3;
    }

    if (PyInt_CheckExact(value))
    {
        *vt = vt_INT;
        return 5;
    }

    if (PyLong_CheckExact(value))
    {
        *vt = vt_LONG;
        return 5;
    }

    *vt = vt_UNKNOWN;
    return 0;
}

static int _writeValue(char *buffer, PyObject *value, valueType vt)
{
    if (vt == vt_UNKNOWN)
        _size_valueType(value, &vt);

    switch (vt) {
      case vt_UNKNOWN:
        break;
      case vt_NONE:
      {
          buffer[0] = '\0';
          return 1;
      }
      case vt_BOOL:
      {
          if (value == Py_True)
          {
              buffer[0] = '\1';
              return 1;
          }
          else if (value == Py_False)
          {
              buffer[0] = '\2';
              return 1;
          }
      }
      case vt_UUID:
      {
          buffer[0] = '\3';
          memcpy(buffer + 1, PyString_AS_STRING(((t_uuid *) value)->uuid), 16);
          return 17;
      }
      case vt_STRING:
      {
          int len = PyString_GET_SIZE(value);

          buffer[0] = '\5';
          *((short *) (buffer + 1)) = htons(len);
          memcpy(buffer + 3, PyString_AS_STRING(value), len);

          return len + 3;
      }
      case vt_UNICODE:
      {
          PyObject *str = PyUnicode_AsUTF8String(value);
          int len = PyString_GET_SIZE(str);

          buffer[0] = '\5';
          *((short *) (buffer + 1)) = htons(len);
          memcpy(buffer + 3, PyString_AS_STRING(str), len);
          Py_DECREF(str);

          return len + 3;
      }
      case vt_INT:
      {
          buffer[0] = '\4';
          *((int *) (buffer + 1)) = htonl(PyInt_AS_LONG(value));

          return 5;
      }
      case vt_LONG:
      {
          buffer[0] = '\4';
          *((int *) (buffer + 1)) = htonl(PyInt_AsLong(value));

          return 5;
      }
    }

    PyErr_SetObject(PyExc_TypeError, value);
    return 0;
}


typedef struct {
    t_container container;
} t_value_container;


static void t_value_container_dealloc(t_value_container *self);
static PyObject *t_value_container_new(PyTypeObject *type,
                                       PyObject *args, PyObject *kwds);
static int t_value_container_init(t_value_container *self,
                                  PyObject *args, PyObject *kwds);
static PyObject *t_value_container_loadValue(t_value_container *self,
                                             PyObject *args);
static PyObject *t_value_container_saveValue(t_value_container *self,
                                             PyObject *args);


static PyMemberDef t_value_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_value_container_methods[] = {
    { "loadValue", (PyCFunction) t_value_container_loadValue, METH_VARARGS,
      "saveValue" },
    { "saveValue", (PyCFunction) t_value_container_saveValue, METH_VARARGS,
      "saveValue" },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject ValueContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.container.CValueContainer",  /* tp_name */
    sizeof(t_value_container),                           /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_value_container_dealloc,               /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    0,                                                   /* tp_repr */
    0,                                                   /* tp_as_number */
    0,                                                   /* tp_as_sequence */
    0,                                                   /* tp_as_mapping */
    0,                                                   /* tp_hash  */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    0,                                                   /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,            /* tp_flags */
    "C ValueContainer type",                             /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_value_container_methods,                           /* tp_methods */
    t_value_container_members,                           /* tp_members */
    0,                                                   /* tp_getset */
    &ContainerType,                                      /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_value_container_init,                    /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_value_container_new,                      /* tp_new */
};


static void t_value_container_dealloc(t_value_container *self)
{
    ContainerType.tp_dealloc((PyObject *) self);
}

static PyObject *t_value_container_new(PyTypeObject *type,
                                       PyObject *args, PyObject *kwds)
{
    PyObject *self = ContainerType.tp_new(type, args, kwds);

    return (PyObject *) self;
}

static int t_value_container_init(t_value_container *self,
                                  PyObject *args, PyObject *kwds)
{
    return ContainerType.tp_init((PyObject *) self, args, kwds);
}

static PyObject *t_value_container_loadValue(t_value_container *self,
                                             PyObject *args)
{
    PyObject *txn, *uValue;

    if (!PyArg_ParseTuple(args, "OO", &txn, &uValue))
        return NULL;
    else
    {
        DB *db = ((DBObject *) (((t_container *) self)->db))->db;
        DB_TXN *db_txn = txn == Py_None ? NULL : ((DBTxnObject *) txn)->txn;
        DBT key, data;
        int err;

        memset(&key, 0, sizeof(key));
        key.data = PyString_AS_STRING(((t_uuid *) uValue)->uuid);
        key.size = PyString_GET_SIZE(((t_uuid *) uValue)->uuid);
        
        memset(&data, 0, sizeof(data));
        data.flags = DB_DBT_MALLOC;

        while (1) {
            Py_BEGIN_ALLOW_THREADS;
            err = db->get(db, db_txn, &key, &data, 0);
            Py_END_ALLOW_THREADS;

            switch (err) {
              case 0:
              {
                  PyObject *tuple = PyTuple_New(2);
                  PyObject *uuid =
                      PyString_FromStringAndSize((char *) data.data, 16);
                  PyObject *value = 
                      PyString_FromStringAndSize((char *) data.data + 36,
                                                 data.size - 36);

                  free(data.data);
                  PyTuple_SET_ITEM(tuple, 0, PyUUID_Make16(uuid));
                  PyTuple_SET_ITEM(tuple, 1, value);

                  return tuple;
              }
              case DB_NOTFOUND:
              {
                  PyObject *tuple = PyTuple_New(2);

                  PyTuple_SET_ITEM(tuple, 0, Py_None); Py_INCREF(Py_None);
                  PyTuple_SET_ITEM(tuple, 1, Py_None); Py_INCREF(Py_None);

                  return tuple;
              }
              case DB_LOCK_DEADLOCK:
                if (!db_txn)
                    continue;
              default:
                return raiseDBError(err);
            }
        }
    }
}

static PyObject *t_value_container_saveValue(t_value_container *self,
                                             PyObject *args)
{
    PyObject *txn, *uItem, *uAttr, *uValue, *value;
    int version;

    if (!PyArg_ParseTuple(args, "OOiOOO", &txn, &uItem, &version,
                          &uAttr, &uValue, &value))
        return NULL;
    else
    {
        DB *db = ((DBObject *) (((t_container *) self)->db))->db;
        DB_TXN *db_txn = txn == Py_None ? NULL : ((DBTxnObject *) txn)->txn;
        DBT key, data;
        int vLen = PyString_GET_SIZE(value);
        int len = 36 + vLen;
        char *buffer = alloca(len);
        int err;

        memset(&key, 0, sizeof(key));
        key.data = PyString_AS_STRING(((t_uuid *) uValue)->uuid);
        key.size = PyString_GET_SIZE(((t_uuid *) uValue)->uuid);

        memcpy(buffer, PyString_AS_STRING(((t_uuid *) uAttr)->uuid), 16);
        memcpy(buffer + 16, PyString_AS_STRING(((t_uuid *) uItem)->uuid), 16);
        *((int *) (buffer + 32)) = htonl(~version);
        memcpy(buffer + 36, PyString_AS_STRING(value), vLen);

        memset(&data, 0, sizeof(data));
        data.data = buffer;
        data.size = len;

        Py_BEGIN_ALLOW_THREADS;
        err = db->put(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        return PyInt_FromLong(key.size + data.size);
    }        
}


typedef struct {
    t_container container;
} t_ref_container;


static void t_ref_container_dealloc(t_ref_container *self);
static PyObject *t_ref_container_new(PyTypeObject *type,
                                     PyObject *args, PyObject *kwds);
static int t_ref_container_init(t_ref_container *self,
                                PyObject *args, PyObject *kwds);
static PyObject *t_ref_container_saveRef(t_ref_container *self,
                                         PyObject *args);


static PyMemberDef t_ref_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_ref_container_methods[] = {
    { "saveRef", (PyCFunction) t_ref_container_saveRef, METH_VARARGS,
      "saveRef" },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject RefContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.container.CRefContainer",    /* tp_name */
    sizeof(t_ref_container),                             /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_ref_container_dealloc,                 /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    0,                                                   /* tp_repr */
    0,                                                   /* tp_as_number */
    0,                                                   /* tp_as_sequence */
    0,                                                   /* tp_as_mapping */
    0,                                                   /* tp_hash  */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    0,                                                   /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,            /* tp_flags */
    "C RefContainer type",                               /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_ref_container_methods,                             /* tp_methods */
    t_ref_container_members,                             /* tp_members */
    0,                                                   /* tp_getset */
    &ContainerType,                                      /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_ref_container_init,                      /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_ref_container_new,                        /* tp_new */
};


static void t_ref_container_dealloc(t_ref_container *self)
{
    ContainerType.tp_dealloc((PyObject *) self);
}

static PyObject *t_ref_container_new(PyTypeObject *type,
                                     PyObject *args, PyObject *kwds)
{
    PyObject *self = ContainerType.tp_new(type, args, kwds);

    return (PyObject *) self;
}

static int t_ref_container_init(t_ref_container *self,
                                PyObject *args, PyObject *kwds)
{
    return ContainerType.tp_init((PyObject *) self, args, kwds);
}


static PyObject *t_ref_container_saveRef(t_ref_container *self, PyObject *args)
{
    PyObject *txn, *prefix, *uuid, *previous, *next, *alias;
    int version;

    if (!PyArg_ParseTuple(args, "OOiOOOO", &txn, &prefix, &version, &uuid,
                          &previous, &next, &alias))
        return NULL;
    else
    {
        DB *db = ((DBObject *) (((t_container *) self)->db))->db;
        DB_TXN *db_txn = txn == Py_None ? NULL : ((DBTxnObject *) txn)->txn;
        valueType prevType, nextType, aliasType;
        char keyBuffer[52], *dataBuffer;
        DBT key, data;
        int len, err;

        memcpy(&keyBuffer, PyString_AS_STRING(prefix), 32);
        memcpy(&keyBuffer[32], PyString_AS_STRING(((t_uuid *) uuid)->uuid), 16);
        *((int *) (&keyBuffer[48])) = htonl(~version);
        memset(&key, 0, sizeof(key));
        key.data = keyBuffer;
        key.size = sizeof(keyBuffer);

        len = 0;
        len += _size_valueType(previous, &prevType);
        len += _size_valueType(next, &nextType);
        len += _size_valueType(alias, &aliasType);
        dataBuffer = alloca(len);
        
        len = 0;
        len += _writeValue(dataBuffer + len, previous, prevType);
        len += _writeValue(dataBuffer + len, next, nextType);
        len += _writeValue(dataBuffer + len, alias, aliasType);
        memset(&data, 0, sizeof(data));
        data.data = dataBuffer;
        data.size = len;
        
        Py_BEGIN_ALLOW_THREADS;
        err = db->put(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        return PyInt_FromLong(key.size + data.size);
    }
}

void initcontainer(void)
{
    if (PyType_Ready(&ContainerType) >= 0 &&
        PyType_Ready(&ValueContainerType) >= 0 &&
        PyType_Ready(&RefContainerType) >= 0)
    {
        PyObject *m = Py_InitModule3("container", container_funcs,
                                     "Container C type module");

        if (m)
        {
            Py_INCREF(&ContainerType);
            PyModule_AddObject(m, "CContainer",
                               (PyObject *) &ContainerType);

            Py_INCREF(&ValueContainerType);
            PyModule_AddObject(m, "CValueContainer",
                               (PyObject *) &ValueContainerType);

            Py_INCREF(&RefContainerType);
            PyModule_AddObject(m, "CRefContainer",
                               (PyObject *) &RefContainerType);

            m = PyImport_ImportModule("bsddb.db");
            LOAD_EXC(m, DBLockDeadlockError);
            LOAD_EXC(m, DBLockNotGrantedError);
            LOAD_EXC(m, DBAccessError);
            LOAD_EXC(m, DBInvalidArgError);
            LOAD_EXC(m, DBNoSpaceError);
            LOAD_EXC(m, DBError);
            Py_DECREF(m);

            m = PyImport_ImportModule("chandlerdb.util.uuid");
            LOAD_FN(m, PyUUID_Check);
            LOAD_FN(m, PyUUID_Make16);
            Py_DECREF(m);
        }
    }
}
