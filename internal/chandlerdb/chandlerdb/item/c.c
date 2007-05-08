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


#include <Python.h>
#include "structmember.h"

#include "c.h"

PyTypeObject *ItemRef = NULL;
PyTypeObject *CLinkedMap = NULL;
PyTypeObject *Iterator = NULL;
PyTypeObject *CItem = NULL;
PyTypeObject *CValues = NULL;
PyTypeObject *CKind = NULL;
PyTypeObject *CAttribute = NULL;
PyTypeObject *CDescriptor = NULL;
PyTypeObject *ItemValue = NULL;
PyTypeObject *PersistentValue = NULL;
PyTypeObject *StaleItemAttributeError = NULL;
PyTypeObject *ReadOnlyAttributeError = NULL;
PyTypeObject *ChangeDuringCommitError = NULL;
PyTypeObject *KindlessItemError = NULL;
PyTypeObject *CView = NULL;
PyObject *Nil = NULL;
PyObject *Default = NULL;
PyObject *True_TUPLE = NULL;
PyObject *Empty_TUPLE = NULL;
long itemCount = 0;

_t_view_invokeMonitors_fn _t_view_invokeMonitors;
_t_persistentvalue_init_fn _t_persistentvalue_init;
PyUUID_Check_fn PyUUID_Check;
C_countAccess_fn C_countAccess;
CAttribute_invokeAfterChange_fn CAttribute_invokeAfterChange;

static PyObject *isitem(PyObject *self, PyObject *obj)
{
    if (PyObject_TypeCheck(obj, CItem))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *isitemref(PyObject *self, PyObject *obj)
{
    if (obj->ob_type == ItemRef)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *getItemCount(PyObject *self)
{
    return PyInt_FromLong(itemCount);
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
    { "isitemref", (PyCFunction) isitemref, METH_O,
      "isinstance(obj, ItemRef)"},
    { "getItemCount", (PyCFunction) getItemCount, METH_NOARGS,
      "the number of item instances currently allocated by this process" },
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
    PyObject *module = Py_InitModule3("c", c_funcs, "C item types module");
    PyObject *m;

    True_TUPLE = PyTuple_Pack(1, Py_True);
    Empty_TUPLE = PyTuple_New(0);

    if (!(m = PyImport_ImportModule("chandlerdb.util.c")))
        return;
    LOAD_TYPE(m, CLinkedMap);
    LOAD_TYPE(m, Iterator);
    LOAD_TYPE(m, PersistentValue);
    LOAD_FN(m, PyUUID_Check);
    LOAD_FN(m, _t_persistentvalue_init);
    LOAD_OBJ(m, Nil);
    LOAD_OBJ(m, Default);
    Py_DECREF(m);

    _init_item(module);
    _init_itemref(module);
    _init_values(module);
    _init_indexes(module);
    _init_itemvalue(module);
    _init_sequence(module);
    _init_mapping(module);
    _init_set(module);

    if (!(m = PyImport_ImportModule("chandlerdb.item.ItemError")))
        return;
    LOAD_TYPE(m, StaleItemAttributeError);
    LOAD_TYPE(m, ReadOnlyAttributeError);
    LOAD_TYPE(m, ChangeDuringCommitError);
    LOAD_TYPE(m, KindlessItemError);
    Py_DECREF(m);

    if (!(m = PyImport_ImportModule("chandlerdb.schema.c")))
        return;
    LOAD_TYPE(m, CKind);
    LOAD_TYPE(m, CAttribute);
    LOAD_TYPE(m, CDescriptor);
    LOAD_FN(m, CAttribute_invokeAfterChange);
    LOAD_FN(m, C_countAccess);
    Py_DECREF(m);

    if (!(m = PyImport_ImportModule("chandlerdb.persistence.c")))
        return;
    LOAD_TYPE(m, CView);
    LOAD_FN(m, _t_view_invokeMonitors);
    Py_DECREF(m);
}    
