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

#ifndef _ATTRIBUTE_H
#define _ATTRIBUTE_H

enum {
    A_VALUE        = 0x00000001,
    A_REF          = 0x00000002,

    A_REQUIRED     = 0x00000008,
    A_PROCESS_GET  = 0x00000010,
    A_PROCESS_SET  = 0x00000020,
    A_SINGLE       = 0x00000040,
    A_LIST         = 0x00000080,
    A_DICT         = 0x00000100,
    A_SET          = 0x00000200,
    A_ALIAS        = 0x00000400,
    A_KIND         = 0x00000800,
    A_NOINHERIT    = 0x00001000,
    A_SIMPLE       = 0x00002000,
    A_INDEXED      = 0x00004000,
    A_DEFAULT      = 0x00008000,
    A_AFTERCHANGE  = 0x00010000,
    A_PURE         = 0x00020000,

    ATTRDICT     = A_VALUE | A_REF,
    CARDINALITY  = A_SINGLE | A_LIST | A_DICT | A_SET,
    PROCESS      = A_PROCESS_GET | A_PROCESS_SET,
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
