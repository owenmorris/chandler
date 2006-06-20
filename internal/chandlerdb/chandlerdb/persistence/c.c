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

#include <db.h>
#include "c.h"

PyTypeObject *SingleRef = NULL;
PyTypeObject *CView = NULL;
PyTypeObject *CRepository = NULL;
PyTypeObject *CItem = NULL;
PyTypeObject *CDB = NULL;
PyTypeObject *CDBCursor = NULL;
PyTypeObject *CDBEnv = NULL;
PyTypeObject *CDBTxn = NULL;
PyTypeObject *CDBLock = NULL;

PyUUID_Check_fn PyUUID_Check = NULL;
PyUUID_Make16_fn PyUUID_Make16 = NULL;

PyObject *PyExc_DBError = NULL;
PyObject *PyExc_DBLockDeadlockError = NULL;
PyObject *PyExc_DBLockNotGrantedError = NULL;
PyObject *PyExc_DBAccessError = NULL;
PyObject *PyExc_DBInvalidArgError = NULL;
PyObject *PyExc_DBNoSpaceError = NULL;
PyObject *PyExc_DBNotFoundError = NULL;
PyObject *PyExc_DBNoSuchFileError = NULL;
PyObject *PyExc_DBPermissionsError = NULL;


PyObject *raiseDBError(int err)
{
    PyObject *tuple, *obj = NULL;

    switch (err) {
      case DB_LOCK_DEADLOCK:
        obj = PyExc_DBLockDeadlockError;
        break;
      case DB_LOCK_NOTGRANTED:
        obj = PyExc_DBLockNotGrantedError;
        break;
      case EACCES:
        obj = PyExc_DBAccessError;
        break;
      case EINVAL:
        obj = PyExc_DBInvalidArgError;
        break;
      case ENOSPC:
        obj = PyExc_DBNoSpaceError;
        break;
      case ENOENT:
        obj = PyExc_DBNoSuchFileError;
        break;
      case EPERM:
        obj = PyExc_DBPermissionsError;
        break;
      case ENOMEM:
        obj = PyExc_MemoryError;
        break;
      case DB_NOTFOUND:
        obj = PyExc_DBNotFoundError;
        break;
      case DB_PYTHON_ERROR:
        return NULL;
      default:
        obj = PyExc_DBError;
        break;
    }

    tuple = Py_BuildValue("(is)", err, db_strerror(err));
    PyErr_SetObject(obj, tuple);
    Py_DECREF(tuple);

    return NULL;
}


static PyMethodDef c_funcs[] = {
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
    PyObject *m = Py_InitModule3("c", c_funcs, "C repository types module");

    _init_view(m);
    _init_repository(m);
    _init_container(m);
    _init_sequence(m);
    _init_db(m);
    _init_cursor(m);
    _init_env(m);
    _init_txn(m);
    _init_lock(m);

    PyExc_DBError = PyErr_NewException("chandlerdb.persistence.c.DBError",
                                       NULL, NULL);
    PyObject_SetAttrString(m, "DBError", PyExc_DBError);

    MAKE_EXC(m, DBLockDeadlockError, DBError);
    MAKE_EXC(m, DBLockNotGrantedError, DBError);
    MAKE_EXC(m, DBAccessError, DBError);
    MAKE_EXC(m, DBInvalidArgError, DBError);
    MAKE_EXC(m, DBNoSpaceError, DBError);
    MAKE_EXC(m, DBNotFoundError, DBError);
    MAKE_EXC(m, DBNoSuchFileError, DBError);
    MAKE_EXC(m, DBPermissionsError, DBError);

    PyModule_AddIntConstant(m, "DB_VERSION_MAJOR", DB_VERSION_MAJOR);
    PyModule_AddIntConstant(m, "DB_VERSION_MINOR", DB_VERSION_MINOR);
    PyModule_AddIntConstant(m, "DB_VERSION_PATCH", DB_VERSION_PATCH);

    m = PyImport_ImportModule("chandlerdb.util.c");
    LOAD_TYPE(m, SingleRef);
    LOAD_FN(m, PyUUID_Check);
    LOAD_FN(m, PyUUID_Make16);
    Py_DECREF(m);

    m = PyImport_ImportModule("chandlerdb.item.c");
    LOAD_TYPE(m, CItem);
    Py_DECREF(m);
}
