
/*
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


typedef struct {
    PyObject_HEAD
    PyObject *owner;
    PyObject *previousKey;
    PyObject *nextKey;
    PyObject *value;
    PyObject *alias;
} t_link;


typedef struct {
    PyObject_HEAD
    int flags;
    int count;
    PyObject *dict;
    PyObject *aliases;
    PyObject *head;
} t_lm;


enum {
    LM_NEW  = 0x0001,
    LM_LOAD = 0x0002
};
