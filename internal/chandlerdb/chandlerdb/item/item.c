
/*
 * The Item C type
 */

#include <Python.h>
#include "structmember.h"

#include "item.h"

static void t_item_dealloc(t_item *self);
static PyObject *t_item_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_item_init(t_item *self, PyObject *args, PyObject *kwds);
static PyObject *t_item_isNew(t_item *self, PyObject *args);
static PyObject *t_item_isDeleting(t_item *self, PyObject *args);
static PyObject *t_item_isDeleted(t_item *self, PyObject *args);
static PyObject *t_item_isStale(t_item *self, PyObject *args);
static PyObject *t_item_isPinned(t_item *self, PyObject *args);
static PyObject *t_item_isDirty(t_item *self, PyObject *args);
static PyObject *t_item_getDirty(t_item *self, PyObject *args);
static PyObject *t_item__isNDirty(t_item *self, PyObject *args);
static PyObject *t_item__isRepository(t_item *self, PyObject *args);
static PyObject *t_item__isView(t_item *self, PyObject *args);
static PyObject *t_item__isItem(t_item *self, PyObject *args);
static PyObject *t_item__isRefList(t_item *self, PyObject *args);
static PyObject *t_item__isUUID(t_item *self, PyObject *args);

#define isNew_DOC \
"Tell whether this item is new.\n\nA new item is defined as an item that\
 was never committed to the repository.\n@return: C{True} or C{False}"

#define isDeleting_DOC \
"Tell whether this item is in the process of being deleted.\n\n\
 @return: C{True} or C{False}"

#define isDeleted_DOC \
"Tell whether this item is deleted.\n\n\
 @return: C{True} or C{False}"

#define isStale_DOC \
"Tell whether this item pointer is out of date.\n\n\
 A stale item pointer is defined as an item pointer that is no longer\
 valid. When an item is unloaded, the item pointer is marked\
 stale. The item pointer can be refreshed by reloading the item via the\
 L{find} method, passing it the item's C{uuid} obtained via the\
 L{itsUUID} property.\n\n\
 Stale items are encountered when item pointers are kept across\
 transaction boundaries. It is recommended to keep the item's\
 C{uuid} instead.\n\n\
 @return: C{True} or C{False}"

#define isPinned_DOC \
"Tell whether this item is pinned.\n\n\
 A pinned item is not freed from memory or marked stale, until it\
 is un-pinned or deleted.\n\n\
 @return: C{True} or C{False}"

#define isDirty_DOC \
"Tell whether this item was changed and needs to be committed.\n\n\
 @return: C{True} or C{False}"

#define getDirty_DOC \
"Return the dirty flags currently set on this item.\n\n\
 @return: an integer"


static PyMemberDef t_item_members[] = {
    { "_lastAccess", T_UINT, offsetof(t_item, lastAccess), 0, "access stamp" },
    { "_status", T_UINT, offsetof(t_item, status), 0, "item status flags" },
    { "_version", T_UINT, offsetof(t_item, version), 0, "item version" },
    { "_uuid", T_OBJECT, offsetof(t_item, uuid), 0, "item uuid" },
    { "_name", T_OBJECT, offsetof(t_item, name), 0, "item name" },
    { "_values", T_OBJECT, offsetof(t_item, values), 0, "literals" },
    { "_references", T_OBJECT, offsetof(t_item, references), 0, "references" },
    { "_kind", T_OBJECT, offsetof(t_item, kind), 0, "item kind" },
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_item_methods[] = {
    { "isNew", (PyCFunction) t_item_isNew, METH_NOARGS, isNew_DOC },
    { "isDeleting", (PyCFunction) t_item_isDeleting, METH_NOARGS, isDeleting_DOC },
    { "isDeleted", (PyCFunction) t_item_isDeleted, METH_NOARGS, isDeleted_DOC },
    { "isStale", (PyCFunction) t_item_isStale, METH_NOARGS, isStale_DOC },
    { "isPinned", (PyCFunction) t_item_isPinned, METH_NOARGS, isPinned_DOC },
    { "isDirty", (PyCFunction) t_item_isDirty, METH_NOARGS, isDirty_DOC },
    { "getDirty", (PyCFunction) t_item_getDirty, METH_NOARGS, getDirty_DOC },
    { "_isNDirty", (PyCFunction) t_item__isNDirty, METH_NOARGS, "" },
    { "_isRepository", (PyCFunction) t_item__isRepository, METH_NOARGS, "" },
    { "_isView", (PyCFunction) t_item__isView, METH_NOARGS, "" },
    { "_isItem", (PyCFunction) t_item__isItem, METH_NOARGS, "" },
    { "_isRefList", (PyCFunction) t_item__isRefList, METH_NOARGS, "" },
    { "_isUUID", (PyCFunction) t_item__isUUID, METH_NOARGS, "" },
    { NULL, NULL, 0, NULL }
};

static PyMethodDef item_funcs[] = {
    { NULL, NULL, 0, NULL }
};

static PyTypeObject ItemType = {
    PyObject_HEAD_INIT(NULL)
    0,                                         /* ob_size */
    "chandlerdb.item.item.CItem",              /* tp_name */
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
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  /* tp_flags */
    "C Item type",                             /* tp_doc */
    0,                                         /* tp_traverse */
    0,                                         /* tp_clear */
    0,                                         /* tp_richcompare */
    0,                                         /* tp_weaklistoffset */
    0,                                         /* tp_iter */
    0,                                         /* tp_iternext */
    t_item_methods,                            /* tp_methods */
    t_item_members,                            /* tp_members */
    0,                                         /* tp_getset */
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
    self->ob_type->tp_free((PyObject *) self);
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
    Py_RETURN_TRUE;
}

static PyObject *t_item__isRefList(t_item *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static PyObject *t_item__isUUID(t_item *self, PyObject *args)
{
    Py_RETURN_FALSE;
}


static void PyDict_SetItemString_Int(PyObject *dict, char *key, int value)
{
    PyObject *pyValue = PyInt_FromLong(value);

    PyDict_SetItemString(dict, key, pyValue);
    Py_DECREF(pyValue);
}

void inititem(void)
{
    if (PyType_Ready(&ItemType) >= 0)
    {
        PyObject *m = Py_InitModule3("item", item_funcs, "Item C type module");

        if (m)
        {
            PyObject *dict;

            Py_INCREF(&ItemType);
            PyModule_AddObject(m, "CItem", (PyObject *) &ItemType);

            dict = ItemType.tp_dict;

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

            PyDict_SetItemString_Int(dict, "VRDIRTY", VRDIRTY);
            PyDict_SetItemString_Int(dict, "DIRTY", DIRTY);
            PyDict_SetItemString_Int(dict, "MERGED", MERGED);
            PyDict_SetItemString_Int(dict, "SAVEMASK", SAVEMASK);
        }
    }
}
