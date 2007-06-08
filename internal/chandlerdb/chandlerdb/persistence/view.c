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
static PyObject *t_view__getStatus(t_view *self, void *data);
static PyObject *t_view__getStore(t_view *self, void *data);
static PyObject *t_view__getLogger(t_view *self, void *data);
static PyObject *t_view__getMONITORING(t_view *self, void *data);
static int t_view__setMONITORING(t_view *self, PyObject *value, void *data);
static PyObject *t_view_get(t_view *self, PyObject *arg);
static PyObject *t_view_find(t_view *self, PyObject *args);
static PyObject *t_view_getSingleton(t_view *self, PyObject *key);
static PyObject *t_view_setSingleton(t_view *self, PyObject *args);
static PyObject *t_view_invokeMonitors(t_view *self, PyObject *args);
static PyObject *t_view_debugOn(t_view *self, PyObject *arg);
static PyObject *t_view__unregisterItem(t_view *self, PyObject *args);
static PyObject *t_view_isReindexingDeferred(t_view *self);
static PyObject *t_view_reindexingDeferred(t_view *self);
static PyObject *t_view__deferIndexMonitor(t_view *self, PyObject *arg);
static PyObject *t_view_areObserversDeferred(t_view *self);
static PyObject *t_view_observersDeferred(t_view *self, PyObject *args);
static PyObject *t_view_areNotificationsDeferred(t_view *self);
static PyObject *t_view_notificationsDeferred(t_view *self, PyObject *args);
static PyObject *t_view_cancelDeferredNotifications(t_view *self);
static PyObject *t_view_isCommitDeferred(t_view *self);
static PyObject *t_view_commitDeferred(t_view *self, PyObject *args);
static PyObject *t_view_cancelDeferredCommits(t_view *self);
static PyObject *t_view_findValues(t_view *self, PyObject *args);
static PyObject *t_view_findInheritedValues(t_view *self, PyObject *args);

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
static PyObject *MONITORS_PATH;
static PyObject *reindex_NAME;
static PyObject *loadValues_NAME;
static PyObject *readValue_NAME;
static PyObject *inheritFrom_NAME;
static PyObject *commit_NAME;

static PyMemberDef t_view_members[] = {
    { "_status", T_UINT, offsetof(t_view, status), 0, "view status flags" },
    { "repository", T_OBJECT, offsetof(t_view, repository),
      0, "view repository" },
    { "name", T_OBJECT, offsetof(t_view, name), 0, "view name" },
    { "_registry", T_OBJECT, offsetof(t_view, registry), 0, "" },
    { "_refRegistry", T_OBJECT, offsetof(t_view, refRegistry), 0, "" },
    { "_deletedRegistry", T_OBJECT, offsetof(t_view, deletedRegistry), 0, "" },
    { "_instanceRegistry", T_OBJECT, offsetof(t_view, instanceRegistry), 0, "" },
    { "_monitors", T_OBJECT, offsetof(t_view, monitors), 0, "" },
    { "_watchers", T_OBJECT, offsetof(t_view, watchers), 0, "" },
    { "_debugOn", T_OBJECT, offsetof(t_view, debugOn), 0, "" },
    { "_deferredDeletes", T_OBJECT, offsetof(t_view, deferredDeletes), 0, "" },
    { "_deferredIndexingCtx", T_OBJECT, offsetof(t_view, deferredIndexingCtx), READONLY, "" },
    { "_deferredObserversCtx", T_OBJECT, offsetof(t_view, deferredObserversCtx), READONLY, "" },
    { "_deferredNotificationsCtx", T_OBJECT, offsetof(t_view, deferredNotificationsCtx), READONLY, "" },
    { "_deferredCommitCtx", T_OBJECT, offsetof(t_view, deferredCommitCtx), READONLY, "" },
    { "refreshErrors", T_UINT, offsetof(t_view, refreshErrors), 0, "" },
    { "pruneSize", T_UINT, offsetof(t_view, pruneSize), 0, "" },
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
    { "get", (PyCFunction) t_view_get, METH_O, NULL },
    { "find", (PyCFunction) t_view_find, METH_VARARGS, NULL },
    { "getSingleton", (PyCFunction) t_view_getSingleton, METH_O, NULL },
    { "setSingleton", (PyCFunction) t_view_setSingleton, METH_VARARGS, "" },
    { "invokeMonitors", (PyCFunction) t_view_invokeMonitors, METH_VARARGS, "" },
    { "debugOn", (PyCFunction) t_view_debugOn, METH_O, "" },
    { "_unregisterItem", (PyCFunction) t_view__unregisterItem, METH_VARARGS, "" },
    { "isReindexingDeferred", (PyCFunction) t_view_isReindexingDeferred, METH_NOARGS, "" },
    { "reindexingDeferred", (PyCFunction) t_view_reindexingDeferred, METH_NOARGS, "" },
    { "_deferIndexMonitor", (PyCFunction) t_view__deferIndexMonitor, METH_O, "" },
    { "areObserversDeferred", (PyCFunction) t_view_areObserversDeferred, METH_NOARGS, "" },
    { "observersDeferred", (PyCFunction) t_view_observersDeferred, METH_VARARGS, "" },
    { "areNotificationsDeferred", (PyCFunction) t_view_areNotificationsDeferred, METH_VARARGS, "" },
    { "notificationsDeferred", (PyCFunction) t_view_notificationsDeferred, METH_VARARGS, "" },
    { "cancelDeferredNotifications", (PyCFunction) t_view_cancelDeferredNotifications, METH_NOARGS, "" },
    { "isCommitDeferred", (PyCFunction) t_view_isCommitDeferred, METH_VARARGS, "" },
    { "commitDeferred", (PyCFunction) t_view_commitDeferred, METH_VARARGS, "" },
    { "cancelDeferredCommits", (PyCFunction) t_view_cancelDeferredCommits, METH_NOARGS, "" },
    { "findValues", (PyCFunction) t_view_findValues, METH_VARARGS, NULL },
    { "findInheritedValues", (PyCFunction) t_view_findInheritedValues, METH_VARARGS, NULL },
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
    { "itsStatus", (getter) t_view__getStatus, NULL,
      "itsStatus property", NULL },
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
    Py_VISIT(self->deferredIndexingCtx);
    Py_VISIT(self->deferredNotificationsCtx);
    Py_VISIT(self->deferredCommitCtx);

    return 0;
}

