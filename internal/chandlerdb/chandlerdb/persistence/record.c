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

#if defined(_MSC_VER)
#include <winsock2.h>
#elif defined(__MACH__)
#include <arpa/inet.h>
#elif defined(linux)
#include <netinet/in.h>
#else
#error system is not linux, os x or winnt
#endif

#include <Python.h>
#include "structmember.h"

#include "c.h"


static PyObject *t_record_new_write(PyTypeObject *type,
                                    PyObject *args, PyObject *kwds);
static void t_record_dealloc(t_record *self);
static int t_record_init(t_record *self, PyObject *args, PyObject *kwds);
static PyObject *t_record_str(t_record *self);
static Py_ssize_t t_record_length(t_record *self);
static PyObject *t_record_item(t_record *self, Py_ssize_t i);
static PyObject *t_record_slice(t_record *self, Py_ssize_t l, Py_ssize_t h);
static int t_record_contains(t_record *self, PyObject *arg);
static PyObject *t_record_inplace_concat(t_record *self, PyObject *obj);
static PyObject *t_record__getData(t_record *self, void *data);
static PyObject *t_record__getTypes(t_record *self, void *data);
static PyObject *t_record_read(t_record *self, PyObject *arg);

static PyMemberDef t_record_members[] = {
    { "size", T_UINT, offsetof(t_record, size), READONLY, "" },
    { "_pairs", T_OBJECT, offsetof(t_record, pairs), READONLY, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_record_methods[] = {
    { "read", (PyCFunction) t_record_read, METH_O, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_record_properties[] = {
    { "data", (getter) t_record__getData, NULL, "", NULL },
    { "types", (getter) t_record__getTypes, NULL, "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PySequenceMethods record_as_sequence = {
    (lenfunc) t_record_length,              /* sq_length */
    0,                                      /* sq_concat */
    0,					    /* sq_repeat */
    (ssizeargfunc) t_record_item,           /* sq_item */
    (ssizessizeargfunc) t_record_slice,     /* sq_slice */
    0,                                      /* sq_ass_item */
    0,                                      /* sq_ass_slice */
    (objobjproc) t_record_contains,         /* sq_contains */
    (binaryfunc) t_record_inplace_concat,   /* sq_inplace_concat */
    0,                                      /* sq_inplace_repeat */
};


static PyTypeObject RecordType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.util.c.Record",                /* tp_name */
    sizeof(t_record),                          /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor) t_record_dealloc,             /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    0,                                         /* tp_repr */
    0,                                         /* tp_as_number */
    &record_as_sequence,                       /* tp_as_sequence */
    0,                                         /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    (reprfunc) t_record_str,                   /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                        /* tp_flags */
    "Record type",                             /* tp_doc */
    0,                                         /* tp_traverse */
    0,                                         /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    0,                                         /* tp_iter */
    0,                                         /* tp_iternext */
    t_record_methods,                          /* tp_methods */
    t_record_members,                          /* tp_members */
    t_record_properties,                       /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc) t_record_init,                  /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc) t_record_new_write,              /* tp_new */
};


static PyObject *t_record_new_write(PyTypeObject *type,
                                    PyObject *args, PyObject *kwds)
{
    t_record *self = (t_record *) type->tp_alloc(type, 0);

    if (self)
    {
        self->size = 0;
        self->pairs = PyList_New(0);
        self->partial = NULL;
    }

    return (PyObject *) self;
}

/* if args is a tuple, create a new record for reading from it
 * if args is a record, reset it for reading
 */
t_record *_t_record_new_read(PyObject *args)
{
    if (args->ob_type == Record)
    {
        t_record *record = (t_record *) args; 
        PyObject *pairs = record->pairs;
        int count = PyList_GET_SIZE(pairs);
        int i;

        record->size = 0;
        Py_CLEAR(record->partial);

        for (i = 0; i < count; i += 2) {
            PyObject *arg = PyList_GET_ITEM(pairs, i);
            int valueType = PyInt_AS_LONG(arg);

            if (valueType < 0)
                PyList_SetItem(pairs, i, PyInt_FromLong(-valueType));
                
            Py_INCREF(Nil);
            PyList_SetItem(pairs, i + 1, Nil);
        }

        Py_INCREF((PyObject *) record);
        return record;
    }
    
    if (PyTuple_CheckExact(args))
    {
        t_record *self = (t_record *) Record->tp_alloc(Record, 0);

        if (self)
        {
            int count = PyTuple_GET_SIZE(args);
            PyObject *list = PyList_New(count*2);
            int i;

            self->size = 0;
            self->pairs = list;
            self->partial = NULL;

            for (i = 0; i < count; i++) {
                PyObject *arg = PyTuple_GET_ITEM(args, i);

                if (!PyInt_CheckExact(arg))
                {
                    PyErr_SetObject(PyExc_TypeError, arg);
                    Py_DECREF(self);
                    return NULL;
                }

                PyList_SET_ITEM(list, i*2, arg); Py_INCREF(arg);
                PyList_SET_ITEM(list, i*2 + 1, Nil); Py_INCREF(Nil);
            }
        }

        return self;
    }

    PyErr_SetObject(PyExc_TypeError, args);
    return NULL;
}

static void t_record_dealloc(t_record *self)
{
    Py_CLEAR(self->pairs);
    Py_CLEAR(self->partial);

    self->ob_type->tp_free((PyObject *) self);
}

static int t_record_init(t_record *self, PyObject *args, PyObject *kwds)
{
    return _t_record_inplace_concat(self, args);
}

static PyObject *t_record_str(t_record *self)
{
    PyObject *str = PyString_FromStringAndSize(NULL, self->size);

    if (str && _t_record_write(self, (unsigned char *) PyString_AS_STRING(str),
                               self->size) < 0)
        Py_CLEAR(str);

    return str;
}

static Py_ssize_t t_record_length(t_record *self)
{
    return PyList_GET_SIZE(self->pairs) >> 1;
}

PyObject *_t_record_item(t_record *self, Py_ssize_t i)
{
    int count = PyList_GET_SIZE(self->pairs) >> 1;

    if (i < 0)
        i = count + i;

    return PyList_GetItem(self->pairs, i*2 + 1);
}

static PyObject *t_record_item(t_record *self, Py_ssize_t i)
{
    PyObject *value = _t_record_item(self, i);

    if (value)
        Py_INCREF(value);

    return value;
}

static PyObject *t_record_slice(t_record *self, Py_ssize_t l, Py_ssize_t h)
{
    int count = PyList_GET_SIZE(self->pairs) >> 1;
    PyObject *tuple;

    if (l < 0)
        l = count + l;
    if (h < 0)
        h = count + h;

    if (l >= 0 && l <= count && h >= 0 && h <= count && h > l)
    {
        int i, j, size = h - l;

        tuple = PyTuple_New(size);
        if (tuple)
            for (i = 0, j = l; i < size; i++, j++) {
                PyObject *value = PyList_GET_ITEM(self->pairs, j*2 + 1);
                PyTuple_SET_ITEM(tuple, i, value);
                Py_INCREF(value);
            }
    }
    else
        tuple = PyTuple_New(0);

    return tuple;
}

static int t_record_contains(t_record *self, PyObject *arg)
{
    int count = PyList_GET_SIZE(self->pairs);
    int i, cmp;

    for (i = 0, cmp = 0; !cmp && i < count; i += 2)
        cmp = PyObject_RichCompareBool(arg,
                                       PyList_GET_ITEM(self->pairs, i + 1),
                                       Py_EQ);

    return cmp;
}

int _t_record_inplace_concat(t_record *self, PyObject *args)
{
    int i, size, vsize, count;

    if (!PyTuple_CheckExact(args))
    {
        PyErr_SetObject(PyExc_TypeError, args);
        return -1;
    }

    count = PyTuple_GET_SIZE(args);
    size = 0;

    if (count & 1)
    {
        PyErr_SetObject(PyExc_ValueError, args);
        return -1;
    }

    for (i = 0; i < count; i += 2) {
        PyObject *valueType = PyTuple_GET_ITEM(args, i);
        PyObject *value = PyTuple_GET_ITEM(args, i + 1);

        if (value == Nil)
            continue;

        if (!PyInt_CheckExact(valueType))
        {
            PyErr_SetObject(PyExc_TypeError, valueType);
            return -1;
        }

        switch (PyInt_AS_LONG(valueType)) {
          case R_NONE:
            if (value == Py_None)
                size += 1;
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_TRUE:
            if (value == Py_True)
                size += 1;
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_FALSE:
            if (value == Py_False)
                size += 1;
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_KEYWORD:
            if (value == Py_None)
                size += 1;
            else if (PyString_CheckExact(value))
            {
                vsize = PyString_GET_SIZE(value);
                if (vsize > 127)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 1;
                PyTuple_SetItem(args, i, PyInt_FromLong(-R_KEYWORD));
            }
            else if (PyUnicode_CheckExact(value))
            {
                value = PyUnicode_AsUTF8String(value);
                if (!value)
                    return -1;
                vsize = PyString_GET_SIZE(value);
                if (vsize > 127)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 1;
                PyTuple_SetItem(args, i + 1, value);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_SYMBOL:
            if (value == Py_None)
                size += 1;
            else if (PyString_CheckExact(value))
            {
                vsize = PyString_GET_SIZE(value);
                if (vsize > 255)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 1;
            }
            else if (PyUnicode_CheckExact(value))
            {
                value = PyUnicode_AsASCIIString(value);
                if (!value)
                    return -1;
                vsize = PyString_GET_SIZE(value);
                if (vsize > 255)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 1;
                PyTuple_SetItem(args, i + 1, value);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_UUID:
            if (PyUUID_Check(value))
                size += 16;
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_UUID_OR_NONE:
            if (value == Py_None)
                size += 1;
            else if (PyUUID_Check(value))
                size += 17;
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_UUID_OR_KEYWORD:
            if (value == Py_None)
                size += 1;
            else if (PyUUID_Check(value))
                size += 17;
            else if (PyString_CheckExact(value))
            {
                vsize = PyString_GET_SIZE(value);
                if (vsize > 127)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 2;
                PyTuple_SetItem(args, i, PyInt_FromLong(-R_UUID_OR_KEYWORD));
            }
            else if (PyUnicode_CheckExact(value))
            {
                value = PyUnicode_AsUTF8String(value);
                if (!value)
                    return -1;
                vsize = PyString_GET_SIZE(value);
                if (vsize > 127)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 2;
                PyTuple_SetItem(args, i + 1, value);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_UUID_OR_SYMBOL:
            if (value == Py_None)
                size += 1;
            else if (PyUUID_Check(value))
                size += 17;
            else if (PyString_CheckExact(value))
            {
                vsize = PyString_GET_SIZE(value);
                if (vsize > 255)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 2;
            }
            else if (PyUnicode_CheckExact(value))
            {
                value = PyUnicode_AsASCIIString(value);
                if (!value)
                    return -1;
                vsize = PyString_GET_SIZE(value);
                if (vsize > 255)
                {
                    PyErr_SetObject(PyExc_OverflowError, value);
                    return -1;
                }
                size += vsize + 2;
                PyTuple_SetItem(args, i + 1, value);
            }
            break;

          case R_STRING:
            if (PyString_CheckExact(value))
            {
                size += PyString_GET_SIZE(value) + 4;
                PyTuple_SetItem(args, i,
                                PyInt_FromLong(-PyInt_AS_LONG(valueType)));
            }
            else if (PyUnicode_CheckExact(value))
            {
                value = PyUnicode_AsUTF8String(value);
                if (!value)
                    return -1;
                size += PyString_GET_SIZE(value) + 4;
                PyTuple_SetItem(args, i + 1, value);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_STRING_OR_NONE:
            if (value == Py_None)
                size += 1;
            else if (PyString_CheckExact(value))
            {
                size += PyString_GET_SIZE(value) + 5;
                PyTuple_SetItem(args, i,
                                PyInt_FromLong(-PyInt_AS_LONG(valueType)));
            }
            else if (PyUnicode_CheckExact(value))
            {
                value = PyUnicode_AsUTF8String(value);
                if (!value)
                    return -1;
                size += PyString_GET_SIZE(value) + 5;
                PyTuple_SetItem(args, i + 1, value);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_HASH:
            if (PyString_CheckExact(value))
                size += 4;
            else if (PyUnicode_CheckExact(value))
            {
                value = PyUnicode_AsUTF8String(value);
                if (!value)
                    return -1;
                size += 4;
                PyTuple_SetItem(args, i + 1, value);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_INT:
            if (PyInt_CheckExact(value))
                size += 4;
            else if (PyFloat_CheckExact(value))
            {
                value = PyInt_FromLong((long) PyFloat_AsDouble(value));
                PyTuple_SetItem(args, i + 1, value);
                size += 4;
            }
            else if (PyLong_CheckExact(value))
            {
                value = PyInt_FromLong(PyLong_AsLong(value));
                if (PyErr_Occurred())
                {
                    Py_DECREF(value);
                    return -1;
                }
                PyTuple_SetItem(args, i + 1, value);
                size += 4;
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_SHORT:
            if (PyInt_CheckExact(value))
                size += 2;
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_BYTE:
            if (PyInt_CheckExact(value))
                size += 1;
            else if (PyString_CheckExact(value))
            {
                if (PyString_GET_SIZE(value) != 1)
                {
                    PyErr_SetObject(PyExc_ValueError, value);
                    return -1;
                }
                value = PyInt_FromLong(PyString_AS_STRING(value)[0]);
                PyTuple_SetItem(args, i + 1, value);
                size += 1;
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_BOOLEAN:
            if (value == Py_True || value == Py_False || value == Py_None)
                size += 1;
            else
            {
                PyErr_SetObject(PyExc_ValueError, value);
                return -1;
            }
            break;

          case R_LONG:
            if (PyInt_CheckExact(value))
            {
                value = PyLong_FromLong(PyInt_AS_LONG(value));
                PyTuple_SetItem(args, i + 1, value);
                size += 8;
            }
            else if (PyLong_CheckExact(value))
            {
                PyLong_AsUnsignedLongLong(value);
                if (PyErr_Occurred())
                    return -1;
                size += 8;
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_DOUBLE:
            if (PyFloat_CheckExact(value))
                size += 8;
            else if (PyInt_CheckExact(value))
            {
                value = PyFloat_FromDouble((double) PyInt_AS_LONG(value));
                PyTuple_SetItem(args, i + 1, value);
                size += 8;
            }
            else if (PyLong_CheckExact(value))
            {
                value = PyFloat_FromDouble(PyLong_AsDouble(value));
                if (PyErr_Occurred())
                    return -1;
                PyTuple_SetItem(args, i + 1, value);
                size += 8;
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          case R_RECORD:
            if (value->ob_type == Record)
            {
                size += 8;
                size += PyList_GET_SIZE(((t_record *) value)->pairs) >> 1;
                size += ((t_record *) value)->size;
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, value);
                return -1;
            }
            break;

          default:
            PyErr_SetObject(PyExc_ValueError, valueType);
            return -1;
        };
    }

    _PyList_Extend((PyListObject *) self->pairs, args);
    self->size += size;

    return 0;
}

static PyObject *t_record_inplace_concat(t_record *self, PyObject *args)
{
    if (_t_record_inplace_concat(self, args) < 0)
        return NULL;

    Py_INCREF(self);
    return (PyObject *) self;
}


/* data */

static PyObject *t_record__getData(t_record *self, void *data)
{
    PyObject *pairs = self->pairs;
    int count = PyList_GET_SIZE(pairs) >> 1;
    PyObject *tuple = PyTuple_New(count);
    int i;

    for (i = 0; i < count; i++) {
        PyObject *value = PyList_GET_ITEM(pairs, i*2 + 1);
        PyTuple_SET_ITEM(tuple, i, value);
        Py_INCREF(value);
    }

    return tuple;
}

PyObject *t_record_getData(t_record *self)
{
    return t_record__getData(self, NULL);
}


/* types */

static PyObject *t_record__getTypes(t_record *self, void *data)
{
    PyObject *pairs = self->pairs;
    int count = PyList_GET_SIZE(pairs) >> 1;
    PyObject *tuple = PyTuple_New(count);
    int i;

    for (i = 0; i < count; i++) {
        PyObject *value = PyList_GET_ITEM(pairs, i << 1);
        PyTuple_SET_ITEM(tuple, i, value);
        Py_INCREF(value);
    }

    return tuple;
}

PyObject *t_record_getTypes(t_record *self)
{
    return t_record__getTypes(self, NULL);
}


int _t_record_write(t_record *self, unsigned char *data, int len)
{
    int i, count, size, offset = 0;
    unsigned long long i64;
    unsigned long i32;
    unsigned short i16;
    unsigned char i8;

    if (len != self->size)
    {
        PyErr_SetString(PyExc_NotImplementedError, "partial record write");
        return -1;
    }

    count = PyList_GET_SIZE(self->pairs);
    for (i = 0; i < count; i += 2) {
        PyObject *valueType = PyList_GET_ITEM(self->pairs, i);
        PyObject *value = PyList_GET_ITEM(self->pairs, i + 1);

        if (value == Nil)
            continue;

        switch (PyInt_AS_LONG(valueType)) {
          case R_NONE:
            if (offset + 1 > len)
                goto overflow;
            data[offset++] = R_NONE;
            break;
            
          case R_TRUE:
            if (offset + 1 > len)
                goto overflow;
            data[offset++] = R_TRUE;
            break;
            
          case R_FALSE:
            if (offset + 1 > len)
                goto overflow;
            data[offset++] = R_FALSE;
            break;

          case R_KEYWORD:
            if (value == Py_None)
            {
                if (offset + 1 > len)
                    goto overflow;
                data[offset++] = R_NONE;
            }
            else
            {
                i8 = (unsigned char) PyString_GET_SIZE(value);
                if (offset + i8 + 1 > len)
                    goto overflow;
                data[offset++] = i8;
                memcpy(data + offset, PyString_AS_STRING(value), i8);
                offset += i8;
            }
            break;

          case -R_KEYWORD:
            i8 = (unsigned char) PyString_GET_SIZE(value);
            if (offset + i8 + 1 > len)
                goto overflow;
            data[offset++] = -i8;
            memcpy(data + offset, PyString_AS_STRING(value), i8);
            offset += i8;
            break;

          case R_SYMBOL:
            if (value == Py_None)
            {
                if (offset + 1 > len)
                    goto overflow;
                data[offset++] = R_NONE;
            }
            else
            {
                i8 = (unsigned char) PyString_GET_SIZE(value);
                if (offset + i8 + 1 > len)
                    goto overflow;
                data[offset++] = i8;
                memcpy(data + offset, PyString_AS_STRING(value), i8);
                offset += i8;
            }
            break;

          case R_UUID:
            if (offset + 16 > len)
                goto overflow;
            memcpy(data + offset,
                   PyString_AS_STRING(((t_uuid *) value)->uuid), 16);
            offset += 16;
            break;

          case R_UUID_OR_NONE:
            if (value == Py_None)
            {
                if (offset + 1 > len)
                    goto overflow;
                data[offset++] = R_NONE;
            }
            else
            {
                if (offset + 17 > len)
                    goto overflow;
                data[offset++] = R_UUID;
                memcpy(data + offset,
                       PyString_AS_STRING(((t_uuid *) value)->uuid), 16);
                offset += 16;
            }
            break;

          case R_UUID_OR_SYMBOL:
            if (value == Py_None)
            {
                if (offset + 1 > len)
                    goto overflow;
                data[offset++] = R_NONE;
            }
            else if (PyUUID_Check(value))
            {
                if (offset + 17 > len)
                    goto overflow;
                data[offset++] = R_UUID;
                memcpy(data + offset,
                       PyString_AS_STRING(((t_uuid *) value)->uuid), 16);
                offset += 16;
            }
            else
            {
                i8 = (unsigned char) PyString_GET_SIZE(value);
                if (offset + i8 + 2 > len)
                    goto overflow;
                data[offset++] = R_SYMBOL;
                data[offset++] = i8;
                memcpy(data + offset, PyString_AS_STRING(value), i8);
                offset += i8;
            }
            break;

          case R_UUID_OR_KEYWORD:
            if (value == Py_None)
            {
                if (offset + 1 > len)
                    goto overflow;
                data[offset++] = R_NONE;
            }
            else if (PyUUID_Check(value))
            {
                if (offset + 17 > len)
                    goto overflow;
                data[offset++] = R_UUID;
                memcpy(data + offset,
                       PyString_AS_STRING(((t_uuid *) value)->uuid), 16);
                offset += 16;
            }
            else
            {
                i8 = (unsigned char) PyString_GET_SIZE(value);
                if (offset + i8 + 2 > len)
                    goto overflow;
                data[offset++] = R_KEYWORD;
                data[offset++] = i8;
                memcpy(data + offset, PyString_AS_STRING(value), i8);
                offset += i8;
            }
            break;

          case -R_UUID_OR_KEYWORD:
            i8 = (unsigned char) PyString_GET_SIZE(value);
            if (offset + i8 + 2 > len)
                goto overflow;
            data[offset++] = R_KEYWORD;
            data[offset++] = -i8;
            memcpy(data + offset, PyString_AS_STRING(value), i8);
            offset += i8;
            break;

          case R_STRING:
            size = PyString_GET_SIZE(value);
            if (offset + size + 4 > len)
                goto overflow;
            *((unsigned long *) (data + offset)) = htonl(size + 1);
            offset += 4;
            memcpy(data + offset, PyString_AS_STRING(value), size);
            offset += size;
            break;

          case -R_STRING:
            size = PyString_GET_SIZE(value);
            if (offset + size + 4 > len)
                goto overflow;
            *((unsigned long *) (data + offset)) = htonl(-(size + 1));
            offset += 4;
            memcpy(data + offset, PyString_AS_STRING(value), size);
            offset += size;
            break;

          case R_STRING_OR_NONE:
            if (value == Py_None)
            {
                if (offset + 1 > len)
                    goto overflow;
                data[offset++] = R_NONE;
            }
            else
            {
                size = PyString_GET_SIZE(value);
                if (offset + size + 5 > len)
                    goto overflow;
                data[offset++] = R_STRING;
                *((unsigned long *) (data + offset)) = htonl(size + 1);
                offset += 4;
                memcpy(data + offset, PyString_AS_STRING(value), size);
                offset += size;
            }
            break;

          case -R_STRING_OR_NONE:
            size = PyString_GET_SIZE(value);
            if (offset + size + 5 > len)
                goto overflow;
            data[offset++] = R_STRING;
            *((unsigned long *) (data + offset)) = htonl(-(size + 1));
            offset += 4;
            memcpy(data + offset, PyString_AS_STRING(value), size);
            offset += size;
            break;

          case R_HASH:
            if (offset + 4 > len)
                goto overflow;
            if (PyString_CheckExact(value))
                i32 = _hash_bytes(PyString_AS_STRING(value),
                                  PyString_GET_SIZE(value));
            else
                i32 = PyInt_AS_LONG(value);
            *((unsigned long *) (data + offset)) = htonl(i32);
            offset += 4;
            break;

          case R_INT:
            if (offset + 4 > len)
                goto overflow;
            i32 = PyInt_AS_LONG(value);
            *((unsigned long *) (data + offset)) = htonl(i32);
            offset += 4;
            break;

          case R_SHORT:
            if (offset + 2 > len)
                goto overflow;
            i16 = (unsigned short) PyInt_AS_LONG(value);
            *((unsigned short *) (data + offset)) = htons(i16);
            offset += 2;
            break;

          case R_BYTE:
            if (offset + 1 > len)
                goto overflow;
            data[offset++] = (char) PyInt_AS_LONG(value);
            break;

          case R_BOOLEAN:
            if (offset + 1 > len)
                goto overflow;
            if (value == Py_True)
                data[offset++] = R_TRUE;
            else if (value == Py_False)
                data[offset++] = R_FALSE;
            else
                data[offset++] = R_NONE;
            break;

          case R_LONG:
            if (offset + 8 > len)
                goto overflow;
            i64 = PyLong_AsUnsignedLongLong(value);
            i32 = (unsigned long) (i64 >> 32);
            *((unsigned long *) (data + offset)) = htonl(i32);
            offset += 4;
            i32 = (unsigned long) (i64 & 0xffffffff);
            *((unsigned long *) (data + offset)) = htonl(i32);
            offset += 4;
            break;

          case R_DOUBLE:
            if (offset + 8 > len)
                goto overflow;
            _PyFloat_Pack8(PyFloat_AsDouble(value), data + offset, 0);
            offset += 8;
            break;

          case R_RECORD:
          {
              t_record *record = (t_record *) value;
              PyObject *pairs = record->pairs;
              int count = PyList_GET_SIZE(pairs);
              int c32 = count >> 1;
              int v;

              if (offset + c32 + record->size + 8 > len)
                  goto overflow;

              i32 = record->size + c32 + 4;
              *(unsigned long *) (data + offset) = htonl(i32);
              offset += 4;
              *(unsigned long *) (data + offset) = htonl(c32);
              offset += 4;

              for (v = 0; v < count; v += 2) {
                  PyObject *vtype = PyList_GET_ITEM(pairs, v);
                  int type = PyInt_AS_LONG(vtype);

                  data[offset++] = (unsigned char) (type < 0 ? -type : type);

                  if (PyList_GET_ITEM(pairs, v + 1) == Nil)
                  {
                      PyErr_SetObject(PyExc_ValueError, (PyObject *) record);
                      return -1;
                  }
              }
              if (_t_record_write(record, data + offset, record->size) < 0)
                  return -1;
              offset += record->size;
          }
          break;

          default:
            PyErr_SetObject(PyExc_ValueError, valueType);
            return -1;
        }
    }

    return 0;

  overflow:
    PyErr_SetObject(PyExc_OverflowError, (PyObject *) self);
    return -1;
}

static int _t_record_read_string(t_record *self, int *offset, PyObject **v,
                                 int size, unsigned char *data, int len)
{
    PyObject *str = self->partial;
    int psize;

    if (*offset + size > len)
        psize = len - *offset;
    else
        psize = size;

    if (!str)
    {
        str = PyString_FromStringAndSize(NULL, size);
        if (!str)
            return -1;

        memcpy(PyString_AS_STRING(str), data + *offset, psize);
        self->partialSize = size - psize;
    }
    else
    {
        memcpy(PyString_AS_STRING(str) + PyString_GET_SIZE(str) - size,
               data + *offset, psize);
        self->partialSize = size - psize;
    }

    *offset += psize;

    if (self->partialSize == 0)
    {
        self->partial = NULL;
        *v = str;
    }
    else
    {
        self->partial = str;
        *v = NULL;
    }

    return 0;
}

static PyObject *_t_record_unpack(unsigned char *data, int len)
{
    int count = ntohl(*(unsigned long *) data);
    PyObject *vtypes = PyTuple_New(count);
    t_record *record;
    int i, offset = 4;

    if (!vtypes)
        return NULL;

    for (i = 0; i < count; i++) {
        int vtype = data[offset++];
        PyTuple_SET_ITEM(vtypes, i, PyInt_FromLong(vtype));
    }

    record = _t_record_new_read(vtypes);
    Py_DECREF(vtypes);
    if (!record)
        return NULL;

    if (_t_record_read(record, data + offset, len - offset) < 0)
    {
        Py_DECREF(record);
        return NULL;
    }

    return (PyObject *) record;
}

int _t_record_read(t_record *self, unsigned char *data, int len)
{
    PyObject *pairs = self->pairs;
    int count = PyList_GET_SIZE(pairs);
    int i, offset = 0;
    long long i64;
    long i32;
    short i16;
    double d64;

    for (i = 0; i < count && offset < len; i += 2) {
        if (PyList_GET_ITEM(pairs, i + 1) == Nil)
        {
            PyObject *valueType = PyList_GET_ITEM(pairs, i);
            PyObject *value = NULL, *v = NULL;
            int size = 0;

            if (self->partial)
                size = self->partialSize;
            else
            {
                switch (PyInt_AS_LONG(valueType)) {
                  case R_NONE:
                    if (data[offset++] != R_NONE)
                    {
                        PyErr_SetString(PyExc_ValueError, "expected R_NONE");
                        return -1;
                    }
                  r_none:
                    v = Py_None; Py_INCREF(v);
                    self->valueType = R_NONE;
                    self->size += 1;
                    break;

                  case R_TRUE:
                    if (data[offset++] != R_TRUE)
                    {
                        PyErr_SetString(PyExc_ValueError, "expected R_TRUE");
                        return -1;
                    }
                  r_true:
                    v = Py_True; Py_INCREF(v);
                    self->valueType = R_TRUE;
                    self->size += 1;
                    break;

                  case R_FALSE:
                    if (data[offset++] != R_FALSE)
                    {
                        PyErr_SetString(PyExc_ValueError, "expected R_FALSE");
                        return -1;
                    }
                  r_false:
                    v = Py_False; Py_INCREF(v);
                    self->valueType = R_FALSE;
                    self->size += 1;
                    break;

                  case R_KEYWORD:
                  r_keyword:
                    size = (char) data[offset++];
                    if (size == 0)
                        goto r_none;
                    else if (size < 0)
                    {
                        self->valueType = -R_KEYWORD;
                        size = -size;
                    }
                    else
                        self->valueType = R_KEYWORD;
                    self->size += size + 1;
                    break;

                  case R_SYMBOL:
                  r_symbol:
                    size = (unsigned char) data[offset++];
                    if (size == 0)
                        goto r_none;
                    else
                    {
                        self->valueType = R_SYMBOL;
                        self->size += size + 1;
                    }
                    break;

                  case R_UUID:
                  r_uuid:
                    size = 16;
                    self->valueType = R_UUID;
                    self->size += 16;
                    break;

                  case R_UUID_OR_NONE:
                    switch (data[offset++]) {
                      case R_NONE:
                        goto r_none;
                      case R_UUID:
                        self->size += 1;
                        goto r_uuid;
                      default:
                        PyErr_SetString(PyExc_ValueError,
                                        "expected R_UUID_OR_NONE");
                        return -1;
                    }
                    break;

                  case R_UUID_OR_SYMBOL:
                    switch (data[offset++]) {
                      case R_NONE:
                        goto r_none;
                      case R_UUID:
                        self->size += 1;
                        goto r_uuid;
                      case R_SYMBOL:
                        self->size += 1;
                        goto r_symbol;
                      default:
                        PyErr_SetString(PyExc_ValueError,
                                        "expected R_UUID_OR_SYMBOL");
                        return -1;
                    }
                    break;

                  case R_UUID_OR_KEYWORD:
                    switch (data[offset++]) {
                      case R_NONE:
                        goto r_none;
                      case R_UUID:
                        self->size += 1;
                        goto r_uuid;
                      case R_KEYWORD:
                        self->size += 1;
                        goto r_keyword;
                      default:
                        PyErr_SetString(PyExc_ValueError,
                                        "expected R_UUID_OR_KEYWORD");
                        return -1;
                    }
                    break;

                  case R_STRING:
                  r_string:
                    if (offset + 4 <= len)
                    {
                        size = *(unsigned long *) (data + offset);
                        size = ntohl(size);
                        offset += 4;

                      r_string_read:
                        if (size < 0)
                        {
                            size = -size - 1;
                            if (size == 0)
                                v = PyString_FromStringAndSize(NULL, 0);
                            self->valueType = -R_STRING;
                        }
                        else
                        {
                            size -= 1;
                            if (size == 0)
                            {
                                v = PyUnicode_FromUnicode(NULL, 0);
                                self->valueType = -R_STRING;
                            }
                            else
                                self->valueType = R_STRING;
                        }
                        self->size += size + 4;
                    }
                    else
                    {
                        size = 4;
                        self->valueType = R_STRING << 16;
                    }
                    break;

                  case R_STRING_OR_NONE:
                    switch (data[offset++]) {
                      case R_NONE:
                        goto r_none;
                      case R_STRING:
                        self->size += 1;
                        goto r_string;
                      default:
                        PyErr_SetString(PyExc_ValueError,
                                        "expected R_STRING_OR_NONE");
                        return -1;
                    }
                    break;

                  case R_HASH:
                  case R_INT:
                    if (offset + 4 <= len)
                    {
                        i32 = *(unsigned long *) (data + offset);
                        i32 = ntohl(i32);
                        offset += 4;
                        v = PyInt_FromLong(i32);
                        self->valueType = R_INT;
                    }
                    else
                    {
                        size = 4;
                        self->valueType = R_INT << 16;
                    }
                    self->size += 4;
                    break;

                  case R_SHORT:
                    if (offset + 2 <= len)
                    {
                        i16 = *(short *) (data + offset);
                        i16 = ntohs(i16);
                        offset += 2;
                        v = PyInt_FromLong(i16);
                        self->valueType = R_SHORT;
                    }
                    else
                    {
                        size = 2;
                        self->valueType = R_SHORT << 16;
                    }
                    self->size += 2;
                    break;

                  case R_BYTE:
                    v = PyInt_FromLong(data[offset++]);
                    self->valueType = R_BYTE;
                    self->size += 1;
                    break;

                  case R_BOOLEAN:
                    switch (data[offset++]) {
                      case R_NONE:
                        goto r_none;
                      case R_TRUE:
                        goto r_true;
                      case R_FALSE:
                        goto r_false;
                      default:
                        PyErr_SetString(PyExc_ValueError, "expected R_BOOLEAN");
                        return -1;
                    }
                    break;

                  case R_LONG:
                    if (offset + 8 <= len)
                    {
                        i32 = *(unsigned long *) (data + offset);
                        offset += 4;
                        i64 = ((unsigned long long) ntohl(i32)) << 32;
                        i32 = *(unsigned long *) (data + offset);
                        offset += 4;
                        i64 |= ntohl(i32);
                        v = PyLong_FromLongLong(i64);
                        self->valueType = R_LONG;
                    }
                    else
                    {
                        size = 8;
                        self->valueType = R_LONG << 16;
                    }
                    self->size += 8;
                    break;

                  case R_DOUBLE:
                    if (offset + 8 <= len)
                    {
                        d64 = _PyFloat_Unpack8(data + offset, 0);
                        offset += 8;
                        v = PyFloat_FromDouble(d64);
                        self->valueType = R_DOUBLE;
                    }
                    else
                    {
                        size = 8;
                        self->valueType = R_DOUBLE << 16;
                    }
                    self->size += 8;
                    break;

                  case R_RECORD:
                    if (offset + 4 <= len)
                    {
                        size = *(unsigned long *) (data + offset);
                        size = ntohl(size);
                        offset += 4;

                      r_record:
                        self->size += size + 4;
                        if (offset + size <= len)
                        {
                            v = _t_record_unpack(data + offset, size);
                            offset += size;
                            if (!v)
                                return -1;
                            size = 0;
                            self->valueType = R_RECORD;
                        }
                        else
                            self->valueType = R_RECORD << 24;
                    }
                    else
                    {
                        size = 4;
                        self->valueType = R_RECORD << 16;
                    }
                    break;
                }
            }

            if (size && _t_record_read_string(self, &offset, &v,
                                              size, data, len) < 0)
                return -1;
            if (!v)
                return 0;

            switch (self->valueType) {
              case R_NONE:
              case R_TRUE:
              case R_FALSE:
                value = v;
                break;

              case R_KEYWORD:
              case R_STRING:
                value = PyUnicode_DecodeUTF8(PyString_AS_STRING(v),
                                             PyString_GET_SIZE(v),
                                             "strict");
                Py_DECREF(v);
                if (!value)
                    return -1;
                break;

              case -R_KEYWORD:
              case R_SYMBOL:
              case -R_STRING:
                value = v;
                break;

              case R_HASH:
              case R_INT:
              case R_SHORT:
              case R_BYTE:
              case R_LONG:
              case R_DOUBLE:
                value = v;
                break;

              case R_UUID:
                value = PyUUID_Make16(v); /* steals ref */
                break;

              case R_STRING << 16:
                size = *(long *) PyString_AS_STRING(v);
                size = ntohl(size);
                Py_CLEAR(v);
                goto r_string_read;

              case R_HASH << 16:
              case R_INT << 16:
                i32 = *(long *) PyString_AS_STRING(v);
                i32 = ntohl(i32);
                Py_DECREF(v);
                value = PyInt_FromLong(i32);
                break;

              case R_SHORT << 16:
                i16 = *(short *) PyString_AS_STRING(v);
                i16 = ntohs(i16);
                Py_DECREF(v);
                value = PyInt_FromLong(i16);
                break;

              case R_LONG << 16:
                i32 = *(unsigned long *) PyString_AS_STRING(v);
                i64 = ((unsigned long long) ntohl(i32)) << 32;
                i32 = *(unsigned long *) (PyString_AS_STRING(v) + 4);
                i64 |= i32;
                Py_DECREF(v);
                value = PyLong_FromLongLong(i64);
                break;

              case R_DOUBLE << 16:
                d64 = _PyFloat_Unpack8((unsigned char *) PyString_AS_STRING(v),
                                       0);
                Py_DECREF(v);
                value = PyFloat_FromDouble(d64);
                break;

              case R_RECORD:
                value = v;
                break;

              case R_RECORD << 16:
                size = *(unsigned long *) (PyString_AS_STRING(v));
                size = ntohl(size);
                Py_CLEAR(v);
                goto r_record;

              case R_RECORD << 24:
                value = _t_record_unpack((unsigned char *)PyString_AS_STRING(v),
                                         PyString_GET_SIZE(v));
                Py_DECREF(v);
                if (!value)
                    return -1;
                break;
            }

            PyList_SetItem(pairs, i + 1, value);
        }
    }

    return 0;
}

static PyObject *t_record_read(t_record *self, PyObject *arg)
{
    if (!PyString_CheckExact(arg))
    {
        PyErr_SetObject(PyExc_TypeError, arg);
        return NULL;
    }

    if (_t_record_read(self, (unsigned char *) PyString_AS_STRING(arg),
                       PyString_GET_SIZE(arg)) < 0)
        return NULL;

    Py_RETURN_NONE;
}

void _init_record(PyObject *m)
{
    if (PyType_Ready(&RecordType) >= 0)
    {
        if (m)
        {
            PyObject *dict = RecordType.tp_dict;

            Py_INCREF(&RecordType);
            PyModule_AddObject(m, "Record", (PyObject *) &RecordType);
            Record = &RecordType;

            PyDict_SetItemString_Int(dict, "NONE", R_NONE);
            PyDict_SetItemString_Int(dict, "TRUE", R_TRUE);
            PyDict_SetItemString_Int(dict, "FALSE", R_FALSE);
            PyDict_SetItemString_Int(dict, "KEYWORD", R_KEYWORD);
            PyDict_SetItemString_Int(dict, "SYMBOL", R_SYMBOL);
            PyDict_SetItemString_Int(dict, "UUID", R_UUID);
            PyDict_SetItemString_Int(dict, "UUID_OR_NONE", R_UUID_OR_NONE);
            PyDict_SetItemString_Int(dict, "UUID_OR_KEYWORD", R_UUID_OR_KEYWORD);
            PyDict_SetItemString_Int(dict, "UUID_OR_SYMBOL", R_UUID_OR_SYMBOL);
            PyDict_SetItemString_Int(dict, "STRING", R_STRING);
            PyDict_SetItemString_Int(dict, "STRING_OR_NONE", R_STRING_OR_NONE);
            PyDict_SetItemString_Int(dict, "HASH", R_HASH);
            PyDict_SetItemString_Int(dict, "INT", R_INT);
            PyDict_SetItemString_Int(dict, "BYTE", R_BYTE);
            PyDict_SetItemString_Int(dict, "SHORT", R_SHORT);
            PyDict_SetItemString_Int(dict, "BOOLEAN", R_BOOLEAN);
            PyDict_SetItemString_Int(dict, "LONG", R_LONG);
            PyDict_SetItemString_Int(dict, "DOUBLE", R_DOUBLE);
            PyDict_SetItemString_Int(dict, "RECORD", R_RECORD);
        }
    }
}
