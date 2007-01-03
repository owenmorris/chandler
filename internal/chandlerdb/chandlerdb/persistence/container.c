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


static void t_container_dealloc(t_container *self);
static PyObject *t_container_new(PyTypeObject *type,
                                 PyObject *args, PyObject *kwds);
static int t_container_init(t_container *self, PyObject *args, PyObject *kwds);

static PyObject *t_container_find_record(t_container *self, PyObject *args);

static PyMemberDef t_container_members[] = {
    { "db", T_OBJECT, offsetof(t_container, db), READONLY, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_container_methods[] = {
    { "find_record", (PyCFunction) t_container_find_record, METH_VARARGS, NULL },
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


typedef struct {
    DBT dbt;
    int found;
    int keySize;
    char *keyData;
    char *keyBuffer;
} t_data_dbt;

static int _t_container_read_record(t_data_dbt *dbt, int offset, void *data,
                                    int len, int mode)
{
    if (dbt->found == -1)
        dbt->found = !memcmp(dbt->keyData, dbt->keyBuffer, dbt->keySize - 4);
    
    if (dbt->found && dbt->dbt.app_data != Nil)
        return _t_db_read_record((DBT *) dbt, offset, data, len, mode);

    return 0;
}

/* finds a versioned record
 * the version number is assumed to be the last 4 bytes of the key
 */
static PyObject *t_container_find_record(t_container *self, PyObject *args)
{
    PyObject *cursor, *keyRecord, *dataTypes, *defaultValue = NULL;
    int flags = 0, err, keySize, returnBoth = 0;
    char keyBuffer[256], keyData[256];
    DBT key;
    t_data_dbt data;
    DBC *dbc;

    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));

    if (!PyArg_ParseTuple(args, "OOO|iOi", &cursor, &keyRecord, &dataTypes,
                          &flags, &defaultValue, &returnBoth))
        return NULL;

    if (!PyObject_TypeCheck(cursor, CDBCursor))
    {
        PyErr_SetObject(PyExc_TypeError, cursor);
        return NULL;
    }

    if (!PyObject_TypeCheck(keyRecord, Record))
    {
        PyErr_SetObject(PyExc_TypeError, keyRecord);
        return NULL;
    }

    if (dataTypes != Nil && !PyTuple_CheckExact(dataTypes))
    {
        PyErr_SetObject(PyExc_TypeError, dataTypes);
        return NULL;
    }

    keySize = ((t_record *) keyRecord)->size;
    if (keySize > sizeof(keyBuffer))
        goto overflow;
    else
    {
        if (_t_record_write((t_record *) keyRecord,
                            (unsigned char *) keyBuffer, keySize) < 0)
            return NULL;

        key.size = keySize;
        memcpy(keyData, keyBuffer, keySize);
        key.data = keyData;
        key.ulen = sizeof(keyData);
        key.flags = DB_DBT_USERMEM;
    }

    data.dbt.app_data = dataTypes;
    data.found = -1;
    data.keySize = keySize;
    data.keyData = keyData;
    data.keyBuffer = keyBuffer;
    data.dbt.usercopy = (usercopy_fn) _t_container_read_record;
    data.dbt.flags = DB_DBT_USERCOPY;

    dbc = ((t_cursor *) cursor)->dbc;

    Py_BEGIN_ALLOW_THREADS;
    err = dbc->c_get(dbc, &key, (DBT *) &data, flags | DB_SET_RANGE);
    Py_END_ALLOW_THREADS;

    switch (err) {
      case 0:
      {
          PyObject *dataRecord;
          PyObject *result;

          if (data.found != 1)
              goto notfound;

          if (dataTypes == Nil)
          {
              dataRecord = Nil;
              Py_INCREF(Nil);
          }
          else
              dataRecord = (PyObject *) data.dbt.app_data;
              
          if (returnBoth)
          {
              keyRecord = _t_db_make_record(keyRecord, keyData, key.size);

              result = PyTuple_New(2);
              PyTuple_SET_ITEM(result, 0, keyRecord);
              PyTuple_SET_ITEM(result, 1, dataRecord);
          }
          else
              result = dataRecord;

          return result;
      }

      case DB_NOTFOUND:
        goto notfound;

      case DB_BUFFER_SMALL:
        goto overflow;

      default:
        return raiseDBError(err);
    }

  notfound:
    if (defaultValue)
    {
        Py_INCREF(defaultValue);
        return defaultValue;
    }

    PyErr_SetObject(PyExc_KeyError, keyRecord);
    return NULL;

  overflow:
    PyErr_SetString(PyExc_OverflowError, "key > 256 bytes");
    return NULL;
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
    t_container container;
} t_value_container;


static void t_value_container_dealloc(t_value_container *self);
static PyObject *t_value_container_new(PyTypeObject *type,
                                       PyObject *args, PyObject *kwds);
static int t_value_container_init(t_value_container *self,
                                  PyObject *args, PyObject *kwds);
static PyObject *t_value_container_loadValue(t_value_container *self,
                                             PyObject *args);
static PyObject *t_value_container_setIndexed(t_value_container *self,
                                              PyObject *args);


static PyMemberDef t_value_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_value_container_methods[] = {
    { "loadValue", (PyCFunction) t_value_container_loadValue, METH_VARARGS,
      "loadValue" },
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
    DBT key, data;
    PyObject *uKey, *txn;

    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));

    if (!PyArg_ParseTuple(args, "OOO", &uKey, &data.app_data, &txn))
        return NULL;

    if (!PyUUID_Check(uKey))
    {
        PyErr_SetObject(PyExc_TypeError, uKey);
        return NULL;
    }

    if (((PyObject *) data.app_data)->ob_type != Record &&
        !PyTuple_CheckExact((PyObject *) data.app_data))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) data.app_data);
        return NULL;
    }

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    key.size = 16;
    key.data = PyString_AS_STRING(((t_uuid *) uKey)->uuid);

    data.flags = DB_DBT_USERCOPY;
    data.usercopy = (usercopy_fn) _t_db_read_record;

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = db->get(db, db_txn, &key, &data, 0);
        Py_END_ALLOW_THREADS;

        switch (err) {
          case 0:
            return (PyObject *) data.app_data;
          case DB_NOTFOUND:
            Py_RETURN_NONE;
          default:
            return raiseDBError(err);
        }
    }
}

