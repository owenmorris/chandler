
/*
 * The C util types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include "fns.h"
#include "uuid.h"
#include "singleref.h"
#include "linkedmap.h"

extern PyTypeObject *UUID;
extern PyTypeObject *SingleRef;
extern PyTypeObject *Key;
extern PyTypeObject *Cipher;
extern PyTypeObject *CLinkedMap;
extern PyTypeObject *CLink;

void PyDict_SetItemString_Int(PyObject *, char *, int);

void _init_uuid(PyObject *m);
void _init_singleref(PyObject *m);
void _init_rijndael(PyObject *m);
void _init_linkedmap(PyObject *m);
