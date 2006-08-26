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


#include <Python.h>
#include "structmember.h"

#include "c.h"

static void t_db_dealloc(t_db *self);
static int t_db_traverse(t_db *self, visitproc visit, void *arg);
static int t_db_clear(t_db *self);
static PyObject *t_db_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_db_init(t_db *self, PyObject *args, PyObject *kwds);

static PyObject *t_db_open(t_db *self, PyObject *args, PyObject *kwds);
static PyObject *t_db_close(t_db *self, PyObject *args);
static PyObject *t_db_associate(t_db *self, PyObject *args);
static PyObject *t_db_compact(t_db *self, PyObject *args);
static PyObject *t_db_get(t_db *self, PyObject *args);
static PyObject *t_db_put(t_db *self, PyObject *args);
static PyObject *t_db_delete(t_db *self, PyObject *args);
static PyObject *t_db_cursor(t_db *self, PyObject *args);

static PyObject *t_db_get_lorder(t_db *self, void *data);
static int t_db_set_lorder(t_db *self, PyObject *value, void *data);
static PyObject *t_db_get_dbtype(t_db *self, void *data);

static PyMemberDef t_db_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_db_methods[] = {
    { "open", (PyCFunction) t_db_open, METH_VARARGS | METH_KEYWORDS, NULL },
    { "close", (PyCFunction) t_db_close, METH_VARARGS, NULL },
    { "associate", (PyCFunction) t_db_associate, METH_VARARGS, NULL },
    { "compact", (PyCFunction) t_db_compact, METH_VARARGS, NULL },
    { "get", (PyCFunction) t_db_get, METH_VARARGS, NULL },
    { "put", (PyCFunction) t_db_put, METH_VARARGS, NULL },
    { "delete", (PyCFunction) t_db_delete, METH_VARARGS, NULL },
    { "cursor", (PyCFunction) t_db_cursor, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_db_properties[] = {
    { "lorder", (getter) t_db_get_lorder, (setter) t_db_set_lorder,
      "database byte order", NULL },
    { "dbtype", (getter) t_db_get_dbtype, (setter) NULL,
      "database type", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject DBType = {
    PyObject_HEAD_INIT(NULL)
    0,                                               /* ob_size */
    "chandlerdb.persistence.c.DB",                   /* tp_name */
    sizeof(t_db),                                    /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)t_db_dealloc,                        /* tp_dealloc */
    0,                                               /* tp_print */
    0,                                               /* tp_getattr */
    0,                                               /* tp_setattr */
    0,                                               /* tp_compare */
    0,                                               /* tp_repr */
    0,                                               /* tp_as_number */
    0,                                               /* tp_as_sequence */
    0,                                               /* tp_as_mapping */
    0,                                               /* tp_hash  */
    0,                                               /* tp_call */
    0,                                               /* tp_str */
    0,                                               /* tp_getattro */
    0,                                               /* tp_setattro */
    0,                                               /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,         /* tp_flags */
    "C DB type",                                     /* tp_doc */
    (traverseproc)t_db_traverse,                     /* tp_traverse */
    (inquiry)t_db_clear,                             /* tp_clear */
    0,                                               /* tp_richcompare */
    0,                                               /* tp_weaklistoffset */
    0,                                               /* tp_iter */
    0,                                               /* tp_iternext */
    t_db_methods,                                    /* tp_methods */
    t_db_members,                                    /* tp_members */
    t_db_properties,                                 /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    (initproc)t_db_init,                             /* tp_init */
    0,                                               /* tp_alloc */
    (newfunc)t_db_new,                               /* tp_new */
};


static int _t_db_close(t_db *self, int flags)
{
    if (self->db)
    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->db->close(self->db, flags);
        Py_END_ALLOW_THREADS;

        if (err)
        {
            raiseDBError(err);
            return -1;
        }

        self->db = NULL;
    }

    return 0;
}

static void t_db_dealloc(t_db *self)
{
    t_db_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_db_traverse(t_db *self, visitproc visit, void *arg)
{
    Py_VISIT(self->associate_cb);

    return 0;
}

static int t_db_clear(t_db *self)
{
    _t_db_close(self, 0);
    Py_CLEAR(self->associate_cb);

    return 0;
}

static PyObject *t_db_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_db *db = (t_db *) type->tp_alloc(type, 0);

    db->associate_cb = NULL;

    return (PyObject *) db;
}

static int t_db_init(t_db *self, PyObject *args, PyObject *kwds)
{
    PyObject *env;
    int flags = 0;

    if (!PyArg_ParseTuple(args, "O|i", &env, &flags))
        return -1;

    if (!PyObject_TypeCheck(env, CDBEnv))
    {
        PyErr_SetObject(PyExc_TypeError, env);
        return -1;
    }
    else
    {
        DB_ENV *db_env = ((t_env *) env)->db_env;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = db_create(&self->db, db_env, flags);
        Py_END_ALLOW_THREADS;

        if (err)
        {
            raiseDBError(err);
            return -1;
        }

        self->db->app_private = self;
    }

    return 0;
}

static PyObject *t_db_open(t_db *self, PyObject *args, PyObject *kwds)
{
    int dbtype = DB_UNKNOWN, flags = 0, mode = 0;
    char *filename = NULL, *dbname = NULL;
    PyObject *txn = Py_None;
    char *names[] = {
        "filename", "dbname", "txn", "dbtype", "flags", "mode", NULL
    };

    if (!self->db)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "z|zOiii", names,
				     &filename, &dbname, &txn,
                                     &dbtype, &flags, &mode))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->db->open(self->db, db_txn, filename, dbname,
                             dbtype, flags, mode);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        Py_RETURN_NONE;
    }
}

