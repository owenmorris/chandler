
typedef struct {
    PyObject_HEAD
    PyObject *uuid;
    int hash;
} t_uuid;

typedef int (*PyUUID_Check_fn)(PyObject *obj);

/* steals reference to obj */
typedef PyObject *(*PyUUID_Make16_fn)(PyObject *obj);
