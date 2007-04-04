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

long _lastAccess = 0L;
PyTypeObject *CDescriptor = NULL;
PyTypeObject *CAttribute = NULL;
PyTypeObject *CItem = NULL;
PyTypeObject *ItemRef = NULL;
PyTypeObject *CValues = NULL;
PyTypeObject *CLinkedMap = NULL;
PyTypeObject *PersistentSequence = NULL;
PyObject *PyExc_StaleItemError = NULL;
PyObject *True_TUPLE = NULL;
PyObject *Empty_TUPLE = NULL;
PyObject *Empty = NULL;

static PyObject *countAccess(PyObject *self, t_item *item)
{
    item->lastAccess = ++_lastAccess;
    Py_RETURN_NONE;
}

static void _countAccess(t_item *item)
{
    item->lastAccess = ++_lastAccess;
}


static PyMethodDef c_funcs[] = {
    { "_countAccess", (PyCFunction) countAccess, METH_O,
      "last access stamper" },
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
    PyObject *m = Py_InitModule3("c", c_funcs, "C schema types module");
    PyObject *cobj;

    _init_descriptor(m);
    _init_attribute(m);
    _init_kind(m);
    _init_redirector(m);

    True_TUPLE = PyTuple_Pack(1, Py_True);
    Empty_TUPLE = PyTuple_New(0);

    cobj = PyCObject_FromVoidPtr(_countAccess, NULL);
    PyModule_AddObject(m, "C_countAccess", cobj);

    if (!(m = PyImport_ImportModule("chandlerdb.item.ItemError")))
        return;
    PyExc_StaleItemError = PyObject_GetAttrString(m, "StaleItemError");
    Py_DECREF(m);
    
    if (!(m = PyImport_ImportModule("chandlerdb.item.c")))
        return;
    LOAD_TYPE(m, CItem);
    LOAD_TYPE(m, ItemRef);
    LOAD_TYPE(m, CValues);
    LOAD_TYPE(m, PersistentSequence);
    Py_DECREF(m);

    if (!(m = PyImport_ImportModule("chandlerdb.util.c")))
        return;
    LOAD_TYPE(m, CLinkedMap);
    LOAD_OBJ(m, Empty);
    Py_DECREF(m);
}
