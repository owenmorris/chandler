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

static void t_txn_dealloc(t_txn *self);
static int t_txn_init(t_txn *self, PyObject *args, PyObject *kwds);

static PyObject *t_txn_abort(t_txn *self, PyObject *args);
static PyObject *t_txn_commit(t_txn *self, PyObject *args);
static PyObject *t_txn_discard(t_txn *self, PyObject *args);
static PyObject *t_txn_set_timeout(t_txn *self, PyObject *args);

static PyObject *t_txn_get_name(t_txn *self, void *data);
static int t_txn_set_name(t_txn *self, PyObject *value, void *data);
static PyObject *t_txn_get_id(t_txn *self, void *data);


static PyMemberDef t_txn_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_txn_methods[] = {
    { "abort", (PyCFunction) t_txn_abort, METH_NOARGS, NULL },
    { "commit", (PyCFunction) t_txn_commit, METH_VARARGS, NULL },
    { "discard", (PyCFunction) t_txn_discard, METH_VARARGS, NULL },
    { "set_timeout", (PyCFunction) t_txn_set_timeout, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_txn_properties[] = {
    { "name", (getter) t_txn_get_name, (setter) t_txn_set_name,
      "transaction name", NULL },
    { "id", (getter) t_txn_get_id, (setter) NULL,
      "transaction id", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject DBTxnType = {
    PyObject_HEAD_INIT(NULL)
    0,                                               /* ob_size */
    "chandlerdb.persistence.c.DBTxn",                /* tp_name */
    sizeof(t_txn),                                   /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)t_txn_dealloc,                       /* tp_dealloc */
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
    "C DBTxn type",                                  /* tp_doc */
    0,                                               /* tp_traverse */
    0,                                               /* tp_clear */
    0,                                               /* tp_richcompare */
    0,                                               /* tp_weaklistoffset */
    0,                                               /* tp_iter */
    0,                                               /* tp_iternext */
    t_txn_methods,                                   /* tp_methods */
    t_txn_members,                                   /* tp_members */
    t_txn_properties,                                /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    (initproc)t_txn_init,                            /* tp_init */
    0,                                               /* tp_alloc */
    (newfunc)t_txn_new,                              /* tp_new */
};


static void t_txn_dealloc(t_txn *self)
{
    self->ob_type->tp_free((PyObject *) self);
}

PyObject *t_txn_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

int _t_txn_init(t_txn *self, DB_ENV *db_env, DB_TXN *parent, int flags)
{
    int err;

    Py_BEGIN_ALLOW_THREADS;
    err = db_env->txn_begin(db_env, parent, &self->txn, flags);
    Py_END_ALLOW_THREADS;

    if (err)
    {
        raiseDBError(err);
        return -1;
    }

    return 0;
}

static int t_txn_init(t_txn *self, PyObject *args, PyObject *kwds)
{
    PyObject *env, *parent = Py_None;
    int flags = 0;

    if (!PyArg_ParseTuple(args, "O|Oi", &env, &parent, &flags))
        return -1;

    if (!PyObject_TypeCheck(env, CDBEnv))
    {
        PyErr_SetObject(PyExc_TypeError, env);
        return -1;
    }

    if (parent != Py_None && !PyObject_TypeCheck(parent, CDBTxn))
    {
        PyErr_SetObject(PyExc_TypeError, parent);
        return -1;
    }

    return _t_txn_init(self, ((t_env *) env)->db_env,
                       parent == Py_None ? NULL : ((t_txn *) parent)->txn,
                       flags);
}

static PyObject *t_txn_abort(t_txn *self, PyObject *args)
{
    if (!self->txn)
        return raiseDBError(EINVAL);

    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->txn->abort(self->txn);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        self->txn = NULL;

        Py_RETURN_NONE;
    }
}

static PyObject *t_txn_commit(t_txn *self, PyObject *args)
{
    int flags = 0;

    if (!self->txn)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "|i", &flags))
        return NULL;

    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->txn->commit(self->txn, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        self->txn = NULL;

        Py_RETURN_NONE;
    }
}

static PyObject *t_txn_discard(t_txn *self, PyObject *args)
{
    int flags = 0;

    if (!self->txn)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "|i", &flags))
        return NULL;

    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->txn->discard(self->txn, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        self->txn = NULL;

        Py_RETURN_NONE;
    }
}

static PyObject *t_txn_set_timeout(t_txn *self, PyObject *args)
{
    db_timeout_t timeout;
    int flags;

    if (!self->txn)
        return raiseDBError(EINVAL);

    if (!PyArg_ParseTuple(args, "ii", &timeout, &flags))
        return NULL;

    {
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = self->txn->set_timeout(self->txn, timeout, flags);
        Py_END_ALLOW_THREADS;

        if (err)
            return raiseDBError(err);

        Py_RETURN_NONE;
    }
}


/* name */

static PyObject *t_txn_get_name(t_txn *self, void *data)
{
    const char *name;
    int err;

    if (self->txn)
    {
        Py_BEGIN_ALLOW_THREADS;
        err = self->txn->get_name(self->txn, &name);
        Py_END_ALLOW_THREADS;
    }
    else
        err = EINVAL;

    if (err)
        return raiseDBError(err);

    return PyString_FromString(name);
}

static int t_txn_set_name(t_txn *self, PyObject *value, void *data)
{
    char *name = PyString_AsString(value);
    int err;

    if (PyErr_Occurred())
        return -1;

    if (self->txn)
    {
        Py_BEGIN_ALLOW_THREADS;
        err = self->txn->set_name(self->txn, name);
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


/* id */

static PyObject *t_txn_get_id(t_txn *self, void *data)
{
    if (self->txn)
    {
        int id;

        Py_BEGIN_ALLOW_THREADS;
        id = self->txn->id(self->txn);
        Py_END_ALLOW_THREADS;

        return PyInt_FromLong(id);
    }

    return raiseDBError(EINVAL);
}


void _init_txn(PyObject *m)
{
    if (PyType_Ready(&DBTxnType) >= 0)
    {
        if (m)
        {
            PyObject *dict = DBTxnType.tp_dict;

            Py_INCREF(&DBTxnType);
            PyModule_AddObject(m, "DBTxn", (PyObject *) &DBTxnType);

            CDBTxn = &DBTxnType;

            /* flags */
            SET_DB_INT(dict, DB_READ_COMMITTED);
            SET_DB_INT(dict, DB_READ_UNCOMMITTED);
            SET_DB_INT(dict, DB_TXN_NOSYNC);
            SET_DB_INT(dict, DB_TXN_NOWAIT);
            SET_DB_INT(dict, DB_TXN_SYNC);
        }
    }
}
