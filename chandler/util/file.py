"""
File-specific utilities.

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import os, shutil

def copyfile(src, dst, flags=os.O_CREAT | os.O_EXCL, mode=0700):
    """
    Smarter copy. You can specify flags and mode on the destination file.

    @param src:   Source file name
    @param dst:   Destination file name
    @param flags: Flags on the dst file. Default flags prevent overwriting.
    @param mode:  Permissions for dst file. Defaults to user only.
    """
    fdst = os.fdopen(os.open(dst, flags | os.O_WRONLY, mode), 'w')
    fsrc = os.fdopen(os.open(src, os.O_RDONLY))
    shutil.copyfileobj(fsrc, fdst)
    fsrc.close()
    fdst.close()
