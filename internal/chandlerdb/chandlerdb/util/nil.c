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
} t_nil;


static PyObject *t_nil_get(t_nil *self, PyObject *args);
static PyObject *t_nil_iternext(t_nil *self);
static int t_nil_length(t_nil *self);
static PyObject *t_nil_dict_get(t_nil *self, PyObject *key);


static PyMethodDef t_nil_methods[] = {
    { "get", (PyCFunction) t_nil_get, METH_VARARGS, NULL },
    { "iteritems", (PyCFunction) PyObject_SelfIter, METH_NOARGS, NULL },
    { "iterkeys", (PyCFunction) PyObject_SelfIter, METH_NOARGS, NULL },
    { "itervalues", (PyCFunction) PyObject_SelfIter, METH_NOARGS, NULL },
    { NULL, NULL, 0, NULL }
};


static PySequenceMethods nil_as_sequence = {
    (inquiry) t_nil_length,             /* sq_length */
    0,                                  /* sq_concat */
    0,					/* sq_repeat */
    0,                                  /* sq_item */
    0,                                  /* sq_slice */
    0,                                  /* sq_ass_item */
    0,                                  /* sq_ass_slice */
    0,                                  /* sq_contains */
};

static PyMappingMethods nil_as_mapping = {
    (inquiry) t_nil_length,             /* mp_length */
    (binaryfunc) t_nil_dict_get,        /* mp_subscript */
    (objobjargproc) 0,                  /* mp_ass_subscript */
};


static PyTypeObject NilType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.util.c.Nil",                   /* tp_name */
    sizeof(t_nil),                             /* tp_basicsize */
    0,                                         /* tp_itemsize */
    0,                                         /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    0,                                         /* tp_repr */
    0,                                         /* tp_as_number */
    &nil_as_sequence,                          /* tp_as_sequence */
    &nil_as_mapping,                           /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    0,                                         /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                        /* tp_flags */
    "Nil type",                                /* tp_doc */
    0,                                         /* tp_traverse */
    0,                                         /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    PyObject_SelfIter,                         /* tp_iter */
    (iternextfunc)t_nil_iternext,              /* tp_iternext */
    t_nil_methods,                             /* tp_methods */
    0,                                         /* tp_members */
    0,                                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    0,                                         /* tp_init */
    0,                                         /* tp_alloc */
    0,                                         /* tp_new */
};


static int t_nil_length(t_nil *self)
{
    return 0;
}

static PyObject *t_nil_dict_get(t_nil *self, PyObject *key)
{
    PyErr_SetObject(PyExc_KeyError, key);
    return NULL;
}

static PyObject *t_nil_get(t_nil *self, PyObject *args)
{
    PyObject *key, *value = Py_None;

    if (!PyArg_ParseTuple(args, "O|O", &key, &value))
        return NULL;

    Py_INCREF(value);
    return value;
}

static PyObject *t_nil_iternext(t_nil *self)
{
    PyErr_SetNone(PyExc_StopIteration);
    return NULL;
}


void _init_nil(PyObject *m)
{
    if (PyType_Ready(&NilType) >= 0)
    {
        if (m)
        {
            Nil = (PyObject *) PyObject_New(t_nil, &NilType);
            Default = (PyObject *) PyObject_New(t_nil, &NilType);

            PyModule_AddObject(m, "Nil", Nil);
            PyModule_AddObject(m, "Default", Default);
        }
    }
}
