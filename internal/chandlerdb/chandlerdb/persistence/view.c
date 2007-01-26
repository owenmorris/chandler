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
#include "frameobject.h"

#include "c.h"

static void t_view_dealloc(t_view *self);
static int t_view_traverse(t_view *self, visitproc visit, void *arg);
static int t_view_clear(t_view *self);
static PyObject *t_view_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_view_init(t_view *self, PyObject *args, PyObject *kwds);
static PyObject *t_view_repr(t_view *self);
static PyObject *t_view__isRepository(t_view *self);
static PyObject *t_view__isView(t_view *self);
static PyObject *t_view__isItem(t_view *self);
static PyObject *t_view__isRecording(t_view *self);
static PyObject *t_view_isNew(t_view *self);
static PyObject *t_view_isStale(t_view *self);
static PyObject *t_view_isRefCounted(t_view *self);
static PyObject *t_view_isLoading(t_view *self);
static PyObject *t_view__setLoading(t_view *self, PyObject *loading);
static PyObject *t_view_isDeferringDelete(t_view *self);
static PyObject *t_view_deferDelete(t_view *self);
static PyObject *t_view_effectDelete(t_view *self);
static PyObject *t_view_cancelDelete(t_view *self);
static PyObject *t_view_isBackgroundIndexed(t_view *self);
static PyObject *t_view_setBackgroundIndexed(t_view *self, PyObject *arg);
static PyObject *t_view_isOpen(t_view *self);
static PyObject *t_view_isDebug(t_view *self);
static PyObject *t_view__isVerify(t_view *self);
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
static PyObject *t_view_debugOn(t_view *self, PyObject *arg);
static PyObject *t_view__unregisterItem(t_view *self, PyObject *args);

static Py_ssize_t t_view_dict_length(t_view *self);
static PyObject *t_view_dict_get(t_view *self, PyObject *key);

static PyObject *refresh_NAME;
static PyObject *_effectDelete_NAME;
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

static PyMemberDef t_view_members[] = {
    { "_status", T_UINT, offsetof(t_view, status), 0, "view status flags" },
    { "repository", T_OBJECT, offsetof(t_view, repository),
      0, "view repository" },
    { "name", T_OBJECT, offsetof(t_view, name), 0, "view name" },
    { "_changeNotifications", T_OBJECT, offsetof(t_view, changeNotifications),
      0, "" },
    { "_registry", T_OBJECT, offsetof(t_view, registry), 0, "" },
    { "_refRegistry", T_OBJECT, offsetof(t_view, refRegistry), 0, "" },
    { "_deletedRegistry", T_OBJECT, offsetof(t_view, deletedRegistry), 0, "" },
    { "_instanceRegistry", T_OBJECT, offsetof(t_view, instanceRegistry), 0, "" },
    { "_monitors", T_OBJECT, offsetof(t_view, monitors), 0, "" },
    { "_watchers", T_OBJECT, offsetof(t_view, watchers), 0, "" },
    { "_debugOn", T_OBJECT, offsetof(t_view, debugOn), 0, "" },
    { "_deferredDeletes", T_OBJECT, offsetof(t_view, deferredDeletes), 0, "" },
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
    { "isDeferringDelete", (PyCFunction) t_view_isDeferringDelete, METH_NOARGS, "" },
    { "deferDelete", (PyCFunction) t_view_deferDelete, METH_NOARGS, "" },
    { "effectDelete", (PyCFunction) t_view_effectDelete, METH_NOARGS, "" },
    { "cancelDelete", (PyCFunction) t_view_cancelDelete, METH_NOARGS, "" },
    { "isBackgroundIndexed", (PyCFunction) t_view_isBackgroundIndexed, METH_NOARGS, "" },
    { "setBackgroundIndexed", (PyCFunction) t_view_setBackgroundIndexed, METH_O, "" },
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
    { "debugOn", (PyCFunction) t_view_debugOn, METH_O, "" },
    { "_unregisterItem", (PyCFunction) t_view__unregisterItem, METH_VARARGS, "" },
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
    (lenfunc) t_view_dict_length,
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
    (reprfunc)t_view_repr,                               /* tp_repr */
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
    Py_VISIT(self->refRegistry);
    Py_VISIT(self->deletedRegistry);
    Py_VISIT(self->instanceRegistry);
    Py_VISIT(self->uuid);
    Py_VISIT(self->singletons);
    Py_VISIT(self->monitors);
    Py_VISIT(self->watchers);
    Py_VISIT(self->debugOn);
    Py_VISIT(self->deferredDeletes);

    return 0;
}

