
/*
 * The Item C type
 */

typedef struct {
    PyObject_HEAD
    unsigned long lastAccess;
    unsigned long status;
    unsigned long version;
    PyObject *uuid;
    PyObject *name;
    PyObject *values;
    PyObject *references;
    PyObject *kind;
    PyObject *parent;
    PyObject *children;
    PyObject *root;
    PyObject *acls;
} t_item;

enum {
    DELETED    = 0x00000001,
    VDIRTY     = 0x00000002,          /* literal or ref changed */
    DELETING   = 0x00000004,
    RAW        = 0x00000008,
    FDIRTY     = 0x00000010,          /* fresh dirty since last mapChange() */
    SCHEMA     = 0x00000020,
    NEW        = 0x00000040,
    STALE      = 0x00000080,
    NDIRTY     = 0x00000100,          /* parent, name or kind changed */
    CDIRTY     = 0x00000200,          /* children list changed */
    RDIRTY     = 0x00000400,          /* ref collection changed */
    CORESCHEMA = 0x00000800,          /* core schema item */
    CONTAINER  = 0x00001000,          /* has children */
    ADIRTY     = 0x00002000,          /* acl(s) changed */
    PINNED     = 0x00004000,          /* auto-refresh, don't stale */
    NODIRTY    = 0x00008000,          /* turn off dirtying */
    VMERGED    = 0x00010000,
    RMERGED    = 0x00020000,
    NMERGED    = 0x00040000,
    CMERGED    = 0x00080000,
    COPYEXPORT = 0x00100000,          /* item instance is copied on export */
    IMPORTING  = 0x00200000,          /* item is being imported */
};

enum {
    VRDIRTY    = VDIRTY | RDIRTY,
    DIRTY      = VDIRTY | RDIRTY | NDIRTY | CDIRTY,
    MERGED     = VMERGED | RMERGED | NMERGED | CMERGED,
    SAVEMASK   = (DIRTY | ADIRTY |
                  NEW | DELETED |
                  SCHEMA | CORESCHEMA | CONTAINER),
};
