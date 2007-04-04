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


#include "fns.h"
#include "uuid.h"
#include "linkedmap.h"
#include "skiplist.h"
#include "ctxmgr.h"
#include "iterator.h"
#include "persistentvalue.h"

extern PyTypeObject *UUID;
extern PyTypeObject *Key;
extern PyTypeObject *Cipher;
extern PyTypeObject *PersistentValue;
extern PyTypeObject *CLinkedMap;
extern PyTypeObject *CLink;
extern PyTypeObject *CPoint;
extern PyTypeObject *CNode;
extern PyTypeObject *SkipList;

extern PyObject *inList, *outList;

extern PyObject *Nil, *Default, *Empty;
extern PyObject *Empty_TUPLE;

void PyDict_SetItemString_Int(PyObject *, char *, int);

void _init_uuid(PyObject *m);
void _init_rijndael(PyObject *m);
void _init_linkedmap(PyObject *m);
void _init_skiplist(PyObject *m);
void _init_hashtuple(PyObject *m);
void _init_nil(PyObject *m);
void _init_ctxmgr(PyObject *m);
void _init_iterator(PyObject *m);
void _init_persistentvalue(PyObject *m);

#ifdef WINDOWS
PyObject *openHFILE(PyObject *self, PyObject *args);
PyObject *closeHFILE(PyObject *self, PyObject *args);
PyObject *lockHFILE(PyObject *self, PyObject *args);
void _init_lock(PyObject *m);
#endif

int _t_persistentvalue_init(t_persistentvalue *self, PyObject *view);
