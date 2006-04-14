
/*
 * The view C type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include <Python.h>
#include "structmember.h"

#include "c.h"
#include "../util/singleref.h"

static void t_view_dealloc(t_view *self);
static int t_view_traverse(t_view *self, visitproc visit, void *arg);
static int t_view_clear(t_view *self);
static PyObject *t_view_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_view_init(t_view *self, PyObject *args, PyObject *kwds);
static PyObject *t_view__isRepository(t_view *self, PyObject *args);
static PyObject *t_view__isView(t_view *self, PyObject *args);
static PyObject *t_view__isItem(t_view *self, PyObject *args);
static PyObject *t_view__isRecording(t_view *self, PyObject *args);
static PyObject *t_view_isNew(t_view *self, PyObject *args);
static PyObject *t_view_isStale(t_view *self, PyObject *args);
static PyObject *t_view_isRefCounted(t_view *self, PyObject *args);
static PyObject *t_view_isLoading(t_view *self, PyObject *args);
static PyObject *t_view__setLoading(t_view *self, PyObject *loading);
static PyObject *t_view_isOpen(t_view *self, PyObject *args);
static PyObject *t_view_isDebug(t_view *self, PyObject *args);
static PyObject *t_view__isVerify(t_view *self, PyObject *args);
static PyObject *t_view__setVerify(t_view *self, PyObject *args);
static PyObject *t_view_getLogger(t_view *self, PyObject *args);
static PyObject *t_view__notifyChange(t_view *self, PyObject *args,
                                      PyObject *kwds);
static PyObject *t_view__getView(t_view *self, void *data);
static PyObject *t_view__getName(t_view *self, void *data);
static PyObject *t_view__getParent(t_view *self, void *data);
static PyObject *t_view__getVersion(t_view *self, void *data);
static int t_view__setVersion(t_view *self, PyObject *value, void *data);
static int t_view__set_version(t_view *self, PyObject *value, void *data);
static PyObject *t_view__getStore(t_view *self, void *data);
static PyObject *t_view__getLogger(t_view *self, void *data);
static PyObject *t_view__getMONITORING(t_view *self, void *data);
static int t_view__setMONITORING(t_view *self, PyObject *value, void *data);
static PyObject *t_view_find(t_view *self, PyObject *args);
static PyObject *t_view_getSingleton(t_view *self, PyObject *key);
static PyObject *t_view_setSingleton(t_view *self, PyObject *args);
static PyObject *t_view_invokeMonitors(t_view *self, PyObject *args);
static PyObject *t_view_invokeWatchers(t_view *self, PyObject *args);

static int t_view_dict_length(t_view *self);
static PyObject *t_view_dict_get(t_view *self, PyObject *key);

static PyObject *refresh_NAME;
static PyObject *logger_NAME;
static PyObject *_loadItem_NAME;
static PyObject *_readItem_NAME;
static PyObject *getRoot_NAME;
static PyObject *_fwalk_NAME;
static PyObject *findPath_NAME;
static PyObject *cacheMonitors_NAME;
static PyObject *method_NAME;
static PyObject *args_NAME, *kwds_NAME;
static PyObject *item_NAME;
static PyObject *MONITORS_PATH;
static PyObject *sourceChanged_NAME;
static PyObject *set_NAME, *kind_NAME, *collection_NAME;

static PyMemberDef t_view_members[] = {
    { "_status", T_UINT, offsetof(t_view, status), 0, "view status flags" },
    { "repository", T_OBJECT, offsetof(t_view, repository),
      0, "view repository" },
    { "name", T_OBJECT, offsetof(t_view, name), 0, "view name" },
    { "_changeNotifications", T_OBJECT, offsetof(t_view, changeNotifications),
      0, "" },
    { "_registry", T_OBJECT, offsetof(t_view, registry), 0, "" },
    { "_deletedRegistry", T_OBJECT, offsetof(t_view, deletedRegistry), 0, "" },
    { "_monitors", T_OBJECT, offsetof(t_view, monitors), 0, "" },
    { "_watcherDispatch", T_OBJECT, offsetof(t_view, watcherDispatch), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_view_methods[] = {
    { "_isRepository", (PyCFunction) t_view__isRepository, METH_NOARGS, "" },
    { "_isView", (PyCFunction) t_view__isView, METH_NOARGS, "" },
    { "_isItem", (PyCFunction) t_view__isItem, METH_NOARGS, "" },
    { "_isRecording", (PyCFunction) t_view__isRecording, METH_NOARGS, "" },
    { "isView", (PyCFunction) t_view_isNew, METH_NOARGS, "" },
    { "isStale", (PyCFunction) t_view_isStale, METH_NOARGS, "" },
    { "isRefCounted", (PyCFunction) t_view_isRefCounted, METH_NOARGS, "" },
    { "isLoading", (PyCFunction) t_view_isLoading, METH_NOARGS, "" },
    { "_setLoading", (PyCFunction) t_view__setLoading, METH_O, "" },
    { "isOpen", (PyCFunction) t_view_isOpen, METH_NOARGS, "" },
    { "isDebug", (PyCFunction) t_view_isDebug, METH_NOARGS, "" },
    { "_isVerify", (PyCFunction) t_view__isVerify, METH_NOARGS, "" },
    { "_setVerify", (PyCFunction) t_view__setVerify, METH_O, "" },
    { "getLogger", (PyCFunction) t_view_getLogger, METH_NOARGS, "" },
    { "_notifyChange", (PyCFunction) t_view__notifyChange, METH_VARARGS|METH_KEYWORDS, "" },
    { "find", (PyCFunction) t_view_find, METH_VARARGS, NULL },
    { "getSingleton", (PyCFunction) t_view_getSingleton, METH_O, NULL },
    { "setSingleton", (PyCFunction) t_view_setSingleton, METH_VARARGS, "" },
    { "invokeMonitors", (PyCFunction) t_view_invokeMonitors, METH_VARARGS, "" },
    { "invokeWatchers", (PyCFunction) t_view_invokeWatchers, METH_VARARGS, "" },
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
    { "_version", (getter) t_view__getVersion, (setter) t_view__set_version,
      "_version property", NULL },
    { "store", (getter) t_view__getStore, NULL,
      "store property", NULL },
    { "logger", (getter) t_view__getLogger, NULL,
      "logger property", NULL },
    { "MONITORING",
      (getter) t_view__getMONITORING,
      (setter) t_view__setMONITORING,
      "MONITORING flag", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyMappingMethods t_view_as_mapping = {
    (inquiry) t_view_dict_length,
    (binaryfunc) t_view_dict_get,
    (objobjargproc) NULL
};

static PyTypeObject ViewType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.CView",                    /* tp_name */
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
    &t_view_as_mapping,                                  /* tp_as_mapping */
    0,                                                   /* tp_hash  */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    0,                                                   /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                                /* tp_flags */
    "C View type",                                       /* tp_doc */
    (traverseproc)t_view_traverse,                       /* tp_traverse */
    (inquiry)t_view_clear,                               /* tp_clear */
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
    t_view_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_view_traverse(t_view *self, visitproc visit, void *arg)
{
    Py_VISIT(self->name);
    Py_VISIT(self->repository);
    Py_VISIT(self->changeNotifications);
    Py_VISIT(self->registry);
    Py_VISIT(self->deletedRegistry);
    Py_VISIT(self->uuid);
    Py_VISIT(self->monitors);
    Py_VISIT(self->singletons);
    Py_VISIT(self->watcherDispatch);

    return 0;
}

