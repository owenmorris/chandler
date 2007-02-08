/*
 *  Copyright (c) 2007 Open Source Applications Foundation
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

#define FUSE_USE_VERSION 26

#include <fuse.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>

static PyObject *_mount_NAME;
static PyObject *start_NAME;
static PyObject *_fuse_NAME;
static PyObject *readdir_NAME;
static PyObject *stat_NAME;
static PyObject *statvfs_NAME;
static PyObject *open_NAME;
static PyObject *create_NAME;
static PyObject *read_NAME;
static PyObject *write_NAME;
static PyObject *close_NAME;
static PyObject *chown_NAME;
static PyObject *chmod_NAME;
static PyObject *utimes_NAME;
static PyObject *error_NAME;
static PyObject *error_STRING;
static PyObject *exc_info_NAME;


typedef struct {
    PyObject_HEAD
    PyObject *logger;
    PyObject *threadClass;
    PyObject *args;
    int argc;
    char **argv;
    int mounted;
} t_fuse;

static void t_fuse_dealloc(t_fuse *self);
static PyObject *t_fuse_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_fuse_init(t_fuse *self, PyObject *args, PyObject *kwds);
static PyObject *t_fuse_mount(t_fuse *self, PyObject *args);
static PyObject *t_fuse__mount(t_fuse *self);

static PyMemberDef t_fuse_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_fuse_methods[] = {
    { "mount", (PyCFunction) t_fuse_mount, METH_VARARGS, NULL },
    { "_mount", (PyCFunction) t_fuse__mount, METH_NOARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_fuse_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject FUSEType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.fuse.c.FUSE",                  /* tp_name */
    sizeof(t_fuse),                            /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_fuse_dealloc,                /* tp_dealloc */
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
     Py_TPFLAGS_BASETYPE),                     /* tp_flags */
    "C FUSE type",                             /* tp_doc */
    0,                                         /* tp_traverse */
    0,                                         /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    0,                                         /* tp_iter */
    0,                                         /* tp_iternext */
    t_fuse_methods,                            /* tp_methods */
    t_fuse_members,                            /* tp_members */
    t_fuse_properties,                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_fuse_init,                     /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_fuse_new,                       /* tp_new */
};


static void t_fuse_dealloc(t_fuse *self)
{
    if (self->argv)
    {
        free(self->argv);
        self->argv = NULL;
    }

    Py_XDECREF(self->threadClass);
    Py_XDECREF(self->args);

    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_fuse_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_fuse *self = (t_fuse *) type->tp_alloc(type, 0);

    return (PyObject *) self;
}

static int t_fuse_init(t_fuse *self, PyObject *args, PyObject *kwds)
{
    PyObject *logger, *threadClass = (PyObject *) Thread;

    if (!PyArg_ParseTuple(args, "O|O", &logger, &threadClass))
        return -1;

    if (!PyCallable_Check(threadClass))
    {
        PyErr_SetObject(PyExc_TypeError, threadClass);
        return -1;
    }

    Py_INCREF(logger);
    Py_XDECREF(self->logger);
    self->logger = logger;

    Py_INCREF(threadClass);
    Py_XDECREF(self->threadClass);
    self->threadClass = threadClass;

    return 0;
}

static PyObject *t_fuse_mount(t_fuse *self, PyObject *args)
{
    int argCount = PyTuple_GET_SIZE(args);
    PyObject *method, *thread, *result;
    int i, argc;
    char **argv;

    if (self->mounted)
    {
        PyErr_SetString(PyExc_ValueError, "is currently mounted");
        return NULL;
    }

    for (i = 0; i < argCount; i++) {
        PyObject *arg = PyTuple_GET_ITEM(args, i);

        if (!PyString_CheckExact(arg))
        {
            PyErr_SetObject(PyExc_TypeError, arg);
            return NULL;
        }
    }

    Py_INCREF(args);
    Py_XDECREF(self->args);
    self->args = args;

    argc = argCount + 3;
    argv = calloc(argc, sizeof(char *));
    if (!argv)
    {
        PyErr_SetNone(PyExc_MemoryError);
        return NULL;
    }

    argv[0] = Py_GetProgramFullPath();
    argv[1] = "-f";
    argv[2] = "-s";

    for (i = 0; i < argCount; i++)
        argv[i + 3] = PyString_AsString(PyTuple_GET_ITEM(args, i));

    self->argc = argc;
    self->argv = argv;

    method = PyObject_GetAttr((PyObject *) self, _mount_NAME);
    args = PyTuple_Pack(3, Py_None, method, _fuse_NAME);
    Py_DECREF(method);

    thread = PyObject_Call(self->threadClass, args, NULL);
    if (!thread)
        return NULL;

    result = PyObject_CallMethodObjArgs(thread, start_NAME, NULL);
    if (!result)
    {
        Py_DECREF(thread);
        return NULL;
    }

    Py_DECREF(result);
    return thread;
}

