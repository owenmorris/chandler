
/*
 * The descriptor C type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

typedef struct {
    PyObject_HEAD
    PyObject *name;
    PyObject *attrs;
} t_descriptor;

