
/*
 * The C view type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
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
    PyObject *monitors;
    PyObject *singletons;
    PyObject *watcherDispatch;
    PyObject *debugOn;
    PyObject *deferredDeletes;
} t_view;

enum {
    OPEN       = 0x0001,
    REFCOUNTED = 0x0002,
    LOADING    = 0x0004,
    COMMITTING = 0x0008,
    /* FDIRTY  = 0x0010, from CItem */
    RECORDING  = 0x0020,
    MONITORING = 0x0040,
    /* STALE   = 0x0080, from CItem */
    REFRESHING = 0x0100,
    /* CDIRTY  = 0x0200, from CItem */
    DEFERDEL   = 0x0400,
    BGNDINDEX  = 0x0800,
    VERIFY     = 0x1000,
    DEBUG      = 0x2000,
    RAMDB      = 0x4000,
    CLOSED     = 0x8000,

    /*
     * merge flags from CItem
     */
};


typedef PyObject *(*CView_invokeMonitors_fn)(t_view *, PyObject *);
typedef int (*CView_invokeWatchers_fn)(t_view *, PyObject *,
                                       PyObject *, PyObject *,
                                       PyObject *, PyObject *,
                                       PyObject *);
