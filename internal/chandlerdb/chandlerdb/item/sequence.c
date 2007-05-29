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

static void t_sequence_dealloc(t_sequence *self);
static int t_sequence_traverse(t_sequence *self, visitproc visit, void *arg);
static int t_sequence_clear(t_sequence *self);
static PyObject *t_sequence_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds);
static int t_sequence_init(t_sequence *self, PyObject *args, PyObject *kwds);
static PyObject *t_sequence_repr(t_sequence *self);
static PyObject *t_sequence_str(t_sequence *self);
static long t_sequence_hash(t_sequence *self);
static PyObject *t_sequence_iter(t_sequence *self);
static PyObject *t_sequence_richcompare(t_sequence *self, PyObject *value,
                                        int op);
static PyObject *t_sequence_index(t_sequence *self, PyObject *value);
static PyObject *t_sequence_count(t_sequence *self, PyObject *value);
static PyObject *t_sequence_append(t_sequence *self, PyObject *args);
static PyObject *t_sequence_extend(t_sequence *self, PyObject *args);
static PyObject *t_sequence_insert(t_sequence *self, PyObject *args);
static PyObject *t_sequence_pop(t_sequence *self, PyObject *args);
static PyObject *t_sequence__useValue(t_sequence *self, PyObject *value);

static Py_ssize_t t_sequence_seq_length(t_sequence *self);
static PyObject *t_sequence_seq_get(t_sequence *self, Py_ssize_t n);
static int t_sequence_seq_contains(t_sequence *self, PyObject *value);
static PyObject *t_sequence_seq_concat(t_sequence *self, PyObject *arg);
static PyObject *t_sequence_seq_repeat(t_sequence *self, Py_ssize_t n);
static PyObject *t_sequence_seq_getslice(t_sequence *self, Py_ssize_t low,
                                         Py_ssize_t high);
static int t_sequence_seq_set(t_sequence *self, Py_ssize_t i, PyObject *value);
static int t_sequence_seq_setslice(t_sequence *self, Py_ssize_t low,
                                   Py_ssize_t high, PyObject *arg);
static PyObject *t_sequence_seq_inplace_concat(t_sequence *self, PyObject *arg);
static PyObject *t_sequence_seq_inplace_repeat(t_sequence *self, Py_ssize_t n);

static PyObject *t_sequence_map_get(t_sequence* self, PyObject *item);



static PyObject *useValue_NAME;
static PyObject *prepareValue_NAME;
static PyObject *restoreValue_NAME;
static PyObject *__getitem___NAME;

