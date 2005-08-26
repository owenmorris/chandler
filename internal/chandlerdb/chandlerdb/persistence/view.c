
/*
 * The view C type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include <Python.h>
#include "structmember.h"

#include "../item/item.h"

/*
 * t_item and t_view share the same top fields because
 * a view is also the parent of root items
 */

typedef struct {
    PyObject_HEAD
    Item_HEAD
    PyObject *repository;
} t_view;

enum {
    OPEN       = 0x0001,
    REFCOUNTED = 0x0002,
    LOADING    = 0x0004,
    COMMITTING = 0x0008,

    /*
     * flags from CItem
     * FDIRTY  = 0x0010
     * STALE   = 0x0080
     * CDIRTY  = 0x0200
     * merge flags
     */
};

static void t_view_dealloc(t_view *self);
static PyObject *t_view_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_view_init(t_view *self, PyObject *args, PyObject *kwds);
static PyObject *t_view__isRepository(t_view *self, PyObject *args);
static PyObject *t_view__isView(t_view *self, PyObject *args);
static PyObject *t_view__isItem(t_view *self, PyObject *args);
static PyObject *t_view_isNew(t_view *self, PyObject *args);
static PyObject *t_view_isStale(t_view *self, PyObject *args);
static PyObject *t_view_isRefCounted(t_view *self, PyObject *args);
static PyObject *t_view_isLoading(t_view *self, PyObject *args);
static PyObject *t_view__setLoading(t_view *self, PyObject *loading);
static PyObject *t_view_getLogger(t_view *self, PyObject *args);
static PyObject *t_view__getView(t_view *self, void *data);
static PyObject *t_view__getName(t_view *self, void *data);
static PyObject *t_view__getParent(t_view *self, void *data);
static PyObject *t_view__getVersion(t_view *self, void *data);
static int t_view__setVersion(t_view *self, PyObject *view, void *data);
static PyObject *t_view__getStore(t_view *self, void *data);
static PyObject *t_view__getLogger(t_view *self, void *data);

static PyObject *store_NAME;
static PyObject *refresh_NAME;
static PyObject *logger_NAME;

