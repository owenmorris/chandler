
/*
 * The C item types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include "item.h"
#include "../util/uuid.h"
#include "../persistence/view.h"

#define LOAD_TYPE(m, name) \
    name = (PyTypeObject *) PyObject_GetAttrString(m, #name);

#define LOAD_FN(m, name) \
    { PyObject *cobj = PyObject_GetAttrString(m, #name); \
      name = (name##_fn) PyCObject_AsVoidPtr(cobj);      \
      Py_DECREF(cobj); }

#define LOAD_CFUNC(m, name) \
    { PyObject *fn = PyObject_GetAttrString(m, #name);   \
      name = (PyCFunction) PyCFunction_GetFunction(fn);  \
      Py_DECREF(fn); }


extern PyTypeObject *SingleRef;
extern PyTypeObject *CLinkedMap;
extern PyTypeObject *CItem;
extern PyTypeObject *CValues;
extern PyTypeObject *CKind;
extern PyTypeObject *CAttribute;
extern PyTypeObject *CDescriptor;
extern PyTypeObject *ItemValue;

extern PyObject *Nil;
extern PyObject *Default;

extern CView_invokeMonitors_fn CView_invokeMonitors;
extern PyUUID_Check_fn PyUUID_Check;
extern PyCFunction _countAccess;


void _init_item(PyObject *m);
void _init_values(PyObject *m);

PyObject *t_values__setDirty(t_values *self, PyObject *key);
void PyDict_SetItemString_Int(PyObject *dict, char *key, int value);