static PyMemberDef t_sequence_members[] = {
    { "_sequence", T_OBJECT, offsetof(t_sequence, sequence), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyGetSetDef t_sequence_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};

static PyMethodDef t_sequence_methods[] = {
    { "index", (PyCFunction) t_sequence_index, METH_O, NULL },
    { "count", (PyCFunction) t_sequence_count, METH_O, NULL },
    { "append", (PyCFunction) t_sequence_append, METH_VARARGS, NULL },
    { "add", (PyCFunction) t_sequence_append, METH_VARARGS, NULL },
    { "extend", (PyCFunction) t_sequence_extend, METH_VARARGS, NULL },
    { "insert", (PyCFunction) t_sequence_insert, METH_VARARGS, NULL },
    { "pop", (PyCFunction) t_sequence_pop, METH_VARARGS, NULL },
    { "_useValue", (PyCFunction) t_sequence__useValue, METH_O, NULL },
    { NULL, NULL, 0, NULL }
};

static PyMappingMethods t_sequence_as_mapping = {
    (lenfunc)t_sequence_seq_length,            /* mp_length          */
    (binaryfunc)t_sequence_map_get,            /* mp_subscript       */
    0,                                         /* mp_ass_subscript   */
};

static PySequenceMethods t_sequence_as_sequence = {
    (lenfunc)t_sequence_seq_length,                 /* sq_length */
    (binaryfunc)t_sequence_seq_concat,              /* sq_concat */
    (ssizeargfunc)t_sequence_seq_repeat,            /* sq_repeat */
    (ssizeargfunc)t_sequence_seq_get,               /* sq_item */
    (ssizessizeargfunc)t_sequence_seq_getslice,     /* sq_slice */
    (ssizeobjargproc)t_sequence_seq_set,            /* sq_ass_item */
    (ssizessizeobjargproc)t_sequence_seq_setslice,  /* sq_ass_slice */
    (objobjproc)t_sequence_seq_contains,            /* sq_contains */
    (binaryfunc)t_sequence_seq_inplace_concat,      /* sq_inplace_concat */
    (ssizeargfunc)t_sequence_seq_inplace_repeat,    /* sq_inplace_repeat */
};


static PyTypeObject SequenceType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.PersistentSequence",    /* tp_name */
    sizeof(t_sequence),                        /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_sequence_dealloc,            /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    (reprfunc)t_sequence_repr,                 /* tp_repr */
    0,                                         /* tp_as_number */
    &t_sequence_as_sequence,                   /* tp_as_sequence */
    &t_sequence_as_mapping,                    /* tp_as_mapping */
    (hashfunc)t_sequence_hash,                 /* tp_hash  */
    0,                                         /* tp_call */
    (reprfunc)t_sequence_str,                  /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "C PersistentSequence type",               /* tp_doc */
    (traverseproc)t_sequence_traverse,         /* tp_traverse */
    (inquiry)t_sequence_clear,                 /* tp_clear */
    (richcmpfunc)t_sequence_richcompare,       /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    (getiterfunc)t_sequence_iter,              /* tp_iter */
    0,                                         /* tp_iternext */
    t_sequence_methods,                        /* tp_methods */
    t_sequence_members,                        /* tp_members */
    t_sequence_properties,                     /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_sequence_init,                 /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_sequence_new,                   /* tp_new */
};


static void t_sequence_dealloc(t_sequence *self)
{
    t_sequence_clear(self);
    self->itemvalue.persistentvalue.ob_type->tp_free((PyObject *) self);
}

static int t_sequence_traverse(t_sequence *self, visitproc visit, void *arg)
{
    Py_VISIT(self->sequence);
    ItemValue->tp_traverse((PyObject *) self, visit, arg);

    return 0;
}

static int t_sequence_clear(t_sequence *self)
{
    Py_CLEAR(self->sequence);
    ItemValue->tp_clear((PyObject *) self);

    return 0;
}

static PyObject *t_sequence_new(PyTypeObject *type,
                                PyObject *args, PyObject *kwds)
{
    t_sequence *self = (t_sequence *) type->tp_alloc(type, 0);

    if (self)
    {
        self->itemvalue.owner = NULL;
        self->itemvalue.attribute = NULL;
        self->itemvalue.flags = 0;
        self->sequence = NULL;
    }

    return (PyObject *) self;
}

static int t_sequence_init(t_sequence *self, PyObject *args, PyObject *kwds)
{
    PyObject *sequence, *view = Py_None, *item = Py_None, *attribute = Py_None;
    int pure = 0;

    if (!PyArg_ParseTuple(args, "O|OOOi", &sequence,
                          &view, &item, &attribute, &pure))
        return -1;

    if (!PySequence_Check(sequence))
    {
        PyErr_SetObject(PyExc_TypeError, sequence);
        return -1;
    }

    if (_t_itemvalue_init((t_itemvalue *) self, view, item, attribute) < 0)
        return -1;

    Py_INCREF(sequence);
    Py_XDECREF(self->sequence);
    self->sequence = sequence;

    if (pure)
        self->itemvalue.flags |= V_PURE;

    return 0;
}

static PyObject *t_sequence_repr(t_sequence *self)
{
    PyObject *str = PyObject_Str(self->sequence);

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

static PyObject *t_sequence_str(t_sequence *self)
{
    return PyObject_Str(self->sequence);
}

static long t_sequence_hash(t_sequence *self)
{
    return PyObject_Hash(self->sequence);
}

static PyObject *_restoreValue(t_sequence *self, PyObject *value)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, restoreValue_NAME,
                                      value, NULL);
}

