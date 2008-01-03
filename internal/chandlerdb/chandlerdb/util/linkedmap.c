/*
 *  Copyright (c) 2003-2008 Open Source Applications Foundation
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

static void t_link_dealloc(t_link *self);
static int t_link_traverse(t_link *self, visitproc visit, void *arg);
static int t_link_clear(t_link *self);
static PyObject *t_link_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_link_init(t_link *self, PyObject *args, PyObject *kwds);
static PyObject *t_link_repr(t_link *self);

static PyObject *t_link__copy_(t_link *self, PyObject *arg);

static PyObject *t_link__getPreviousKey(t_link *self, void *data);
static int _t_link_setPreviousKey(t_link *self,
                                  PyObject *previousKey, PyObject *key);
static int _t_link_setNextKey(t_link *self,
                              PyObject *nextKey, PyObject *key);
static int t_link__setPreviousKey(t_link *self, PyObject *value, void *data);
static PyObject *t_link__getNextKey(t_link *self, void *data);
static int t_link__setNextKey(t_link *self, PyObject *value, void *data);
static PyObject *t_link_getValue(t_link *self, void *data);
static int t_link_setValue(t_link *self, PyObject *arg, void *data);
static PyObject *t_link_getAlias(t_link *self, void *data);
static int t_link_setAlias(t_link *self, PyObject *arg, void *data);


static PyObject *t_lm_get(t_lm *self, PyObject *args);
static t_link *_t_lm__get(t_lm *self, PyObject *key, int load, int noError);
static PyObject *t_lm__get(t_lm *self, PyObject *args);
static int t_lm_dict_contains(t_lm *self, PyObject *key);
static PyObject *t_lm_dict_clear(t_lm *self, PyObject *args);

static PyObject *t_lm__getDict(t_lm *self, void *data);
static PyObject *t_lm__getAliases(t_lm *self, void *data);
static int t_lm__setAliases(t_lm *self, PyObject *arg, void *data);

static PyObject *t_lm__getFirstKey(t_lm *self, void *data);
static int t_lm___setFirstKey(t_lm *self, PyObject *arg, void *data);
static PyObject *t_lm__getLastKey(t_lm *self, void *data);
static int t_lm___setLastKey(t_lm *self, PyObject *arg, void *data);

static PyObject *_load_NAME;
static PyObject *linkChanged_NAME;
static PyObject *view_NAME;


static PyMemberDef t_link_members[] = {
    { "_value", T_OBJECT, offsetof(t_link, value), READONLY, "" },
    { "_otherKey", T_OBJECT, offsetof(t_link, otherKey), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_link_methods[] = {
    { "_copy_", (PyCFunction) t_link__copy_, METH_O, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_link_properties[] = {
    { "_previousKey",
      (getter) t_link__getPreviousKey,
      (setter) t_link__setPreviousKey,
      "", NULL },
    { "_nextKey",
      (getter) t_link__getNextKey,
      (setter) t_link__setNextKey,
      "", NULL },
    { "value",
      (getter) t_link_getValue,
      (setter) t_link_setValue,
      "", NULL },
    { "alias",
      (getter) t_link_getAlias,
      (setter) t_link_setAlias,
      "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};


static PyTypeObject LinkType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.util.c.CLink",        /* tp_name */
    sizeof(t_link),                   /* tp_basicsize */
    0,                                /* tp_itemsize */
    (destructor)t_link_dealloc,       /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    0,                                /* tp_compare */
    (reprfunc)t_link_repr,            /* tp_repr */
    0,                                /* tp_as_number */
    0,                                /* tp_as_sequence */
    0,                                /* tp_as_mapping */
    0,                                /* tp_hash  */
    0,                                /* tp_call */
    0,                                /* tp_str */
    0,                                /* tp_getattro */
    0,                                /* tp_setattro */
    0,                                /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),             /* tp_flags */
    "t_link objects",                 /* tp_doc */
    (traverseproc)t_link_traverse,    /* tp_traverse */
    (inquiry)t_link_clear,            /* tp_clear */
    0,                                /* tp_richcompare */
    0,                                /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    t_link_methods,                   /* tp_methods */
    t_link_members,                   /* tp_members */
    t_link_properties,                /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    (initproc)t_link_init,            /* tp_init */
    0,                                /* tp_alloc */
    (newfunc)t_link_new,              /* tp_new */
};


