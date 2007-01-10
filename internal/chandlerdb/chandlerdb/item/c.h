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


#include "item.h"
#include "indexes.h"
#include "../util/uuid.h"
#include "../persistence/view.h"
#include "../schema/kind.h"
#include "../schema/attribute.h"
#include "../schema/descriptor.h"


#define LOAD_TYPE(m, name) \
    name = (PyTypeObject *) PyObject_GetAttrString(m, #name);

#define LOAD_OBJ(m, name) \
    name = PyObject_GetAttrString(m, #name);

#define LOAD_FN(m, name) \
    { PyObject *cobj = PyObject_GetAttrString(m, #name); \
      name = (name##_fn) PyCObject_AsVoidPtr(cobj);      \
      Py_DECREF(cobj); }

#define LOAD_CFUNC(m, name) \
    { PyObject *fn = PyObject_GetAttrString(m, #name);   \
      name = (PyCFunction) PyCFunction_GetFunction(fn);  \
      Py_DECREF(fn); }


extern PyTypeObject *ItemRef;
extern PyTypeObject *CLinkedMap;
extern PyTypeObject *CItem;
extern PyTypeObject *CValues;
extern PyTypeObject *CKind;
extern PyTypeObject *CAttribute;
extern PyTypeObject *CDescriptor;
extern PyTypeObject *ItemValue;
extern PyTypeObject *StaleItemAttributeError;
extern PyTypeObject *CView;

extern PyObject *Nil;
extern PyObject *Default;

extern CView_invokeMonitors_fn CView_invokeMonitors;
extern PyUUID_Check_fn PyUUID_Check;
extern C_countAccess_fn C_countAccess;
extern long itemCount;

extern CAttribute_invokeAfterChange_fn CAttribute_invokeAfterChange;

void _init_item(PyObject *m);
void _init_itemref(PyObject *m);
void _init_values(PyObject *m);
void _init_indexes(PyObject *m);

PyObject *t_values__setDirty(t_values *self, PyObject *key);
void PyDict_SetItemString_Int(PyObject *dict, char *key, int value);
t_itemref *_t_itemref_new(PyObject *uuid, t_view *view, t_item *item);
PyObject *t_itemref_call(t_itemref *self, PyObject *args, PyObject *kwds);
t_item *_t_itemref_call(t_itemref *self); /* borrows reference */
