
/*
 * The C item types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include <Python.h>
#include "structmember.h"

#include "c.h"

PyTypeObject *CItem = NULL;
PyTypeObject *CDescriptor = NULL;
PyObject *Nil = NULL;
PyObject *Default = NULL;


static PyObject *isitem(PyObject *self, PyObject *obj)
{
    if (PyObject_TypeCheck(obj, CItem))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}


static PyMethodDef c_funcs[] = {
    { "isitem", (PyCFunction) isitem, METH_O,
      "isinstance(), but not as easily fooled" },
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
    PyObject *m = Py_InitModule3("c", c_funcs, "C item types module");

    _init_item(m);

    m = PyImport_ImportModule("chandlerdb.schema.c");
    LOAD_TYPE(m, CDescriptor);
    Py_DECREF(m);
}    
