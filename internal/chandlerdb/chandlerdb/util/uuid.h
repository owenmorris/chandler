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

#ifndef _UUID_H
#define _UUID_H

typedef struct {
    PyObject_HEAD
    PyObject *uuid;
    long hash;
} t_uuid;

typedef int (*PyUUID_Check_fn)(PyObject *obj);
/* steals reference to obj */
typedef PyObject *(*PyUUID_Make16_fn)(PyObject *obj);
typedef int (*_hash_bytes_fn)(char *obj, int len);
typedef long (*_long_hash_bytes_fn)(char *obj, int len);

#endif /* _UUID_H */
