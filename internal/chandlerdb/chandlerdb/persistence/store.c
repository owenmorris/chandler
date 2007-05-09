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


#include <Python.h>
#include "structmember.h"

#include "c.h"

static PyObject *start_NAME;
static PyObject *abort_NAME;
static PyObject *commit_NAME;
static PyObject *txn_NAME;

static PyObject *t_transaction_new(PyTypeObject *type,
                                   PyObject *args, PyObject *kwds);
static void t_transaction_dealloc(t_transaction *self);
static int t_transaction_init(t_transaction *self,
                              PyObject *args, PyObject *kwds);

static PyObject *t_transaction_abort(t_transaction *self);
static PyObject *t_transaction_commit(t_transaction *self);
static PyObject *t_transaction__getTxn(t_transaction *self, void *data);

static PyMemberDef t_transaction_members[] = {
    { "_status", T_UINT, offsetof(t_transaction, status), 0, "" },
    { "_count", T_UINT, offsetof(t_transaction, count), 0, "" },
    { "_mvcc", T_UINT, offsetof(t_transaction, mvcc), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_transaction_methods[] = {
    { "abort", (PyCFunction) t_transaction_abort, METH_NOARGS, NULL },
    { "commit", (PyCFunction) t_transaction_commit, METH_NOARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_transaction_properties[] = {
    { "_txn", (getter) t_transaction__getTxn, 0, NULL, NULL },
    { NULL, NULL, NULL, NULL, NULL }
};


static PyTypeObject TransactionType = {
    PyObject_HEAD_INIT(NULL)
    0,                                               /* ob_size */
    "chandlerdb.persistence.c.Transaction",          /* tp_name */
    sizeof(t_transaction),                           /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)t_transaction_dealloc,               /* tp_dealloc */
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
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE),                           /* tp_flags */
    "C Transaction type",                            /* tp_doc */
    0,                                               /* tp_traverse */
    0,                                               /* tp_clear */
    0,                                               /* tp_richcompare */
    0,                                               /* tp_weaklistoffset */
    0,                                               /* tp_iter */
    0,                                               /* tp_iternext */
    t_transaction_methods,                           /* tp_methods */
    t_transaction_members,                           /* tp_members */
    t_transaction_properties,                        /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    (initproc)t_transaction_init,                    /* tp_init */
    0,                                               /* tp_alloc */
    (newfunc)t_transaction_new,                      /* tp_new */
};


static void t_transaction_dealloc(t_transaction *self)
{
    Py_XDECREF(self->txn);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_transaction_new(PyTypeObject *type,
                                   PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

static int t_transaction_init(t_transaction *self,
                              PyObject *args, PyObject *kwds)
{
    PyObject *store, *txn, *mvcc;
    int status;

    if (!PyArg_ParseTuple(args, "OOiO", &store, &txn, &status, &mvcc))
        return -1;

    txn = PyObject_CallMethodObjArgs((PyObject *) self, start_NAME,
                                     store, txn, mvcc, NULL);
    if (txn)
    {
        self->txn = txn;
        self->status = status;
        self->count = 1;

        return 0;
    }

    return -1;
}

static PyObject *_t_transaction_op(t_transaction *self, PyObject *op)
{
    if (self->count)
    {
        if (--self->count == 0)
        {
            if (self->txn != Py_None)
            {
                PyObject *result = PyObject_CallMethodObjArgs(self->txn, op,
                                                              NULL);
                if (result)
                {
                    Py_DECREF(result);
                    Py_INCREF(Py_None);
                    Py_DECREF(self->txn);
                    self->txn = Py_None;
                }
            }

            Py_RETURN_TRUE;
        }

        Py_RETURN_FALSE;
    }

    PyErr_SetString(PyExc_AssertionError, "count is already zero");
    return NULL;
}

static PyObject *t_transaction_abort(t_transaction *self)
{
    return _t_transaction_op(self, abort_NAME);
}

static PyObject *t_transaction_commit(t_transaction *self)
{
    return _t_transaction_op(self, commit_NAME);
}


/* _txn */

static PyObject *t_transaction__getTxn(t_transaction *self, void *data)
{
    Py_INCREF(self->txn);
    return self->txn;
}


static int t_store_traverse(t_store *self, visitproc visit, void *arg);
static int t_store_clear(t_store *self);
static PyObject *t_store_new(PyTypeObject *type,
                             PyObject *args, PyObject *kwds);
static void t_store_dealloc(t_store *self);
static int t_store_init(t_store *self,
                        PyObject *args, PyObject *kwds);

static PyObject *t_store_getRepository(t_store *self, void *data);
static PyObject *t_store_getTxn(t_store *self, void *data);
static PyObject *t_store__getThreaded(t_store *self, void *data);

static PyMemberDef t_store_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_store_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_store_properties[] = {
    { "repository", (getter) t_store_getRepository, 0, NULL, NULL },
    { "txn", (getter) t_store_getTxn, 0, NULL, NULL },
    { "_threaded", (getter) t_store__getThreaded, 0, NULL, NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject StoreType = {
    PyObject_HEAD_INIT(NULL)
    0,                                               /* ob_size */
    "chandlerdb.persistence.c.CStore",               /* tp_name */
    sizeof(t_store),                                 /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)t_store_dealloc,                     /* tp_dealloc */
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
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                            /* tp_flags */
    "C Store type",                                  /* tp_doc */
    (traverseproc)t_store_traverse,                  /* tp_traverse */
    (inquiry)t_store_clear,                          /* tp_clear */
    0,                                               /* tp_richcompare */
    0,                                               /* tp_weaklistoffset */
    0,                                               /* tp_iter */
    0,                                               /* tp_iternext */
    t_store_methods,                                 /* tp_methods */
    t_store_members,                                 /* tp_members */
    t_store_properties,                              /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    (initproc)t_store_init,                          /* tp_init */
    0,                                               /* tp_alloc */
    (newfunc)t_store_new,                            /* tp_new */
};


static int t_store_traverse(t_store *self, visitproc visit, void *arg)
{
    Py_VISIT(self->repository);
    Py_VISIT(self->key);

    return 0;
}

static int t_store_clear(t_store *self)
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

    Py_CLEAR(self->repository);
    Py_CLEAR(self->key);

    return 0;
}

static void t_store_dealloc(t_store *self)
{
    t_store_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_store_new(PyTypeObject *type,
                             PyObject *args, PyObject *kwds)
{
    t_store *self = (t_store *) type->tp_alloc(type, 0);

    if (self)
        self->key = PyInt_FromLong(_Py_HashPointer(self));

    return (PyObject *) self;
}

static int t_store_init(t_store *self, PyObject *args, PyObject *kwds)
{
    PyObject *repository;

    if (!PyArg_ParseTuple(args, "O", &repository))
        return -1;

    if (!PyObject_TypeCheck(repository, CRepository))
    {
        PyErr_SetObject(PyExc_TypeError, repository);
        return -1;
    }

    Py_INCREF(repository); Py_XDECREF(self->repository);
    self->repository = repository;

    return 0;
}


/* repository */

static PyObject *t_store_getRepository(t_store *self, void *data)
{
    if (self->repository)
    {
        Py_INCREF(self->repository);
        return self->repository;
    }

    PyErr_SetString(PyExc_AttributeError, "store has no repository");
    return NULL;
}


/* _threaded */

static PyObject *_t_store__getThreaded(t_store *self)
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

static PyObject *t_store__getThreaded(t_store *self, void *data)
{
    PyObject *threaded = _t_store__getThreaded(self);

    if (threaded)
        Py_INCREF(threaded);

    return threaded;
}


/* txn */

PyObject *_t_store_getTxn(t_store *self)
{
    PyObject *threaded = _t_store__getThreaded(self);

    if (threaded)
    {
        PyObject *txn = PyDict_GetItem(threaded, txn_NAME);

        if (txn && txn != Py_None)
        {
            if (!PyObject_TypeCheck(txn, &TransactionType))
            {
                PyErr_SetObject(PyExc_TypeError, txn);
                return NULL;
            }

            return ((t_transaction *) txn)->txn;
        }

        return Py_None;
    }

    return NULL;
}

static PyObject *t_store_getTxn(t_store *self, void *data)
{
    PyObject *result = _t_store_getTxn(self);

    if (!result)
        return NULL;

    Py_INCREF(result);
    return result;
}


void _init_store(PyObject *m)
{
    if (PyType_Ready(&TransactionType) >= 0 &&
        PyType_Ready(&StoreType) >= 0)
    {
        if (m)
        {
            PyObject *dict;

            Py_INCREF(&TransactionType);
            PyModule_AddObject(m, "Transaction", (PyObject *) &TransactionType);

            Py_INCREF(&StoreType);
            PyModule_AddObject(m, "CStore", (PyObject *) &StoreType);
            CStore = &StoreType;

            dict = TransactionType.tp_dict;
            PyDict_SetItemString_Int(dict, "TXN_STARTED", TXN_STARTED);
            PyDict_SetItemString_Int(dict, "TXN_NESTED", TXN_NESTED);

            dict = StoreType.tp_dict;
            PyDict_SetItemString_Int(dict, "TXN_STARTED", TXN_STARTED);
            PyDict_SetItemString_Int(dict, "TXN_NESTED", TXN_NESTED);

            start_NAME = PyString_FromString("start");
            abort_NAME = PyString_FromString("abort");
            commit_NAME = PyString_FromString("commit");
            txn_NAME = PyString_FromString("txn");
        }
    }
}
