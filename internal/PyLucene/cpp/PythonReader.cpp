
#include <gcj/cni.h>
#include <wchar.h>
#include <java/lang/RuntimeException.h>
#include <java/lang/StringBuffer.h>

#include "Python.h"
#include "org/osafoundation/io/PythonReader.h"

/**
 * The native functions declared in org.osafoundation.io.PythonReader
 * 
 * @author Andi Vajda
 */

namespace org {
    namespace osafoundation {
        namespace io {

            void PythonReader::close(void)
            {
                PyObject_CallMethod(*(PyObject **) &pythonReader,
                                    "close", NULL);
            }

            jint PythonReader::read(jcharArray buf, jint offset, jint len)
            {
                PyUnicodeObject *s = (PyUnicodeObject *)
                    PyObject_CallMethod(*(PyObject **) &pythonReader, "read",
                                        "(i)", len);

                if (s == NULL)
                {
                    PyObject *type, *value, *traceback;
                    PyObject *typeName, *valueName, *file;
                    java::lang::StringBuffer *msg =
                        new java::lang::StringBuffer();

//                    PyThreadState *state = PyThreadState_Get();
//                    PyTraceBack_Here(state->frame);

                    PyErr_Fetch(&type, &value, &traceback);

//                    file = PyFile_FromFile(stderr, "stderr", "w", NULL);
//                    PyFile_WriteString("Begin original traceback:\n", file);
//                    PyTraceBack_Print(traceback, file);
//                    PyFile_WriteString("End original traceback:\n", file);

                    typeName = PyObject_GetAttrString(type, "__name__");
                    valueName = PyObject_Str(value);

                    msg->append(JvNewStringUTF(PyString_AsString(typeName)));
                    msg->append(JvNewStringUTF(": "));
                    msg->append(JvNewStringUTF(PyString_AsString(valueName)));

                    throw new java::lang::RuntimeException(msg->toString());
                }
                else
                {
                    int length = s->length;

                    if (length == 0)
                        return -1;
                    else
                    {
                        int size = buf->length;
                        jchar *dest = elements(buf);
                        Py_UNICODE *src = s->str;

                        if (offset + length > size)
                            length = size - offset;

                        for (int i = offset; i < offset + length; i++)
                            dest[i] = src[i];

                        return length;
                    }
                }
            }
        }
    }
}