static PyMemberDef t_view_members[] = {
    { "_status", T_UINT, offsetof(t_view, status), 0, "view status flags" },
    { "_version", T_UINT, offsetof(t_view, version), 0, "view version" },
    { "repository", T_OBJECT, offsetof(t_view, repository), 0, "view repository" },
    { "name", T_OBJECT, offsetof(t_view, name), 0, "view name" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_view_methods[] = {
    { "_isRepository", (PyCFunction) t_view__isRepository, METH_NOARGS, "" },
    { "_isView", (PyCFunction) t_view__isView, METH_NOARGS, "" },
    { "_isItem", (PyCFunction) t_view__isItem, METH_NOARGS, "" },
    { "isView", (PyCFunction) t_view_isNew, METH_NOARGS, "" },
    { "isStale", (PyCFunction) t_view_isStale, METH_NOARGS, "" },
    { "isRefCounted", (PyCFunction) t_view_isRefCounted, METH_NOARGS, "" },
    { "isLoading", (PyCFunction) t_view_isLoading, METH_NOARGS, "" },
    { "_setLoading", (PyCFunction) t_view__setLoading, METH_O, "" },
    { "getLogger", (PyCFunction) t_view_getLogger, METH_NOARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_view_properties[] = {
    { "itsView", (getter) t_view__getView, NULL,
      "itsView property", NULL },
    { "itsName", (getter) t_view__getName, NULL,
      "itsName property", NULL },
    { "itsParent", (getter) t_view__getParent, NULL,
      "itsParent property", NULL },
    { "itsVersion", (getter) t_view__getVersion, (setter) t_view__setVersion,
      "itsVersion property", NULL },
    { "store", (getter) t_view__getStore, NULL,
      "store property", NULL },
    { "logger", (getter) t_view__getLogger, NULL,
      "logger property", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyMethodDef view_funcs[] = {
    { NULL, NULL, 0, NULL }
};

static PyTypeObject ViewType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.view.CView",                 /* tp_name */
    sizeof(t_view),                                      /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_view_dealloc,                          /* tp_dealloc */
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
    "C View type",                                       /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_view_methods,                                      /* tp_methods */
    t_view_members,                                      /* tp_members */
    t_view_properties,                                   /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_view_init,                               /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_view_new,                                 /* tp_new */
};


static void t_view_dealloc(t_view *self)
{
    Py_XDECREF(self->name);
    Py_XDECREF(self->repository);

    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_view_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

static int t_view_init(t_view *self, PyObject *args, PyObject *kwds)
{
    PyObject *repository, *name;

    if (!PyArg_ParseTuple(args, "OOk", &repository, &name, &self->version))
        return -1;

    self->status = 0;
    Py_INCREF(name); self->name = name;
    Py_INCREF(repository); self->repository = repository;

    return 0;
}


static PyObject *t_view__isRepository(t_view *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view__isView(t_view *self, PyObject *args)
{
    Py_RETURN_TRUE;
}

static PyObject *t_view__isItem(t_view *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view_isNew(t_view *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view_isStale(t_view *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view_isRefCounted(t_view *self, PyObject *args)
{
    if (self->status & REFCOUNTED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_isLoading(t_view *self, PyObject *args)
{
    if (self->status & LOADING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view__setLoading(t_view *self, PyObject *loading)
{
    PyObject *wasLoading = self->status & LOADING ? Py_True : Py_False;

    if (PyObject_IsTrue(loading))
        self->status |= LOADING;
    else
        self->status &= ~LOADING;

    Py_INCREF(wasLoading);
    return wasLoading;
}

static PyObject *t_view_getLogger(t_view *self, PyObject *args)
{
    return PyObject_GetAttr(self->repository, logger_NAME);
}


/* itsView */

static PyObject *t_view__getView(t_view *self, void *data)
{
    Py_INCREF(self);
    return (PyObject *) self;
}


/* itsName */

static PyObject *t_view__getName(t_view *self, void *data)
{
    Py_INCREF(self->name);
    return self->name;
}


/* itsParent */

static PyObject *t_view__getParent(t_view *self, void *data)
{
    Py_RETURN_NONE;
}


/* itsVersion */

static PyObject *t_view__getVersion(t_view *self, void *data)
{
    return PyInt_FromLong(self->version);
}

static int t_view__setVersion(t_view *self, PyObject *version, void *data)
{
    if (!PyObject_CallMethodObjArgs((PyObject *) self, refresh_NAME,
                                    Py_None, version, NULL))
        return -1;

    return 0;
}


/* store */

static PyObject *t_view__getStore(t_view *self, void *data)
{
    PyObject *repository = self->repository;

    if (repository != Py_None)
        return PyObject_GetAttr(repository, store_NAME);

    Py_RETURN_NONE;
}


/* logger */

static PyObject *t_view__getLogger(t_view *self, void *data)
{
    return PyObject_GetAttr(self->repository, logger_NAME);
}


static void PyDict_SetItemString_Int(PyObject *dict, char *key, int value)
{
    PyObject *pyValue = PyInt_FromLong(value);

    PyDict_SetItemString(dict, key, pyValue);
    Py_DECREF(pyValue);
}

void initview(void)
{
    if (PyType_Ready(&ViewType) >= 0)
    {
        PyObject *m = Py_InitModule3("view", view_funcs, "view C type module");

        if (m)
        {
            PyObject *dict = ViewType.tp_dict;

            Py_INCREF(&ViewType);
            PyModule_AddObject(m, "CView", (PyObject *) &ViewType);

            PyDict_SetItemString_Int(dict, "OPEN", OPEN);
            PyDict_SetItemString_Int(dict, "REFCOUNTED", REFCOUNTED);
            PyDict_SetItemString_Int(dict, "LOADING", LOADING);
            PyDict_SetItemString_Int(dict, "COMMITTING", COMMITTING);
            PyDict_SetItemString_Int(dict, "FDIRTY", FDIRTY);

            store_NAME = PyString_FromString("store");
            refresh_NAME = PyString_FromString("refresh");
            logger_NAME = PyString_FromString("logger");
        }
    }
}
