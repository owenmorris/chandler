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
    PyObject *set;
} t_set;

static void t_set_dealloc(t_set *self);
static int t_set_traverse(t_set *self, visitproc visit, void *arg);
static int t_set_clear_(t_set *self);
static PyObject *t_set_new(PyTypeObject *type,
                           PyObject *args, PyObject *kwds);
static int t_set_init(t_set *self, PyObject *args, PyObject *kwds);
static PyObject *t_set_repr(t_set *self);
static PyObject *t_set_str(t_set *self);
static long t_set_hash(t_set *self);
static PyObject *t_set_iter(t_set *self);

static PyObject *t_set_add(t_set *self, PyObject *args);
static PyObject *t_set_update(t_set *self, PyObject *args);
static PyObject *t_set_pop(t_set *self, PyObject *args);
static PyObject *t_set_remove(t_set *self, PyObject *args);
static PyObject *t_set_discard(t_set *self, PyObject *args);
static PyObject *t_set_clear(t_set *self, PyObject *args);
static PyObject *t_set__useValue(t_set *self, PyObject *value);

static PyObject *t_set_num_subtract(t_set *self, PyObject *value);
static PyObject *t_set_num_and(t_set *self, PyObject *value);
static PyObject *t_set_num_xor(t_set *self, PyObject *value);
static PyObject *t_set_num_or(t_set *self, PyObject *value);
static PyObject *t_set_num_inplace_subtract(t_set *self, PyObject *value);
static PyObject *t_set_num_inplace_and(t_set *self, PyObject *value);
static PyObject *t_set_num_inplace_xor(t_set *self, PyObject *value);
static PyObject *t_set_num_inplace_or(t_set *self, PyObject *value);

static Py_ssize_t t_set_seq_length(t_set *self);
static int t_set_seq_contains(t_set *self, PyObject *value);


static PyObject *useValue_NAME;
static PyObject *prepareValue_NAME;
static PyObject *restoreValue_NAME;

