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

static void t_cursor_dealloc(t_cursor *self);
static int t_cursor_init(t_cursor *self, PyObject *args, PyObject *kwds);

static PyObject *t_cursor_dup(t_cursor *self, PyObject *args);
static PyObject *t_cursor_close(t_cursor *self, PyObject *args);
static PyObject *t_cursor_delete(t_cursor *self, PyObject *args);
static PyObject *t_cursor_set_range(t_cursor *self, PyObject *args);
static PyObject *t_cursor_first(t_cursor *self, PyObject *args);
static PyObject *t_cursor_last(t_cursor *self, PyObject *args);
static PyObject *t_cursor_prev(t_cursor *self, PyObject *args);
static PyObject *t_cursor_next(t_cursor *self, PyObject *args);
static PyObject *t_cursor_current(t_cursor *self, PyObject *args);

static PyMemberDef t_cursor_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_cursor_methods[] = {
    { "dup", (PyCFunction) t_cursor_dup, METH_VARARGS, NULL },
    { "close", (PyCFunction) t_cursor_close, METH_NOARGS, NULL },
    { "delete", (PyCFunction) t_cursor_delete, METH_VARARGS, NULL },
    { "set_range", (PyCFunction) t_cursor_set_range, METH_VARARGS, NULL },
    { "first", (PyCFunction) t_cursor_first, METH_VARARGS, NULL },
    { "last", (PyCFunction) t_cursor_last, METH_VARARGS, NULL },
    { "prev", (PyCFunction) t_cursor_prev, METH_VARARGS, NULL },
    { "next", (PyCFunction) t_cursor_next, METH_VARARGS, NULL },
    { "current", (PyCFunction) t_cursor_current, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_cursor_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};


static PyTypeObject DBCursorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                               /* ob_size */
    "chandlerdb.persistence.c.DBCursor",             /* tp_name */
    sizeof(t_cursor),                                /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)t_cursor_dealloc,                    /* tp_dealloc */
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
    Py_TPFLAGS_DEFAULT,                              /* tp_flags */
    "C DBCursor type",                               /* tp_doc */
    0,                                               /* tp_traverse */
    0,                                               /* tp_clear */
    0,                                               /* tp_richcompare */
    0,                                               /* tp_weaklistoffset */
    0,                                               /* tp_iter */
    0,                                               /* tp_iternext */
    t_cursor_methods,                                /* tp_methods */
    t_cursor_members,                                /* tp_members */
    t_cursor_properties,                             /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    (initproc)t_cursor_init,                         /* tp_init */
    0,                                               /* tp_alloc */
    (newfunc)t_cursor_new,                           /* tp_new */
};

static void t_cursor_dealloc(t_cursor *self)
{
    self->ob_type->tp_free((PyObject *) self);
}

PyObject *t_cursor_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

int _t_cursor_init(t_cursor *self, DB *db, DB_TXN *txn, int flags)
{
    int err;

    if (db == NULL)
    {
        raiseDBError(EINVAL);
        return -1;
    }

    Py_BEGIN_ALLOW_THREADS;
    err = db->cursor(db, txn, &self->dbc, flags);
    Py_END_ALLOW_THREADS;

    if (err)
    {
        raiseDBError(err);
        return -1;
    }

    return 0;
}

static int t_cursor_init(t_cursor *self, PyObject *args, PyObject *kwds)
{
    PyObject *db, *txn = Py_None;
    int flags = 0;

    if (!PyArg_ParseTuple(args, "O|Oi", &db, &txn, &flags))
        return -1;

    if (!PyObject_TypeCheck(db, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, db);
        return -1;
    }
 
    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return -1;
    }

    return _t_cursor_init(self, ((t_db *) db)->db,
                          txn == Py_None ? NULL : ((t_txn *) txn)->txn,
                          flags);
}

static PyObject *t_cursor_dup(t_cursor *self, PyObject *args)
{
    int flags = 0;

    if (self->dbc == NULL)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "|i", &flags))
        return NULL;
    else
    {
        t_cursor *cursor = (t_cursor *) t_cursor_new(&DBCursorType, NULL, NULL);
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->dbc->c_dup(self->dbc, &cursor->dbc, flags);
        Py_END_ALLOW_THREADS;

        if (err)
        {
            Py_DECREF(cursor);
            return raiseDBError(err);
        }

        return (PyObject *) cursor;
    }
}

