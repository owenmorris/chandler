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
    PyObject *index;
} t_delegating_index;


static void t_delegating_index_dealloc(t_delegating_index *self);
static PyObject *t_delegating_index_new(PyTypeObject *type,
                                        PyObject *args, PyObject *kwds);
static int t_delegating_index_init(t_delegating_index *self,
                                   PyObject *args, PyObject *kwds);
static PyObject *t_delegating_index_repr(t_delegating_index *self);
static PyObject *t_delegating_index_getattro(t_delegating_index *self,
                                             PyObject *name);

static int t_delegating_index_dict_length(t_delegating_index *self);
static PyObject *t_delegating_index_dict_get(t_delegating_index *self,
                                             PyObject *key);
static int t_delegating_index_dict_set(t_delegating_index *self,
                                       PyObject *key, PyObject *value);
static int t_delegating_index_contains(t_delegating_index *self, PyObject *key);
static PyObject *t_delegating_index_iter(t_delegating_index *self);

static PyMemberDef t_delegating_index_members[] = {
    { "_index", T_OBJECT, offsetof(t_delegating_index, index), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMappingMethods t_delegating_index_as_mapping = {
    (inquiry) t_delegating_index_dict_length,
    (binaryfunc) t_delegating_index_dict_get,
    (objobjargproc) t_delegating_index_dict_set
};

static PySequenceMethods t_delegating_index_as_sequence = {
    (inquiry) t_delegating_index_dict_length,     /* sq_length */
    0,                                            /* sq_concat */
    0,                                            /* sq_repeat */
    0,                                            /* sq_item */
    0,                                            /* sq_slice */
    0,                                            /* sq_ass_item */
    0,                                            /* sq_ass_slice */
    (objobjproc) t_delegating_index_contains,     /* sq_contains */
    0,                                            /* sq_inplace_concat */
    0,                                            /* sq_inplace_repeat */
};

static PyTypeObject DelegatingIndexType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.DelegatingIndex",       /* tp_name */
    sizeof(t_delegating_index),                /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_delegating_index_dealloc,    /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    (reprfunc)t_delegating_index_repr,         /* tp_repr */
    0,                                         /* tp_as_number */
    &t_delegating_index_as_sequence,           /* tp_as_sequence */
    &t_delegating_index_as_mapping,            /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    0,                                         /* tp_str */
    (getattrofunc)t_delegating_index_getattro, /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE),                     /* tp_flags */
    "C DelegatingIndex type",                  /* tp_doc */
    0,                                         /* tp_traverse */
    0,                                         /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    (getiterfunc)t_delegating_index_iter,      /* tp_iter */
    0,                                         /* tp_iternext */
    0,                                         /* tp_methods */
    t_delegating_index_members,                /* tp_members */
    0,                                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_delegating_index_init,         /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_delegating_index_new,           /* tp_new */
};


static void t_delegating_index_dealloc(t_delegating_index *self)
{
    Py_XDECREF(self->index);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_delegating_index_new(PyTypeObject *type,
                                        PyObject *args, PyObject *kwds)
{
    t_delegating_index *self = (t_delegating_index *) type->tp_alloc(type, 0);

    if (self)
        self->index = NULL;

    return (PyObject *) self;
}

static int t_delegating_index_init(t_delegating_index *self,
                                   PyObject *args, PyObject *kwds)
{
    if (!PyArg_ParseTuple(args, "O", &self->index))
        return -1;

    Py_INCREF(self->index);

    return 0;
}

static PyObject *t_delegating_index_repr(t_delegating_index *self)
{
    PyObject *type = PyObject_GetAttrString((PyObject *) self->ob_type,
                                            "__name__");
    PyObject *repr = PyString_FromFormat("<%s: %d>",
                                         PyString_AsString(type),
                                         t_delegating_index_dict_length(self));

    Py_DECREF(type);

    return repr;
}

static int t_delegating_index_dict_length(t_delegating_index *self)
{
    return PyObject_Size(self->index);
}

static PyObject *t_delegating_index_dict_get(t_delegating_index *self,
                                             PyObject *key)
{
    return PyObject_GetItem(self->index, key);
}

static int t_delegating_index_dict_set(t_delegating_index *self,
                                       PyObject *key, PyObject *value)
{
    return PyObject_SetItem(self->index, key, value);
}

static int t_delegating_index_contains(t_delegating_index *self, PyObject *key)
{
    return PySequence_Contains(self->index, key);
}

static PyObject *t_delegating_index_iter(t_delegating_index *self)
{
    return PyObject_GetIter(self->index);
}

static PyObject *t_delegating_index_getattro(t_delegating_index *self,
                                             PyObject *name)
{
    PyObject *value = PyObject_GenericGetAttr((PyObject *) self, name);

    if (value)
        return value;

    PyErr_Clear();
    return PyObject_GetAttr(self->index, name);
}


void _init_indexes(PyObject *m)
{
    if (PyType_Ready(&DelegatingIndexType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&DelegatingIndexType);
            PyModule_AddObject(m, "DelegatingIndex",
                               (PyObject *) &DelegatingIndexType);
        }
    }
}
