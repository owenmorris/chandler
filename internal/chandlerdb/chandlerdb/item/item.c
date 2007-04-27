/*
 *  Copyright (c) 2003-2007 Open Source Applications Foundation
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

static void t_item_dealloc(t_item *self);
static int t_item_traverse(t_item *self, visitproc visit, void *arg);
static int t_item_clear(t_item *self);
static PyObject *t_item_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_item_init(t_item *self, PyObject *args, PyObject *kwds);
static PyObject *t_item_getattro(t_item *self, PyObject *name);
static int t_item_setattro(t_item *self, PyObject *name, PyObject *value);
static PyObject *t_item_isNew(t_item *self);
static PyObject *t_item_isDeleting(t_item *self);
static PyObject *t_item_isDeleted(t_item *self);
static PyObject *t_item_isDeferring(t_item *self);
static PyObject *t_item_isDeferred(t_item *self);
static PyObject *t_item_isLive(t_item *self);
static PyObject *t_item_isStale(t_item *self);
static PyObject *t_item_isPinned(t_item *self);
static PyObject *t_item_isSchema(t_item *self);
static PyObject *t_item__isWithSchema(t_item *self);
static PyObject *t_item__isCoreSchema(t_item *self);
static PyObject *t_item_isDirty(t_item *self);
static PyObject *t_item_getDirty(t_item *self, PyObject *args);
static PyObject *t_item__isNDirty(t_item *self);
static PyObject *t_item__isKDirty(t_item *self);
static PyObject *t_item__isNoDirty(t_item *self);
static PyObject *t_item_isMutating(t_item *self);
static PyObject *t_item_isMutatingOrDeleting(t_item *self);
static PyObject *t_item_isDeferringOrDeleting(t_item *self);
static PyObject *t_item__isRefs(t_item *self);
static PyObject *t_item__isMerged(t_item *self);
static PyObject *t_item_isWatched(t_item *self);
static PyObject *t_item_getAttributeAspect(t_item *self, PyObject *args);
static PyObject *t_item_getLocalAttributeValue(t_item *self, PyObject *args);
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
static PyObject *t_item__getParent(t_item *self, void *data);
static int t_item__setParent(t_item *self, PyObject *parent, void *data);
static PyObject *t_item___getParent(t_item *self, void *data);
static int t_item___setParent(t_item *self, PyObject *parent, void *data);
static PyObject *t_item__getName(t_item *self, void *data);
static int t_item__setName(t_item *self, PyObject *name, void *data);
static PyObject *t_item__getRoot(t_item *self, void *data);
static PyObject *t_item__getRef(t_item *self, void *data);
static PyObject *t_item__getUUID(t_item *self, void *data);
static PyObject *t_item__getPath(t_item *self, void *data);
static PyObject *t_item__getStatus(t_item *self, void *data);
static PyObject *t_item__getVersion(t_item *self, void *data);
static int t_item__setVersion(t_item *self, PyObject *value, void *data);
static PyObject *t_item__getValues(t_item *self, void *data);
static PyObject *t_item__getRefs(t_item *self, void *data);
static PyObject *t_item_map_get(t_item *self, PyObject *key);

static PyObject *_setKind_NAME;
static PyObject *move_NAME;
static PyObject *rename_NAME;
static PyObject *_getPath_NAME;
static PyObject *find_NAME;
static PyObject *getAttribute_NAME;
static PyObject *getAspect_NAME;
static PyObject *getAttributeAspect_NAME;
static PyObject *redirectTo_NAME;
static PyObject *_redirectTo_NAME;
static PyObject *logger_NAME;
static PyObject *_verifyAssignment_NAME;
static PyObject *_setDirty_NAME;
static PyObject *set_NAME;
static PyObject *item_NAME;
static PyObject *_logItem_NAME;
static PyObject *_clearDirties_NAME;
static PyObject *_flags_NAME;
static PyObject *watchers_NAME;
static PyObject *filterItem_NAME;
static PyObject *_setItem_NAME;
static PyObject *getAttributeValue_NAME;
static PyObject *_addItem_NAME;
static PyObject *invokeAfterChange_NAME;
static PyObject *getItemChild_NAME;

/* NULL docstrings are set in chandlerdb/__init__.py
 * "" docstrings are missing docstrings
 */