static PyObject *t_value_container_setIndexed(t_value_container *self,
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
static PyObject *t_ref_container_associateHistory(t_ref_container *self,
                                                  PyObject *args);
static PyObject *t_ref_container_find_ref(t_ref_container *self,
                                          PyObject *args);


static PyMemberDef t_ref_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_ref_container_methods[] = {
    { "find_ref", (PyCFunction) t_ref_container_find_ref, METH_VARARGS, NULL },
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

static PyObject *t_ref_container_find_ref(t_ref_container *self, PyObject *args)
{
    PyObject *cursor, *uCol, *uKey, *dataTypes;
    int flags = 0, err;
    char keyBuffer[36], keyData[36];
    unsigned long version;
    DBT key;
    t_data_dbt data;
    DBC *dbc;

    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));

    if (!PyArg_ParseTuple(args, "OOOkO|i", &cursor, &uCol, &uKey, &version,
                          &dataTypes, &flags))
        return NULL;

    if (!PyObject_TypeCheck(cursor, CDBCursor))
    {
        PyErr_SetObject(PyExc_TypeError, cursor);
        return NULL;
    }

    if (!PyUUID_Check(uCol))
    {
        PyErr_SetObject(PyExc_TypeError, uCol);
        return NULL;
    }
    if (!PyUUID_Check(uKey))
    {
        PyErr_SetObject(PyExc_TypeError, uKey);
        return NULL;
    }

    if (dataTypes != Nil && !PyTuple_CheckExact(dataTypes))
    {
        PyErr_SetObject(PyExc_TypeError, dataTypes);
        return NULL;
    }

    version = htonl(version);

    key.size = 36;
    memcpy(keyBuffer, PyString_AS_STRING(((t_uuid *) uCol)->uuid), 16);
    memcpy(keyBuffer + 16, PyString_AS_STRING(((t_uuid *) uKey)->uuid), 16);
    memcpy(keyBuffer + 32, (unsigned char *) &version, 4);
    memcpy(keyData, keyBuffer, 36);
    key.data = keyData;
    key.ulen = sizeof(keyData);
    key.flags = DB_DBT_USERMEM;

    data.dbt.app_data = dataTypes;
    data.found = -1;
    data.keySize = 36;
    data.keyData = keyData;
    data.keyBuffer = keyBuffer;
    data.dbt.usercopy = (usercopy_fn) _t_container_read_record;
    data.dbt.flags = DB_DBT_USERCOPY;

    dbc = ((t_cursor *) cursor)->dbc;

    Py_BEGIN_ALLOW_THREADS;
    err = dbc->c_get(dbc, &key, (DBT *) &data, flags | DB_SET_RANGE);
    Py_END_ALLOW_THREADS;

    switch (err) {
      case 0:
      {
          if (data.found != 1)
              Py_RETURN_NONE;

          if (dataTypes == Nil)
          {
              Py_INCREF(Nil);
              return Nil;
          }

          if (((t_record *) data.dbt.app_data)->size == 1)
          {
              Py_DECREF((PyObject *) data.dbt.app_data);
              Py_RETURN_NONE;
          }
           
          return (PyObject *) data.dbt.app_data;
      }

      case DB_NOTFOUND:
        Py_RETURN_NONE;

      default:
        return raiseDBError(err);
    }
}


/* uCol, uRef, ~version -> uCol, version, uRef */

static int _t_ref_container_historyKey(DB *secondary,
                                       const DBT *key, const DBT *data,
                                       DBT *result)
{
    char *buffer = (char *) malloc(36);
    unsigned long version = ~*(unsigned long *) ((char *) key->data + 32);

    if (!buffer)
        return ENOMEM;

    memcpy(buffer, key->data, 16);
    memcpy(buffer + 16, &version, 4);
    memcpy(buffer + 20, (char *) key->data + 16, 16);

    result->data = buffer;
    result->flags = DB_DBT_APPMALLOC;
    result->size = 36;

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
    char *buffer = (char *) malloc(36);

    if (!buffer)
        return ENOMEM;

    memcpy(buffer, data->data, 16);
    memcpy(buffer + 16, key->data, 20);

    result->data = buffer;
    result->flags = DB_DBT_APPMALLOC;
    result->size = 36;

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
    char *buffer = (char *) malloc(20);
    unsigned long version = ~*(unsigned long *) ((char *) key->data + 16);

    if (!buffer)
        return ENOMEM;

    memcpy(buffer, &version, 4);
    memcpy(buffer + 4, key->data, 16);

    result->data = buffer;
    result->flags = DB_DBT_APPMALLOC;
    result->size = 20;

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
    unsigned long version;
    unsigned int status;

    if (!PyArg_ParseTuple(args, "OkOi", &txn, &version, &uItem, &status))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
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
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        DBT key, data;
        char keyBuffer[20];
        unsigned int value;
        int err;

        memcpy(keyBuffer, PyString_AS_STRING(((t_uuid *) uItem)->uuid), 16);
        *((unsigned long *) (&keyBuffer[16])) = htonl(~(unsigned long) version);

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