static void t_link_dealloc(t_link *self)
{
    t_link_clear(self);
    self->ob_type->tp_free((PyObject *) self);

    linkCount -= 1;
}

static int t_link_traverse(t_link *self, visitproc visit, void *arg)
{
    Py_VISIT(self->owner);
    Py_VISIT(self->previousKey);
    Py_VISIT(self->nextKey);
    Py_VISIT(self->value);
    Py_VISIT(self->alias);
    Py_VISIT(self->otherKey);

    return 0;
}

static int t_link_clear(t_link *self)
{
    Py_CLEAR(self->owner);
    Py_CLEAR(self->previousKey);
    Py_CLEAR(self->nextKey);
    Py_CLEAR(self->value);
    Py_CLEAR(self->alias);
    Py_CLEAR(self->otherKey);

    return 0;
}

static PyObject *t_link_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_link *self = (t_link *) type->tp_alloc(type, 0);

    if (self)
    {
        linkCount += 1;
        self->owner = NULL;
        self->previousKey = NULL;
        self->nextKey = NULL;
        self->value = NULL;
        self->alias = NULL;
        self->otherKey = NULL;
    }

    return (PyObject *) self;
}

static int _t_link_init(t_link *self,
                        PyObject *owner, PyObject *value,
                        PyObject *previousKey, PyObject *nextKey,
                        PyObject *alias, PyObject *otherKey)
{
    if (t_link_setValue(self, value, NULL) < 0)
        return -1;

    Py_INCREF(owner); Py_XDECREF(self->owner);
    self->owner = owner;

    Py_INCREF(previousKey); Py_XDECREF(self->previousKey);
    self->previousKey = previousKey;

    Py_INCREF(nextKey); Py_XDECREF(self->nextKey);
    self->nextKey = nextKey;

    Py_INCREF(alias); Py_XDECREF(self->alias);
    self->alias = alias;

    Py_INCREF(otherKey); Py_XDECREF(self->otherKey);
    self->otherKey = otherKey;

    return 0;
}

static int t_link_init(t_link *self, PyObject *args, PyObject *kwds)
{
    PyObject *owner, *value;
    PyObject *previousKey = Py_None, *nextKey = Py_None;
    PyObject *alias = Py_None, *otherKey = Py_None;

    if (!PyArg_ParseTuple(args, "OO|OOOO", &owner, &value,
                          &previousKey, &nextKey, &alias, &otherKey))
        return -1;
    else
        return _t_link_init(self, owner, value, previousKey, nextKey,
                            alias, otherKey);
}

static PyObject *t_link_repr(t_link *self)
{
    PyObject *value = self->value ? PyObject_Repr(self->value) : NULL;

    if (!value && PyErr_Occurred())
        return NULL;

    if (value)
    {
        PyObject *format = PyString_FromString("<link: %s>");
        PyObject *repr = PyString_Format(format, value);

        Py_DECREF(format);
        Py_XDECREF(value);

        return repr;
    }

    return PyString_FromString("<link: (null)>");
}

static PyObject *t_link__copy_(t_link *self, PyObject *arg)
{
    if (!PyObject_TypeCheck(arg, &LinkType))
    {
        PyErr_SetObject(PyExc_TypeError, arg);
        return NULL;
    }
    else
    {
        PyObject *obj;

        obj = ((t_link *) arg)->previousKey;
        Py_INCREF(obj); Py_XDECREF(self->previousKey);
        self->previousKey = obj;

        obj = ((t_link *) arg)->nextKey;
        Py_INCREF(obj); Py_XDECREF(self->nextKey);
        self->nextKey = obj;

        obj = ((t_link *) arg)->alias;
        Py_INCREF(obj); Py_XDECREF(self->alias);
        self->alias = obj;

        obj = ((t_link *) arg)->otherKey;
        Py_INCREF(obj); Py_XDECREF(self->otherKey);
        self->otherKey = obj;

        Py_RETURN_NONE;
    }
}

static int _t_link_linkChanged(t_link *self, PyObject *link, PyObject *key)
{
    PyObject *result =
        PyObject_CallMethodObjArgs(self->owner, linkChanged_NAME,
                                   link, key, NULL);
    if (!result)
        return -1;
    
    Py_DECREF(result);
    return 0;
}


/* _previousKey property */

static PyObject *t_link__getPreviousKey(t_link *self, void *data)
{
    PyObject *previousKey = self->previousKey;

    Py_INCREF(previousKey);
    return previousKey;
}

