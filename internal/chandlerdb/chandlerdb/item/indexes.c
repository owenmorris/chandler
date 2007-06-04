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


/* Index */

static void t_index_dealloc(t_index *self);
static int t_index_traverse(t_index *self, visitproc visit, void *arg);
static int t_index_clear(t_index *self);

static PyObject *t_index_new(PyTypeObject *type,
                             PyObject *args, PyObject *kwds);
static int t_index_init(t_index *self, PyObject *args, PyObject *kwds);
static PyObject *t_index_repr(t_index *self);

static Py_ssize_t t_index_dict_length(t_index *self);
static PyObject *t_index_dict_get(t_index *self, PyObject *key);
static int t_index_dict_set(t_index *self, PyObject *key, PyObject *value);
static int t_index_contains(t_index *self, PyObject *key);
static PyObject *t_index__loadKey(t_index *self, PyObject *key);
static PyObject *t_index_get(t_index *self, PyObject *args);
static PyObject *t_index_has_key(t_index *self, PyObject *key);
static PyObject *t_index_iter(t_index *self);
static PyObject *t_index_dict_clear(t_index *self);
static PyObject *t_index_insertKey(t_index *self, PyObject *ignore);
static PyObject *t_index_removeKey(t_index *self, PyObject *ignore);
static PyObject *t_index_moveKey(t_index *self, PyObject *ignore);
static PyObject *t_index_moveKeys(t_index *self, PyObject *ignore);

static PyObject *_loadKey_NAME;
static PyObject *iterkeys_NAME;

static PyMemberDef t_index_members[] = {
    { "_dict", T_OBJECT, offsetof(t_index, dict), 0, "" },
    { "_count", T_UINT, offsetof(t_index, count), 0, "" },
    { "_changedKeys", T_OBJECT, offsetof(t_index, changedKeys), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_index_methods[] = {
    { "_loadKey", (PyCFunction) t_index__loadKey, METH_O, "" },
    { "get", (PyCFunction) t_index_get, METH_VARARGS, "" },
    { "clear", (PyCFunction) t_index_dict_clear, METH_NOARGS, "" },
    { "has_key", (PyCFunction) t_index_has_key, METH_O, "" },
    { "insertKey", (PyCFunction) t_index_insertKey, METH_VARARGS, "" },
    { "removeKey", (PyCFunction) t_index_removeKey, METH_O, "" },
    { "moveKey", (PyCFunction) t_index_moveKey, METH_VARARGS, "" },
    { "moveKeys", (PyCFunction) t_index_moveKeys, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyMappingMethods t_index_as_mapping = {
    (lenfunc) t_index_dict_length,
    (binaryfunc) t_index_dict_get,
    (objobjargproc) t_index_dict_set
};

static PySequenceMethods t_index_as_sequence = {
    (lenfunc) t_index_dict_length,     /* sq_length */
    0,                                 /* sq_concat */
    0,                                 /* sq_repeat */
    0,                                 /* sq_item */
    0,                                 /* sq_slice */
    0,                                 /* sq_ass_item */
    0,                                 /* sq_ass_slice */
    (objobjproc) t_index_contains,     /* sq_contains */
    0,                                 /* sq_inplace_concat */
    0,                                 /* sq_inplace_repeat */
};

static PyTypeObject IndexType = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /* ob_size */
    "chandlerdb.item.c.Index",         /* tp_name */
    sizeof(t_index),                   /* tp_basicsize */
    0,                                 /* tp_itemsize */
    (destructor)t_index_dealloc,       /* tp_dealloc */
    0,                                 /* tp_print */
    0,                                 /* tp_getattr */
    0,                                 /* tp_setattr */
    0,                                 /* tp_compare */
    (reprfunc)t_index_repr,            /* tp_repr */
    0,                                 /* tp_as_number */
    &t_index_as_sequence,              /* tp_as_sequence */
    &t_index_as_mapping,               /* tp_as_mapping */
    0,                                 /* tp_hash  */
    0,                                 /* tp_call */
    0,                                 /* tp_str */
    0,                                 /* tp_getattro */
    0,                                 /* tp_setattro */
    0,                                 /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),              /* tp_flags */
    "C Index type",                    /* tp_doc */
    (traverseproc)t_index_traverse,    /* tp_traverse */
    (inquiry)t_index_clear,            /* tp_clear */
    0,                                 /* tp_richcompare */
    0,                                 /* tp_weaklistoffset */
    (getiterfunc)t_index_iter,         /* tp_iter */
    0,                                 /* tp_iternext */
    t_index_methods,                   /* tp_methods */
    t_index_members,                   /* tp_members */
    0,                                 /* tp_getset */
    0,                                 /* tp_base */
    0,                                 /* tp_dict */
    0,                                 /* tp_descr_get */
    0,                                 /* tp_descr_set */
    0,                                 /* tp_dictoffset */
    (initproc)t_index_init,            /* tp_init */
    0,                                 /* tp_alloc */
    (newfunc)t_index_new,              /* tp_new */
};


static void t_index_dealloc(t_index *self)
{
    t_index_clear(self);
    self->ob_type->tp_free((PyObject *) self);

    indexCount -= 1;
}

static int t_index_traverse(t_index *self, visitproc visit, void *arg)
{
    Py_VISIT(self->dict);
    Py_VISIT(self->changedKeys);
    return 0;
}

static int t_index_clear(t_index *self)
{
    Py_CLEAR(self->dict);
    Py_CLEAR(self->changedKeys);
    return 0;
}

static PyObject *t_index_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_index *self = (t_index *) type->tp_alloc(type, 0);

    if (self)
    {
        indexCount += 1;
        self->dict = PyDict_New();
        self->changedKeys = NULL;
    }

    return (PyObject *) self;
}

static int t_index_init(t_index *self, PyObject *args, PyObject *kwds)
{
    self->count = 0;
    return 0;
}

static PyObject *t_index_repr(t_index *self)
{
    PyObject *type = PyObject_GetAttrString((PyObject *) self->ob_type,
                                            "__name__");
    PyObject *repr = PyString_FromFormat("<%s: %d>",
                                         PyString_AsString(type),
                                         self->count);

    Py_DECREF(type);

    return repr;
}

static PyObject *t_index_iter(t_index *self)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, iterkeys_NAME, NULL);
}

