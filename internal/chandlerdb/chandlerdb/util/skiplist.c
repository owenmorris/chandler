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


#include <time.h>
#include <stdlib.h>

#include <Python.h>
#include "structmember.h"

#include "c.h"

enum sl_flags {
    SL_INVALID = 0x0001,
};

static PyObject *get_NAME;
static PyObject *_keyChanged_NAME;
static PyObject *exact_NAME, *first_NAME, *last_NAME;


static void t_point_dealloc(t_point *self);
static int t_point_traverse(t_point *self, visitproc visit, void *arg);
static int t_point_clear(t_point *self);
static PyObject *t_point_new(PyTypeObject *type,
                             PyObject *args, PyObject *kwds);
static int t_point_init(t_point *self, PyObject *args, PyObject *kwds);
static PyObject *t_point_repr(t_point *self);

static PyObject *t_point_getPrevKey(t_point *self, void *data);
static int t_point_setPrevKey(t_point *self, PyObject *value, void *data);
static PyObject *t_point_getNextKey(t_point *self, void *data);
static int t_point_setNextKey(t_point *self, PyObject *value, void *data);

static PyMemberDef t_point_members[] = {
    { "_prevKey", T_OBJECT, offsetof(t_point, prevKey), 0, "" },
    { "_nextKey", T_OBJECT, offsetof(t_point, nextKey), 0, "" },
    { "dist", T_INT, offsetof(t_point, dist), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_point_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_point_properties[] = {
    { "prevKey",
      (getter) t_point_getPrevKey,
      (setter) t_point_setPrevKey,
      "", NULL },
    { "nextKey",
      (getter) t_point_getNextKey,
      (setter) t_point_setNextKey,
      "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};


static PyTypeObject PointType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.util.c.CPoint",       /* tp_name */
    sizeof(t_point),                  /* tp_basicsize */
    0,                                /* tp_itemsize */
    (destructor)t_point_dealloc,      /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    0,                                /* tp_compare */
    (reprfunc)t_point_repr,           /* tp_repr */
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
    "t_point objects",                /* tp_doc */
    (traverseproc)t_point_traverse,   /* tp_traverse */
    (inquiry)t_point_clear,           /* tp_clear */
    0,                                /* tp_richcompare */
    0,                                /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    t_point_methods,                  /* tp_methods */
    t_point_members,                  /* tp_members */
    t_point_properties,               /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    (initproc)t_point_init,           /* tp_init */
    0,                                /* tp_alloc */
    (newfunc)t_point_new,             /* tp_new */
};


static void t_point_dealloc(t_point *self)
{
    t_point_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_point_traverse(t_point *self, visitproc visit, void *arg)
{
    Py_VISIT(self->prevKey);
    Py_VISIT(self->nextKey);

    return 0;
}

static int t_point_clear(t_point *self)
{
    Py_CLEAR(self->prevKey);
    Py_CLEAR(self->nextKey);

    return 0;
}

static PyObject *t_point_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_point *self = (t_point *) type->tp_alloc(type, 0);

    if (self)
    {
        self->prevKey = NULL;
        self->nextKey = NULL;
        self->dist = 0;
    }

    return (PyObject *) self;
}

static int _t_point_init(t_point *self, int dist)
{
    self->dist = dist;

    Py_INCREF(Py_None); Py_XDECREF(self->prevKey);
    self->prevKey = Py_None;

    Py_INCREF(Py_None); Py_XDECREF(self->nextKey);
    self->nextKey = Py_None;

    return 0;
}

static int t_point_init(t_point *self, PyObject *args, PyObject *kwds)
{
    int dist;

    if (!PyArg_ParseTuple(args, "i", &dist))
        return -1;

    return _t_point_init(self, dist);
}

static PyObject *t_point_repr(t_point *self)
{
    PyObject *prev = PyObject_Repr(self->prevKey);
    PyObject *next = PyObject_Repr(self->nextKey);
    PyObject *repr = NULL;

    if (prev && next)
        repr = PyString_FromFormat("<point: %s, %s, %d>",
                                   PyString_AsString(prev),
                                   PyString_AsString(next),
                                   self->dist);
                                         
    Py_XDECREF(prev);
    Py_XDECREF(next);

    return repr;
}


/* prevKey property */

static PyObject *t_point_getPrevKey(t_point *self, void *data)
{
    PyObject *key = self->prevKey;

    Py_INCREF(key);
    return key;
}

static int t_point_setPrevKey(t_point *self, PyObject *value, void *data)
{
    if (!value)
        value = Py_None;

    Py_INCREF(value); Py_XDECREF(self->prevKey);
    self->prevKey = value;

    return 0;
}

/* nextKey property */

static PyObject *t_point_getNextKey(t_point *self, void *data)
{
    PyObject *key = self->nextKey;

    Py_INCREF(key);
    return key;
}

static int t_point_setNextKey(t_point *self, PyObject *value, void *data)
{
    if (!value)
        value = Py_None;

    Py_INCREF(value); Py_XDECREF(self->nextKey);
    self->nextKey = value;

    return 0;
}


static void t_node_dealloc(t_node *self);
static int t_node_traverse(t_node *self, visitproc visit, void *arg);
static int t_node_clear(t_node *self);
static PyObject *t_node_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_node_init(t_node *self, PyObject *args, PyObject *kwds);

static Py_ssize_t t_node_list_length(t_node *self);
static t_point *_t_node_list_get(t_node *self, Py_ssize_t i);
static PyObject *t_node_list_get(t_node *self, Py_ssize_t i);

static PyObject *t_node_getLevel(t_node *self, PyObject *arg);
static PyObject *t_node_getPoint(t_node *self, PyObject *arg);

static PyObject *t_node_setPrev(t_node *self, PyObject *arg);
static PyObject *t_node_setNext(t_node *self, PyObject *arg);
static int _t_node_check(PyObject *node);


static PyMemberDef t_node_members[] = {
    { "_levels", T_OBJECT, offsetof(t_node, levels), READONLY, "" },
    { "_entryValue", T_INT, offsetof(t_node, entryValue), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_node_methods[] = {
    { "getLevel", (PyCFunction) t_node_getLevel, METH_NOARGS, "" },
    { "getPoint", (PyCFunction) t_node_getPoint, METH_O, "" },
    { "setPrev", (PyCFunction) t_node_setPrev, METH_VARARGS, "" },
    { "setNext", (PyCFunction) t_node_setNext, METH_VARARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_node_properties[] = {
    { "level",
      (getter) t_node_getLevel,
      NULL,
      "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PySequenceMethods t_node_as_sequence = {
    (lenfunc)t_node_list_length,      /* sq_length */
    0,                                /* sq_concat */
    0,                                /* sq_repeat */
    (ssizeargfunc)t_node_list_get,    /* sq_item */
    0,                                /* sq_slice */
    0,                                /* sq_ass_item */
    0,                                /* sq_ass_slice */
    0,                                /* sq_contains */
    0,                                /* sq_inplace_concat */
    0,                                /* sq_inplace_repeat */
};

static PyTypeObject NodeType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.util.c.CNode",        /* tp_name */
    sizeof(t_node),                   /* tp_basicsize */
    0,                                /* tp_itemsize */
    (destructor)t_node_dealloc,       /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    0,                                /* tp_compare */
    0,                                /* tp_repr */
    0,                                /* tp_as_number */
    &t_node_as_sequence,              /* tp_as_sequence */
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
    "t_node objects",                 /* tp_doc */
    (traverseproc)t_node_traverse,    /* tp_traverse */
    (inquiry)t_node_clear,            /* tp_clear */
    0,                                /* tp_richcompare */
    0,                                /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    t_node_methods,                   /* tp_methods */
    t_node_members,                   /* tp_members */
    t_node_properties,                /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    (initproc)t_node_init,            /* tp_init */
    0,                                /* tp_alloc */
    (newfunc)t_node_new,              /* tp_new */
};


static void t_node_dealloc(t_node *self)
{
    t_node_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_node_traverse(t_node *self, visitproc visit, void *arg)
{
    Py_VISIT(self->levels);
    return 0;
}

static int t_node_clear(t_node *self)
{
    Py_CLEAR(self->levels);
    return 0;
}

static PyObject *t_node_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_node *self = (t_node *) type->tp_alloc(type, 0);

    if (self)
    {
        self->levels = NULL;
        self->entryValue = 0;
    }

    return (PyObject *) self;
}

static int _t_node_init(t_node *self, int level)
{
    PyObject *levels = PyList_New(level);
    int i;

    for (i = 0; i < level; i++) {
        PyObject *point = t_point_new(&PointType, NULL, NULL);

        _t_point_init((t_point *) point, 0);
        PyList_SET_ITEM(levels, i, point);
    }

    Py_XDECREF(self->levels);
    self->levels = levels;
    self->entryValue = 0;

    return 0;
}

static int t_node_init(t_node *self, PyObject *args, PyObject *kwds)
{
    int level;

    if (!PyArg_ParseTuple(args, "i", &level))
        return -1;
 
    return _t_node_init(self, level);
}


static PyObject *t_node_getLevel(t_node *self, PyObject *arg)
{
    return PyInt_FromLong(PyList_GET_SIZE(self->levels));
}

static PyObject *t_node_getPoint(t_node *self, PyObject *arg)
{
    if (!PyInt_Check(arg))
    {
        PyErr_SetObject(PyExc_TypeError, arg);
        return NULL;
    }

    return t_node_list_get(self, PyInt_AsLong(arg));
}


/* node as 1-based sequence */

static Py_ssize_t t_node_list_length(t_node *self)
{
    return PyList_GET_SIZE(self->levels);
}

static t_point *_t_node_list_get(t_node *self, Py_ssize_t i)
{
    if (i > 0 && i <= PyList_GET_SIZE(self->levels))
    {
        PyObject *point = PyList_GET_ITEM(self->levels, i - 1);

        if (!point)
            return NULL;
        if (!PyObject_TypeCheck(point, CPoint))
        {
            PyErr_SetObject(PyExc_TypeError, point);
            return NULL;
        }

        return (t_point *) point;
    }

    PyErr_Format(PyExc_IndexError, "index out of range: %d", (int) i);
    return NULL;
}

static PyObject *t_node_list_get(t_node *self, Py_ssize_t i)
{
    PyObject *point = (PyObject *) _t_node_list_get(self, i);

    if (!point)
        return NULL;

    Py_INCREF(point);
    return point;
}


static int _t_node_setPrev(t_node *self, int level,
                           PyObject *prevKey, PyObject *key, t_sl *skipList)
{
    t_point *point;

    if (prevKey == Py_None)
    {
        point = _t_node_list_get((t_node *) skipList->head, level);
        if (!point)
            return -1;

        t_point_setNextKey(point, key, NULL);
    }

    point = _t_node_list_get(self, level);
    if (!point)
        return -1;

    t_point_setPrevKey(point, prevKey, NULL);

    return 0;
}

static PyObject *t_node_setPrev(t_node *self, PyObject *args)
{
    PyObject *prevKey, *key, *skipList;
    int level;

    if (!PyArg_ParseTuple(args, "iOOO", &level, &prevKey, &key, &skipList))
        return NULL;

    if (!PyObject_TypeCheck(skipList, SkipList))
    {
        PyErr_SetObject(PyExc_TypeError, skipList);
        return NULL;
    }

    if (_t_node_setPrev(self, level, prevKey, key, (t_sl *) skipList) < 0)
        return NULL;

    Py_RETURN_NONE;
}


static int _t_node_setNext(t_node *self, int level,
                           PyObject *nextKey, PyObject *key, t_sl *skipList,
                           int delta)
{
    t_point *point;

    if (nextKey == Py_None)
    {
        point = _t_node_list_get((t_node *) skipList->tail, level);
        if (!point)
            return -1;

        t_point_setPrevKey(point, key, NULL);
    }

    point = _t_node_list_get(self, level);
    if (!point)
        return -1;

    t_point_setNextKey(point, nextKey, NULL);
    point->dist += delta;

    return 0;
}

static PyObject *t_node_setNext(t_node *self, PyObject *args)
{
    PyObject *nextKey, *key, *skipList;
    int level, delta;

    if (!PyArg_ParseTuple(args, "iOOOi",
                          &level, &nextKey, &key, &skipList, &delta))
        return NULL;

    if (!PyObject_TypeCheck(skipList, SkipList))
    {
        PyErr_SetObject(PyExc_TypeError, skipList);
        return NULL;
    }

    if (_t_node_setNext(self, level, nextKey, key, (t_sl *) skipList,
                        delta) < 0)
        return NULL;

    Py_RETURN_NONE;
}


static void t_sl_dealloc(t_sl *self);
static int t_sl_traverse(t_sl *self, visitproc visit, void *arg);
static int t_sl_clear(t_sl *self);
static PyObject *t_sl_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_sl_init(t_sl *self, PyObject *args, PyObject *kwds);
static PyObject *t_sl__clear_(t_sl *self, PyObject *arg);
static PyObject *t_sl_getMap(t_sl *self, PyObject *arg);
static PyObject *t_sl_getLevel(t_sl *self, PyObject *arg);
static Py_ssize_t t_sl_list_length(t_sl *self);
static PyObject *t_sl_list_get(t_sl *self, Py_ssize_t i);
static PyObject *t_sl_position(t_sl *self, PyObject *key);
/*
static PyObject *t_sl__p0(t_sl *self, PyObject *args);
static PyObject *t_sl__p1(t_sl *self, PyObject *args);
static PyObject *t_sl__p2(t_sl *self, PyObject *args);
static PyObject *t_sl__p3(t_sl *self, PyObject *args);
static PyObject *t_sl__p4(t_sl *self, PyObject *args);
static PyObject *t_sl__p5(t_sl *self, PyObject *args);
*/
static PyObject *t_sl_insert(t_sl *self, PyObject *args);
static PyObject *t_sl_move(t_sl *self, PyObject *args);
static PyObject *t_sl_remove(t_sl *self, PyObject *key);
static PyObject *t_sl_first(t_sl *self, PyObject *args);
static PyObject *t_sl_next(t_sl *self, PyObject *args);
static PyObject *t_sl_previous(t_sl *self, PyObject *args);
static PyObject *t_sl_last(t_sl *self, PyObject *args);
static PyObject *t_sl_after(t_sl *self, PyObject *args);
static PyObject *t_sl_find(t_sl *self, PyObject *args);
static PyObject *t_sl_validate(t_sl *self, PyObject *arg);
static PyObject *t_sl_isValid(t_sl *self);


static PyMemberDef t_sl_members[] = {
    { "_head", T_OBJECT, offsetof(t_sl, head), 0, "" },
    { "_tail", T_OBJECT, offsetof(t_sl, tail), 0, "" },
    { "_flags", T_UINT, offsetof(t_sl, flags), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_sl_methods[] = {
    { "_clear_", (PyCFunction) t_sl__clear_, METH_NOARGS, "" },
    { "getLevel", (PyCFunction) t_sl_getLevel, METH_NOARGS, "" },
    { "position", (PyCFunction) t_sl_position, METH_O, "" },
/*
    { "_p0", (PyCFunction) t_sl__p0, METH_VARARGS, "" },
    { "_p1", (PyCFunction) t_sl__p1, METH_VARARGS, "" },
    { "_p2", (PyCFunction) t_sl__p2, METH_VARARGS, "" },
    { "_p3", (PyCFunction) t_sl__p3, METH_VARARGS, "" },
    { "_p4", (PyCFunction) t_sl__p4, METH_VARARGS, "" },
    { "_p5", (PyCFunction) t_sl__p5, METH_VARARGS, "" },
*/
    { "insert", (PyCFunction) t_sl_insert, METH_VARARGS, "" },
    { "move", (PyCFunction) t_sl_move, METH_VARARGS, "" },
    { "remove", (PyCFunction) t_sl_remove, METH_O, "" },
    { "first", (PyCFunction) t_sl_first, METH_VARARGS, "" },
    { "next", (PyCFunction) t_sl_next, METH_VARARGS, "" },
    { "previous", (PyCFunction) t_sl_previous, METH_VARARGS, "" },
    { "last", (PyCFunction) t_sl_last, METH_VARARGS, "" },
    { "after", (PyCFunction) t_sl_after, METH_VARARGS, "" },
    { "find", (PyCFunction) t_sl_find, METH_VARARGS, "" },
    { "validate", (PyCFunction) t_sl_validate, METH_O, "" },
    { "isValid", (PyCFunction) t_sl_isValid, METH_NOARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_sl_properties[] = {
    { "map",
      (getter) t_sl_getMap, NULL,
      "", NULL },
    { "level",
      (getter) t_sl_getLevel, NULL,
      "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PySequenceMethods t_sl_as_sequence = {
    (lenfunc)t_sl_list_length,        /* sq_length */
    0,                                /* sq_concat */
    0,                                /* sq_repeat */
    (ssizeargfunc)t_sl_list_get,      /* sq_item */
    0,                                /* sq_slice */
    0,                                /* sq_ass_item */
    0,                                /* sq_ass_slice */
    0,                                /* sq_contains */
    0,                                /* sq_inplace_concat */
    0,                                /* sq_inplace_repeat */
};

static PyTypeObject SkipListType = {
    PyObject_HEAD_INIT(NULL)
    0,                                /* ob_size */
    "chandlerdb.util.c.SkipList",     /* tp_name */
    sizeof(t_sl),                     /* tp_basicsize */
    0,                                /* tp_itemsize */
    (destructor)t_sl_dealloc,         /* tp_dealloc */
    0,                                /* tp_print */
    0,                                /* tp_getattr */
    0,                                /* tp_setattr */
    0,                                /* tp_compare */
    0,                                /* tp_repr */
    0,                                /* tp_as_number */
    &t_sl_as_sequence,                /* tp_as_sequence */
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
    "t_sl objects",                   /* tp_doc */
    (traverseproc)t_sl_traverse,      /* tp_traverse */
    (inquiry)t_sl_clear,              /* tp_clear */
    0,                                /* tp_richcompare */
    0,                                /* tp_weaklistoffset */
    0,                                /* tp_iter */
    0,                                /* tp_iternext */
    t_sl_methods,                     /* tp_methods */
    t_sl_members,                     /* tp_members */
    t_sl_properties,                  /* tp_getset */
    0,                                /* tp_base */
    0,                                /* tp_dict */
    0,                                /* tp_descr_get */
    0,                                /* tp_descr_set */
    0,                                /* tp_dictoffset */
    (initproc)t_sl_init,              /* tp_init */
    0,                                /* tp_alloc */
    (newfunc)t_sl_new,                /* tp_new */
};


static void t_sl_dealloc(t_sl *self)
{
    t_sl_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_sl_traverse(t_sl *self, visitproc visit, void *arg)
{
    Py_VISIT(self->head);
    Py_VISIT(self->tail);
    Py_VISIT(self->map);

    return 0;
}

static int t_sl_clear(t_sl *self)
{
    Py_CLEAR(self->head);
    Py_CLEAR(self->tail);
    Py_CLEAR(self->map);

    return 0;
}

static PyObject *t_sl_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_sl *self = (t_sl *) type->tp_alloc(type, 0);

    if (self)
    {
        self->head = NULL;
        self->tail = NULL;
        self->map = NULL;
        self->flags = 0;
    }

    return (PyObject *) self;
}

static int _t_sl_init(t_sl *self)
{
    PyObject *head = t_node_new(&NodeType, NULL, NULL);
    PyObject *tail = t_node_new(&NodeType, NULL, NULL);

    _t_node_init((t_node *) head, 1);
    _t_node_init((t_node *) tail, 1);

    Py_XDECREF(self->head);
    self->head = head;

    Py_XDECREF(self->tail);
    self->tail = tail;
    
    return 0;
}

static int t_sl_init(t_sl *self, PyObject *args, PyObject *kwds)
{
    PyObject *map;

    if (!PyArg_ParseTuple(args, "O", &map))
        return -1;

    Py_INCREF(map); Py_XDECREF(self->map);
    self->map = map;
    self->flags = 0;

    return _t_sl_init(self);
}

static PyObject *t_sl__clear_(t_sl *self, PyObject *arg)
{
    _t_sl_init(self);
    Py_RETURN_NONE;
}

static int _t_node_check(PyObject *node)
{
    if (!node)
        return -1;
    if (!PyObject_TypeCheck(node, CNode))
    {
        PyErr_SetObject(PyExc_TypeError, node);
        Py_DECREF(node);

        return -1;
    }

    return 0;
}

static t_node *_t_sl_map_get(t_sl *sl, PyObject *key)
{
    PyObject *node = PyObject_GetItem(sl->map, key);

    if (_t_node_check(node) < 0)
        return NULL;

    Py_DECREF(node); /* node must be in map for Py_DECREF to be safe */
    return (t_node *) node;
}

static int _t_sl_keyChanged(t_sl *sl, PyObject *key)
{
    PyObject *result =
        PyObject_CallMethodObjArgs(sl->map, _keyChanged_NAME, key, NULL);

    if (!result)
        return -1;

    Py_DECREF(result);
    return 0;
}

static PyObject *_t_sl_invalid(t_sl *self)
{
    PyErr_SetString(PyExc_LookupError,
                    "Access to skiplist is denied, it is marked INVALID");
    return NULL;
}

static PyObject *t_sl_position(t_sl *self, PyObject *key)
{
    t_node *node = _t_sl_map_get(self, key);
    int dist = -1;

    if (!node)
        return NULL;

    while (1) {
        int level = PyList_GET_SIZE(node->levels);
        t_point *point = _t_node_list_get(node, level);

        if (!point)
            return NULL;
        else
        {
            PyObject *prevKey = point->prevKey;

            if (prevKey == Py_None)
            {
                point = _t_node_list_get((t_node *) self->head, level);
                if (!point)
                    return NULL;

                dist += point->dist;
                break;
            }
            else
            {
                node = _t_sl_map_get(self, prevKey);
                if (!node)
                    return NULL;
                point = _t_node_list_get(node, level);
                if (!point)
                    return NULL;

                dist += point->dist;
            }
        }
    }
     
    return PyInt_FromLong(dist);
}


/* map property */

static PyObject *t_sl_getMap(t_sl *self, PyObject *arg)
{
    PyObject *map = self->map;

    Py_INCREF(map);
    return map;
}

/* level property */

static PyObject *t_sl_getLevel(t_sl *self, PyObject *arg)
{
    return PyInt_FromLong(PyList_GET_SIZE(((t_node *) self->head)->levels));
}


/* sl as sequence */

static Py_ssize_t t_sl_list_length(t_sl *self)
{
    return PyObject_Size(self->map);
}

static PyObject *_t_sl_list_get(t_sl *self, Py_ssize_t position)
{
    int count = PyObject_Size(self->map);

    if (count < 0)
        return NULL;

    if (position < 0)
        position += count;

    if (position < 0 || position >= count)
    {
        PyErr_Format(PyExc_IndexError, "position out of range: %d",
                     (int) position);
        return NULL;
    }
    else
    {
        t_node *node = (t_node *) self->head;
        int level = PyList_GET_SIZE(node->levels);
        int pos = -1;

        for (; level > 0; level--) {
            while (1) {
                t_point *point = _t_node_list_get(node, level);
                PyObject *nextKey;
                int next;

                if (!point)
                    return NULL;

                nextKey = point->nextKey;
                next = pos + point->dist;

                if (nextKey == Py_None || next > position)
                    break;

                if (next == position)
                    return nextKey;

                pos = next;

                node = _t_sl_map_get(self, nextKey);
                if (!node)
                    return NULL;
            }
        }

        PyErr_SetNone(PyExc_AssertionError);
        return NULL;
    }
}

static PyObject *t_sl_list_get(t_sl *self, Py_ssize_t position)
{
    PyObject *key = _t_sl_list_get(self, position);

    if (self->flags & SL_INVALID)
        return _t_sl_invalid(self);

    if (!key)
        return NULL;

    Py_INCREF(key);
    return key;
}

/*
        curr = map.get(key, None)

        if curr is None:
            if op == SkipList.REMOVE:
                raise KeyError, key
            elif op != SkipList.INSERT:
                op = SkipList.INSERT
            
            level = 1
            while (random() < 0.25 and level < SkipList.MAXLEVEL):
                level += 1

            if level > len(self):
                for i in xrange(len(self), level):
                    self._head._levels.append(CPoint(len(map)))
                    self._tail._levels.append(CPoint(0))
            curr = CNode(level)
            map[key] = curr
            prevKey = None

        else:
            if op == SkipList.INSERT:
                op = SkipList.MOVE
            elif op == SkipList.REMOVE:
                del map[key]
            elif op != SkipList.MOVE:
                raise ValueError, op

            level = len(curr)
            prevKey = curr[1].prevKey
*/

static int _t_sl__p0(t_sl *self, int op, PyObject *key,
                     PyObject **curr, int *level, PyObject **prevKey)
{
    *curr = PyObject_CallMethodObjArgs(self->map, get_NAME, key, Py_None, NULL);
    if (*curr != Py_None && _t_node_check(*curr) < 0)
        return -1;
    else
        Py_DECREF(*curr); /* *curr must be in map for Py_DECREF to be safe */

    if (*curr == Py_None)
    {
        int currentLevel;

        if (op == SL_REMOVE)
        {
            PyErr_SetObject(PyExc_KeyError, key);
            return -1;
        }
        else if (op != SL_INSERT)
            op = SL_INSERT;

        *level = 1;
        currentLevel = PyList_GET_SIZE(((t_node *) self->head)->levels);

#ifdef _MSC_VER            
        /* RAND_MAX >> 2 is 1 / P of the range of random(), P == 4 */
        while (rand() < (RAND_MAX >> 2) && *level < SL_MAXLEVEL)
            *level += 1;
#else
        /* 1 << 29 is 1 / P of the range of random(), P == 4 */
        while (random() < (1 << 29) && *level < SL_MAXLEVEL)
            *level += 1;
#endif

        if (*level > currentLevel)
        {
            PyObject *hl = ((t_node *) self->head)->levels;
            PyObject *tl = ((t_node *) self->tail)->levels;
            int dist = PyObject_Size(self->map);
            int i;

            for (i = currentLevel; i < *level; i++) {
                t_point *hp = (t_point *) t_point_new(CPoint, NULL, NULL);
                t_point *tp = (t_point *) t_point_new(CPoint, NULL, NULL);
                    
                _t_point_init(hp, dist);
                _t_point_init(tp, 0);

                PyList_Append(hl, (PyObject *) hp); Py_DECREF(hp);
                PyList_Append(tl, (PyObject *) tp); Py_DECREF(tp);
            }
        }
            
        *curr = (PyObject *) t_node_new(CNode, NULL, NULL);
        _t_node_init((t_node *) *curr, *level);

        PyObject_SetItem(self->map, key, *curr); Py_DECREF(*curr);
        *prevKey = Py_None;
    }
    else
    {
        t_point *point;

        switch (op) {
          case SL_INSERT:
            op = SL_MOVE;
            break;
          case SL_MOVE:
            break;
          case SL_REMOVE:
            break;
          default:
            PyErr_Format(PyExc_ValueError, "invalid op: %d", op);
            return -1;
        }

        *level = PyList_GET_SIZE(((t_node *) *curr)->levels);
        point = _t_node_list_get((t_node *) *curr, 1);
        if (!point)
            return -1;
        *prevKey = point->prevKey;
    }

    return 0;
}

/*
static PyObject *t_sl__p0(t_sl *self, PyObject *args)
{
    PyObject *key;
    int op;

    if (!PyArg_ParseTuple(args, "iO", &op, &key))
        return NULL;
    else
    {
        PyObject *curr, *prevKey;
        int level;

        if (_t_sl__p0(self, op, key, &curr, &level, &prevKey) < 0)
            return NULL;

        return Py_BuildValue("(OiO)", curr, level, prevKey);
    }
}
*/

/*
            while prevKey is not None:
                prev = map[prevKey]
                if len(prev) == lvl:
                    prevKey = prev[lvl].prevKey
                else:
                    break
*/

static int _t_sl__p1(t_sl *self, int lvl, PyObject **prevKey, t_node **prev)
{
    while (*prevKey != Py_None) {
        *prev = _t_sl_map_get(self, *prevKey);
        if (!*prev)
            return -1;

        if (PyList_GET_SIZE((*prev)->levels) == lvl)
        {
            t_point *point = _t_node_list_get(*prev, lvl);
    
            if (!point)
                return -1;

            *prevKey = point->prevKey;
        }
        else
            break;
    }

    return 0;
}

/*
static PyObject *t_sl__p1(t_sl *self, PyObject *args)
{
    PyObject *prevKey, *prev;
    int lvl;

    if (!PyArg_ParseTuple(args, "iO", &lvl, &prevKey))
        return NULL;

    if (_t_sl__p1(self, lvl, &prevKey, &prev) < 0)
        return NULL;

    return PyTuple_Pack(2, prevKey, prev);
}
*/

/*
            while afterKey is not None:
                after = map[afterKey]
                if len(after) == lvl:
                    afterKey = after[lvl].prevKey
                    if lvl < level:
                        if afterKey is None:
                            dist += self._head[lvl].dist
                        else:
                            dist += map[afterKey][lvl].dist
                else:
                    break
*/

static int _t_sl__p2(t_sl *self, int lvl, int level,
                     PyObject **afterKey, int *dist)
{
    while (*afterKey != Py_None) {
        t_node *after = _t_sl_map_get(self, *afterKey);

        if (!after)
            return -1;

        if (PyList_GET_SIZE(after->levels) == lvl)
        {
            t_point *point = _t_node_list_get(after, lvl);

            if (!point)
                return -1;

            *afterKey = point->prevKey;

            if (lvl < level)
            {
                if (*afterKey == Py_None)
                {
                    point = _t_node_list_get((t_node *) self->head, lvl);
                    if (!point)
                        return -1;

                    *dist += point->dist;
                }
                else
                {
                    t_node *node = _t_sl_map_get(self, *afterKey);

                    if (!node)
                        return -1;

                    point = _t_node_list_get(node, lvl);
                    if (!point)
                        return -1;

                    *dist += point->dist;
                }
            }
        }
        else
            break;
    }

    return 0;
}

/*
static PyObject *t_sl__p2(t_sl *self, PyObject *args)
{
    PyObject *afterKey;
    int lvl, level, dist;

    if (!PyArg_ParseTuple(args, "iiOi", &lvl, &level, &afterKey, &dist))
        return NULL;

    if (_t_sl__p2(self, lvl, level, &afterKey, &dist) < 0)
        return NULL;

    return Py_BuildValue("(Oi)", afterKey, dist);
}
*/

/*
                if prevKey is not None:
                    map[prevKey][lvl].dist -= 1
                    self.map._keyChanged(prevKey)
                elif op != SkipList.INSERT:
                    self._head[lvl].dist -= 1

                if op != SkipList.REMOVE:
                    if afterKey is not None:
                        map[afterKey][lvl].dist += 1
                        self.map._keyChanged(afterKey)
                    else:
                        self._head[lvl].dist += 1
*/

static int _t_sl__p3(t_sl *self, PyObject *prevKey, PyObject *afterKey,
                     int lvl, int op)
{
    t_point *point;

    if (prevKey != Py_None)
    {
        t_node *node = _t_sl_map_get(self, prevKey);

        if (!node)
            return -1;

        point = _t_node_list_get(node, lvl);
        if (!point)
            return -1;
        point->dist -= 1;

        if (_t_sl_keyChanged(self, prevKey) < 0)
            return -1;
    }
    else if (op != SL_INSERT)
    {
        point = _t_node_list_get((t_node *) self->head, lvl);
        if (!point)
            return -1;
        point->dist -= 1;
    }

    if (op != SL_REMOVE)
    {
        if (afterKey != Py_None)
        {
            t_node *node = _t_sl_map_get(self, afterKey);

            if (!node)
                return -1;

            point = _t_node_list_get(node, lvl);
            if (!point)
                return -1;
            point->dist += 1;

            if (_t_sl_keyChanged(self, afterKey) < 0)
                return -1;
        }
        else
        {
            point = _t_node_list_get((t_node *) self->head, lvl);
            if (!point)
                return -1;
            point->dist += 1;
        }
    }

    return 0;
}

/*
static PyObject *t_sl__p3(t_sl *self, PyObject *args)
{
    PyObject *prevKey, *afterKey;
    int lvl, op;

    if (!PyArg_ParseTuple(args, "OOii", &prevKey, &afterKey, &lvl, &op))
        return NULL;
    else if (_t_sl__p3(self, prevKey, afterKey, lvl, op) < 0)
        return NULL;

    Py_RETURN_NONE;
}
*/

/*
                prevKey = point.prevKey
                nextKey = point.nextKey

                if prevKey is not None:
                    prev = map[prevKey]
                    self.map._keyChanged(prevKey)
                elif op != SkipList.INSERT:
                    prev = self._head
                else:
                    prev = None

                if nextKey is not None:
                    next = map[nextKey]
                    self.map._keyChanged(nextKey)
                elif op != SkipList.INSERT:
                    next = self._tail
                else:
                    next = None
*/

static PyObject *__t_sl__p4(t_sl *self, PyObject *key, int op, int next)
{
    PyObject *node;

    if (key != Py_None)
    {
        node = (PyObject *) _t_sl_map_get(self, key);
        if (!node)
            return NULL;
        if (_t_sl_keyChanged(self, key) < 0)
            return NULL;
    }
    else if (op != SL_INSERT)
    {
        if (next)
            node = self->tail;
        else
            node = self->head;
    }
    else
        node = Py_None;

    return node;
}

/*
                if prev is not None:
                    prev.setNext(lvl, nextKey, prevKey, self, currDist - 1)
                if next is not None:
                    next.setPrev(lvl, prevKey, nextKey, self)
*/

static int _t_sl__p4(t_sl *self, int lvl, t_point *point, int op,
                     PyObject **prev, PyObject **next)
{
    *prev = __t_sl__p4(self, point->prevKey, op, 0);
    if (!*prev)
        return -1;

    *next = __t_sl__p4(self, point->nextKey, op, 1);
    if (!*next)
        return -1;

    if (*prev != Py_None)
    {
        if (_t_node_setNext((t_node *) *prev, lvl,
                            point->nextKey, point->prevKey,
                            self, point->dist - 1) < 0)
            return -1;
    }

    if (*next != Py_None)
    {
        if (_t_node_setPrev((t_node *) *next, lvl,
                            point->prevKey, point->nextKey,
                            self) < 0)
            return -1;
    }

    return 0;
}

/*
static PyObject *t_sl__p4(t_sl *self, PyObject *args)
{
    t_point *point;
    int lvl, op;

    if (!PyArg_ParseTuple(args, "iOi", &lvl, &point, &op))
        return NULL;
    else if (!PyObject_TypeCheck((PyObject *) point, CPoint))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) point);
        return NULL;
    }
    else
    {
        PyObject *prev, *next;
        
        if (_t_sl__p4(self, lvl, point, op, &prev, &next) < 0)
            return NULL;

        return PyTuple_Pack(2, prev, next);
    }
}
*/

/*
                    if afterKey is not None:
                        after = map[afterKey]
                        self.map._keyChanged(afterKey)
                    else:
                        after = self._head
                    afterPoint = after[lvl]
                    afterNextKey = afterPoint.nextKey
                    afterDist = afterPoint.dist
            
                    if afterNextKey is not None:
                        map[afterNextKey].setPrev(lvl, key, afterNextKey, self)
                        self.map._keyChanged(afterNextKey)

                    after.setNext(lvl, key, afterKey, self,
                                  -afterDist + dist + 1)

                    curr.setPrev(lvl, afterKey, key, self)
                    curr.setNext(lvl, afterNextKey, key, self,
                                 -currDist + afterDist - dist)
                    self.map._keyChanged(key)
*/

static int _t_sl__p5(t_sl *self, PyObject *key, PyObject *afterKey,
                     t_node *curr, int dist, int currDist, int lvl)
{
    PyObject *afterNextKey;
    t_point *afterPoint;
    int afterDist;
    t_node *after;

    if (afterKey != Py_None)
    {
        after = _t_sl_map_get(self, afterKey);
        if (!after)
            return -1;
        if (_t_sl_keyChanged(self, afterKey) < 0)
            return -1;
    }
    else
        after = (t_node *) self->head;

    afterPoint = _t_node_list_get(after, lvl);
    if (!afterPoint)
        return -1;

    afterDist = afterPoint->dist;
    afterNextKey = afterPoint->nextKey;
    Py_INCREF(afterNextKey);

    if (afterNextKey != Py_None)
    {
        t_node *node = _t_sl_map_get(self, afterNextKey);

        if (!node ||
            _t_node_setPrev(node, lvl, key, afterNextKey, self) < 0 ||
            _t_sl_keyChanged(self, afterNextKey) < 0)
        {
            Py_DECREF(afterNextKey);
            return -1;
        }
    }

    if (_t_node_setNext(after, lvl, key, afterKey, self,
                        -afterDist + dist + 1) < 0 ||
        _t_node_setPrev(curr, lvl, afterKey, key, self) < 0 ||
        _t_node_setNext(curr, lvl, afterNextKey, key, self,
                        -currDist + afterDist - dist) ||
        _t_sl_keyChanged(self, key) < 0)
    {
        Py_DECREF(afterNextKey);
        return -1;
    }

    Py_DECREF(afterNextKey);
    return 0;
}

/*
static PyObject *t_sl__p5(t_sl *self, PyObject *args)
{
    PyObject *key, *afterKey, *curr;
    int lvl, dist, currDist;

    if (!PyArg_ParseTuple(args, "OOOiii", &key, &afterKey,
                          &curr, &dist, &currDist, &lvl))
        return NULL;
    else if (!PyObject_TypeCheck(curr, CNode))
    {
        PyErr_SetObject(PyExc_TypeError, curr);
        return NULL;
    }
    else if (_t_sl__p5(self, key, afterKey, (t_node *) curr,
                       dist, currDist, lvl) < 0)
        return NULL;

    Py_RETURN_NONE;
}
*/

/*
    def _place(self, op, key, afterKey=None):

        map = self.map
        assert key != afterKey

        curr, level, prevKey = self._p0(op, key)

        dist = 0
        for lvl in xrange(1, self.level + 1):
            if lvl <= level:
                point = curr[lvl]
                currDist = point.dist
            
                prev, next = self._p4(lvl, point, op)

                if op == SkipList.REMOVE:
                    point.nextKey = None
                    point.prevKey = None
                    point.dist = 0
                else:
                    self._p5(key, afterKey, curr, dist, currDist, lvl)

            else:
                self._p3(prevKey, afterKey, lvl, op)

            prevKey, prev = self._p1(prevKey, lvl)
            afterKey, after, dist = self._p2(afterKey, lvl, level, dist)
*/

static int _t_sl__place(t_sl *self, int op, PyObject *key, PyObject *afterKey)
{
    PyObject *prevKey, *prev, *next;
    int level, headLevel, lvl;
    int dist = 0;
    t_node *curr;

    if (afterKey == Default || afterKey == Nil)
        afterKey = Py_None;

    if (!PyObject_Compare(key, afterKey))
    {
        PyErr_Format(PyExc_AssertionError, "key != afterKey");
        return -1;
    }

    if (_t_sl__p0(self, op, key, (PyObject **) &curr, &level, &prevKey) < 0)
        return -1;

    headLevel = PyList_GET_SIZE(((t_node *) self->head)->levels);

    for (lvl = 1; lvl <= headLevel; lvl++) {
        if (lvl <= level)
        {
            t_point *point = _t_node_list_get(curr, lvl);
            int currDist;

            if (!point)
                return -1;

            currDist = point->dist;
            
            if (_t_sl__p4(self, lvl, point, op, &prev, &next) < 0)
                return -1;

            if (op != SL_REMOVE)
                if (_t_sl__p5(self, key, afterKey,
                              curr, dist, currDist, lvl) < 0)
                    return -1;
        }
        else if (_t_sl__p3(self, prevKey, afterKey, lvl, op) < 0)
            return -1;

        if (_t_sl__p1(self, lvl, &prevKey, (t_node **) &prev) < 0 ||
            _t_sl__p2(self, lvl, level, &afterKey, &dist) < 0)
            return -1;
    }

    if (op == SL_REMOVE && PyObject_DelItem(self->map, key) < 0)
        return -1;

    return 0;
}


static PyObject *t_sl_insert(t_sl *self, PyObject *args)
{
    PyObject *key, *afterKey;

    if (!PyArg_ParseTuple(args, "OO", &key, &afterKey))
        return NULL;

    if (_t_sl__place(self, SL_INSERT, key, afterKey) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_sl_move(t_sl *self, PyObject *args)
{
    PyObject *key, *afterKey;

    if (!PyArg_ParseTuple(args, "OO", &key, &afterKey))
        return NULL;

    if (_t_sl__place(self, SL_MOVE, key, afterKey) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_sl_remove(t_sl *self, PyObject *key)
{
    if (_t_sl__place(self, SL_REMOVE, key, Py_None) < 0)
        return NULL;

    Py_RETURN_NONE;
}

static PyObject *t_sl_first(t_sl *self, PyObject *args)
{
    int level = 1;

    if (self->flags & SL_INVALID)
        return _t_sl_invalid(self);

    if (!PyArg_ParseTuple(args, "|i", &level))
        return NULL;
    else
    {
        t_point *point = _t_node_list_get((t_node *) self->head, level);

        if (!point)
            return NULL;

        Py_INCREF(point->nextKey);
        return point->nextKey;
    }
}

static PyObject *t_sl_next(t_sl *self, PyObject *args)
{
    PyObject *key;
    int level = 1;

    if (self->flags & SL_INVALID)
        return _t_sl_invalid(self);

    if (!PyArg_ParseTuple(args, "O|i", &key, &level))
        return NULL;
    else
    {
        t_node *node = _t_sl_map_get(self, key);
        t_point *point;

        if (!node)
            return NULL;

        point = _t_node_list_get(node, level);
        if (!point)
            return NULL;

        Py_INCREF(point->nextKey);
        return point->nextKey;
    }
}

static PyObject *t_sl_previous(t_sl *self, PyObject *args)
{
    PyObject *key;
    int level = 1;

    if (self->flags & SL_INVALID)
        return _t_sl_invalid(self);

    if (!PyArg_ParseTuple(args, "O|i", &key, &level))
        return NULL;
    else
    {
        t_node *node = _t_sl_map_get(self, key);
        t_point *point;

        if (!node)
            return NULL;

        point = _t_node_list_get(node, level);
        if (!point)
            return NULL;

        Py_INCREF(point->prevKey);
        return point->prevKey;
    }
}

static PyObject *t_sl_last(t_sl *self, PyObject *args)
{
    int level = 1;

    if (self->flags & SL_INVALID)
        return _t_sl_invalid(self);

    if (!PyArg_ParseTuple(args, "|i", &level))
        return NULL;
    else
    {
        t_point *point = _t_node_list_get((t_node *) self->tail, level);

        if (!point)
            return NULL;

        Py_INCREF(point->prevKey);
        return point->prevKey;
    }
}

/*
        pos = lo = 0
        hi = len(index) - 1
        afterKey = None
        
        while lo <= hi:
            pos = (lo + hi) >> 1
            afterKey = skipList[pos]
            diff = self.compare(key, afterKey)

            if diff == 0:
                return afterKey

            if diff < 0:
                hi = pos - 1
            else:
                pos += 1
                lo = pos

        if pos == 0:
            return None

        return skipList[pos - 1]
*/

/* if the skip list is sorted, return the insertion point for a key */
static PyObject *t_sl_after(t_sl *self, PyObject *args)
{
    PyObject *key, *callable;

    if (self->flags & SL_INVALID)
        return _t_sl_invalid(self);

    if (!PyArg_ParseTuple(args, "OO", &key, &callable))
        return NULL;
    else
    {
        int pos = 0, lo = 0;
        int hi = PyObject_Size(self->map) - 1;
        
        while (lo <= hi) {
            PyObject *afterKey;
            PyObject *result, *args;
            int diff;

            pos = (lo + hi) >> 1;
            afterKey = _t_sl_list_get(self, pos);
            if (!afterKey)
                return NULL;

            args = PyTuple_Pack(2, key, afterKey);
            result = PyObject_Call(callable, args, NULL);
            Py_DECREF(args);

            if (!result)
                return NULL;
            if (!PyInt_CheckExact(result))
            {
                PyErr_SetObject(PyExc_TypeError, result);
                Py_DECREF(result);
                return NULL;
            }

            diff = PyInt_AS_LONG(result);
            Py_DECREF(result);

            if (diff == 0)
            {
                Py_INCREF(afterKey);
                return afterKey;
            }

            if (diff < 0)
                hi = pos - 1;
            else
            {
                pos += 1;
                lo = pos;
            }
        }

        if (pos == 0)
            Py_RETURN_NONE;

        return t_sl_list_get(self, pos - 1);
    }
}

/*
        pos = lo = 0
        hi = len(self) - 1
        match = None

        while lo <= hi:
            pos = (lo + hi) / 2
            key = self.getKey(pos)
            diff = callable(key, *args)

            if diff == 0:
                if mode == 'exact':
                    return key

                match = key
                if mode == 'first':
                    hi = pos - 1
                elif mode == 'last':
                    pos += 1
                    lo = pos
                else:
                    raise ValueError, mode

            elif diff < 0:
                hi = pos - 1

            else:
                pos += 1
                lo = pos

        return match
*/

/* if the skip list is sorted, return a key matching a congruent predicate */
static PyObject *t_sl_find(t_sl *self, PyObject *args)
{
    PyObject *mode, *callable, *match;
    int numArgs, lo, hi;

    if (self->flags & SL_INVALID)
        return _t_sl_invalid(self);

    if (!PyTuple_Check(args))
    {
        PyErr_SetObject(PyExc_TypeError, args);
        return NULL;
    }

    numArgs = PyTuple_Size(args);
    if (numArgs < 2)
    {
        PyErr_SetString(PyExc_TypeError, "at least 2 arguments required");
        return NULL;
    }

    mode = PyTuple_GetItem(args, 0);
    callable = PyTuple_GetItem(args, 1);

    lo = 0;
    hi = PyObject_Size(self->map) - 1;
    match = Py_None;

    while (lo <= hi) {
        int pos = (lo + hi) >> 1;
        PyObject *key = _t_sl_list_get(self, pos);
        PyObject *result, *_args;
        int diff;

        if (!key)
            return NULL;

        _args = PyTuple_New(numArgs - 1);
        Py_INCREF(key); PyTuple_SET_ITEM(_args, 0, key);
        if (numArgs > 2)
        {
            int i, j;

            for (i = 2, j = 1; i < numArgs; i++, j++) {
                PyObject *arg = PyTuple_GET_ITEM(args, i);
                Py_INCREF(arg); PyTuple_SET_ITEM(_args, j, arg);
            }
        }
        result = PyObject_Call(callable, _args, NULL);
        Py_DECREF(_args);
        if (!result)
            return NULL;
        if (!PyInt_Check(result))
        {
            PyErr_SetObject(PyExc_TypeError, result);
            Py_DECREF(result);
            return NULL;
        }

        diff = PyInt_AsLong(result);
        Py_DECREF(result);

        if (diff == 0)
        {
            if (!PyObject_Compare(mode, exact_NAME))
            {
                Py_INCREF(key);
                return key;
            }

            match = key;
        
            if (!PyObject_Compare(mode, first_NAME))
                hi = pos - 1;
            else if (!PyObject_Compare(mode, last_NAME))
                lo = pos + 1;
            else
            {
                PyErr_SetObject(PyExc_ValueError, mode);
                return NULL;
            }
        }
        else if (diff < 0)
            hi = pos - 1;
        else
            lo = pos + 1;
    }
    
    Py_INCREF(match);
    return match;
}

static PyObject *t_sl_validate(t_sl *self, PyObject *arg)
{
    if (PyObject_IsTrue(arg))
        self->flags &= ~SL_INVALID;
    else
        self->flags |= SL_INVALID;

    Py_RETURN_NONE;
}

static PyObject *t_sl_isValid(t_sl *self)
{
    if (self->flags & SL_INVALID)
        Py_RETURN_FALSE;

    Py_RETURN_TRUE;
}


void _init_skiplist(PyObject *m)
{
    if (PyType_Ready(&PointType) >= 0 &&
        PyType_Ready(&NodeType) >= 0 &&
        PyType_Ready(&SkipListType) >= 0)
    {
        if (m)
        {
            PyObject *dict;

#ifdef _MSC_VER
            srand((unsigned long) clock());
#else
            srandom((unsigned long) clock());
#endif

            Py_INCREF(&PointType);
            PyModule_AddObject(m, "CPoint", (PyObject *) &PointType);
            CPoint = &PointType;

            Py_INCREF(&NodeType);
            PyModule_AddObject(m, "CNode", (PyObject *) &NodeType);
            CNode = &NodeType;

            Py_INCREF(&SkipListType);
            PyModule_AddObject(m, "SkipList", (PyObject *) &SkipListType);
            SkipList = &SkipListType;

            dict = SkipListType.tp_dict;

            PyDict_SetItemString(dict, "Node", (PyObject *) &NodeType);
            PyDict_SetItemString_Int(dict, "MAXLEVEL", SL_MAXLEVEL);

            PyDict_SetItemString_Int(dict, "INSERT", SL_INSERT);
            PyDict_SetItemString_Int(dict, "MOVE", SL_MOVE);
            PyDict_SetItemString_Int(dict, "REMOVE", SL_REMOVE);

            get_NAME = PyString_FromString("get");
            _keyChanged_NAME = PyString_FromString("_keyChanged");
            exact_NAME = PyString_FromString("exact");
            first_NAME = PyString_FromString("first");
            last_NAME = PyString_FromString("last");
        }
    }
}
