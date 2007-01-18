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

static void t_descriptor_dealloc(t_descriptor *self);
static int t_descriptor_traverse(t_descriptor *self,
                                 visitproc visit, void *arg);
static int t_descriptor_clear(t_descriptor *self);
static PyObject *t_descriptor_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds);
static int t_descriptor_init(t_descriptor *self,
                             PyObject *args, PyObject *kwds);
static PyObject *t_descriptor___get__(t_descriptor *self,
                                      t_item *item, PyObject *type);
static int t_descriptor___set__(t_descriptor *self,
                                t_item *item, PyObject *value);
static int t_descriptor___delete__(t_descriptor *self, t_item *item);
static PyObject *t_descriptor_isValueRequired(t_descriptor *self, t_item *item);

static PyObject *_getRef_NAME;
static PyObject *getAttributeValue_NAME;
static PyObject *setAttributeValue_NAME;
static PyObject *removeAttributeValue_NAME;
static PyObject *inheritFrom_NAME;


static PyMemberDef t_descriptor_members[] = {
    { "name", T_OBJECT, offsetof(t_descriptor, name), READONLY,
      "attribute name" },
    { "attr", T_OBJECT, offsetof(t_descriptor, attr), READONLY,
      "C attribute" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_descriptor_methods[] = {
    { "isValueRequired", (PyCFunction) t_descriptor_isValueRequired,
      METH_O, "" },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject DescriptorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                          /* ob_size */
    "chandlerdb.schema.c.CDescriptor",          /* tp_name */
    sizeof(t_descriptor),                       /* tp_basicsize */
    0,                                          /* tp_itemsize */
    (destructor)t_descriptor_dealloc,           /* tp_dealloc */
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
    "attribute descriptor",                     /* tp_doc */
    (traverseproc)t_descriptor_traverse,        /* tp_traverse */
    (inquiry)t_descriptor_clear,                /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    t_descriptor_methods,                       /* tp_methods */
    t_descriptor_members,                       /* tp_members */
    0,                                          /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    (descrgetfunc)t_descriptor___get__,         /* tp_descr_get */
    (descrsetfunc)t_descriptor___set__,         /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    (initproc)t_descriptor_init,                /* tp_init */
    0,                                          /* tp_alloc */
    (newfunc)t_descriptor_new,                  /* tp_new */
};


static void t_descriptor_dealloc(t_descriptor *self)
{
    t_descriptor_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_descriptor_traverse(t_descriptor *self,
                                 visitproc visit, void *arg)
{
    Py_VISIT(self->name);
    Py_VISIT((PyObject *) self->attr);

    return 0;
}

static int t_descriptor_clear(t_descriptor *self)
{
    Py_CLEAR(self->name);
    Py_CLEAR(self->attr);

    return 0;
}


static PyObject *t_descriptor_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds)
{
    t_descriptor *self = (t_descriptor *) type->tp_alloc(type, 0);

    if (self)
    {
        self->name = NULL;
        self->attr = NULL;
    }

    return (PyObject *) self;
}

static int t_descriptor_init(t_descriptor *self,
                             PyObject *args, PyObject *kwds)
{
    PyObject *name, *attr = NULL;

    if (!PyArg_ParseTuple(args, "O|O", &name, &attr))
        return -1;

    Py_INCREF(name);
    self->name = name;

    if (attr)
    {
        if (PyObject_TypeCheck(attr, CAttribute))
        {
            Py_INCREF(attr);
            self->attr = (t_attribute *) attr;
        }
        else
        {
            PyErr_SetObject(PyExc_TypeError, attr);
            return -1;
        }
    }

    return 0;
}

static t_values *get_attrdict(t_item *item, int flags)
{
    switch (flags & ATTRDICT) {
      case VALUE:
        return item->values;
      case REF:
        return item->references;
      default:
        return NULL;
    }
}

static PyObject *t_descriptor___get__(t_descriptor *self,
                                      t_item *item, PyObject *type)
{
    if (item == NULL || (PyObject *) item == Py_None)
    {
        Py_INCREF(self);
        return (PyObject *) self;
    }
    else if (item->status & STALE)
    {
        PyErr_SetObject(PyExc_StaleItemError, (PyObject *) item);
        return NULL;
    }
    else
    {
        t_attribute *attr = self->attr;

        if (attr != NULL)
        {
            int flags = attr->flags;
            t_values *attrDict = get_attrdict(item, flags);
            PyObject *value = NULL;
            int found = 0;

            if (attrDict)
            {
                if (!(flags & PROCESS_GET))
                {
                    value = PyDict_GetItem(attrDict->dict, self->name);
                    if (value)
                    {
                        if (value->ob_type == ItemRef)
                            value = PyObject_Call(value, True_TUPLE, NULL);
                        else
                            Py_INCREF(value);
                        found = 1;
                    }
                    else
                        found = -1;
                }
                else if (flags & REF)
                {
                    value = PyDict_GetItem(attrDict->dict, self->name);
                    if (value)
                    {
                        if (value->ob_type == ItemRef)
                            value = PyObject_Call(value, Empty_TUPLE, NULL);
                        else if (value == Py_None ||
                                 PyObject_TypeCheck(value, CLinkedMap))
                            Py_INCREF(value);
                        else
                            value = PyObject_CallMethodObjArgs((PyObject *) attrDict, _getRef_NAME, self->name, Py_None, attr->otherName, NULL);
                        found = 1;
                    }
                    else
                        found = -1;
                }
            }

            if (found > 0)
                item->lastAccess = ++_lastAccess;
            else if (found < 0 && flags & NOINHERIT)
            {
                PyObject *inheritFrom = PyDict_GetItem(item->references->dict,
                                                       inheritFrom_NAME);
                if (inheritFrom)
                {
                    if (inheritFrom->ob_type == ItemRef)
                    {
                        inheritFrom = PyObject_Call(inheritFrom, Empty_TUPLE,
                                                    NULL);
                        if (inheritFrom)
                        {
                            item->lastAccess = ++_lastAccess;
                            value = PyObject_GetAttr(inheritFrom, self->name);
                            Py_DECREF(inheritFrom);
                        }
                        else
                            return NULL;
                    }
                    else
                    {
                        PyErr_SetObject(PyExc_TypeError, inheritFrom);
                        return NULL;
                    }
                }
                else if (flags & DEFAULT)
                {
                    value = attr->defaultValue;
                    Py_INCREF(value);
                }
                else
                    PyErr_SetObject(PyExc_AttributeError, self->name);
            }                    
            else
                value = PyObject_CallMethodObjArgs((PyObject *) item, getAttributeValue_NAME, self->name, attrDict, attr->attrID, NULL);

            return value;
        }

        PyErr_SetObject(PyExc_AttributeError, self->name);
        return NULL;
    }
}

static int t_descriptor___set__(t_descriptor *self,
                                t_item *item, PyObject *value)
{
    if (item == NULL || (PyObject *) item == Py_None)
    {
        PyErr_SetObject(PyExc_AttributeError, (PyObject *) item);
        return -1;
    }
    else if (item->status & STALE)
    {
        PyErr_SetObject(PyExc_StaleItemError, (PyObject *) item);
        return -1;
    }
    else if (value == NULL)
        return t_descriptor___delete__(self, item);
    else
    {
        t_attribute *attr = self->attr;

        if (attr != NULL)
        {
            int flags = attr->flags;
            t_values *attrDict = get_attrdict(item, flags);

            if (attrDict)
            {
                PyObject *oldValue =
                    PyDict_GetItem(attrDict->dict, self->name);

                if (oldValue && oldValue->ob_type == ItemRef)
                    oldValue = (PyObject *) ((t_itemref *) oldValue)->item;

                if (value == oldValue)
                    return 0;

                if (flags & SINGLE && !(flags & PROCESS_SET) && oldValue)
                {
                    int eq = PyObject_RichCompareBool(value, oldValue, Py_EQ);

                    if (eq == -1)
                        PyErr_Clear();
                    else if (eq == 1)
                        return 0;
                }
            }

            value = PyObject_CallMethodObjArgs((PyObject *) item, setAttributeValue_NAME, self->name, value, attrDict ? (PyObject *) attrDict : Py_None, flags & REF ? attr->otherName : Py_None, Py_True, NULL);

            if (!value)
                return -1;
                    
            Py_DECREF(value);
            return 0;
        }

        PyErr_SetObject(PyExc_AttributeError, self->name);
        return -1;
    }
}

static int t_descriptor___delete__(t_descriptor *self, t_item *item)
{
    t_attribute *attr = self->attr;

    if (attr)
    {
        t_values *attrDict = get_attrdict(item, attr->flags);
        PyObject *value = PyObject_CallMethodObjArgs((PyObject *) item, removeAttributeValue_NAME, self->name, attrDict ? (PyObject *) attrDict : Py_None, attr->attrID, NULL);

        if (!value)
            return -1;

        Py_DECREF(value);
        return 0;
    }

    PyErr_SetObject(PyExc_AttributeError, self->name);
    return -1;
}

static PyObject *t_descriptor_isValueRequired(t_descriptor *self, t_item *item)
{
    t_attribute *attr = self->attr;

    if (!PyObject_TypeCheck(item, CItem))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) item);
        return NULL;
    }

    if (attr)
    {
        int flags = attr->flags;
        t_values *attrDict = get_attrdict(item, flags);

        return PyTuple_Pack(2,
                            attrDict ? (PyObject *) attrDict : Py_None,
                            attrDict && flags & REQUIRED ? Py_True : Py_False);
    }
    else
        return PyTuple_Pack(2, Py_None, Py_False);
}


void _init_descriptor(PyObject *m)
{
    if (PyType_Ready(&DescriptorType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&DescriptorType);
            PyModule_AddObject(m, "CDescriptor", (PyObject *) &DescriptorType);
            CDescriptor = &DescriptorType;

            _getRef_NAME = PyString_FromString("_getRef");
            getAttributeValue_NAME = PyString_FromString("getAttributeValue");
            setAttributeValue_NAME = PyString_FromString("setAttributeValue");
            removeAttributeValue_NAME = PyString_FromString("removeAttributeValue");
            inheritFrom_NAME = PyString_FromString("inheritFrom");
        }
    }
}