static int _restoreValues(t_sequence *self, PyObject *values)
{
    int size = PySequence_Size(values);
    int i, isTuple;

    if (size < 0)
        return -1;

    isTuple = PyTuple_Check(values);

    for (i = 0; i < size; i++) {
        PyObject *value = PySequence_GetItem(values, i);
        PyObject *v;

        if (!value)
            return -1;

        v = _restoreValue(self, value);
        Py_DECREF(value);
        if (!v)
            return -1;

        if (v == value)
            Py_DECREF(v);
        else if (isTuple)
        {
            if (PyTuple_SetItem(values, i, v) < 0)
            {
                Py_DECREF(v);
                return -1;
            }
        }
        else if (PySequence_SetItem(values, i, v) < 0)
        {
            Py_DECREF(v);
            return -1;
        }
        else
            Py_DECREF(v);
    }

    return 0;
}

static PyObject *_useValue(t_sequence *self, PyObject *value)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, useValue_NAME,
                                      value, NULL);
}

static PyObject *_prepareValue(t_sequence *self, PyObject *value)
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

PyObject *_prepareValues(t_itemvalue *self, PyObject *values)
{
    PyObject *item = PyObject_Call(self->owner, Empty_TUPLE, NULL);
    PyObject *result;
    int i, size;

    if (!item)
        return NULL;

    if (!PySequence_Check(values))
    {
        PyObject *args = PyTuple_Pack(1, values);

        values = PyObject_Call((PyObject *) &PyTuple_Type, args, NULL);
        Py_DECREF(args);
        if (!values)
        {
            Py_DECREF(item);
            return NULL;
        }
    }
    else
    {
        values = PySequence_Fast(values, "not a sequence");
        if (!values)
        {
            Py_DECREF(item);
            return NULL;
        }
    }

    size = PySequence_Fast_GET_SIZE(values);
    if (size < 0)
    {
        Py_DECREF(item);
        Py_DECREF(values);
        return NULL;
    }

    result = PyTuple_New(size);
    if (!result)
    {
        Py_DECREF(item);
        Py_DECREF(values);
        return NULL;
    }

    for (i = 0; i < size; i++) {
        PyObject *value = PySequence_Fast_GET_ITEM(values, i);
        PyObject *v;

        if (!value)
        {
            Py_DECREF(item);
            Py_DECREF(values);
            Py_DECREF(result);
            return NULL;
        }

        v = PyObject_CallMethodObjArgs((PyObject *) self, prepareValue_NAME,
                                        item, self->attribute, value,
                                        Py_False, NULL);
        if (!v)
        {
            Py_DECREF(item);
            Py_DECREF(values);
            Py_DECREF(result);
            return NULL;
        }

        PyTuple_SET_ITEM(result, i, v);
    }
    Py_DECREF(item);
    Py_DECREF(values);

    return result;
}


static PyObject *_t_sequence__next(PyObject *target, t_iterator *iterator)
{
    t_sequence *self = (t_sequence *) target;
    PyObject *value = iterator->data->ob_type->tp_iternext(iterator->data);
    PyObject *v;

    if (!value)
        return NULL;

    v = _restoreValue(self, value);
    Py_DECREF(value);

    return v;
}

static PyObject *t_sequence_iter(t_sequence *self)
{
    PyObject *iter = PyObject_GetIter(self->sequence);

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
            iterator->nextFn = _t_sequence__next;
        }
        iter = (PyObject *) iterator;
    }

    return iter;
}

static int _compare(t_sequence *self,
                    PyObject *sequence, PyObject *value, int i0, int i1,
                    int op, int *cmp)
{
    PyObject *v0 = PySequence_Fast_GET_ITEM(sequence, i0);
    PyObject *v1 = PySequence_Fast_GET_ITEM(value, i1);

    if (!v0 || !v1)
        return -1;

    if (self->itemvalue.flags & V_PURE)
        *cmp = PyObject_RichCompareBool(v0, v1, op);
    else
    {
        PyObject *v = _useValue(self, v0);
                
        if (!v)
            return -1;
        *cmp = PyObject_RichCompareBool(v, v1, op);
        Py_DECREF(v);
    }
                    
    if (*cmp < 0)
        return -1;

    return 0;
}

