/*
 *  Copyright (c) 2007-2007 Open Source Applications Foundation
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


#ifndef _CTXMGR_H
#define _CTXMGR_H

typedef struct _ctxmgr {
    PyObject_HEAD
    int count;
    PyObject *target;
    PyObject *(*enterFn)(PyObject *, struct _ctxmgr *);
    PyObject *(*exitFn)(PyObject *, struct _ctxmgr *,
                        PyObject *, PyObject *, PyObject *);
    PyObject *data;
} t_ctxmgr;


#endif /* _CTXMGR_H */