static int _t_link_setPreviousKey(t_link *self,
                                  PyObject *previousKey, PyObject *key)
{
    t_lm *owner = (t_lm *) self->owner;

    if (!previousKey)
        previousKey = Py_None;

    if (previousKey == Py_None)
    {
        t_lm___setFirstKey(owner, key, NULL);
        if (_t_link_linkChanged(self, owner->head, Py_None) < 0)
            return -1;
    }

    Py_INCREF(previousKey); Py_XDECREF(self->previousKey);
    self->previousKey = previousKey;

    if (_t_link_linkChanged(self, (PyObject *) self, key) < 0)
        return -1;
        
    return 0;
}

static int t_link__setPreviousKey(t_link *self, PyObject *value, void *data)
{
    PyObject *previousKey, *key;

    if (!PyArg_ParseTuple(value, "OO", &previousKey, &key))
        return -1;
    else
        return _t_link_setPreviousKey(self, previousKey, key);
}


/* _nextKey property */

static PyObject *t_link__getNextKey(t_link *self, void *data)
{
    PyObject *nextKey = self->nextKey;

    Py_INCREF(nextKey);
    return nextKey;
}

static int _t_link_setNextKey(t_link *self, PyObject *nextKey, PyObject *key)
{
    t_lm *owner = (t_lm *) self->owner;

    if (!nextKey)
        nextKey = Py_None;

    if (nextKey == Py_None)
    {
        t_lm___setLastKey(owner, key, NULL);
        if (_t_link_linkChanged(self, owner->head, Py_None) < 0)
            return -1;
    }

    Py_INCREF(nextKey); Py_XDECREF(self->nextKey);
    self->nextKey = nextKey;

    if (_t_link_linkChanged(self, (PyObject *) self, key) < 0)
        return -1;
        
    return 0;
}

static int t_link__setNextKey(t_link *self, PyObject *value, void *data)
{
    PyObject *nextKey, *key;

    if (!PyArg_ParseTuple(value, "OO", &nextKey, &key))
        return -1;
    else
        return _t_link_setNextKey(self, nextKey, key);
}


/* value property */

static PyObject *t_link_getValue(t_link *self, void *data)
{
    if (self->value)
        return PyObject_Call(self->value, Empty_TUPLE, NULL);

    Py_RETURN_NONE;
}

static int t_link_setValue(t_link *self, PyObject *value, void *data)
{
    if (value == Py_None)
        value = NULL;

    if (value && !value->ob_type->tp_call)
    {
        PyErr_SetString(PyExc_TypeError, "link value is not callable");
        return -1;
    }

    Py_XINCREF(value); Py_XDECREF(self->value);
    self->value = value;

    return 0;
}


/* alias property */

static PyObject *t_link_getAlias(t_link *self, void *data)
{
    PyObject *alias = self->alias;

    Py_INCREF(alias);
    return alias;
}

static int t_link_setAlias(t_link *self, PyObject *alias, void *data)
{
    if (!alias)
        alias = Py_None;

    Py_INCREF(alias); Py_XDECREF(self->alias);
    self->alias = alias;

    return 0;
}


static void t_lm_dealloc(t_lm *self);
static int t_lm_traverse(t_lm *self, visitproc visit, void *arg);
static int t_lm_clear(t_lm *self);
static PyObject *t_lm_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_lm_init(t_lm *self, PyObject *args, PyObject *kwds);

static Py_ssize_t t_lm_dict_length(t_lm *self);
static PyObject *t_lm_dict_get(t_lm *self, PyObject *key);
static int t_lm_dict_set(t_lm *self, PyObject *key, PyObject *value);

static PyObject *t_lm_previousKey(t_lm *self, PyObject *key);
static PyObject *t_lm_nextKey(t_lm *self, PyObject *key);
static PyObject *t_lm_isDeferred(t_lm *self);