static Py_ssize_t t_index_dict_length(t_index *self)
{
    return self->count;
}

static PyObject *t_index_dict_get(t_index *self, PyObject *key)
{
    PyObject *node = PyDict_GetItem(self->dict, key);

    if (node)
    {
        Py_INCREF(node);
        return node;
    }

    node = PyObject_CallMethodObjArgs((PyObject *) self,
                                      _loadKey_NAME, key, NULL);
    if (node == Py_None)
    {
        Py_DECREF(node);
        PyErr_SetObject(PyExc_KeyError, key);
        return NULL;
    }

    return node;
}

static int t_index_dict_set(t_index *self, PyObject *key, PyObject *value)
{
    if (value)
        return PyDict_SetItem(self->dict, key, value);

    return PyDict_DelItem(self->dict, key);
}

static int t_index_contains(t_index *self, PyObject *key)
{
    if (PyDict_Contains(self->dict, key))
        return 1;
    else
    {
        PyObject *node = PyObject_CallMethodObjArgs((PyObject *) self,
                                                    _loadKey_NAME, key, NULL);
        if (!node)
            return -1;

        Py_DECREF(node);
        return node != Py_None;
    }
}

static PyObject *t_index__loadKey(t_index *self, PyObject *key)
{
    Py_RETURN_NONE;
}

static PyObject *t_index_get(t_index *self, PyObject *args)
{
    PyObject *key, *node, *defaultValue = Py_None;
    
    if (!PyArg_ParseTuple(args, "O|O", &key, &defaultValue))
        return NULL;

    node = PyDict_GetItem(self->dict, key);
    if (node)
    {
        Py_INCREF(node);
        return node;
    }

    node = PyObject_CallMethodObjArgs((PyObject *) self,
                                      _loadKey_NAME, key, NULL);
    if (node == Py_None)
    {
        Py_INCREF(defaultValue);
        Py_DECREF(node);
        return defaultValue;
    }

    return node;
}

static PyObject *t_index_dict_clear(t_index *self)
{
    PyDict_Clear(self->dict);
    self->count = 0;

    Py_RETURN_NONE;
}

