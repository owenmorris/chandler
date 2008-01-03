/*
 *  Copyright (c) 2003-2008 Open Source Applications Foundation
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

#ifndef _LINKEDMAP_H
#define _LINKEDMAP_H

#include "../util/persistentvalue.h"

typedef struct {
    PyObject_HEAD
    PyObject *owner;
    PyObject *previousKey;
    PyObject *nextKey;
    PyObject *value;
    PyObject *alias;
    PyObject *otherKey;
} t_link;


typedef struct {
    t_persistentvalue persistentvalue;
    int flags;
    int count;
    PyObject *dict;
    PyObject *aliases;
    PyObject *head;
} t_lm;


enum {
    LM_NEW      = 0x0001,
    LM_LOAD     = 0x0002,
    LM_MERGING  = 0x0004,
    LM_SETDIRTY = 0x0008,
    LM_READONLY = 0x0010,
    LM_DEFERRED = 0x0020,
};

#endif /* _LINKEDMAP_H */