static PyMemberDef t_lm_members[] = {
    { "_flags", T_UINT, offsetof(t_lm, flags), 0, "" },
    { "_count", T_UINT, offsetof(t_lm, count), 0, "" },
    { "_head", T_OBJECT, offsetof(t_lm, head), READONLY, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_lm_methods[] = {
    { "get", (PyCFunction) t_lm_get, METH_VARARGS, "" },
    { "_get", (PyCFunction) t_lm__get, METH_VARARGS, "" },
    { "clear", (PyCFunction) t_lm_dict_clear, METH_NOARGS, "" },
    { "firstKey", (PyCFunction) t_lm__getFirstKey, METH_NOARGS, "" },
    { "lastKey", (PyCFunction) t_lm__getLastKey, METH_NOARGS, "" },
    { "previousKey", (PyCFunction) t_lm_previousKey, METH_O, "" },
    { "nextKey", (PyCFunction) t_lm_nextKey, METH_O, "" },
    { "isDeferred", (PyCFunction) t_lm_isDeferred, METH_NOARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_lm_properties[] = {
    { "_dict",
      (getter) t_lm__getDict,
      NULL, "", NULL },
    { "_aliases",
      (getter) t_lm__getAliases,
      (setter) t_lm__setAliases,
      "", NULL },
    { "_firstKey",
      (getter) t_lm__getFirstKey,
      (setter) t_lm___setFirstKey,
      "", NULL },
    { "_lastKey",
      (getter) t_lm__getLastKey,
      (setter) t_lm___setLastKey,
      "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PySequenceMethods t_lm_as_sequence = {
    (lenfunc) t_lm_dict_length,       /* sq_length */
    0,                                /* sq_concat */
    0,                                /* sq_repeat */
    0,                                /* sq_item */
    0,                                /* sq_slice */
    0,                                /* sq_ass_item */
    0,                                /* sq_ass_slice */
    (objobjproc) t_lm_dict_contains,  /* sq_contains */
    0,                                /* sq_inplace_concat */
    0,                                /* sq_inplace_repeat */
};

static PyMappingMethods t_lm_as_mapping = {
    (lenfunc) t_lm_dict_length,
    (binaryfunc) t_lm_dict_get,
    (objobjargproc) t_lm_dict_set
};

static PyTypeObject LinkedMapType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.util.c.CLinkedMap",   /* tp_name */
    sizeof(t_lm),                     /* tp_basicsize */
    0,                                /* tp_itemsize */
    (destructor)t_lm_dealloc,         /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    0,                                /* tp_compare */
    0,                                /* tp_repr */
    0,                                /* tp_as_number */
    &t_lm_as_sequence,                /* tp_as_sequence */
    &t_lm_as_mapping,                 /* tp_as_mapping */
    0,                                /* tp_hash  */
    0,                                /* tp_call */
    0,                                /* tp_str */
    0,                                /* tp_getattro */
    0,                                /* tp_setattro */
    0,                                /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),             /* tp_flags */
    "t_lm objects",                   /* tp_doc */
    (traverseproc)t_lm_traverse,      /* tp_traverse */
    (inquiry)t_lm_clear,              /* tp_clear */
    0,                                /* tp_richcompare */
    0,                                /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    t_lm_methods,                     /* tp_methods */
    t_lm_members,                     /* tp_members */
    t_lm_properties,                  /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    (initproc)t_lm_init,              /* tp_init */
    0,                                /* tp_alloc */
    (newfunc)t_lm_new,                /* tp_new */
};


static void t_lm_dealloc(t_lm *self)
{
    t_lm_clear(self);
    self->persistentvalue.ob_type->tp_free((PyObject *) self);

    linkedMapCount -= 1;
}

static int t_lm_traverse(t_lm *self, visitproc visit, void *arg)
{
    Py_VISIT(self->dict);
    Py_VISIT(self->aliases);
    Py_VISIT(self->head);

    PersistentValue->tp_traverse((PyObject *) self, visit, arg);

    return 0;
}

static int t_lm_clear(t_lm *self)
{
    Py_CLEAR(self->dict);
    Py_CLEAR(self->aliases);
    Py_CLEAR(self->head);

    PersistentValue->tp_clear((PyObject *) self);

    return 0;
}

static PyObject *t_lm_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_lm *self = (t_lm *) type->tp_alloc(type, 0);

    if (self)
    {
        linkedMapCount += 1;
        self->dict = PyDict_New();
        self->aliases = Nil; Py_INCREF(Nil);
        self->flags = 0;
        self->count = 0;
    }

    return (PyObject *) self;
}

static int t_lm_init(t_lm *self, PyObject *args, PyObject *kwds)
{
    PyObject *view, *link;
    int flags = 0;

    if (!PyArg_ParseTuple(args, "O|i", &view, &flags))
        return -1;

    if (_t_persistentvalue_init((t_persistentvalue *) self, view) < 0)
        return -1;

    link = t_link_new(&LinkType, NULL, NULL);
    if (!link)
        return -1;

    if (_t_link_init((t_link *) link, (PyObject *) self, Py_None,
                     Py_None, Py_None, Py_None, Py_None) < 0)
    {
        Py_DECREF(link);
        return -1;
    }

    Py_XDECREF(self->head);
    self->head = link;

    self->flags |= flags;

    return 0;
}

static t_link *_t_lm__get(t_lm *self, PyObject *key, int load, int noError)
{
    PyObject *link = PyDict_GetItem(self->dict, key);

    if (link == NULL)
    {
        if (load && self->flags & LM_LOAD)
        {
            PyObject *loaded =
                PyObject_CallMethodObjArgs((PyObject *) self, _load_NAME,
                                           key, NULL);

            if (!loaded)
                return NULL;

            if (PyObject_IsTrue(loaded))
                link = PyDict_GetItem(self->dict, key);

            Py_DECREF(loaded);
        }

        if (link == NULL)
        {
            if (!noError)
                PyErr_SetObject(PyExc_KeyError, key);
            return NULL;
        }
    }

    if (!PyObject_TypeCheck(link, &LinkType))
    {
        PyErr_SetObject(PyExc_TypeError, link);
        return NULL;
    }

    return (t_link *) link;
}

static PyObject *t_lm__get(t_lm *self, PyObject *args)
{
    PyObject *key;
    int load = 1;
    int noError = 0;

    if (!PyArg_ParseTuple(args, "O|ii", &key, &load, &noError))
        return NULL;
    else
    {
        PyObject *link = (PyObject *) _t_lm__get(self, key, load, noError);

        if (!link)
        {
            if (noError)
                Py_RETURN_NONE;

            return NULL;
        }

        Py_INCREF(link);
        return link;
    }
}

/* as_mapping */

static Py_ssize_t t_lm_dict_length(t_lm *self)
{
    return self->count;
}

static PyObject *t_lm_dict_get(t_lm *self, PyObject *key)
{
    t_link *link = _t_lm__get(self, key, 1, 0);

    if (!link)
        return NULL;

    return t_link_getValue(link, NULL);
}

static int t_lm_dict_set(t_lm *self, PyObject *key, PyObject *value)
{
    if (value == NULL)
        return PyDict_DelItem(self->dict, key);
    else
    {
        if (!PyObject_TypeCheck(value, &LinkType))
        {
            PyErr_SetObject(PyExc_TypeError, value);
            return -1;
        }
        else
        {
            t_link *link = (t_link *) value;
            t_link *head = (t_link *) self->head;
            PyObject *previousKey = head->nextKey;

            if (previousKey != Py_None && PyObject_Compare(previousKey, key))
            {
                t_link *previous = _t_lm__get(self, previousKey, 1, 0);

                if (!previous)
                    return -1;
                if (_t_link_setNextKey(previous, key, previousKey) < 0)
                    return -1;
            }

            PyDict_SetItem(self->dict, key, value);
            self->count += 1;

            if (previousKey == Py_None || PyObject_Compare(previousKey, key))
            {
                if (_t_link_setPreviousKey(link, previousKey, key) < 0)
                    return -1;
            }

            if (_t_link_setNextKey(link, Py_None, key) < 0)
                return -1;

            if (link->alias != Py_None)
            {
                if (self->aliases == Nil)
                {
                    Py_DECREF(self->aliases);
                    self->aliases = PyDict_New();
                }

                PyDict_SetItem(self->aliases, link->alias, key);
            }

            return 0;
        }
    }
}


static PyObject *t_lm_get(t_lm *self, PyObject *args)
{
    PyObject *key, *defaultValue = Py_None;

    if (!PyArg_ParseTuple(args, "O|O", &key, &defaultValue))
        return NULL;
    else
    {
        PyObject *value = PyDict_GetItem(self->dict, key);

        if (!value)
            value = defaultValue;

        Py_INCREF(value);
        return value;
    }
}

static int t_lm_dict_contains(t_lm *self, PyObject *key)
{
    if (PyDict_Contains(self->dict, key))
        return 1;
    
    if (self->flags & LM_LOAD)
    {
        PyObject *loaded = PyObject_CallMethodObjArgs((PyObject *) self,
                                                      _load_NAME, key, NULL);
        if (loaded)
        {
            int result = PyObject_IsTrue(loaded);

            Py_DECREF(loaded);
            return result;
        }

        return -1;
    }
    
    return 0;
}

static PyObject *t_lm_dict_clear(t_lm *self, PyObject *args)
{
    PyDict_Clear(self->dict);
    if (self->aliases != Nil)
    {
        Py_DECREF(self->aliases);
        self->aliases = Nil; Py_INCREF(Nil);
    }

    t_lm___setFirstKey(self, Py_None, NULL);
    t_lm___setLastKey(self, Py_None, NULL);

    Py_RETURN_NONE;
}


static PyObject *t_lm_previousKey(t_lm *self, PyObject *key)
{
    t_link *link = _t_lm__get(self, key, 1, 0);

    if (!link)
        return NULL;
    else
    {
        PyObject *previousKey = link->previousKey;

        Py_INCREF(previousKey);
        return previousKey;
    }
}

static PyObject *t_lm_nextKey(t_lm *self, PyObject *key)
{
    t_link *link = _t_lm__get(self, key, 1, 0);

    if (!link)
        return NULL;
    else
    {
        PyObject *nextKey = link->nextKey;

        Py_INCREF(nextKey);
        return nextKey;
    }
}

static PyObject *t_lm_isDeferred(t_lm *self)
{
    if (self->flags & LM_DEFERRED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}


/* _dict property */

static PyObject *t_lm__getDict(t_lm *self, void *data)
{
    PyObject *dict = self->dict;

    Py_INCREF(dict);
    return dict;
}


/* _aliases property */

static PyObject *t_lm__getAliases(t_lm *self, void *data)
{
    PyObject *aliases = self->aliases;

    Py_INCREF(aliases);
    return aliases;
}

static int t_lm__setAliases(t_lm *self, PyObject *arg, void *data)
{
    if (!arg)
        arg = Py_None;

    if (self->aliases != arg)
    {
        Py_DECREF(self->aliases);
        self->aliases = arg; Py_INCREF(arg);
    }

    return 0;
}


/* _firstKey property */

static PyObject *t_lm__getFirstKey(t_lm *self, void *data)
{
    t_link *head = (t_link *) self->head;
    PyObject *key = head->previousKey;

    Py_INCREF(key);
    return key;
}

static int t_lm___setFirstKey(t_lm *self, PyObject *arg, void *data)
{
    t_link *head = (t_link *) self->head;

    if (!arg)
        arg = Py_None;

    Py_INCREF(arg); Py_XDECREF(head->previousKey);
    head->previousKey = arg;

    return 0;
}


/* _lastKey property */

static PyObject *t_lm__getLastKey(t_lm *self, void *data)
{
    t_link *head = (t_link *) self->head;
    PyObject *key = head->nextKey;

    Py_INCREF(key);
    return key;
}

static int t_lm___setLastKey(t_lm *self, PyObject *arg, void *data)
{
    t_link *head = (t_link *) self->head;

    if (!arg)
        arg = Py_None;

    Py_INCREF(arg); Py_XDECREF(head->nextKey);
    head->nextKey = arg;

    return 0;
}


void _init_linkedmap(PyObject *m)
{
    LinkedMapType.tp_base = PersistentValue;

    if (PyType_Ready(&LinkedMapType) >= 0 && PyType_Ready(&LinkType) >= 0)
    {
        if (m)
        {
            PyObject *dict = LinkedMapType.tp_dict;

            Py_INCREF(&LinkedMapType);
            PyModule_AddObject(m, "CLinkedMap", (PyObject *) &LinkedMapType);
            CLinkedMap = &LinkedMapType;

            PyDict_SetItemString_Int(dict, "NEW", LM_NEW);
            PyDict_SetItemString_Int(dict, "LOAD", LM_LOAD);
            PyDict_SetItemString_Int(dict, "MERGING", LM_MERGING);
            PyDict_SetItemString_Int(dict, "SETDIRTY", LM_SETDIRTY);
            PyDict_SetItemString_Int(dict, "READONLY", LM_READONLY);
            PyDict_SetItemString_Int(dict, "DEFERRED", LM_DEFERRED);

            Py_INCREF(&LinkType);
            PyModule_AddObject(m, "CLink", (PyObject *) &LinkType);
            CLink = &LinkType;

            _load_NAME = PyString_FromString("_load");
            linkChanged_NAME = PyString_FromString("linkChanged");
            view_NAME = PyString_FromString("view");
        }
    }
}
