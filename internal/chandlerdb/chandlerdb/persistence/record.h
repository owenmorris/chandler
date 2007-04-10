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

#ifndef _RECORD_H
#define _RECORD_H

typedef struct {
    PyObject_HEAD
    int size;
    PyObject *pairs;
    PyObject *partial;
    int partialSize;
    int valueType;
} t_record;

enum {
    R_NONE = 0,
    R_TRUE,
    R_FALSE,
    R_KEYWORD,           /* str or utf-8 unicode, 1 <= len <= 127, or None */
    R_SYMBOL,            /* str or ascii unicode, 1 <= len <= 255, or None */
    R_UUID,              /* 16 byte uuid                                   */
    R_UUID_OR_NONE,
    R_UUID_OR_SYMBOL,
    R_UUID_OR_KEYWORD,
    R_STRING,            /* str or utf-8 unicode, 0 <= len <= 1^31 - 1     */
    R_STRING_OR_NONE,
    R_HASH,              /* hash of str or utf-8 unicode                   */
    R_INT,               /* 32 bit signed long int                         */
    R_SHORT,             /* 16 bit signed short int                        */
    R_BYTE,              /* 8 bit unsigned char                            */
    R_BOOLEAN,           /* 8 bit R_TRUE, R_FALSE or R_NONE                */
    R_LONG,              /* 64 bit signed long long int                    */
    R_DOUBLE,            /* 64 bit double float                            */
    R_RECORD,            /* a nested record                                */
};


int _t_record_inplace_concat(t_record *self, PyObject *args);
int _t_record_write(t_record *record, unsigned char *data, int len);
int _t_record_read(t_record *self, unsigned char *data, int len);
t_record *_t_record_new_read(PyObject *args);
PyObject *t_record_getData(t_record *self);
PyObject *t_record_getTypes(t_record *self);
PyObject *_t_record_item(t_record *self, Py_ssize_t i); /* borrowed ref */

#endif /* _RECORD_H */
