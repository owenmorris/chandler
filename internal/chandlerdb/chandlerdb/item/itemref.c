/*
 *  Copyright (c) 2003-2007 Open Source Applications Foundation
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

static void t_itemref_dealloc(t_itemref *self);
static int t_itemref_clear(t_itemref *self);
static int t_itemref_traverse(t_itemref *self, visitproc visit, void *arg);
static PyObject *t_itemref_new(PyTypeObject *type,
                               PyObject *args, PyObject *kwds);
static long t_itemref_hash(t_itemref *self);
static PyObject *t_itemref_repr(t_itemref *self);
static int t_itemref_cmp(t_itemref *self, t_itemref *other);
static PyObject *t_itemref_richcmp(t_itemref *self, t_itemref *other, int opid);
static PyObject *t_itemref__getUUID(t_itemref *self, void *data);
static PyObject *t_itemref__getView(t_itemref *self, void *data);
static PyObject *t_itemref__getItem(t_itemref *self, void *data);
static PyObject *t_itemref__getRef(t_itemref *self, void *data);
static PyObject *t_itemref__isRefs(t_itemref *self);

static PyMemberDef t_itemref_members[] = {
    { "_uuid", T_OBJECT, offsetof(t_itemref, uuid), READONLY, "UUID" },
    { "_item", T_OBJECT, offsetof(t_itemref, item), READONLY, "item" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_itemref_methods[] = {
    { "_isRefs", (PyCFunction) t_itemref__isRefs, METH_NOARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_itemref_properties[] = {
    { "itsUUID", (getter) t_itemref__getUUID, NULL, NULL, NULL },
    { "itsView", (getter) t_itemref__getView, NULL, NULL, NULL },
    { "itsItem", (getter) t_itemref__getItem, NULL, NULL, NULL },
    { "itsRef", (getter) t_itemref__getRef, NULL, NULL, NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject ItemRefType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.item.c.ItemRef",      /* tp_name */
    sizeof(t_itemref),                /* tp_basicsize */
    0,                                /* tp_itemsize */
    (destructor)t_itemref_dealloc,    /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    (cmpfunc)t_itemref_cmp,           /* tp_compare */
    (reprfunc)t_itemref_repr,         /* tp_repr */
    0,                                /* tp_as_number */
    0,                                /* tp_as_sequence */
    0,                                /* tp_as_mapping */
    (hashfunc)t_itemref_hash,         /* tp_hash  */
    (ternaryfunc)t_itemref_call,      /* tp_call */
    0,                                /* tp_str */
    0,                                /* tp_getattro */
    0,                                /* tp_setattro */
    0,                                /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_HAVE_GC),             /* tp_flags */
    "t_itemref objects",              /* tp_doc */
    (traverseproc)t_itemref_traverse, /* tp_traverse */
    (inquiry)t_itemref_clear,         /* tp_clear */
    (richcmpfunc)t_itemref_richcmp,   /* tp_richcompare */
    offsetof(t_itemref, weakrefs),    /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    t_itemref_methods,                /* tp_methods */
    t_itemref_members,                /* tp_members */
    t_itemref_properties,             /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    0,                                /* tp_init */
    0,                                /* tp_alloc */
    (newfunc)t_itemref_new,           /* tp_new */
};


