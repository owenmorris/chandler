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
#include <windows.h>
#define UUID _UUID

#include "c.h"

#define LOCK_SH 0x01
#define LOCK_EX 0x02
#define LOCK_NB 0x04
#define LOCK_UN 0x08


PyObject *openHFILE(PyObject *self, PyObject *args)
{
    unsigned char *filename;
    int len;
    HANDLE hFile;

    PyArg_ParseTuple(args, "s#", &filename, &len);
    hFile = CreateFile(filename,
                       GENERIC_READ | GENERIC_WRITE,
                       FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                       NULL,
                       OPEN_ALWAYS,
                       FILE_FLAG_DELETE_ON_CLOSE,
                       0L);

    return PyInt_FromLong((long) hFile);
}

PyObject *closeHFILE(PyObject *self, PyObject *args)
{
    HANDLE hFile;
    
    PyArg_ParseTuple(args, "l", (long *) &hFile);
    return PyInt_FromLong(CloseHandle(hFile));
}

/* Locks don't upgrade or downgrade on Windows, therefore this function has
 * to be called with LOCK_UN in combination with a lock flag to fake
 * upgrading or downgrading of locks. See lock.py for posix version.
 */
PyObject *lockHFILE(PyObject *self, PyObject *args)
{
    DWORD flags = 0;
    HANDLE hFile;
    int mode;
    BOOL result;
    OVERLAPPED ov;

    PyArg_ParseTuple(args, "li", (long *) &hFile, &mode);

    if (mode & LOCK_UN)
    {
        memset(&ov, 0, sizeof(ov));
        result = UnlockFileEx(hFile, 0, 1, 0, &ov);
    }

    if (mode & ~LOCK_UN)
    {
        if (mode & LOCK_EX)
            flags |= LOCKFILE_EXCLUSIVE_LOCK;
        if (mode & LOCK_NB)
            flags |= LOCKFILE_FAIL_IMMEDIATELY;

        memset(&ov, 0, sizeof(ov));
        result = LockFileEx(hFile, flags, 0, 1, 0, &ov);
    }

    return PyBool_FromLong(result);
}

void _init_lock(PyObject *m)
{
    if (m)
    {
        PyModule_AddIntConstant(m, "LOCK_SH", LOCK_SH);
        PyModule_AddIntConstant(m, "LOCK_EX", LOCK_EX);
        PyModule_AddIntConstant(m, "LOCK_NB", LOCK_NB);
        PyModule_AddIntConstant(m, "LOCK_UN", LOCK_UN);
    }
}
