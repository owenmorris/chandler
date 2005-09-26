
/*
 * The item C type
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include <Python.h>
#include "structmember.h"

#include "c.h"
#include "../schema/descriptor.h"
#include "../schema/attribute.h"

static void t_item_dealloc(t_item *self);
static int t_item_traverse(t_item *self, visitproc visit, void *arg);
static int t_item_clear(t_item *self);
static PyObject *t_item_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_item_init(t_item *self, PyObject *args, PyObject *kwds);
static PyObject *t_item_isNew(t_item *self, PyObject *args);
static PyObject *t_item_isDeleting(t_item *self, PyObject *args);
static PyObject *t_item_isDeleted(t_item *self, PyObject *args);
static PyObject *t_item_isStale(t_item *self, PyObject *args);
static PyObject *t_item_isPinned(t_item *self, PyObject *args);
static PyObject *t_item_isSchema(t_item *self, PyObject *args);
static PyObject *t_item_isDirty(t_item *self, PyObject *args);
static PyObject *t_item_getDirty(t_item *self, PyObject *args);
static PyObject *t_item__isNDirty(t_item *self, PyObject *args);
static PyObject *t_item__isNoDirty(t_item *self, PyObject *args);
static PyObject *t_item__isCopyExport(t_item *self, PyObject *args);
static PyObject *t_item__isImporting(t_item *self, PyObject *args);
static PyObject *t_item__isRepository(t_item *self, PyObject *args);
static PyObject *t_item__isView(t_item *self, PyObject *args);
static PyObject *t_item__isItem(t_item *self, PyObject *args);
static PyObject *t_item__isRefList(t_item *self, PyObject *args);
static PyObject *t_item__isUUID(t_item *self, PyObject *args);
static PyObject *t_item__isMerged(t_item *self, PyObject *args);
static PyObject *t_item_getAttributeAspect(t_item *self, PyObject *args);
static PyObject *t_item__getKind(t_item *self, void *data);
static int t_item__setKind(t_item *self, PyObject *kind, void *data);
static PyObject *t_item__getView(t_item *self, void *data);
static int t_item__setView(t_item *self, PyObject *view, void *data);
static PyObject *t_item__getParent(t_item *self, void *data);
static int t_item__setParent(t_item *self, PyObject *view, void *data);
static PyObject *t_item__getName(t_item *self, void *data);
static int t_item__setName(t_item *self, PyObject *name, void *data);
static PyObject *t_item__getRoot(t_item *self, void *data);
static PyObject *t_item__getUUID(t_item *self, void *data);
static PyObject *t_item__getPath(t_item *self, void *data);
static PyObject *t_item__getVersion(t_item *self, void *data);

static PyObject *_setKind_NAME;
static PyObject *importItem_NAME;
static PyObject *move_NAME;
static PyObject *rename_NAME;
static PyObject *_getPath_NAME;
static PyObject *find_NAME;
static PyObject *getAttribute_NAME;
static PyObject *getAspect_NAME;
static PyObject *getAttributeAspect_NAME;
static PyObject *redirectTo_NAME;
static PyObject *_redirectTo_NAME;

/* NULL docstrings are set in chandlerdb/__init__.py
 * "" docstrings are missing docstrings
 */