static PyObject *t_sequence_richcompare(t_sequence *self, PyObject *value,
                                        int op)
{
    PyObject *result = NULL;
    int s0, s1;

    if (!PySequence_Check(value))
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    value = PySequence_Fast(value, "not a sequence");
    if (!value)
        return NULL;

    s0 = PySequence_Fast_GET_SIZE(value);
    s1 = PySequence_Size(self->sequence);

    if (s1 < 0)
    {
        Py_DECREF(value);
        return NULL;
    }

    if (s0 != s1)
    {
        switch (op) {
          case Py_EQ: result = Py_False; break;
          case Py_NE: result = Py_True; break;
        }
    }

    if (!result)
    {
        PyObject *sequence = PySequence_Fast(self->sequence, "not a sequence");
        int i0, i1, cmp = 1;

        if (!sequence)
        {
            Py_DECREF(value);
            return NULL;
        }

        for (i0 = 0, i1 = 0; i0 < s0 && i1 < s1 && cmp; i0++, i1++) {
            if (_compare(self, sequence, value, i0, i1, Py_EQ, &cmp) < 0)
            {
                Py_DECREF(sequence);
                Py_DECREF(value);
                return NULL;
            }                
        }

        if (cmp)
        {
            switch (op) {
              case Py_LT: cmp = s0 < s1; break;
              case Py_LE: cmp = s0 <= s1; break;
              case Py_EQ: cmp = s0 == s1; break;
              case Py_NE: cmp = s0 != s1; break;
              case Py_GT: cmp = s0 > s1; break;
              case Py_GE: cmp = s0 >= s1; break;
              default: cmp = 0;
            }

            result = cmp ? Py_True : Py_False;
        }
        else if (op == Py_EQ)
            result = Py_False;
        else if (op == Py_NE)
            result = Py_True;
        else if (_compare(self, sequence, value, i0, i1, op, &cmp) < 0)
        {
            Py_DECREF(sequence);
            Py_DECREF(value);
            return NULL;
        }
        else
            result = cmp ? Py_True : Py_False;

        Py_DECREF(sequence);
    }
    Py_DECREF(value);

    Py_INCREF(result);
    return result;
}

static Py_ssize_t t_sequence_seq_length(t_sequence *self)
{
    return PySequence_Size(self->sequence);
}

