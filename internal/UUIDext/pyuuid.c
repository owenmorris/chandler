
#include <Python.h>
#include "uuid.h"


static PyObject *make(PyObject *self, PyObject *args)
{
    unsigned char uuid[16];
    unsigned char *text;
    unsigned int len = 0;

    PyArg_ParseTuple(args, "|s#", &text, &len);
    switch (len) {
      case 0:
        if (generate_uuid(uuid))
            return Py_BuildValue("");
        break;
      case 16:
      case 22:
      case 36:
        if (make_uuid(uuid, text, len))
            return Py_BuildValue("");
        break;
      default:
        return Py_BuildValue("");
    }

    return Py_BuildValue("s#", uuid, 16);
}

static PyObject *format16(PyObject *self, PyObject *args)
{
    unsigned char buf[36];
    unsigned char *uuid;
    unsigned int len = 0;

    PyArg_ParseTuple(args, "s#", &uuid, &len);
    if (len != 16)
        return Py_BuildValue("");

    format16_uuid(uuid, buf);

    return Py_BuildValue("s#", buf, sizeof(buf));
}

static PyObject *format64(PyObject *self, PyObject *args)
{
    unsigned char buf[22];
    unsigned char *uuid;
    unsigned int len = 0;

    PyArg_ParseTuple(args, "s#", &uuid, &len);
    if (len != 16)
        return Py_BuildValue("");

    format64_uuid(uuid, buf);

    return Py_BuildValue("s#", buf, sizeof(buf));
}

static PyObject *hash(PyObject *self, PyObject *args)
{
    unsigned char *uuid;
    unsigned int len = 0;

    PyArg_ParseTuple(args, "s#", &uuid, &len);
    if (len < 0)
        return Py_BuildValue("");

    return Py_BuildValue("l", hash_uuid(uuid, len));
}

static PyMethodDef methods[] = {
    { "make", (PyCFunction) make, METH_VARARGS,
      "make uuid" },
    { "toString", (PyCFunction) format16, METH_VARARGS,
      "format uuid in standard hexadecimal syntax" },
    { "to64String", (PyCFunction) format64, METH_VARARGS,
      "format uuid in abbreviated base 64 syntax" },
    { "hash", (PyCFunction) hash, METH_VARARGS,
      "hash 128 bit uuid down to 32 bits" },
    { NULL, NULL, 0, NULL }
};

void initUUIDext(void)
{
    Py_InitModule3("UUIDext", methods, "UUID generation utility");
}