static t_fuse *_t_fuse_getself(void)
{
    PyObject *locals, *self;

    locals = PyThreadState_GetDict();
    if (!locals)
    {
        PyErr_SetString(PyExc_RuntimeError, "Could not get thread state dict");
        return NULL;
    }

    self = PyDict_GetItem(locals, _fuse_NAME);
    if (!self)
    {
        PyErr_SetString(PyExc_RuntimeError, "Could not get thread FUSE self");
        return NULL;
    }

    if (!PyObject_TypeCheck(self, &FUSEType))
    {
        PyErr_SetString(PyExc_TypeError, "Thread FUSE self not of type FUSE");
        return NULL;
    }

    return (t_fuse *) self;
}

static unsigned long long _uint64(PyObject *obj)
{
    PyObject *longObj = PyNumber_Long(obj);

    if (longObj)
    {
        unsigned long long i64 = PyLong_AsUnsignedLongLongMask(longObj);

        Py_DECREF(longObj);
        return i64;
    }
    else
        PyErr_Clear();

    return 0;
}

static unsigned long _uint32(PyObject *obj)
{
    PyObject *longObj = PyNumber_Long(obj);

    if (longObj)
    {
        unsigned long i32 = PyLong_AsUnsignedLongMask(longObj);

        Py_DECREF(longObj);
        return i32;
    }
    else
        PyErr_Clear();

    return 0;
}

static int _t_fuse_error(t_fuse *self, PyObject *name)
{
    PyObject *type, *value, *tb;

    PyErr_Fetch(&type, &value, &tb);
    if (type && value && tb)
    {
        PyObject *method = PyObject_GetAttr(self->logger, error_NAME);

        if (method)
        {
            PyObject *exc_info = PyTuple_Pack(3, type, value, tb);
            PyObject *args = PyTuple_Pack(2, error_STRING, name);
            PyObject *kwds = PyDict_New();
            PyObject *result;

            PyDict_SetItem(kwds, exc_info_NAME, exc_info);
            result = PyObject_Call(method, args, kwds);

            Py_DECREF(method);
            Py_DECREF(exc_info);
            Py_DECREF(args);
            Py_DECREF(kwds);

            PyErr_Clear();
            Py_CLEAR(result);
        }

        Py_DECREF(type);
        Py_DECREF(value);
        Py_DECREF(tb);

        return 0;
    }

    Py_XDECREF(type);
    Py_XDECREF(value);
    Py_XDECREF(tb);

    return -1;
}

