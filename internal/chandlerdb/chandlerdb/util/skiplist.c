
/*
 * The C SkipList type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include <Python.h>
#include "structmember.h"

#include "c.h"


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
    PyObject *repr = PyString_FromFormat("<point: %s, %s, %d>",
                                         PyString_AsString(prev),
                                         PyString_AsString(next),
                                         self->dist);
                                         
    Py_DECREF(prev);
    Py_DECREF(next);

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
    Py_INCREF(value); Py_XDECREF(self->nextKey);
    self->nextKey = value;

    return 0;
}


static void t_node_dealloc(t_node *self);
static int t_node_traverse(t_node *self, visitproc visit, void *arg);
static int t_node_clear(t_node *self);
static PyObject *t_node_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_node_init(t_node *self, PyObject *args, PyObject *kwds);

static int t_node_list_length(t_node *self);
static t_point *_t_node_list_get(t_node *self, int i);
static PyObject *t_node_list_get(t_node *self, int i);

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
    (inquiry)t_node_list_length,      /* sq_length */
    0,                                /* sq_concat */
    0,                                /* sq_repeat */
    (intargfunc)t_node_list_get,      /* sq_item */
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

static int t_node_list_length(t_node *self)
{
    return PyList_GET_SIZE(self->levels);
}

static t_point *_t_node_list_get(t_node *self, int i)
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

    PyErr_Format(PyExc_IndexError, "index out of range: %d", i);
    return NULL;
}

static PyObject *t_node_list_get(t_node *self, int i)
{
    PyObject *point = (PyObject *) _t_node_list_get(self, i);

    if (!point)
        return NULL;

    Py_INCREF(point);
    return point;
}


static PyObject *t_node_setPrev(t_node *self, PyObject *args)
{
    PyObject *prevKey, *key, *skipList;
    t_point *point;
    int level;

    if (!PyArg_ParseTuple(args, "iOOO", &level, &prevKey, &key, &skipList))
        return NULL;

    if (!PyObject_TypeCheck(skipList, CSkipList))
    {
        PyErr_SetObject(PyExc_TypeError, skipList);
        return NULL;
    }

    if (prevKey == Py_None)
    {
        t_node *head = (t_node *) ((t_sl *) skipList)->head;

        point = _t_node_list_get(head, level);
        if (!point)
            return NULL;

        t_point_setNextKey(point, key, NULL);
    }

    point = _t_node_list_get(self, level);
    if (!point)
        return NULL;
    t_point_setPrevKey(point, prevKey, NULL);

    Py_RETURN_NONE;
}

