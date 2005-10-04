
/*
 * The C util types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include "fns.h"
#include "uuid.h"

extern PyTypeObject *UUID;
extern PyTypeObject *Key;
extern PyTypeObject *Cipher;

void PyDict_SetItemString_Int(PyObject *, char *, int);

void _init_uuid(PyObject *m);
void _init_rijndael(PyObject *m);