static PyObject *t_db_close(t_db *self, PyObject *args)
{
    int flags = 0;

    if (!PyArg_ParseTuple(args, "|i", &flags))
        return NULL;

    if (_t_db_close(self, flags))
        return NULL;
        
    Py_RETURN_NONE;
}

static int _t_db_associate_callback(DB *secondary,
                                    const DBT *key, const DBT *data,
                                    DBT *result)
{
    t_db *db = (t_db *) secondary->app_private;
    PyObject *args, *indexKey;
    PyGILState_STATE state = PyGILState_Ensure();

    if (!PyObject_TypeCheck(db, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) db);
        PyGILState_Release(state);

        return DB_PYTHON_ERROR;
    }

    args = Py_BuildValue("(s#s#)",
                         key->data, key->size, data->data, data->size);
    indexKey = PyObject_Call(db->associate_cb, args, NULL);
    Py_DECREF(args);

    if (indexKey == NULL)
    {
        PyGILState_Release(state);
        return DB_PYTHON_ERROR;
    }

    if (indexKey == Py_None)
    {
        Py_DECREF(indexKey);
	PyGILState_Release(state);

        return DB_DONOTINDEX;
    }

    if (!PyString_Check(indexKey))
    {
        PyErr_SetObject(PyExc_TypeError, indexKey);
        Py_DECREF(indexKey);
	PyGILState_Release(state);

        return DB_PYTHON_ERROR;
    }

    result->size = PyString_GET_SIZE(indexKey);
    result->data = malloc(result->size);
    if (!result->data)
    {
        Py_DECREF(indexKey);
	PyGILState_Release(state);

        return ENOMEM;
    }

    result->flags = DB_DBT_APPMALLOC;
    memcpy(result->data, PyString_AS_STRING(indexKey), result->size);

    Py_DECREF(indexKey);
    PyGILState_Release(state);

    return 0;
}

