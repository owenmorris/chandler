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

static void t_kind_dealloc(t_kind *self);
static int t_kind_traverse(t_kind *self, visitproc visit, void *arg);
static int t_kind_clear(t_kind *self);
static PyObject *t_kind_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_kind_init(t_kind *self, PyObject *args, PyObject *kwds);

static PyObject *t_kind_getAttribute(t_kind *self, PyObject *args);
static PyObject *t_kind__setupDescriptors(t_kind *self, PyObject *args);

static PyObject *t_kind_getMonitorSchema(t_kind *self, void *data);
static int t_kind_setMonitorSchema(t_kind *self, PyObject *arg, void *data);
static PyObject *t_kind_getAttributesCached(t_kind *self, void *data);
static int t_kind_setAttributesCached(t_kind *self, PyObject *arg, void *data);
static PyObject *t_kind_getSuperKindsCached(t_kind *self, void *data);
static int t_kind_setSuperKindsCached(t_kind *self, PyObject *arg, void *data);


static PyMemberDef t_kind_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_kind_methods[] = {
    { "getAttribute", (PyCFunction) t_kind_getAttribute,
      METH_VARARGS, "" },
    { "_setupDescriptors", (PyCFunction) t_kind__setupDescriptors,
      METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_kind_properties[] = {
    { "monitorSchema",
      (getter) t_kind_getMonitorSchema,
      (setter) t_kind_setMonitorSchema,
      NULL, NULL },
    { "attributesCached",
      (getter) t_kind_getAttributesCached,
      (setter) t_kind_setAttributesCached,
      NULL, NULL },
    { "superKindsCached",
      (getter) t_kind_getSuperKindsCached,
      (setter) t_kind_setSuperKindsCached,
      NULL, NULL },
    { NULL, NULL, NULL, NULL, NULL }
};


static PyTypeObject KindType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.schema.c.CKind",                         /* tp_name */
    sizeof(t_kind),                                      /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_kind_dealloc,                          /* tp_dealloc */
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
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,            /* tp_flags */
    "C Kind type",                                       /* tp_doc */
    (traverseproc)t_kind_traverse,                       /* tp_traverse */
    (inquiry)t_kind_clear,                               /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_kind_methods,                                      /* tp_methods */
    t_kind_members,                                      /* tp_members */
    t_kind_properties,                                   /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_kind_init,                               /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_kind_new,                                 /* tp_new */
};


static void t_kind_dealloc(t_kind *self)
{
    t_kind_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_kind_traverse(t_kind *self, visitproc visit, void *arg)
{
    Py_VISIT((PyObject *) self->kind);
    return 0;
}

static int t_kind_clear(t_kind *self)
{
    Py_CLEAR(self->kind);
    return 0;
}

static PyObject *t_kind_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_kind *self = (t_kind *) type->tp_alloc(type, 0);

    if (self)
    {
        self->kind = NULL;
        self->flags = 0;
    }

    return (PyObject *) self;
}

static int t_kind_init(t_kind *self, PyObject *args, PyObject *kwds)
{
    PyObject *kind;

    if (!PyArg_ParseTuple(args, "O", &kind))
        return -1;

    Py_INCREF(kind);
    self->kind = (t_item *) kind;

    return 0;
}


static PyObject *t_kind_getAttribute(t_kind *self, PyObject *args)
{
    PyObject *item, *name, *descriptor;

    if (!PyArg_ParseTuple(args, "OO", &item, &name))
        return NULL;
    
    descriptor = PyObject_GetAttr((PyObject *) item->ob_type, name);
    if (descriptor)
    {
        if (PyObject_TypeCheck(descriptor, CDescriptor))
        {
            t_attribute *attr = (t_attribute *)
                PyDict_GetItem(((t_descriptor *) descriptor)->attrs,
                               self->kind->uuid);

            Py_DECREF(descriptor);

            if (attr)
            {
                PyObject *view = ((t_item *) self->kind->root)->parent;
                return PyObject_GetItem(view, attr->attrID);
            }
        }
        else
            Py_DECREF(descriptor);
    }
    else
        PyErr_Clear();

    Py_RETURN_NONE;
}

static PyObject *t_kind__setupDescriptors(t_kind *self, PyObject *args)
{
    PyObject *descriptors, *cls, *clsDescriptors, *actions;
    int actionCount, i;

    if (!PyArg_ParseTuple(args, "OOOO!", &descriptors, &cls,
                          &clsDescriptors, &PyList_Type, &actions))
        return NULL;

    actionCount = PyList_GET_SIZE(actions);

    for (i = 0; i < actionCount; i++) {
        PyObject *action = PyList_GET_ITEM(actions, i);
        PyObject *descriptor, *attribute;
        int count;

        if (!PyTuple_Check(action))
        {
            PyErr_SetObject(PyExc_TypeError, action);
            return NULL;
        }

        count = PyTuple_GET_SIZE(action);

        if (count != 2 && count != 3)
        {
            PyErr_SetObject(PyExc_ValueError, action);
            return NULL;
        }

        descriptor = PyTuple_GET_ITEM(action, 0);
        attribute = PyTuple_GET_ITEM(action, 1);

        if (!PyObject_TypeCheck(descriptor, CDescriptor))
        {
            PyErr_SetObject(PyExc_TypeError, descriptor);
            return NULL;
        }

        if (!PyObject_TypeCheck(attribute, CAttribute))
        {
            PyErr_SetObject(PyExc_TypeError, attribute);
            return NULL;
        }

        PyDict_SetItem(((t_descriptor *) descriptor)->attrs,
                       self->kind->uuid, attribute);

        if (count == 3)
            PyObject_SetAttr(cls, PyTuple_GET_ITEM(action, 2), descriptor);
    }

    PyDict_SetItem(descriptors, cls, clsDescriptors);

    Py_RETURN_NONE;
}


/* monitorSchema */

static PyObject *t_kind_getMonitorSchema(t_kind *self, void *data)
{
    if (self->flags & MONITOR_SCHEMA)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int t_kind_setMonitorSchema(t_kind *self, PyObject *arg, void *data)
{
    if (arg == Py_True)
        self->flags |= MONITOR_SCHEMA;
    else if (arg == Py_False)
        self->flags &= ~MONITOR_SCHEMA;
    else
    {
        PyErr_SetObject(PyExc_ValueError, arg);
        return -1;
    }

    return 0;
}


/* attributesCached */

static PyObject *t_kind_getAttributesCached(t_kind *self, void *data)
{
    if (self->flags & ATTRIBUTES_CACHED)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int t_kind_setAttributesCached(t_kind *self, PyObject *arg, void *data)
{
    if (arg == Py_True)
        self->flags |= ATTRIBUTES_CACHED;
    else if (arg == Py_False)
        self->flags &= ~ATTRIBUTES_CACHED;
    else
    {
        PyErr_SetObject(PyExc_ValueError, arg);
        return -1;
    }

    return 0;
}


/* superKindsCached */

static PyObject *t_kind_getSuperKindsCached(t_kind *self, void *data)
{
    if (self->flags & SUPERKINDS_CACHED)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int t_kind_setSuperKindsCached(t_kind *self, PyObject *arg, void *data)
{
    if (arg == Py_True)
        self->flags |= SUPERKINDS_CACHED;
    else if (arg == Py_False)
        self->flags &= ~SUPERKINDS_CACHED;
    else
    {
        PyErr_SetObject(PyExc_ValueError, arg);
        return -1;
    }

    return 0;
}


void _init_kind(PyObject *m)
{
    if (PyType_Ready(&KindType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&KindType);
            PyModule_AddObject(m, "CKind", (PyObject *) &KindType);
        }
    }
}
