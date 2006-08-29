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
#include "structmember.h"

#include "c.h"
#include "../util/singleref.h"
#include "../schema/kind.h"
#include "../schema/descriptor.h"

static void t_item_dealloc(t_item *self);
static int t_item_traverse(t_item *self, visitproc visit, void *arg);
static int t_item_clear(t_item *self);
static PyObject *t_item_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_item_init(t_item *self, PyObject *args, PyObject *kwds);
static PyObject *t_item_repr(t_item *self);
static PyObject *t_item_isNew(t_item *self);
static PyObject *t_item_isDeleting(t_item *self);
static PyObject *t_item_isDeleted(t_item *self);
static PyObject *t_item_isDeferring(t_item *self);
static PyObject *t_item_isDeferred(t_item *self);
static PyObject *t_item_isStale(t_item *self);
static PyObject *t_item_isPinned(t_item *self);
static PyObject *t_item_isSchema(t_item *self);
static PyObject *t_item_isDirty(t_item *self);
static PyObject *t_item_getDirty(t_item *self, PyObject *args);
static PyObject *t_item__isNDirty(t_item *self);
static PyObject *t_item__isKDirty(t_item *self);
static PyObject *t_item__isNoDirty(t_item *self);
static PyObject *t_item__isCopyExport(t_item *self);
static PyObject *t_item__isImporting(t_item *self);
static PyObject *t_item_isMutating(t_item *self);
static PyObject *t_item__isRepository(t_item *self);
static PyObject *t_item__isView(t_item *self);
static PyObject *t_item__isItem(t_item *self);
static PyObject *t_item__isRefs(t_item *self);
static PyObject *t_item__isUUID(t_item *self);
static PyObject *t_item__isMerged(t_item *self);
static PyObject *t_item_isWatched(t_item *self);
static PyObject *t_item_getAttributeAspect(t_item *self, PyObject *args);
static PyObject *t_item_hasLocalAttributeValue(t_item *self, PyObject *args);
static PyObject *t_item_hasTrueAttributeValue(t_item *self, PyObject *args);
static PyObject *t_item__fireChanges(t_item *self, PyObject *args);
static PyObject *t_item__fillItem(t_item *self, PyObject *args);
static PyObject *t_item_setDirty(t_item *self, PyObject *args);
static PyObject *t_item__collectionChanged(t_item *self, PyObject *args);
static int _t_item__itemChanged(t_item *self, PyObject *op, PyObject *names);
static PyObject *t_item__itemChanged(t_item *self, PyObject *args);
static PyObject *t_item__getKind(t_item *self, void *data);
static int t_item__setKind(t_item *self, PyObject *kind, void *data);
static PyObject *t_item__getView(t_item *self, void *data);
static int t_item__setView(t_item *self, PyObject *view, void *data);
static PyObject *t_item__getParent(t_item *self, void *data);
static int t_item__setParent(t_item *self, PyObject *parent, void *data);
static PyObject *t_item__getName(t_item *self, void *data);
static int t_item__setName(t_item *self, PyObject *name, void *data);
static PyObject *t_item__getRoot(t_item *self, void *data);
static PyObject *t_item__getUUID(t_item *self, void *data);
static PyObject *t_item__getPath(t_item *self, void *data);
static PyObject *t_item__getVersion(t_item *self, void *data);
static int t_item__setVersion(t_item *self, PyObject *value, void *data);

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
static PyObject *persisted_NAME;
static PyObject *_redirectTo_NAME;
static PyObject *logger_NAME;
static PyObject *_verifyAssignment_NAME;
static PyObject *_setDirty_NAME;
static PyObject *set_NAME, *remove_NAME;
static PyObject *item_NAME;
static PyObject *_logItem_NAME;
static PyObject *_clearDirties_NAME;
static PyObject *_flags_NAME;
static PyObject *watchers_NAME;
static PyObject *filterItem_NAME;
static PyObject *_setParent_NAME;
static PyObject *_setItem_NAME;
static PyObject *c_NAME;
static PyObject *getAttributeValue_NAME;

/* NULL docstrings are set in chandlerdb/__init__.py
 * "" docstrings are missing docstrings
 */

