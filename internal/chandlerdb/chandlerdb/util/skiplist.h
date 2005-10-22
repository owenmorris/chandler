
/*
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


typedef struct {
    PyObject_HEAD
    PyObject *levels;
    int entryValue;
} t_node;

typedef struct {
    PyObject_HEAD
    PyObject *prevKey;
    PyObject *nextKey;
    int dist;
} t_point;


typedef struct {
    PyObject_HEAD
    PyObject *head;
    PyObject *tail;
    PyObject *map;
} t_sl;