static int _t_fuse_getattr(const char *path, struct stat *stbuf)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, stat_NAME))
    {
        PyGILState_Release(state);
        return -ENOSYS;
    }

    py_path = PyString_FromString(path + 1);
    result = PyObject_CallMethodObjArgs((PyObject *) self, stat_NAME,
                                        py_path, NULL);
    Py_DECREF(py_path);

    if (!result)
    {
        _t_fuse_error(self, stat_NAME);
        err = -ENOENT;
    }
    else
    {
        memset(stbuf, 0, sizeof(struct stat));
        
        if (result == Py_None)
            err = -ENOENT;
        else if (PySequence_Check(result))
        {
            PyObject *seq = PySequence_Fast(result, "");
            int size = PySequence_Fast_GET_SIZE(seq);

            if (size > 0)
                stbuf->st_mode = _uint64(PySequence_Fast_GET_ITEM(result, 0));
            if (size > 1)
                stbuf->st_ino = _uint64(PySequence_Fast_GET_ITEM(result, 1));
            if (size > 2)
                stbuf->st_dev = _uint64(PySequence_Fast_GET_ITEM(result, 2));
            if (size > 3)
                stbuf->st_nlink = _uint64(PySequence_Fast_GET_ITEM(result, 3));
            if (size > 4)
                stbuf->st_uid = _uint64(PySequence_Fast_GET_ITEM(result, 4));
            if (size > 5)
                stbuf->st_gid = _uint64(PySequence_Fast_GET_ITEM(result, 5));
            if (size > 6)
                stbuf->st_size = _uint64(PySequence_Fast_GET_ITEM(result, 6));
            if (size > 7)
                stbuf->st_atime = _uint64(PySequence_Fast_GET_ITEM(result, 7));
            if (size > 8)
                stbuf->st_mtime = _uint64(PySequence_Fast_GET_ITEM(result, 8));
            if (size > 9)
                stbuf->st_ctime = _uint64(PySequence_Fast_GET_ITEM(result, 9));

            Py_DECREF(seq);
        }

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_fgetattr(const char *path, struct stat *stbuf,
                            struct fuse_file_info *fi)
{
    return _t_fuse_getattr(path, stbuf);
}


static int _t_fuse_statfs(const char *path, struct statvfs *stbuf)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, statvfs_NAME))
    {
        PyGILState_Release(state);
        return -ENOSYS;
    }

    py_path = PyString_FromString(path + 1);
    result = PyObject_CallMethodObjArgs((PyObject *) self, statvfs_NAME,
                                        py_path, NULL);
    Py_DECREF(py_path);

    if (!result)
    {
        _t_fuse_error(self, statvfs_NAME);
        err = -ENOENT;
    }
    else
    {
        memset(stbuf, 0, sizeof(struct statvfs));
        
        if (result == Py_None)
            err = -ENOENT;
        else if (PySequence_Check(result))
        {
            PyObject *seq = PySequence_Fast(result, "");
            int size = PySequence_Fast_GET_SIZE(seq);

            if (size > 0)
                stbuf->f_bsize = _uint64(PySequence_Fast_GET_ITEM(result, 0));
            if (size > 1)
                stbuf->f_frsize = _uint64(PySequence_Fast_GET_ITEM(result, 1));
            if (size > 2)
                stbuf->f_blocks = _uint64(PySequence_Fast_GET_ITEM(result, 2));
            if (size > 3)
                stbuf->f_bfree = _uint64(PySequence_Fast_GET_ITEM(result, 3));
            if (size > 4)
                stbuf->f_bavail = _uint64(PySequence_Fast_GET_ITEM(result, 4));
            if (size > 5)
                stbuf->f_files = _uint64(PySequence_Fast_GET_ITEM(result, 5));
            if (size > 6)
                stbuf->f_ffree = _uint64(PySequence_Fast_GET_ITEM(result, 6));
            if (size > 7)
                stbuf->f_favail = _uint64(PySequence_Fast_GET_ITEM(result, 7));
            if (size > 8)
                stbuf->f_flag = _uint64(PySequence_Fast_GET_ITEM(result, 8));
            if (size > 9)
                stbuf->f_namemax = _uint64(PySequence_Fast_GET_ITEM(result, 9));

            Py_DECREF(seq);
        }

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_readdir(const char *path, void *buf, fuse_fill_dir_t filler,
                           off_t offset, struct fuse_file_info *fi)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, readdir_NAME))
    {
        PyGILState_Release(state);
        return -ENOSYS;
    }

    py_path = PyString_FromString(path + 1);
    result = PyObject_CallMethodObjArgs((PyObject *) self, readdir_NAME,
                                        py_path, NULL);
    Py_DECREF(py_path);

    if (!result)
    {
        _t_fuse_error(self, readdir_NAME);
        err = -ENOENT;
    }
    else
    {
        if (PySequence_Check(result))
        {
            int i = 0, len = PySequence_Size(result);

            filler(buf, ".", NULL, 0);
            filler(buf, "..", NULL, 0);

            while (i < len) {
                PyObject *name = PySequence_GetItem(result, i++);

                if (name)
                {
                    PyObject *str = PyObject_Str(name);

                    if (str)
                    {
                        filler(buf, PyString_AsString(str), NULL, 0);
                        Py_DECREF(str);
                    }

                    Py_DECREF(name);
                }
            }
        }
        else
            filler(buf, "(result not a sequence)", NULL, 0);

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_open(const char *path, struct fuse_file_info *fi)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *py_flags, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, open_NAME))
    {
        PyGILState_Release(state);
        return -ENOSYS;
    }

    py_path = PyString_FromString(path + 1);
    py_flags = PyInt_FromLong(fi->flags);
    result = PyObject_CallMethodObjArgs((PyObject *) self, open_NAME,
                                        py_path, py_flags, NULL);
    Py_DECREF(py_path);
    Py_DECREF(py_flags);

    if (!result)
    {
        _t_fuse_error(self, open_NAME);
        err = -EACCES;
    }
    else
    {
        if (!PyObject_IsTrue(result))
            err = -EACCES;

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_create(const char *path, mode_t mode,
                          struct fuse_file_info *fi)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *py_mode, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, create_NAME))
    {
        PyGILState_Release(state);
        return -ENOSYS;
    }

    py_path = PyString_FromString(path + 1);
    py_mode = PyInt_FromLong(mode);
    result = PyObject_CallMethodObjArgs((PyObject *) self, create_NAME,
                                        py_path, py_mode, NULL);
    Py_DECREF(py_path);
    Py_DECREF(py_mode);

    if (!result)
    {
        _t_fuse_error(self, create_NAME);
        err = -EACCES;
    }
    else
    {
        if (!PyObject_IsTrue(result))
            err = -EACCES;

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_read(const char *path, char *buf, size_t size, off_t offset,
                        struct fuse_file_info *fi)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *py_size, *py_offset, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, read_NAME))
    {
        PyGILState_Release(state);
        return -ENOSYS;
    }

    py_path = PyString_FromString(path + 1);
    py_size = PyLong_FromUnsignedLongLong(size);
    py_offset = PyLong_FromUnsignedLongLong(offset);
    result = PyObject_CallMethodObjArgs((PyObject *) self, read_NAME,
                                        py_path, py_size, py_offset, NULL);
    Py_DECREF(py_path);
    Py_DECREF(py_size);
    Py_DECREF(py_offset);

    if (!result)
    {
        _t_fuse_error(self, read_NAME);
        err = -ENOENT;
    }
    else
    {
        if (PyString_CheckExact(result))
        {
            Py_ssize_t len = PyString_GET_SIZE(result);

            if (len > size)
                len = size;

            memcpy(buf, PyString_AS_STRING(result), len);
            Py_DECREF(result);

            err = len;
        }
        else
        {
            Py_DECREF(result);
            err = 0;
        }
    }

    PyErr_Clear();
    PyGILState_Release(state);
    
    return err;
}


