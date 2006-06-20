/*
 *  Copyright (c) 2003-2006 Open Source Applications Foundation
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */


#if defined(_MSC_VER)
#include <winsock2.h>
#elif defined(__MACH__)
#include <arpa/inet.h>
#elif defined(linux)
#include <netinet/in.h>
#else
#error system is not linux, os x or winnt
#endif

#include <Python.h>
#include "structmember.h"

#include "c.h"

typedef struct {
    PyObject_HEAD
    t_db *db;
} t_container;

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


static PyMemberDef t_container_members[] = {
    { "db", T_OBJECT, offsetof(t_container, db), READONLY, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_container_methods[] = {
    { NULL, NULL, 0, NULL }
};


static PyTypeObject ContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.CContainer",               /* tp_name */
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

    if (!PyObject_TypeCheck(db, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, db);
        return -1;
    }

    Py_INCREF(db);
    self->db = (t_db *) db;

    return 0;
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

static PyObject *_readValue(char *buffer, int *offset)
{
    switch (buffer[(*offset)++]) {
      case '\0':
        Py_RETURN_NONE;
      case '\1':
        Py_RETURN_TRUE;
      case '\2':
        Py_RETURN_FALSE;
      case '\3':
      {
          PyObject *string = PyString_FromStringAndSize(buffer + *offset, 16);
          *offset += 16;

          return PyUUID_Make16(string);
      }
      case '\4':
      {
          long n = ntohl(*(long *) (buffer + *offset));
          
          *offset += 4;
          return PyInt_FromLong(n);
      }
      case '\5':
      {
          int len = ntohs(*(unsigned short *) (buffer + *offset));
          PyObject *string;

          *offset += 2;
          string = PyString_FromStringAndSize(buffer + *offset, len);
          *offset += len;

          return string;
      }
      case '\6':
      {
          int len = ntohs(*(unsigned short *) (buffer + *offset));
          PyObject *string;
          
          *offset += 2;
          string = PyUnicode_DecodeUTF8(buffer + *offset, len, NULL);
          *offset += len;

          return string;
      }
      default:
        PyErr_SetString(PyExc_ValueError, "unexpected type code");
        return NULL;
    }
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
          *((unsigned short *) (buffer + 1)) = htons(len);
          memcpy(buffer + 3, PyString_AS_STRING(value), len);

          return len + 3;
      }
      case vt_UNICODE:
      {
          PyObject *str = PyUnicode_AsUTF8String(value);
          int len = PyString_GET_SIZE(str);

          buffer[0] = '\6';
          *((unsigned short *) (buffer + 1)) = htons(len);
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

static PyObject *_t_container_associate(t_container *self, PyObject *args,
                                        int (*fn)(DB *, const DBT *, const DBT *, DBT *))
{
    PyObject *index, *txn = Py_None;
    int flags = 0;

    if (!PyArg_ParseTuple(args, "O|Oi", &index, &txn, &flags))
        return NULL;

    if (!PyObject_TypeCheck(index, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, index);
        return NULL;
    }

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB *db = self->db->db;
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = db->associate(db, db_txn, ((t_db *) index)->db, fn, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);
    }

    Py_RETURN_NONE;
}

typedef struct {
    DBT dbt;
    int *offsets;
} t_tuple_dbt;

static int _t_container_get_strings(t_tuple_dbt *dbt, void *data,
                                    int len, int offset)
{
    PyGILState_STATE state = PyGILState_Ensure();
    PyObject *tuple, *str;
    int count = dbt->offsets[0];
    int i, prev;

    if (offset == 0)
    {
        tuple = PyTuple_New(count);
        if (!tuple)
        {
            PyGILState_Release(state);
            return DB_PYTHON_ERROR;
        }

        prev = 0;
        for (i = 1; i < count; i++) {
            int curr = dbt->offsets[i];

            str = PyString_FromStringAndSize(NULL, curr - prev);
            if (!str)
            {
                Py_DECREF(tuple);
                PyGILState_Release(state);
                return DB_PYTHON_ERROR;
            }
                
            PyTuple_SET_ITEM(tuple, i - 1, str);
            prev = curr;
        }

        str = PyString_FromStringAndSize(NULL, dbt->dbt.size - prev);
        if (!str)
        {
            Py_DECREF(tuple);
            PyGILState_Release(state);
            return DB_PYTHON_ERROR;
        }        

        PyTuple_SET_ITEM(tuple, count - 1, str);
        dbt->dbt.data = tuple;
    }
    else
        tuple = (PyObject *) dbt->dbt.data;

    prev = 0;
    for (i = 1; i < count; i++) {
        int curr = dbt->offsets[i];

        if (offset < curr)
        {
            int size = curr - offset;      /* curr - prev - (offset - prev) */

            str = PyTuple_GET_ITEM(tuple, i - 1);
            memcpy(PyString_AS_STRING(str) + offset - prev, data,
                   len > size ? size : len);

            len -= size;

            if (len <= 0)
            {
                PyGILState_Release(state);
                return 0;
            }

            data = (char *) data + size;
            offset += size;
        }

        prev = curr;
    }

    str = PyTuple_GET_ITEM(tuple, count - 1);
    memcpy(PyString_AS_STRING(str) + offset - prev, data, len);

    PyGILState_Release(state);
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
static PyObject *t_value_container_setIndexed(t_value_container *self,
                                              PyObject *args);


static PyMemberDef t_value_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_value_container_methods[] = {
    { "loadValue", (PyCFunction) t_value_container_loadValue, METH_VARARGS,
      "saveValue" },
    { "saveValue", (PyCFunction) t_value_container_saveValue, METH_VARARGS,
      "saveValue" },
    { "setIndexed", (PyCFunction) t_value_container_setIndexed, METH_VARARGS,
      "setIndexed" },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject ValueContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.CValueContainer",          /* tp_name */
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

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    if (!PyUUID_Check(uValue))
    {
        PyErr_SetObject(PyExc_TypeError, uValue);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        DBT key;
        t_tuple_dbt data;
        int offsets[] = { 3, 16, 17 };   /* 3 strings, starting at 0, 16, 17 */

        memset(&key, 0, sizeof(key));
        key.data = PyString_AS_STRING(((t_uuid *) uValue)->uuid);
        key.size = PyString_GET_SIZE(((t_uuid *) uValue)->uuid);
        
        memset(&data, 0, sizeof(data));
        data.dbt.flags = DB_DBT_USERCOPY;
        data.dbt.data = _t_container_get_strings;
        data.offsets = offsets;

        while (1) {
            int err;

            Py_BEGIN_ALLOW_THREADS;
            err = db->get(db, db_txn, &key, (DBT *) &data, 0);
            Py_END_ALLOW_THREADS;

            switch (err) {
              case 0:
              {
                  PyObject *tuple = (PyObject *) data.dbt.data;
                  PyObject *uuid = PyTuple_GET_ITEM(tuple, 0);

                  PyTuple_SET_ITEM(tuple, 0, PyUUID_Make16(uuid));

                  return tuple;
              }
              case DB_NOTFOUND:
                Py_RETURN_NONE;
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
    PyObject *txn, *uAttr, *uValue;
    char *value;
    int vLen;

    if (!PyArg_ParseTuple(args, "OOOs#", &txn, &uAttr, &uValue, &value, &vLen))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        DBT key, data;
        char *buffer, stackBuffer[1024];
        int len = 16 + vLen;
        int err;

        memset(&key, 0, sizeof(key));
        key.data = PyString_AS_STRING(((t_uuid *) uValue)->uuid);
        key.size = PyString_GET_SIZE(((t_uuid *) uValue)->uuid);

        if (len > sizeof(stackBuffer))
        {
            buffer = malloc(len);
            if (!buffer)
            {
                PyErr_SetString(PyExc_MemoryError, "malloc failed");
                return NULL;
            }
        }
        else
            buffer = stackBuffer;

        memcpy(buffer, PyString_AS_STRING(((t_uuid *) uAttr)->uuid), 16);
        memcpy(buffer + 16, value, vLen);

        memset(&data, 0, sizeof(data));
        data.data = buffer;
        data.size = len;
        
        Py_BEGIN_ALLOW_THREADS;
        err = db->put(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        if (len > sizeof(stackBuffer))
            free(buffer);

        if (err)
            return raiseDBError(err);

        return PyInt_FromLong(key.size + data.size);
    }        
}

static PyObject *t_value_container_setIndexed(t_value_container *self,
                                              PyObject *args)
{
    PyObject *txn, *uValue;

    if (!PyArg_ParseTuple(args, "OO", &txn, &uValue))
        return NULL;

    if (!PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    if (!PyUUID_Check(uValue))
    {
        PyErr_SetObject(PyExc_TypeError, uValue);
        return NULL;
    }

    {
        DB_TXN *db_txn = ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        DBT key, data;
        unsigned char vFlags;
        int err;

        memset(&key, 0, sizeof(key));
        key.data = PyString_AS_STRING(((t_uuid *) uValue)->uuid);
        key.size = PyString_GET_SIZE(((t_uuid *) uValue)->uuid);
        
        memset(&data, 0, sizeof(data));
        data.flags = DB_DBT_USERMEM | DB_DBT_PARTIAL;
        data.doff = 16;
        data.dlen = 1;
        data.ulen = 1;
        data.data = &vFlags;

        Py_BEGIN_ALLOW_THREADS;
        err = db->get(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        if (!err)
        {
            vFlags &= ~V_TOINDEX;
            vFlags |= V_INDEXED;
        }
        else
            return raiseDBError(err);

        Py_BEGIN_ALLOW_THREADS;
        err = db->put(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        if (!err)
            Py_RETURN_NONE;
        else
            return raiseDBError(err);
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
static PyObject *t_ref_container_loadRef(t_ref_container *self, PyObject *args);
static PyObject *t_ref_container_saveRef(t_ref_container *self, PyObject *args);
static PyObject *t_ref_container_associateHistory(t_ref_container *self,
                                                  PyObject *args);


static PyMemberDef t_ref_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_ref_container_methods[] = {
    { "saveRef", (PyCFunction) t_ref_container_saveRef,
      METH_VARARGS, "saveRef" },
    { "loadRef", (PyCFunction) t_ref_container_loadRef,
      METH_VARARGS, "loadRef" },
    { "associateHistory", (PyCFunction) t_ref_container_associateHistory,
      METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject RefContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.CRefContainer",            /* tp_name */
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

typedef struct {
    DBT dbt;
    char buffer[128];
} t_buffer_dbt;

static int _t_ref_container_load_ref(t_buffer_dbt *dbt, void *data,
                                     int len, int offset)
{
    if (offset == 0)
    {
        if (dbt->dbt.size > sizeof(dbt->buffer))
        {
            dbt->dbt.data = malloc(dbt->dbt.size);
            if (!dbt->dbt.data)
                return ENOMEM;
        }
        else
            dbt->dbt.data = dbt->buffer;
    }

    memcpy((char *) dbt->dbt.data + offset, data, len);
    return 0;
}

static PyObject *t_ref_container_loadRef(t_ref_container *self, PyObject *args)
{
    PyObject *cursor;
    char *uCol, *uRef;
    int uColLen, uRefLen, flags = 0;
    unsigned long long version;

    if (!PyArg_ParseTuple(args, "Os#s#K|i", &cursor,
                          &uCol, &uColLen, &uRef, &uRefLen, &version, &flags))
        return NULL;

    if (!PyObject_TypeCheck(cursor, CDBCursor))
    {
        PyErr_SetObject(PyExc_TypeError, cursor);
        return NULL;
    }

    if (uColLen != 16)
    {
        PyErr_SetString(PyExc_ValueError, "invalid uCol length");
        return NULL;
    }

    if (uRefLen != 16)
    {
        PyErr_SetString(PyExc_ValueError, "invalid uRef length");
        return NULL;
    }

    {
        DBC *dbc = ((t_cursor *) cursor)->dbc;
        char keyBuffer[40];
        DBT key;
        t_buffer_dbt data;
        int err;

        memset(&key, 0, sizeof(key));
        memcpy(keyBuffer, uCol, 16);
        memcpy(keyBuffer + 16, uRef, 16);
        key.data = keyBuffer;
        key.size = 32;
        key.flags = DB_DBT_USERMEM;
        key.ulen = sizeof(keyBuffer);

        memset(&data, 0, sizeof(data));
        data.dbt.flags = DB_DBT_USERCOPY;
        data.dbt.data = _t_ref_container_load_ref;

        Py_BEGIN_ALLOW_THREADS;
        err = dbc->c_get(dbc, &key, (DBT *) &data, flags | DB_SET_RANGE);
        Py_END_ALLOW_THREADS;

        do {
            char *buffer = data.dbt.data;

            switch (err) {
              case 0:
              {
                  unsigned long long ver;

                  if (key.size != 40 ||
                      memcmp(key.data, uCol, 16) ||
                      memcmp((char *) key.data + 16, uRef, 16))
                  {
                      if (buffer != data.buffer)
                          free(buffer);
                              
                      Py_RETURN_NONE;
                  }

                  ver = ntohl(*(unsigned long *) ((char *) key.data + 32));
                  ver <<= 32;
                  ver += ntohl(*(unsigned long *) ((char *) key.data + 36));

                  if (~ver <= version)
                  {
                      if (data.dbt.size == 1)  /* deleted ref */
                          Py_RETURN_NONE;
                      else
                      {
                          PyObject *tuple = PyTuple_New(3);
                          int pos = 0;

                          PyTuple_SET_ITEM(tuple, 0, _readValue(buffer, &pos));
                          PyTuple_SET_ITEM(tuple, 1, _readValue(buffer, &pos));
                          PyTuple_SET_ITEM(tuple, 2, _readValue(buffer, &pos));

                          if (buffer != data.buffer)
                              free(buffer);

                          if (PyErr_Occurred())
                          {
                              Py_DECREF(tuple);
                              return NULL;
                          }

                          return tuple;
                      }
                  }
                  break;
              }

              case DB_NOTFOUND:
                Py_RETURN_NONE;

              default:
                return raiseDBError(err);
            }

            key.size = 32;

            if (buffer != data.buffer)
                free(buffer);
            data.dbt.data = _t_ref_container_load_ref;
            data.dbt.size = 0;

            Py_BEGIN_ALLOW_THREADS;
            err = dbc->c_get(dbc, &key, (DBT *) &data, flags | DB_NEXT);
            Py_END_ALLOW_THREADS;
        } while (1);
    }
}

static PyObject *t_ref_container_saveRef(t_ref_container *self, PyObject *args)
{
    PyObject *txn, *previous, *next, *alias;
    char *uCol, *uRef;
    int uColLen, uRefLen;
    unsigned long long version;

    if (!PyArg_ParseTuple(args, "Os#Ks#OOO", &txn, &uCol, &uColLen,
                          &version, &uRef, &uRefLen, 
                          &previous, &next, &alias))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    if (uColLen != 16)
    {
        PyErr_SetString(PyExc_ValueError, "invalid uCol length");
        return NULL;
    }

    if (uRefLen != 16)
    {
        PyErr_SetString(PyExc_ValueError, "invalid uRef length");
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        valueType prevType, nextType, aliasType;
        char keyBuffer[40], *dataBuffer, stackBuffer[128];
        DBT key, data;
        int len, err;

        memcpy(keyBuffer, uCol, 16);
        memcpy(keyBuffer + 16, uRef, 16);
        *((unsigned long *) (&keyBuffer[32])) = htonl(~(unsigned long) (version >> 32));
        *((unsigned long *) (&keyBuffer[36])) = htonl(~(unsigned long) version);
        memset(&key, 0, sizeof(key));
        key.data = keyBuffer;
        key.size = sizeof(keyBuffer);

        len = 0;
        len += _size_valueType(previous, &prevType);
        len += _size_valueType(next, &nextType);
        len += _size_valueType(alias, &aliasType);

        if (len > sizeof(stackBuffer))
        {
            dataBuffer = malloc(len);
            if (!dataBuffer)
            {
                PyErr_SetString(PyExc_MemoryError, "malloc failed");
                return NULL;
            }
        }
        else
            dataBuffer = stackBuffer;
        
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

        if (len > sizeof(stackBuffer))
            free(dataBuffer);

        if (err)
            return raiseDBError(err);

        return PyInt_FromLong(key.size + data.size);
    }
}


/* uCol, uRef, ~version -> uCol, version, uRef */

static int _t_ref_container_historyKey(DB *secondary,
                                       const DBT *key, const DBT *data,
                                       DBT *result)
{
    char *buffer = (char *) malloc(40);
    unsigned long long version =
        ~*(unsigned long long *) ((char *) key->data + 32);

    if (!buffer)
        return ENOMEM;

    memcpy(buffer, key->data, 16);
    memcpy(buffer + 16, &version, 8);
    memcpy(buffer + 24, (char *) key->data + 16, 16);

    result->data = buffer;
    result->flags = DB_DBT_APPMALLOC;
    result->size = 40;

    return 0;
}

static PyObject *t_ref_container_associateHistory(t_ref_container *self,
                                                  PyObject *args)
{
    return _t_container_associate((t_container *) self, args,
                                  _t_ref_container_historyKey);
}


typedef struct {
    t_container container;
} t_item_container;


static void t_item_container_dealloc(t_item_container *self);
static PyObject *t_item_container_new(PyTypeObject *type,
                                     PyObject *args, PyObject *kwds);
static int t_item_container_init(t_item_container *self,
                                 PyObject *args, PyObject *kwds);
static PyObject *t_item_container_associateKind(t_item_container *self,
                                                PyObject *args);
static PyObject *t_item_container_associateVersion(t_item_container *self,
                                                   PyObject *args);
static PyObject *t_item_container_setItemStatus(t_item_container *self,
                                                PyObject *args);



static PyMemberDef t_item_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_item_container_methods[] = {
    { "associateKind", (PyCFunction) t_item_container_associateKind,
      METH_VARARGS, NULL },
    { "associateVersion", (PyCFunction) t_item_container_associateVersion,
      METH_VARARGS, NULL },
    { "setItemStatus", (PyCFunction) t_item_container_setItemStatus,
      METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject ItemContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.CItemContainer",           /* tp_name */
    sizeof(t_item_container),                            /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_item_container_dealloc,                /* tp_dealloc */
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
    "C ItemContainer type",                              /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_item_container_methods,                            /* tp_methods */
    t_item_container_members,                            /* tp_members */
    0,                                                   /* tp_getset */
    &ContainerType,                                      /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_item_container_init,                     /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_item_container_new,                       /* tp_new */
};


static void t_item_container_dealloc(t_item_container *self)
{
    ContainerType.tp_dealloc((PyObject *) self);
}

static PyObject *t_item_container_new(PyTypeObject *type,
                                     PyObject *args, PyObject *kwds)
{
    PyObject *self = ContainerType.tp_new(type, args, kwds);

    return (PyObject *) self;
}

static int t_item_container_init(t_item_container *self,
                                 PyObject *args, PyObject *kwds)
{
    return ContainerType.tp_init((PyObject *) self, args, kwds);
}


/* uItem, ~version -> uKind, uItem, ~version */

static int _t_item_container_kindKey(DB *secondary,
                                     const DBT *key, const DBT *data,
                                     DBT *result)
{
    char *buffer = (char *) malloc(40);

    if (!buffer)
        return ENOMEM;

    memcpy(buffer, data->data, 16);
    memcpy(buffer + 16, key->data, 24);

    result->data = buffer;
    result->flags = DB_DBT_APPMALLOC;
    result->size = 40;

    return 0;
}

static PyObject *t_item_container_associateKind(t_item_container *self,
                                                PyObject *args)
{
    return _t_container_associate((t_container *) self, args,
                                  _t_item_container_kindKey);
}


/* uItem, ~version -> version, uItem */

static int _t_item_container_versionKey(DB *secondary,
                                        const DBT *key, const DBT *data,
                                        DBT *result)
{
    char *buffer = (char *) malloc(24);
    unsigned long long version = ~*(unsigned long long *) ((char *) key->data + 16);

    if (!buffer)
        return ENOMEM;

    memcpy(buffer, &version, 8);
    memcpy(buffer + 8, key->data, 16);

    result->data = buffer;
    result->flags = DB_DBT_APPMALLOC;
    result->size = 24;

    return 0;
}

static PyObject *t_item_container_associateVersion(t_item_container *self,
                                                   PyObject *args)
{
    return _t_container_associate((t_container *) self, args,
                                  _t_item_container_versionKey);
}

static PyObject *t_item_container_setItemStatus(t_item_container *self,
                                                PyObject *args)
{
    PyObject *txn, *uItem;
    unsigned long long version;
    unsigned int status;

    if (!PyArg_ParseTuple(args, "OKOi", &txn, &version, &uItem, &status))
        return NULL;

    if (!PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    if (!PyUUID_Check(uItem))
    {
        PyErr_SetObject(PyExc_TypeError, uItem);
        return NULL;
    }

    {
        DB_TXN *db_txn = ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        DBT key, data;
        char keyBuffer[24];
        unsigned int value;
        int err;

        memcpy(keyBuffer, PyString_AS_STRING(((t_uuid *) uItem)->uuid), 16);
        *((unsigned long *) (&keyBuffer[16])) = htonl(~(unsigned long) (version >> 32));
        *((unsigned long *) (&keyBuffer[20])) = htonl(~(unsigned long) version);

        memset(&key, 0, sizeof(key));
        key.data = keyBuffer;
        key.size = sizeof(keyBuffer);
        
        memset(&data, 0, sizeof(data));
        data.flags = DB_DBT_USERMEM | DB_DBT_PARTIAL;
        data.doff = 16;
        data.dlen = 4;
        data.ulen = 4;
        data.data = &value;

        Py_BEGIN_ALLOW_THREADS;
        err = db->get(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        if (!err)
            value = htonl(status);
        else
            return raiseDBError(err);

        Py_BEGIN_ALLOW_THREADS;
        err = db->put(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        if (!err)
            Py_RETURN_NONE;
        else
            return raiseDBError(err);
    }
}


void _init_container(PyObject *m)
{
    if (PyType_Ready(&ContainerType) >= 0 &&
        PyType_Ready(&ValueContainerType) >= 0 &&
        PyType_Ready(&RefContainerType) >= 0 &&
        PyType_Ready(&ItemContainerType) >= 0)
    {
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

            Py_INCREF(&ItemContainerType);
            PyModule_AddObject(m, "CItemContainer",
                               (PyObject *) &ItemContainerType);
        }
    }
}
