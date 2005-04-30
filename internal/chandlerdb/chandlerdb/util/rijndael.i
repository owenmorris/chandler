/* ====================================================================
 * Copyright (c) 2004 Open Source Applications Foundation.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions: 
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software. 
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 * ====================================================================
 */

%module rijndael

%pythoncode %{

VERSION = '2.4'

%}

%{

#include "rijndael.h"

#ifdef _MSC_VER
#include <malloc.h>
#endif

static PyObject *reportError(int result)
{
    char *msg;

    switch (result) {
      case RIJNDAEL_UNSUPPORTED_MODE:
        msg = "RIJNDAEL_UNSUPPORTED_MODE";
        break;
      case RIJNDAEL_UNSUPPORTED_DIRECTION:
        msg = "RIJNDAEL_UNSUPPORTED_DIRECTION";
        break;
      case RIJNDAEL_UNSUPPORTED_KEY_LENGTH:
        msg = "RIJNDAEL_UNSUPPORTED_KEY_LENGTH";
        break;
      case RIJNDAEL_BAD_KEY:
        msg = "RIJNDAEL_BAD_KEY";
        break;
      case RIJNDAEL_NOT_INITIALIZED:
        msg = "RIJNDAEL_NOT_INITIALIZED";
        break;
      case RIJNDAEL_BAD_DIRECTION:
        msg = "RIJNDAEL_BAD_DIRECTION";
        break;
      case RIJNDAEL_CORRUPTED_DATA:
        msg = "RIJNDAEL_CORRUPTED_DATA";
        break;
      default:
        msg = "unknown error";
        break;
    }

    PyErr_SetString(PyExc_ValueError, msg);

    return NULL;
}

%}

%typemap(in) (const UINT8 *key) {
    if (!PyString_Check($input))
        SWIG_fail;

    $1 = (UINT8 *) PyString_AsString($input);
}

%typemap(in) (const UINT8 *input, int inputBits, UINT8 *outBuffer) {
    if (!PyString_Check($input))
        SWIG_fail;

    PyString_AsStringAndSize($input, (char **) &$1, &$2);
    $3 = (UINT8 *) alloca($2);
    $2 <<= 3;
}

%typemap(argout) (const UINT8 *input, int inputBits, UINT8 *outBuffer) {
    Py_DECREF($result);
    if (result < 0)
        $result = reportError(result);
    else
        $result = PyString_FromStringAndSize((char *) $3, result >> 3);
}

%typemap(in) (const UINT8 *input, int inputBytes, UINT8 *outBuffer) {
    if (!PyString_Check($input))
        SWIG_fail;

    PyString_AsStringAndSize($input, (char **) &$1, &$2);
    $3 = (UINT8 *) alloca($2 + 16);
}

%typemap(argout) (const UINT8 *input, int inputBytes, UINT8 *outBuffer) {
    Py_DECREF($result);
    if (result < 0)
        $result = reportError(result);
    else
        $result = PyString_FromStringAndSize((char *) $3, result);
}


class Rijndael {
public:
    enum Direction { Encrypt, Decrypt };
    enum Mode { ECB, CBC, CFB1 };
    enum KeyLength { Key16Bytes, Key24Bytes, Key32Bytes };
    Rijndael();
    ~Rijndael();
    int init(Mode mode, Direction direction, const UINT8 *key,
             KeyLength keyLength);
    int blockEncrypt(const UINT8 *input, int inputBits, UINT8 *outBuffer);
    int padEncrypt(const UINT8 *input, int inputBytes, UINT8 *outBuffer);
    int blockDecrypt(const UINT8 *input, int inputBits, UINT8 *outBuffer);
    int padDecrypt(const UINT8 *input, int inputBytes, UINT8 *outBuffer);
};
