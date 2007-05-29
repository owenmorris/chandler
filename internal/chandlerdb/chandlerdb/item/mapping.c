/*
 *  Copyright (c) 2007 Open Source Applications Foundation
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

typedef struct {
    t_itemvalue itemvalue;
    PyObject *mapping;
} t_mapping;

static void t_mapping_dealloc(t_mapping *self);
static int t_mapping_traverse(t_mapping *self, visitproc visit, void *arg);
static int t_mapping_clear(t_mapping *self);
static PyObject *t_mapping_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds);
static int t_mapping_init(t_mapping *self, PyObject *args, PyObject *kwds);
static PyObject *t_mapping_repr(t_mapping *self);
static PyObject *t_mapping_str(t_mapping *self);
static long t_mapping_hash(t_mapping *self);
static PyObject *t_mapping_iter(t_mapping *self);

static PyObject *t_mapping_get(t_mapping *self, PyObject *args);
static PyObject *t_mapping_setdefault(t_mapping *self, PyObject *args);
static PyObject *t_mapping_pop(t_mapping *self, PyObject *args);
static PyObject *t_mapping_set(t_mapping *self, PyObject *args);
static PyObject *t_mapping_items(t_mapping *self);
static PyObject *t_mapping_keys(t_mapping *self);
static PyObject *t_mapping_values(t_mapping *self);
static PyObject *t_mapping__useValue(t_mapping *self, PyObject *value);

static Py_ssize_t t_mapping_map_length(t_mapping *self);
static PyObject *t_mapping_map_get(t_mapping *self, PyObject *key);
static int t_mapping_map_set(t_mapping *self, PyObject *key, PyObject *value);
static int t_mapping_map_contains(t_mapping *self, PyObject *value);


static PyObject *useValue_NAME;
static PyObject *prepareValue_NAME;
static PyObject *restoreValue_NAME;

static PyMemberDef t_mapping_members[] = {
    { "_mapping", T_OBJECT, offsetof(t_mapping, mapping), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_mapping_methods[] = {
    { "get", (PyCFunction) t_mapping_get, METH_VARARGS, NULL },
    { "setdefault", (PyCFunction) t_mapping_setdefault, METH_VARARGS, NULL },
    { "pop", (PyCFunction) t_mapping_pop, METH_VARARGS, NULL },
    { "set", (PyCFunction) t_mapping_set, METH_VARARGS, NULL },
    { "items", (PyCFunction) t_mapping_items, METH_NOARGS, NULL },
    { "keys", (PyCFunction) t_mapping_keys, METH_NOARGS, NULL },
    { "values", (PyCFunction) t_mapping_values, METH_NOARGS, NULL },
    { "_useValue", (PyCFunction) t_mapping__useValue, METH_O, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_mapping_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};


static PySequenceMethods t_mapping_as_sequence = {
    (lenfunc)t_mapping_map_length,              /* sq_length         */
    0,                                          /* sq_concat         */
    0,                                          /* sq_repeat         */
    0,                                          /* sq_item           */
    0,                                          /* sq_slice          */
    0,                                          /* sq_ass_item       */
    0,                                          /* sq_ass_slice      */
    (objobjproc)t_mapping_map_contains,         /* sq_contains       */
    0,                                          /* sq_inplace_concat */
    0,                                          /* sq_inplace_repeat */
};

static PyMappingMethods t_mapping_as_mapping = {
    (lenfunc)t_mapping_map_length,             /* mp_length          */
    (binaryfunc)t_mapping_map_get,             /* mp_subscript       */
    (objobjargproc)t_mapping_map_set,          /* mp_ass_subscript   */
};


