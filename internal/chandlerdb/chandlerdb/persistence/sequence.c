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

typedef struct {
    PyObject_HEAD
    DB_SEQUENCE *seq;
} t_sequence;


static void t_sequence_dealloc(t_sequence *self);
static PyObject *t_sequence_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds);
static int t_sequence_init(t_sequence *self, PyObject *args, PyObject *kwds);
static PyObject *t_sequence_close(t_sequence *self, PyObject *args);
static PyObject *t_sequence_remove(t_sequence *self, PyObject *args);
static PyObject *t_sequence_open(t_sequence *self, PyObject *args);
static PyObject *t_sequence_get(t_sequence *self, PyObject *args);
static PyObject *t_sequence_stat(t_sequence *self, PyObject *args);

static PyObject *t_sequence__get_cachesize(t_sequence *self, void *data);
static int t_sequence__set_cachesize(t_sequence *self, PyObject *value,
                                     void *data);
static PyObject *t_sequence__get_range(t_sequence *self, void *data);
static int t_sequence__set_range(t_sequence *self, PyObject *value,
                                 void *data);
static PyObject *t_sequence__get_flags(t_sequence *self, void *data);
static int t_sequence__set_flags(t_sequence *self, PyObject *value,
                                 void *data);
static PyObject *t_sequence__get_key(t_sequence *self, void *data);
static PyObject *t_sequence__get_last_value(t_sequence *self, void *data);
static int t_sequence__set_initial_value(t_sequence *self, PyObject *value,
                                         void *data);

static PyMemberDef t_sequence_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_sequence_methods[] = {
    { "close", (PyCFunction) t_sequence_close, METH_NOARGS, "" },
    { "remove", (PyCFunction) t_sequence_remove, METH_VARARGS, "" },
    { "open", (PyCFunction) t_sequence_open, METH_VARARGS, "" },
    { "get", (PyCFunction) t_sequence_get, METH_VARARGS, "" },
    { "stat", (PyCFunction) t_sequence_stat, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_sequence_properties[] = {
    { "cachesize",
      (getter) t_sequence__get_cachesize, (setter) t_sequence__set_cachesize,
      "sequence cachesize", NULL },
    { "range",
      (getter) t_sequence__get_range, (setter) t_sequence__set_range,
      "sequence range", NULL },
    { "flags",
      (getter) t_sequence__get_flags, (setter) t_sequence__set_flags,
      "sequence flags", NULL },
    { "key",
      (getter) t_sequence__get_key, (setter) NULL,
      "sequence key", NULL },
    { "last_value",
      (getter) t_sequence__get_last_value, (setter) NULL,
      "sequence current value in database", NULL },
    { "initial_value",
      (getter) NULL, (setter) t_sequence__set_initial_value,
      "sequence initial value", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};


static PyTypeObject SequenceType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.DBSequence",               /* tp_name */
    sizeof(t_sequence),                                  /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_sequence_dealloc,                      /* tp_dealloc */
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
    Py_TPFLAGS_DEFAULT,                                  /* tp_flags */
    "Berkeley DB DB_SEQUENCE type",                      /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_sequence_methods,                                  /* tp_methods */
    t_sequence_members,                                  /* tp_members */
    t_sequence_properties,                               /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_sequence_init,                           /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_sequence_new,                             /* tp_new */
};

static void _t_sequence_close(t_sequence *self)
{
    if (self->seq != NULL)
    {
        Py_BEGIN_ALLOW_THREADS;
        self->seq->close(self->seq, 0);
        Py_END_ALLOW_THREADS;

        self->seq = NULL;
    }
}

static void t_sequence_dealloc(t_sequence *self)
{
    _t_sequence_close(self);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_sequence_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds)
{
    t_sequence *self = (t_sequence *) type->tp_alloc(type, 0);

    self->seq = NULL;
    return (PyObject *) self;
}

static int t_sequence_init(t_sequence *self, PyObject *args, PyObject *kwds)
{
    PyObject *db;
    int flags = 0;

    if (!PyArg_ParseTuple(args, "O|i", &db, &flags))
        return -1;

    if (!PyObject_TypeCheck(db, CDB))
    {
        PyErr_SetObject(PyExc_TypeError, db);
        return -1;
    }

    {
        DB_SEQUENCE *seq;
        int err;

        _t_sequence_close(self);

        Py_BEGIN_ALLOW_THREADS;
        err = db_sequence_create(&seq, ((t_db *) db)->db, flags);
        Py_END_ALLOW_THREADS;

        if (err)
        {
            raiseDBError(err);
            return -1;
        }

        self->seq = seq;

        return 0;
    }
}

static PyObject *t_sequence_close(t_sequence *self, PyObject *args)
{
    _t_sequence_close(self);
    Py_RETURN_NONE;
}

static PyObject *t_sequence_remove(t_sequence *self, PyObject *args)
{
    PyObject *txn;
    int flags = 0;

    if (!self->seq)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "O|i", &txn, &flags))
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
        err = self->seq->remove(self->seq, db_txn, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        self->seq = NULL;

        Py_RETURN_NONE;
    }
}

