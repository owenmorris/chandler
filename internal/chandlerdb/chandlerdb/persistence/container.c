/*
 *  Copyright (c) 2003-2007 Open Source Applications Foundation
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
#include <malloc.h>
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

static PyObject *startTransaction_NAME;
static PyObject *abortTransaction_NAME;
static PyObject *_logDL_NAME;

typedef struct {
    PyObject_HEAD
    t_db *db;
    int flags;
    t_store *store;
    PyObject *key;
} t_container;


static int t_container_traverse(t_container *self, visitproc visit, void *arg);
static int t_container_clear(t_container *self);
static void t_container_dealloc(t_container *self);
static PyObject *t_container_new(PyTypeObject *type,
                                 PyObject *args, PyObject *kwds);
static int t_container_init(t_container *self, PyObject *args, PyObject *kwds);

static PyObject *t_container_find_record(t_container *self, PyObject *args);
static PyObject *t_container_openCursor(t_container *self, PyObject *args);
static PyObject *t_container_closeCursor(t_container *self, PyObject *args);

static PyObject *_t_container__getThreaded(t_container *self);
static PyObject *t_container__getThreaded(t_container *self, void *data);

static PyMemberDef t_container_members[] = {
    { "db", T_OBJECT, offsetof(t_container, db), READONLY, "" },
    { "flags", T_UINT, offsetof(t_container, flags), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_container_methods[] = {
    { "find_record", (PyCFunction) t_container_find_record, METH_VARARGS, NULL },
    { "openCursor", (PyCFunction) t_container_openCursor, METH_VARARGS, NULL },
    { "closeCursor", (PyCFunction) t_container_closeCursor, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_container_properties[] = {
    { "_threaded", (getter) t_container__getThreaded, 0, NULL, NULL },
    { NULL, NULL, NULL, NULL, NULL }
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
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                                /* tp_flags */
    "C Container type",                                  /* tp_doc */
    (traverseproc)t_container_traverse,                  /* tp_traverse */
    (inquiry)t_container_clear,                          /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_container_methods,                                 /* tp_methods */
    t_container_members,                                 /* tp_members */
    t_container_properties,                              /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_container_init,                          /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_container_new,                            /* tp_new */
};


static int t_container_traverse(t_container *self, visitproc visit, void *arg)
{
    Py_VISIT(self->store);
    Py_VISIT(self->key);

    return 0;
}

static int t_container_clear(t_container *self)
{
    if (self->key)
    {
        PyObject *locals = PyThreadState_GetDict();

        if (locals)
        {
            PyObject *threaded = PyDict_GetItem(locals, self->key);

            if (threaded)
            {
                Py_INCREF(threaded);
                PyDict_DelItem(locals, self->key);
                Py_CLEAR(threaded);
            }
        }
    }

    Py_CLEAR(self->store);
    Py_CLEAR(self->key);

    return 0;
}

