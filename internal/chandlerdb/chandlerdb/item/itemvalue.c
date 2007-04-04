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


static void t_itemvalue_dealloc(t_itemvalue *self);
static int t_itemvalue_traverse(t_itemvalue *self, visitproc visit, void *arg);
static int t_itemvalue_clear(t_itemvalue *self);
static PyObject *t_itemvalue_new(PyTypeObject *type,
                                 PyObject *args, PyObject *kwds);
static int t_itemvalue_init(t_itemvalue *self, PyObject *args, PyObject *kwds);

static PyObject *t_itemvalue_isReadOnly(t_itemvalue *self);
static PyObject *t_itemvalue_isPure(t_itemvalue *self);
static PyObject *t_itemvalue__setDirty(t_itemvalue *self, PyObject *args);
static PyObject *t_itemvalue__setReadOnly(t_itemvalue *self, PyObject *args);
static PyObject *t_itemvalue__setPure(t_itemvalue *self, PyObject *args);
static PyObject *t_itemvalue__setOwner(t_itemvalue *self, PyObject *args);
static int _t_itemvalue__setOwner(t_itemvalue *self,
                                  PyObject *item, PyObject *attribute,
                                  PyObject **pure);
static PyObject *t_itemvalue__copy(t_itemvalue *self, PyObject *args);
static PyObject *t_itemvalue__clone(t_itemvalue *self, PyObject *args);
static PyObject *t_itemvalue__check(t_itemvalue *self, PyObject *args);

static PyObject *t_itemvalue__getOwner(t_itemvalue *self, void *data);
static PyObject *t_itemvalue__getItem(t_itemvalue *self, void *data);
static PyObject *t_itemvalue__getAttribute(t_itemvalue *self, void *data);

static PyObject *error_NAME;

