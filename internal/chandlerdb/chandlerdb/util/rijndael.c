
/*
 * The rijndael module
 *
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

#include <Python.h>
#include "structmember.h"

#include "rijndael-api-fst.h"

#ifdef _MSC_VER
#include <malloc.h>
#endif

static PyObject *reportError(int code)
{
    char *reason;

    switch (code) {
      case BAD_KEY_DIR:
        reason = "Key direction is invalid, e.g., unknown value";
        break;
      case BAD_KEY_MAT:
        reason = "Key material not of correct length (16, 24 or 32 bytes)";
        break;
      case BAD_KEY_INSTANCE:
        reason = "Key object passed is not valid";
        break;
      case BAD_CIPHER_MODE:
        reason = "Cipher mode not one of ECB, CBC or CFB1";
        break;
      case BAD_CIPHER_STATE:
        reason = "Cipher in wrong state (for example, not initialized)";
        break;
      case BAD_BLOCK_LENGTH:
        reason = "Bad block length (not 16 byte aligned)";
        break;
      case BAD_CIPHER_INSTANCE:
        reason = "Cipher object passed is not valid";
        break;
      case BAD_DATA:
        reason = "Data contents are invalid (for example, invalid padding)";
        break;
      case BAD_OTHER:
        reason = "Unknown error (BAD_OTHER)";
        break;
      default:
        reason = "Unknown error";
        break;
    }

    PyErr_Format(PyExc_ValueError, "rijndael error %d: %s", code, reason);

    return NULL;
}


typedef struct {
    PyObject_HEAD
    keyInstance key;
} t_key;


static void t_key_dealloc(t_key *self);
static PyObject *t_key_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int t_key_init(t_key *self, PyObject *args, PyObject *kwds);


static PyMemberDef t_key_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_key_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_key_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject KeyType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.util.rijndael.Key",                      /* tp_name */
    sizeof(t_key),                                       /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_key_dealloc,                           /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    0,                                                   /* tp_repr */
    0,                                                   /* tp_as_number */
    0,                                                   /* tp_as_sequence */
    0,                                                   /* tp_as_mapping */
    0,                                                   /* tp_hash  */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    0,                                                   /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                                  /* tp_flags */
    "Rijndael Key type",                                 /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_key_methods,                                       /* tp_methods */
    t_key_members,                                       /* tp_members */
    t_key_properties,                                    /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_key_init,                                /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_key_new,                                  /* tp_new */
};


static void t_key_dealloc(t_key *self)
{
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_key_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    t_key *self = (t_key *) type->tp_alloc(type, 0);

    if (self)
        memset(&self->key, 0, sizeof(self->key));

    return (PyObject *) self;
}

static int t_key_init(t_key *self, PyObject *args, PyObject *kwds)
{
    int direction, keyLen, result;
    char *keyMaterial;

    if (!PyArg_ParseTuple(args, "is#", &direction, &keyMaterial, &keyLen))
        return -1;

    result = makeKey(&self->key, direction, keyLen * 8, keyMaterial);
    if (result != TRUE)
    {
        reportError(result);
        return -1;
    }

    return 0;
}


typedef struct {
    PyObject_HEAD
    cipherInstance cipher;
} t_cipher;


static void t_cipher_dealloc(t_cipher *self);
static PyObject *t_cipher_new(PyTypeObject *type,
                              PyObject *args, PyObject *kwds);
static int t_cipher_init(t_cipher *self, PyObject *args, PyObject *kwds);

static PyObject *t_cipher_blockEncrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds);
static PyObject *t_cipher_blockDecrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds);
static PyObject *t_cipher_padEncrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds);
static PyObject *t_cipher_padDecrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds);


