
/*
 * A UUID python type
 */

#include <Python.h>
#include "structmember.h"
#include "fns.h"
#include "uuid.h"

static void t_uuid_dealloc(t_uuid *self);
static PyObject *t_uuid_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_uuid_init(t_uuid *self, PyObject *args, PyObject *kwds);
static int t_uuid_hash(t_uuid *self);
static PyObject *t_uuid_str(t_uuid *self);
static PyObject *t_uuid_repr(t_uuid *self);
static int t_uuid_cmp(t_uuid *o1, t_uuid *o2);
static PyObject *t_uuid_richcmp(t_uuid *o1, t_uuid *o2, int opid);

static PyObject *format64(t_uuid *self);
static PyObject *hash(PyObject *self, PyObject *args);
static PyObject *combine(PyObject *self, PyObject *args);
static PyObject *_isUUID(PyObject *self);
static PyObject *_isItem(PyObject *self);
static PyObject *_isRefList(PyObject *self);


static PyMemberDef t_uuid_members[] = {
    { "_uuid", T_OBJECT, offsetof(t_uuid, uuid), READONLY, "UUID bytes" },
    { "_hash", T_INT, offsetof(t_uuid, hash), READONLY, "UUID hash" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_uuid_methods[] = {
    { "str16", (PyCFunction) t_uuid_str, METH_NOARGS,
      "format uuid in standard syntax" },
    { "str64", (PyCFunction) format64, METH_NOARGS,
      "format uuid in abbreviated base 64 syntax" },
    { "_isUUID", (PyCFunction) _isUUID, METH_NOARGS, "return True" },
    { "_isItem", (PyCFunction) _isItem, METH_NOARGS, "return False" },
    { "_isRefList", (PyCFunction) _isRefList, METH_NOARGS, "return False" },
    { NULL, NULL, 0, NULL }
};

static PyMethodDef uuid_funcs[] = {
    { "_hash", (PyCFunction) hash, METH_VARARGS, "hash bytes" },
    { "_combine", (PyCFunction) combine, METH_VARARGS, "combine two hashes" },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject UUIDType = {
    PyObject_HEAD_INIT(NULL)
    0,                           /* ob_size */
    "chandlerdb.util.uuid.UUID", /* tp_name */
    sizeof(t_uuid),              /* tp_basicsize */
    0,                           /* tp_itemsize */
    (destructor)t_uuid_dealloc,  /* tp_dealloc */
    0,                           /* tp_print */
    0,                           /* tp_getattr */
    0,                           /* tp_setattr */
    (cmpfunc)t_uuid_cmp,         /* tp_compare */
    (reprfunc)t_uuid_repr,       /* tp_repr */
    0,                           /* tp_as_number */
    0,                           /* tp_as_sequence */
    0,                           /* tp_as_mapping */
    (hashfunc)t_uuid_hash,       /* tp_hash  */
    0,                           /* tp_call */
    (reprfunc)t_uuid_str,        /* tp_str */
    0,                           /* tp_getattro */
    0,                           /* tp_setattro */
    0,                           /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,          /* tp_flags */
    "t_uuid objects",            /* tp_doc */
    0,                           /* tp_traverse */
    0,                           /* tp_clear */
    (richcmpfunc)t_uuid_richcmp, /* tp_richcompare */
    0,                           /* tp_weaklistoffset */
    0,                           /* tp_iter */
    0,                           /* tp_iternext */
    t_uuid_methods,              /* tp_methods */
    t_uuid_members,              /* tp_members */
    0,                           /* tp_getset */
    0,                           /* tp_base */
    0,                           /* tp_dict */
    0,                           /* tp_descr_get */
    0,                           /* tp_descr_set */
    0,                           /* tp_dictoffset */
    (initproc)t_uuid_init,       /* tp_init */
    0,                           /* tp_alloc */
    (newfunc)t_uuid_new,         /* tp_new */
};


static void t_uuid_dealloc(t_uuid *self)
{
    Py_XDECREF(self->uuid);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_uuid_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_uuid *self = (t_uuid *) type->tp_alloc(type, 0);

    if (self)
    {
        self->uuid = NULL;
        self->hash = 0;
    }

    return (PyObject *) self;
}

static int t_uuid_init(t_uuid *self, PyObject *args, PyObject *kwds)
{
    unsigned char uuid[16];
    unsigned int len = 0;
    char *text;

    if (!PyArg_ParseTuple(args, "|z#", &text, &len))
        return -1; 

    switch (len) {
      case 0:
        if (generate_uuid(uuid))
        {
            PyErr_SetString(PyExc_ValueError,
                            "an error occurred while generating new UUID");
            return -1;
        }
        break;
      case 16:
      case 22:
      case 36:
        if (make_uuid(uuid, text, len))
        {
            PyErr_SetString(PyExc_ValueError,
                            "an error occurred while parsing UUID string");
            return -1;
        }
        break;
      default:
        PyErr_SetString(PyExc_ValueError,
                        "uuid string is not 16, 22, or 36 characters long");
        return -1;
    }

    self->uuid = PyString_FromStringAndSize((char *) uuid, sizeof(uuid));
    self->hash = hash_bytes(uuid, sizeof(uuid));

    return 0;
}

static int t_uuid_hash(t_uuid *self)
{
    return self->hash;
}

static PyObject *t_uuid_str(t_uuid *self)
{
    unsigned char *uuid = (unsigned char *) PyString_AS_STRING(self->uuid);
    char buf[36];

    format16_uuid(uuid, buf);

    return PyString_FromStringAndSize(buf, sizeof(buf));
}

static PyObject *t_uuid_repr(t_uuid *self)
{
    unsigned char *uuid = (unsigned char *) PyString_AS_STRING(self->uuid);
    char buf[44];

    strcpy(buf, "<UUID: ");
    format16_uuid(uuid, buf + 7);
    buf[43] = '>';

    return PyString_FromStringAndSize(buf, sizeof(buf));
}

static int t_uuid_cmp(t_uuid *o1, t_uuid *o2)
{
    if (!PyObject_TypeCheck(o1, &UUIDType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) o1);
        return -1;
    }

    if (!PyObject_TypeCheck(o2, &UUIDType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) o2);
        return -1;
    }

    return PyObject_Compare(o1->uuid, o2->uuid);
}

static PyObject *t_uuid_richcmp(t_uuid *o1, t_uuid *o2, int opid)
{
    if (!PyObject_TypeCheck(o1, &UUIDType) ||
        !PyObject_TypeCheck(o2, &UUIDType))
    {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    return PyObject_RichCompare(o1->uuid, o2->uuid, opid);
}

static PyObject *format64(t_uuid *self)
{
    unsigned char *uuid = (unsigned char *) PyString_AS_STRING(self->uuid);
    char buf[22];

    format64_uuid(uuid, buf);

    return PyString_FromStringAndSize(buf, sizeof(buf));
}

static PyObject *hash(PyObject *self, PyObject *args)
{
    unsigned char *data;
    unsigned int len = 0;

    if (!PyArg_ParseTuple(args, "s#", &data, &len))
        return 0;

    return PyInt_FromLong(hash_bytes(data, len));
}

static PyObject *combine(PyObject *self, PyObject *args)
{
    unsigned long h0, h1;

    if (!PyArg_ParseTuple(args, "ll", &h0, &h1))
        return 0;

    return PyInt_FromLong(combine_longs(h0, h1));
}

static PyObject *_isUUID(PyObject *self)
{
    Py_RETURN_TRUE;
}

static PyObject *_isItem(PyObject *self)
{
    Py_RETURN_FALSE;
}

static PyObject *_isRefList(PyObject *self)
{
    Py_RETURN_FALSE;
}


int PyUUID_Check(PyObject *obj)
{
    return obj->ob_type == &UUIDType;
}

PyObject *PyUUID_Make16(PyObject *str16)
{
    t_uuid *uuid = (t_uuid *) PyObject_New(t_uuid, &UUIDType);
    
    /* steals reference */
    uuid->uuid = str16;
    uuid->hash = hash_bytes((unsigned char *) PyString_AS_STRING(str16), 16);

    return (PyObject *) uuid;
}


void inituuid(void)
{
    if (PyType_Ready(&UUIDType) >= 0)
    {
        PyObject *m = Py_InitModule3("uuid", uuid_funcs,
                                     "UUID generation utility");
        if (m)
        {
            PyObject *cobj;

            Py_INCREF(&UUIDType);
            PyModule_AddObject(m, "UUID", (PyObject *) &UUIDType);

            cobj = PyCObject_FromVoidPtr(PyUUID_Check, NULL);
            PyModule_AddObject(m, "PyUUID_Check", cobj);
            cobj = PyCObject_FromVoidPtr(PyUUID_Make16, NULL);
            PyModule_AddObject(m, "PyUUID_Make16", cobj);
        }
    }
}
