/*
 *  Copyright (c) 2007-2007 Open Source Applications Foundation
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

static PyObject *t_iterator_new(PyTypeObject *self,
                                PyObject *args, PyObject *kwds);
static void t_iterator_dealloc(t_iterator *self);
static int t_iterator_traverse(t_iterator *self, visitproc visit, void *arg);
static int t_iterator_clear(t_iterator *self);

static PyObject *t_iterator_iternext(t_iterator *self);

static PyMemberDef t_iterator_members[] = {
    { "_data", T_OBJECT, offsetof(t_iterator, data), READONLY, "data" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_iterator_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyTypeObject IteratorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.util.c.Iterator",              /* tp_name */
    sizeof(t_iterator),                        /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_iterator_dealloc,            /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    0,                                         /* tp_repr */
    0,                                         /* tp_as_number */
    0,                                         /* tp_as_sequence */
    0,                                         /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    0,                                         /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "Iterator type",                           /* tp_doc */
    (traverseproc)t_iterator_traverse,         /* tp_traverse */
    (inquiry)t_iterator_clear,                 /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    PyObject_SelfIter,                         /* tp_iter */
    (iternextfunc)t_iterator_iternext,         /* tp_iternext */
    t_iterator_methods,                        /* tp_methods */
    t_iterator_members,                        /* tp_members */
    0,                                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    0,                                         /* tp_init */
    0,                                         /* tp_alloc */ 
    (newfunc)t_iterator_new,                   /* tp_new */
};

static PyObject *t_iterator_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds)
{
    t_iterator *self = (t_iterator *) type->tp_alloc(type, 0);

    if (self)
    {
        self->target = NULL;
        self->data = NULL;
    }

    return (PyObject *) self;
}

static void t_iterator_dealloc(t_iterator *self)
{
    t_iterator_clear(self);
    self->ob_type->tp_free((PyObject *) self);    
}

static int t_iterator_traverse(t_iterator *self, visitproc visit, void *arg)
{
    Py_VISIT(self->target);
    Py_VISIT(self->data);

    return 0;
}

static int t_iterator_clear(t_iterator *self)
{
    Py_CLEAR(self->target);
    Py_CLEAR(self->data);

    return 0;
}

static PyObject *t_iterator_iternext(t_iterator *self)
{
    return self->nextFn(self->target, self);
}


void _init_iterator(PyObject *m)
{
    if (PyType_Ready(&IteratorType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&IteratorType);
            PyModule_AddObject(m, "Iterator", (PyObject *) &IteratorType);
        }
    }
}
