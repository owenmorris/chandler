
/*
 * An attribute descriptor type
 */

#include <Python.h>
#include "structmember.h"
#include "../item/item.h"

enum {
    VALUE    = 0x0001,
    REF      = 0x0002,
    REDIRECT = 0x0004,
    DICTMASK = 0x0007,
    REQUIRED = 0x0008,
    SIMPLE   = 0x0010,
    SINGLE   = 0x0020
};

typedef struct {
    PyObject_HEAD
    PyObject *name;
    PyObject *attrs;
} t_descriptor;



static void t_descriptor_dealloc(t_descriptor *self);
static PyObject *t_descriptor_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds);
static int t_descriptor_init(t_descriptor *self,
                             PyObject *args, PyObject *kwds);
static PyObject *t_descriptor___get__(t_descriptor *self, PyObject *args);
static PyObject *t_descriptor___set__(t_descriptor *self, PyObject *args);
static PyObject *countAccess(PyObject *self, t_item *item);

static long _lastAccess = 0L;
static PyObject *PyExc_StaleItemError;
static PyObject *_getRef_NAME;
static PyObject *getAttributeValue_NAME;
static PyObject *setAttributeValue_NAME;


static PyMemberDef t_descriptor_members[] = {
    { "name", T_OBJECT, offsetof(t_descriptor, name), READONLY,
      "attribute name" },
    { "attrs", T_OBJECT, offsetof(t_descriptor, attrs), READONLY,
      "kind/attribute lookup table" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_descriptor_methods[] = {
    { "__get__", (PyCFunction) t_descriptor___get__, METH_VARARGS,
      "descriptor __get__ method" },
    { "__set__", (PyCFunction) t_descriptor___set__, METH_VARARGS,
      "descriptor __set__ method" },
    { NULL, NULL, 0, NULL }
};

static PyMethodDef descriptor_funcs[] = {
    { "_countAccess", (PyCFunction) countAccess, METH_O,
      "last access stamper" },
    { NULL, NULL, 0, NULL }
};

static PyTypeObject DescriptorType = {
    PyObject_HEAD_INIT(NULL)
    0,                                          /* ob_size */
    "chandlerdb.schema.descriptor.CDescriptor", /* tp_name */
    sizeof(t_descriptor),                       /* tp_basicsize */
    0,                                          /* tp_itemsize */
    (destructor)t_descriptor_dealloc,           /* tp_dealloc */
    0,                                          /* tp_print */
    0,                                          /* tp_getattr */
    0,                                          /* tp_setattr */
    0,                                          /* tp_compare */
    0,                                          /* tp_repr */
    0,                                          /* tp_as_number */
    0,                                          /* tp_as_sequence */
    0,                                          /* tp_as_mapping */
    0,                                          /* tp_hash  */
    0,                                          /* tp_call */
    0,                                          /* tp_str */
    0,                                          /* tp_getattro */
    0,                                          /* tp_setattro */
    0,                                          /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   /* tp_flags */
    "attribute descriptor",                     /* tp_doc */
    0,                                          /* tp_traverse */
    0,                                          /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    t_descriptor_methods,                       /* tp_methods */
    t_descriptor_members,                       /* tp_members */
    0,                                          /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    0,                                          /* tp_descr_get */
    0,                                          /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    (initproc)t_descriptor_init,                /* tp_init */
    0,                                          /* tp_alloc */
    (newfunc)t_descriptor_new,                  /* tp_new */
};


static void t_descriptor_dealloc(t_descriptor *self)
{
    Py_XDECREF(self->name);
    Py_XDECREF(self->attrs);
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_descriptor_new(PyTypeObject *type,
                                  PyObject *args, PyObject *kwds)
{
    t_descriptor *self = (t_descriptor *) type->tp_alloc(type, 0);

    if (self)
    {
        self->name = NULL;
        self->attrs = NULL;
    }

    return (PyObject *) self;
}

static int t_descriptor_init(t_descriptor *self,
                             PyObject *args, PyObject *kwds)
{
    PyObject *name;

    if (!PyArg_ParseTuple(args, "O", &name))
        return -1;

    Py_INCREF(name);
    self->name = name;
    self->attrs = PyDict_New();

    return 0;
}

static PyObject *get_attrdict(PyObject *obj, int flags)
{
    switch (flags & DICTMASK) {
      case VALUE:
        return ((t_item *) obj)->values;
      case REF:
        return ((t_item *) obj)->references;
      case REDIRECT:
        return Py_None;
      default:
        return NULL;
    }
}

static PyObject *t_descriptor___get__(t_descriptor *self, PyObject *args)
{
    PyObject *obj, *owner;

    if (!PyArg_ParseTuple(args, "OO", &obj, &owner))
        return NULL;
    
    if (obj == Py_None)
    {
        PyErr_SetObject(PyExc_AttributeError, self->name);
        return NULL;
    }
    else if (((t_item *) obj)->status & STALE)
    {
        PyErr_SetObject(PyExc_StaleItemError, obj);
        return NULL;
    }
    else
    {
        PyObject *kind = ((t_item *) obj)->kind;

        if (kind != Py_None)
        {
            PyObject *uuid = ((t_item *) kind)->uuid;
            PyObject *tuple = PyDict_GetItem(self->attrs, uuid);

            if (tuple != NULL)
            {
                PyObject *attrID = PyTuple_GET_ITEM(tuple, 0);
                int flags = PyInt_AS_LONG(PyTuple_GET_ITEM(tuple, 1));
                PyObject *attrDict = get_attrdict(obj, flags);
                PyObject *value;
                int found = 0;

                if (attrDict != Py_None)
                {
                    if (flags & SIMPLE)
                    {
                        value = PyDict_GetItem(attrDict, self->name);
                        if (value != NULL)
                        {
                            Py_INCREF(value);
                            found = 1;
                        }
                    }
                    else if (flags & REF &&
                             PyDict_Contains(attrDict, self->name))
                    {
                        value = PyObject_CallMethodObjArgs(attrDict, _getRef_NAME, self->name, Py_None, attrID, NULL);
                        found = 1;
                    }
                }

                if (found)
                    ((t_item *) obj)->lastAccess = ++_lastAccess;
                else
                    value = PyObject_CallMethodObjArgs(obj, getAttributeValue_NAME, self->name, attrDict, attrID, NULL);

                return value;
            }
        }

        {
            PyObject *dict = PyObject_GetAttrString(obj, "__dict__");
            PyObject *value = PyDict_GetItem(dict, self->name);

            Py_DECREF(dict);

            if (value == NULL)
                PyErr_SetObject(PyExc_AttributeError, self->name);
            else
                Py_INCREF(value);

            return value;
        }
    }
}

static PyObject *t_descriptor___set__(t_descriptor *self, PyObject *args)
{
    PyObject *obj, *value;

    if (!PyArg_ParseTuple(args, "OO", &obj, &value))
        return NULL;
    
    if (obj == Py_None)
    {
        PyErr_SetObject(PyExc_AttributeError, self->name);
        return NULL;
    }
    else if (((t_item *) obj)->status & STALE)
    {
        PyErr_SetObject(PyExc_StaleItemError, obj);
        return NULL;
    }
    else
    {
        PyObject *kind = ((t_item *) obj)->kind;

        if (kind != Py_None)
        {
            PyObject *uuid = ((t_item *) kind)->uuid;
            PyObject *tuple = PyDict_GetItem(self->attrs, uuid);

            if (tuple != NULL)
            {
                PyObject *attrID = PyTuple_GET_ITEM(tuple, 0);
                int flags = PyInt_AS_LONG(PyTuple_GET_ITEM(tuple, 1));
                PyObject *attrDict = get_attrdict(obj, flags);

                if (attrDict != Py_None && flags & SIMPLE)
                {
                    PyObject *oldValue = PyDict_GetItem(attrDict, self->name);

                    if (oldValue && !PyObject_Compare(value, oldValue))
                        Py_RETURN_NONE;
                }

                PyObject_CallMethodObjArgs(obj, setAttributeValue_NAME, self->name, value, attrDict, attrID, Py_True, Py_False, NULL);

                Py_RETURN_NONE;
            }
        }

        {
            PyObject *dict = PyObject_GetAttrString(obj, "__dict__");

            PyDict_SetItem(dict, self->name, value);
            Py_DECREF(dict);

            Py_RETURN_NONE;
        }
    }
}

static PyObject *countAccess(PyObject *self, t_item *item)
{
    item->lastAccess = ++_lastAccess;
    Py_RETURN_NONE;
}

static void PyDict_SetItemString_Int(PyObject *dict, char *key, int value)
{
    PyObject *pyValue = PyInt_FromLong(value);

    PyDict_SetItemString(dict, key, pyValue);
    Py_DECREF(pyValue);
}

void initdescriptor(void)
{
    if (PyType_Ready(&DescriptorType) >= 0)
    {
        PyObject *m = Py_InitModule3("descriptor", descriptor_funcs,
                                     "attribute descriptor module");
        if (m)
        {
            PyObject *dict;

            Py_INCREF(&DescriptorType);
            PyModule_AddObject(m, "CDescriptor", (PyObject *) &DescriptorType);

            dict = DescriptorType.tp_dict;
            PyDict_SetItemString_Int(dict, "VALUE", VALUE);
            PyDict_SetItemString_Int(dict, "REF", REF);
            PyDict_SetItemString_Int(dict, "REDIRECT", REDIRECT);
            PyDict_SetItemString_Int(dict, "REQUIRED", REQUIRED);
            PyDict_SetItemString_Int(dict, "SIMPLE", SIMPLE);
            PyDict_SetItemString_Int(dict, "SINGLE", SINGLE);

            m = PyImport_ImportModule("chandlerdb.item.ItemError");
            PyExc_StaleItemError = PyObject_GetAttrString(m, "StaleItemError");
            Py_DECREF(m);

            _getRef_NAME = PyString_FromString("_getRef");
            getAttributeValue_NAME = PyString_FromString("getAttributeValue");
            setAttributeValue_NAME = PyString_FromString("setAttributeValue");
        }
    }
}
