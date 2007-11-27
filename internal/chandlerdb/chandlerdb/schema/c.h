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


#include "../item/item.h"
#include "../item/sequence.h"
#include "kind.h"
#include "attribute.h"
#include "descriptor.h"

#define LOAD_TYPE(m, name) \
    name = (PyTypeObject *) PyObject_GetAttrString(m, #name);

#define LOAD_OBJ(m, name) \
    name = PyObject_GetAttrString(m, #name);

#define LOAD_FN(m, name) \
    { PyObject *cobj = PyObject_GetAttrString(m, #name); \
      name = (name##_fn) PyCObject_AsVoidPtr(cobj); \
      Py_DECREF(cobj); }


extern long _lastAccess;
extern PyTypeObject *CDescriptor;
extern PyTypeObject *CAttribute;
extern PyTypeObject *CItem;
extern PyTypeObject *ItemRef;
extern PyTypeObject *CValues;
extern PyTypeObject *CLinkedMap;
extern PyTypeObject *PersistentSequence;
extern PyTypeObject *StaleItemError;
extern PyTypeObject *NoValueForAttributeError;
extern PyObject *True_TUPLE, *Empty_TUPLE;
extern PyObject *Empty;

void _init_descriptor(PyObject *m);
void _init_attribute(PyObject *m);
void _init_kind(PyObject *m);
void _init_redirector(PyObject *m);

void PyDict_SetItemString_Int(PyObject *dict, char *key, int value);