static PyObject *t_db_associate(t_db *self, PyObject *args)
{
    PyObject *secondaryDB, *txn = Py_None, *callback = Py_None;
    int flags = 0;

    if (!self->db)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "O|OOi", &secondaryDB, &txn, &callback, &flags))
        return NULL;

    if (callback != Py_None && !PyCallable_Check(callback))
    {
        PyErr_SetObject(PyExc_TypeError, callback);
        return NULL;
    }

    if (!PyObject_TypeCheck(secondaryDB, &DBType))
    {
        PyErr_SetObject(PyExc_TypeError, callback);
        return NULL;
    }

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        t_db *secondary_db = (t_db *) secondaryDB;
        int err;

        if (callback != Py_None)
        {
            Py_INCREF(callback); Py_XDECREF(secondary_db->associate_cb);
            secondary_db->associate_cb = callback;

            Py_BEGIN_ALLOW_THREADS;
            err = self->db->associate(self->db, db_txn, secondary_db->db,
                                      _t_db_associate_callback, flags);
            Py_END_ALLOW_THREADS;
            if (err)
            {
                Py_XDECREF(secondary_db->associate_cb);
                secondary_db->associate_cb = NULL;

                return raiseDBError(err);
            }
        }
        else
        {
            Py_BEGIN_ALLOW_THREADS;
            err = self->db->associate(self->db, db_txn, secondary_db->db,
                                      NULL, flags);
            Py_END_ALLOW_THREADS;
            if (err)
                return raiseDBError(err);
        }

        Py_RETURN_NONE;
    }
}

static PyObject *t_db_compact(t_db *self, PyObject *args)
{
    PyObject *txn = Py_None;
    int flags = DB_FREE_SPACE;

    if (!PyArg_ParseTuple(args, "|Oi", &txn, &flags))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->db->compact(self->db, db_txn,
                                NULL, NULL, NULL, flags, NULL);
        Py_END_ALLOW_THREADS;
        if (err)
            return raiseDBError(err);

        Py_RETURN_NONE;
    }
}

int _t_db_get(DBT *dbt, void *data, int len, int offset)
{
    PyGILState_STATE state = PyGILState_Ensure();

    if (offset == 0)
    {
        if (len == dbt->size)
        {
            dbt->data = PyString_FromStringAndSize((char *) data, len);
            if (!dbt->data)
            {
                PyGILState_Release(state);
                return DB_PYTHON_ERROR;
            }
        }
        else
        {
            dbt->data = PyString_FromStringAndSize(NULL, dbt->size);
            if (!dbt->data)
            {
                PyGILState_Release(state);
                return DB_PYTHON_ERROR;
            }

            memcpy(PyString_AS_STRING(dbt->data), data, len);
        }
    }   
    else
        memcpy(PyString_AS_STRING(dbt->data) + offset, data, len);

    PyGILState_Release(state);
    return 0;
}

static PyObject *t_db_get(t_db *self, PyObject *args)
{
    DBT key;
    PyObject *txn = Py_None, *defaultValue = NULL;
    int flags = 0;

    memset(&key, 0, sizeof(key));

    if (!PyArg_ParseTuple(args, "s#|OiO",
                          &key.data, &key.size, &txn, &flags, &defaultValue))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        DBT data;
        int err;

        memset(&data, 0, sizeof(data));
        data.flags = DB_DBT_USERCOPY;
        data.data = _t_db_get;

        Py_BEGIN_ALLOW_THREADS;
        err = self->db->get(self->db, db_txn, &key, &data, flags);
        Py_END_ALLOW_THREADS;

        switch (err) {
          case 0:
            return (PyObject *) data.data;
          case DB_NOTFOUND:
            if (defaultValue)
            {
                Py_INCREF(defaultValue);
                return defaultValue;
            }
          default:
            return raiseDBError(err);
        }
    }
}

static PyObject *t_db_put(t_db *self, PyObject *args)
{
    DBT key, data;
    PyObject *txn = Py_None;
    int flags = 0;

    memset(&key, 0, sizeof(key));
    memset(&data, 0, sizeof(data));

    if (!PyArg_ParseTuple(args, "s#s#|Oi",
                          &key.data, &key.size, &data.data, &data.size,
                          &txn, &flags))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->db->put(self->db, db_txn, &key, &data, flags);
        Py_END_ALLOW_THREADS;
        
        if (err)
            return raiseDBError(err);

        Py_RETURN_NONE;
    }
}

static PyObject *t_db_delete(t_db *self, PyObject *args)
{
    DBT key;
    PyObject *txn = Py_None;
    int flags = 0;

    memset(&key, 0, sizeof(key));

    if (!PyArg_ParseTuple(args, "s#|Oi", &key.data, &key.size, &txn, &flags))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->db->del(self->db, db_txn, &key, flags);
        Py_END_ALLOW_THREADS;
                               
        if (err)
            return raiseDBError(err);

        Py_RETURN_NONE;
    }
}