static void t_itemref_dealloc(t_itemref *self)
{
    t_itemref_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_itemref_clear(t_itemref *self)
{
    if (self->view)
    {
        PyObject *dict = ((t_view *) self->view)->refRegistry;

        if (dict)
        {
            PyObject *ref = PyDict_GetItem(dict, self->uuid);
            
            if (ref && PyWeakref_GET_OBJECT(ref) == (PyObject *) self)
                PyDict_DelItem(dict, self->uuid);
        }
    }

    if (self->weakrefs)
        PyObject_ClearWeakRefs((PyObject *) self);

    Py_CLEAR(self->uuid);
    Py_CLEAR(self->view);
    self->item = NULL; /* weak reference, not counted */

    return 0;
}

static int t_itemref_traverse(t_itemref *self, visitproc visit, void *arg)
{
    Py_VISIT(self->uuid);
    Py_VISIT(self->view);

    return 0;
}

t_itemref *_t_itemref_new(PyObject *uuid, t_view *view, t_item *item)
{
    t_itemref *self = NULL;
    PyObject *old = NULL;

    if (item)
    {
        old = PyDict_GetItem(view->registry, uuid);
        if (old)
        {
            if (old != (PyObject *) item)
            {
                PyErr_SetString(PyExc_ValueError,
                                "re-registering item with different instance");
                return NULL;
            }
        }
    }

    if (item && item->ref)
    {
        self = item->ref;
        Py_INCREF(self);
    }
    else
    {
        PyObject *ref = PyDict_GetItem(view->refRegistry, uuid);

        if (ref)
        {
            PyObject *value = PyWeakref_GetObject(ref);

            if (!value)
                return NULL;

            if (value != Py_None)
            {
                if (value->ob_type != ItemRef)
                {
                    PyErr_SetObject(PyExc_TypeError, value);
                    return NULL;
                }

                self = (t_itemref *) value;
                Py_INCREF(self);
            }
        }

        if (!self)
        {
            self = (t_itemref *) ItemRef->tp_alloc(ItemRef, 0);
            if (!self)
                return NULL;

            ref = PyWeakref_NewRef((PyObject *) self, NULL);
            if (!ref)
            {
                Py_DECREF(self);
                return NULL;
            }

            self->uuid = uuid; Py_INCREF(uuid);
            self->view = (PyObject *) view; Py_INCREF(view);
            self->item = NULL;

            PyDict_SetItem(view->refRegistry, uuid, ref);
            Py_DECREF(ref);
        }
    }

    if (item)
    {
        if (old != (PyObject *) item)
            PyDict_SetItem(view->registry, uuid, (PyObject *) item);

        self->item = item; /* weak reference, not counted */
    }

    return self;
}

static PyObject *t_itemref_new(PyTypeObject *type,
                               PyObject *args, PyObject *kwds)
{
    PyObject *uuid, *view;

    if (!PyArg_ParseTuple(args, "OO", &uuid, &view))
        return NULL;

    if (!PyUUID_Check(uuid))
    {
        PyErr_SetObject(PyExc_TypeError, uuid);
        return NULL;
    }
    if (!PyObject_TypeCheck(view, CView))
    {
        PyErr_SetObject(PyExc_TypeError, view);
        return NULL;
    }

    return (PyObject *) _t_itemref_new(uuid, (t_view *) view, NULL);
}

static long t_itemref_hash(t_itemref *self)
{
    return ((t_uuid *) self->uuid)->hash;
}

static PyObject *t_itemref_repr(t_itemref *self)
{
    PyObject *str = self->uuid->ob_type->tp_str(self->uuid);
    PyObject *repr = PyString_FromFormat("<ref: (%sloaded) %s>",
                                         self->item ? "" : "not ",
                                         PyString_AsString(str));
    Py_DECREF(str);

    return repr;
}

static int t_itemref_cmp(t_itemref *self, t_itemref *other)
{
    if (!PyObject_TypeCheck(other, &ItemRefType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) other);
        return -1;
    }

    return PyObject_Compare(((t_uuid *) self->uuid)->uuid,
                            ((t_uuid *) other->uuid)->uuid);
}

static PyObject *t_itemref_richcmp(t_itemref *self, t_itemref *other, int opid)
{
    if (!PyObject_TypeCheck(other, &ItemRefType))
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    return PyObject_RichCompare(((t_uuid *) self->uuid)->uuid,
                                ((t_uuid *) other->uuid)->uuid, opid);
}

/* borrows reference */
t_item *_t_itemref_call(t_itemref *self)
{
    t_item *item = self->item;

    if (!item || item->status & STALE)
    {
        item = (t_item *) PyObject_GetItem(self->view, self->uuid);
        self->item = item;  /* weak reference, not counted */

        if (!item)
            return NULL;
        else
            Py_DECREF(item);
    }

    return item;
}

PyObject *t_itemref_call(t_itemref *self, PyObject *args, PyObject *kwds)
{
    t_item *item = self->item;

    if (!item || item->status & STALE)
    {
        int noError = 0;

        item = (t_item *) PyObject_GetItem(self->view, self->uuid);
        self->item = item;  /* weak reference, not counted */

        if (!item && args && !PyArg_ParseTuple(args, "|i", &noError))
            return NULL;

        if (noError && PyErr_ExceptionMatches(PyExc_KeyError))
        {
            PyErr_Clear();
            Py_INCREF(self);

            return (PyObject *) self;
        }
    }
    else
        Py_INCREF(item);

    return (PyObject *) item;
}


/* itsUUID */

static PyObject *t_itemref__getUUID(t_itemref *self, void *data)
{
    PyObject *uuid = self->uuid;

    Py_INCREF(uuid);
    return uuid;
}


/* itsView */

static PyObject *t_itemref__getView(t_itemref *self, void *data)
{
    PyObject *view = self->view;

    Py_INCREF(view);
    return view;
}


/* itsItem */

static PyObject *t_itemref__getItem(t_itemref *self, void *data)
{
    PyObject *item = (PyObject *) self->item;

    if (!item)
        item = Py_None;

    Py_INCREF(item);
    return item;
}


/* itsRef */

static PyObject *t_itemref__getRef(t_itemref *self, void *data)
{
    Py_INCREF(self);
    return (PyObject *) self;
}


static PyObject *t_itemref__isRefs(t_itemref *self)
{
    Py_RETURN_FALSE;
}


void _init_itemref(PyObject *m)
{
    if (PyType_Ready(&ItemRefType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&ItemRefType);
            PyModule_AddObject(m, "ItemRef", (PyObject *) &ItemRefType);
            ItemRef = &ItemRefType;
        }
    }
}