static int t_view_clear(t_view *self)
{
    Py_CLEAR(self->name);
    Py_CLEAR(self->repository);
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
    Py_CLEAR(self->deferredIndexingCtx);
    Py_CLEAR(self->deferredNotificationsCtx);
    Py_CLEAR(self->deferredCommitCtx);

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
        int i;

        self->status &= ~DEFERDEL;

        for (i = 0; i < len; i++) {
            PyObject *tuple = PyList_GET_ITEM(items, i);
            PyObject *item = PyTuple_GET_ITEM(tuple, 0);

            if (!(((t_item *) item)->status & (DELETED | SCHEMA)))
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

        for (i = 0; i < len; i++) {
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
    if (self->status & TOINDEX)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_view_setBackgroundIndexed(t_view *self, PyObject *arg)
{
    PyObject *value = t_view_isBackgroundIndexed(self);

    if (PyObject_IsTrue(arg))
        self->status |= TOINDEX;
    else
        self->status &= ~TOINDEX;

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

    if (self->status & DEFERNOTIF)
    {
        PyObject *notif = PyTuple_Pack(3, callable, callArgs,
                                       kwds ? kwds : Py_None);

        PyList_Append(self->deferredNotificationsCtx->data, notif);
        Py_DECREF(notif);
    }
    else
    {
        PyObject *result = PyObject_Call(callable, callArgs, kwds);

        if (!result)
        {
            Py_DECREF(callArgs);
            return NULL;
        }
        Py_DECREF(result);
    }

    Py_DECREF(callArgs);
    Py_RETURN_NONE;
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


/* itsStatus */

static PyObject *t_view__getStatus(t_view *self, void *data)
{
    return PyInt_FromLong(self->status);
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


static PyObject *t_view_get(t_view *self, PyObject *key)
{
    if (PyUUID_Check(key))
    {
        PyObject *item = PyDict_GetItem(self->registry, key);

        if (item)
        {
            Py_INCREF(item);
            return item;
        }

        Py_RETURN_NONE;
    }
    else if (PyString_Check(key) || PyUnicode_Check(key))
        return PyObject_CallMethodObjArgs((PyObject *) self,
                                          getRoot_NAME, key, NULL);
    else
    {
        PyErr_SetObject(PyExc_TypeError, key);
        return NULL;
    }
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

            if (monitor->status & (DEFERRING | DELETING))
                continue;

            if (sysOnly && !(monitor->status & SYSMONITOR))
                continue;
            if (userOnly && (monitor->status & SYSMONITOR))
                continue;

            if (self->status & DEFERNOTIF)
            {
                PyObject *notif = PyTuple_Pack(3, monitor, args, Py_None);

                PyList_Append(self->deferredNotificationsCtx->data, notif);
                Py_DECREF(notif);
            }
            else
            {
                PyObject *result = PyObject_Call((PyObject *) monitor,
                                                 args, NULL);
                if (!result)
                {
                    Py_DECREF(args);
                    return NULL;
                }
                Py_DECREF(result);
            }
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
        PyErr_SetString(PyExc_AssertionError,
                        "view._unregisterItem(): item doesn't belong to view");
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


/* with view.reindexingDeferred() */

static PyObject *_t_view_deferidx__enter(PyObject *target, t_ctxmgr *mgr)
{
    t_view *self = (t_view *) target;

    if (self->deferredIndexingCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count == 0)
    {
        mgr->data = PySet_New(NULL);
        self->status |= DEFERIDX;
    }
    mgr->count += 1;

    return PyInt_FromLong(mgr->count);
}

static PyObject *_t_view_deferidx__exit(PyObject *target, t_ctxmgr *mgr,
                                        PyObject *type, PyObject *value,
                                        PyObject *traceback)
{
    t_view *self = (t_view *) target;

    if (self->deferredIndexingCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count > 0)
        mgr->count -= 1;
    
    if (mgr->count == 0)
    {
        PyObject *monitors = PyObject_GetIter(self->deferredIndexingCtx->data);
        PyObject *monitor;

        self->status &= ~DEFERIDX;
        Py_CLEAR(self->deferredIndexingCtx);

        if (!monitors)
            return NULL;

        while ((monitor = PyIter_Next(monitors))) {
            PyObject *result = PyObject_CallMethodObjArgs(monitor, reindex_NAME,
                                                          NULL);
            Py_DECREF(monitor);
            if (result == NULL)
                break;
            else
                Py_DECREF(result);
        }
        Py_DECREF(monitors);

        if (PyErr_Occurred())
            return NULL;
    }

    if (type != Py_None)
        Py_RETURN_FALSE;

    Py_RETURN_TRUE;
}

static PyObject *t_view_isReindexingDeferred(t_view *self)
{
    if (self->status & DEFERIDX)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_view_reindexingDeferred(t_view *self)
{
    if (self->deferredIndexingCtx)
    {
        Py_INCREF(self->deferredIndexingCtx);
        return (PyObject *) self->deferredIndexingCtx;
    }
    else
    {
        t_ctxmgr *ctxmgr = (t_ctxmgr *) PyObject_Call((PyObject *) CtxMgr,
                                                      Empty_TUPLE, NULL);
        
        if (ctxmgr)
        {
            ctxmgr->target = (PyObject *) self; Py_INCREF(self);
            ctxmgr->enterFn = _t_view_deferidx__enter;
            ctxmgr->exitFn = _t_view_deferidx__exit;
            self->deferredIndexingCtx = ctxmgr; Py_INCREF(ctxmgr);
        }

        return (PyObject *) ctxmgr;
    }
}

static PyObject *t_view__deferIndexMonitor(t_view *self, PyObject *arg)
{
    if (self->status & DEFERIDX)
    {
        if (PySet_Add(self->deferredIndexingCtx->data, arg) < 0)
            return NULL;
    }

    Py_RETURN_NONE;    
}


/* with view.observersDeferred(discard=True) */

static PyObject *_t_view_deferobs__enter(PyObject *target, t_ctxmgr *mgr)
{
    t_view *self = (t_view *) target;

    if (self->deferredObserversCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count == 0)
    {
        int discard = mgr->data == Py_True;

        Py_DECREF(mgr->data);

        if (discard)
        {
            mgr->data = PyDict_New();
            self->status |= DEFEROBSD;
        }
        else
        {
            mgr->data = PyList_New(0);
            self->status |= DEFEROBSA;
        }
    }
    mgr->count += 1;

    return PyInt_FromLong(mgr->count);
}

static PyObject *_t_view_deferobs__exit(PyObject *target, t_ctxmgr *mgr,
                                        PyObject *type, PyObject *value,
                                        PyObject *traceback)
{
    t_view *self = (t_view *) target;

    if (self->deferredObserversCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count > 0)
        mgr->count -= 1;
    
    if (mgr->count == 0)
    {
        PyObject *calls = self->deferredObserversCtx->data;
        int status = self->status;

        Py_INCREF(calls);
        self->status &= ~DEFEROBS;
        Py_CLEAR(self->deferredObserversCtx);

        if (status & DEFEROBSA)
        {
            int i = -1, size = PyList_GET_SIZE(calls);

            while (++i < size) {
                PyObject *call = PyList_GET_ITEM(calls, i);
                PyObject *attr = PyTuple_GET_ITEM(call, 0);
                PyObject *item = PyTuple_GET_ITEM(call, 1);
                PyObject *op = PyTuple_GET_ITEM(call, 2);
                PyObject *name = PyTuple_GET_ITEM(call, 3);

                if (CAttribute_invokeAfterChange((t_attribute *) attr,
                                                 item, op, name) < 0)
                    break;
            }
        }
        else if (status & DEFEROBSD)
        {
            PyObject *call, *op;
            Py_ssize_t pos = 0;

            while (PyDict_Next(calls, &pos, &call, &op)) {
                PyObject *attr = PyTuple_GET_ITEM(call, 0);
                PyObject *item = PyTuple_GET_ITEM(call, 1);
                PyObject *name = PyTuple_GET_ITEM(call, 2);

                if (CAttribute_invokeAfterChange((t_attribute *) attr,
                                                 item, op, name) < 0)
                    break;
            }
        }

        Py_DECREF(calls);
        if (PyErr_Occurred())
            return NULL;
    }

    if (type != Py_None)
        Py_RETURN_FALSE;

    Py_RETURN_TRUE;
}

static PyObject *t_view_areObserversDeferred(t_view *self)
{
    if (self->status & DEFEROBS)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_view_observersDeferred(t_view *self, PyObject *args)
{
    PyObject *discard = Py_True;

    if (!PyArg_ParseTuple(args, "|O", &discard))
        return NULL;

    if (discard != Py_True && PyObject_IsTrue(discard))
        discard = Py_True;

    if (self->deferredObserversCtx)
    {
        if ((discard == Py_True && self->status & DEFEROBSA) ||
            (discard != Py_True && self->status & DEFEROBSD))
        {
            PyErr_SetString(PyExc_ValueError,
                            "nested call with different discard option");
            return NULL;
        }

        Py_INCREF(self->deferredObserversCtx);
        return (PyObject *) self->deferredObserversCtx;
    }
    else
    {
        t_ctxmgr *ctxmgr = (t_ctxmgr *) PyObject_Call((PyObject *) CtxMgr,
                                                      Empty_TUPLE, NULL);
        
        if (ctxmgr)
        {
            ctxmgr->target = (PyObject *) self; Py_INCREF(self);
            ctxmgr->data = discard; Py_INCREF(discard);
            ctxmgr->enterFn = _t_view_deferobs__enter;
            ctxmgr->exitFn = _t_view_deferobs__exit;
            self->deferredObserversCtx = ctxmgr; Py_INCREF(ctxmgr);
        }

        return (PyObject *) ctxmgr;
    }
}


/* with view.notificationsDeferred() */

static PyObject *_t_view_defernotif__enter(PyObject *target, t_ctxmgr *mgr)
{
    t_view *self = (t_view *) target;

    if (self->deferredNotificationsCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count == 0)
    {
        mgr->data = PyList_New(0);
        self->status |= DEFERNOTIF;
    }
    mgr->count += 1;

    return PyInt_FromLong(mgr->count);
}

static PyObject *_t_view_defernotif__exit(PyObject *target, t_ctxmgr *mgr,
                                          PyObject *type, PyObject *value,
                                          PyObject *traceback)
{
    t_view *self = (t_view *) target;

    if (self->deferredNotificationsCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count > 0)
        mgr->count -= 1;
    
    if (mgr->count == 0)
    {
        PyObject *notifs = self->deferredNotificationsCtx->data;
        int status = self->status;

        Py_INCREF(notifs);
        self->status &= ~DEFERNOTIF;
        Py_CLEAR(self->deferredNotificationsCtx);

        if (status & DEFERNOTIF)
        {
            int i = -1, size = PyList_GET_SIZE(notifs);

            while (++i < size) {
                PyObject *notif = PyList_GET_ITEM(notifs, i);
                PyObject *callable = PyTuple_GET_ITEM(notif, 0);
                PyObject *args = PyTuple_GET_ITEM(notif, 1);
                PyObject *kwds = PyTuple_GET_ITEM(notif, 2);
                PyObject *result = PyObject_Call(callable, args,
                                                 kwds == Py_None ? NULL : kwds);

                if (!result)
                    break;
                Py_DECREF(result);
            }
        }

        Py_DECREF(notifs);
        if (PyErr_Occurred())
            return NULL;
    }

    if (type != Py_None)
        Py_RETURN_FALSE;

    Py_RETURN_TRUE;
}

static PyObject *t_view_areNotificationsDeferred(t_view *self)
{
    if (self->status & DEFERNOTIF)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_view_notificationsDeferred(t_view *self, PyObject *args)
{
    if (self->deferredNotificationsCtx)
    {
        Py_INCREF(self->deferredNotificationsCtx);
        return (PyObject *) self->deferredNotificationsCtx;
    }
    else
    {
        t_ctxmgr *ctxmgr = (t_ctxmgr *) PyObject_Call((PyObject *) CtxMgr,
                                                      Empty_TUPLE, NULL);
        
        if (ctxmgr)
        {
            ctxmgr->target = (PyObject *) self; Py_INCREF(self);
            ctxmgr->enterFn = _t_view_defernotif__enter;
            ctxmgr->exitFn = _t_view_defernotif__exit;
            self->deferredNotificationsCtx = ctxmgr; Py_INCREF(ctxmgr);
        }

        return (PyObject *) ctxmgr;
    }
}

static PyObject *t_view_cancelDeferredNotifications(t_view *self)
{
    if (self->deferredNotificationsCtx)
    {
        PyObject *list = self->deferredNotificationsCtx->data;
 
        PyList_SetSlice(list, 0, PyList_GET_SIZE(list), NULL);
        Py_RETURN_TRUE;
    }

    Py_RETURN_FALSE;
}


/* with view.commitDeferred() */

static PyObject *_t_view_defercommit__enter(PyObject *target, t_ctxmgr *mgr)
{
    t_view *self = (t_view *) target;

    if (self->deferredCommitCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count == 0)
    {
        mgr->data = PyList_New(0);
        self->status |= DEFERCOMMIT;
    }
    mgr->count += 1;

    return PyInt_FromLong(mgr->count);
}

static PyObject *_t_view_defercommit__exit(PyObject *target, t_ctxmgr *mgr,
                                           PyObject *type, PyObject *value,
                                           PyObject *traceback)
{
    t_view *self = (t_view *) target;

    if (self->deferredCommitCtx != mgr)
    {
        PyErr_SetString(PyExc_ValueError, "Invalid CtxMgr target");
        return NULL;
    }

    if (mgr->count > 0)
        mgr->count -= 1;
    
    if (mgr->count == 0)
    {
        PyObject *calls = self->deferredCommitCtx->data;
        int status = self->status;

        Py_INCREF(calls);
        self->status &= ~DEFERCOMMIT;
        Py_CLEAR(self->deferredCommitCtx);

        if (!PyList_Check(calls))
            PyErr_SetObject(PyExc_TypeError, calls);
        else if (status & DEFERCOMMIT)
        {
            int size = PyList_GET_SIZE(calls);
            int i;

            for (i = 0; i < size; i++) {
                PyObject *call = PyList_GET_ITEM(calls, i);
                PyObject *method, *args, *result;

                if (!PyTuple_Check(call))
                {
                    PyErr_SetObject(PyExc_TypeError, call);
                    break;
                }

                method = PyTuple_GET_ITEM(call, 0);
                args = PyTuple_GetSlice(call, 1, PyTuple_GET_SIZE(call));
                if (!args)
                    break;

                result = PyObject_Call(method, args, NULL);
                Py_DECREF(args);
                if (!result)
                    break;
                Py_DECREF(result);
            }
        }

        Py_DECREF(calls);
        if (PyErr_Occurred())
            return NULL;
    }

    if (type != Py_None)
        Py_RETURN_FALSE;

    Py_RETURN_TRUE;
}

static PyObject *t_view_isCommitDeferred(t_view *self)
{
    if (self->status & DEFERCOMMIT)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_view_commitDeferred(t_view *self, PyObject *args)
{
    if (self->deferredCommitCtx)
    {
        Py_INCREF(self->deferredCommitCtx);
        return (PyObject *) self->deferredCommitCtx;
    }
    else
    {
        t_ctxmgr *ctxmgr = (t_ctxmgr *) PyObject_Call((PyObject *) CtxMgr,
                                                      Empty_TUPLE, NULL);
        
        if (ctxmgr)
        {
            ctxmgr->target = (PyObject *) self; Py_INCREF(self);
            ctxmgr->enterFn = _t_view_defercommit__enter;
            ctxmgr->exitFn = _t_view_defercommit__exit;
            self->deferredCommitCtx = ctxmgr; Py_INCREF(ctxmgr);
        }

        return (PyObject *) ctxmgr;
    }
}

/* Replace deferred commit calls with refresh calls
 * so that expected merge and notify policies are still observed.
 */
static PyObject *t_view_cancelDeferredCommits(t_view *self)
{
    if (self->status & DEFERCOMMIT)
    {
        PyObject *calls = self->deferredCommitCtx->data;

        if (!PyList_Check(calls))
        {
            PyErr_SetObject(PyExc_TypeError, calls);
            return NULL;
        }
        else
        {
            int size = PyList_GET_SIZE(calls);
            int i;

            for (i = 0; i < size; i++) {
                PyObject *call = PyList_GET_ITEM(calls, i);
                PyObject *method;

                if (!PyTuple_Check(call))
                {
                    PyErr_SetObject(PyExc_TypeError, call);
                    return NULL;
                }

                method = PyObject_GetAttr((PyObject *) self, refresh_NAME);
                if (!method)
                    return NULL;

                if (PyTuple_SetItem(call, 0, method) < 0) /* steals ref */
                {
                    Py_DECREF(method);
                    return NULL;
                }
            }
        }
    }

    Py_RETURN_NONE;
}


static int _check_pair(PyObject *obj)
{
    if (!obj)
        return -1;
    
    if (!PyTuple_Check(obj))
    {
        PyErr_SetObject(PyExc_TypeError, obj);
        return -1;
    }

    if (PyTuple_GET_SIZE(obj) != 2)
    {
        PyErr_SetObject(PyExc_ValueError, obj);
        return -1;
    }

    return 0;
}

static PyObject *_read_value(t_view *self, PyObject *reader,
                             PyObject *uValues, int i)
{
    if (reader == Py_None)
    {
        Py_INCREF(Nil);
        return Nil;
    }
    else
    {
        PyObject *uValue = PySequence_GetItem(uValues, i);
        PyObject *loadedValue, *value;

        if (!uValue)
            return NULL;

        if (uValue == Py_None)
        {
            Py_DECREF(uValue);
            Py_INCREF(Nil);
            return Nil;
        }

        loadedValue = PyObject_CallMethodObjArgs(reader, readValue_NAME,
                                                 self, uValue, NULL);
        Py_DECREF(uValue);

        if (_check_pair(loadedValue) < 0)
        {
            Py_XDECREF(loadedValue);
            return NULL;
        }

        value = PyTuple_GET_ITEM(loadedValue, 1);
        Py_INCREF(value);
        Py_DECREF(loadedValue);

        return value;
    }
}

static PyObject *_t_view_findValues(t_view *self, PyObject *args,
                                    PyObject **inheritFrom)
{
    PyObject *uItem, *item;
    PyObject *values = NULL, *names = NULL, *result = NULL;
    int size, i;

    if (!PyTuple_Check(args))
    {
        PyErr_SetObject(PyExc_TypeError, args);
        return NULL;
    }

    size = PyTuple_GET_SIZE(args);
    if (size < 1)
    {
        PyErr_SetString(PyExc_ValueError, "missing args");
        return NULL;
    }

    uItem = PyTuple_GET_ITEM(args, 0);
    if (PyUUID_Check(uItem))
        item = PyDict_GetItem(self->registry, uItem);
    else if (PyObject_TypeCheck(uItem, CItem))
        item = uItem;
    else
    {
        PyErr_SetObject(PyExc_TypeError, uItem);
        return NULL;
    }
        
    values = PyTuple_New(size - 1);
    if (!values)
        return NULL;

    if (item != NULL)
    {
        for (i = 1; i < size; i++) {
            PyObject *arg = PyTuple_GET_ITEM(args, i);
            PyObject *name, *defaultValue, *value;

            if (_check_pair(arg) < 0)
                goto error;

            name = PyTuple_GET_ITEM(arg, 0);
            defaultValue = inheritFrom ? Nil : PyTuple_GET_ITEM(arg, 1);
            value = CItem_getLocalAttributeValue((t_item *) item, name,
                                                 defaultValue, NULL);
            if (!value)
                goto error;
            PyTuple_SET_ITEM(values, i - 1, value);
        }
        if (inheritFrom)
        {
            *inheritFrom =
                CItem_getLocalAttributeValue((t_item *) item, inheritFrom_NAME,
                                             Py_None, NULL);
            if (!*inheritFrom)
                goto error;
        }
    }
    else if (PyObject_TypeCheck(self->repository, CRepository))
    {
        t_repository *repository = (t_repository *) self->repository;
        PyObject *reader, *uValues, *version;

        names = PyTuple_New(size - (inheritFrom == NULL));
        if (!names)
            return NULL;

        for (i = 1; i < size; i++) {
            PyObject *arg = PyTuple_GET_ITEM(args, i);
            PyObject *name;

            if (_check_pair(arg) < 0)
                goto error;

            name = PyTuple_GET_ITEM(arg, 0);
            PyTuple_SET_ITEM(names, i - 1, name);
            Py_INCREF(name);
        }
        if (inheritFrom)
        {
            Py_INCREF(inheritFrom_NAME);
            PyTuple_SET_ITEM(names, size - 1, inheritFrom_NAME);
        }

        version = PyInt_FromLong(self->version);
        result = PyObject_CallMethodObjArgs(repository->store, loadValues_NAME,
                                            self, version, uItem, names, NULL);
        Py_DECREF(version);
        Py_CLEAR(names);
        if (_check_pair(result) < 0)
            goto error;

        reader = PyTuple_GET_ITEM(result, 0);
        uValues = PyTuple_GET_ITEM(result, 1);

        for (i = 1; i < size; i++) {
            PyObject *value = _read_value(self, reader, uValues, i - 1);

            if (!value)
                goto error;

            if (value != Nil)
                PyTuple_SET_ITEM(values, i - 1, value);
            else if (inheritFrom)
                PyTuple_SET_ITEM(values, i - 1, value);
            else
            {
                PyObject *arg = PyTuple_GET_ITEM(args, i);
                PyObject *defaultValue = PyTuple_GET_ITEM(arg, 1);

                Py_INCREF(defaultValue);
                Py_DECREF(value);
                PyTuple_SET_ITEM(values, i - 1, defaultValue);
            }
        }
        if (inheritFrom)
        {
            PyObject *value = _read_value(self, reader, uValues, size - 1);

            if (!value)
                goto error;

            if (value == Nil)
            {
                Py_DECREF(Nil);
                Py_INCREF(Py_None);
                *inheritFrom = Py_None;
            }
            else
                *inheritFrom = value;
        }

        Py_CLEAR(result);
    }
    else
    {
        if (inheritFrom)
        {
            for (i = 1; i < size; i++) {
                Py_INCREF(Nil);
                PyTuple_SET_ITEM(values, i - 1, Nil);
            }
            Py_INCREF(Py_None);
            *inheritFrom = Py_None;
        }
        else
        {
            for (i = 1; i < size; i++) {
                PyObject *arg = PyTuple_GET_ITEM(args, i);
                PyObject *defaultValue = PyTuple_GET_ITEM(arg, 1);

                PyTuple_SET_ITEM(values, i - 1, defaultValue);
                Py_INCREF(defaultValue);
            }
        }
    }

    return values;

  error:
    if (inheritFrom)
        Py_CLEAR(*inheritFrom);
    Py_CLEAR(values);
    Py_CLEAR(names);
    Py_CLEAR(result);

    return NULL;
}

static PyObject *t_view_findValues(t_view *self, PyObject *args)
{
    return _t_view_findValues(self, args, NULL);
}

static PyObject *t_view_findInheritedValues(t_view *self, PyObject *args)
{
    PyObject *localValues, *values, *inheritFrom = NULL;
    int size, i;

    if (!PyTuple_Check(args))
    {
        PyErr_SetObject(PyExc_TypeError, args);
        return NULL;
    }

    size = PyTuple_GET_SIZE(args);
    localValues = _t_view_findValues(self, args, &inheritFrom);
    if (!localValues)
        return NULL;

    values = PyTuple_New(size - 1);
    if (!values)
    {
        Py_DECREF(localValues);
        return NULL;
    }

    if (inheritFrom == Py_None)
    {
        for (i = 1; i < size; i++) {
            PyObject *value = PyTuple_GET_ITEM(localValues, i - 1);

            if (value == Nil)
                value = PyTuple_GET_ITEM(PyTuple_GET_ITEM(args, i), 1);

            Py_INCREF(value);
            PyTuple_SET_ITEM(values, i - 1, value);
        }
    }
    else
    {
        int nilCount = 0;

        for (i = 1; i < size; i++) {
            PyObject *value = PyTuple_GET_ITEM(localValues, i - 1);

            if (value == Nil)
                nilCount += 1;

            Py_INCREF(value);
            PyTuple_SET_ITEM(values, i - 1, value);
        }

        if (nilCount)
        {
            PyObject *inheritArgs, *inheritedValues;
            int j;

            inheritArgs = PyTuple_New(nilCount + 1);
            if (!inheritArgs)
            {
                Py_DECREF(inheritFrom);
                Py_DECREF(localValues);
                Py_DECREF(values);
                return NULL;
            }

            Py_INCREF(inheritFrom);
            PyTuple_SET_ITEM(inheritArgs, 0, inheritFrom);

            for (i = 1, j = 1; i < size; i++) {
                PyObject *value = PyTuple_GET_ITEM(localValues, i - 1);

                if (value == Nil)
                {
                    PyObject *arg = PyTuple_GET_ITEM(args, i);
                    
                    Py_INCREF(arg);
                    PyTuple_SET_ITEM(inheritArgs, j++, arg);
                }
            }

            inheritedValues = t_view_findInheritedValues(self, inheritArgs);
            Py_DECREF(inheritArgs);
            if (!inheritedValues)
            {
                Py_DECREF(inheritFrom);
                Py_DECREF(localValues);
                Py_DECREF(values);
                return NULL;
            }

            for (i = 1, j = 0; i < size; i++) {
                PyObject *value = PyTuple_GET_ITEM(localValues, i - 1);

                if (value == Nil)
                {
                    value = PyTuple_GET_ITEM(inheritedValues, j++);
                    Py_INCREF(value);
                    PyTuple_SetItem(values, i - 1, value);
                }
            }
            Py_DECREF(inheritedValues);
        }
    }
    Py_DECREF(inheritFrom);
    Py_DECREF(localValues);

    return values;
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
            PyDict_SetItemString_Int(dict, "CDIRTY", CDIRTY);
            PyDict_SetItemString_Int(dict, "STALE", STALE);
            PyDict_SetItemString_Int(dict, "DEFERNOTIF", DEFERNOTIF);
            PyDict_SetItemString_Int(dict, "REFRESHING", REFRESHING);
            PyDict_SetItemString_Int(dict, "VERIFY", VERIFY);
            PyDict_SetItemString_Int(dict, "COMMITREQ", COMMITREQ);
            PyDict_SetItemString_Int(dict, "DEFERIDX", DEFERIDX);
            PyDict_SetItemString_Int(dict, "DEFEROBSD", DEFEROBSD);
            PyDict_SetItemString_Int(dict, "DEFEROBSA", DEFEROBSA);
            PyDict_SetItemString_Int(dict, "DEFERCOMMIT", DEFERCOMMIT);
            PyDict_SetItemString_Int(dict, "COMMITLOCK", COMMITLOCK);
            PyDict_SetItemString_Int(dict, "DONTNOTIFY", DONTNOTIFY);
            PyDict_SetItemString_Int(dict, "TOINDEX", TOINDEX);
            PyDict_SetItemString_Int(dict, "SAVEMASK", W_SAVEMASK);

            refresh_NAME = PyString_FromString("refresh");
            _effectDelete_NAME = PyString_FromString("_effectDelete");
            logger_NAME = PyString_FromString("logger");
            _loadItem_NAME = PyString_FromString("_loadItem");
            _readItem_NAME = PyString_FromString("_readItem");
            getRoot_NAME = PyString_FromString("getRoot");
            _fwalk_NAME = PyString_FromString("_fwalk");
            findPath_NAME = PyString_FromString("findPath");
            cacheMonitors_NAME = PyString_FromString("cacheMonitors");
            reindex_NAME = PyString_FromString("reindex");
            loadValues_NAME = PyString_FromString("loadValues");
            readValue_NAME = PyString_FromString("readValue");
            inheritFrom_NAME = PyString_FromString("inheritFrom");
            commit_NAME = PyString_FromString("commit");

            MONITORS_PATH = PyString_FromString("//Schema/Core/items/Monitors");
            PyDict_SetItemString(dict, "MONITORS", MONITORS_PATH);

            cobj = PyCObject_FromVoidPtr(_t_view_invokeMonitors, NULL);
            PyModule_AddObject(m, "_t_view_invokeMonitors", cobj);
        }
    }
}
