
/*
 * The C schema types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include <Python.h>
#include "structmember.h"

#include "c.h"

long _lastAccess = 0L;
PyTypeObject *CDescriptor = NULL;
PyTypeObject *CAttribute = NULL;
PyTypeObject *CItem = NULL;
PyTypeObject *CValues = NULL;
PyObject *PyExc_StaleItemError;


static PyObject *countAccess(PyObject *self, t_item *item)
{
    item->lastAccess = ++_lastAccess;
    Py_RETURN_NONE;
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

    _init_descriptor(m);
    _init_attribute(m);
    _init_kind(m);

    m = PyImport_ImportModule("chandlerdb.item.ItemError");
    PyExc_StaleItemError = PyObject_GetAttrString(m, "StaleItemError");
    Py_DECREF(m);
    
    m = PyImport_ImportModule("chandlerdb.item.c");
    LOAD_TYPE(m, CItem);
    LOAD_TYPE(m, CValues);
    Py_DECREF(m);
}