static PyMemberDef t_item_members[] = {
    { "_status", T_UINT, offsetof(t_item, status), 0, "item status flags" },
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
    { "isDeferring", (PyCFunction) t_item_isDeferring, METH_NOARGS, NULL },
    { "isDeferred", (PyCFunction) t_item_isDeferred, METH_NOARGS, NULL },
    { "isStale", (PyCFunction) t_item_isStale, METH_NOARGS, NULL },
    { "isPinned", (PyCFunction) t_item_isPinned, METH_NOARGS, NULL },
    { "isSchema", (PyCFunction) t_item_isSchema, METH_NOARGS, "" },
    { "isDirty", (PyCFunction) t_item_isDirty, METH_NOARGS, NULL },
    { "getDirty", (PyCFunction) t_item_getDirty, METH_NOARGS, NULL },
    { "_isNDirty", (PyCFunction) t_item__isNDirty, METH_NOARGS, "" },
    { "_isKDirty", (PyCFunction) t_item__isKDirty, METH_NOARGS, "" },
    { "_isNoDirty", (PyCFunction) t_item__isNoDirty, METH_NOARGS, "" },
    { "_isCopyExport", (PyCFunction) t_item__isCopyExport, METH_NOARGS, "" },
    { "_isImporting", (PyCFunction) t_item__isImporting, METH_NOARGS, "" },
    { "isMutating", (PyCFunction) t_item_isMutating, METH_NOARGS, NULL },
    { "_isRepository", (PyCFunction) t_item__isRepository, METH_NOARGS, "" },
    { "_isView", (PyCFunction) t_item__isView, METH_NOARGS, "" },
    { "_isItem", (PyCFunction) t_item__isItem, METH_NOARGS, "" },
    { "_isRefs", (PyCFunction) t_item__isRefs, METH_NOARGS, "" },
    { "_isUUID", (PyCFunction) t_item__isUUID, METH_NOARGS, "" },
    { "_isMerged", (PyCFunction) t_item__isMerged, METH_NOARGS, "" },
    { "isWatched", (PyCFunction) t_item_isWatched, METH_NOARGS, "" },
    { "getAttributeAspect", (PyCFunction) t_item_getAttributeAspect, METH_VARARGS, NULL },
    { "hasLocalAttributeValue", (PyCFunction) t_item_hasLocalAttributeValue, METH_VARARGS, NULL },
    { "hasTrueAttributeValue", (PyCFunction) t_item_hasTrueAttributeValue, METH_VARARGS, NULL },
    { "_fireChanges", (PyCFunction) t_item__fireChanges, METH_VARARGS, "" },
    { "_fillItem", (PyCFunction) t_item__fillItem, METH_VARARGS, "" },
    { "setDirty", (PyCFunction) t_item_setDirty, METH_VARARGS, NULL },
    { "_collectionChanged", (PyCFunction) t_item__collectionChanged, METH_VARARGS, NULL },
    { "_itemChanged", (PyCFunction) t_item__itemChanged, METH_VARARGS, NULL },
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
    { "_version", (getter) t_item__getVersion, (setter) t_item__setVersion,
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
    (reprfunc)t_item_repr,                     /* tp_repr */
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
    Py_VISIT((PyObject *) self->values);
    Py_VISIT((PyObject *) self->references);
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

static PyObject *t_item_repr(t_item *self)
{
    if (self->status & RAW)
        return PyString_FromFormat("<raw item at %p>", self);
    else
    {
        PyObject *name, *uuid, *type, *repr;
        char *status;

        if (self->status & DELETED)
            status = " (deleted)";
        else if (self->status & DEFERRED)
            status = " (deferred)";
        else if (self->status & STALE)
            status = " (stale)";
        else if (self->status & NEW)
            status = " (new)";
        else
            status = "";

        if (self->name != Py_None)
            name = PyObject_Str(self->name);
        else
            name = NULL;

        type = PyObject_GetAttrString((PyObject *) self->ob_type, "__name__");
        uuid = PyObject_Str(self->uuid);
        
        repr = PyString_FromFormat("<%s%s:%s%s %s>",
                                   PyString_AsString(type),
                                   status,
                                   name ? " " : "",
                                   name ? PyString_AsString(name) : "",
                                   PyString_AsString(uuid));

        Py_DECREF(type);
        Py_XDECREF(name);
        Py_DECREF(uuid);

        return repr;
    }
}

static PyObject *t_item_isNew(t_item *self)
{
    if (self->status & NEW)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isDeleting(t_item *self)
{
    if (self->status & DELETING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isDeleted(t_item *self)
{
    if (self->status & DELETED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isDeferring(t_item *self)
{
    if (self->status & DEFERRING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isDeferred(t_item *self)
{
    if (self->status & DEFERRED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isStale(t_item *self)
{
    if (self->status & STALE)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}
    
static PyObject *t_item_isPinned(t_item *self)
{
    if (self->status & PINNED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isSchema(t_item *self)
{
    if (self->status & SCHEMA)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isDirty(t_item *self)
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

static PyObject *t_item__isNDirty(t_item *self)
{
    if (self->status & NDIRTY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isKDirty(t_item *self)
{
    if (self->status & KDIRTY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isNoDirty(t_item *self)
{
    if (self->status & NODIRTY)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isCopyExport(t_item *self)
{
    if (self->status & COPYEXPORT)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isImporting(t_item *self)
{
    if (self->status & IMPORTING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isMutating(t_item *self)
{
    if (self->status & MUTATING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isRepository(t_item *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isView(t_item *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isItem(t_item *self)
{
    if (PyObject_TypeCheck(self, &ItemType))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static PyObject *t_item__isRefs(t_item *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isUUID(t_item *self)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isMerged(t_item *self)
{
    if (self->status & MERGED)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isWatched(t_item *self)
{
    if (self->status & WATCHED)
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

static PyObject *t_item_hasLocalAttributeValue(t_item *self, PyObject *args)
{
    PyObject *name, *attrDict = NULL;

    if (!PyArg_ParseTuple(args, "O|O", &name, &attrDict))
        return NULL;
    
    if (attrDict != NULL && attrDict != Py_None)
    {
        if (!PyObject_TypeCheck(attrDict, CValues))
        {
            PyErr_SetObject(PyExc_TypeError, attrDict);
            return NULL;
        }

        if (PyDict_Contains(((t_values *) attrDict)->dict, name))
            Py_RETURN_TRUE;

        Py_RETURN_FALSE;
    }

    if (PyDict_Contains(((t_values *) self->values)->dict, name) ||
        PyDict_Contains(((t_values *) self->references)->dict, name))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int get_attr_flags(t_item *item, PyObject *name, PyObject *uuid,
                          t_attribute **attr, int *flags)
{
    PyObject *descriptor = PyObject_GetAttr((PyObject *) item->ob_type, name);
    PyObject *obj;

    if (descriptor == NULL)
    {
        PyErr_Clear();
        return 0;
    }
        
    if (!PyObject_TypeCheck(descriptor, CDescriptor))
    {
        PyErr_SetObject(PyExc_TypeError, descriptor);
        Py_DECREF(descriptor);
        return -1;
    }

    obj = PyDict_GetItem(((t_descriptor *) descriptor)->attrs, uuid);
    Py_DECREF(descriptor);

    if (obj)
    {
        if (!PyObject_TypeCheck(obj, CAttribute))
        {
            PyErr_SetObject(PyExc_TypeError, obj);
            return -1;
        }

        *attr = (t_attribute *) obj;
        *flags = (*attr)->flags;
    }

    return 0;
}

static PyObject *t_item_hasTrueAttributeValue(t_item *self, PyObject *args)
{
    PyObject *kind = self->kind;

    if (kind != Py_None)
    {
        PyObject *value, *name, *attrDict = Py_None;
        PyObject *uuid = ((t_item *) kind)->uuid;
        int attributesCached;

        if (!PyArg_ParseTuple(args, "O|O", &name, &attrDict))
            return NULL;

        kind = PyObject_GetAttr(kind, c_NAME);
        if (kind == NULL)
            return NULL;
        if (!PyObject_TypeCheck(kind, CKind))
        {
            PyErr_SetObject(PyExc_TypeError, kind);
            Py_DECREF(kind);
            return NULL;
        }

        attributesCached = ((t_kind *) kind)->flags & ATTRIBUTES_CACHED;
        Py_DECREF(kind);

        if (attributesCached)
        {
            t_attribute *attr = NULL;
            int flags = 0;

            if (attrDict == Py_None)
            {
                if (get_attr_flags(self, name, uuid, &attr, &flags) < 0)
                    return NULL;
                if (attr == NULL)
                    Py_RETURN_FALSE;

                switch (flags & ATTRDICT) {
                  case VALUE:
                    attrDict = (PyObject *) self->values;
                    break;
                  case REF:
                    attrDict = (PyObject *) self->references;
                    break;
                }
            }

            if (attrDict != Py_None)
            {
                value = PyDict_GetItem(((t_values *) attrDict)->dict, name);
                if (value != NULL)
                {
                    if (PyObject_TypeCheck(value, CItem) ||
                        PyObject_IsTrue(value))
                        Py_RETURN_TRUE;

                    Py_RETURN_FALSE;
                }
            }

            if (attr == NULL)
            {
                if (get_attr_flags(self, name, uuid, &attr, &flags) < 0)
                    return NULL;
                if (attr == NULL)
                    Py_RETURN_FALSE;
            }

            if (flags & NOINHERIT)
            {
                if (flags & DEFAULT)
                {
                    value = attr->defaultValue;
                    if (PyObject_TypeCheck(value, CItem) ||
                        PyObject_IsTrue(value))
                        Py_RETURN_TRUE;
                }

                Py_RETURN_FALSE;
            }
        }

        /* value is inherited, redirected or schema isn't yet cached */
        value = PyObject_CallMethodObjArgs((PyObject *) self,
                                           getAttributeValue_NAME,
                                           name, attrDict, Py_None, NULL);
        if (value == NULL)
        {
            PyErr_Clear();
            Py_RETURN_FALSE;
        }

        if (PyObject_TypeCheck(value, CItem) || PyObject_IsTrue(value))
            Py_RETURN_TRUE;
    }

    Py_RETURN_FALSE;
}

static PyObject *_t_item__fireChanges(t_item *self,
                                      PyObject *op, PyObject *name)
{
    if (self->kind != Py_None)
    {
        PyObject *attribute =
            PyObject_CallMethodObjArgs(self->kind, getAttribute_NAME,
                                       name, Py_False, self, NULL);

        if (attribute)
        {
            PyObject *c = PyObject_GetAttr(attribute, c_NAME);

            Py_DECREF(attribute);
            if (!c)
                return NULL;

            if (!PyObject_TypeCheck(c, CAttribute))
            {
                PyErr_SetObject(PyExc_TypeError, c);
                Py_DECREF(c);
                return NULL;
            }

            if (CAttribute_invokeAfterChange((t_attribute *) c,
                                             (PyObject *) self, op, name) < 0)
            {
                Py_DECREF(c);
                return NULL;
            }

            Py_DECREF(c);
        }
        else
            return NULL;
    }

    {
        PyObject *args = PyTuple_Pack(3, op, self, name);
        t_view *view = (t_view *) ((t_item *) self->root)->parent;
        PyObject *result = CView_invokeMonitors(view, args);

        Py_DECREF(args);
        if (result == NULL)
            return NULL;

        Py_DECREF(result);
    }

    if (self->status & WATCHED)
    {
        PyObject *names = PyTuple_Pack(1, name);
        int result = _t_item__itemChanged(self, op, names);

        Py_DECREF(names);
        if (result < 0)
            return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *t_item__fireChanges(t_item *self, PyObject *args)
{
    PyObject *op, *name;

    if (!PyArg_ParseTuple(args, "OO", &op, &name))
        return NULL;

    return _t_item__fireChanges(self, op, name);
}

static PyObject *t_item__fillItem(t_item *self, PyObject *args)
{
    PyObject *name, *parent, *kind, *uuid, *values, *references, *hooks;
    int status, update;
    unsigned long long version;

    if (!PyArg_ParseTuple(args, "OOOOOOiK|Oi", &name, &parent, &kind,
                          &uuid, &values, &references, &status, &version,
                          &hooks, &update))
        return NULL;

    self->version = version;
    if (!version)
        status |= NEW;

    self->status = status;

    Py_INCREF(uuid); Py_XDECREF(self->uuid);
    self->uuid = uuid;

    if (!PyObject_TypeCheck(values, CValues))
    {
        PyErr_SetObject(PyExc_TypeError, values);
        return NULL;
    }
    Py_INCREF(values); Py_XDECREF(self->values);
    self->values = (t_values *) values;

    if (!PyObject_TypeCheck(references, CValues))
    {
        PyErr_SetObject(PyExc_TypeError, references);
        return NULL;
    }
    Py_INCREF(references); Py_XDECREF(self->references);
    self->references = (t_values *) references;

    if (name != Py_None && !PyObject_IsTrue(name))
        name = Py_None;
    Py_INCREF(name); Py_XDECREF(self->name);
    self->name = name;

    Py_INCREF(kind); Py_XDECREF(self->kind);
    self->kind = kind;
        
    if (!PyObject_CallMethodObjArgs((PyObject *) self,
                                    _setParent_NAME, parent, NULL) ||
        !PyObject_CallMethodObjArgs(values, _setItem_NAME, self, NULL) ||
        !PyObject_CallMethodObjArgs(references, _setItem_NAME, self, NULL))
        return NULL;

    if (self->parent == Py_None || ((t_item *) self->parent)->status & STALE)
    {
        PyErr_SetString(PyExc_AssertionError, "stale or None parent");
        return NULL;
    }

    if (self->root == Py_None || ((t_item *) self->root)->status & STALE)
    {
        PyErr_SetString(PyExc_AssertionError, "stale or None root");
        return NULL;
    }

    Py_RETURN_NONE;
}

static int verify(t_item *self, t_view *view,
                  t_values *attrDict, PyObject *attribute)
{
    PyObject *value = PyDict_GetItem(attrDict->dict, attribute);
                
    if (value != NULL)
    {
        PyObject *logger = PyObject_GetAttr((PyObject *) view, logger_NAME);
        PyObject *verified =
            PyObject_CallMethodObjArgs((PyObject *) attrDict,
                                       _verifyAssignment_NAME,
                                       attribute, value, logger, NULL);

        Py_DECREF(logger);
        if (verified == NULL)
            return -1;

        if (verified == Py_False)
        {
            PyObject *msgValue = PyObject_Repr(value);
            PyObject *msgAttr = PyObject_Str(attribute);
            PyObject *msgItem = t_item_repr(self);
                                                
            PyErr_Format(PyExc_ValueError, "Assigning %s to attribute '%s' on %s didn't match schema",
                         PyString_AsString(msgValue),
                         PyString_AsString(msgAttr),
                         PyString_AsString(msgItem));

            Py_DECREF(msgValue);
            Py_DECREF(msgAttr);
            Py_DECREF(msgItem);
            Py_DECREF(verified);

            return -1;
        }

        Py_DECREF(verified);
        return 0;
    }

    return 0;
}

static PyObject *t_item_setDirty(t_item *self, PyObject *args)
{
    PyObject *attribute = Py_None, *result;
    t_values *attrDict = NULL;
    int dirty, noMonitors = 0, transient = 0;

    if (self->status & NODIRTY)
        Py_RETURN_FALSE;

    if (!PyArg_ParseTuple(args, "i|OOi", &dirty,
                          &attribute, &attrDict, &noMonitors))
        return NULL;

    if (dirty)
    {
        t_view *view = (t_view *) ((t_item *) self->root)->parent;

        if (dirty & VRDIRTY)
        {
            if (attribute == Py_None)
            {
                PyErr_SetString(PyExc_ValueError, "attribute is None");
                return NULL;
            }
            if (attrDict == NULL)
            {
                PyErr_SetString(PyExc_ValueError, "attrDict is missing");
                return NULL;
            }
            if (!PyObject_TypeCheck(attrDict, CValues))
            {
                PyErr_SetString(PyExc_TypeError, "attrDict is not a Values");
                return NULL;
            }

            if (view->status & VERIFY && dirty & VDIRTY &&
                verify(self, view, attrDict, attribute) < 0)
                return NULL;
            else
            {
                PyObject *args = PyTuple_Pack(5, attribute, persisted_NAME,
                                              Py_True, Py_None, Py_True);

                result = t_item_getAttributeAspect(self, args);
                Py_DECREF(args);
                if (result == NULL)
                    return NULL;

                transient = result == Py_False;
                Py_DECREF(result);
            }

            if (!transient)
            {
                result = t_values__setDirty(attrDict, attribute);
                Py_DECREF(result);
            }

            if (!noMonitors)
            {
                result = _t_item__fireChanges(self, set_NAME, attribute);
                if (result == NULL)
                    return NULL;
                Py_DECREF(result);
            }
        }

        result = _countAccess(NULL, (PyObject *) self);
        Py_DECREF(result);

        if (!transient)
        {
            dirty |= FDIRTY;
            view->status |= FDIRTY;
            
            if (!(self->status & DIRTY))
            {
                if (!(view->status & LOADING))
                {
                    result =
                        PyObject_CallMethodObjArgs((PyObject *) view,
                                                   _logItem_NAME, self, NULL);
                    if (!result)
                        return NULL;

                    if (PyObject_IsTrue(result))
                    {
                        self->status |= dirty;
                        return result;
                    }
                }
            }
            else
                self->status |= dirty;
        }
    }
    else
    {
        self->status &= ~(DIRTY | ADIRTY | FDIRTY);

        result = PyObject_CallMethodObjArgs((PyObject *) self->values,
                                            _clearDirties_NAME, NULL); 
        if (result == NULL)
            return NULL;
        Py_DECREF(result);

        result = PyObject_CallMethodObjArgs((PyObject *) self->references,
                                            _clearDirties_NAME, NULL);
        if (result == NULL)
            return NULL;
        Py_DECREF(result);

        if (self->children != NULL && self->children != Py_None)
        {
            result = PyObject_CallMethodObjArgs(self->children,
                                                _clearDirties_NAME, NULL);
            if (result == NULL)
                return NULL;
            Py_DECREF(result);
        }
    }

    Py_RETURN_FALSE;
}

static int invokeWatchers(PyObject *dispatch, PyObject *name,
                          PyObject *op, PyObject *change,
                          PyObject *item, PyObject *other)
{
    PyObject *watchers = PyObject_GetItem(dispatch, name);

    if (watchers)
    {
        PyObject *iter = PyObject_GetIter(watchers);
        Py_DECREF(watchers);

        if (iter)
        {
            PyObject *watcher;

            while ((watcher = PyIter_Next(iter))) {
                PyObject *args = PyTuple_Pack(5, op, change, item, name, other);
                PyObject *obj = PyObject_Call(watcher, args, NULL);

                Py_DECREF(args);
                Py_DECREF(watcher);
                if (!obj)
                    break;
                Py_DECREF(obj);
            }
            Py_DECREF(iter);

            if (PyErr_Occurred())
                return -1;
        }

        return 0;
    }

    return -1;
}

static PyObject *t_item__collectionChanged(t_item *self, PyObject *args)
{
    PyObject *op, *change, *name, *other, *dispatch;
    t_view *view = (t_view *) ((t_item *) self->root)->parent;

    if (self->status & NODIRTY)
        Py_RETURN_NONE;

    if (!PyArg_ParseTuple(args, "OOOO", &op, &change, &name, &other))
        return NULL;

    dispatch = PyDict_GetItem(self->references->dict, watchers_NAME);
    if (dispatch && PySequence_Contains(dispatch, name))
        if (invokeWatchers(dispatch, name, op, change,
                           (PyObject *) self, other) < 0)
            return NULL;

    if (view->watchers)
    {
        dispatch = PyDict_GetItem(view->watchers, self->uuid);

        if (dispatch && PySequence_Contains(dispatch, name))
            if (invokeWatchers(dispatch, name, op, change,
                               (PyObject *) self, other) < 0)
                return NULL;
    }

    Py_RETURN_NONE;
}

static int invokeItemWatchers(PyObject *dispatch, PyObject *uItem,
                              PyObject *op, PyObject *names)
{
    PyObject *watchers = PyObject_GetItem(dispatch, uItem);

    if (watchers)
    {
        PyObject *iter = PyObject_GetIter(watchers);
        Py_DECREF(watchers);

        if (iter)
        {
            PyObject *watcher;

            while ((watcher = PyIter_Next(iter))) {
                PyObject *args = PyTuple_Pack(3, op, uItem, names);
                PyObject *obj = PyObject_Call(watcher, args, NULL);

                Py_DECREF(args);
                Py_DECREF(watcher);
                if (!obj)
                    break;
                Py_DECREF(obj);
            }
            Py_DECREF(iter);

            if (PyErr_Occurred())
                return -1;
        }
    }

    return 0;
}

static int _t_item__itemChanged(t_item *self, PyObject *op, PyObject *names)
{
    if (self->status & NODIRTY)
        return 0;

    if (self->status & P_WATCHED)
    {
        PyObject *dispatch = PyDict_GetItem(self->references->dict,
                                            watchers_NAME);

        if (dispatch && PySequence_Contains(dispatch, self->uuid))
            return invokeItemWatchers(dispatch, self->uuid, op, names);
    }

    if (self->status & T_WATCHED)
    {
        t_view *view = (t_view *) ((t_item *) self->root)->parent;

        if (view->watchers)
        {
            PyObject *dispatch = PyDict_GetItem(view->watchers, self->uuid);

            if (dispatch && PySequence_Contains(dispatch, self->uuid))
                return invokeItemWatchers(dispatch, self->uuid, op, names);
        }
    }

    return 0;
}

static PyObject *t_item__itemChanged(t_item *self, PyObject *args)
{
    PyObject *op, *names;

    if (!PyArg_ParseTuple(args, "OO", &op, &names))
        return NULL;

    if (_t_item__itemChanged(self, op, names) < 0)
        return NULL;

    Py_RETURN_NONE;
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


/* itsVersion, _version */

static PyObject *t_item__getVersion(t_item *self, void *data)
{
    return PyLong_FromUnsignedLongLong(self->version);
}

static int t_item__setVersion(t_item *self, PyObject *value, void *data)
{
    unsigned long long version = PyLong_AsUnsignedLongLong(value);
    
    if (PyErr_Occurred())
        return -1;

    self->version = version;
    
    return 0;
}


void _init_item(PyObject *m)
{
    if (PyType_Ready(&ItemType) >= 0)
    {
        if (m)
        {
            PyObject *dict = ItemType.tp_dict;

            Py_INCREF(&ItemType);
            PyModule_AddObject(m, "CItem", (PyObject *) &ItemType);
            CItem = &ItemType;

            PyDict_SetItemString_Int(dict, "DELETED", DELETED);
            PyDict_SetItemString_Int(dict, "DEFERRED", DEFERRED);
            PyDict_SetItemString_Int(dict, "VDIRTY", VDIRTY);
            PyDict_SetItemString_Int(dict, "DELETING", DELETING);
            PyDict_SetItemString_Int(dict, "DEFERRING", DEFERRING);
            PyDict_SetItemString_Int(dict, "RAW", RAW);
            PyDict_SetItemString_Int(dict, "FDIRTY", FDIRTY);
            PyDict_SetItemString_Int(dict, "SCHEMA", SCHEMA);
            PyDict_SetItemString_Int(dict, "NEW", NEW);
            PyDict_SetItemString_Int(dict, "STALE", STALE);
            PyDict_SetItemString_Int(dict, "NDIRTY", NDIRTY);
            PyDict_SetItemString_Int(dict, "KDIRTY", KDIRTY);
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
            PyDict_SetItemString_Int(dict, "MUTATING", MUTATING);
            PyDict_SetItemString_Int(dict, "P_WATCHED", P_WATCHED);
            PyDict_SetItemString_Int(dict, "T_WATCHED", T_WATCHED);
            PyDict_SetItemString_Int(dict, "TOINDEX", TOINDEX);
            PyDict_SetItemString_Int(dict, "WATCHED", WATCHED);

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
            persisted_NAME = PyString_FromString("persisted");
            _redirectTo_NAME = PyString_FromString("_redirectTo");
            logger_NAME = PyString_FromString("logger");
            _verifyAssignment_NAME = PyString_FromString("_verifyAssignment");
            _setDirty_NAME = PyString_FromString("_setDirty");
            set_NAME = PyString_FromString("set");
            remove_NAME = PyString_FromString("remove");
            item_NAME = PyString_FromString("item");
            _logItem_NAME = PyString_FromString("_logItem");
            _clearDirties_NAME = PyString_FromString("_clearDirties");
            _flags_NAME = PyString_FromString("_flags");
            watchers_NAME = PyString_FromString("watchers");
            filterItem_NAME = PyString_FromString("filterItem");
            _setParent_NAME = PyString_FromString("_setParent");
            _setItem_NAME = PyString_FromString("_setItem");
            c_NAME = PyString_FromString("c");
            getAttributeValue_NAME = PyString_FromString("getAttributeValue");
        }
    }
}