static PyObject *t_sequence_open(t_sequence *self, PyObject *args)
{
    PyObject *txn;
    int flags = 0;
    DBT key;

    if (!self->seq)
        return raiseDBError(EINVAL);

    memset(&key, 0, sizeof(key));

    if (!PyArg_ParseTuple(args, "Os#|i", &txn, &key.data, &key.size, &flags))
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
        err = self->seq->open(self->seq, db_txn, &key, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        Py_RETURN_NONE;
    }
}

static PyObject *t_sequence_get(t_sequence *self, PyObject *args)
{
    PyObject *txn = Py_None;
    int delta = 1;
    int flags = 0;
    
    if (!self->seq)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "|Oii", &txn, &delta, &flags))
        return NULL;

    if (txn != Py_None && !PyObject_TypeCheck(txn, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, txn);
        return NULL;
    }

    {
        DB_TXN *db_txn = txn == Py_None ? NULL : ((t_txn *) txn)->txn;
        db_seq_t value;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->get(self->seq, db_txn, delta, &value, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        return PyLong_FromLongLong(value);
    }
}

static int _t_sequence_stat(t_sequence *self, DB_SEQUENCE_STAT *stats,
                            int flags)
{
    void *ptr;
    int err;

    if (!self->seq)
    {
        raiseDBError(EINVAL);
        return -1;
    }

    Py_BEGIN_ALLOW_THREADS;
    err = self->seq->stat(self->seq, (void *) &ptr, flags);
    Py_END_ALLOW_THREADS;

    if (err)
        return err;

    *stats = *(DB_SEQUENCE_STAT *) ptr;
    free(ptr);

    return 0;
}

static PyObject *t_sequence_stat(t_sequence *self, PyObject *args)
{
    int flags = 0;
    
    if (!PyArg_ParseTuple(args, "|i", &flags))
        return NULL;

    {
        DB_SEQUENCE_STAT stats;
        int err = _t_sequence_stat(self, &stats, flags);

        if (err)
            return raiseDBError(err);

        return Py_BuildValue("(iiLLLLLii)",
                             stats.st_wait, stats.st_nowait,
                             stats.st_current, stats.st_value,
                             stats.st_last_value,
                             stats.st_min, stats.st_max, stats.st_cache_size,
                             stats.st_flags);
    }
}


/* cachesize */

static PyObject *t_sequence__get_cachesize(t_sequence *self, void *data)
{
    if (!self->seq)
        return raiseDBError(EINVAL);

    {
        int32_t size;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->get_cachesize(self->seq, &size);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        return PyInt_FromLong(size);
    }
}

static int t_sequence__set_cachesize(t_sequence *self, PyObject *value,
                                     void *data)
{
    if (!self->seq)
    {
        raiseDBError(EINVAL);
        return -1;
    }

    if (value && !PyInt_CheckExact(value))
    {
        PyErr_SetObject(PyExc_TypeError, value);
        return -1;
    }

    {
        int32_t size = value ? PyInt_AS_LONG(value) : 0;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->set_cachesize(self->seq, size);
        Py_END_ALLOW_THREADS;
        
        if (err)
        {
            raiseDBError(err);
            return -1;
        }

        return 0;
    }
}


