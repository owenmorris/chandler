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

#include "c.h"

PyTypeObject *UUID = NULL;
PyTypeObject *Key = NULL;
PyTypeObject *Cipher = NULL;
PyTypeObject *PersistentValue = NULL;
PyTypeObject *CLinkedMap = NULL;
PyTypeObject *CLink = NULL;
PyTypeObject *CPoint = NULL;
PyTypeObject *CNode = NULL;
PyTypeObject *SkipList = NULL;

PyObject *Nil = NULL, *Default = NULL, *Empty = NULL;
PyObject *Empty_TUPLE = NULL;

static PyObject *isuuid(PyObject *self, PyObject *obj)
{
    if (PyObject_TypeCheck(obj, UUID))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *hash(PyObject *self, PyObject *args)
{
    unsigned char *data;
    unsigned int len = 0;

    if (!PyArg_ParseTuple(args, "s#", &data, &len))
        return 0;

    return PyInt_FromLong(hash_bytes(data, len));
}

static PyObject *combine(PyObject *self, PyObject *args)
{
    unsigned long h0, h1;

    if (!PyArg_ParseTuple(args, "ll", &h0, &h1))
        return 0;

    return PyInt_FromLong(combine_longs(h0, h1));
}

static PyObject *loadUUIDs(PyObject *self, PyObject *arg)
{
    if (arg == Py_None)
        arg = NULL;
    else if (!PyList_Check(arg))
    {
        PyErr_SetObject(PyExc_TypeError, arg);
        return NULL;
    }

    Py_XDECREF(inList);

    if (arg)
    {
        inList = PyList_GetSlice(arg, 0, PyList_Size(arg));
        PyList_Reverse(inList);
    }
    else
        inList = NULL;

    Py_RETURN_NONE;
}

static PyObject *saveUUIDs(PyObject *self, PyObject *arg)
{
    if (arg == Py_None)
        arg = NULL;
    else if (!PyList_Check(arg))
    {
        PyErr_SetObject(PyExc_TypeError, arg);
        return NULL;
    }
    else
        Py_INCREF(arg);

    Py_XDECREF(outList);
    outList = arg;

    Py_RETURN_NONE;
}

static PyObject *packDigits(PyObject *self, PyObject *arg)
{
    if (!PyTuple_Check(arg))
    {
        PyErr_SetObject(PyExc_TypeError, arg);
        return NULL;
    }
    else
    {
        int len = PyTuple_GET_SIZE(arg);
        int blen = len & 1 ? (len >> 1) + 1 : len >> 1;
        PyObject *digits = PyString_FromStringAndSize(NULL, blen);
        unsigned char *bytes;
        int i;

        if (!digits)
            return NULL;

        bytes = (unsigned char *) PyString_AS_STRING(digits);
        memset(bytes, 0, blen);
        if (len & 1)
            bytes[blen - 1] |= 0x0f;

        for (i = 0; i < len; i++) {
            PyObject *digit = PyTuple_GET_ITEM(arg, i);
            int n = PyInt_AS_LONG(digit) & 0x0f;

            if (i & 1)
                bytes[i >> 1] |= n;
            else
                bytes[i >> 1] |= (n << 4);
        }

        return digits;
    }
}

static PyObject *unpackDigits(PyObject *self, PyObject *arg)
{
    if (!PyString_CheckExact(arg))
    {
        PyErr_SetObject(PyExc_TypeError, arg);
        return NULL;
    }
    else
    {
        unsigned char *bytes = (unsigned char *) PyString_AS_STRING(arg);
        int blen = PyString_GET_SIZE(arg);
        int len = blen * 2;
        PyObject *digits;
        int i;

        if ((bytes[blen - 1] & 0x0f) == 0x0f)
            len -= 1;

        digits = PyTuple_New(len);
        if (!digits)
            return NULL;

        for (i = 0; i < len; i++) {
            int n;

            if (i & 1)
                n = bytes[i >> 1] & 0x0f;
            else
                n = bytes[i >> 1] >> 4;

            PyTuple_SET_ITEM(digits, i, PyInt_FromLong(n));
        }

        return digits;
    }
}

#ifdef __MACH__
static PyObject *_vfork(PyObject *self)
{
    return PyInt_FromLong(vfork());
}
#endif

/* 
 * Return a platform name that can be used for Berkeley DB
 * compatibility testing.
 */
static PyObject *getPlatformName(PyObject *self)
{
#if defined(__MACH__) && defined(__i386__)
    return PyString_FromString("darwin-i386");
#elif defined(__MACH__) && defined(__ppc__)
    return PyString_FromString("darwin-ppc");
#elif defined(linux) && defined(__i386__)
    return PyString_FromString("linux-i386");
#elif defined(WINDOWS) && defined(_M_IX86)
    return PyString_FromString("win32-i386");
#else
#error "unknown or unsupported platform"
#endif
}

static PyMethodDef c_funcs[] = {
    { "isuuid", (PyCFunction) isuuid, METH_O, "isinstance(UUID)" },
    { "_hash", (PyCFunction) hash, METH_VARARGS, "hash bytes" },
    { "_combine", (PyCFunction) combine, METH_VARARGS, "combine two hashes" },
    { "loadUUIDs", (PyCFunction) loadUUIDs, METH_O,
      "use a list of pre-generated UUIDs, for debugging" },
    { "saveUUIDs", (PyCFunction) saveUUIDs, METH_O,
      "use a list to save UUIDs as they are generated, for debugging" },
    { "packDigits", (PyCFunction) packDigits, METH_O,
      "pack decimal digits from a tuple into a string, 4 bits each" },
    { "unpackDigits", (PyCFunction) unpackDigits, METH_O,
      "unpack decimal digits from a string into a tuple, 4 bits each" },
    { "getPlatformName", (PyCFunction) getPlatformName, METH_NOARGS,
      "return a suitable platform name for Berkeley DB compatibility check" },
#ifdef __MACH__
    { "vfork", (PyCFunction) _vfork, METH_NOARGS, "" },
#endif
#ifdef WINDOWS
    { "openHFILE", (PyCFunction) openHFILE, METH_VARARGS, "open HFILE" },
    { "closeHFILE", (PyCFunction) closeHFILE, METH_VARARGS, "close HFILE" },
    { "lockHFILE", (PyCFunction) lockHFILE, METH_VARARGS,
      "lock, unlock, upgrade or downgrade lock on an HFILE" },
#endif
    { NULL, NULL, 0, NULL }
};


void PyDict_SetItemString_Int(PyObject *dict, char *key, int value)
{
    PyObject *pyValue = PyInt_FromLong(value);

    PyDict_SetItemString(dict, key, pyValue);
    Py_DECREF(pyValue);
}


void initc(void)
{
    PyObject *m = Py_InitModule3("c", c_funcs, "C util types module");

    Empty_TUPLE = PyTuple_New(0);

    _init_uuid(m);
    _init_rijndael(m);
    _init_persistentvalue(m);
    _init_linkedmap(m);
    _init_skiplist(m);
    _init_hashtuple(m);
    _init_nil(m);
    _init_ctxmgr(m);
    _init_iterator(m);
#ifdef WINDOWS
    _init_lock(m);
#endif
}    
