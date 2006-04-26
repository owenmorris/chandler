
/*
 * The item C type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


/*
 * t_item and t_view share the same top fields because
 * a view is also the parent of root items
 */

#ifndef _ITEM_H
#define _ITEM_H


#define Item_HEAD                   \
    unsigned long status;           \
    unsigned long long version;     \
    PyObject *name;


typedef struct {
    PyObject_HEAD
    PyObject *item;
    PyObject *dict;
    PyObject *flags;
} t_values;

typedef struct {
    PyObject_HEAD
    Item_HEAD
    unsigned long lastAccess;
    PyObject *uuid;
    t_values *values;
    t_values *references;
    PyObject *kind;
    PyObject *parent;
    PyObject *children;
    PyObject *root;
    PyObject *acls;
} t_item;

enum {
    DELETED    = 0x00000001,
    VDIRTY     = 0x00000002,          /* literal or ref changed */
    DELETING   = 0x00000004,
    RAW        = 0x00000008,
    FDIRTY     = 0x00000010,          /* fresh dirty since last mapChange() */
    SCHEMA     = 0x00000020,
    NEW        = 0x00000040,
    STALE      = 0x00000080,
    NDIRTY     = 0x00000100,          /* parent, name changed */
    CDIRTY     = 0x00000200,          /* children list changed */
    RDIRTY     = 0x00000400,          /* ref collection changed */
    CORESCHEMA = 0x00000800,          /* core schema item */
    CONTAINER  = 0x00001000,          /* has children */
    ADIRTY     = 0x00002000,          /* acl(s) changed */
    PINNED     = 0x00004000,          /* auto-refresh, don't stale */
    NODIRTY    = 0x00008000,          /* turn off dirtying */
    VMERGED    = 0x00010000,
    RMERGED    = 0x00020000,
    NMERGED    = 0x00040000,
    CMERGED    = 0x00080000,
    COPYEXPORT = 0x00100000,          /* item instance is copied on export */
    IMPORTING  = 0x00200000,          /* item is being imported */
    MUTATING   = 0x00400000,          /* kind is being removed */
    KDIRTY     = 0x00800000,          /* kind changed */
    P_WATCHED  = 0x01000000,          /* watched, persistently */
    T_WATCHED  = 0x02000000,          /* watched, transiently  */
    DEFERRED   = 0x04000000,          /* delete deferred until commit */
    DEFERRING  = 0x08000000,          /* deferring delete */
};

enum {
    VRDIRTY    = VDIRTY | RDIRTY,
    DIRTY      = VDIRTY | RDIRTY | NDIRTY | CDIRTY | KDIRTY,
    MERGED     = VMERGED | RMERGED | NMERGED | CMERGED,
    SAVEMASK   = (DIRTY | ADIRTY |
                  NEW | DELETED | P_WATCHED |
                  SCHEMA | CORESCHEMA | CONTAINER),
    WATCHED    = P_WATCHED | T_WATCHED,
};

#endif
