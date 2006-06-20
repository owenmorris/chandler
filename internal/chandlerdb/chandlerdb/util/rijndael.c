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
#include "rijndael-api-fst.h"


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
static PyObject *t_key_repr(t_key *self);
static PyObject *t_key__getDirection(t_key *self, void *data);


static PyMemberDef t_key_members[] = {
    { NULL, 0, 0, 0, NULL }
};

static PyMethodDef t_key_methods[] = {
    { NULL, NULL, 0, NULL }
};

static PyGetSetDef t_key_properties[] = {
    { "direction", (getter) t_key__getDirection, NULL, "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject KeyType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.util.c.Key",                             /* tp_name */
    sizeof(t_key),                                       /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_key_dealloc,                           /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    (reprfunc)t_key_repr,                                /* tp_repr */
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
    int direction, keyLen, code;
    char *keyMaterial;

    if (!PyArg_ParseTuple(args, "is#", &direction, &keyMaterial, &keyLen))
        return -1;

    code = makeKey(&self->key, direction, keyLen * 8, keyMaterial);
    if (code != TRUE)
    {
        reportError(code);
        return -1;
    }

    return 0;
}

static PyObject *t_key_repr(t_key *self)
{
    return PyString_FromFormat("<AES %s key (%d bit)>",
                               (self->key.direction == DIR_ENCRYPT
                                ? "encryption"
                                : "decryption"),
                               self->key.keyLen);
}

static PyObject *t_key__getDirection(t_key *self, void *data)
{
    return PyInt_FromLong(self->key.direction);
}


typedef struct {
    PyObject_HEAD
    cipherInstance cipher;
} t_cipher;


static void t_cipher_dealloc(t_cipher *self);
static PyObject *t_cipher_new(PyTypeObject *type,
                              PyObject *args, PyObject *kwds);
static int t_cipher_init(t_cipher *self, PyObject *args, PyObject *kwds);
static PyObject *t_cipher_repr(t_cipher *self);

static PyObject *t_cipher_blockEncrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds);
static PyObject *t_cipher_blockDecrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds);
static PyObject *t_cipher_padEncrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds);
static PyObject *t_cipher_padDecrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds);
static PyObject *t_cipher__getMode(t_cipher *self, void *data);
static PyObject *t_cipher__getIV(t_cipher *self, void *data);


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
    { "mode", (getter) t_cipher__getMode, NULL, "", NULL },
    { "IV", (getter) t_cipher__getIV, NULL, "", NULL },
    { NULL, NULL, NULL, NULL, NULL }
};

static PyTypeObject CipherType = {
    PyObject_HEAD_INIT(NULL)
    0,                                                   /* ob_size */
    "chandlerdb.util.c.Cipher",                          /* tp_name */
    sizeof(t_cipher),                                    /* tp_basicsize */
    0,                                                   /* tp_itemsize */
    (destructor)t_cipher_dealloc,                        /* tp_dealloc */
    0,                                                   /* tp_print */
    0,                                                   /* tp_getattr */
    0,                                                   /* tp_setattr */
    0,                                                   /* tp_compare */
    (reprfunc)t_cipher_repr,                             /* tp_repr */
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
    int mode, code;

    if (!PyArg_ParseTuple(args, "i|z#", &mode, &IV, &code))
        return -1;

    code = cipherInit(&self->cipher, mode, IV);
    if (code != TRUE)
    {
        reportError(code);
        return -1;
    }

    return 0;
}

static PyObject *t_cipher_repr(t_cipher *self)
{
    u8 *iv = self->cipher.IV;
    int hasIV = 0, i = 0;
    char *mode;
    
    while (i < MAX_IV_SIZE && !hasIV)
        hasIV = iv[i++];

    switch (self->cipher.mode) {
      case MODE_ECB:
        mode = "ECB";
        break;
      case MODE_CBC:
        mode = "CBC";
        break;
      case MODE_CFB1:
        mode = "CFB1";
        break;
      default:
        mode = "invalid";
        break;
    }

    return PyString_FromFormat("<AES %s cipher (%s IV)>",
                               mode, hasIV ? "with" : "without");
}

static PyObject *t_cipher_blockEncrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds)
{
    PyObject *result = NULL;
    u8 *input, *output;
    int inputLen;
    t_key *key;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = malloc(inputLen);
    if (!output)
        PyErr_SetString(PyExc_MemoryError, "malloc failed");
    else
    {
        int len = blockEncrypt(&self->cipher, &key->key,
                               input, inputLen * 8, output);

        if (len < 0)
            result = reportError(len);
        else
            result = PyString_FromStringAndSize((char *) output, len / 8);

        free(output);
    }

    return result;
}

static PyObject *t_cipher_blockDecrypt(t_cipher *self,
                                       PyObject *args, PyObject *kwds)
{
    PyObject *result = NULL;
    u8 *input, *output;
    int inputLen;
    t_key *key;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = malloc(inputLen);
    if (!output)
        PyErr_SetString(PyExc_MemoryError, "malloc failed");
    else
    {
        int len  = blockDecrypt(&self->cipher, &key->key,
                                input, inputLen * 8, output);

        if (len < 0)
            result = reportError(len);
        else
            result = PyString_FromStringAndSize((char *) output, len / 8);

        free(output);
    }

    return result;
}

static PyObject *t_cipher_padEncrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds)
{
    PyObject *result = NULL;
    u8 *input, *output;
    int inputLen;
    t_key *key;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = malloc(inputLen + 16);
    if (!output)
        PyErr_SetString(PyExc_MemoryError, "malloc failed");
    else
    {
        int len = padEncrypt(&self->cipher, &key->key, input, inputLen, output);

        if (len < 0)
            result = reportError(len);
        else
            result = PyString_FromStringAndSize((char *) output, len);

        free(output);
    }

    return result;
}

static PyObject *t_cipher_padDecrypt(t_cipher *self,
                                     PyObject *args, PyObject *kwds)
{
    PyObject *result = NULL;
    u8 *input, *output;
    int inputLen;
    t_key *key;

    if (!PyArg_ParseTuple(args, "Os#", &key, &input, &inputLen))
        return NULL;

    if (!PyObject_TypeCheck((PyObject *) key, &KeyType))
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *) key);
        return NULL;
    }

    output = malloc(inputLen);
    if (!output)
        PyErr_SetString(PyExc_MemoryError, "malloc failed");
    else
    {
        int len = padDecrypt(&self->cipher, &key->key, input, inputLen, output);

        if (len < 0)
            result = reportError(len);
        else
            result = PyString_FromStringAndSize((char *) output, len);
        
        free(output);
    }

    return result;
}

static PyObject *t_cipher__getMode(t_cipher *self, void *data)
{
    return PyInt_FromLong(self->cipher.mode);
}

static PyObject *t_cipher__getIV(t_cipher *self, void *data)
{
    return PyString_FromStringAndSize((char *) self->cipher.IV, MAX_IV_SIZE);
}


void _init_rijndael(PyObject *m)
{
    if (PyType_Ready(&KeyType) >= 0)
    {
        if (m)
        {
            PyObject *dict = KeyType.tp_dict;

            Py_INCREF(&KeyType);
            PyModule_AddObject(m, "Key", (PyObject *) &KeyType);
            Key = &KeyType;

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
            Cipher = &CipherType;

            PyDict_SetItemString_Int(dict, "ECB", MODE_ECB);
            PyDict_SetItemString_Int(dict, "CBC", MODE_CBC);
            PyDict_SetItemString_Int(dict, "CFB1", MODE_CFB1);
        }
    }
}