static int t_view_clear(t_view *self)
{
    Py_CLEAR(self->name);
    Py_CLEAR(self->repository);
    Py_CLEAR(self->changeNotifications);
    Py_CLEAR(self->registry);
    Py_CLEAR(self->refRegistry);
    Py_CLEAR(self->deletedRegistry);
    Py_CLEAR(self->instanceRegistry);
    Py_CLEAR(self->uuid);
    Py_CLEAR(self->singletons);
    Py_CLEAR(self->monitors);
    Py_CLEAR(self->watchers);
    Py_CLEAR(self->debugOn);
    Py_CLEAR(self->deferredDeletes);

    return 0;
}

static PyObject *t_view_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

static int t_view_init(t_view *self, PyObject *args, PyObject *kwds)
{
    PyObject *repository, *name, *uuid;

    if (!PyArg_ParseTuple(args, "OOO", &repository, &name, &uuid))
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

    self->version = 0;
    Py_INCREF(name); self->name = name;
    Py_INCREF(repository); self->repository = repository;
    Py_INCREF(Py_None); self->changeNotifications = Py_None;
    self->registry = NULL;
    self->refRegistry = NULL;
    self->deletedRegistry = NULL;
    self->instanceRegistry = NULL;
    Py_INCREF(uuid); self->uuid = uuid;
    self->singletons = PyDict_New();
    self->monitors = NULL;
    self->watchers = PyDict_New();
    self->debugOn = NULL;
    self->deferredDeletes = PyList_New(0);

    return 0;
}

static PyObject *t_view_repr(t_view *self)
{
    PyObject *format = PyString_FromString("<%s: %s (%d)>");
    PyObject *typeName = PyObject_GetAttrString((PyObject *) self->ob_type,
                                                "__name__");
    PyObject *version = PyLong_FromUnsignedLong(self->version);
    PyObject *args = PyTuple_Pack(3, typeName, self->name, version);
    PyObject *repr = PyString_Format(format, args);

    Py_DECREF(args);
    Py_DECREF(version);
    Py_DECREF(typeName);
    Py_DECREF(format);

    return repr;
}

