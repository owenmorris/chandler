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
    PyObject *name;
    t_attribute *attr;
} t_descriptor;

typedef PyObject *(*CDescriptor_get_fn)(t_descriptor *self,
                                        t_item *item, PyObject *type);
typedef int (*CDescriptor_set_fn)(t_descriptor *self,
                                  t_item *item, PyObject *value);
