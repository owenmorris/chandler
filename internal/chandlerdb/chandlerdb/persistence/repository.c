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

static void t_repository_dealloc(t_repository *self);
static int t_repository_traverse(t_repository *self,
                                 visitproc visit, void *arg);
static int t_repository_clear(t_repository *self);
static PyObject *t_repository_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds);
static int t_repository_init(t_repository *self,
                             PyObject *args, PyObject *kwds);
static PyObject *t_repository__isRepository(t_repository *self, PyObject *args);
static PyObject *t_repository__isView(t_repository *self, PyObject *args);
static PyObject *t_repository__isItem(t_repository *self, PyObject *args);
static PyObject *t_repository__getRepository(t_repository *self, void *data);
static PyObject *t_repository_isOpen(t_repository *self, PyObject *args);
static PyObject *t_repository_isClosed(t_repository *self, PyObject *args);
static PyObject *t_repository_isRefCounted(t_repository *self, PyObject *args);
static PyObject *t_repository_isDebug(t_repository *self, PyObject *args);
static PyObject *t_repository__isVerify(t_repository *self, PyObject *args);


static PyMemberDef t_repository_members[] = {
    { "_status", T_UINT, offsetof(t_repository, status), 0,
      "repository status flags" },
    { "store", T_OBJECT, offsetof(t_repository, store), 0,
      "repository store" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_repository_methods[] = {
    { "_isRepository", (PyCFunction) t_repository__isRepository, METH_NOARGS, "" },
    { "_isView", (PyCFunction) t_repository__isView, METH_NOARGS, "" },
    { "_isItem", (PyCFunction) t_repository__isItem, METH_NOARGS, "" },
    { "isOpen", (PyCFunction) t_repository_isOpen, METH_NOARGS, "" },
    { "isClosed", (PyCFunction) t_repository_isClosed, METH_NOARGS, "" },
    { "isRefCounted", (PyCFunction) t_repository_isRefCounted, METH_NOARGS, "" },
    { "isDebug", (PyCFunction) t_repository_isDebug, METH_NOARGS, "" },
    { "_isVerify", (PyCFunction) t_repository__isVerify, METH_NOARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_repository_properties[] = {
    { "repository", (getter) t_repository__getRepository, NULL,
      "repository property", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject RepositoryType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.persistence.c.CRepository",              /* tp_name */
    sizeof(t_repository),                                /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_repository_dealloc,                    /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    0,                                                   /* tp_repr */
    0,                                                   /* tp_as_number */
    0,                                                   /* tp_as_sequence */
    0,                                                   /* tp_as_mapping */
    0,                                                   /* tp_hash  */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    0,                                                   /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                                /* tp_flags */
    "C Repository type",                                 /* tp_doc */
    (traverseproc)t_repository_traverse,                 /* tp_traverse */
    (inquiry)t_repository_clear,                         /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_repository_methods,                                /* tp_methods */
    t_repository_members,                                /* tp_members */
    t_repository_properties,                             /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_repository_init,                         /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_repository_new,                           /* tp_new */
};


static void t_repository_dealloc(t_repository *self)
{
    t_repository_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_repository_traverse(t_repository *self,
                                 visitproc visit, void *arg)
{
    Py_VISIT(self->store);
    return 0;
}

static int t_repository_clear(t_repository *self)
{
    Py_CLEAR(self->store);
    return 0;
}

static PyObject *t_repository_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

static int t_repository_init(t_repository *self,
                             PyObject *args, PyObject *kwds)
{
    self->status = CLOSED;
    return 0;
}


static PyObject *t_repository__isRepository(t_repository *self, PyObject *args)
{
    Py_RETURN_TRUE;
}

static PyObject *t_repository__isView(t_repository *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_repository__isItem(t_repository *self, PyObject *args)
{
    Py_RETURN_FALSE;
}


static PyObject *t_repository_isOpen(t_repository *self, PyObject *args)
{
    if (self->status & OPEN)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_repository_isClosed(t_repository *self, PyObject *args)
{
    if (self->status & CLOSED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_repository_isRefCounted(t_repository *self, PyObject *args)
{
    if (self->status & REFCOUNTED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_repository_isDebug(t_repository *self, PyObject *args)
{
    if (self->status & DEBUG)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_repository__isVerify(t_repository *self, PyObject *args)
{
    if (self->status & VERIFY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}


/* repository */

static PyObject *t_repository__getRepository(t_repository *self, void *data)
{
    Py_INCREF(self);
    return (PyObject *) self;
}


void _init_repository(PyObject *m)
{
    if (PyType_Ready(&RepositoryType) >= 0)
    {
        if (m)
        {
            PyObject *dict = RepositoryType.tp_dict;

            Py_INCREF(&RepositoryType);
            PyModule_AddObject(m, "CRepository", (PyObject *) &RepositoryType);
            CRepository = &RepositoryType;

            PyDict_SetItemString_Int(dict, "OPEN", OPEN);
            PyDict_SetItemString_Int(dict, "REFCOUNTED", REFCOUNTED);
            PyDict_SetItemString_Int(dict, "VERIFY", VERIFY);
            PyDict_SetItemString_Int(dict, "DEBUG", DEBUG);
            PyDict_SetItemString_Int(dict, "RAMDB", RAMDB);
            PyDict_SetItemString_Int(dict, "CLOSED", CLOSED);
            PyDict_SetItemString_Int(dict, "BADPASSWD", BADPASSWD);
            PyDict_SetItemString_Int(dict, "ENCRYPTED", ENCRYPTED);
        }
    }
}
