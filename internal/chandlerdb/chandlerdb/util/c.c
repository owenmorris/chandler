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

PyTypeObject *UUID = NULL;
PyTypeObject *SingleRef = NULL;
PyTypeObject *Key = NULL;
PyTypeObject *Cipher = NULL;
PyTypeObject *CLinkedMap = NULL;
PyTypeObject *CLink = NULL;
PyTypeObject *CPoint = NULL;
PyTypeObject *CNode = NULL;
PyTypeObject *SkipList = NULL;


static PyObject *isuuid(PyObject *self, PyObject *obj)
{
    if (PyObject_TypeCheck(obj, UUID))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *issingleref(PyObject *self, PyObject *obj)
{
    if (PyObject_TypeCheck(obj, SingleRef))
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


static PyMethodDef c_funcs[] = {
    { "isuuid", (PyCFunction) isuuid, METH_O, "isinstance(UUID)" },
    { "issingleref", (PyCFunction) issingleref, METH_O, "isinstance(SingleRef)" },
    { "_hash", (PyCFunction) hash, METH_VARARGS, "hash bytes" },
    { "_combine", (PyCFunction) combine, METH_VARARGS, "combine two hashes" },
    { "loadUUIDs", (PyCFunction) loadUUIDs, METH_O,
      "use a list of pre-generated UUIDs, for debugging" },
    { "saveUUIDs", (PyCFunction) saveUUIDs, METH_O,
      "use a list to save UUIDs as they are generated, for debugging" },
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

    _init_uuid(m);
    _init_singleref(m);
    _init_rijndael(m);
    _init_linkedmap(m);
    _init_skiplist(m);
    _init_hashtuple(m);
#ifdef WINDOWS
    _init_lock(m);
#endif
}    
