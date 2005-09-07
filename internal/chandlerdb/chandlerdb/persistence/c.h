
/*
 * The C repository types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include "../item/item.h"

/*
 * t_item and t_view share the same top fields because
 * a view is also the parent of root items
 */

typedef struct {
    PyObject_HEAD
    Item_HEAD
    PyObject *repository;
    PyObject *changeNotifications;
} t_view;

typedef struct {
    PyObject_HEAD
    unsigned long status;
} t_repository;

enum {
    OPEN       = 0x0001,
    REFCOUNTED = 0x0002,
    LOADING    = 0x0004,
    COMMITTING = 0x0008,
    /* FDIRTY  = 0x0010, from CItem */
    RECORDING  = 0x0020,

    /* STALE   = 0x0080, from CItem */
    /* CDIRTY  = 0x0200, from CItem */

    VERIFY     = 0x1000,
    DEBUG      = 0x2000,
    RAMDB      = 0x4000,
    CLOSED     = 0x8000,
    /*
     * merge flags from CItem
     */
};

void _init_view(PyObject *m);
void _init_repository(PyObject *m);
void PyDict_SetItemString_Int(PyObject *dict, char *key, int value);
