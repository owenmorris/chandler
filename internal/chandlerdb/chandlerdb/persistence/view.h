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
    t_ctxmgr *deferredNotificationsCtx;
    t_ctxmgr *deferredCommitCtx;
    int refreshErrors;
} t_view;


enum {
    OPEN        = 0x00000001,
    REFCOUNTED  = 0x00000002,
    LOADING     = 0x00000004,
    COMMITTING  = 0x00000008,
    /* FDIRTY   = 0x00000010, from CItem */
    DEFERNOTIF  = 0x00000020,  /* defer all change notifications */
    MONITORING  = 0x00000040,
    /* STALE    = 0x00000080, from CItem */
    REFRESHING  = 0x00000100,
    /* CDIRTY   = 0x00000200, from CItem */
    DEFERDEL    = 0x00000400,

    VERIFY      = 0x00001000,
    DEBUG       = 0x00002000,
    RAMDB       = 0x00004000,
    CLOSED      = 0x00008000,
    /* MERGED   = 0x00010000, from CItem */
    DONTNOTIFY  = 0x00020000,  /* invert notify default to False         */


    COMMITREQ   = 0x00100000,
    BADPASSWD   = 0x00200000,
    ENCRYPTED   = 0x00400000,
    DEFERIDX    = 0x00800000,
    DEFEROBSD   = 0x01000000,  /* defer observers, discarding dup. calls */
    DEFEROBSA   = 0x02000000,  /* defer observers, keeping all calls     */
    DEFERCOMMIT = 0x04000000,  /* defer commit calls                     */
    COMMITLOCK  = 0x08000000,  /* view locked during commit              */
    /* TOINDEX  = 0x10000000, from CItem */
};

enum {
    DEFEROBS   = DEFEROBSD | DEFEROBSA,
    W_SAVEMASK = TOINDEX
};

typedef PyObject *(*_t_view_invokeMonitors_fn)(t_view *, PyObject *,
                                               PyObject *);

#endif /* _VIEW_H */
