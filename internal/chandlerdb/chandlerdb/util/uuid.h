
typedef struct {
    PyObject_HEAD
    PyObject *uuid;
    int hash;
} t_uuid;

typedef int (*PyUUID_Check_fn)(PyObject *obj);