static PyObject *t_db_cursor(t_db *self, PyObject *args)
{
    PyObject *txn = Py_None;
    int flags = 0;

    if (!PyArg_ParseTuple(args, "|Oi", &txn, &flags))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        PyObject *cursor = t_cursor_new(CDBCursor, NULL, NULL);

        if (_t_cursor_init((t_cursor *) cursor, self->db,
                           txn == Py_None ? NULL : ((t_txn *) txn)->txn,
                           flags) < 0)
        {
            Py_DECREF(cursor);
            return NULL;
        }

        return cursor;
    }
}


/* lorder */

static PyObject *t_db_get_lorder(t_db *self, void *data)
{
    int lorder, err;

    if (self->db)
    {
        Py_BEGIN_ALLOW_THREADS;
        err = self->db->get_lorder(self->db, &lorder);
        Py_END_ALLOW_THREADS;
    }
    else
        err = EINVAL;

    if (err)
        return raiseDBError(err);

    return PyInt_FromLong(lorder);
}

static int t_db_set_lorder(t_db *self, PyObject *value, void *data)
{
    int lorder = PyInt_AsLong(value);
    int err;

    if (PyErr_Occurred())
        return -1;

    if (self->db)
    {
        Py_BEGIN_ALLOW_THREADS;
        err = self->db->set_lorder(self->db, lorder);
        Py_END_ALLOW_THREADS;
    }
    else
        err = EINVAL;

    if (err)
    {
        raiseDBError(err);
        return -1;
    }

    return 0;
}


/* dbtype */

static PyObject *t_db_get_dbtype(t_db *self, void *data)
{
    int dbtype, err;

    if (self->db)
    {
        Py_BEGIN_ALLOW_THREADS;
        err = self->db->get_type(self->db, (DBTYPE *) &dbtype);
        Py_END_ALLOW_THREADS;
    }
    else
        err = EINVAL;

    if (err)
        return raiseDBError(err);

    return PyInt_FromLong(dbtype);
}


void _init_db(PyObject *m)
{
    if (PyType_Ready(&DBType) >= 0)
    {
        if (m)
        {
            PyObject *dict = DBType.tp_dict;

            Py_INCREF(&DBType);
            PyModule_AddObject(m, "DB", (PyObject *) &DBType);

            CDB = &DBType;

            /* flags */
            SET_DB_INT(dict, DB_AUTO_COMMIT);
            SET_DB_INT(dict, DB_CREATE);
            SET_DB_INT(dict, DB_EXCL);
            SET_DB_INT(dict, DB_NOMMAP);
            SET_DB_INT(dict, DB_RDONLY);
            SET_DB_INT(dict, DB_READ_COMMITTED);
            SET_DB_INT(dict, DB_READ_UNCOMMITTED);
            SET_DB_INT(dict, DB_RMW);
            SET_DB_INT(dict, DB_THREAD);
            SET_DB_INT(dict, DB_TRUNCATE);
            SET_DB_INT(dict, DB_IMMUTABLE_KEY);
            SET_DB_INT(dict, DB_FREE_SPACE);
            SET_DB_INT(dict, DB_APPEND);
            SET_DB_INT(dict, DB_NODUPDATA);
            SET_DB_INT(dict, DB_NOOVERWRITE);
            SET_DB_INT(dict, DB_CONSUME);
            SET_DB_INT(dict, DB_CONSUME_WAIT);
            SET_DB_INT(dict, DB_GET_BOTH);
            SET_DB_INT(dict, DB_SET_RECNO);
            SET_DB_INT(dict, DB_ENCRYPT);

            /* db types */
            SET_DB_INT(dict, DB_BTREE);
            SET_DB_INT(dict, DB_HASH);
            SET_DB_INT(dict, DB_QUEUE);
            SET_DB_INT(dict, DB_RECNO);
            SET_DB_INT(dict, DB_UNKNOWN);
        }
    }
}
