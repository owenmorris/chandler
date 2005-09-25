
/*
 * The attribute C type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


enum {
    VALUE        = 0x0001,
    REF          = 0x0002,
    REDIRECT     = 0x0004,
    REQUIRED     = 0x0008,
    PROCESS_GET  = 0x0010,
    PROCESS_SET  = 0x0020,
    SINGLE       = 0x0040,
    LIST         = 0x0080,
    DICT         = 0x0100,
    SET          = 0x0200,
    ALIAS        = 0x0400,
    KIND         = 0x0800,
    NOINHERIT    = 0x1000,
    TRANSIENT    = 0x2000,
    INDEXED      = 0x4000,

    ATTRDICT     = VALUE | REF | REDIRECT,
    CARDINALITY  = SINGLE | LIST | DICT | SET,
    PROCESS      = PROCESS_GET | PROCESS_SET,
};

typedef struct {
    PyObject_HEAD
    PyObject *attrID;
    int flags;
    PyObject *otherName;
    PyObject *redirectTo;
    PyObject *typeID;
} t_attribute;


typedef PyObject *(*CAttribute_getAspect_fn)(t_attribute *,
                                             PyObject *, PyObject *);