static PyTypeObject MappingType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.PersistentMapping",     /* tp_name */
    sizeof(t_mapping),                         /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_mapping_dealloc,             /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    (reprfunc)t_mapping_repr,                  /* tp_repr */
    0,                                         /* tp_as_number */
    &t_mapping_as_sequence,                    /* tp_as_sequence */
    &t_mapping_as_mapping,                     /* tp_as_mapping */
    (hashfunc)t_mapping_hash,                  /* tp_hash  */
    0,                                         /* tp_call */
    (reprfunc)t_mapping_str,                   /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "C PersistentMapping type",                /* tp_doc */
    (traverseproc)t_mapping_traverse,          /* tp_traverse */
    (inquiry)t_mapping_clear,                  /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    (getiterfunc)t_mapping_iter,               /* tp_iter */
    0,                                         /* tp_iternext */
    t_mapping_methods,                         /* tp_methods */
    t_mapping_members,                         /* tp_members */
    t_mapping_properties,                      /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_mapping_init,                  /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_mapping_new,                    /* tp_new */
};


static void t_mapping_dealloc(t_mapping *self)
{
    t_mapping_clear(self);
    self->itemvalue.persistentvalue.ob_type->tp_free((PyObject *) self);
}

static int t_mapping_traverse(t_mapping *self, visitproc visit, void *arg)
{
    Py_VISIT(self->mapping);
    ItemValue->tp_traverse((PyObject *) self, visit, arg);

    return 0;
}

static int t_mapping_clear(t_mapping *self)
{
    Py_CLEAR(self->mapping);
    ItemValue->tp_clear((PyObject *) self);

    return 0;
}

static PyObject *t_mapping_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds)
{
    t_mapping *self = (t_mapping *) type->tp_alloc(type, 0);

    if (self)
    {
        self->itemvalue.owner = NULL;
        self->itemvalue.attribute = NULL;
        self->itemvalue.flags = 0;
        self->mapping = NULL;
    }

    return (PyObject *) self;
}

static int t_mapping_init(t_mapping *self, PyObject *args, PyObject *kwds)
{
    PyObject *mapping, *view = Py_None, *item = Py_None, *attribute = Py_None;
    int pure = 0;

    if (!PyArg_ParseTuple(args, "O|OOOi", &mapping,
                          &view, &item, &attribute, &pure))
        return -1;

    if (!PyMapping_Check(mapping))
    {
        PyErr_SetObject(PyExc_TypeError, mapping);
        return -1;
    }

    if (_t_itemvalue_init((t_itemvalue *) self, view, item, attribute) < 0)
        return -1;

    Py_INCREF(mapping);
    Py_XDECREF(self->mapping);
    self->mapping = mapping;

    if (pure)
        self->itemvalue.flags |= V_PURE;

    return 0;
}

static PyObject *t_mapping_repr(t_mapping *self)
{
    PyObject *str = PyObject_Str(self->mapping);

    if (str)
    {
        PyObject *format = PyString_FromString("<%s: %s>");
        PyTypeObject *type = self->itemvalue.persistentvalue.ob_type;
        PyObject *name = PyObject_GetAttrString((PyObject *) type, "__name__");
        PyObject *args = PyTuple_Pack(2, name, str);

        Py_DECREF(str);
        Py_DECREF(name);
        str = PyString_Format(format, args);
        Py_DECREF(format);
        Py_DECREF(args);
    }

    return str;
}

static PyObject *t_mapping_str(t_mapping *self)
{
    return PyObject_Str(self->mapping);
}

static long t_mapping_hash(t_mapping *self)
{
    return PyObject_Hash(self->mapping);
}

static PyObject *_restoreValue(t_mapping *self, PyObject *value)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, restoreValue_NAME,
                                      value, NULL);
}

static PyObject *_useValue(t_mapping *self, PyObject *value)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, useValue_NAME,
                                      value, NULL);
}

static PyObject *_prepareValue(t_mapping *self, PyObject *value)
{
    PyObject *item = PyObject_Call(self->itemvalue.owner, Empty_TUPLE, NULL);

    if (!item)
        return NULL;

    value = PyObject_CallMethodObjArgs((PyObject *) self, prepareValue_NAME,
                                        item, self->itemvalue.attribute, value,
                                        Py_False, NULL);
    Py_DECREF(item);

    return value;
}


