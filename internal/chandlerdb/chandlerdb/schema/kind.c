
/*
 * The C kind type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include <Python.h>
#include "structmember.h"

#include "c.h"


typedef struct {
    PyObject_HEAD
    t_item *kind;
} t_kind;


static void t_kind_dealloc(t_kind *self);
static int t_kind_traverse(t_kind *self, visitproc visit, void *arg);
static int t_kind_clear(t_kind *self);
static PyObject *t_kind_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_kind_init(t_kind *self, PyObject *args, PyObject *kwds);

static PyObject *t_kind_getAttribute(t_kind *self, PyObject *args);


static PyMemberDef t_kind_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_kind_methods[] = {
    { "getAttribute", (PyCFunction) t_kind_getAttribute, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
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
    0,                                                   /* tp_getset */
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
        self->kind = NULL;

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
