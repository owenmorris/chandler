
#include <Python.h>
#include <windows.h>

#define LOCK_SH 0x01
#define LOCK_EX 0x02
#define LOCK_NB 0x04
#define LOCK_UN 0x08


static PyObject *openHFILE(PyObject *self, PyObject *args)
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
                       FILE_FLAG_DELETE_ON_CLOSE | FILE_FLAG_POSIX_SEMANTICS,
                       0L);

    return PyInt_FromLong((long) hFile);
}

static PyObject *closeHFILE(PyObject *self, PyObject *args)
{
    HANDLE hFile;
    
    PyArg_ParseTuple(args, "l", (long *) &hFile);
    return PyInt_FromLong(CloseHandle(hFile));
}

/* Locks don't upgrade or downgrade on Windows, therefore this function has
 * to be called with LOCK_UN in combination with a lock flag to fake
 * upgrading or downgrading of locks. See lock.py for posix version.
 */
static PyObject *lockHFILE(PyObject *self, PyObject *args)
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

static PyMethodDef methods[] = {
    { "open", (PyCFunction) openHFILE, METH_VARARGS,
      "open file" },
    { "close", (PyCFunction) closeHFILE, METH_VARARGS,
      "close file" },
    { "lock", (PyCFunction) lockHFILE, METH_VARARGS,
      "lock, unlock, upgrade or downgrade lock on file" },
    { NULL, NULL, 0, NULL }
};

void initlock(void)
{
    PyObject *module = Py_InitModule3("lock", methods, "windows file locking");
    PyObject *dict = PyModule_GetDict(module);

    PyDict_SetItemString(dict, "LOCK_SH", PyInt_FromLong(LOCK_SH));
    PyDict_SetItemString(dict, "LOCK_EX", PyInt_FromLong(LOCK_EX));
    PyDict_SetItemString(dict, "LOCK_NB", PyInt_FromLong(LOCK_NB));
    PyDict_SetItemString(dict, "LOCK_UN", PyInt_FromLong(LOCK_UN));
}
