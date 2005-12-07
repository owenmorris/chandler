
/*
 * The kind C type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


typedef struct {
    PyObject_HEAD
    t_item *kind;
    unsigned long flags;
} t_kind;

enum {
    MONITOR_SCHEMA    = 0x0001,
    ATTRIBUTES_CACHED = 0x0002,
    SUPERKINDS_CACHED = 0x0004,
};
