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
    TOINDEX    = 0x10000000,          /* to be full-text indexed */
};

enum {
    VRDIRTY    = VDIRTY | RDIRTY,
    DIRTY      = VDIRTY | RDIRTY | NDIRTY | CDIRTY | KDIRTY,
    MERGED     = VMERGED | RMERGED | NMERGED | CMERGED,
    SAVEMASK   = (DIRTY | ADIRTY |
                  NEW | DELETED | P_WATCHED | TOINDEX |
                  SCHEMA | CORESCHEMA | CONTAINER),
    WATCHED    = P_WATCHED | T_WATCHED,
};


enum {
    V_READONLY  = 0x0001,        /* value is read-only      */

    /* flags in 0x00f0 are used by the persistence format   */
    V_INDEXED   = 0x0010,        /* value is indexed        */
    V_TOINDEX   = 0x0020,        /* value needs indexing    */

    V_DIRTY     = 0x0100,        /* value is dirty          */
    V_TRANSIENT = 0x0200,        /* value is transient      */
    V_SAVEMASK  = 0x000f,        /* save these flags        */
    V_COPYMASK  = V_READONLY | V_TRANSIENT
};


#endif
