
/*
 * The C item types module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */


#include <Python.h>
#include "structmember.h"

#include "c.h"

PyTypeObject *SingleRef = NULL;
PyTypeObject *CItem = NULL;
PyTypeObject *CValues = NULL;
PyTypeObject *CDescriptor = NULL;
PyTypeObject *ItemValue = NULL;
PyObject *Nil = NULL;
PyObject *Default = NULL;

CView_invokeMonitors_fn CView_invokeMonitors = NULL;
PyCFunction _countAccess = NULL;


static PyObject *isitem(PyObject *self, PyObject *obj)
{
    if (PyObject_TypeCheck(obj, CItem))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *_install__doc__(PyObject *self, PyObject *args)
{
    PyObject *object, *doc, *x;
    PyTypeObject *type;
    char *string;

    if (!PyArg_ParseTuple(args, "OO", &object, &doc))
        return NULL;

    string = PyString_AsString(doc);
    if (!string)
        return NULL;

    x = PyObject_GetAttrString((PyObject *) CItem, "isNew");
    type = x->ob_type;
    Py_DECREF(x);

    if (object->ob_type == type)
    {
        ((PyMethodDescrObject *) object)->d_method->ml_doc = strdup(string);
        Py_RETURN_NONE;
    }

    x = PyObject_GetAttrString((PyObject *) CItem, "itsKind");
    type = x->ob_type;
    Py_DECREF(x);

    if (object->ob_type == type)
    {
        ((PyGetSetDescrObject *) object)->d_getset->doc = strdup(string);
        Py_RETURN_NONE;
    }

    x = PyObject_GetAttrString((PyObject *) CItem, "_uuid");
    type = x->ob_type;
    Py_DECREF(x);

    if (object->ob_type == type)
    {
        ((PyMemberDescrObject *) object)->d_member->doc = strdup(string);
        Py_RETURN_NONE;
    }

    if (object->ob_type == CItem->ob_type)
    {
        object->ob_type->tp_doc = strdup(string);
        Py_RETURN_NONE;
    }

    PyErr_SetObject(PyExc_TypeError, object);
    return NULL;
}

static PyMethodDef c_funcs[] = {
    { "isitem", (PyCFunction) isitem, METH_O,
      "isinstance(), but not as easily fooled" },
    { "_install__doc__", (PyCFunction) _install__doc__, METH_VARARGS,
      "install immutable doc strings from python" },
    { NULL, NULL, 0, NULL }
};


void PyDict_SetItemString_Int(PyObject *dict, char *key, int value)
{
    PyObject *pyValue = PyInt_FromLong(value);

    PyDict_SetItemString(dict, key, pyValue);
    Py_DECREF(pyValue);
}


void initc(void)
{
    PyObject *m = Py_InitModule3("c", c_funcs, "C item types module");

    _init_item(m);
    _init_values(m);

    m = PyImport_ImportModule("chandlerdb.util.c");
    LOAD_TYPE(m, SingleRef);
    Py_DECREF(m);

    m = PyImport_ImportModule("chandlerdb.item.ItemValue");
    LOAD_TYPE(m, ItemValue);
    Py_DECREF(m);

    m = PyImport_ImportModule("chandlerdb.schema.c");
    LOAD_TYPE(m, CDescriptor);
    LOAD_CFUNC(m, _countAccess);
    Py_DECREF(m);

    m = PyImport_ImportModule("chandlerdb.persistence.c");
    LOAD_FN(m, CView_invokeMonitors);
    Py_DECREF(m);
}    