static PyMemberDef t_itemvalue_members[] = {
    { "_owner", T_OBJECT, offsetof(t_itemvalue, owner), 0, "" },
    { "_attribute", T_OBJECT, offsetof(t_itemvalue, attribute), 0, "" },
    { "_flags", T_UINT, offsetof(t_itemvalue, flags), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_itemvalue_methods[] = {
    { "isReadOnly", (PyCFunction) t_itemvalue_isReadOnly, METH_NOARGS, NULL },
    { "isPure", (PyCFunction) t_itemvalue_isPure, METH_NOARGS, NULL },
    { "_setDirty", (PyCFunction) t_itemvalue__setDirty, METH_VARARGS, NULL },
    { "_setReadOnly", (PyCFunction) t_itemvalue__setReadOnly, METH_VARARGS, NULL },
    { "_setPure", (PyCFunction) t_itemvalue__setPure, METH_VARARGS, NULL },
    { "_setOwner", (PyCFunction) t_itemvalue__setOwner, METH_VARARGS, NULL },
    { "_copy", (PyCFunction) t_itemvalue__copy, METH_VARARGS, NULL },
    { "_clone", (PyCFunction) t_itemvalue__clone, METH_VARARGS, NULL },
    { "_check", (PyCFunction) t_itemvalue__check, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_itemvalue_properties[] = {
    { "itsOwner", (getter) t_itemvalue__getOwner, NULL,
      NULL, NULL },
    { "itsItem", (getter) t_itemvalue__getItem, NULL,
      NULL, NULL },
    { "itsAttribute", (getter) t_itemvalue__getAttribute, NULL,
      NULL, NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject ItemValueType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.ItemValue",             /* tp_name */
    sizeof(t_itemvalue),                       /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_itemvalue_dealloc,           /* tp_dealloc */
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
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "C ItemValue type",                        /* tp_doc */
    (traverseproc)t_itemvalue_traverse,        /* tp_traverse */
    (inquiry)t_itemvalue_clear,                /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    0,                                         /* tp_iter */
    0,                                         /* tp_iternext */
    t_itemvalue_methods,                       /* tp_methods */
    t_itemvalue_members,                       /* tp_members */
    t_itemvalue_properties,                    /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_itemvalue_init,                /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_itemvalue_new,                  /* tp_new */
};


static void t_itemvalue_dealloc(t_itemvalue *self)
{
    t_itemvalue_clear(self);
    self->persistentvalue.ob_type->tp_free((PyObject *) self);
}

static int t_itemvalue_traverse(t_itemvalue *self, visitproc visit, void *arg)
{
    Py_VISIT(self->owner);
    Py_VISIT(self->attribute);

    PersistentValue->tp_traverse((PyObject *) self, visit, arg);

    return 0;
}

static int t_itemvalue_clear(t_itemvalue *self)
{
    Py_CLEAR(self->owner);
    Py_CLEAR(self->attribute);

    PersistentValue->tp_clear((PyObject *) self);

    return 0;
}

static PyObject *t_itemvalue_new(PyTypeObject *type,
                                 PyObject *args, PyObject *kwds)
{
    t_itemvalue *self = (t_itemvalue *) type->tp_alloc(type, 0);

    if (self)
    {
        self->owner = NULL;
        self->attribute = NULL;
        self->flags = 0;
    }

    return (PyObject *) self;
}

int _t_itemvalue_init(t_itemvalue *self, PyObject *view,
                      PyObject *item, PyObject *attribute)
{
    PyObject *pure = Py_False;

    if (_t_persistentvalue_init((t_persistentvalue *) self, view) < 0)
        return -1;

    self->flags = 0;

    if (_t_itemvalue__setOwner(self, item, attribute, &pure) < 0)
        return -1;

    return 0;
}

static int t_itemvalue_init(t_itemvalue *self, PyObject *args, PyObject *kwds)
{
    PyObject *view, *item, *attribute;

    if (!PyArg_ParseTuple(args, "OOO", &view, &item, &attribute))
        return -1;

    return _t_itemvalue_init(self, view, item, attribute);
}

static PyObject *t_itemvalue_isReadOnly(t_itemvalue *self)
{
    if (self->flags & V_READONLY)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_itemvalue_isPure(t_itemvalue *self)
{
    if (self->flags & V_PURE)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

int _t_itemvalue__setDirty(t_itemvalue *self, int noChanges)
{
    PyObject *item;

    if (self->flags & V_READONLY)
    {
        PyErr_SetObject((PyObject *) ReadOnlyAttributeError, (PyObject *) self);
        return -1;
    }

    item = PyObject_Call(self->owner, Empty_TUPLE, NULL);
    if (!item)
        return -1;

    if (item != Py_None)
    {
        int result =
            _t_item_setDirty((t_item *) item, VDIRTY, self->attribute,
                             ((t_item *) item)->values, noChanges);

        Py_DECREF(item);
        return result;
    }

    Py_DECREF(item);
    return 0;
}

static PyObject *t_itemvalue__setDirty(t_itemvalue *self, PyObject *args)
{
    int noChanges = 0, result;

    if (!PyArg_ParseTuple(args, "|i", &noChanges))
        return NULL;

    result = _t_itemvalue__setDirty(self, noChanges);
    if (result < 0)
        return NULL;

    if (result)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_itemvalue__setReadOnly(t_itemvalue *self, PyObject *args)
{
    PyObject *readOnly = Py_True;
    
    if (!PyArg_ParseTuple(args, "|O", &readOnly))
        return NULL;

    if (PyObject_IsTrue(readOnly))
        self->flags |= V_READONLY;
    else
        self->flags &= ~V_READONLY;

    Py_RETURN_NONE;
}

static PyObject *t_itemvalue__setPure(t_itemvalue *self, PyObject *args)
{
    PyObject *pure = Py_True;
    
    if (!PyArg_ParseTuple(args, "|O", &pure))
        return NULL;

    if (PyObject_IsTrue(pure))
        self->flags |= V_PURE;
    else
        self->flags &= ~V_PURE;

    Py_RETURN_NONE;
}

static int _t_itemvalue__setOwner(t_itemvalue *self,
                                  PyObject *item, PyObject *attribute,
                                  PyObject **pure)
{
    PyObject *owner;

    if (item == Py_None)
        owner = Nil;
    else if (PyObject_TypeCheck(item, CItem))
    {
        PyObject *ref = (PyObject *) ((t_item *) item)->ref;
        PyObject *view = ((t_item *) item)->ref->view;

        if (self->owner && self->owner != Nil && self->owner != ref)
        {
            PyObject *err = PyTuple_Pack(3, self->owner, self->attribute, self);
            PyErr_SetObject(PyExc_ValueError, err);
            Py_DECREF(err);
            return -1;
        }

        Py_INCREF(view);
        Py_XDECREF(self->persistentvalue.view);
        self->persistentvalue.view = view;

        if (*pure == Py_None)
        {
            t_attribute *attr = _t_item_get_attr((t_item *) item, attribute);

            if (attr)
            {
                if (attr->flags & PURE)
                    *pure = Py_True;
                else
                    *pure = Py_False;
            }
            else if (PyErr_Occurred())
                PyErr_Clear();
        }

        owner = ref;
    }
    else
    {
        PyErr_SetObject(PyExc_TypeError, item);
        return -1;
    }

    Py_INCREF(owner);
    Py_XDECREF(self->owner);
    self->owner = owner;

    Py_INCREF(attribute);
    Py_XDECREF(self->attribute);
    self->attribute = attribute;

    if (*pure == Py_True)
        self->flags |= V_PURE;
    else if (*pure == Py_False)
        self->flags &= ~V_PURE;

    return 0;
}

static PyObject *t_itemvalue__setOwner(t_itemvalue *self, PyObject *args)
{
    PyObject *item, *attribute, *pure = Py_None;
    PyObject *oldOwner, *oldAttribute, *oldItem, *result;

    if (!PyArg_ParseTuple(args, "OO|O", &item, &attribute, &pure))
        return NULL;

    oldOwner = self->owner;
    Py_INCREF(oldOwner);
    oldAttribute = self->attribute;
    Py_INCREF(oldAttribute);

    if (_t_itemvalue__setOwner(self, item, attribute, &pure) < 0)
    {
        Py_DECREF(oldOwner);
        Py_DECREF(oldAttribute);
        return NULL;
    }

    oldItem = PyObject_Call(oldOwner, Empty_TUPLE, NULL);
    Py_DECREF(oldOwner);
    if (!oldItem)
        return NULL;

    result = PyTuple_Pack(3, oldItem, oldAttribute, pure);
    Py_DECREF(oldItem);
    Py_DECREF(oldAttribute);

    return result;
}

static PyObject *t_itemvalue__copy(t_itemvalue *self, PyObject *args)
{
    PyErr_SetString(PyExc_NotImplementedError, "_copy");
    return NULL;
}

static PyObject *t_itemvalue__clone(t_itemvalue *self, PyObject *args)
{
    PyErr_SetString(PyExc_NotImplementedError, "_clone");
    return NULL;
}

static PyObject *t_itemvalue__check(t_itemvalue *self, PyObject *args)
{
    PyObject *logger, *item, *attribute, *repair;
    PyObject *owner, *result = Py_True;

    if (!PyArg_ParseTuple(args, "OOOO", &logger, &item, &attribute, &repair))
        return NULL;

    if (!PyObject_TypeCheck(item, CItem))
    {
        PyErr_SetObject(PyExc_TypeError, item);
        return NULL;
    }

    owner = PyObject_Call(self->owner, True_TUPLE, NULL);
    if (!owner)
        return NULL;

    if (item != owner || PyObject_Compare(attribute, self->attribute))
    {
        PyObject *format = PyString_FromString("Value %s of type %s in attribute %s on %s is owned by attribute %s on %s");
        PyObject *repr = t_item_repr((t_item *) item);

        result = PyObject_CallMethodObjArgs(logger, error_NAME, format,
                                            self, self->persistentvalue.ob_type,
                                            attribute, repr, self->attribute,
                                            owner, NULL);
        Py_DECREF(repr);
        Py_DECREF(format);
        if (!result)
            return NULL;

        Py_DECREF(result);
        result = Py_False;
    }

    Py_DECREF(owner);
    Py_INCREF(result);

    return result;
}


/* itsOwner */

static PyObject *t_itemvalue__getOwner(t_itemvalue *self, void *data)
{
    PyObject *item = PyObject_Call(self->owner, Empty_TUPLE, NULL);
    PyObject *result;

    if (!item)
        return NULL;

    result = PyTuple_Pack(2, item, self->attribute);
    Py_DECREF(item);

    return result;
}


/* itsItem */

static PyObject *t_itemvalue__getItem(t_itemvalue *self, void *data)
{
    return PyObject_Call(self->owner, Empty_TUPLE, NULL);
}


/* itsAttribute */

static PyObject *t_itemvalue__getAttribute(t_itemvalue *self, void *data)
{
    Py_INCREF(self->attribute);
    return self->attribute;
}


void _init_itemvalue(PyObject *m)
{
    ItemValueType.tp_base = PersistentValue;

    if (PyType_Ready(&ItemValueType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&ItemValueType);
            PyModule_AddObject(m, "ItemValue", (PyObject *) &ItemValueType);
            ItemValue = &ItemValueType;

            error_NAME = PyString_FromString("error");
        }
    }
}