static PyMemberDef t_cipher_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_cipher_methods[] = {
    { "blockEncrypt", (PyCFunction) t_cipher_blockEncrypt, METH_VARARGS,
      "encrypt one or several 16 byte blocks" },
    { "blockDecrypt", (PyCFunction) t_cipher_blockDecrypt, METH_VARARGS,
      "decrypt one or several 16 byte blocks" },
    { "padEncrypt", (PyCFunction) t_cipher_padEncrypt, METH_VARARGS,
      "encrypt data padding output to 16 bytes" },
    { "padDecrypt", (PyCFunction) t_cipher_padDecrypt, METH_VARARGS,
      "encrypt data encrypted with padEncrypt" },
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_cipher_properties[] = {
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject CipherType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.util.rijndael.Cipher",                   /* tp_name */
    sizeof(t_cipher),                                    /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_cipher_dealloc,                        /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    0,                                                   /* tp_repr */
    0,                                                   /* tp_as_number */
    0,                                                   /* tp_as_sequence */
    0,                                                   /* tp_as_mapping */
    0,                                                   /* tp_hash  */
    0,                                                   /* tp_call */
    0,                                                   /* tp_str */
    0,                                                   /* tp_getattro */
    0,                                                   /* tp_setattro */
    0,                                                   /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                                  /* tp_flags */
    "Rijndael Cipher type",                              /* tp_doc */
    0,                                                   /* tp_traverse */
    0,                                                   /* tp_clear */
    0,                                                   /* tp_richcompare */
    0,                                                   /* tp_weaklistoffset */
    0,                                                   /* tp_iter */
    0,                                                   /* tp_iternext */
    t_cipher_methods,                                    /* tp_methods */
    t_cipher_members,                                    /* tp_members */
    t_cipher_properties,                                 /* tp_getset */
    0,                                                   /* tp_base */
    0,                                                   /* tp_dict */
    0,                                                   /* tp_descr_get */
    0,                                                   /* tp_descr_set */
    0,                                                   /* tp_dictoffset */
    (initproc)t_cipher_init,                             /* tp_init */
    0,                                                   /* tp_alloc */
    (newfunc)t_cipher_new,                               /* tp_new */
};


static void t_cipher_dealloc(t_cipher *self)
{
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *t_cipher_new(PyTypeObject *type,
                              PyObject *args, PyObject *kwds)
{
    t_cipher *self = (t_cipher *) type->tp_alloc(type, 0);

    if (self)
        memset(&self->cipher, 0, sizeof(self->cipher));

    return (PyObject *) self;
}

static int t_cipher_init(t_cipher *self, PyObject *args, PyObject *kwds)
{
    char *IV = NULL;
    int mode, result;

    if (!PyArg_ParseTuple(args, "i|z#", &mode, &IV, &result))
        return -1;

    result = cipherInit(&self->cipher, mode, IV);
    if (result != TRUE)
    {
        reportError(result);
        return -1;
    }

    return 0;
}

static PyObject *t_cipher_blockEncrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds)
{
    t_key *key;
    u8 *input, *output;
    int inputLen, result;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = alloca(inputLen);
    result = blockEncrypt(&self->cipher, &key->key,
                          input, inputLen * 8, output);

    if (result < 0)
        return reportError(result);

    return PyString_FromStringAndSize((char *) output, result / 8);
}


static PyObject *t_cipher_blockDecrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds)
{
    t_key *key;
    u8 *input, *output;
    int inputLen, result;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = alloca(inputLen);
    result = blockDecrypt(&self->cipher, &key->key,
                          input, inputLen * 8, output);

    if (result < 0)
        return reportError(result);

    return PyString_FromStringAndSize((char *) output, result / 8);
}


static PyObject *t_cipher_padEncrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds)
{
    t_key *key;
    u8 *input, *output;
    int inputLen, result;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = alloca(inputLen + 16);
    result = padEncrypt(&self->cipher, &key->key, input, inputLen, output);

    if (result < 0)
        return reportError(result);

    return PyString_FromStringAndSize((char *) output, result);
}


static PyObject *t_cipher_padDecrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds)
{
    t_key *key;
    u8 *input, *output;
    int inputLen, result;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = alloca(inputLen);
    result = padDecrypt(&self->cipher, &key->key, input, inputLen, output);

    if (result < 0)
        return reportError(result);

    return PyString_FromStringAndSize((char *) output, result);
}


static PyMethodDef rijndael_funcs[] = {
    { NULL, NULL, 0, NULL }
};


static void PyDict_SetItemString_Int(PyObject *dict, char *key, int value)
{
    PyObject *pyValue = PyInt_FromLong(value);

    PyDict_SetItemString(dict, key, pyValue);
    Py_DECREF(pyValue);
}

void initrijndael(void)
{
    PyObject *m = Py_InitModule3("rijndael", rijndael_funcs,
                                 "rijndael API module");

    if (PyType_Ready(&KeyType) >= 0)
    {
        if (m)
        {
            PyObject *dict = KeyType.tp_dict;

            Py_INCREF(&KeyType);
            PyModule_AddObject(m, "Key", (PyObject *) &KeyType);

            PyDict_SetItemString_Int(dict, "ENCRYPT", DIR_ENCRYPT);
            PyDict_SetItemString_Int(dict, "DECRYPT", DIR_DECRYPT);
        }
    }

    if (PyType_Ready(&CipherType) >= 0)
    {
        if (m)
        {
            PyObject *dict = CipherType.tp_dict;

            Py_INCREF(&CipherType);
            PyModule_AddObject(m, "Cipher", (PyObject *) &CipherType);

            PyDict_SetItemString_Int(dict, "ECB", MODE_ECB);
            PyDict_SetItemString_Int(dict, "CBC", MODE_CBC);
            PyDict_SetItemString_Int(dict, "CFB1", MODE_CFB1);
        }
    }
}