static int _t_fuse_write(const char *path, const char *buf,
                         size_t size, off_t offset,
                         struct fuse_file_info *fi)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *py_offset, *py_data, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, write_NAME))
    {
        PyGILState_Release(state);
        return -ENOSYS;
    }

    py_data = PyString_FromStringAndSize(buf, size);
    if (!py_data)
    {
        PyGILState_Release(state);
        return -EFBIG;
    }

    py_path = PyString_FromString(path + 1);
    py_offset = PyLong_FromUnsignedLongLong(offset);
    result = PyObject_CallMethodObjArgs((PyObject *) self, write_NAME,
                                        py_path, py_data, py_offset, NULL);
    Py_DECREF(py_data);
    Py_DECREF(py_path);
    Py_DECREF(py_offset);

    if (!result)
    {
        _t_fuse_error(self, write_NAME);
        err = -ENOENT;
    }
    else
    {
        err = _uint32(result);
        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);
    
    return err;
}


static int _t_fuse_release(const char *path, struct fuse_file_info *fi)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, close_NAME))
    {
        PyGILState_Release(state);
        return 0;
    }

    py_path = PyString_FromString(path + 1);
    result = PyObject_CallMethodObjArgs((PyObject *) self, close_NAME,
                                        py_path, NULL);
    Py_DECREF(py_path);

    if (!result)
    {
        _t_fuse_error(self, close_NAME);
        err = -ENOENT;
    }
    else
    {
        if (!PyObject_IsTrue(result))
            err = -ENOENT;

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_chown(const char *path, uid_t uid, gid_t gid)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *py_uid, *py_gid, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, chown_NAME))
    {
        PyGILState_Release(state);
        return 0;
    }

    py_path = PyString_FromString(path + 1);
    py_uid = PyInt_FromLong(uid);
    py_gid = PyInt_FromLong(gid);
    result = PyObject_CallMethodObjArgs((PyObject *) self, chown_NAME,
                                        py_path, py_uid, py_gid, NULL);
    Py_DECREF(py_path);
    Py_DECREF(py_uid);
    Py_DECREF(py_gid);

    if (!result)
    {
        _t_fuse_error(self, chown_NAME);
        err = -ENOENT;
    }
    else
    {
        if (!PyObject_IsTrue(result))
            err = -ENOENT;

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_chmod(const char *path, mode_t mode)
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *py_mode, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, chmod_NAME))
    {
        PyGILState_Release(state);
        return 0;
    }

    py_path = PyString_FromString(path + 1);
    py_mode = PyInt_FromLong(mode);
    result = PyObject_CallMethodObjArgs((PyObject *) self, chmod_NAME,
                                        py_path, py_mode, NULL);
    Py_DECREF(py_path);
    Py_DECREF(py_mode);

    if (!result)
    {
        _t_fuse_error(self, chmod_NAME);
        err = -ENOENT;
    }
    else
    {
        if (!PyObject_IsTrue(result))
            err = -ENOENT;

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}


