
/*
 * An attribute descriptor type
 */

#include <Python.h>
#include "structmember.h"
#include "../item/item.h"

enum {
    VALUE        = 0x0001,
    REF          = 0x0002,
    REDIRECT     = 0x0004,
    REQUIRED     = 0x0008,
    PROCESS      = 0x0010,
    SINGLE       = 0x0020,
    LIST         = 0x0040,
    DICT         = 0x0080,
    SET          = 0x0100,
    ALIAS        = 0x0200,
    KIND         = 0x0400,
    ATTRDICT     = VALUE | REF | REDIRECT,
    CARDINALITY  = SINGLE | LIST | DICT | SET,
    COLLECTION   = LIST | DICT | SET,
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
static PyObject *t_descriptor___get__(t_descriptor *self,
                                      PyObject *obj, PyObject *type);
static int t_descriptor___set__(t_descriptor *self,
                                PyObject *obj, PyObject *value);
static int t_descriptor___delete__(t_descriptor *self, PyObject *args);
static PyObject *t_descriptor_getAttribute(t_descriptor *self, PyObject *kind);
static PyObject *t_descriptor_unregisterAttribute(t_descriptor *self,
                                                  PyObject *kind);
static PyObject *t_descriptor_registerAttribute(t_descriptor *self,
                                                PyObject *args);
static PyObject *t_descriptor_isValueRequired(t_descriptor *self,
                                              PyObject *item);
static PyObject *countAccess(PyObject *self, t_item *item);

static long _lastAccess = 0L;
static PyObject *PyExc_StaleItemError;

static PyObject *_getRef_NAME;
static PyObject *getAttributeValue_NAME;
static PyObject *setAttributeValue_NAME;
static PyObject *removeAttributeValue_NAME;
static PyObject *getFlags_NAME;
static PyObject *otherName_NAME;
static PyObject *cardinality_NAME;
static PyObject *redirectTo_NAME;
static PyObject *type_NAME;
static PyObject *required_NAME;
static PyObject *single_NAME;
static PyObject *list_NAME;
static PyObject *dict_NAME;
static PyObject *set_NAME;


static PyMemberDef t_descriptor_members[] = {
    { "name", T_OBJECT, offsetof(t_descriptor, name), READONLY,
      "attribute name" },
    { "attrs", T_OBJECT, offsetof(t_descriptor, attrs), READONLY,
      "kind/attribute lookup table" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_descriptor_methods[] = {
    { "getAttribute", (PyCFunction) t_descriptor_getAttribute, METH_O, "" },
    { "unregisterAttribute", (PyCFunction) t_descriptor_unregisterAttribute,
      METH_O, "" },
    { "registerAttribute", (PyCFunction) t_descriptor_registerAttribute,
      METH_VARARGS, "" },
    { "isValueRequired", (PyCFunction) t_descriptor_isValueRequired,
      METH_O, "" },
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
    (descrgetfunc)t_descriptor___get__,         /* tp_descr_get */
    (descrsetfunc)t_descriptor___set__,         /* tp_descr_set */
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
    switch (flags & ATTRDICT) {
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

static PyObject *t_descriptor___get__(t_descriptor *self,
                                      PyObject *obj, PyObject *type)
{
    if (obj == NULL || obj == Py_None)
    {
        Py_INCREF(self);
        return (PyObject *) self;
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
                    if (!(flags & PROCESS))
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

static int t_descriptor___set__(t_descriptor *self,
                                PyObject *obj, PyObject *value)
{
    if (obj == Py_None)
    {
        PyErr_SetObject(PyExc_AttributeError, self->name);
        return -1;
    }
    else if (((t_item *) obj)->status & STALE)
    {
        PyErr_SetObject(PyExc_StaleItemError, obj);
        return -1;
    }
    else if (value == NULL)
        return t_descriptor___delete__(self, obj);
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

                if (attrDict != Py_None)
                {
                    PyObject *oldValue = PyDict_GetItem(attrDict, self->name);

                    if (value == oldValue)
                        return 0;

                    if (flags & SINGLE && !(flags & (PROCESS | COLLECTION)) &&
                        oldValue && !PyObject_Compare(value, oldValue))
                        return 0;
                }

                value = PyObject_CallMethodObjArgs(obj, setAttributeValue_NAME, self->name, value, attrDict, attrID, Py_True, Py_False, NULL);

                if (!value)
                    return -1;
                    
                Py_DECREF(value);
                return 0;
            }
        }

        {
            PyObject *dict = PyObject_GetAttrString(obj, "__dict__");

            PyDict_SetItem(dict, self->name, value);
            Py_DECREF(dict);

            return 0;
        }
    }
}

static int t_descriptor___delete__(t_descriptor *self, PyObject *obj)
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
            PyObject *value = PyObject_CallMethodObjArgs(obj, removeAttributeValue_NAME, self->name, attrDict, attrID, NULL);

            if (!value)
                return -1;

            Py_DECREF(value);
            return 0;
        }
    }

    {
        PyObject *dict = PyObject_GetAttrString(obj, "__dict__");
        int err = PyDict_DelItem(dict, self->name);

        Py_DECREF(dict);
        if (err == 0)
            return 0;

        PyErr_SetObject(PyExc_AttributeError, self->name);
        return -1;
    }
}

static PyObject *t_descriptor_getAttribute(t_descriptor *self, PyObject *kind)
{
    PyObject *uuid = ((t_item *) kind)->uuid;
    PyObject *tuple = PyDict_GetItem(self->attrs, uuid);

    if (tuple != NULL)
    {
        Py_INCREF(tuple);
        return tuple;
    }

    PyErr_SetObject(PyExc_KeyError, uuid);
    return NULL;
}

static PyObject *t_descriptor_unregisterAttribute(t_descriptor *self,
                                                  PyObject *kind)
{
    PyObject *uuid = ((t_item *) kind)->uuid;
    int err = PyDict_DelItem(self->attrs, uuid);

    if (err == 0)
    {
        PyObject *value = PyDict_Size(self->attrs) == 0 ? Py_True : Py_False;

        Py_INCREF(value);
        return value;
    }

    PyErr_SetObject(PyExc_KeyError, uuid);
    return NULL;
}

static PyObject *t_descriptor_registerAttribute(t_descriptor *self,
                                                PyObject *args)
{
    PyObject *kind, *attribute;

    if (!PyArg_ParseTuple(args, "OO", &kind, &attribute))
        return NULL;
    else
    {
        PyObject *values = ((t_item *) attribute)->values;
        PyObject *cardinality = PyDict_GetItem(values, cardinality_NAME);
        int flags = 0;

        if (!cardinality)
            flags |= SINGLE;
        else if (!PyObject_Compare(cardinality, single_NAME))
            flags |= SINGLE;
        else if (!PyObject_Compare(cardinality, list_NAME))
            flags |= LIST;
        else if (!PyObject_Compare(cardinality, dict_NAME))
            flags |= DICT;
        else if (!PyObject_Compare(cardinality, set_NAME))
            flags |= SET;

        if (PyDict_GetItem(values, required_NAME) == Py_True)
            flags |= REQUIRED;

        if (PyDict_Contains(values, otherName_NAME))
        {
            if (flags & SINGLE)
                flags |= PROCESS;

            flags |= REF;
        }            
        else if (PyDict_Contains(values, redirectTo_NAME))
        {
            flags |= REDIRECT | PROCESS;
            flags &= ~CARDINALITY;
        }
        else
        {
            PyObject *references = ((t_item *) attribute)->references;

            if (PyDict_Contains(references, type_NAME))
            {
                PyObject *type = PyObject_CallMethodObjArgs(references, _getRef_NAME, type_NAME, Py_None, Py_None, NULL);

                if (type == NULL)
                    return NULL;

                if (type != Py_None)
                {
                    PyObject *typeFlags =
                        PyObject_CallMethodObjArgs(type, getFlags_NAME, NULL);

                    Py_DECREF(type);

                    if (typeFlags == NULL)
                        return NULL;

                    if (!PyInt_Check(typeFlags))
                    {
                        PyErr_SetObject(PyExc_TypeError, typeFlags);
                        Py_DECREF(typeFlags);

                        return NULL;
                    }

                    flags |= PyInt_AsLong(typeFlags);
                    Py_DECREF(typeFlags);
                }
                else
                    Py_DECREF(type);
            }
            else
                flags |= PROCESS;

            flags |= VALUE;
        }

        {
            PyObject *tuple = PyTuple_New(2);
            PyObject *key = ((t_item *) kind)->uuid;
            PyObject *uuid = ((t_item *) attribute)->uuid;

            PyTuple_SET_ITEM(tuple, 0, uuid); Py_INCREF(uuid);
            PyTuple_SET_ITEM(tuple, 1, PyInt_FromLong(flags));
            PyDict_SetItem(self->attrs, key, tuple);

            Py_RETURN_NONE;
        }
    }
}

static PyObject *t_descriptor_isValueRequired(t_descriptor *self,
                                              PyObject *item)
{
    PyObject *kind = ((t_item *) item)->kind;
    PyObject *uuid = ((t_item *) kind)->uuid;
    PyObject *tuple = PyDict_GetItem(self->attrs, uuid);

    if (tuple != NULL)
    {
        int flags = PyInt_AS_LONG(PyTuple_GET_ITEM(tuple, 1));
        PyObject *attrDict = get_attrdict(item, flags);
        PyObject *value;

        tuple = PyTuple_New(2);
        value = attrDict != Py_None && flags & REQUIRED ? Py_True : Py_False;

        PyTuple_SET_ITEM(tuple, 0, attrDict); Py_INCREF(attrDict);
        PyTuple_SET_ITEM(tuple, 1, value); Py_INCREF(value);

        return tuple;
    }
    else
    {
        tuple = PyTuple_New(2);
        PyTuple_SET_ITEM(tuple, 0, Py_None); Py_INCREF(Py_None);
        PyTuple_SET_ITEM(tuple, 1, Py_False); Py_INCREF(Py_False);
    
        return tuple;
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
            PyDict_SetItemString_Int(dict, "PROCESS", PROCESS);
            PyDict_SetItemString_Int(dict, "SINGLE", SINGLE);
            PyDict_SetItemString_Int(dict, "LIST", LIST);
            PyDict_SetItemString_Int(dict, "DICT", DICT);
            PyDict_SetItemString_Int(dict, "SET", SET);
            PyDict_SetItemString_Int(dict, "ALIAS", ALIAS);
            PyDict_SetItemString_Int(dict, "KIND", KIND);

            m = PyImport_ImportModule("chandlerdb.item.ItemError");
            PyExc_StaleItemError = PyObject_GetAttrString(m, "StaleItemError");
            Py_DECREF(m);

            _getRef_NAME = PyString_FromString("_getRef");
            getAttributeValue_NAME = PyString_FromString("getAttributeValue");
            setAttributeValue_NAME = PyString_FromString("setAttributeValue");
            removeAttributeValue_NAME = PyString_FromString("removeAttributeValue");
            getFlags_NAME = PyString_FromString("getFlags");
            otherName_NAME = PyString_FromString("otherName");
            cardinality_NAME = PyString_FromString("cardinality");
            redirectTo_NAME = PyString_FromString("redirectTo");
            type_NAME = PyString_FromString("type");
            required_NAME = PyString_FromString("required");
            single_NAME = PyString_FromString("single");
            list_NAME = PyString_FromString("list");
            dict_NAME = PyString_FromString("dict");
            set_NAME = PyString_FromString("set");
        }
    }
}
