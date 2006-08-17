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

/*
 * t_item and t_view share the same top fields because
 * a view is also the parent of root items
 */

typedef struct {
    PyObject_HEAD
    Item_HEAD
    PyObject *repository;
    PyObject *changeNotifications;
    PyObject *registry;
    PyObject *deletedRegistry;
    PyObject *uuid;
    PyObject *singletons;
    PyObject *monitors;
    PyObject *watchers;
    PyObject *debugOn;
    PyObject *deferredDeletes;
} t_view;

enum {
    OPEN       = 0x00000001,
    REFCOUNTED = 0x00000002,
    LOADING    = 0x00000004,
    COMMITTING = 0x00000008,
    /* FDIRTY  = 0x00000010, from CItem */
    RECORDING  = 0x00000020,
    MONITORING = 0x00000040,
    /* STALE   = 0x00000080, from CItem */
    REFRESHING = 0x00000100,
    /* CDIRTY  = 0x00000200, from CItem */
    DEFERDEL   = 0x00000400,
    BGNDINDEX  = 0x00000800,
    VERIFY     = 0x00001000,
    DEBUG      = 0x00002000,
    RAMDB      = 0x00004000,
    CLOSED     = 0x00008000,
    COMMITREQ  = 0x00010000,

    /*
     * merge flags from CItem
     */
};


typedef PyObject *(*CView_invokeMonitors_fn)(t_view *, PyObject *);
