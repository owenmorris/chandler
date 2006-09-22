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
    PyObject *cdesc;
    PyObject *name;
} t_redirector;


static void t_redirector_dealloc(t_redirector *self);
static int t_redirector_traverse(t_redirector *self,
                                 visitproc visit, void *arg);
static int t_redirector_clear(t_redirector *self);
static PyObject *t_redirector_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds);
static int t_redirector_init(t_redirector *self,
                             PyObject *args, PyObject *kwds);
static PyObject *t_redirector___get__(t_redirector *self,
                                      PyObject *obj, PyObject *type);
static int t_redirector___set__(t_redirector *self,
                                PyObject *obj, PyObject *value);

static PyObject *name_NAME;
static PyObject *itsItem = NULL;


static PyMemberDef t_redirector_members[] = {
    { "cdesc", T_OBJECT, offsetof(t_redirector, cdesc), READONLY, "" },
    { "name", T_OBJECT, offsetof(t_redirector, name), READONLY, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_redirector_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyTypeObject RedirectorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                          /* ob_size */
    "chandlerdb.schema.c.Redirector",           /* tp_name */
    sizeof(t_redirector),                       /* tp_basicsize */
    0,                                          /* tp_itemsize */
    (destructor)t_redirector_dealloc,           /* tp_dealloc */
    0,                                          /* tp_print */
    0,                                          /* tp_getattr */
    0,                                          /* tp_setattr */
    0,                                          /* tp_compare */
    0,                                          /* tp_repr */
    0,                                          /* tp_as_number */
    0,                                          /* tp_as_sequence */
    0,                                          /* tp_as_mapping */
    0,                                          /* tp_hash  */
    0,                                          /* tp_call */
    0,                                          /* tp_str */
    0,                                          /* tp_getattro */
    0,                                          /* tp_setattro */
    0,                                          /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                       /* tp_flags */
    "attribute redirector",                     /* tp_doc */
    (traverseproc)t_redirector_traverse,        /* tp_traverse */
    (inquiry)t_redirector_clear,                /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    t_redirector_methods,                       /* tp_methods */
    t_redirector_members,                       /* tp_members */
    0,                                          /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    (descrgetfunc)t_redirector___get__,         /* tp_descr_get */
    (descrsetfunc)t_redirector___set__,         /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    (initproc)t_redirector_init,                /* tp_init */
    0,                                          /* tp_alloc */
    (newfunc)t_redirector_new,                  /* tp_new */
};


static void t_redirector_dealloc(t_redirector *self)
{
    t_redirector_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_redirector_traverse(t_redirector *self,
                                 visitproc visit, void *arg)
{
    Py_VISIT(self->cdesc);
    Py_VISIT(self->name);

    return 0;
}

static int t_redirector_clear(t_redirector *self)
{
    Py_CLEAR(self->cdesc);
    Py_CLEAR(self->name);

    return 0;
}


static PyObject *t_redirector_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds)
{
    t_redirector *self = (t_redirector *) type->tp_alloc(type, 0);

    if (self)
    {
        self->cdesc = NULL;
        self->name = NULL;
    }

    return (PyObject *) self;
}

static int t_redirector_init(t_redirector *self,
                             PyObject *args, PyObject *kwds)
{
    PyObject *cdesc;

    if (!PyArg_ParseTuple(args, "O", &cdesc))
        return -1;

    Py_INCREF(cdesc);
    self->cdesc = cdesc;
    self->name = PyObject_GetAttr(cdesc, name_NAME);

    return 0;
}


static PyObject *t_redirector___get__(t_redirector *self,
                                      PyObject *obj, PyObject *type)
{
    if (obj == NULL || obj == Py_None)
    {
        /* pretend to be the original descriptor if retrieved from class */
        Py_INCREF(self->cdesc);
        return self->cdesc;
    }
    else
    {
        PyObject *item, *result;

        if (!itsItem)
        {
            itsItem = PyObject_GetAttrString((PyObject *) obj->ob_type,
                                             "itsItem");
            if (!itsItem)
                return NULL;
        }
        
        item = itsItem->ob_type->tp_descr_get(itsItem, obj, NULL);
        if (!item)
            return NULL;

        result = item->ob_type->tp_getattro(item, self->name);
        Py_DECREF(item);

        return result;
    }
}

static int t_redirector___set__(t_redirector *self,
                                PyObject *obj, PyObject *value)
{
    if (obj == NULL || obj == Py_None)
    {
        PyErr_SetObject(PyExc_AttributeError, obj);
        return -1;
    }
    else
    {
        PyObject *item;
        int result;

        if (!itsItem)
        {
            itsItem = PyObject_GetAttrString((PyObject *) obj->ob_type,
                                             "itsItem");
            if (!itsItem)
                return -1;
        }
        
        item = itsItem->ob_type->tp_descr_get(itsItem, obj, NULL);
        if (!item)
            return -1;

        result = item->ob_type->tp_setattro(item, self->name, value);
        Py_DECREF(item);

        return result;
    }
}


void _init_redirector(PyObject *m)
{
    if (PyType_Ready(&RedirectorType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&RedirectorType);
            PyModule_AddObject(m, "Redirector", (PyObject *) &RedirectorType);

            name_NAME = PyString_FromString("name");
        }
    }
}
