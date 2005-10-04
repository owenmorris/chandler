
/*
 * The C repository types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include "../item/item.h"
#include "../util/uuid.h"
#include "view.h"

#define LOAD_TYPE(m, name) \
    name = (PyTypeObject *) PyObject_GetAttrString(m, #name);

#define LOAD_FN(m, name) \
    { PyObject *cobj = PyObject_GetAttrString(m, #name); \
      name = (name##_fn) PyCObject_AsVoidPtr(cobj); \
      Py_DECREF(cobj); }

#define LOAD_EXC(m, name) \
    PyExc_##name = PyObject_GetAttrString(m, #name)


typedef struct {
    PyObject_HEAD
    unsigned long status;
    PyObject *store;
} t_repository;


extern PyTypeObject *CView;
extern PyTypeObject *CRepository;
extern PyTypeObject *CItem;

extern PyUUID_Check_fn PyUUID_Check;
extern PyUUID_Make16_fn PyUUID_Make16;

void PyDict_SetItemString_Int(PyObject *dict, char *key, int value);

void _init_view(PyObject *m);
void _init_repository(PyObject *m);
void _init_container(PyObject *m);
