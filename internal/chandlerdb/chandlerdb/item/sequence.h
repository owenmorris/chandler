/*
 *  Copyright (c) 2007 Open Source Applications Foundation
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

#ifndef _SEQUENCE_H
#define _SEQUENCE_H

#include "../item/itemvalue.h"

typedef struct {
    t_itemvalue itemvalue;
    PyObject *sequence;
} t_sequence;

#endif /* _SEQUENCE_H */
