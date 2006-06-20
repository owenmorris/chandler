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

static void t_lock_dealloc(t_lock *self);
static int t_lock_init(t_lock *self, PyObject *args, PyObject *kwds);

static PyMemberDef t_lock_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_lock_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_lock_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject DBLockType = {
    PyObject_HEAD_INIT(NULL)
    0,                                               /* ob_size */
    "chandlerdb.persistence.c.DBLock",               /* tp_name */
    sizeof(t_lock),                                  /* tp_basicsize */
    0,                                               /* tp_itemsize */
    (destructor)t_lock_dealloc,                      /* tp_dealloc */
    0,                                               /* tp_print */
    0,                                               /* tp_getattr */
    0,                                               /* tp_setattr */
    0,                                               /* tp_compare */
    0,                                               /* tp_repr */
    0,                                               /* tp_as_number */
    0,                                               /* tp_as_sequence */
    0,                                               /* tp_as_mapping */
    0,                                               /* tp_hash  */
    0,                                               /* tp_call */
    0,                                               /* tp_str */
    0,                                               /* tp_getattro */
    0,                                               /* tp_setattro */
    0,                                               /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                              /* tp_flags */
    "C DBLock type",                                 /* tp_doc */
    0,                                               /* tp_traverse */
    0,                                               /* tp_clear */
    0,                                               /* tp_richcompare */
    0,                                               /* tp_weaklistoffset */
    0,                                               /* tp_iter */
    0,                                               /* tp_iternext */
    t_lock_methods,                                  /* tp_methods */
    t_lock_members,                                  /* tp_members */
    t_lock_properties,                               /* tp_getset */
    0,                                               /* tp_base */
    0,                                               /* tp_dict */
    0,                                               /* tp_descr_get */
    0,                                               /* tp_descr_set */
    0,                                               /* tp_dictoffset */
    (initproc)t_lock_init,                           /* tp_init */
    0,                                               /* tp_alloc */
    (newfunc)t_lock_new,                             /* tp_new */
};


int _t_lock_put(t_lock *self)
{
    if (self->env && self->env->db_env)
    {
        DB_ENV *db_env = self->env->db_env;
        int err;

        Py_BEGIN_ALLOW_THREADS;
        err = db_env->lock_put(db_env, &self->lock);
        Py_END_ALLOW_THREADS;

        if (err)
        {
            raiseDBError(err);
            return -1;
        }

        self->held = 0;
    }

    return 0;
}

static void t_lock_dealloc(t_lock *self)
{
    if (self->held == 1)
    {
        _t_lock_put(self);
        self->held = 0;
    }

    Py_XDECREF(self->env);
    self->env = NULL;

    self->ob_type->tp_free((PyObject *) self);
}

PyObject *t_lock_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    return type->tp_alloc(type, 0);
}

int _t_lock_init(t_lock *self, t_env *env, int id, DBT *data,
                 db_lockmode_t mode, int flags)
{
    int err;

    Py_BEGIN_ALLOW_THREADS;
    err = env->db_env->lock_get(env->db_env, id, flags, data, mode,
                                &self->lock);
    Py_END_ALLOW_THREADS;

    if (err)
    {
        raiseDBError(err);
        return -1;
    }

    Py_INCREF(env); Py_XDECREF(self->env);
    self->env = env;
    self->held = 1;

    return 0;
}

static int t_lock_init(t_lock *self, PyObject *args, PyObject *kwds)
{
    PyObject *env;
    int id;
    db_lockmode_t mode;
    DBT data;
    int flags = 0;

    if (!self->env || !self->env->db_env)
    {
        raiseDBError(EINVAL);
        return -1;
    }

    if (!PyArg_ParseTuple(args, "Ois#i|i", &env, &id, &data.data, &data.size,
                          &mode, &flags))
        return -1;

    if (!PyObject_TypeCheck(env, CDBEnv))
    {
        PyErr_SetObject(PyExc_TypeError, env);
        return -1;
    }

    return _t_lock_init(self, (t_env *) env, id, &data, mode, flags);
}


void _init_lock(PyObject *m)
{
    if (PyType_Ready(&DBLockType) >= 0)
    {
        if (m)
        {
            PyObject *dict = DBLockType.tp_dict;

            Py_INCREF(&DBLockType);
            PyModule_AddObject(m, "DBLock", (PyObject *) &DBLockType);

            CDBLock = &DBLockType;

            /* flags */
            SET_DB_INT(dict, DB_LOCK_READ);
            SET_DB_INT(dict, DB_LOCK_WRITE);
            SET_DB_INT(dict, DB_LOCK_IWRITE);
            SET_DB_INT(dict, DB_LOCK_IREAD);
            SET_DB_INT(dict, DB_LOCK_IWR);
        }
    }
}