static int t_view_clear(t_view *self)
{
    Py_CLEAR(self->name);
    Py_CLEAR(self->repository);
    Py_CLEAR(self->changeNotifications);
    Py_CLEAR(self->registry);
    Py_CLEAR(self->deletedRegistry);
    Py_CLEAR(self->uuid);
    Py_CLEAR(self->monitors);
    Py_CLEAR(self->singletons);
    Py_CLEAR(self->watcherDispatch);

    return 0;
}

static PyObject *t_view_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

static int t_view_init(t_view *self, PyObject *args, PyObject *kwds)
{
    PyObject *repository, *name, *uuid;

    if (!PyArg_ParseTuple(args, "OOLO", &repository, &name, &self->version,
                          &uuid))
        return -1;

    if (PyObject_TypeCheck(repository, CRepository))
        self->status = ((t_repository *) repository)->status & VERIFY;
    else if (repository == Py_None)
        self->status = 0;
    else
    {
        PyErr_SetObject(PyExc_TypeError, repository);
        return -1;
    }

    Py_INCREF(name); self->name = name;
    Py_INCREF(repository); self->repository = repository;
    Py_INCREF(Py_None); self->changeNotifications = Py_None;
    self->registry = NULL;
    self->deletedRegistry = NULL;
    Py_INCREF(uuid); self->uuid = uuid;
    self->monitors = NULL;
    self->singletons = PyDict_New();
    self->watcherDispatch = NULL;

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

static PyObject *t_view__isRecording(t_view *self, PyObject *args)
{
    if (self->status & RECORDING)
        Py_RETURN_TRUE;
    else
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

static PyObject *t_view_isOpen(t_view *self, PyObject *args)
{
    if (self->status & OPEN &&
        ((t_repository *) self->repository)->status & OPEN)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_isDebug(t_view *self, PyObject *args)
{
    if (((t_repository *) self->repository)->status & DEBUG)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view__isVerify(t_view *self, PyObject *args)
{
    if (self->status & VERIFY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view__setVerify(t_view *self, PyObject *arg)
{
    PyObject *result = self->status & VERIFY ? Py_True : Py_False;

    if (PyObject_IsTrue(arg))
        self->status |= VERIFY;
    else
        self->status &= ~VERIFY;

    Py_INCREF(result);
    return result;
}

static PyObject *t_view_getLogger(t_view *self, PyObject *args)
{
    return PyObject_GetAttr(self->repository, logger_NAME);
}

static PyObject *t_view__getMONITORING(t_view *self, void *data)
{
    if (self->status & MONITORING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static int t_view__setMONITORING(t_view *self, PyObject *value, void *data)
{
    if (PyObject_IsTrue(value))
        self->status |= MONITORING;
    else
        self->status &= ~MONITORING;

    return 0;
}


static PyObject *t_view__notifyChange(t_view *self, PyObject *args,
                                      PyObject *kwds)
{
    PyObject *callable = PyTuple_GetItem(args, 0); /* borrowed */
    PyObject *callArgs = PyTuple_GetSlice(args, 1, PyTuple_GET_SIZE(args));
    int ok;

    if (self->status & RECORDING)
    {
        int noKwds = kwds == NULL;
        PyObject *tuple;

        if (noKwds)
            kwds = PyDict_New();

        tuple = PyTuple_Pack(3, callable, callArgs, kwds);
        ok = PyList_Append(self->changeNotifications, tuple) == 0;

        if (noKwds) {
            Py_DECREF(kwds);
        }
        Py_DECREF(tuple);
    }
    else
        ok = PyObject_Call(callable, callArgs, kwds) != NULL;

    Py_DECREF(callArgs);

    if (ok)
        Py_RETURN_NONE;
    else
        return NULL;
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


/* itsVersion, _version */

static PyObject *t_view__getVersion(t_view *self, void *data)
{
    return PyLong_FromUnsignedLongLong(self->version);
}

static int t_view__setVersion(t_view *self, PyObject *version, void *data)
{
    if (!PyObject_CallMethodObjArgs((PyObject *) self, refresh_NAME,
                                    Py_None, version, NULL))
        return -1;

    return 0;
}

static int t_view__set_version(t_view *self, PyObject *value, void *data)
{
    unsigned long long version = PyLong_AsUnsignedLongLong(value);
    
    if (PyErr_Occurred())
        return -1;

    self->version = version;
    
    return 0;
}


/* store */

static PyObject *t_view__getStore(t_view *self, void *data)
{
    PyObject *repository = self->repository;

    if (PyObject_TypeCheck(repository, CRepository))
    {
        PyObject *store = ((t_repository *) repository)->store;

        Py_INCREF(store);
        return store;
    }

    PyErr_SetObject(PyExc_TypeError, repository);
    return NULL;
}


/* logger */

static PyObject *t_view__getLogger(t_view *self, void *data)
{
    return PyObject_GetAttr(self->repository, logger_NAME);
}


/* as_mapping (read-only) */

static int t_view_dict_length(t_view *self)
{
    return PyDict_Size(self->registry);
}

static PyObject *t_view_dict_get(t_view *self, PyObject *key)
{
    if (PyUUID_Check(key))
    {
        PyObject *item;

        if (!PyObject_Compare(key, self->uuid))
        {
            Py_INCREF(self);
            return (PyObject *) self;
        }

        item = PyDict_GetItem(self->registry, key);
        if (item == NULL)
        {
            item = PyObject_CallMethodObjArgs((PyObject *) self,
                                              _loadItem_NAME, key, NULL);

            if (item == NULL)
                return NULL;

            if (item == Py_None)
            {
                Py_DECREF(item);
                PyErr_SetObject(PyExc_KeyError, key);

                return NULL;
            }
        }
        else
            Py_INCREF(item);

        return item;
    }

    if (PyString_Check(key) || PyUnicode_Check(key))
    {
        PyObject *root = PyObject_CallMethodObjArgs((PyObject *) self,
                                                    getRoot_NAME, key, NULL);

        if (root == NULL)
            return NULL;

        if (root == Py_None)
        {
            Py_DECREF(root);
            PyErr_SetObject(PyExc_KeyError, key);

            return NULL;
        }
            
        return root;
    }

    PyErr_SetObject(PyExc_TypeError, key);
    return NULL;
}


static PyObject *t_view_find(t_view *self, PyObject *args)
{
    PyObject *spec, *load = Py_True;

    if (!PyArg_ParseTuple(args, "O|O", &spec, &load))
        return NULL;

    if (PyUUID_Check(spec))
    {
        PyObject *item;

        if (!PyObject_Compare(spec, self->uuid))
        {
            Py_INCREF(self);
            return (PyObject *) self;
        }

        item = PyDict_GetItem(self->registry, spec);
        if (item != NULL)
        {
            Py_INCREF(item);
            return item;
        }
        else
        {
            if (load == Py_True)
                return PyObject_CallMethodObjArgs((PyObject *) self,
                                                  _loadItem_NAME, spec, NULL);

            if (PyObject_IsTrue(load) &&
                !PyDict_Contains(self->deletedRegistry, spec))
            {
                /* in this case, load is an itemReader (queryItems) */
                return PyObject_CallMethodObjArgs((PyObject *) self,
                                                  _readItem_NAME, load, NULL);
            }

            Py_RETURN_NONE;
        }
    }
     
    return PyObject_CallMethodObjArgs((PyObject *) self,
                                      _fwalk_NAME, spec, NULL);
}


static PyObject *t_view_getSingleton(t_view *self, PyObject *key)
{
    PyObject *uuid = PyDict_GetItem(self->singletons, key);

    if (uuid != NULL)
        return t_view_dict_get(self, uuid);

    return PyObject_CallMethodObjArgs((PyObject *) self,
                                      findPath_NAME, key, NULL);
}

static PyObject *t_view_setSingleton(t_view *self, PyObject *args)
{
    PyObject *key, *item;

    if (!PyArg_ParseTuple(args, "OO", &key, &item))
        return NULL;

    if (item == Py_None)
    {
        if (PyDict_Contains(self->singletons, key))
            PyDict_DelItem(self->singletons, key);
    }
    else if (PyObject_TypeCheck(item, CItem))
        PyDict_SetItem(self->singletons, key, ((t_item *) item)->uuid);
    else if (PyUUID_Check(item))
        PyDict_SetItem(self->singletons, key, item);
    else
    {
        PyErr_SetObject(PyExc_TypeError, item);
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *t_view_invokeMonitors(t_view *self, PyObject *args)
{
    PyObject *op, *attribute, *monitors;
    int argCount = PySequence_Size(args);

    if (argCount < 3)
    {
        PyErr_SetString(PyExc_TypeError, "missing args");
        return NULL;
    }

    if (!(self->status & MONITORING))
    {
        PyObject *singleton = t_view_getSingleton(self, MONITORS_PATH);
        PyObject *result;

        if (singleton == NULL)
            return NULL;

        if (singleton == Py_None) /* during core schema loading */
            return singleton;

        result = PyObject_CallMethodObjArgs(singleton,
                                            cacheMonitors_NAME, NULL);
        Py_DECREF(singleton);

        if (result == NULL)
            return NULL;

        Py_DECREF(result);
    }

    args = PySequence_Tuple(args);
    op = PyTuple_GET_ITEM(args, 0);
    attribute = PyTuple_GET_ITEM(args, 2);

    monitors = PyDict_GetItem(PyDict_GetItem(self->monitors, op), attribute);
    if (monitors != NULL)
    {
        int size = PyList_Size(monitors);
        int i;

        for (i = 0; i < size; i++) {
            t_item *monitor = (t_item *) PyList_GetItem(monitors, i);
            PyObject *monitoringItem, *callable, *result;
            PyObject *monitorArgs, *monitorKwds;
            int j, margCount = 0;

            if (monitor->status & DELETING)
                continue;

            monitoringItem = PyDict_GetItem(monitor->references->dict,
                                            item_NAME);
            if (monitoringItem == NULL)
                continue;

            if (PyUUID_Check(monitoringItem))
            {
                monitoringItem = t_view_dict_get(self, monitoringItem);
                if (monitoringItem == NULL)
                {
                    Py_DECREF(args);
                    return NULL;
                }
            }
            else
                Py_INCREF(monitoringItem);

            callable = PyDict_GetItem(monitor->values->dict, method_NAME);
            if (callable == NULL)
            {
                Py_DECREF(args);
                Py_DECREF(monitoringItem);
                PyErr_SetObject(PyExc_AttributeError, method_NAME);
                return NULL;
            }

            callable = PyObject_GetAttr(monitoringItem, callable);
            Py_DECREF(monitoringItem);
            if (callable == NULL)
            {
                Py_DECREF(args);
                return NULL;
            }

            monitorArgs = PyDict_GetItem(monitor->values->dict, args_NAME);
            if (monitorArgs != NULL)
                margCount = PySequence_Size(monitorArgs);

            monitorKwds = PyDict_GetItem(monitor->values->dict, kwds_NAME);

            if (self->status & RECORDING)
            {
                PyObject *_args = PyTuple_New(argCount + 1 + margCount);

                PyTuple_SET_ITEM(_args, 0, callable);
                for (j = 0; j < argCount; j++) {
                    PyObject *o = PyTuple_GET_ITEM(args, j);
                    Py_INCREF(o);
                    PyTuple_SET_ITEM(_args, j + 1, o);
                }

                if (margCount > 0)
                    for (j = 0; j < margCount; j++) {
                        PyObject *o = PySequence_GetItem(monitorArgs, j);
                        PyTuple_SET_ITEM(_args, j + 1 + argCount, o);
                    }

                result = t_view__notifyChange(self, _args, monitorKwds);
                Py_DECREF(_args);

                if (result == NULL)
                {
                    Py_DECREF(args);
                    return NULL;
                }
            }
            else
            {
                PyObject *_args;

                if (margCount > 0)
                {
                    _args = PyTuple_New(argCount + margCount);

                    for (j = 0; j < argCount; j++) {
                        PyObject *o = PyTuple_GET_ITEM(args, j);
                        Py_INCREF(o);
                        PyTuple_SET_ITEM(_args, j, o);
                    }
                    for (j = 0; j < margCount; j++) {
                        PyObject *o = PySequence_GetItem(monitorArgs, j);
                        PyTuple_SET_ITEM(_args, j + argCount, o);
                    }
                }
                else
                {
                    _args = args;
                    Py_INCREF(args);
                }

                result = PyObject_Call(callable, _args, monitorKwds);
                Py_DECREF(_args);

                if (result == NULL)
                {
                    Py_DECREF(args);
                    return NULL;
                }
            }

            Py_DECREF(result);
        }
    }

    Py_DECREF(args);
    Py_RETURN_NONE;
}

static int _t_view_invokeWatchers(t_view *self, PyObject *watchers,
                                  PyObject *op, PyObject *change,
                                  PyObject *owner, PyObject *name,
                                  PyObject *other)
{
    PyObject *dict, *key, *value;
    int pos = 0;

    if (!PyAnySet_Check(watchers))
    {
        PyErr_SetObject(PyExc_TypeError, watchers);
        return -1;
    }

    /* a set's dict is organized as { value: True } */
    dict = ((PySetObject *) watchers)->data;

    while (PyDict_Next(dict, &pos, &key, &value)) {
        PyObject *watcher = PyTuple_GetItem(key, 0);
        PyObject *watch = PyTuple_GetItem(key, 1);

        if (!watcher || !watch)
            return -1;

        if (PyObject_TypeCheck(watcher, SingleRef))
            watcher = t_view_dict_get(self, ((t_sr *) watcher)->uuid);
        else if (PyUUID_Check(watcher))
            watcher = t_view_dict_get(self, watcher);
        else
        {
            PyErr_SetObject(PyExc_TypeError, watcher);
            return -1;
        }

        if (!watcher)
        {
            if (PyErr_Occurred() == PyExc_KeyError)
            {
                PyErr_Clear();
                continue;
            }
            return -1;
        }

        if (!PyObject_Compare(watch, set_NAME))
        {
            PyObject *attrName = PyTuple_GetItem(key, 2);
            PyObject *set = PyObject_GetAttr(watcher, attrName);
            PyObject *result;

            if (!set)
            {
                Py_DECREF(watcher);
                return -1;
            }

            result = PyObject_CallMethodObjArgs(set, sourceChanged_NAME,
                                                op, change, owner, name,
                                                Py_False, other, NULL);
            Py_DECREF(watcher);
            Py_DECREF(set);

            if (!result)
                return -1;
            Py_DECREF(result);
        }
        else if (!PyObject_Compare(watch, kind_NAME))
        {
            PyObject *methName = PyTuple_GetItem(key, 2);
            PyObject *result, *kind;

            if (PyUUID_Check(owner))
            {
                PyObject *extent = t_view_dict_get(self, owner);

                if (!extent)
                {
                    Py_DECREF(watcher);
                    return -1;
                }

                kind = PyObject_GetAttr(extent, kind_NAME);
                Py_DECREF(extent);
            }
            else
                kind = PyObject_GetAttr(owner, kind_NAME);

            if (!kind)
            {
                Py_DECREF(watcher);
                return -1;
            }

            result = PyObject_CallMethodObjArgs(watcher, methName,
                                                op, kind, other, NULL);
            Py_DECREF(kind);
            Py_DECREF(watcher);

            if (!result)
                return -1;
            Py_DECREF(result);
        }
        else if (!PyObject_Compare(watch, collection_NAME))
        {
            PyObject *methName = PyTuple_GetItem(key, 2);
            PyObject *result =
                PyObject_CallMethodObjArgs(watcher, methName,
                                           op, owner, name, other, NULL);

            Py_DECREF(watcher);
            if (!result)
                return -1;
            Py_DECREF(result);
        }
        else
            Py_DECREF(watcher);
    }

    return 0;
}

static PyObject *t_view_invokeWatchers(t_view *self, PyObject *args)
{
    PyObject *watchers, *op, *change, *owner, *name, *other;

    if (!PyArg_ParseTuple(args, "OOOOOO", &watchers, &op, &change,
                          &owner, &name, &other))
        return NULL;

    if (_t_view_invokeWatchers(self, watchers, op, change,
                               owner, name, other) < 0)
        return NULL;

    Py_RETURN_NONE;
}


void _init_view(PyObject *m)
{
    if (PyType_Ready(&ViewType) >= 0)
    {
        if (m)
        {
            PyObject *dict = ViewType.tp_dict;
            PyObject *cobj;

            Py_INCREF(&ViewType);
            PyModule_AddObject(m, "CView", (PyObject *) &ViewType);
            CView = &ViewType;

            PyDict_SetItemString_Int(dict, "OPEN", OPEN);
            PyDict_SetItemString_Int(dict, "REFCOUNTED", REFCOUNTED);
            PyDict_SetItemString_Int(dict, "LOADING", LOADING);
            PyDict_SetItemString_Int(dict, "COMMITTING", COMMITTING);
            PyDict_SetItemString_Int(dict, "FDIRTY", FDIRTY);
            PyDict_SetItemString_Int(dict, "RECORDING", RECORDING);
            PyDict_SetItemString_Int(dict, "VERIFY", VERIFY);

            refresh_NAME = PyString_FromString("refresh");
            logger_NAME = PyString_FromString("logger");
            _loadItem_NAME = PyString_FromString("_loadItem");
            _readItem_NAME = PyString_FromString("_readItem");
            getRoot_NAME = PyString_FromString("getRoot");
            _fwalk_NAME = PyString_FromString("_fwalk");
            findPath_NAME = PyString_FromString("findPath");
            cacheMonitors_NAME = PyString_FromString("cacheMonitors");
            method_NAME = PyString_FromString("method");
            args_NAME = PyString_FromString("args");
            kwds_NAME = PyString_FromString("kwds");
            item_NAME = PyString_FromString("item");
            sourceChanged_NAME = PyString_FromString("sourceChanged");
            set_NAME = PyString_FromString("set");
            kind_NAME = PyString_FromString("kind");
            collection_NAME = PyString_FromString("collection");

            MONITORS_PATH = PyString_FromString("//Schema/Core/items/Monitors");
            PyDict_SetItemString(dict, "MONITORS", MONITORS_PATH);

            cobj = PyCObject_FromVoidPtr(t_view_invokeMonitors, NULL);
            PyModule_AddObject(m, "CView_invokeMonitors", cobj);
            cobj = PyCObject_FromVoidPtr(_t_view_invokeWatchers, NULL);
            PyModule_AddObject(m, "CView_invokeWatchers", cobj);
        }
    }
}