static int _t_fuse_utimens(const char *path, const struct timespec ts[2])
{
    PyGILState_STATE state = PyGILState_Ensure();
    t_fuse *self = _t_fuse_getself();
    PyObject *py_path, *py_atime, *py_mtime, *result;
    int err = 0;

    if (!self)
    {
        PyGILState_Release(state);
        return -ESRCH;
    }

    if (!PyObject_HasAttr((PyObject *) self, utimes_NAME))
    {
        PyGILState_Release(state);
        return 0;
    }

    py_path = PyString_FromString(path + 1);
    py_atime = PyFloat_FromDouble((double) ts[0].tv_sec +
                                  (double) ts[0].tv_nsec / 1e9);
    py_mtime = PyFloat_FromDouble((double) ts[1].tv_sec +
                                  (double) ts[1].tv_nsec / 1e9);
    result = PyObject_CallMethodObjArgs((PyObject *) self, utimes_NAME,
                                        py_path, py_atime, py_mtime, NULL);
    Py_DECREF(py_path);
    Py_DECREF(py_atime);
    Py_DECREF(py_mtime);

    if (!result)
    {
        _t_fuse_error(self, utimes_NAME);
        err = -ENOENT;
    }
    else
    {
        if (!PyObject_IsTrue(result))
            err = -ENOENT;

        Py_DECREF(result);
    }

    PyErr_Clear();
    PyGILState_Release(state);

    return err;
}

static struct fuse_operations t_fuse_ops = {
    .getattr    = _t_fuse_getattr,
    .fgetattr   = _t_fuse_fgetattr,
    .statfs     = _t_fuse_statfs,
    .readdir    = _t_fuse_readdir,
    .open       = _t_fuse_open,
    .create     = _t_fuse_create,
    .release    = _t_fuse_release,
    .read       = _t_fuse_read,
    .write      = _t_fuse_write,
    .chown      = _t_fuse_chown,
    .chmod      = _t_fuse_chmod,
    .utimens    = _t_fuse_utimens,
};

static PyObject *t_fuse__mount(t_fuse *self)
{
    if (self->argv)
    {
        PyObject *locals = PyThreadState_GetDict();

        if (!locals)
        {
            PyErr_SetString(PyExc_RuntimeError,
                            "Could not get thread state dict");
            return NULL;
        }

        PyDict_SetItem(locals, _fuse_NAME, (PyObject *) self);
        self->mounted = 1;

        Py_BEGIN_ALLOW_THREADS;
        fuse_main(self->argc, self->argv, &t_fuse_ops, NULL);
        Py_END_ALLOW_THREADS;

        self->mounted = 0;
        PyDict_DelItem(locals, _fuse_NAME);

        Py_RETURN_NONE;
    }
    
    PyErr_SetString(PyExc_ValueError, "argv is NULL");
    return NULL;
}
    

void _init_fuse(PyObject *m)
{
    if (PyType_Ready(&FUSEType) >= 0)
    {
        Py_INCREF(&FUSEType);
        PyModule_AddObject(m, "FUSE", (PyObject *) &FUSEType);

        _mount_NAME = PyString_FromString("_mount");
        start_NAME = PyString_FromString("start");
        _fuse_NAME = PyString_FromString("_fuse");
        readdir_NAME = PyString_FromString("readdir");
        stat_NAME = PyString_FromString("stat");
        statvfs_NAME = PyString_FromString("statvfs");
        open_NAME = PyString_FromString("open");
        create_NAME = PyString_FromString("create");
        close_NAME = PyString_FromString("close");
        read_NAME = PyString_FromString("read");
        write_NAME = PyString_FromString("write");
        chown_NAME = PyString_FromString("chown");
        chmod_NAME = PyString_FromString("chmod");
        utimes_NAME = PyString_FromString("utimes");
        error_NAME = PyString_FromString("error");
        error_STRING = PyString_FromString("%s: an error occurred");
        exc_info_NAME = PyString_FromString("exc_info");
    }
}