static void t_container_dealloc(t_container *self)
{
    t_container_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_container_new(PyTypeObject *type,
                                 PyObject *args, PyObject *kwds)
{
    t_container *self = (t_container *) type->tp_alloc(type, 0);

    if (self)
    {
        self->key = PyInt_FromLong(_Py_HashPointer(self));
        self->flags = 0;
    }

    return (PyObject *) self;
}

static int t_container_init(t_container *self, PyObject *args, PyObject *kwds)
{
    PyObject *db, *store;

    if (!PyArg_ParseTuple(args, "OO", &db, &store))
        return -1;

    if (!PyObject_TypeCheck(db, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, db);
        return -1;
    }

    if (!PyObject_TypeCheck(store, CStore))
    {
        PyErr_SetObject(PyExc_TypeError, store);
        return -1;
    }

    Py_INCREF(db);
    self->db = (t_db *) db;

    Py_INCREF(store);
    self->store = (t_store *) store;

    return 0;
}

static PyObject *_t_container_openCursor(t_container *self, PyObject *db)
{
    PyObject *threaded, *cursor, *txn;
    int flags = self->flags;

    if (db == Py_None)
        db = (PyObject *) self->db;
    else if (!PyObject_TypeCheck(db, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, db);
        return NULL;
    }

    threaded = _t_container__getThreaded(self);
    if (!threaded)
        return NULL;

    cursor = PyDict_GetItem(threaded, db);
    if (cursor)
    {
        if (!PyObject_TypeCheck(cursor, CDBCursor))
        {
            PyErr_SetObject(PyExc_TypeError, cursor);
            return NULL;
        }

        if (((t_cursor *) cursor)->dbc)
            return _t_cursor_dup((t_cursor *) cursor, 0);
    }

    txn = _t_store_getTxn(self->store);
    if (!txn)
        return NULL;

    cursor = _t_db_cursor((t_db *) db, txn, flags);
    if (!cursor)
        return NULL;

    PyDict_SetItem(threaded, db, cursor);

    return cursor;
}

static PyObject *t_container_openCursor(t_container *self, PyObject *args)
{
    PyObject *db = Py_None;

    if (!PyArg_ParseTuple(args, "|O", &db))
        return NULL;

    return _t_container_openCursor(self, db);
}

static int _t_container_closeCursor(t_container *self,
                                    PyObject *cursor, PyObject *db)
{
    PyObject *threaded;

    if (cursor == Py_None)
        return 0;

    if (!PyObject_TypeCheck(cursor, CDBCursor))
    {
        PyErr_SetObject(PyExc_TypeError, cursor);
        return -1;
    }

    if (db == Py_None)
        db = (PyObject *) self->db;
    else if (!PyObject_TypeCheck(db, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, db);
        return -1;
    }

    if (_t_cursor_close((t_cursor *) cursor) < 0)
        return -1;

    threaded = _t_container__getThreaded(self);
    if (!threaded)
        return -1;

    if (PyDict_GetItem(threaded, db) == cursor)
        PyDict_DelItem(threaded, db);

    return 0;
}

static PyObject *t_container_closeCursor(t_container *self, PyObject *args)
{
    PyObject *cursor, *db = Py_None;

    if (!PyArg_ParseTuple(args, "O|O", &cursor, &db))
        return NULL;

    if (_t_container_closeCursor(self, cursor, db) < 0)
        return NULL;

    Py_RETURN_NONE;
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
static PyObject *_t_container_find_record(t_container *self, PyObject *cursor,
                                          PyObject *keyRecord,
                                          PyObject *dataTypes,
                                          int flags, PyObject *defaultValue,
                                          int returnBoth)
{
    char keyBuffer[256], keyData[256];
    int err, keySize;
    DBT key;
    t_data_dbt data;
    DBC *dbc;

    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));

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

static PyObject *t_container_find_record(t_container *self, PyObject *args)
{
    PyObject *cursor, *keyRecord, *dataTypes, *defaultValue = NULL;
    int flags = 0, returnBoth = 0;

    if (!PyArg_ParseTuple(args, "OOO|iOi", &cursor, &keyRecord, &dataTypes,
                          &flags, &defaultValue, &returnBoth))
        return NULL;

    return _t_container_find_record(self, cursor, keyRecord, dataTypes,
                                    flags, defaultValue, returnBoth);
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


/* _threaded */

static PyObject *_t_container__getThreaded(t_container *self)
{
    PyObject *locals = PyThreadState_GetDict();
    PyObject *threaded = NULL;

    if (!locals)
    {
        PyErr_SetString(PyExc_RuntimeError, "Could not get thread state dict");
        return NULL;
    }

    if (self->key)
        threaded = PyDict_GetItem(locals, self->key);

    if (!threaded)
    {
        threaded = PyDict_New();
        if (!threaded)
            return NULL;

        PyDict_SetItem(locals, self->key, threaded);
        Py_DECREF(threaded);
    }

    return threaded;  /* borrowed reference */
}

static PyObject *t_container__getThreaded(t_container *self, void *data)
{
    PyObject *threaded = _t_container__getThreaded(self);

    if (threaded)
        Py_INCREF(threaded);

    return threaded;
}

static PyObject *_t_container_load_record(t_container *self, PyObject *view,
                                          PyObject *key, PyObject *dataTypes,
                                          PyObject *defaultValue,
                                          int returnBoth)
{
    PyObject *store = (PyObject *) self->store;

    while (1) {
        PyObject *result =
            PyObject_CallMethodObjArgs(store, startTransaction_NAME,
                                       view, NULL);
        PyObject *type = NULL, *value = NULL, *traceback = NULL;
        PyObject *cursor = NULL, *record = NULL, *status;
        int txnStatus;

        if (!result)
            goto done;

        txnStatus = PyInt_AsLong(result);
        Py_DECREF(result);

        cursor = _t_container_openCursor(self, Py_None);
        if (!cursor)
            goto error;

        record = _t_container_find_record(self, cursor, key, dataTypes,
                                          self->flags, defaultValue,
                                          returnBoth);
        if (!record)
            goto error;

      finally:
        if (cursor)
        {
            if (_t_container_closeCursor(self, cursor, Py_None) < 0)
            {
                Py_CLEAR(cursor);
                Py_CLEAR(record);
                goto error;
            }
            Py_CLEAR(cursor);
        }
        status = PyInt_FromLong(txnStatus);
        result = PyObject_CallMethodObjArgs(store, abortTransaction_NAME,
                                            view, status, NULL);
        Py_DECREF(status);
        if (!result)
        {
            Py_CLEAR(record);
            goto done;
        }
        Py_DECREF(result);
        if (type == NULL)
            goto done;

      error:
        if (type == NULL)
        {
            PyErr_Fetch(&type, &value, &traceback);
            goto finally;
        }
        if (txnStatus & TXN_STARTED &&
            PyErr_GivenExceptionMatches(type, PyExc_DBLockDeadlockError))
        {
            result = PyObject_CallMethodObjArgs(store, _logDL_NAME, NULL);
            if (!result)
                goto done;
            Py_DECREF(result);
            Py_CLEAR(type);
            Py_CLEAR(value);
            Py_CLEAR(traceback);
            continue;
        }

      done:
        if (type)
            PyErr_Restore(type, value, traceback);

        return record;
    }
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
static PyObject *t_value_container_loadValues(t_value_container *self,
                                              PyObject *args);
static PyObject *t_value_container_saveValue(t_value_container *self,
                                             PyObject *args);


static PyMemberDef t_value_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_value_container_methods[] = {
    { "loadValue", (PyCFunction) t_value_container_loadValue, METH_VARARGS, "" },
    { "loadValues", (PyCFunction) t_value_container_loadValues, METH_VARARGS, "" },
    { "saveValue", (PyCFunction) t_value_container_saveValue, METH_VARARGS, "" },
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

static PyObject *_t_value_container_loadValue(t_value_container *self,
                                              t_uuid *uItem, t_uuid *uKey,
                                              PyObject *types, PyObject *txn)
{
    char buffer[32];
    DBT key, data;

    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));
    memcpy(buffer, PyString_AS_STRING(uItem->uuid), 16);
    memcpy(buffer + 16, PyString_AS_STRING(uKey->uuid), 16);
    key.size = 32;
    key.data = buffer;

    data.flags = DB_DBT_USERCOPY;
    data.app_data = types;
    data.usercopy = (usercopy_fn) _t_db_read_record;

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        DB *db = (((t_container *) self)->db)->db;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = db->get(db, db_txn, &key, &data, self->container.flags);
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

static PyObject *t_value_container_loadValue(t_value_container *self,
                                             PyObject *args)
{
    PyObject *uItem, *uKey, *types, *txn;

    if (!PyArg_ParseTuple(args, "OOO", &uItem, &uKey, &types))
        return NULL;

    if (!PyUUID_Check(uItem))
    {
        PyErr_SetObject(PyExc_TypeError, uItem);
        return NULL;
    }

    if (!PyUUID_Check(uKey))
    {
        PyErr_SetObject(PyExc_TypeError, uKey);
        return NULL;
    }

    if (types->ob_type != Record && !PyTuple_CheckExact(types))
    {
        PyErr_SetObject(PyExc_TypeError, types);
        return NULL;
    }

    txn = _t_store_getTxn(self->container.store); /* borrows ref */
    if (!txn)
        return NULL;

    return _t_value_container_loadValue(self, (t_uuid *) uItem,
                                        (t_uuid *) uKey, types, txn);
}


#if 0  /* without DB_MULTIPLE_KEY */

static PyObject *t_value_container_loadValues(t_value_container *self,
                                              PyObject *args)
{
    PyObject *uItem, *uKeys, *types, *txn, *values;
    char buffer[32];
    int i;

    if (!PyArg_ParseTuple(args, "OOO", &uItem, &uKeys, &types))
        return NULL;

    if (!PyTuple_Check(uKeys))
    {
        PyErr_SetObject(PyExc_TypeError, uKeys);
        return NULL;
    }

    if (!PyTuple_Check(types))
    {
        PyErr_SetObject(PyExc_TypeError, types);
        return NULL;
    }

    txn = _t_store_getTxn(self->container.store); /* borrows ref */
    if (!txn)
        return NULL;

    values = PyDict_New();
    if (!values)
        return NULL;

    memcpy(buffer, PyString_AS_STRING(((t_uuid *) uItem)->uuid), 16);

    for (i = 0; i < PyTuple_GET_SIZE(uKeys); i++) {
        PyObject *uKey = PyTuple_GET_ITEM(uKeys, i);
        DBT key, data;

        if (!PyUUID_Check(uKey))
        {
            Py_DECREF(values);
            return NULL;
        }

        memset(&key, 0, sizeof(key));
        memset(&data, 0, sizeof(data));

        memcpy(buffer + 16, PyString_AS_STRING(((t_uuid *) uKey)->uuid), 16);
        key.size = 32;
        key.data = buffer;

        data.flags = DB_DBT_USERCOPY;
        data.app_data = _t_record_new_read(types);
        data.usercopy = (usercopy_fn) _t_db_read_record;

        {
            DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
            DB *db = (((t_container *) self)->db)->db;
            int err;

            Py_BEGIN_ALLOW_THREADS;
            err = db->get(db, db_txn, &key, &data, self->container.flags);
            Py_END_ALLOW_THREADS;

            switch (err) {
              case 0:
                PyDict_SetItem(values, uKey, (PyObject *) data.app_data);
                Py_DECREF((PyObject *) data.app_data);
                break;
              case DB_NOTFOUND:
                PyDict_SetItem(values, uKey, Py_None);
                break;
              default:
                Py_DECREF(values);
                return raiseDBError(err);
            }
        }
    }

    return values;
}

#else  /* with DB_MULTIPLE_KEY */

static PyObject *t_value_container_loadValues(t_value_container *self,
                                              PyObject *args)
{
    PyObject *uItem, *uKeys, *types, *uKey, *txn;
    PyObject *values = NULL, *record = NULL;
    char *dataBuffer = NULL;
    DBC *dbc = NULL;
    int size;

    if (!PyArg_ParseTuple(args, "OOO", &uItem, &uKeys, &types))
        return NULL;

    if (!PyUUID_Check(uItem))
    {
        PyErr_SetObject(PyExc_TypeError, uItem);
        return NULL;
    }

    if (!PyTuple_Check(uKeys))
    {
        PyErr_SetObject(PyExc_TypeError, uKeys);
        return NULL;
    }

    if (!PyTuple_Check(types))
    {
        PyErr_SetObject(PyExc_TypeError, types);
        return NULL;
    }

    values = PyDict_New();
    if (!values)
        return NULL;

    size = PyTuple_GET_SIZE(uKeys);

    switch (size) {
      case 0:
        return values;

      case 1:
        uKey = PyTuple_GET_ITEM(uKeys, 0);
        if (!PyUUID_Check(uKey))
        {
            PyErr_SetObject(PyExc_TypeError, uKey);
            goto error;
        }
        txn = _t_store_getTxn(self->container.store); /* borrows ref */
        if (!txn)
            goto error;
        record = _t_value_container_loadValue(self, (t_uuid *) uItem,
                                              (t_uuid *) uKey, types, txn);
        if (!record)
            goto error;
        if (record == Py_None)
        {
            PyErr_SetObject(PyExc_KeyError, uKey);
            goto error;
        }

        PyDict_SetItem(values, uKey, record);
        Py_DECREF(record);

        return values;

      default:
      {
          DB *db = self->container.db->db;
          DBT key, data;
          DB_TXN *db_txn;
          PyObject *uKey;
          char keyBuffer[32];
          unsigned int pageSize;
          int i, err;
          char *buffer;
          void *pointer;

          err = db->get_pagesize(db, &pageSize);
          if (err)
          {
              raiseDBError(err);
              goto error;
          }

          buffer = alloca(pageSize);
          dataBuffer = NULL;

          uKey = PyTuple_GET_ITEM(uKeys, 0);
          if (!PyUUID_Check(uKey))
          {
              PyErr_SetObject(PyExc_TypeError, uKey);
              goto error;
          }

          txn = _t_store_getTxn(self->container.store); /* borrows ref */
          if (!txn)
              goto error;
          db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;

          Py_BEGIN_ALLOW_THREADS;
          err = db->cursor(db, db_txn, &dbc, self->container.flags);
          Py_END_ALLOW_THREADS;
          if (err)
          {
              raiseDBError(err);
              goto error;
          }

          i = 0;

        again:
          memset(&key, 0, sizeof(key));
          memset(&data, 0, sizeof(data));

          memcpy(keyBuffer,
                 PyString_AS_STRING(((t_uuid *) uItem)->uuid), 16);
          memcpy(keyBuffer + 16,
                 PyString_AS_STRING(((t_uuid *) uKey)->uuid), 16);
          key.size = 32;
          key.data = keyBuffer;

          if (dataBuffer)
          {
              free(dataBuffer);
              dataBuffer = NULL;
          }
          data.ulen = pageSize;
          data.data = buffer;
          data.flags = DB_DBT_USERMEM;

        bigger:
          Py_BEGIN_ALLOW_THREADS;
          err = dbc->c_get(dbc, &key, &data,
                           self->container.flags | DB_SET | DB_MULTIPLE_KEY);
          Py_END_ALLOW_THREADS;

          switch (err) {
            case 0:
              DB_MULTIPLE_INIT(pointer, &data);
              break;
            case DB_BUFFER_SMALL:
              data.ulen = data.size;
              data.data = dataBuffer = malloc(data.size);
              if (!dataBuffer)
              {
                  PyErr_SetNone(PyExc_MemoryError);
                  goto error;
              }
              goto bigger;
            default:
              raiseDBError(err);
              goto error;
          }

          while (pointer != NULL) {
              void *keyData = NULL, *dataData = NULL;
              int keyLen = 0, dataLen = 0;

              DB_MULTIPLE_KEY_NEXT(pointer, &data, keyData, keyLen,
                                   dataData, dataLen);
              if (keyData == NULL)
                  goto again;

              if (!memcmp(((char *) keyData) + 16,
                          PyString_AS_STRING(((t_uuid *) uKey)->uuid), 16))
              {
                  record = (PyObject *) _t_record_new_read(types);
                  if (!record)
                      goto error;
                  if (_t_record_read((t_record *) record,
                                     (unsigned char *) dataData, dataLen) < 0)
                      goto error;

                  PyDict_SetItem(values, uKey, record);
                  Py_CLEAR(record);

                  if (++i >= size)
                      break;

                  uKey = PyTuple_GET_ITEM(uKeys, i);
                  if (!PyUUID_Check(uKey))
                  {
                      PyErr_SetObject(PyExc_TypeError, uKey);
                      goto error;
                  }
              }
          }

          if (i < size)
          {
              PyErr_SetObject(PyExc_KeyError, uKey);
              goto error;
          }

          if (dataBuffer)
          {
              free(dataBuffer);
              dataBuffer = NULL;
          }

          if (dbc)
          {
              dbc->c_close(dbc);
              dbc = NULL;
          }

          return values;
      }
    }

  error:
    if (dbc)
        dbc->c_close(dbc);
    if (dataBuffer)
        free(dataBuffer);

    Py_CLEAR(values);
    Py_CLEAR(record);

    return NULL;
}

#endif


static PyObject *t_value_container_saveValue(t_value_container *self,
                                             PyObject *args)
{
    PyObject *uItem, *uKey, *txn;
    DBT key, data;
    int result;

    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));

    if (!PyArg_ParseTuple(args, "OOO", &uItem, &uKey, &data.app_data))
        return NULL;
    
    if (!PyUUID_Check(uItem))
    {
        PyErr_SetObject(PyExc_TypeError, uItem);
        return NULL;
    }

    if (!PyUUID_Check(uKey))
    {
        PyErr_SetObject(PyExc_TypeError, uKey);
        return NULL;
    }

    if (!PyObject_TypeCheck((PyObject *) data.app_data, Record))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) data.app_data);
        return NULL;
    }
    
    txn = _t_store_getTxn(self->container.store); /* borrows ref */
    if (!txn)
        return NULL;

    args = PyTuple_New(4);
    PyTuple_SET_ITEM(args, 0, PyInt_FromLong(R_UUID));
    PyTuple_SET_ITEM(args, 1, uItem); Py_INCREF(uItem);
    PyTuple_SET_ITEM(args, 2, PyInt_FromLong(R_UUID));
    PyTuple_SET_ITEM(args, 3, uKey); Py_INCREF(uKey);

    key.app_data = PyObject_Call((PyObject *) Record, args, NULL);
    Py_DECREF(args);
    if (!key.app_data)
        return NULL;

    result = _t_db_put_record(self->container.db, &key, &data, txn, 0);
    Py_DECREF((PyObject *) key.app_data);

    if (result < 0)
        return NULL;

    return PyInt_FromLong(key.size + data.size);
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
    { "associateHistory", (PyCFunction) t_ref_container_associateHistory, METH_VARARGS, NULL },
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
    unsigned int version;
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
    unsigned int version = ~*(unsigned int *) ((char *) key->data + 32);

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
static PyObject *t_item_container_findItem(t_item_container *self,
                                           PyObject *args);


