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


typedef struct {
    PyObject_HEAD
    PyObject *owner;
    PyObject *previousKey;
    PyObject *nextKey;
    PyObject *value;
    PyObject *alias;
} t_link;


typedef struct {
    PyObject_HEAD
    int flags;
    int count;
    PyObject *dict;
    PyObject *aliases;
    PyObject *head;
} t_lm;


enum {
    LM_NEW     = 0x0001,
    LM_LOAD    = 0x0002,
    LM_MERGING = 0x0004
};