static PyMemberDef t_set_members[] = {
    { "_set", T_OBJECT, offsetof(t_set, set), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_set_methods[] = {
    { "add", (PyCFunction) t_set_add, METH_VARARGS, NULL },
    { "update", (PyCFunction) t_set_update, METH_VARARGS, NULL },
    { "pop", (PyCFunction) t_set_pop, METH_VARARGS, NULL },
    { "remove", (PyCFunction) t_set_remove, METH_VARARGS, NULL },
    { "discard", (PyCFunction) t_set_discard, METH_VARARGS, NULL },
    { "clear", (PyCFunction) t_set_clear, METH_VARARGS, NULL },
    { "_useValue", (PyCFunction) t_set__useValue, METH_O, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_set_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};


static PyNumberMethods t_set_as_number = {
    0,                                       /* nb_add               */
    (binaryfunc)t_set_num_subtract,          /* nb_subtract          */
    0,                                       /* nb_multiply          */
    0,                                       /* nb_divide            */
    0,                                       /* nb_remainder         */
    0,                                       /* nb_divmod            */
    0,                                       /* nb_power             */
    0,                                       /* nb_negative          */
    0,                                       /* nb_positive          */
    0,                                       /* nb_absolute          */
    0,                                       /* nb_nonzero           */
    0,                                       /* nb_invert            */
    0,                                       /* nb_lshift            */
    0,                                       /* nb_rshift            */
    (binaryfunc)t_set_num_and,               /* nb_and               */
    (binaryfunc)t_set_num_xor,               /* nb_xor               */
    (binaryfunc)t_set_num_or,                /* nb_or                */
    0,                                       /* nb_coerce            */
    0,                                       /* nb_int               */
    0,                                       /* nb_long              */
    0,                                       /* nb_float             */
    0,                                       /* nb_oct               */
    0,                                       /* nb_hex               */
    0,                                       /* nb_inplace_add       */
    (binaryfunc)t_set_num_inplace_subtract,  /* nb_inplace_subtract  */
    0,                                       /* nb_inplace_multiply  */
    0,                                       /* nb_inplace_divide    */
    0,                                       /* nb_inplace_remainder */
    0,                                       /* nb_inplace_power     */
    0,                                       /* nb_inplace_lshift    */
    0,                                       /* nb_inplace_rshift    */
    (binaryfunc)t_set_num_inplace_and,       /* nb_inplace_and       */
    (binaryfunc)t_set_num_inplace_xor,       /* nb_inplace_xor       */
    (binaryfunc)t_set_num_inplace_or,        /* nb_inplace_or        */
};

static PySequenceMethods t_set_as_sequence = {
    (lenfunc)t_set_seq_length,                  /* sq_length         */
    0,                                          /* sq_concat         */
    0,                                          /* sq_repeat         */
    0,                                          /* sq_item           */
    0,                                          /* sq_slice          */
    0,                                          /* sq_ass_item       */
    0,                                          /* sq_ass_slice      */
    (objobjproc)t_set_seq_contains,             /* sq_contains       */
    0,                                          /* sq_inplace_concat */
    0,                                          /* sq_inplace_repeat */
};

static PyTypeObject SetType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.PersistentSet",         /* tp_name */
    sizeof(t_set),                             /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_set_dealloc,                 /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    (reprfunc)t_set_repr,                      /* tp_repr */
    &t_set_as_number,                          /* tp_as_number */
    &t_set_as_sequence,                        /* tp_as_sequence */
    0,                                         /* tp_as_mapping */
    (hashfunc)t_set_hash,                      /* tp_hash  */
    0,                                         /* tp_call */
    (reprfunc)t_set_str,                       /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_CHECKTYPES |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "C PersistentSet type",                    /* tp_doc */
    (traverseproc)t_set_traverse,              /* tp_traverse */
    (inquiry)t_set_clear_,                     /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    (getiterfunc)t_set_iter,                   /* tp_iter */
    0,                                         /* tp_iternext */
    t_set_methods,                             /* tp_methods */
    t_set_members,                             /* tp_members */
    t_set_properties,                          /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_set_init,                      /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_set_new,                        /* tp_new */
};


static void t_set_dealloc(t_set *self)
{
    t_set_clear_(self);
    self->itemvalue.persistentvalue.ob_type->tp_free((PyObject *) self);
}

static int t_set_traverse(t_set *self, visitproc visit, void *arg)
{
    Py_VISIT(self->set);
    ItemValue->tp_traverse((PyObject *) self, visit, arg);

    return 0;
}

static int t_set_clear_(t_set *self)
{
    Py_CLEAR(self->set);
    ItemValue->tp_clear((PyObject *) self);

    return 0;
}

static PyObject *t_set_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds)
{
    t_set *self = (t_set *) type->tp_alloc(type, 0);

    if (self)
    {
        self->itemvalue.owner = NULL;
        self->itemvalue.attribute = NULL;
        self->itemvalue.flags = 0;
        self->set = NULL;
    }

    return (PyObject *) self;
}

static int t_set_init(t_set *self, PyObject *args, PyObject *kwds)
{
    PyObject *set, *view = Py_None, *item = Py_None, *attribute = Py_None;
    int pure = 0;

    if (!PyArg_ParseTuple(args, "O|OOOi", &set,
                          &view, &item, &attribute, &pure))
        return -1;

    if (!PyObject_TypeCheck(set, &PySet_Type))
    {
        PyErr_SetObject(PyExc_TypeError, set);
        return -1;
    }

    if (_t_itemvalue_init((t_itemvalue *) self, view, item, attribute) < 0)
        return -1;

    Py_INCREF(set);
    Py_XDECREF(self->set);
    self->set = set;

    if (pure)
        self->itemvalue.flags |= V_PURE;

    return 0;
}

static PyObject *t_set_repr(t_set *self)
{
    PyObject *str = PyObject_Str(self->set);

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

static PyObject *t_set_str(t_set *self)
{
    return PyObject_Str(self->set);
}

static long t_set_hash(t_set *self)
{
    return PyObject_Hash(self->set);
}


static PyObject *_restoreValue(t_set *self, PyObject *value)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, restoreValue_NAME,
                                      value, NULL);
}

static PyObject *_useValue(t_set *self, PyObject *value)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, useValue_NAME,
                                      value, NULL);
}

static PyObject *_prepareValue(t_set *self, PyObject *value)
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


static PyObject *_t_set__next(PyObject *target, t_iterator *iterator)
{
    t_set *self = (t_set *) target;
    PyObject *value = iterator->data->ob_type->tp_iternext(iterator->data);
    PyObject *v;

    if (!value)
        return NULL;

    v = _restoreValue(self, value);
    Py_DECREF(value);

    return v;
}

static PyObject *t_set_iter(t_set *self)
{
    PyObject *iter = PyObject_GetIter(self->set);

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
            iterator->nextFn = _t_set__next;
        }
        iter = (PyObject *) iterator;
    }

    return iter;
}


static PyObject *_t_set_binary(t_set *self, PyObject *value,
                               int setDirty, binaryfunc fn)
{
    PyObject *result;

    if (self->itemvalue.flags & V_PURE)
        result = (*fn)(self->set, value);
    else
    {
        value = _useValue(self, value);
        if (!value)
            return NULL;
        result = (*fn)(self->set, value);
        Py_DECREF(value);
    }

    if (!result)
        return NULL;

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
    {
        Py_DECREF(result);
        return NULL;
    }

    return result;
}

static PyObject *t_set_num_subtract(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 0,
                         self->set->ob_type->tp_as_number->nb_subtract);
}

static PyObject *t_set_num_and(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 0,
                         self->set->ob_type->tp_as_number->nb_and);
}

static PyObject *t_set_num_xor(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 0,
                         self->set->ob_type->tp_as_number->nb_xor);
}