static PyMemberDef t_item_members[] = {
    { "_status", T_UINT, offsetof(t_item, status), 0, "item status flags" },
    { "_version", T_UINT, offsetof(t_item, version), 0, "item version" },
    { "_lastAccess", T_UINT, offsetof(t_item, lastAccess), 0, "access stamp" },
    { "_uuid", T_OBJECT, offsetof(t_item, uuid), 0, "item uuid" },
    { "_name", T_OBJECT, offsetof(t_item, name), 0, "item name" },
    { "_values", T_OBJECT, offsetof(t_item, values), 0, "literals" },
    { "_references", T_OBJECT, offsetof(t_item, references), 0, "references" },
    { "_kind", T_OBJECT, offsetof(t_item, kind), 0, "item kind" },
    { "_parent", T_OBJECT, offsetof(t_item, parent), 0, "item parent" },
    { "_children", T_OBJECT, offsetof(t_item, children), 0, "item children" },
    { "_root", T_OBJECT, offsetof(t_item, root), 0, "item root" },
    { "_acls", T_OBJECT, offsetof(t_item, acls), 0, "item acls" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_item_methods[] = {
    { "isNew", (PyCFunction) t_item_isNew, METH_NOARGS, NULL },
    { "isDeleting", (PyCFunction) t_item_isDeleting, METH_NOARGS, NULL },
    { "isDeleted", (PyCFunction) t_item_isDeleted, METH_NOARGS, NULL },
    { "isStale", (PyCFunction) t_item_isStale, METH_NOARGS, NULL },
    { "isPinned", (PyCFunction) t_item_isPinned, METH_NOARGS, NULL },
    { "isSchema", (PyCFunction) t_item_isSchema, METH_NOARGS, "" },
    { "isDirty", (PyCFunction) t_item_isDirty, METH_NOARGS, NULL },
    { "getDirty", (PyCFunction) t_item_getDirty, METH_NOARGS, NULL },
    { "_isNDirty", (PyCFunction) t_item__isNDirty, METH_NOARGS, "" },
    { "_isNoDirty", (PyCFunction) t_item__isNoDirty, METH_NOARGS, "" },
    { "_isCopyExport", (PyCFunction) t_item__isCopyExport, METH_NOARGS, "" },
    { "_isImporting", (PyCFunction) t_item__isImporting, METH_NOARGS, "" },
    { "_isRepository", (PyCFunction) t_item__isRepository, METH_NOARGS, "" },
    { "_isView", (PyCFunction) t_item__isView, METH_NOARGS, "" },
    { "_isItem", (PyCFunction) t_item__isItem, METH_NOARGS, "" },
    { "_isRefList", (PyCFunction) t_item__isRefList, METH_NOARGS, "" },
    { "_isUUID", (PyCFunction) t_item__isUUID, METH_NOARGS, "" },
    { "_isMerged", (PyCFunction) t_item__isMerged, METH_NOARGS, "" },
    { "getAttributeAspect", (PyCFunction) t_item_getAttributeAspect, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_item_properties[] = {
    { "itsKind", (getter) t_item__getKind, (setter) t_item__setKind,
      NULL, NULL },
    { "itsView", (getter) t_item__getView, (setter) t_item__setView,
      NULL, NULL },
    { "itsParent", (getter) t_item__getParent, (setter) t_item__setParent,
      NULL, NULL },
    { "itsName", (getter) t_item__getName, (setter) t_item__setName,
      NULL, NULL },
    { "itsRoot", (getter) t_item__getRoot, NULL,
      NULL, NULL },
    { "itsUUID", (getter) t_item__getUUID, NULL,
      NULL, NULL },
    { "itsPath", (getter) t_item__getPath, NULL,
      NULL, NULL },
    { "itsVersion", (getter) t_item__getVersion, NULL,
      "itsVersion property", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject ItemType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.CItem",                 /* tp_name */
    sizeof(t_item),                            /* tp_basicsize */
    0,                                         /* tp_itemsize */
    (destructor)t_item_dealloc,                /* tp_dealloc */
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
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "C Item type",                             /* tp_doc */
    (traverseproc)t_item_traverse,             /* tp_traverse */
    (inquiry)t_item_clear,                     /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    0,                                         /* tp_iter */
    0,                                         /* tp_iternext */
    t_item_methods,                            /* tp_methods */
    t_item_members,                            /* tp_members */
    t_item_properties,                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    (initproc)t_item_init,                     /* tp_init */
    0,                                         /* tp_alloc */
    (newfunc)t_item_new,                       /* tp_new */
};


static void t_item_dealloc(t_item *self)
{
    t_item_clear(self);
    self->ob_type->tp_free((PyObject *) self);
}

static int t_item_traverse(t_item *self, visitproc visit, void *arg)
{
    Py_VISIT(self->uuid);
    Py_VISIT(self->name);
    Py_VISIT(self->values);
    Py_VISIT(self->references);
    Py_VISIT(self->kind);
    Py_VISIT(self->parent);
    Py_VISIT(self->children);
    Py_VISIT(self->root);
    Py_VISIT(self->acls);

    return 0;
}

static int t_item_clear(t_item *self)
{
    Py_CLEAR(self->uuid);
    Py_CLEAR(self->name);
    Py_CLEAR(self->values);
    Py_CLEAR(self->references);
    Py_CLEAR(self->kind);
    Py_CLEAR(self->parent);
    Py_CLEAR(self->children);
    Py_CLEAR(self->root);
    Py_CLEAR(self->acls);

    return 0;
}

static PyObject *t_item_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_item *self = (t_item *) type->tp_alloc(type, 0);

    if (self)
    {
        self->lastAccess = 0;
        self->status = RAW;
        self->version = 0;
        self->uuid = NULL;
        self->name = NULL;
        self->values = NULL;
        self->references = NULL;
        self->kind = NULL;
        self->parent = NULL;
        self->children = NULL;
        self->root = NULL;
        self->acls = NULL;
    }

    return (PyObject *) self;
}

static int t_item_init(t_item *self, PyObject *args, PyObject *kwds)
{
    self->status = NEW;

    return 0;
}

static PyObject *t_item_isNew(t_item *self, PyObject *args)
{
    if (self->status & NEW)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isDeleting(t_item *self, PyObject *args)
{
    if (self->status & DELETING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isDeleted(t_item *self, PyObject *args)
{
    if (self->status & DELETED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isStale(t_item *self, PyObject *args)
{
    if (self->status & STALE)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isPinned(t_item *self, PyObject *args)
{
    if (self->status & PINNED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isSchema(t_item *self, PyObject *args)
{
    if (self->status & SCHEMA)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isDirty(t_item *self, PyObject *args)
{
    if (self->status & DIRTY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_getDirty(t_item *self, PyObject *args)
{
    return PyInt_FromLong(self->status & DIRTY);
}

static PyObject *t_item__isNDirty(t_item *self, PyObject *args)
{
    if (self->status & NDIRTY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isNoDirty(t_item *self, PyObject *args)
{
    if (self->status & NODIRTY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isCopyExport(t_item *self, PyObject *args)
{
    if (self->status & COPYEXPORT)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isImporting(t_item *self, PyObject *args)
{
    if (self->status & IMPORTING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isRepository(t_item *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isView(t_item *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isItem(t_item *self, PyObject *args)
{
    if (PyObject_TypeCheck(self, &ItemType))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_item__isRefList(t_item *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isUUID(t_item *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isMerged(t_item *self, PyObject *args)
{
    if (self->status & MERGED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_getAttributeAspect(t_item *self, PyObject *args)
{
    PyObject *name, *aspect;
    PyObject *noError = Py_False;
    PyObject *attrID = Py_None;
    PyObject *defaultValue = Default;

    if (!PyArg_ParseTuple(args, "OO|OOO", &name, &aspect,
                          &noError, &attrID, &defaultValue))
        return NULL;

    if (self->kind != Py_None)
    {
        PyObject *descriptor = PyObject_GetAttr((PyObject *) self->ob_type,
                                                name);
        PyObject *attribute;

        if (descriptor)
        {
            if (PyObject_TypeCheck(descriptor, CDescriptor))
            {
                PyObject *attr =
                    PyDict_GetItem(((t_descriptor *) descriptor)->attrs,
                                   ((t_item *) self->kind)->uuid);

                if (attr)
                {
                    PyObject *value = PyObject_GetAttr(attr, aspect);

                    if (value)
                    {
                        Py_DECREF(descriptor);
                        Py_INCREF(value);

                        return value;
                    }
                    else
                        PyErr_Clear();

                    attrID = ((t_attribute *) attr)->attrID;
                }
            }

            Py_DECREF(descriptor);
        }
        else
            PyErr_Clear();

        if (attrID != Py_None)
        {
            PyObject *view = ((t_item *) self->root)->parent;
            attribute = PyObject_CallMethodObjArgs(view, find_NAME,
                                                   attrID, NULL);
        }
        else
            attribute = PyObject_CallMethodObjArgs(self->kind,
                                                   getAttribute_NAME,
                                                   name, noError,
                                                   self, NULL);

        if (!attribute)
            return NULL;

        if (attribute != Py_None)
        {
            if (PyObject_Compare(aspect, redirectTo_NAME))
            {
                PyObject *redirect =
                    PyObject_CallMethodObjArgs(attribute, getAspect_NAME,
                                               redirectTo_NAME, Py_None, NULL);

                if (!redirect)
                {
                    Py_DECREF(attribute);
                    return NULL;
                }

                if (redirect != Py_None)
                {
                    PyObject *value =
                        PyObject_CallMethodObjArgs((PyObject *) self,
                                                   _redirectTo_NAME, redirect,
                                                   getAttributeAspect_NAME,
                                                   aspect, noError, Py_None,
                                                   defaultValue, NULL);

                    Py_DECREF(attribute);
                    Py_DECREF(redirect);

                    return value;
                }

                Py_DECREF(redirect);
            }

            {
                PyObject *value =
                    PyObject_CallMethodObjArgs(attribute, getAspect_NAME,
                                               aspect, defaultValue, NULL);

                Py_DECREF(attribute);
                return value;
            }
        }
        
        Py_DECREF(attribute);
    }

    if (defaultValue == Default)
        defaultValue = Py_None;

    Py_INCREF(defaultValue);
    return defaultValue;
}


/* itsKind */

static PyObject *t_item__getKind(t_item *self, void *data)
{
    PyObject *kind = self->kind;

    if (kind != Py_None && ((t_item *) kind)->status & STALE)
    {
        PyObject *view = ((t_item *) self->root)->parent;
        PyObject *uuid = ((t_item *) kind)->uuid;

        Py_DECREF(kind);
        self->kind = kind = PyObject_GetItem(view, uuid);
    }

    Py_INCREF(kind);
    return kind;
}

static int t_item__setKind(t_item *self, PyObject *kind, void *data)
{
    if (!PyObject_CallMethodObjArgs((PyObject *) self, _setKind_NAME,
                                    kind, NULL))
        return -1;

    return 0;
}


/* itsView */

static PyObject *t_item__getView(t_item *self, void *data)
{
    PyObject *root = self->root;
    PyObject *view;

    if (root != Py_None)
        view = ((t_item *) root)->parent;
    else
        view = Py_None;

    Py_INCREF(view);
    return view;
}

static int t_item__setView(t_item *self, PyObject *view, void *data)
{
    if (!PyObject_CallMethodObjArgs(view, importItem_NAME,
                                    (PyObject *) self, NULL))
        return -1;

    return 0;
}


/* itsParent */

static PyObject *t_item__getParent(t_item *self, void *data)
{
    PyObject *parent = self->parent;

    if (parent != Py_None && ((t_item *) parent)->status & STALE)
    {
        PyObject *view = ((t_item *) self->root)->parent;
        PyObject *uuid = ((t_item *) parent)->uuid;

        Py_DECREF(parent);
        self->parent = parent = PyObject_GetItem(view, uuid);
    }

    Py_INCREF(parent);
    return parent;
}

static int t_item__setParent(t_item *self, PyObject *parent, void *data)
{
    if (!PyObject_CallMethodObjArgs((PyObject *) self, move_NAME, parent, NULL))
        return -1;

    return 0;
}


/* itsName */

static PyObject *t_item__getName(t_item *self, void *data)
{
    PyObject *name = self->name;

    Py_INCREF(name);
    return name;
}

static int t_item__setName(t_item *self, PyObject *name, void *data)
{
    if (!PyObject_CallMethodObjArgs((PyObject *) self, rename_NAME, name, NULL))
        return -1;

    return 0;
}


/* itsRoot */

static PyObject *t_item__getRoot(t_item *self, void *data)
{
    PyObject *root = self->root;

    if (root != Py_None && ((t_item *) root)->status & STALE)
    {
        PyObject *view = ((t_item *) root)->parent;
        PyObject *uuid = ((t_item *) root)->uuid;

        Py_DECREF(root);
        self->root = root = PyObject_GetItem(view, uuid);
    }

    Py_INCREF(root);
    return root;
}


/* itsUUID */

static PyObject *t_item__getUUID(t_item *self, void *data)
{
    PyObject *uuid = self->uuid;

    Py_INCREF(uuid);
    return uuid;
}


/* itsPath */

static PyObject *t_item__getPath(t_item *self, void *data)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, _getPath_NAME, NULL);
}


/* itsVersion */

static PyObject *t_item__getVersion(t_item *self, void *data)
{
    return PyInt_FromLong(self->version);
}


typedef struct {
    PyObject_HEAD
} t_nil;

static int t_nil_length(t_nil *self)
{
    return 0;
}

static PySequenceMethods nil_as_sequence = {
    (inquiry) t_nil_length,             /* sq_length */
    0,                                  /* sq_concat */
    0,					/* sq_repeat */
    0,                                  /* sq_item */
    0,                                  /* sq_slice */
    0,                                  /* sq_ass_item */
    0,                                  /* sq_ass_slice */
    0,                                  /* sq_contains */
};

static PyTypeObject NilType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.c.Nil",                   /* tp_name */
    sizeof(t_nil),                             /* tp_basicsize */
    0,                                         /* tp_itemsize */
    0,                                         /* tp_dealloc */
    0,                                         /* tp_print */
    0,                                         /* tp_getattr */
    0,                                         /* tp_setattr */
    0,                                         /* tp_compare */
    0,                                         /* tp_repr */
    0,                                         /* tp_as_number */
    &nil_as_sequence,                          /* tp_as_sequence */
    0,                                         /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    0,                                         /* tp_str */
    0,                                         /* tp_getattro */
    0,                                         /* tp_setattro */
    0,                                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                        /* tp_flags */
    "Nil type",                                /* tp_doc */
    0,                                         /* tp_traverse */
    0,                                         /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    0,                                         /* tp_iter */
    0,                                         /* tp_iternext */
    0,                                         /* tp_methods */
    0,                                         /* tp_members */
    0,                                         /* tp_getset */
    0,                                         /* tp_base */
    0,                                         /* tp_dict */
    0,                                         /* tp_descr_get */
    0,                                         /* tp_descr_set */
    0,                                         /* tp_dictoffset */
    0,                                         /* tp_init */
    0,                                         /* tp_alloc */
    0,                                         /* tp_new */
};


void _init_item(PyObject *m)
{
    if (PyType_Ready(&ItemType) >= 0 && PyType_Ready(&NilType) >= 0)
    {
        if (m)
        {
            PyObject *dict = ItemType.tp_dict;

            Py_INCREF(&ItemType);
            PyModule_AddObject(m, "CItem", (PyObject *) &ItemType);
            CItem = &ItemType;

            Nil = (PyObject *) PyObject_New(t_nil, &NilType);
            Default = (PyObject *) PyObject_New(t_nil, &NilType);

            PyModule_AddObject(m, "Nil", Nil);
            PyModule_AddObject(m, "Default", Default);

            PyDict_SetItemString_Int(dict, "DELETED", DELETED);
            PyDict_SetItemString_Int(dict, "VDIRTY", VDIRTY);
            PyDict_SetItemString_Int(dict, "DELETING", DELETING);
            PyDict_SetItemString_Int(dict, "RAW", RAW);
            PyDict_SetItemString_Int(dict, "FDIRTY", FDIRTY);
            PyDict_SetItemString_Int(dict, "SCHEMA", SCHEMA);
            PyDict_SetItemString_Int(dict, "NEW", NEW);
            PyDict_SetItemString_Int(dict, "STALE", STALE);
            PyDict_SetItemString_Int(dict, "NDIRTY", NDIRTY);
            PyDict_SetItemString_Int(dict, "CDIRTY", CDIRTY);
            PyDict_SetItemString_Int(dict, "RDIRTY", RDIRTY);
            PyDict_SetItemString_Int(dict, "CORESCHEMA", CORESCHEMA);
            PyDict_SetItemString_Int(dict, "CONTAINER", CONTAINER);
            PyDict_SetItemString_Int(dict, "ADIRTY", ADIRTY);
            PyDict_SetItemString_Int(dict, "PINNED", PINNED);
            PyDict_SetItemString_Int(dict, "NODIRTY", NODIRTY);
            PyDict_SetItemString_Int(dict, "VMERGED", VMERGED);
            PyDict_SetItemString_Int(dict, "RMERGED", RMERGED);
            PyDict_SetItemString_Int(dict, "NMERGED", NMERGED);
            PyDict_SetItemString_Int(dict, "CMERGED", CMERGED);
            PyDict_SetItemString_Int(dict, "COPYEXPORT", COPYEXPORT);
            PyDict_SetItemString_Int(dict, "IMPORTING", IMPORTING);

            PyDict_SetItemString_Int(dict, "VRDIRTY", VRDIRTY);
            PyDict_SetItemString_Int(dict, "DIRTY", DIRTY);
            PyDict_SetItemString_Int(dict, "MERGED", MERGED);
            PyDict_SetItemString_Int(dict, "SAVEMASK", SAVEMASK);

            _setKind_NAME = PyString_FromString("_setKind");
            importItem_NAME = PyString_FromString("importItem");
            move_NAME = PyString_FromString("move");
            rename_NAME = PyString_FromString("rename");
            _getPath_NAME = PyString_FromString("_getPath");
            find_NAME = PyString_FromString("find");
            getAttribute_NAME = PyString_FromString("getAttribute");
            getAspect_NAME = PyString_FromString("getAspect");
            getAttributeAspect_NAME = PyString_FromString("getAttributeAspect");
            redirectTo_NAME = PyString_FromString("redirectTo");
            _redirectTo_NAME = PyString_FromString("_redirectTo");
        }
    }
}