static PyMemberDef t_item_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_item_container_methods[] = {
    { "associateKind", (PyCFunction) t_item_container_associateKind, METH_VARARGS, NULL },
    { "associateVersion", (PyCFunction) t_item_container_associateVersion, METH_VARARGS, NULL },
    { "setItemStatus", (PyCFunction) t_item_container_setItemStatus, METH_VARARGS, NULL },
    { "findItem", (PyCFunction) t_item_container_findItem, METH_VARARGS, NULL },
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
    unsigned int version = ~*(unsigned int *) ((char *) key->data + 16);

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
    unsigned int version;
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
        *((unsigned int *) (&keyBuffer[16])) = htonl(~(unsigned int) version);

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
        err = db->get(db, db_txn, &key, &data, self->container.flags);
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

/*
    def findItem(self, view, version, uuid, dataTypes):

        store = self.store
        key = Record(Record.UUID, uuid,
                     Record.INT, ~version)

        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction(view)
                cursor = self.c.openCursor()

                key, item = self.c.find_record(cursor, key, dataTypes,
                                               self.c.flags, NONE_PAIR, True)
                if item is not None:
                    return ~key[1], item

                return NONE_PAIR

            except DBLockDeadlockError:
                if txnStatus & store.TXN_STARTED:
                    store._logDL()
                    continue
                else:
                    raise

            finally:
                self.c.closeCursor(cursor)
                store.abortTransaction(view, txnStatus)
*/

static PyObject *t_item_container_findItem(t_item_container *self,
                                           PyObject *args)
{
    PyObject *view, *uuid, *dataTypes, *key, *record, *foundItem;
    unsigned int version;

    if (!PyArg_ParseTuple(args, "OiOO", &view, &version, &uuid, &dataTypes))
        return NULL;

    args = Py_BuildValue("(iOii)", R_UUID, uuid, R_INT, ~version);
    key = PyObject_Call((PyObject *) Record, args, NULL);
    Py_DECREF(args);
    if (!key)
        return NULL;

    record = _t_container_load_record((t_container *) self, view,
                                      key, dataTypes, None_PAIR, 1);
    Py_DECREF(key);
    if (!record)
        return NULL;

    if (PyTuple_GET_ITEM(record, 1) == Py_None)
    {
        Py_DECREF(record);
        Py_INCREF(None_PAIR);
        foundItem = None_PAIR;
    }
    else
    {
        PyObject *keyRecord = PyTuple_GET_ITEM(record, 0);
        PyObject *itemRecord = PyTuple_GET_ITEM(record, 1);
        PyObject *itemVer = _t_record_item((t_record *) keyRecord, 1);

        itemVer = PyInt_FromLong(~PyInt_AsLong(itemVer));
        foundItem = PyTuple_Pack(2, itemVer, itemRecord);
        Py_DECREF(itemVer);
        Py_DECREF(record);
    }

    return foundItem;
}


typedef struct {
    t_container container;
} t_indexes_container;


static void t_indexes_container_dealloc(t_indexes_container *self);
static PyObject *t_indexes_container_new(PyTypeObject *type,
                                         PyObject *args, PyObject *kwds);
static int t_indexes_container_init(t_indexes_container *self,
                                    PyObject *args, PyObject *kwds);
static PyObject *t_indexes_container_loadKey(t_indexes_container *self,
                                             PyObject *args);


static PyMemberDef t_indexes_container_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_indexes_container_methods[] = {
    { "loadKey", (PyCFunction) t_indexes_container_loadKey, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject IndexesContainerType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.CIndexesContainer",        /* tp_name */
    sizeof(t_indexes_container),                         /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_indexes_container_dealloc,             /* tp_dealloc */
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
    "C IndexesContainer type",                           /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_indexes_container_methods,                         /* tp_methods */
    t_indexes_container_members,                         /* tp_members */
    0,                                                   /* tp_getset */
    &ContainerType,                                      /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_indexes_container_init,                  /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_indexes_container_new,                    /* tp_new */
};


static void t_indexes_container_dealloc(t_indexes_container *self)
{
    ContainerType.tp_dealloc((PyObject *) self);
}

static PyObject *t_indexes_container_new(PyTypeObject *type,
                                         PyObject *args, PyObject *kwds)
{
    PyObject *self = ContainerType.tp_new(type, args, kwds);

    return (PyObject *) self;
}

static int t_indexes_container_init(t_indexes_container *self,
                                    PyObject *args, PyObject *kwds)
{
    return ContainerType.tp_init((PyObject *) self, args, kwds);
}

/*
    def loadKey(self, view, uIndex, version, uKey):
        
        store = self.store
        
        key = Record(Record.UUID, uIndex,
                     Record.UUID, uKey,
                     Record.INT, ~version)

        while True:
            txnStatus = 0
            cursor = None

            try:
                txnStatus = store.startTransaction(view)
                cursor = self.c.openCursor()

                entry = self.c.find_record(cursor, key,
                                           IndexesContainer.ENTRY_TYPES,
                                           self.c.flags, None)
                if entry is not None:
                    level, points = entry.data
                    if level == 0:  # deleted entry
                        return None
                    
                    node = SkipList.Node(level)

                    for lvl in xrange(0, level):
                        point = node[lvl+1]
                        (point.prevKey, point.nextKey,
                         point.dist) = points[lvl*3:(lvl+1)*3]

                    return node

                return None
                        
            except DBLockDeadlockError:
                if txnStatus & store.TXN_STARTED:
                    store._logDL()
                    continue
                else:
                    raise

            finally:
                self.c.closeCursor(cursor)
                store.abortTransaction(view, txnStatus)
*/

static PyObject *t_indexes_container_loadKey(t_indexes_container *self,
                                             PyObject *args)
{
    PyObject *view, *uIndex, *uKey, *record;
    PyObject *node = NULL, *key, *dataTypes;
    unsigned int version;

    if (!PyArg_ParseTuple(args, "OOiO", &view, &uIndex, &version, &uKey))
        return NULL;

    args = Py_BuildValue("(iOiOii)", R_UUID, uIndex, R_UUID, uKey,
                         R_INT, ~version);
    key = PyObject_Call((PyObject *) Record, args, NULL);
    Py_DECREF(args);
    if (!key)
        return NULL;

    dataTypes = Py_BuildValue("(ii)", R_BYTE, R_RECORD);
    record = _t_container_load_record((t_container *) self, view,
                                      key, dataTypes, Py_None, 0);
    Py_DECREF(dataTypes);
    Py_DECREF(key);
    if (!record)
        return NULL;

    if (record != Py_None)
    {
        PyObject *level = _t_record_item((t_record *) record, 0);
        t_record *points = (t_record *) _t_record_item((t_record *) record, 1);
        PyObject *args;
        int i, lvl;

        if (!level || !points)
            goto error;

        lvl = PyInt_AsLong(level);
        if (lvl == 0) /* deleted entry */
        {
            Py_DECREF(record);
            Py_RETURN_NONE;
        }

        args = PyTuple_Pack(1, level);
        node = PyObject_Call((PyObject *) SkipList_Node, args, NULL);
        Py_DECREF(args);
        if (!node)
            goto error;

        for (i = 0; i < lvl; i++) {
            t_point *point = (t_point *)
                SkipList_Node->tp_as_sequence->sq_item(node, i + 1);
            PyObject *value;

            if (!point)
                goto error;

            value = _t_record_item(points, i*3);
            if (!value)
                goto error;
            Py_INCREF(value);
            point->prevKey = value;
            
            value = _t_record_item(points, i*3 + 1);
            if (!value)
                goto error;
            Py_INCREF(value);
            point->nextKey = value;

            value = _t_record_item(points, i*3 + 2);
            if (!value)
                goto error;
            point->dist = PyInt_AsLong(value);

            Py_DECREF(point);
        }

        Py_DECREF(record);
        return node;
    }

    return record;

  error:
    Py_DECREF(record);
    Py_XDECREF(node);
    return NULL;
}


void _init_container(PyObject *m)
{
    if (PyType_Ready(&ContainerType) >= 0 &&
        PyType_Ready(&ValueContainerType) >= 0 &&
        PyType_Ready(&RefContainerType) >= 0 &&
        PyType_Ready(&ItemContainerType) >= 0 &&
        PyType_Ready(&IndexesContainerType) >= 0)
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

            Py_INCREF(&IndexesContainerType);
            PyModule_AddObject(m, "CIndexesContainer",
                               (PyObject *) &IndexesContainerType);

            startTransaction_NAME = PyString_FromString("startTransaction");
            abortTransaction_NAME = PyString_FromString("abortTransaction");
            _logDL_NAME = PyString_FromString("_logDL");
        }
    }
}