static PyObject *t_index_has_key(t_index *self, PyObject *key)
{
    int contains = t_index_contains(self, key);

    if (contains < 0)
        return NULL;

    if (contains)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_index_insertKey(t_index *self, PyObject *ignore)
{
    self->count += 1;
    Py_RETURN_NONE;

}

static PyObject *t_index_removeKey(t_index *self, PyObject *ignore)
{
    self->count -= 1;
    Py_RETURN_TRUE;
}

static PyObject *t_index_moveKey(t_index *self, PyObject *ignore)
{
    Py_RETURN_NONE;
}

static PyObject *t_index_moveKeys(t_index *self, PyObject *ignore)
{
    Py_RETURN_NONE;
}


/* DelegatingIndex */

typedef struct {
    PyObject_HEAD
    PyObject *index;
} t_delegating_index;

static void t_delegating_index_dealloc(t_delegating_index *self);
static int t_delegating_index_traverse(t_delegating_index *self,
                                       visitproc visit, void *arg);
static int t_delegating_index_clear(t_delegating_index *self);

static PyObject *t_delegating_index_new(PyTypeObject *type,
                                        PyObject *args, PyObject *kwds);
static int t_delegating_index_init(t_delegating_index *self,
                                   PyObject *args, PyObject *kwds);
static PyObject *t_delegating_index_repr(t_delegating_index *self);
static PyObject *t_delegating_index_getattro(t_delegating_index *self,
                                             PyObject *name);

static Py_ssize_t t_delegating_index_dict_length(t_delegating_index *self);
static PyObject *t_delegating_index_dict_get(t_delegating_index *self,
                                             PyObject *key);
static int t_delegating_index_dict_set(t_delegating_index *self,
                                       PyObject *key, PyObject *value);
static int t_delegating_index_contains(t_delegating_index *self, PyObject *key);
static PyObject *t_delegating_index_iter(t_delegating_index *self);

static PyMemberDef t_delegating_index_members[] = {
    { "_index", T_OBJECT, offsetof(t_delegating_index, index), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMappingMethods t_delegating_index_as_mapping = {
    (lenfunc) t_delegating_index_dict_length,
    (binaryfunc) t_delegating_index_dict_get,
    (objobjargproc) t_delegating_index_dict_set
};

static PySequenceMethods t_delegating_index_as_sequence = {
    (lenfunc) t_delegating_index_dict_length,     /* sq_length */
    0,                                            /* sq_concat */
    0,                                            /* sq_repeat */
    0,                                            /* sq_item */
    0,                                            /* sq_slice */
    0,                                            /* sq_ass_item */
    0,                                            /* sq_ass_slice */
    (objobjproc) t_delegating_index_contains,     /* sq_contains */
    0,                                            /* sq_inplace_concat */
    0,                                            /* sq_inplace_repeat */
};

static PyTypeObject DelegatingIndexType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.DelegatingIndex",       /* tp_name */
    sizeof(t_delegating_index),                /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_delegating_index_dealloc,    /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    (reprfunc)t_delegating_index_repr,         /* tp_repr */
    0,                                         /* tp_as_number */
    &t_delegating_index_as_sequence,           /* tp_as_sequence */
    &t_delegating_index_as_mapping,            /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    0,                                         /* tp_str */
    (getattrofunc)t_delegating_index_getattro, /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "C DelegatingIndex type",                  /* tp_doc */
    (traverseproc)t_delegating_index_traverse, /* tp_traverse */
    (inquiry)t_delegating_index_clear,         /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    (getiterfunc)t_delegating_index_iter,      /* tp_iter */
    0,                                         /* tp_iternext */
    0,                                         /* tp_methods */
    t_delegating_index_members,                /* tp_members */
    0,                                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_delegating_index_init,         /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_delegating_index_new,           /* tp_new */
};


static void t_delegating_index_dealloc(t_delegating_index *self)
{
    t_delegating_index_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_delegating_index_traverse(t_delegating_index *self,
                                       visitproc visit, void *arg)
{
    Py_VISIT(self->index);
    return 0;
}

static int t_delegating_index_clear(t_delegating_index *self)
{
    Py_CLEAR(self->index);
    return 0;
}


static PyObject *t_delegating_index_new(PyTypeObject *type,
                                        PyObject *args, PyObject *kwds)
{
    t_delegating_index *self = (t_delegating_index *) type->tp_alloc(type, 0);

    if (self)
        self->index = NULL;

    return (PyObject *) self;
}

static int t_delegating_index_init(t_delegating_index *self,
                                   PyObject *args, PyObject *kwds)
{
    if (!PyArg_ParseTuple(args, "O", &self->index))
        return -1;

    Py_INCREF(self->index);

    return 0;
}

static PyObject *t_delegating_index_repr(t_delegating_index *self)
{
    PyObject *type = PyObject_GetAttrString((PyObject *) self->ob_type,
                                            "__name__");
    PyObject *repr =
        PyString_FromFormat("<%s: %d>",
                            PyString_AsString(type),
                            (int) t_delegating_index_dict_length(self));

    Py_DECREF(type);

    return repr;
}

static Py_ssize_t t_delegating_index_dict_length(t_delegating_index *self)
{
    return PyObject_Size(self->index);
}

static PyObject *t_delegating_index_dict_get(t_delegating_index *self,
                                             PyObject *key)
{
    return PyObject_GetItem(self->index, key);
}

static int t_delegating_index_dict_set(t_delegating_index *self,
                                       PyObject *key, PyObject *value)
{
    return PyObject_SetItem(self->index, key, value);
}

static int t_delegating_index_contains(t_delegating_index *self, PyObject *key)
{
    return PySequence_Contains(self->index, key);
}

static PyObject *t_delegating_index_iter(t_delegating_index *self)
{
    return PyObject_GetIter(self->index);
}

static PyObject *t_delegating_index_getattro(t_delegating_index *self,
                                             PyObject *name)
{
    PyObject *value = PyObject_GenericGetAttr((PyObject *) self, name);

    if (value)
        return value;

    PyErr_Clear();
    return PyObject_GetAttr(self->index, name);
}


void _init_indexes(PyObject *m)
{
    if (PyType_Ready(&IndexType) >= 0 &&
        PyType_Ready(&DelegatingIndexType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&IndexType);
            PyModule_AddObject(m, "CIndex",
                               (PyObject *) &IndexType);

            Py_INCREF(&DelegatingIndexType);
            PyModule_AddObject(m, "DelegatingIndex",
                               (PyObject *) &DelegatingIndexType);

            _loadKey_NAME = PyString_FromString("_loadKey");
            iterkeys_NAME = PyString_FromString("iterkeys");
        }
    }
}
