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


static void t_persistentvalue_dealloc(t_persistentvalue *self);
static int t_persistentvalue_traverse(t_persistentvalue *self,
                                      visitproc visit, void *arg);
static int t_persistentvalue_clear(t_persistentvalue *self);
static PyObject *t_persistentvalue_new(PyTypeObject *type,
                                       PyObject *args, PyObject *kwds);
static int t_persistentvalue_init(t_persistentvalue *self,
                                  PyObject *args, PyObject *kwds);

static PyObject *t_persistentvalue__getView(t_persistentvalue *self,
                                            void *data);

static PyMemberDef t_persistentvalue_members[] = {
    { "_view", T_OBJECT, offsetof(t_persistentvalue, view), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_persistentvalue_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_persistentvalue_properties[] = {
    { "itsView", (getter) t_persistentvalue__getView, NULL,
      "itsView property", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject PersistentValueType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.util.c.PersistentValue",                 /* tp_name */
    sizeof(t_persistentvalue),                           /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_persistentvalue_dealloc,               /* tp_dealloc */
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
    "C PersistentValue type",                            /* tp_doc */
    (traverseproc)t_persistentvalue_traverse,            /* tp_traverse */
    (inquiry)t_persistentvalue_clear,                    /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_persistentvalue_methods,                           /* tp_methods */
    t_persistentvalue_members,                           /* tp_members */
    t_persistentvalue_properties,                        /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_persistentvalue_init,                    /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_persistentvalue_new,                      /* tp_new */
};

static void t_persistentvalue_dealloc(t_persistentvalue *self)
{
    t_persistentvalue_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_persistentvalue_traverse(t_persistentvalue *self,
                                      visitproc visit, void *arg)
{
    Py_VISIT(self->view);
    return 0;
}

static int t_persistentvalue_clear(t_persistentvalue *self)
{
    Py_CLEAR(self->view);
    return 0;
}

static PyObject *t_persistentvalue_new(PyTypeObject *type,
                                       PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

int _t_persistentvalue_init(t_persistentvalue *self, PyObject *view)
{
    Py_XDECREF(self->view);
    Py_INCREF(view);
    self->view = view;

    return 0;
}

static int t_persistentvalue_init(t_persistentvalue *self,
                                  PyObject *args, PyObject *kwds)
{
    PyObject *view;

    if (!PyArg_ParseTuple(args, "O", &view))
        return -1;

    return _t_persistentvalue_init(self, view);
}

static PyObject *t_persistentvalue__getView(t_persistentvalue *self,
                                            void *data)
{
    Py_INCREF(self->view);
    return self->view;
}

void _init_persistentvalue(PyObject *m)
{
    if (PyType_Ready(&PersistentValueType) >= 0)
    {
        if (m)
        {
            PyObject *cobj;

            Py_INCREF(&PersistentValueType);
            PyModule_AddObject(m, "PersistentValue",
                               (PyObject *) &PersistentValueType);
            PersistentValue = &PersistentValueType;

            cobj = PyCObject_FromVoidPtr(_t_persistentvalue_init, NULL);
            PyModule_AddObject(m, "_t_persistentvalue_init", cobj);
        }
    }
}
