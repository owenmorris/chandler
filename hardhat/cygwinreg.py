__version__     = "$Revision$"
__date__        = "$Date$"
__copyright__   = "Copyright (c) 2003 Open Source Applications Foundation"
__license__     = "GPL -- see LICENSE.txt"


"""
  Partial implementation of _winreg. Not all api's supported, many
supported incorrectly and inefficiently.
"""

import os, os.path, string

HKEY_CLASSES_ROOT = "HKEY_CLASSES_ROOT"
HKEY_LOCAL_MACHINE = "HKEY_LOCAL_MACHINE"
HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
HKEY_USERS = "HKEY_USERS"

_handles = []

def OpenKeyEx(base, key):
    regpath = string.join(["/proc/registry", base, key], "/")
    regpath = string.join(string.split(regpath, "\\"), "/")
    if os.path.exists(regpath):
        _handles.append(regpath)
        return len(_handles)-1
    raise error

def EnumKey(handle, index):
    keys = []
    items = os.listdir(_handles[handle])
    for item in items:
        if os.path.isdir(_handles[handle]+"/"+item):
            keys.append(item)
    keys.sort()
    if len(keys) <= index:
        raise error
    return keys[index]


def EnumValue(handle, index):
    values = []
    items = os.listdir(_handles[handle])
    for item in items:
        if os.path.isfile(_handles[handle]+"/"+item):
            values.append(item)
    values.sort()
    if index >= len(values):
        raise error
    value = values[index]
    valuefile = file(_handles[handle] + "/" + value, "r")
    buf = valuefile.readline()
    valuefile.close()
    if len(buf) > 0 and ord(buf [-1]) == 0:
        buf = buf[:-1]
    return ( value, buf, 1 )

class error(Exception):
    pass