static PyObject *_t_mapping__next(PyObject *target, t_iterator *iterator)
{
    t_mapping *self = (t_mapping *) target;
    PyObject *value = iterator->data->ob_type->tp_iternext(iterator->data);
    PyObject *v;

    if (!value)
        return NULL;

    v = _restoreValue(self, value);
    Py_DECREF(value);

    return v;
}

static PyObject *t_mapping_iter(t_mapping *self)
{
    PyObject *iter = PyObject_GetIter(self->mapping);

    if (!iter)
        return NULL;

    if (!(self->itemvalue.flags & V_PURE))
    {
        t_iterator *iterator =
            (t_iterator *) PyObject_Call((PyObject *) Iterator,
                                         Empty_TUPLE, NULL);
        if (iterator)
        {
            iterator->target = (PyObject *) self; Py_INCREF((PyObject *) self);
            iterator->data = iter;
            iterator->nextFn = _t_mapping__next;
        }
        iter = (PyObject *) iterator;
    }

    return iter;
}


static Py_ssize_t t_mapping_map_length(t_mapping *self)
{
    return PyMapping_Size(self->mapping);
}

static PyObject *t_mapping_map_get(t_mapping *self, PyObject *key)
{
    PyObject *value = PyObject_GetItem(self->mapping, key);

    if (!value)
        return NULL;

    if (!(self->itemvalue.flags & V_PURE))
    {
        PyObject *v = _restoreValue(self, value);

        Py_DECREF(value);
        if (!v)
            return NULL;

        value = v;
    }

    return value;
}

static int t_mapping_map_contains(t_mapping *self, PyObject *value)
{
    int result;

    if (self->itemvalue.flags & V_PURE)
        result = PyMapping_HasKey(self->mapping, value);
    else
    {
        value = _useValue(self, value);
        if (!value)
            return -1;

        result = PyMapping_HasKey(self->mapping, value);
        Py_DECREF(value);
    }

    return result;
}

static int _t_mapping_set(t_mapping *self, PyObject *key, PyObject *value,
                          int setDirty)
{
    int result;

    if (value == NULL)
        result = PyObject_DelItem(self->mapping, key);
    else if (self->itemvalue.flags & V_PURE)
        result = PyObject_SetItem(self->mapping, key, value);
    else
    {
        value = _prepareValue(self, value);
        if (!value)
            return -1;

        result = PyObject_SetItem(self->mapping, key, value);
        Py_DECREF(value);
    }

    if (result < 0)
        return -1;

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        return -1;

    return 0;
}

static int t_mapping_map_set(t_mapping *self, PyObject *key, PyObject *value)
{
    return _t_mapping_set(self, key, value, 1);
}

