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

#ifndef _SKIPLIST_H
#define _SKIPLIST_H

/* from 1 to 16 */
#define SL_MAXLEVEL 16       

enum {
    SL_INSERT = 0x0001,
    SL_MOVE   = 0x0002,
    SL_REMOVE = 0x0004
};


typedef struct {
    PyObject_HEAD
    PyObject *prevKey;
    PyObject *nextKey;
    int dist;
} t_point;

typedef struct {
    PyObject_HEAD
    PyObject *levels;
} t_node;

typedef struct {
    PyObject_HEAD
    PyObject *head;
    PyObject *tail;
    PyObject *map;
    int flags;
} t_sl;

#endif /* _SKIPLIST_H */
