
/*
 * The C schema types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include "../item/item.h"
#include "descriptor.h"
#include "attribute.h"

#define LOAD_TYPE(m, name) \
    name = (PyTypeObject *) PyObject_GetAttrString(m, #name);

#define LOAD_FN(m, name) \
    { PyObject *cobj = PyObject_GetAttrString(m, #name); \
      name = (name##_fn) PyCObject_AsVoidPtr(cobj); \
      Py_DECREF(cobj); }


extern long _lastAccess;
extern PyTypeObject *CDescriptor;
extern PyTypeObject *CAttribute;
extern PyTypeObject *CItem;
extern PyObject *PyExc_StaleItemError;


void _init_descriptor(PyObject *m);
void _init_attribute(PyObject *m);
void _init_kind(PyObject *m);

void PyDict_SetItemString_Int(PyObject *dict, char *key, int value);