static PyObject *t_mapping_set(t_mapping *self, PyObject *args)
{
    PyObject *key, *value;
    int setDirty = 1;

    if (!PyArg_ParseTuple(args, "OO|i", &key, &value, &setDirty))
        return NULL;

    if (_t_mapping_set(self, key, value, setDirty) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_mapping_get(t_mapping *self, PyObject *args)
{
    PyObject *key, *defaultValue = Py_None;
    PyObject *value;

    if (!PyArg_ParseTuple(args, "O|O", &key, &defaultValue))
        return NULL;

    value = t_mapping_map_get(self, key);
    if (!value && PyErr_ExceptionMatches(PyExc_KeyError))
    {
        PyErr_Clear();
        Py_INCREF(defaultValue);
        value = defaultValue;
    }

    return value;
}

static PyObject *t_mapping_setdefault(t_mapping *self, PyObject *args)
{
    PyObject *key, *defaultValue = Py_None;
    int setDirty = 1;
    PyObject *value;

    if (!PyArg_ParseTuple(args, "O|Oi", &key, &defaultValue, &setDirty))
        return NULL;

    value = t_mapping_map_get(self, key);
    if (!value && PyErr_ExceptionMatches(PyExc_KeyError))
    {
        PyErr_Clear();
        if (_t_mapping_set(self, key, defaultValue, setDirty) < 0)
            return NULL;

        Py_INCREF(defaultValue);
        value = defaultValue;
    }

    return value;
}

static PyObject *t_mapping_pop(t_mapping *self, PyObject *args)
{
    PyObject *key, *defaultValue = Py_None;
    PyObject *value;

    if (!PyArg_ParseTuple(args, "O|O", &key, &defaultValue))
        return NULL;

    value = t_mapping_map_get(self, key);
    if (!value && PyErr_ExceptionMatches(PyExc_KeyError))
    {
        PyErr_Clear();
        Py_INCREF(defaultValue);
        value = defaultValue;
    }
    else if (PyObject_DelItem((PyObject *) self, key) < 0)
    {
        Py_DECREF(value);
        return NULL;
    }

    return value;
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

static PyObject *t_mapping_items(t_mapping *self)
{
    PyObject *items = PyMapping_Items(self->mapping);
    
    if (!items)
        return NULL;

    if (!PyList_Check(items))
    {
        PyErr_SetObject(PyExc_TypeError, items);
        Py_DECREF(items);
        return NULL;
    }

    if (!(self->itemvalue.flags & V_PURE))
    {
        int size = PyList_GET_SIZE(items);
        int i;

        for (i = 0; i < size; i++) {
            PyObject *pair = PyList_GET_ITEM(items, i);
            PyObject *value;

            if (!_check_pair(pair) < 0)
            {
                Py_DECREF(items);
                return NULL;
            }

            value = _restoreValue(self, PyTuple_GET_ITEM(pair, 1));
            if (!value)
            {
                Py_DECREF(items);
                return NULL;
            }

            pair = PyTuple_Pack(2, PyTuple_GET_ITEM(pair, 0), value);
            Py_DECREF(value);
            if (PyList_SetItem(items, i, pair) < 0)
            {
                Py_DECREF(items);
                return NULL;
            }
        }
    }

    return items;
}

static PyObject *t_mapping_keys(t_mapping *self)
{
    return PyMapping_Keys(self->mapping);
}

static PyObject *t_mapping_values(t_mapping *self)
{
    PyObject *values = PyMapping_Values(self->mapping);
    
    if (!values)
        return NULL;

    if (!PyList_Check(values))
    {
        PyErr_SetObject(PyExc_TypeError, values);
        Py_DECREF(values);
        return NULL;
    }

    if (!(self->itemvalue.flags & V_PURE))
    {
        int size = PyList_GET_SIZE(values);
        int i;

        for (i = 0; i < size; i++) {
            PyObject *value = PyList_GET_ITEM(values, i);

            value = _restoreValue(self, value);
            if (!value)
            {
                Py_DECREF(values);
                return NULL;
            }

            if (PyList_SetItem(values, i, value) < 0)
            {
                Py_DECREF(values);
                return NULL;
            }
        }
    }

    return values;
}

static PyObject *t_mapping__useValue(t_mapping *self, PyObject *value)
{
    if (self->itemvalue.flags & V_PURE)
        Py_INCREF(value);
    else
        value = _useValue(self, value);

    return value;
}


void _init_mapping(PyObject *m)
{
    MappingType.tp_base = ItemValue;

    if (PyType_Ready(&MappingType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&MappingType);
            PyModule_AddObject(m, "PersistentMapping",
                               (PyObject *) &MappingType);

            restoreValue_NAME = PyString_FromString("restoreValue");
            useValue_NAME = PyString_FromString("useValue");
            prepareValue_NAME = PyString_FromString("prepareValue");
        }
    }
}
