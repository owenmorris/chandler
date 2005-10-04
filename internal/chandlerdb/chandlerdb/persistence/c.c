
/*
 * The C repository types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include <Python.h>
#include "structmember.h"

#include "c.h"

PyTypeObject *CView = NULL;
PyTypeObject *CRepository = NULL;
PyTypeObject *CItem = NULL;

PyUUID_Check_fn PyUUID_Check = NULL;
PyUUID_Make16_fn PyUUID_Make16 = NULL;


static PyMethodDef c_funcs[] = {
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
    PyObject *m = Py_InitModule3("c", c_funcs, "C repository types module");

    _init_view(m);
    _init_repository(m);
    _init_container(m);

    m = PyImport_ImportModule("chandlerdb.util.c");
    LOAD_FN(m, PyUUID_Check);
    LOAD_FN(m, PyUUID_Make16);
    Py_DECREF(m);

    m = PyImport_ImportModule("chandlerdb.item.c");
    LOAD_TYPE(m, CItem);
    Py_DECREF(m);
}