static PyObject *t_set_num_or(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 0,
                         self->set->ob_type->tp_as_number->nb_or);
}

static PyObject *t_set_num_inplace_subtract(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 1,
                         self->set->ob_type->tp_as_number->nb_inplace_subtract);
}

static PyObject *t_set_num_inplace_and(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 1,
                         self->set->ob_type->tp_as_number->nb_inplace_and);
}

static PyObject *t_set_num_inplace_xor(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 1,
                         self->set->ob_type->tp_as_number->nb_inplace_xor);
}

static PyObject *t_set_num_inplace_or(t_set *self, PyObject *value)
{
    return _t_set_binary(self, value, 1,
                         self->set->ob_type->tp_as_number->nb_inplace_or);
}


static Py_ssize_t t_set_seq_length(t_set *self)
{
    return PySet_Size(self->set);
}

static int t_set_seq_contains(t_set *self, PyObject *value)
{
    int result;

    if (self->itemvalue.flags & V_PURE)
        result = PySet_Contains(self->set, value);
    else
    {
        value = _useValue(self, value);
        if (!value)
            return -1;

        result = PySet_Contains(self->set, value);
        Py_DECREF(value);
    }

    return result;
}


static PyObject *t_set_add(t_set *self, PyObject *args)
{
    PyObject *value;
    int setDirty = 1, result;

    if (!PyArg_ParseTuple(args, "O|i", &value, &setDirty))
        return NULL;

    if (self->itemvalue.flags & V_PURE)
        result = PySet_Add(self->set, value);
    else
    {
        value = _prepareValue(self, value);
        if (!value)
            return NULL;
        result = PySet_Add(self->set, value);
        Py_DECREF(value);
    }

    if (result < 0)
        return NULL;

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_set_update(t_set *self, PyObject *args)
{
    PyObject *values;
    int setDirty = 1, result;

    if (!PyArg_ParseTuple(args, "O|i", &values, &setDirty))
        return NULL;

    if (self->itemvalue.flags & V_PURE)
        result = _PySet_Update(self->set, values);
    else
    {
        values = _prepareValues((t_itemvalue *) self, values);
        if (!values)
            return NULL;
        result = _PySet_Update(self->set, values);
        Py_DECREF(values);
    }

    if (result < 0)
        return NULL;

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_set_pop(t_set *self, PyObject *args)
{
    PyObject *value;
    int setDirty = 1;

    if (!PyArg_ParseTuple(args, "|i", &setDirty))
        return NULL;

    value = PySet_Pop(self->set);
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

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
    {
        Py_DECREF(value);
        return NULL;
    }

    return value;
}

static PyObject *t_set_remove(t_set *self, PyObject *args)
{
    PyObject *value;
    int setDirty = 1, result;

    if (!PyArg_ParseTuple(args, "O|i", &value, &setDirty))
        return NULL;

    if (self->itemvalue.flags & V_PURE)
    {
        result = PySet_Discard(self->set, value);
        if (result == 0)
        {
            PyErr_SetObject(PyExc_KeyError, value);
            return NULL;
        }
    }
    else
    {
        value = _useValue(self, value);
        if (!value)
            return NULL;
        result = PySet_Discard(self->set, value);
        if (result == 0)
        {
            PyErr_SetObject(PyExc_KeyError, value);
            Py_DECREF(value);
            return NULL;
        }
        Py_DECREF(value);
    }

    if (result < 0)
        return NULL;

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_set_discard(t_set *self, PyObject *args)
{
    PyObject *value;
    int setDirty = 1, result;

    if (!PyArg_ParseTuple(args, "O|i", &value, &setDirty))
        return NULL;

    if (self->itemvalue.flags & V_PURE)
        result = PySet_Discard(self->set, value);
    else
    {
        value = _useValue(self, value);
        if (!value)
            return NULL;
        result = PySet_Discard(self->set, value);
        Py_DECREF(value);
    }

    if (result < 0)
        return NULL;

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_set_clear(t_set *self, PyObject *args)
{
    int setDirty = 1, result;

    if (!PyArg_ParseTuple(args, "|i", &setDirty))
        return NULL;

    result = PySet_Clear(self->set);
    if (result < 0)
        return NULL;

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_set__useValue(t_set *self, PyObject *value)
{
    if (self->itemvalue.flags & V_PURE)
        Py_INCREF(value);
    else
        value = _useValue(self, value);

    return value;
}


void _init_set(PyObject *m)
{
    SetType.tp_base = ItemValue;

    if (PyType_Ready(&SetType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&SetType);
            PyModule_AddObject(m, "PersistentSet", (PyObject *) &SetType);

            restoreValue_NAME = PyString_FromString("restoreValue");
            useValue_NAME = PyString_FromString("useValue");
            prepareValue_NAME = PyString_FromString("prepareValue");
        }
    }
}
