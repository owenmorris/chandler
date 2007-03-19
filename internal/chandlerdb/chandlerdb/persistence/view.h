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

#ifndef _VIEW_H
#define _VIEW_H

#include "../util/ctxmgr.h"

typedef struct {
    PyObject_HEAD
    Item_HEAD
    PyObject *repository;
    PyObject *changeNotifications;
    PyObject *registry;
    PyObject *refRegistry;
    PyObject *deletedRegistry;
    PyObject *instanceRegistry;
    PyObject *uuid;
    PyObject *singletons;
    PyObject *monitors;
    PyObject *watchers;
    PyObject *debugOn;
    PyObject *deferredDeletes;
    t_ctxmgr *deferredIndexingCtx;
    t_ctxmgr *deferredObserversCtx;
    int refreshErrors;
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
    /* VMERGED    = 0x00010000, from CItem */
    /* RMERGED    = 0x00020000, from CItem */
    /* NMERGED    = 0x00040000, from CItem */
    /* CMERGED    = 0x00080000, from CItem */
    COMMITREQ  = 0x00100000,
    BADPASSWD  = 0x00200000,
    ENCRYPTED  = 0x00400000,
    DEFERIDX   = 0x00800000,
    DEFEROBSD  = 0x01000000,  /* defer observers, discarding redundant calls */
    DEFEROBSA  = 0x02000000,  /* defer observers, keeping all calls */
};

enum {
    DEFEROBS   = DEFEROBSD | DEFEROBSA,
};


typedef PyObject *(*_t_view_invokeMonitors_fn)(t_view *, PyObject *,
                                               PyObject *);

#endif /* _VIEW_H */
