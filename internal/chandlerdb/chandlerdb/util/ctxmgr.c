/*
 *  Copyright (c) 2007-2007 Open Source Applications Foundation
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

static PyObject *t_ctxmgr_new(PyTypeObject *self,
                              PyObject *args, PyObject *kwds);
static void t_ctxmgr_dealloc(t_ctxmgr *self);
static int t_ctxmgr_traverse(t_ctxmgr *self, visitproc visit, void *arg);
static int t_ctxmgr_clear(t_ctxmgr *self);

static PyObject *t_ctxmgr_enter(t_ctxmgr *self);
static PyObject *t_ctxmgr_exit(t_ctxmgr *self, PyObject *args);

static PyMemberDef t_ctxmgr_members[] = {
    { "_count", T_UINT, offsetof(t_ctxmgr, count), READONLY, "call depth" },
    { "_data", T_OBJECT, offsetof(t_ctxmgr, data), READONLY, "ctx data" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_ctxmgr_methods[] = {
    { "__enter__", (PyCFunction) t_ctxmgr_enter, METH_NOARGS, NULL },
    { "__exit__", (PyCFunction) t_ctxmgr_exit, METH_VARARGS, NULL },
    { "enter", (PyCFunction) t_ctxmgr_enter, METH_NOARGS, NULL },
    { "exit", (PyCFunction) t_ctxmgr_exit, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject CtxMgrType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.util.c.CtxMgr",                /* tp_name */
    sizeof(t_ctxmgr),                          /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_ctxmgr_dealloc,              /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    0,                                         /* tp_repr */
    0,                                         /* tp_as_number */
    0,                                         /* tp_as_sequence */
    0,                                         /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    0,                                         /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "CtxMgr type",                             /* tp_doc */
    (traverseproc)t_ctxmgr_traverse,           /* tp_traverse */
    (inquiry)t_ctxmgr_clear,                   /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    0,                                         /* tp_iter */
    0,                                         /* tp_iternext */
    t_ctxmgr_methods,                          /* tp_methods */
    t_ctxmgr_members,                          /* tp_members */
    0,                                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    0,                                         /* tp_init */
    0,                                         /* tp_alloc */ 
    (newfunc)t_ctxmgr_new,                     /* tp_new */
};

static PyObject *t_ctxmgr_new(PyTypeObject *type,
                              PyObject *args, PyObject *kwds)
{
    t_ctxmgr *self = (t_ctxmgr *) type->tp_alloc(type, 0);

    if (self)
    {
        self->count = 0;
        self->target = NULL;
        self->enterFn = NULL;
        self->exitFn = NULL;
        self->data = NULL;
    }

    return (PyObject *) self;
}

static void t_ctxmgr_dealloc(t_ctxmgr *self)
{
    t_ctxmgr_clear(self);
    self->ob_type->tp_free((PyObject *) self);    
}

static int t_ctxmgr_traverse(t_ctxmgr *self, visitproc visit, void *arg)
{
    Py_VISIT(self->target);
    Py_VISIT(self->data);

    return 0;
}

static int t_ctxmgr_clear(t_ctxmgr *self)
{
    Py_CLEAR(self->target);
    Py_CLEAR(self->data);

    return 0;
}

static PyObject *t_ctxmgr_enter(t_ctxmgr *self)
{
    if (!self->target || !self->enterFn)
    {
        PyErr_SetString(PyExc_ValueError, "CtxMgr instance has no target");
        return NULL;
    }

    return self->enterFn(self->target, self);
}

static PyObject *t_ctxmgr_exit(t_ctxmgr *self, PyObject *args)
{
    PyObject *type, *value, *traceback;

    if (!PyArg_ParseTuple(args, "OOO", &type, &value, &traceback))
        return NULL;

    if (!self->target || !self->exitFn)
    {
        PyErr_SetString(PyExc_ValueError, "CtxMgr instance has no target");
        return NULL;
    }

    return self->exitFn(self->target, self, type, value, traceback);
}

void _init_ctxmgr(PyObject *m)
{
    if (PyType_Ready(&CtxMgrType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&CtxMgrType);
            PyModule_AddObject(m, "CtxMgr", (PyObject *) &CtxMgrType);
        }
    }
}