static PyObject *t_cursor_close(t_cursor *self, PyObject *args)
{
    if (self->dbc)
    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->dbc->c_close(self->dbc);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        self->dbc = NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *t_cursor_delete(t_cursor *self, PyObject *args)
{
    int flags = 0;

    if (self->dbc == NULL)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "|i", &flags))
        return NULL;
    else
    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->dbc->c_del(self->dbc, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        Py_RETURN_NONE;
    }
}

static PyObject *t_cursor_set_range(t_cursor *self, PyObject *args)
{
    DBT key;
    int flags = 0;
    PyObject *defaultValue = NULL;

    if (self->dbc == NULL)
        return raiseDBError(EINVAL);

    memset(&key, 0, sizeof(key));

    if (!PyArg_ParseTuple(args, "s#|iO", &key.data, &key.size,
                          &flags, &defaultValue))
        return NULL;
    else
    {
        char buffer[256];
        DBT data;
        int err;

        if (key.size > sizeof(buffer) - 32)
            key.flags = DB_DBT_MALLOC;
        else
        {
            memcpy(buffer, key.data, key.size);
            key.data = buffer;
            key.flags = DB_DBT_USERMEM;
            key.ulen = sizeof(buffer);
        }

        memset(&data, 0, sizeof(data));
        data.flags = DB_DBT_USERCOPY;
        data.usercopy = (usercopy_fn) _t_db_get;

        Py_BEGIN_ALLOW_THREADS;
        err = self->dbc->c_get(self->dbc, &key, &data, flags | DB_SET_RANGE);
        Py_END_ALLOW_THREADS;

        switch (err) {
          case 0:
          {
              PyObject *tuple = PyTuple_New(2);
              
              PyTuple_SET_ITEM(tuple, 0, 
                               PyString_FromStringAndSize(key.data, key.size));
              PyTuple_SET_ITEM(tuple, 1, data.app_data);

              if (key.flags == DB_DBT_MALLOC)
                  free(key.data);

              return tuple;
          }
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

static PyObject *_t_cursor_get_pair(t_cursor *self, PyObject *args, int flag)
{
    int flags = 0;
    PyObject *defaultValue = NULL;

    if (!PyArg_ParseTuple(args, "|iO", &flags, &defaultValue))
        return NULL;
    else
    {
        DBT key, data;
        int err;

        memset(&key, 0, sizeof(key));
        key.flags = DB_DBT_USERCOPY;
        key.usercopy = (usercopy_fn) _t_db_get;

        memset(&data, 0, sizeof(data));
        data.flags = DB_DBT_USERCOPY;
        data.usercopy = (usercopy_fn) _t_db_get;

        Py_BEGIN_ALLOW_THREADS;
        err = self->dbc->c_get(self->dbc, &key, &data, flags | flag);
        Py_END_ALLOW_THREADS;

        switch (err) {
          case 0:
          {
              PyObject *tuple = PyTuple_New(2);

              PyTuple_SET_ITEM(tuple, 0, key.app_data);
              PyTuple_SET_ITEM(tuple, 1, data.app_data);

              return tuple;
          }
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

static PyObject *t_cursor_first(t_cursor *self, PyObject *args)
{
    return _t_cursor_get_pair(self, args, DB_FIRST);
}

static PyObject *t_cursor_last(t_cursor *self, PyObject *args)
{
    return _t_cursor_get_pair(self, args, DB_LAST);
}

static PyObject *t_cursor_prev(t_cursor *self, PyObject *args)
{
    return _t_cursor_get_pair(self, args, DB_PREV);
}

static PyObject *t_cursor_next(t_cursor *self, PyObject *args)
{
    return _t_cursor_get_pair(self, args, DB_NEXT);
}

static PyObject *t_cursor_current(t_cursor *self, PyObject *args)
{
    return _t_cursor_get_pair(self, args, DB_CURRENT);
}


void _init_cursor(PyObject *m)
{
    if (PyType_Ready(&DBCursorType) >= 0)
    {
        if (m)
        {
            PyObject *dict = DBCursorType.tp_dict;

            Py_INCREF(&DBCursorType);
            PyModule_AddObject(m, "DBCursor", (PyObject *) &DBCursorType);

            CDBCursor = &DBCursorType;

            SET_DB_INT(dict, DB_MULTIPLE);
            SET_DB_INT(dict, DB_WRITECURSOR);
            SET_DB_INT(dict, DB_POSITION);
        }
    }
}