static PyObject *t_sequence_seq_get(t_sequence *self, Py_ssize_t i)
{
    PyObject *value = PySequence_GetItem(self->sequence, i);

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

static int t_sequence_seq_contains(t_sequence *self, PyObject *value)
{
    int result;

    if (self->itemvalue.flags & V_PURE)
        result = PySequence_Contains(self->sequence, value);
    else
    {
        value = _useValue(self, value);
        if (!value)
            return -1;

        result = PySequence_Contains(self->sequence, value);
        Py_DECREF(value);
    }

    return result;
}

static PyObject *t_sequence_seq_concat(t_sequence *self, PyObject *arg)
{
    if (self->itemvalue.flags & V_PURE)
        return PySequence_Concat(self->sequence, arg);
    else
    {
        int size = PySequence_Size(self->sequence);
        PyObject *values, *result;

        if (size < 0)
            return NULL;

        values = t_sequence_seq_getslice(self, 0, size);
        if (!values)
            return NULL;

        result = PySequence_Concat(values, arg);
        Py_DECREF(values);

        return result;
    }
}

static PyObject *t_sequence_seq_repeat(t_sequence *self, Py_ssize_t n)
{
    if (self->itemvalue.flags & V_PURE)
        return PySequence_Repeat(self->sequence, n);
    else
    {
        int size = PySequence_Size(self->sequence);
        PyObject *values, *result;

        if (size < 0)
            return NULL;

        values = t_sequence_seq_getslice(self, 0, size);
        if (!values)
            return NULL;

        result = PySequence_Repeat(values, n);
        Py_DECREF(values);

        return result;
    }
}

static PyObject *t_sequence_seq_getslice(t_sequence *self, Py_ssize_t low,
                                         Py_ssize_t high)
{
    PyObject *slice = PySequence_GetSlice(self->sequence, low, high);

    if (!slice || self->itemvalue.flags & V_PURE)
        return slice;

    if (_restoreValues(self, slice) < 0)
    {
        Py_DECREF(slice);
        return NULL;
    }

    return slice;
}

static int t_sequence_seq_set(t_sequence *self, Py_ssize_t i, PyObject *value)
{
    int result;

    if (value == NULL)
        result = PySequence_DelItem(self->sequence, i);
    else if (self->itemvalue.flags & V_PURE)
        result = PySequence_SetItem(self->sequence, i, value);
    else
    {
        value = _prepareValue(self, value);
        if (!value)
            return -1;

        result = PySequence_SetItem(self->sequence, i, value);
        Py_DECREF(value);
    }

    if (result >= 0)
        result = _t_itemvalue__setDirty((t_itemvalue *) self, 0);

    return result;
}

static int t_sequence_seq_setslice(t_sequence *self, Py_ssize_t low,
                                   Py_ssize_t high, PyObject *values)
{
    int result;

    if (values == NULL)
        result = PySequence_DelSlice(self->sequence, low, high);
    else if (self->itemvalue.flags & V_PURE)
        result = PySequence_SetSlice(self->sequence, low, high, values);
    else
    {
        values = _prepareValues((t_itemvalue *) self, values);
        if (!values)
            return -1;

        result = PySequence_SetSlice(self->sequence, low, high, values);
        Py_DECREF(values);
    }

    if (result >= 0)
        result = _t_itemvalue__setDirty((t_itemvalue *) self, 0);

    return result;
}

static PyObject *t_sequence_seq_inplace_concat(t_sequence *self,
                                               PyObject *values)
{
    PyObject *result;

    if (self->itemvalue.flags & V_PURE)
        result = PySequence_InPlaceConcat(self->sequence, values);
    else
    {
        values = _prepareValues((t_itemvalue *) self, values);
        if (!values)
            return NULL;

        result = PySequence_InPlaceConcat(self->sequence, values);
        Py_DECREF(values);
    }

    if (!result)
        return NULL;

    if (result == self->sequence)
    {
        if (_t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        {
            Py_DECREF(result);
            return NULL;
        }

        Py_DECREF(result);
        Py_INCREF((PyObject *) self);
        result = (PyObject *) self;
    }
     
    return result;
}

static PyObject *t_sequence_seq_inplace_repeat(t_sequence *self, Py_ssize_t n)
{
    PyObject *result = PySequence_InPlaceRepeat(self->sequence, n);

    if (!result)
        return NULL;

    if (result == self->sequence)
    {
        if (_t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        {
            Py_DECREF(result);
            return NULL;
        }

        Py_DECREF(result);
        Py_INCREF((PyObject *) self);
        result = (PyObject *) self;
    }
     
    return result;
}

static PyObject *t_sequence_map_get(t_sequence* self, PyObject *item)
{
    PyObject *value;

    if (PyIndex_Check(item))
    {
        Py_ssize_t i = PyNumber_AsSsize_t(item, PyExc_IndexError);

        if (i == -1 && PyErr_Occurred())
            return NULL;
        value = t_sequence_seq_get(self, i);
    }
    else if ((!(self->itemvalue.flags & V_PURE)) ||
             (!((self->sequence->ob_type->tp_as_mapping &&
                 self->sequence->ob_type->tp_as_mapping->mp_subscript) ||
                (PyObject_HasAttr(self->sequence, __getitem___NAME)))))
    {
        int size = PySequence_Size(self->sequence);
        PyObject *values;

        if (size < 0)
            return NULL;

        values = t_sequence_seq_getslice(self, 0, size);
        if (!values)
            return NULL;

        value = PyObject_GetItem(values, item);
        Py_DECREF(values);
    }
    else
        value = PyObject_GetItem(self->sequence, item);
    
    return value;
}


static PyObject *t_sequence_index(t_sequence *self, PyObject *value)
{
    int index;

    if (self->itemvalue.flags & V_PURE)
        index = PySequence_Index(self->sequence, value);
    else
    {
        value = _useValue(self, value);
        if (!value)
            return NULL;

        index = PySequence_Index(self->sequence, value);
        Py_DECREF(value);
    }

    if (index < 0)
        return NULL;

    return PyInt_FromLong(index);
}

static PyObject *t_sequence_count(t_sequence *self, PyObject *value)
{
    int count;

    if (self->itemvalue.flags & V_PURE)
        count = PySequence_Count(self->sequence, value);
    else
    {
        value = _useValue(self, value);
        if (!value)
            return NULL;

        count = PySequence_Count(self->sequence, value);
        Py_DECREF(value);
    }

    if (count < 0)
        return NULL;

    return PyInt_FromLong(count);
}

static PyObject *t_sequence_append(t_sequence *self, PyObject *args)
{
    PyObject *value, *values, *result;
    int setDirty = 1;

    if (!PyArg_ParseTuple(args, "O|i", &value, &setDirty))
        return NULL;

    if (self->itemvalue.flags & V_PURE)
        values = PyTuple_Pack(1, value);
    else
    {
        value = _prepareValue(self, value);
        if (!value)
            return NULL;
        values = PyTuple_Pack(1, value);
        Py_DECREF(value);
    }

    result = PySequence_InPlaceConcat(self->sequence, values);
    Py_DECREF(values);
    if (!result)
        return NULL;

    if (result == self->sequence)
    {
        if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        {
            Py_DECREF(result);
            return NULL;
        }

        Py_DECREF(result);
        Py_RETURN_NONE;
    }

    Py_DECREF(result);
    PyErr_SetString(PyExc_NotImplementedError, "in-place concat");

    return NULL;
}

static PyObject *t_sequence_extend(t_sequence *self, PyObject *args)
{
    PyObject *values, *result;
    int setDirty = 1;

    if (!PyArg_ParseTuple(args, "O|i", &values, &setDirty))
        return NULL;

    if (self->itemvalue.flags & V_PURE)
        result = PySequence_InPlaceConcat(self->sequence, values);
    else
    {
        values = _prepareValues((t_itemvalue *) self, values);
        if (!values)
            return NULL;
        result = PySequence_InPlaceConcat(self->sequence, values);
        Py_DECREF(values);
    }

    if (!result)
        return NULL;

    if (result == self->sequence)
    {
        if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        {
            Py_DECREF(result);
            return NULL;
        }

        Py_DECREF(result);
        Py_RETURN_NONE;
    }

    Py_DECREF(result);
    PyErr_SetString(PyExc_NotImplementedError, "in-place concat");

    return NULL;
}

static PyObject *t_sequence_insert(t_sequence *self, PyObject *args)
{
    PyObject *value, *values;
    int index, setDirty = 1;

    if (!PyArg_ParseTuple(args, "iO|i", &index, &value, &setDirty))
        return NULL;

    if (self->itemvalue.flags & V_PURE)
        values = PyTuple_Pack(1, value);
    else
    {
        value = _prepareValue(self, value);
        if (!value)
            return NULL;
        values = PyTuple_Pack(1, value);
        Py_DECREF(value);
    }

    if (PySequence_SetSlice(self->sequence, index, index, values) < 0)
    {
        Py_DECREF(values);
        return NULL;
    }
    Py_DECREF(values);

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_sequence_pop(t_sequence *self, PyObject *args)
{
    int index = -1, setDirty = 1;
    PyObject *value;

    if (!PyArg_ParseTuple(args, "|ii", &index, &setDirty))
        return NULL;

    value = PySequence_GetItem(self->sequence, index);
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

    if (PySequence_DelItem(self->sequence, index) < 0)
    {
        Py_DECREF(value);
        return NULL;
    }

    if (setDirty && _t_itemvalue__setDirty((t_itemvalue *) self, 0) < 0)
    {
        Py_DECREF(value);
        return NULL;
    }

    return value;
}

static PyObject *t_sequence__useValue(t_sequence *self, PyObject *value)
{
    if (self->itemvalue.flags & V_PURE)
        Py_INCREF(value);
    else
        value = _useValue(self, value);

    return value;
}


void _init_sequence(PyObject *m)
{
    SequenceType.tp_base = ItemValue;

    if (PyType_Ready(&SequenceType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&SequenceType);
            PyModule_AddObject(m, "PersistentSequence",
                               (PyObject *) &SequenceType);

            restoreValue_NAME = PyString_FromString("restoreValue");
            useValue_NAME = PyString_FromString("useValue");
            prepareValue_NAME = PyString_FromString("prepareValue");
            __getitem___NAME = PyString_FromString("__getitem__");
        }
    }
}