static PyMemberDef t_item_members[] = {
    { "_status", T_UINT, offsetof(t_item, status), 0, "item status flags" },
    { "_lastAccess", T_UINT, offsetof(t_item, lastAccess), 0, "access stamp" },
    { "_name", T_OBJECT, offsetof(t_item, name), 0, "item name" },
    { "_values", T_OBJECT, offsetof(t_item, values), 0, "literals" },
    { "_references", T_OBJECT, offsetof(t_item, references), 0, "references" },
    { "_kind", T_OBJECT, offsetof(t_item, kind), 0, "item kind" },
    { "_children", T_OBJECT, offsetof(t_item, children), 0, "item children" },
    { "_acls", T_OBJECT, offsetof(t_item, acls), 0, "item acls" },
    { "c", T_OBJECT, offsetof(t_item, c), 0, "item c buddy" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_item_methods[] = {
    { "isNew", (PyCFunction) t_item_isNew, METH_NOARGS, NULL },
    { "isDeleting", (PyCFunction) t_item_isDeleting, METH_NOARGS, NULL },
    { "isDeleted", (PyCFunction) t_item_isDeleted, METH_NOARGS, NULL },
    { "isDeferring", (PyCFunction) t_item_isDeferring, METH_NOARGS, NULL },
    { "isDeferred", (PyCFunction) t_item_isDeferred, METH_NOARGS, NULL },
    { "isLive", (PyCFunction) t_item_isLive, METH_NOARGS, NULL },
    { "isStale", (PyCFunction) t_item_isStale, METH_NOARGS, NULL },
    { "isPinned", (PyCFunction) t_item_isPinned, METH_NOARGS, NULL },
    { "isSchema", (PyCFunction) t_item_isSchema, METH_NOARGS, "" },
    { "_isWithSchema", (PyCFunction) t_item__isWithSchema, METH_NOARGS, "" },
    { "_isCoreSchema", (PyCFunction) t_item__isCoreSchema, METH_NOARGS, "" },
    { "isDirty", (PyCFunction) t_item_isDirty, METH_NOARGS, NULL },
    { "getDirty", (PyCFunction) t_item_getDirty, METH_NOARGS, NULL },
    { "_isNDirty", (PyCFunction) t_item__isNDirty, METH_NOARGS, "" },
    { "_isKDirty", (PyCFunction) t_item__isKDirty, METH_NOARGS, "" },
    { "_isNoDirty", (PyCFunction) t_item__isNoDirty, METH_NOARGS, "" },
    { "isMutating", (PyCFunction) t_item_isMutating, METH_NOARGS, NULL },
    { "isMutatingOrDeleting", (PyCFunction) t_item_isMutatingOrDeleting, METH_NOARGS, NULL },
    { "isDeferringOrDeleting", (PyCFunction) t_item_isDeferringOrDeleting, METH_NOARGS, NULL },
    { "_isRefs", (PyCFunction) t_item__isRefs, METH_NOARGS, "" },
    { "_isMerged", (PyCFunction) t_item__isMerged, METH_NOARGS, "" },
    { "isWatched", (PyCFunction) t_item_isWatched, METH_NOARGS, "" },
    { "getAttributeAspect", (PyCFunction) t_item_getAttributeAspect, METH_VARARGS, NULL },
    { "getLocalAttributeValue", (PyCFunction) t_item_getLocalAttributeValue, METH_VARARGS, NULL },
    { "hasLocalAttributeValue", (PyCFunction) t_item_hasLocalAttributeValue, METH_VARARGS, NULL },
    { "hasTrueAttributeValue", (PyCFunction) t_item_hasTrueAttributeValue, METH_VARARGS, NULL },
    { "_fireChanges", (PyCFunction) t_item__fireChanges, METH_VARARGS, "" },
    { "_fillItem", (PyCFunction) t_item__fillItem, METH_VARARGS, "" },
    { "setDirty", (PyCFunction) t_item_setDirty, METH_VARARGS, NULL },
    { "_collectionChanged", (PyCFunction) t_item__collectionChanged, METH_VARARGS, NULL },
    { "_itemChanged", (PyCFunction) t_item__itemChanged, METH_VARARGS, NULL },
    { NULL, NULL, 0, NULL }
};

static PyMappingMethods t_item_as_mapping = {
    0,                                /* mp_length          */
    (binaryfunc)t_item_map_get,       /* mp_subscript       */
    0,                                /* mp_ass_subscript   */
};


static PyGetSetDef t_item_properties[] = {
    { "itsKind", (getter) t_item__getKind, (setter) t_item__setKind,
      NULL, NULL },
    { "itsView", (getter) t_item__getView, NULL,
      NULL, NULL },
    { "itsParent", (getter) t_item__getParent, (setter) t_item__setParent,
      NULL, NULL },
    { "_parent", (getter) t_item___getParent, (setter) t_item___setParent,
      NULL, NULL },
    { "itsName", (getter) t_item__getName, (setter) t_item__setName,
      NULL, NULL },
    { "itsRoot", (getter) t_item__getRoot, NULL,
      NULL, NULL },
    { "itsRef", (getter) t_item__getRef, NULL,
      NULL, NULL },
    { "itsUUID", (getter) t_item__getUUID, NULL,
      NULL, NULL },
    { "_uuid", (getter) t_item__getUUID, NULL,
      NULL, NULL },
    { "itsPath", (getter) t_item__getPath, NULL,
      NULL, NULL },
    { "itsStatus", (getter) t_item__getStatus, NULL,
      NULL, NULL },
    { "itsVersion", (getter) t_item__getVersion, NULL,
      "itsVersion property", NULL },
    { "_version", (getter) t_item__getVersion, (setter) t_item__setVersion,
      "itsVersion property", NULL },
    { "itsValues", (getter) t_item__getValues, NULL,
      NULL, NULL },
    { "itsRefs", (getter) t_item__getRefs, NULL,
      NULL, NULL },
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
    &t_item_as_mapping,                        /* tp_as_mapping */
    0,                                         /* tp_hash  */
    0,                                         /* tp_call */
    0,                                         /* tp_str */
    (getattrofunc)t_item_getattro,             /* tp_getattro */
    (setattrofunc)t_item_setattro,             /* tp_setattro */
    0,                                         /* tp_as_buffer */
    (Py_TPFLAGS_DEFAULT |
     Py_TPFLAGS_BASETYPE |
     Py_TPFLAGS_HAVE_GC),                      /* tp_flags */
    "C Item type",                             /* tp_doc */
    (traverseproc)t_item_traverse,             /* tp_traverse */
    (inquiry)t_item_clear,                     /* tp_clear */
    0,                                         /* tp_richcompare */
    offsetof(t_item, weakrefs),                /* tp_weaklistoffset */
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
    if (self->weakrefs)
        PyObject_ClearWeakRefs((PyObject *) self);

    t_item_clear(self);
    self->ob_type->tp_free((PyObject *) self);

    itemCount -= 1;
}

static int t_item_traverse(t_item *self, visitproc visit, void *arg)
{
    Py_VISIT(self->ref);
    Py_VISIT(self->name);
    Py_VISIT((PyObject *) self->values);
    Py_VISIT((PyObject *) self->references);
    Py_VISIT(self->kind);
    Py_VISIT(self->parentRef);
    Py_VISIT(self->children);
    Py_VISIT(self->acls);
    Py_VISIT(self->c);

    return 0;
}

static int t_item_clear(t_item *self)
{
    if (self->ref && self->ref->item == self)
        self->ref->item = NULL;

    Py_CLEAR(self->ref);
    Py_CLEAR(self->name);
    Py_CLEAR(self->values);
    Py_CLEAR(self->references);
    Py_CLEAR(self->kind);
    Py_CLEAR(self->parentRef);
    Py_CLEAR(self->children);
    Py_CLEAR(self->acls);
    Py_CLEAR(self->c);

    return 0;
}

static PyObject *t_item_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_item *self = (t_item *) type->tp_alloc(type, 0);

    if (self)
    {
        itemCount += 1;

        self->lastAccess = 0;
        self->status = RAW;
        self->version = 0;
        self->ref = NULL;
        self->name = NULL;
        self->values = NULL;
        self->references = NULL;
        self->kind = NULL;
        self->parentRef = NULL;
        self->children = NULL;
        self->acls = NULL;
        self->c = NULL;
    }

    return (PyObject *) self;
}

static int t_item_init(t_item *self, PyObject *args, PyObject *kwds)
{
    PyObject *uuid, *name, *parent, *view;

    if (!PyArg_ParseTuple(args, "OOO", &uuid, &name, &parent))
        return -1;

    if (!PyUUID_Check(uuid))
    {
        PyErr_SetObject(PyExc_TypeError, uuid);
        return -1;
    }

    if (PyObject_TypeCheck(parent, CView))
        view = parent;
    else if (PyObject_TypeCheck(parent, CItem))
        view = ((t_item *) parent)->ref->view;
    else
    {
        PyErr_SetObject(PyExc_TypeError, parent);
        return -1;
    }

    Py_INCREF(name); Py_XDECREF(self->name);
    self->name = name;

    self->ref = _t_itemref_new(uuid, (t_view *) view, self);
    if (!self->ref)
        return -1;

    if (t_item___setParent(self, parent, NULL) < 0)
    {
        PyDict_DelItem(((t_view *) view)->registry, uuid);
        Py_CLEAR(self->ref);
        return -1;
    }

    self->status = NEW;

    return 0;
}

PyObject *t_item_repr(t_item *self)
{
    if (self->status & RAW)
        return PyString_FromFormat("<raw item at %p>", self);
    else
    {
        PyObject *name, *uuid, *type, *repr;
        char *status;

        if (self->status & DELETED)
            status = " (deleted)";
        else if (self->status & DELETING)
            status = " (deleting)";
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
        if (self->ref && self->ref->uuid)
            uuid = PyObject_Str(self->ref->uuid);
        else
            uuid = NULL;
        
        repr = PyString_FromFormat("<%s%s:%s%s %s>",
                                   PyString_AsString(type),
                                   status,
                                   name ? " " : "",
                                   name ? PyString_AsString(name) : "",
                                   uuid ? PyString_AsString(uuid) : "(no ref)");

        Py_DECREF(type);
        Py_XDECREF(name);
        Py_XDECREF(uuid);

        return repr;
    }
}

static PyObject *t_item_map_get(t_item *self, PyObject *key)
{
    PyObject *child =
        PyObject_CallMethodObjArgs((PyObject *) self, getItemChild_NAME,
                                   key, NULL);

    if (child == Py_None)
    {
        Py_DECREF(child);
        PyErr_SetObject(PyExc_KeyError, key);
        return NULL;
    }

    return child;
}

static PyObject *t_item_getattro(t_item *self, PyObject *name)
{
    PyObject *kind = self->kind;

    if (kind != NULL && kind != Py_None)
    {
        t_kind *c = (t_kind *) ((t_item *) kind)->c;

        if (c->flags & DESCRIPTORS_INSTALLED)
        {
            PyObject *dsc = PyDict_GetItem(c->descriptors, name);

            if (dsc)
                return dsc->ob_type->tp_descr_get(dsc, (PyObject *) self, NULL);
        }
    }

    {
        PyObject *value = PyObject_GenericGetAttr((PyObject *) self, name);

        if (!value && self->status & STALE)
        {
            if (PyErr_ExceptionMatches(PyExc_AttributeError))
            {
                PyObject *tuple = PyTuple_Pack(2, self, name);

                PyErr_SetObject((PyObject *) StaleItemAttributeError, tuple);
                Py_DECREF(tuple);
            }
        }

        return value;
    }
}

static int t_item_setattro(t_item *self, PyObject *name, PyObject *value)
{
    PyObject *kind = self->kind;

    if (kind != NULL && kind != Py_None)
    {
        t_kind *c = (t_kind *) ((t_item *) kind)->c;

        if (c->flags & DESCRIPTORS_INSTALLED)
        {
            PyObject *dsc = PyDict_GetItem(c->descriptors, name);

            if (dsc)
                return dsc->ob_type->tp_descr_set(dsc, (PyObject *) self,
                                                  value);
        }
    }

    return PyObject_GenericSetAttr((PyObject *) self, name, value);
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
    
static PyObject *t_item_isLive(t_item *self)
{
    if (self->status & (STALE | DELETED | DEFERRED))
        Py_RETURN_FALSE;
    else
        Py_RETURN_TRUE;
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

static PyObject *t_item__isWithSchema(t_item *self)
{
    if (self->status & WITHSCHEMA)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isCoreSchema(t_item *self)
{
    if (self->status & CORESCHEMA)
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

static PyObject *t_item_isMutating(t_item *self)
{
    if (self->status & MUTATING)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isMutatingOrDeleting(t_item *self)
{
    if (self->status & (MUTATING | DELETING))
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item_isDeferringOrDeleting(t_item *self)
{
    if (self->status & (DEFERRING | DELETING))
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

static PyObject *t_item__isRefs(t_item *self)
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
        t_kind *c = (t_kind *) ((t_item *) self->kind)->c;
        PyObject *descriptor = NULL;
        PyObject *attribute;

        if (c->flags & DESCRIPTORS_INSTALLED)
            descriptor = PyDict_GetItem(c->descriptors, name);
        
        if (descriptor)
        {
            t_attribute *attr = ((t_descriptor *) descriptor)->attr;
            
            if (attr)
            {
                PyObject *value = PyObject_GetAttr((PyObject *) attr, aspect);

                if (value)
                    return value;

                PyErr_Clear();
                attrID = attr->attrID;
            }
        }

        if (attrID != Py_None)
            attribute = PyObject_CallMethodObjArgs(self->ref->view, find_NAME,
                                                   attrID, NULL);
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

static PyObject *_t_item_getLocalAttributeValue(t_item *self, PyObject *name,
                                                PyObject *defaultValue,
                                                PyObject *attrDict)
{
    PyObject *value;

    if (attrDict != NULL && attrDict != Py_None)
    {
        if (!PyObject_TypeCheck(attrDict, CValues))
        {
            PyErr_SetObject(PyExc_TypeError, attrDict);
            return NULL;
        }

        value = PyDict_GetItem(((t_values *) attrDict)->dict, name);
    }
    else if (!(value = PyDict_GetItem(self->values->dict, name)))
        value = PyDict_GetItem(self->references->dict, name);

    if (value)      /* must match t_values_dict_get */
    {
        if (value->ob_type == ItemRef)
            value = PyObject_Call(value, NULL, NULL);
        else
            Py_INCREF(value);

        return value;
    }

    if (defaultValue)
    {
        Py_INCREF(defaultValue);
        return defaultValue;
    }

    PyErr_SetObject(PyExc_AttributeError, name);
    return NULL;
}

static PyObject *t_item_getLocalAttributeValue(t_item *self, PyObject *args)
{
    PyObject *name, *defaultValue = NULL, *attrDict = NULL;

    if (!PyArg_ParseTuple(args, "O|OO", &name, &defaultValue, &attrDict))
        return NULL;

    return _t_item_getLocalAttributeValue(self, name, defaultValue, attrDict);
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

    if (PyDict_Contains(self->values->dict, name) ||
        PyDict_Contains(self->references->dict, name))
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int get_attr_flags(t_item *item, PyObject *name, t_kind *c,
                          t_attribute **attr, int *flags)
{
    t_descriptor *descriptor = NULL;
    t_attribute *attribute;

    if (c->flags & DESCRIPTORS_INSTALLED)
        descriptor = (t_descriptor *) PyDict_GetItem(c->descriptors, name);

    if (descriptor == NULL)
        return 0;
        
    attribute = descriptor->attr;
    if (attribute)
    {
        *attr = attribute;
        *flags = attribute->flags;
    }

    return 0;
}

static PyObject *t_item_hasTrueAttributeValue(t_item *self, PyObject *args)
{
    if (self->kind != Py_None)
    {
        PyObject *value, *name, *attrDict = Py_None;
        t_kind *c;

        if (!PyArg_ParseTuple(args, "O|O", &name, &attrDict))
            return NULL;

        c = (t_kind *) ((t_item *) self->kind)->c;

        if (c->flags & ATTRIBUTES_CACHED)
        {
            t_attribute *attr = NULL;
            int flags = 0;

            if (attrDict == Py_None)
            {
                if (get_attr_flags(self, name, c, &attr, &flags) < 0)
                    return NULL;
                if (attr == NULL)
                    Py_RETURN_FALSE;

                switch (flags & ATTRDICT) {
                  case A_VALUE:
                    attrDict = (PyObject *) self->values;
                    break;
                  case A_REF:
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
                if (get_attr_flags(self, name, c, &attr, &flags) < 0)
                    return NULL;
                if (attr == NULL)
                    Py_RETURN_FALSE;
            }

            if (flags & A_NOINHERIT)
            {
                if (flags & A_DEFAULT)
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
        {
            Py_DECREF(value);
            Py_RETURN_TRUE;
        }

        Py_DECREF(value);
    }

    Py_RETURN_FALSE;
}

t_attribute *_t_item_get_attr(t_item *self, PyObject *name)
{
    t_kind *c = (t_kind *) ((t_item *) self->kind)->c;
    t_attribute *attr = NULL;
    
    if (!c)
        return NULL;

    if (c->flags & DESCRIPTORS_INSTALLED)
    {
        t_descriptor *descriptor = (t_descriptor *)
            PyDict_GetItem(c->descriptors, name);

        if (!descriptor)
        {
            PyErr_SetObject(PyExc_AttributeError, name);
            return NULL;
        }

        attr = descriptor->attr;
    }
    else
    {
        PyObject *attribute =
            PyObject_CallMethodObjArgs(self->kind, getAttribute_NAME,
                                       name, Py_False, self, NULL);

        if (attribute)
        {
            attr = (t_attribute *) ((t_item *) attribute)->c;
            Py_DECREF(attribute);
        }
        else
            return NULL;
    }

    return attr;
}

static PyObject *_t_item__fireChanges(t_item *self,
                                      PyObject *op, PyObject *name,
                                      PyObject *fireAfterChange)
{
    /* first fire system monitors */
    {
        PyObject *args = PyTuple_Pack(3, op, self, name);
        PyObject *result = _t_view_invokeMonitors((t_view *) self->ref->view,
                                                  args, Py_True);

        Py_DECREF(args);
        if (result == NULL)
            return NULL;

        Py_DECREF(result);
    }

    /* fireAfterChange is one of Py_True, Py_False or Default */
    if (fireAfterChange != Py_False && self->kind != Py_None)
    {
        t_attribute *attr = _t_item_get_attr(self, name);
        t_view *view = (t_view *) self->ref->view;

        if (!attr)
            return NULL;

        if (attr->flags & A_AFTERCHANGE)
        {
            if (view->status & DEFERNOTIF)
            {
                PyObject *args = PyTuple_Pack(3, self, op, name);
                PyObject *method = PyObject_GetAttr((PyObject *) attr,
                                                    invokeAfterChange_NAME);
                PyObject *notif = PyTuple_Pack(3, method, args, Py_None);

                PyList_Append(view->deferredNotificationsCtx->data, notif);
                Py_DECREF(notif);
                Py_DECREF(method);
                Py_DECREF(args);
            }
            else if (view->status & DEFEROBS)
            {
                PyObject *call = NULL;

                if (view->status & DEFEROBSA)
                {
                    call = PyTuple_Pack(4, attr, self, op, name);
                    PyList_Append(view->deferredObserversCtx->data, call);
                }
                else if (view->status & DEFEROBSD)
                {
                    call = PyTuple_Pack(3, attr, self, name);
                    PyDict_SetItem(view->deferredObserversCtx->data, call, op);
                }

                Py_XDECREF(call);
            }
            else if (CAttribute_invokeAfterChange(attr, (PyObject *) self,
                                                  op, name) < 0)
                return NULL;
        }
    }

    /* during SYSMONONLY only sys monitors fire */
    if (!(self->status & SYSMONONLY))
    {
        PyObject *args = PyTuple_Pack(3, op, self, name);
        PyObject *result = _t_view_invokeMonitors((t_view *) self->ref->view,
                                                  args, Py_False);

        Py_DECREF(args);
        if (result == NULL)
            return NULL;

        Py_DECREF(result);
    }

    /* during SYSMONONLY no watchers fire */
    if (!(self->status & SYSMONONLY) && self->status & WATCHED)
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
    PyObject *fireAfterChange = Default;

    if (!PyArg_ParseTuple(args, "OO|O", &op, &name, &fireAfterChange))
        return NULL;

    return _t_item__fireChanges(self, op, name, fireAfterChange);
}

static PyObject *t_item__fillItem(t_item *self, PyObject *args)
{
    PyObject *name, *parent, *kind, *uuid, *view, *values, *references, *hooks;
    int status, update;
    unsigned long version;
    PyObject *result;
    t_itemref *ref;

    if (!PyArg_ParseTuple(args, "OOOOOOOik|Oi", &name, &parent, &kind,
                          &uuid, &view, &values, &references, &status, &version,
                          &hooks, &update))
        return NULL;

    self->version = version;
    if (!version)
        status |= NEW;

    self->status = status;

    if (name != Py_None && !PyObject_IsTrue(name))
        name = Py_None;
    Py_INCREF(name); Py_XDECREF(self->name);
    self->name = name;

    ref = _t_itemref_new(uuid, (t_view *) view, self);
    if (!ref)
        return NULL;
    Py_XDECREF(self->ref);
    self->ref = ref;

    if (t_item___setParent(self, parent, NULL) < 0)
    {
        PyDict_DelItem(((t_view *) view)->registry, uuid);
        Py_CLEAR(self->ref);
        return NULL;
    }
    
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

    Py_INCREF(kind); Py_XDECREF(self->kind);
    self->kind = kind;

    result = PyObject_CallMethodObjArgs(values, _setItem_NAME, self, NULL);
    if (!result)
        return NULL;
    Py_DECREF(result);
        
    result = PyObject_CallMethodObjArgs(references, _setItem_NAME, self, NULL);
    if (!result)
        return NULL;
    Py_DECREF(result);

    if (!self->parentRef)
    {
        PyErr_SetString(PyExc_AssertionError, "item._fillItem(): no parent");
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
                                                
            PyErr_Format(PyExc_ValueError, "Assigning %s to attribute '%s' on %s didn't match schema or failed (see log for explanation)",
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

int _t_item_setDirty(t_item *self, int dirty,
                     PyObject *attribute, t_values *attrDict,
                     int noChanges)
{
    PyObject *result;

    if (dirty)
    {
        t_view *view = (t_view *) self->ref->view;

        if (view->status & COMMITLOCK)
        {
            PyObject *args = PyTuple_Pack(2, self, view);

            PyErr_SetObject((PyObject *) ChangeDuringCommitError, args);
            Py_DECREF(args);

            return -1;
        }

        if (dirty & VRDIRTY)
        {
            if (attribute == Py_None)
            {
                PyErr_SetString(PyExc_ValueError, "attribute is None");
                return -1;
            }
            if (attrDict == NULL)
            {
                PyErr_SetString(PyExc_ValueError, "attrDict is missing");
                return -1;
            }
            if (!PyObject_TypeCheck(attrDict, CValues))
            {
                PyErr_SetString(PyExc_TypeError, "attrDict is not a Values");
                return -1;
            }

            if (view->status & VERIFY && dirty & VDIRTY &&
                verify(self, view, attrDict, attribute) < 0)
                return -1;

            result = t_values__setDirty(attrDict, attribute);
            Py_DECREF(result);

            if (!noChanges)
            {
                result = _t_item__fireChanges(self, set_NAME, attribute,
                                              Default);
                if (result == NULL)
                    return -1;
                Py_DECREF(result);
            }
        }

        C_countAccess(self);

        dirty |= FDIRTY;
        view->status |= FDIRTY;
            
        if (!(self->status & DIRTY))
        {
            if (!(view->status & LOADING))
            {
                result = PyObject_CallMethodObjArgs((PyObject *) view,
                                                    _logItem_NAME, self, NULL);
                if (!result)
                    return -1;

                if (PyObject_IsTrue(result))
                {
                    Py_DECREF(result);
                    self->status |= dirty;
                    return 1;
                }

                Py_DECREF(result);
            }
        }
        else
            self->status |= dirty;
    }
    else
    {
        self->status &= ~(DIRTY | ADIRTY | FDIRTY);

        result = PyObject_CallMethodObjArgs((PyObject *) self->values,
                                            _clearDirties_NAME, NULL); 
        if (result == NULL)
            return -1;
        Py_DECREF(result);

        result = PyObject_CallMethodObjArgs((PyObject *) self->references,
                                            _clearDirties_NAME, NULL);
        if (result == NULL)
            return -1;
        Py_DECREF(result);

        if (self->children != NULL && self->children != Py_None)
        {
            result = PyObject_CallMethodObjArgs(self->children,
                                                _clearDirties_NAME, NULL);
            if (result == NULL)
                return -1;
            Py_DECREF(result);
        }
    }

    return 0;
}

static PyObject *t_item_setDirty(t_item *self, PyObject *args)
{
    PyObject *attribute = Py_None;
    t_values *attrDict = NULL;
    int dirty, result, noChanges = 0;

    if (self->status & NODIRTY)
        Py_RETURN_FALSE;

    if (!PyArg_ParseTuple(args, "i|OOi", &dirty,
                          &attribute, &attrDict, &noChanges))
        return NULL;

    result = _t_item_setDirty(self, dirty, attribute, attrDict, noChanges);
    if (result < 0)
        return NULL;

    if (result)
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}

static int invokeWatchers(PyObject *dispatch, PyObject *name,
                          PyObject *op, PyObject *change,
                          PyObject *item, PyObject *other,
                          t_view *view)
{
    PyObject *watchers = PyObject_GetItem(dispatch, name);

    if (watchers)
    {
        PyObject *iter = PyObject_GetIter(watchers);
        Py_DECREF(watchers);

        if (iter)
        {
            PyObject *watcher;

            if (view->status & DEFERNOTIF)
                while ((watcher = PyIter_Next(iter))) {
                    PyObject *args =
                        PyTuple_Pack(5, op, change, item, name, other);
                    PyObject *notif =
                        PyTuple_Pack(3, watcher, args, Py_None);

                    PyList_Append(view->deferredNotificationsCtx->data, notif);
                    Py_DECREF(notif);
                    Py_DECREF(args);
                    Py_DECREF(watcher);
                }
            else
                while ((watcher = PyIter_Next(iter))) {
                    PyObject *args =
                        PyTuple_Pack(5, op, change, item, name, other);
                    PyObject *result =
                        PyObject_Call(watcher, args, NULL);

                    Py_DECREF(args);
                    Py_DECREF(watcher);
                    if (!result)
                        break;
                    Py_DECREF(result);
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
    t_view *view = (t_view *) self->ref->view;

    if (self->status & NODIRTY)
        Py_RETURN_NONE;

    if (!PyArg_ParseTuple(args, "OOOO", &op, &change, &name, &other))
        return NULL;

    dispatch = PyDict_GetItem(self->references->dict, watchers_NAME);
    if (dispatch && PySequence_Contains(dispatch, name))
        if (invokeWatchers(dispatch, name, op, change,
                           (PyObject *) self, other, view) < 0)
            return NULL;

    if (view->watchers)
    {
        dispatch = PyDict_GetItem(view->watchers, self->ref->uuid);

        if (dispatch && PySequence_Contains(dispatch, name))
            if (invokeWatchers(dispatch, name, op, change,
                               (PyObject *) self, other, view) < 0)
                return NULL;
    }

    Py_RETURN_NONE;
}

static int invokeItemWatchers(PyObject *dispatch, PyObject *uItem,
                              PyObject *op, PyObject *names, t_view *view)
{
    PyObject *watchers = PyObject_GetItem(dispatch, uItem);

    if (watchers)
    {
        PyObject *iter = PyObject_GetIter(watchers);
        Py_DECREF(watchers);

        if (iter)
        {
            PyObject *watcher;

            if (view->status & DEFERNOTIF)
                while ((watcher = PyIter_Next(iter))) {
                    PyObject *args = PyTuple_Pack(3, op, uItem, names);
                    PyObject *notif = PyTuple_Pack(3, watcher, args, Py_None);

                    PyList_Append(view->deferredNotificationsCtx->data, notif);
                    Py_DECREF(notif);
                    Py_DECREF(args);
                    Py_DECREF(watcher);
                }
            else
                while ((watcher = PyIter_Next(iter))) {
                    PyObject *args = PyTuple_Pack(3, op, uItem, names);
                    PyObject *result = PyObject_Call(watcher, args, NULL);

                    Py_DECREF(args);
                    Py_DECREF(watcher);
                    if (!result)
                        break;
                    Py_DECREF(result);
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
        t_view *view = (t_view *) self->ref->view;
        PyObject *dispatch = PyDict_GetItem(self->references->dict,
                                            watchers_NAME);

        if (dispatch && PySequence_Contains(dispatch, self->ref->uuid))
            return invokeItemWatchers(dispatch, self->ref->uuid, op, names,
                                      view);
    }

    if (self->status & T_WATCHED)
    {
        t_view *view = (t_view *) self->ref->view;

        if (view->watchers)
        {
            PyObject *dispatch = PyDict_GetItem(view->watchers,
                                                self->ref->uuid);

            if (dispatch && PySequence_Contains(dispatch, self->ref->uuid))
                return invokeItemWatchers(dispatch, self->ref->uuid, op, names,
                                          view);
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
        PyObject *view = self->ref->view;
        PyObject *uuid = ((t_item *) kind)->ref->uuid;
        PyObject *newKind = PyObject_GetItem(view, uuid);

        if (newKind)
        {
            Py_DECREF(kind);
            self->kind = kind = newKind;
        }
        else
            return NULL;
    }

    Py_INCREF(kind);
    return kind;
}

static int t_item__setKind(t_item *self, PyObject *kind, void *data)
{
    PyObject *result =
        PyObject_CallMethodObjArgs((PyObject *) self, _setKind_NAME,
                                   kind, NULL);
    
    if (!result)
        return -1;

    Py_DECREF(result);
    return 0;
}


/* itsView */

static PyObject *t_item__getView(t_item *self, void *data)
{
    PyObject *view = self->ref->view;

    Py_INCREF(view);
    return view;
}


/* itsParent */

static PyObject *t_item__getParent(t_item *self, void *data)
{
    PyObject *parentRef = self->parentRef;

    if (parentRef)
    {
        if (parentRef->ob_type == ItemRef)
            return t_itemref_call((t_itemref *) parentRef, NULL, NULL);

        Py_INCREF(parentRef); /* a view */
        return parentRef;
    }

    Py_RETURN_NONE;
}

static int t_item__setParent(t_item *self, PyObject *parent, void *data)
{
    PyObject *result =
        PyObject_CallMethodObjArgs((PyObject *) self, move_NAME,
                                   parent ? parent : Py_None, NULL);

    if (!result)
        return -1;

    Py_DECREF(result);
    return 0;
}


/* _parent */

static PyObject *t_item___getParent(t_item *self, void *data)
{
    PyObject *parentRef = self->parentRef;

    if (parentRef)
    {
        if (parentRef->ob_type == ItemRef)
        {
            t_item *parent = ((t_itemref *) parentRef)->item;

            if (parent)
            {
                Py_INCREF(parent);
                return (PyObject *) parent;
            }
        }
        else if (PyObject_TypeCheck(parentRef, CView))
        {
            Py_INCREF(parentRef);
            return parentRef;
        }
    }

    Py_RETURN_NONE;
}

static int t_item___setParent(t_item *self, PyObject *parent, void *data)
{
    PyObject *parentRef = NULL;

    if (parent == Py_None)
        parent = NULL;

    if (parent)
    {
        PyObject *result;

        if (PyObject_TypeCheck(parent, CItem))
            parentRef = (PyObject *) ((t_item *) parent)->ref;
        else if (PyObject_TypeCheck(parent, CView))
            parentRef = parent;
        else
        {
            PyErr_SetObject(PyExc_TypeError, parent);
            return -1;
        }

        result = PyObject_CallMethodObjArgs(parent, _addItem_NAME, self, NULL);
        if (!result)
            return -1;
        Py_DECREF(result);

        Py_INCREF(parentRef);
    }

    Py_XDECREF(self->parentRef);
    self->parentRef = parentRef;

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
    PyObject *result =
        PyObject_CallMethodObjArgs((PyObject *) self, rename_NAME,
                                   name ? name : Py_None, NULL);

    if (!result)
        return -1;

    Py_DECREF(result);
    return 0;
}


/* itsRoot */

static PyObject *t_item__getRoot(t_item *self, void *data)
{
    t_item *root = self;

    while (root) {
        PyObject *parentRef = root->parentRef;

        if (!parentRef)
            Py_RETURN_NONE;

        if (parentRef->ob_type != ItemRef)
            break;
        else
            root = ((t_itemref *) parentRef)->item;
    }

    if (!root)
        Py_RETURN_NONE;

    if (root->status & STALE)
        return PyObject_GetItem(root->ref->view, root->ref->uuid);

    Py_INCREF(root);
    return (PyObject *) root;
}


/* itsRef */

static PyObject *t_item__getRef(t_item *self, void *data)
{
    if (self->ref)
    {
        Py_INCREF(self->ref);
        return (PyObject *) self->ref;
    }

    Py_RETURN_NONE;
}


/* itsUUID */

static PyObject *t_item__getUUID(t_item *self, void *data)
{
    if (self->ref)
    {
        PyObject *uuid = self->ref->uuid;

        Py_INCREF(uuid);
        return uuid;
    }
    
    Py_RETURN_NONE;
}


/* itsPath */

static PyObject *t_item__getPath(t_item *self, void *data)
{
    return PyObject_CallMethodObjArgs((PyObject *) self, _getPath_NAME, NULL);
}


/* itsStatus */

static PyObject *t_item__getStatus(t_item *self, void *data)
{
    return PyInt_FromLong(self->status);
}


/* itsVersion, _version */

static PyObject *t_item__getVersion(t_item *self, void *data)
{
    return PyLong_FromUnsignedLong(self->version);
}

static int t_item__setVersion(t_item *self, PyObject *value, void *data)
{
    unsigned long version;

    if (!value)
        version = 0;
    else if (PyInt_Check(value))
        version = PyInt_AS_LONG(value);
    else if (PyLong_Check(value))
        version = PyLong_AsUnsignedLong(value);
    else
    {
        PyErr_SetObject(PyExc_TypeError, value);
        return -1;
    }

    self->version = version;
    
    return 0;
}


/* itsValues */

static PyObject *t_item__getValues(t_item *self, void *data)
{
    Py_INCREF(self->values);
    return (PyObject *) self->values;
}


/* itsRefs */

static PyObject *t_item__getRefs(t_item *self, void *data)
{
    Py_INCREF(self->references);
    return (PyObject *) self->references;
}


void _init_item(PyObject *m)
{
    if (PyType_Ready(&ItemType) >= 0)
    {
        if (m)
        {
            PyObject *dict = ItemType.tp_dict;
            PyObject *cobj;

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
            PyDict_SetItemString_Int(dict, "WITHSCHEMA", WITHSCHEMA);
            PyDict_SetItemString_Int(dict, "CONTAINER", CONTAINER);
            PyDict_SetItemString_Int(dict, "ADIRTY", ADIRTY);
            PyDict_SetItemString_Int(dict, "PINNED", PINNED);
            PyDict_SetItemString_Int(dict, "NODIRTY", NODIRTY);
            PyDict_SetItemString_Int(dict, "MERGED", MERGED);
            PyDict_SetItemString_Int(dict, "MUTATING", MUTATING);
            PyDict_SetItemString_Int(dict, "P_WATCHED", P_WATCHED);
            PyDict_SetItemString_Int(dict, "T_WATCHED", T_WATCHED);
            PyDict_SetItemString_Int(dict, "TOINDEX", TOINDEX);
            PyDict_SetItemString_Int(dict, "WATCHED", WATCHED);
            PyDict_SetItemString_Int(dict, "SYSMONONLY", SYSMONONLY);
            PyDict_SetItemString_Int(dict, "SYSMONITOR", SYSMONITOR);
            PyDict_SetItemString_Int(dict, "IDXMONITOR", IDXMONITOR);

            PyDict_SetItemString_Int(dict, "VRDIRTY", VRDIRTY);
            PyDict_SetItemString_Int(dict, "DIRTY", DIRTY);
            PyDict_SetItemString_Int(dict, "SAVEMASK", SAVEMASK);

            _setKind_NAME = PyString_FromString("_setKind");
            move_NAME = PyString_FromString("move");
            rename_NAME = PyString_FromString("rename");
            _getPath_NAME = PyString_FromString("_getPath");
            find_NAME = PyString_FromString("find");
            getAttribute_NAME = PyString_FromString("getAttribute");
            getAspect_NAME = PyString_FromString("getAspect");
            getAttributeAspect_NAME = PyString_FromString("getAttributeAspect");
            redirectTo_NAME = PyString_FromString("redirectTo");
            _redirectTo_NAME = PyString_FromString("_redirectTo");
            logger_NAME = PyString_FromString("logger");
            _verifyAssignment_NAME = PyString_FromString("_verifyAssignment");
            _setDirty_NAME = PyString_FromString("_setDirty");
            set_NAME = PyString_FromString("set");
            item_NAME = PyString_FromString("item");
            _logItem_NAME = PyString_FromString("_logItem");
            _clearDirties_NAME = PyString_FromString("_clearDirties");
            _flags_NAME = PyString_FromString("_flags");
            watchers_NAME = PyString_FromString("watchers");
            filterItem_NAME = PyString_FromString("filterItem");
            _setItem_NAME = PyString_FromString("_setItem");
            getAttributeValue_NAME = PyString_FromString("getAttributeValue");
            _addItem_NAME = PyString_FromString("_addItem");
            invokeAfterChange_NAME = PyString_FromString("invokeAfterChange");
            getItemChild_NAME = PyString_FromString("getItemChild");

            cobj = PyCObject_FromVoidPtr(_t_item_getLocalAttributeValue, NULL);
            PyModule_AddObject(m, "CItem_getLocalAttributeValue", cobj);
        }
    }
}
