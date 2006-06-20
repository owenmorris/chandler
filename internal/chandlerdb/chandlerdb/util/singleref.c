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

static void t_sr_dealloc(t_sr *self);
static PyObject *t_sr_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_sr_init(t_sr *self, PyObject *args, PyObject *kwds);
static int t_sr_hash(t_sr *self);
static PyObject *t_sr_str(t_sr *self);
static PyObject *t_sr_repr(t_sr *self);
static int t_sr_cmp(t_sr *o1, t_sr *o2);
static PyObject *t_sr_richcmp(t_sr *o1, t_sr *o2, int opid);
static PyObject *t_sr__getUUID(t_sr *self, void *data);


static PyMemberDef t_sr_members[] = {
    { "_uuid", T_OBJECT, offsetof(t_sr, uuid), 0, "UUID" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_sr_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_sr_properties[] = {
    { "itsUUID", (getter) t_sr__getUUID, NULL, NULL, NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject SingleRefType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.util.c.SingleRef",    /* tp_name */
    sizeof(t_sr),                     /* tp_basicsize */
    0,                                /* tp_itemsize */
    (destructor)t_sr_dealloc,         /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    (cmpfunc)t_sr_cmp,                /* tp_compare */
    (reprfunc)t_sr_repr,              /* tp_repr */
    0,                                /* tp_as_number */
    0,                                /* tp_as_sequence */
    0,                                /* tp_as_mapping */
    (hashfunc)t_sr_hash,              /* tp_hash  */
    0,                                /* tp_call */
    (reprfunc)t_sr_str,               /* tp_str */
    0,                                /* tp_getattro */
    0,                                /* tp_setattro */
    0,                                /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,               /* tp_flags */
    "t_sr objects",                   /* tp_doc */
    0,                                /* tp_traverse */
    0,                                /* tp_clear */
    (richcmpfunc)t_sr_richcmp,        /* tp_richcompare */
    0,                                /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    t_sr_methods,                     /* tp_methods */
    t_sr_members,                     /* tp_members */
    t_sr_properties,                  /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    (initproc)t_sr_init,              /* tp_init */
    0,                                /* tp_alloc */
    (newfunc)t_sr_new,                /* tp_new */
};


static void t_sr_dealloc(t_sr *self)
{
    Py_XDECREF(self->uuid);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_sr_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_sr *self = (t_sr *) type->tp_alloc(type, 0);

    if (self)
        self->uuid = NULL;

    return (PyObject *) self;
}

static int t_sr_init(t_sr *self, PyObject *args, PyObject *kwds)
{
    PyObject *uuid;

    if (!PyArg_ParseTuple(args, "O", &uuid))
        return -1; 

    Py_INCREF(uuid);
    Py_XDECREF(self->uuid);
    self->uuid = uuid;

    return 0;
}

static int t_sr_hash(t_sr *self)
{
    return ((t_uuid *) self->uuid)->hash;
}

static PyObject *t_sr_str(t_sr *self)
{
    t_uuid *uuid = (t_uuid *) self->uuid;
    return uuid->ob_type->tp_str((PyObject *) uuid);
}

static PyObject *t_sr_repr(t_sr *self)
{
    PyObject *str = t_sr_str(self);
    PyObject *repr = PyString_FromFormat("<ref: %s>", PyString_AsString(str));

    Py_DECREF(str);

    return repr;
}

static int t_sr_cmp(t_sr *o1, t_sr *o2)
{
    if (!PyObject_TypeCheck(o1, &SingleRefType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) o1);
        return -1;
    }

    if (!PyObject_TypeCheck(o2, &SingleRefType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) o2);
        return -1;
    }

    return PyObject_Compare(((t_uuid *) o1->uuid)->uuid,
                            ((t_uuid *) o2->uuid)->uuid);
}

static PyObject *t_sr_richcmp(t_sr *o1, t_sr *o2, int opid)
{
    if (!PyObject_TypeCheck(o1, &SingleRefType) ||
        !PyObject_TypeCheck(o2, &SingleRefType))
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    return PyObject_RichCompare(((t_uuid *) o1->uuid)->uuid,
                                ((t_uuid *) o2->uuid)->uuid, opid);
}


/* itsUUID */

static PyObject *t_sr__getUUID(t_sr *self, void *data)
{
    PyObject *uuid = self->uuid;

    Py_INCREF(uuid);
    return uuid;
}



void _init_singleref(PyObject *m)
{
    if (PyType_Ready(&SingleRefType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&SingleRefType);
            PyModule_AddObject(m, "SingleRef", (PyObject *) &SingleRefType);
            SingleRef = &SingleRefType;
        }
    }
}