static PyObject *t_view__isRepository(t_view *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view__isView(t_view *self)
{
    Py_RETURN_TRUE;
}

static PyObject *t_view__isItem(t_view *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view__isRecording(t_view *self)
{
    if (self->status & RECORDING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_isNew(t_view *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view_isStale(t_view *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_view_isRefCounted(t_view *self)
{
    if (self->status & REFCOUNTED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_isLoading(t_view *self)
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

static PyObject *t_view_isDeferringDelete(t_view *self)
{
    if (self->status & DEFERDEL)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_deferDelete(t_view *self)
{
    if (self->status & COMMITTING)
    {
        PyErr_SetString(PyExc_ValueError, "Cannot defer deletes during commit");
        return NULL;
    }

    self->status |= DEFERDEL;
    Py_RETURN_NONE;
}

static PyObject *t_view_effectDelete(t_view *self)
{
    if (self->status & DEFERDEL)
    {
        PyObject *items = self->deferredDeletes;
        int len = PyList_GET_SIZE(items);
        int i = -1;

        self->status &= ~DEFERDEL;

        while (++i < len) {
            PyObject *tuple = PyList_GET_ITEM(items, i);
            PyObject *item = PyTuple_GET_ITEM(tuple, 0);

            if (!(((t_item *) item)->status & DELETED))
            {
                PyObject *op = PyTuple_GET_ITEM(tuple, 1);
                PyObject *args = PyTuple_GET_ITEM(tuple, 2);
                PyObject *result =
                    PyObject_CallMethodObjArgs(item, _effectDelete_NAME,
                                               op, args, NULL);
                if (!result)
                    return NULL;
                Py_DECREF(result);
            }
        }

        PyList_SetSlice(items, 0, len, NULL);
    }

    Py_RETURN_NONE;
}

static PyObject *t_view_cancelDelete(t_view *self)
{
    if (self->status & DEFERDEL)
    {
        PyObject *items = self->deferredDeletes;
        int len = PyList_GET_SIZE(items);
        int i = -1;

        self->status &= ~DEFERDEL;

        while (++i < len) {
            PyObject *tuple = PyList_GET_ITEM(items, i);
            t_item *item = (t_item *) PyTuple_GET_ITEM(tuple, 0);
            item->status &= ~DEFERRED;
        }

        PyList_SetSlice(items, 0, len, NULL);
    }

    Py_RETURN_NONE;
}

static PyObject *t_view_isBackgroundIndexed(t_view *self)
{
    if (self->status & BGNDINDEX)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_setBackgroundIndexed(t_view *self, PyObject *arg)
{
    PyObject *value = t_view_isBackgroundIndexed(self);

    if (PyObject_IsTrue(arg))
        self->status |= BGNDINDEX;
    else
        self->status &= ~BGNDINDEX;

    return value;
}

static PyObject *t_view_isOpen(t_view *self)
{
    if (self->status & OPEN &&
        ((t_repository *) self->repository)->status & OPEN)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_isDebug(t_view *self)
{
    if (((t_repository *) self->repository)->status & DEBUG)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view__isVerify(t_view *self)
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
    if (value && PyObject_IsTrue(value))
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
    return PyLong_FromUnsignedLong(self->version);
}

static int t_view__setVersion(t_view *self, PyObject *version, void *data)
{
    PyObject *result =
        PyObject_CallMethodObjArgs((PyObject *) self, refresh_NAME,
                                   Py_None, version, NULL);

    if (!result)
        return -1;

    Py_DECREF(result);
    return 0;
}

static int t_view__set_version(t_view *self, PyObject *value, void *data)
{
    unsigned long version;

    if (PyInt_Check(value))
        version = PyInt_AS_LONG(value);
    else if (PyLong_Check(value))
        version = PyLong_AsUnsignedLong(value);
    else
    {
        PyErr_SetObject(PyExc_TypeError, value);
        return -1;
    }

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

static Py_ssize_t t_view_dict_length(t_view *self)
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
        PyDict_SetItem(self->singletons, key, ((t_item *) item)->ref->uuid);
    else if (PyUUID_Check(item))
        PyDict_SetItem(self->singletons, key, item);
    else
    {
        PyErr_SetObject(PyExc_TypeError, item);
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *_t_view_invokeMonitors(t_view *self, PyObject *args,
                                        PyObject *mode)
{
    PyObject *op, *attribute, *monitors, *changedItem;
    int argCount = PySequence_Size(args);
    int sysOnly = 0, userOnly = 0;

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
    changedItem = PyTuple_GET_ITEM(args, 1);
    attribute = PyTuple_GET_ITEM(args, 2);

    if (mode == Py_True)
    {
        sysOnly = 1;
        userOnly = 0;
    }
    else if (mode == Py_False)
    {
        sysOnly = 0;
        userOnly = 1;
    }

    monitors = PyDict_GetItem(PyDict_GetItem(self->monitors, op), attribute);
    if (monitors != NULL)
    {
        int size = PyList_Size(monitors);
        int i;

        if (PyObject_TypeCheck(changedItem, CItem))
        {
            if (!sysOnly)
                sysOnly = ((t_item *) changedItem)->status & SYSMONONLY;
        }
        else
        {
            PyErr_SetObject(PyExc_TypeError, changedItem);
            return NULL;
        }

        for (i = 0; i < size; i++) {
            t_item *monitor = (t_item *) PyList_GetItem(monitors, i);
            PyObject *monitoringItem, *callable, *result;
            PyObject *monitorArgs, *monitorKwds;
            int j, margCount = 0;

            if (monitor->status & (DEFERRING | DELETING))
                continue;

            if (sysOnly && !(monitor->status & SYSMONITOR))
                continue;
            if (userOnly && (monitor->status & SYSMONITOR))
                continue;

            monitoringItem = PyDict_GetItem(monitor->references->dict,
                                            item_NAME);
            if (monitoringItem == NULL)
                continue;

            if (monitoringItem->ob_type == ItemRef)
            {
                monitoringItem = PyObject_Call(monitoringItem, NULL, NULL);
                if (!monitoringItem)
                    return NULL;
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

static PyObject *t_view_invokeMonitors(t_view *self, PyObject *args)
{
    PyObject *monitorArgs, *mode = Py_None;

    if (!PyArg_ParseTuple(args, "O|O", &monitorArgs, &mode))
        return NULL;

    return _t_view_invokeMonitors(self, monitorArgs, mode);
}


static int _debugOn(PyObject *obj, PyFrameObject *frame,
                    int what, PyObject *arg)
{
    if (what == PyTrace_EXCEPTION)
    {
        PyObject *exc_type = PyTuple_GET_ITEM(arg, 0);

        if (PyErr_GivenExceptionMatches(exc_type, ((t_view *) obj)->debugOn))
        {
            PyObject *m = PyImport_ImportModule("chandlerdb.util.debugger");
            PyObject *fn = PyObject_GetAttrString(m, "set_trace");
            PyObject *result = PyObject_CallFunctionObjArgs(fn, obj, NULL);

            Py_XDECREF(result);
            Py_DECREF(fn);
            Py_DECREF(m);
        }
    }

    return 0;
}

static PyObject *t_view_debugOn(t_view *self, PyObject *arg)
{
    PyObject *debugOn = self->debugOn;

    if (arg == Py_None)
    {
        self->debugOn = NULL;
        PyEval_SetTrace(NULL, NULL);
    }
    else
    {
        Py_INCREF(arg);
        self->debugOn = arg;
        PyEval_SetTrace(_debugOn, (PyObject *) self);
    }

    if (debugOn)
        return debugOn;

    Py_RETURN_NONE;
}

int _t_view__unregisterItem(t_view *self, t_item *item, int reloadable)
{
    PyObject *uuid = item->ref->uuid;

    if (item->ref->view != (PyObject *) self)
    {
        PyErr_SetObject(PyExc_AssertionError, (PyObject *) item);
        return -1;
    }

    if (item->status & DELETING)
        PyDict_SetItem(self->deletedRegistry, uuid, (PyObject *) item);
    else if (reloadable)
        PyDict_SetItem(self->instanceRegistry, uuid, (PyObject *) item);

    if (PyDict_DelItem(self->registry, uuid) < 0)
        return -1;

    return 0;
}

static PyObject *t_view__unregisterItem(t_view *self, PyObject *args)
{
    PyObject *item;
    int reloadable;

    if (!PyArg_ParseTuple(args, "Oi", &item, &reloadable))
        return NULL;

    if (_t_view__unregisterItem(self, (t_item *) item, reloadable) < 0)
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
            PyDict_SetItemString_Int(dict, "DEFERDEL", DEFERDEL);
            PyDict_SetItemString_Int(dict, "FDIRTY", FDIRTY);
            PyDict_SetItemString_Int(dict, "RECORDING", RECORDING);
            PyDict_SetItemString_Int(dict, "REFRESHING", REFRESHING);
            PyDict_SetItemString_Int(dict, "VERIFY", VERIFY);
            PyDict_SetItemString_Int(dict, "COMMITREQ", COMMITREQ);

            refresh_NAME = PyString_FromString("refresh");
            _effectDelete_NAME = PyString_FromString("_effectDelete");
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

            MONITORS_PATH = PyString_FromString("//Schema/Core/items/Monitors");
            PyDict_SetItemString(dict, "MONITORS", MONITORS_PATH);

            cobj = PyCObject_FromVoidPtr(_t_view_invokeMonitors, NULL);
            PyModule_AddObject(m, "_t_view_invokeMonitors", cobj);
        }
    }
}

