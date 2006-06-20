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

static int t_hashtuple_contains(PyObject *self, PyObject *arg);


static PySequenceMethods hashtuple_as_sequence = {
    0,                                   /* sq_length */
    0,                                   /* sq_concat */
    0,                                   /* sq_repeat */
    0,                                   /* sq_item */
    0,                                   /* sq_slice */
    0,                                   /* sq_ass_item */
    0,                                   /* sq_ass_slice */
    (objobjproc) t_hashtuple_contains,   /* sq_contains */
};

static PyTypeObject HashTupleType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.util.c.HashTuple",    /* tp_name */
    0,                                /* tp_basicsize */
    0,                                /* tp_itemsize */
    0,                                /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    0,                                /* tp_compare */
    0,                                /* tp_repr */
    0,                                /* tp_as_number */
    &hashtuple_as_sequence,           /* tp_as_sequence */
    0,                                /* tp_as_mapping */
    0,                                /* tp_hash  */
    0,                                /* tp_call */
    0,                                /* tp_str */
    0,                                /* tp_getattro */
    0,                                /* tp_setattro */
    0,                                /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,               /* tp_flags */
    "tuple of string hashes",         /* tp_doc */
    0,                                /* tp_traverse */
    0,                                /* tp_clear */
    0,                                /* tp_richcompare */
    0,                                /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    0,                                /* tp_methods */
    0,                                /* tp_members */
    0,                                /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    0,                                /* tp_init */
    0,                                /* tp_alloc */
    0,                                /* tp_new */
};


/* as_sequence */

static int t_hashtuple_contains(PyObject *self, PyObject *arg)
{
    PyObject *string = NULL;
    char *data;
    int len, hash, i;

    if (PyString_Check(arg))
    {
        data = PyString_AS_STRING(arg);
        len = PyString_GET_SIZE(arg);
    }
    else if (PyUnicode_Check(arg))
    {
        string = PyUnicode_AsUTF8String(arg);
        if (!string)
            return -1;

        data = PyString_AS_STRING(string);
        len = PyString_GET_SIZE(string);
    }
    else
        return 0;

    hash = hash_bytes((unsigned char *) data, len);
    Py_XDECREF(string);

    for (i = 0; i < PyTuple_GET_SIZE(self); ++i) {
        if (hash == PyInt_AS_LONG(PyTuple_GET_ITEM(self, i)))
            return 1;
    }

    return 0;
}


void _init_hashtuple(PyObject *m)
{
    HashTupleType.tp_base = &PyTuple_Type;

    if (PyType_Ready(&HashTupleType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&HashTupleType);
            PyModule_AddObject(m, "HashTuple", (PyObject *) &HashTupleType);
        }
    }
}