/* range */

static PyObject *t_sequence__get_range(t_sequence *self, void *data)
{
    if (!self->seq)
        return raiseDBError(EINVAL);

    {
        db_seq_t min_r, max_r;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->get_range(self->seq, &min_r, &max_r);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        return Py_BuildValue("(LL)", min_r, max_r);
    }
}

static int t_sequence__set_range(t_sequence *self, PyObject *value,
                                 void *data)
{
    db_seq_t min_r, max_r;
    
    if (!self->seq)
    {
     	raiseDBError(EINVAL);
        return -1;
    }

    if (!PyArg_ParseTuple(value ? value : Py_None, "LL", &min_r, &max_r))
        return -1;

    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->set_range(self->seq, min_r, max_r);
        Py_END_ALLOW_THREADS;
        
        if (err)
        {
            raiseDBError(err);
            return -1;
        }

        return 0;
    }
}


/* flags */

static PyObject *t_sequence__get_flags(t_sequence *self, void *data)
{
    if (!self->seq)
        return raiseDBError(EINVAL);

    {
        u_int32_t flags;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->get_flags(self->seq, &flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        return PyInt_FromLong(flags);
    }
}

static int t_sequence__set_flags(t_sequence *self, PyObject *value,
                                 void *data)
{
    u_int32_t flags = value ? PyInt_AsLong(value) : 0;
    
    if (!self->seq)
    {
        raiseDBError(EINVAL);
        return -1;
    }

    if (PyErr_Occurred())
        return -1;

    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->set_flags(self->seq, flags);
        Py_END_ALLOW_THREADS;
        
        if (err)
        {
            raiseDBError(err);
            return -1;
        }

        return 0;
    }
}


/* key */

static PyObject *t_sequence__get_key(t_sequence *self, void *data)
{
    if (!self->seq)
        return raiseDBError(EINVAL);

    {
        DBT key;
        int err;

        memset(&key, 0, sizeof(key));

        Py_BEGIN_ALLOW_THREADS;
        err = self->seq->get_key(self->seq, &key);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        return PyString_FromStringAndSize(key.data, key.size);
    }
}


/* last_value */

static PyObject *t_sequence__get_last_value(t_sequence *self, void *data)
{
    if (!self->seq)
        return raiseDBError(EINVAL);

    {
        DB_SEQUENCE_STAT stats;
        int err = _t_sequence_stat(self, &stats, 0);

        if (err)
            return raiseDBError(err);

        return PyLong_FromLongLong(stats.st_last_value);
    }
}


/* initial_value */

static int t_sequence__set_initial_value(t_sequence *self, PyObject *value,
                                         void *data)
{
    if (!self->seq)
    {
        raiseDBError(EINVAL);
        return -1;
    }

    {
        db_seq_t initial_value = value ? PyLong_AsLongLong(value) : 0;

        if (PyErr_Occurred())
            return -1;

        {
            int err;

            Py_BEGIN_ALLOW_THREADS;
            err = self->seq->initial_value(self->seq, initial_value);
            Py_END_ALLOW_THREADS;
        
            if (err)
            {
                raiseDBError(err);
                return -1;
            }

            return 0;
        }
    }
}


void _init_sequence(PyObject *m)
{
    if (PyType_Ready(&SequenceType) >= 0)
    {
        if (m)
        {
            PyObject *dict = SequenceType.tp_dict;

            Py_INCREF(&SequenceType);
            PyModule_AddObject(m, "DBSequence", (PyObject *) &SequenceType);

            SET_DB_INT(dict, DB_CREATE);
            SET_DB_INT(dict, DB_THREAD);

            SET_DB_INT(dict, DB_SEQ_DEC);
            SET_DB_INT(dict, DB_SEQ_INC);
            SET_DB_INT(dict, DB_SEQ_WRAP);
        }
    }
}
