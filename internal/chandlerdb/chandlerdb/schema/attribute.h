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

#ifndef _ATTRIBUTE_H
#define _ATTRIBUTE_H

enum {
    VALUE        = 0x00000001,
    REF          = 0x00000002,

    REQUIRED     = 0x00000008,
    PROCESS_GET  = 0x00000010,
    PROCESS_SET  = 0x00000020,
    SINGLE       = 0x00000040,
    LIST         = 0x00000080,
    DICT         = 0x00000100,
    SET          = 0x00000200,
    ALIAS        = 0x00000400,
    KIND         = 0x00000800,
    NOINHERIT    = 0x00001000,
    SIMPLE       = 0x00002000,
    INDEXED      = 0x00004000,
    DEFAULT      = 0x00008000,
    AFTERCHANGE  = 0x00010000,
    PURE         = 0x00020000,

    ATTRDICT     = VALUE | REF,
    CARDINALITY  = SINGLE | LIST | DICT | SET,
    PROCESS      = PROCESS_GET | PROCESS_SET,
};

typedef struct {
    PyObject_HEAD
    PyObject *attrID;
    unsigned long flags;
    PyObject *otherName;
    PyObject *defaultValue;
    PyObject *typeID;
    PyObject *afterChange;
} t_attribute;

typedef int (*CAttribute_invokeAfterChange_fn)(t_attribute *, PyObject *,
                                               PyObject *, PyObject *);

#endif /* _ATTRIBUTE_H */
