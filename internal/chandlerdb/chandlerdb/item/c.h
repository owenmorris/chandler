
/*
 * The C item types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include "item.h"

#define LOAD_TYPE(m, name) \
    name = (PyTypeObject *) PyObject_GetAttrString(m, #name);

#define LOAD_FN(m, name) \
    { PyObject *cobj = PyObject_GetAttrString(m, #name); \
      name = (name##_fn) PyCObject_AsVoidPtr(cobj); \
      Py_DECREF(cobj); }


extern PyTypeObject *CItem;
extern PyTypeObject *CDescriptor;

extern PyObject *Nil;
extern PyObject *Default;


void _init_item(PyObject *m);

void PyDict_SetItemString_Int(PyObject *dict, char *key, int value);