static PyObject *t_node_setNext(t_node *self, PyObject *args)
{
    PyObject *nextKey, *key, *skipList;
    t_point *point;
    int level, delta;

    if (!PyArg_ParseTuple(args, "iOOOi",
                          &level, &nextKey, &key, &skipList, &delta))
        return NULL;

    if (!PyObject_TypeCheck(skipList, CSkipList))
    {
        PyErr_SetObject(PyExc_TypeError, skipList);
        return NULL;
    }

    if (nextKey == Py_None)
    {
        t_node *tail = (t_node *) ((t_sl *) skipList)->tail;
        point = _t_node_list_get(tail, level);
        if (!point)
            return NULL;
        t_point_setPrevKey(point, key, NULL);
    }

    point = _t_node_list_get(self, level);
    if (!point)
        return NULL;
    t_point_setNextKey(point, nextKey, NULL);
    point->dist += delta;

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
static int t_sl_list_length(t_sl *self);
static PyObject *t_sl_list_get(t_sl *self, int i);
static PyObject *t_sl_position(t_sl *self, PyObject *key);


static PyMemberDef t_sl_members[] = {
    { "_head", T_OBJECT, offsetof(t_sl, head), 0, "" },
    { "_tail", T_OBJECT, offsetof(t_sl, tail), 0, "" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_sl_methods[] = {
    { "_clear_", (PyCFunction) t_sl__clear_, METH_NOARGS, "" },
    { "getLevel", (PyCFunction) t_sl_getLevel, METH_NOARGS, "" },
    { "position", (PyCFunction) t_sl_position, METH_O, "" },
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
    (inquiry)t_sl_list_length,        /* sq_length */
    0,                                /* sq_concat */
    0,                                /* sq_repeat */
    (intargfunc)t_sl_list_get,        /* sq_item */
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
    "chandlerdb.util.c.CSkipList",    /* tp_name */
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

static PyObject *t_sl_position(t_sl *self, PyObject *key)
{
    PyObject *node = PyObject_GetItem(self->map, key);
    int dist = -1;

    if (_t_node_check(node) < 0)
        return NULL;

    while (1) {
        PyObject *levels = ((t_node *) node)->levels;
        int level = PyList_GET_SIZE(levels);
        t_point *point = _t_node_list_get((t_node *) node, level);

        if (!point)
        {
            Py_DECREF(node);
            return NULL;
        }
        else
        {
            PyObject *prevKey = point->prevKey;

            if (prevKey == Py_None)
            {
                Py_DECREF(node); node = self->head;
                point = _t_node_list_get((t_node *) node, level);
                if (!point)
                    return NULL;

                dist += point->dist;
                break;
            }
            else
            {
                Py_DECREF(node); node = PyObject_GetItem(self->map, prevKey);
                if (_t_node_check(node) < 0)
                    return NULL;
                point = _t_node_list_get((t_node *) node, level);
                if (!point)
                {
                    Py_DECREF(node);
                    return NULL;
                }
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

static int t_sl_list_length(t_sl *self)
{
    return PyObject_Size(self->map);
}

static PyObject *t_sl_list_get(t_sl *self, int position)
{
    PyObject *map = self->map;
    int count = PyObject_Size(map);

    if (!self->ob_refcnt)
        abort();

    if (count < 0)
        return NULL;

    if (position < 0)
        position += count;

    if (position < 0 || position >= count)
    {
        PyErr_Format(PyExc_IndexError, "position out of range: %d", position);
        return NULL;
    }
    else
    {
        t_node *node = (t_node *) self->head;
        int level = PyList_GET_SIZE(node->levels);
        int pos = -1;

        if (level > 0)
            Py_INCREF(node);

        for (; level > 0; level--) {
            while (1) {
                t_point *point = _t_node_list_get(node, level);
                PyObject *nextKey;
                int next;

                if (!point)
                {
                    Py_DECREF(node);
                    return NULL;
                }

                nextKey = point->nextKey;
                next = pos + point->dist;

                if (nextKey == Py_None || next > position)
                    break;
                if (next == position)
                {
                    Py_INCREF(nextKey);
                    Py_DECREF(node);
                    return nextKey;
                }

                pos = next;

                node = (t_node *) PyObject_GetItem(map, nextKey);
                if (!node)
                    return NULL;
                if (!PyObject_TypeCheck(node, CNode))
                {
                    PyErr_SetObject(PyExc_TypeError, (PyObject *) node);
                    Py_DECREF(node);

                    return NULL;
                }
            }
        }

        PyErr_SetNone(PyExc_AssertionError);
        return NULL;
    }
}


void _init_skiplist(PyObject *m)
{
    if (PyType_Ready(&PointType) >= 0 &&
        PyType_Ready(&NodeType) >= 0 &&
        PyType_Ready(&SkipListType) >= 0)
    {
        if (m)
        {
            Py_INCREF(&PointType);
            PyModule_AddObject(m, "CPoint", (PyObject *) &PointType);
            CPoint = &PointType;

            Py_INCREF(&NodeType);
            PyModule_AddObject(m, "CNode", (PyObject *) &NodeType);
            CNode = &NodeType;

            Py_INCREF(&SkipListType);
            PyModule_AddObject(m, "CSkipList", (PyObject *) &SkipListType);
            CSkipList = &SkipListType;
        }
    }
}
