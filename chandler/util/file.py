#   Copyright (c) 2005-2008 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
File-specific utilities.
"""

import os, shutil

def copy(src, dst, flags=os.O_CREAT | os.O_EXCL, mode=0700):
    """
    Smarter copy. You can specify flags and mode on the destination file.

    @param src:   Source file name
    @param dst:   Destination file name
    @param flags: Flags on the dst file. Default flags prevent overwriting.
    @param mode:  Permissions for dst file. Defaults to user only.
    """
    fdst = os.fdopen(os.open(dst, flags | os.O_WRONLY, mode), 'w')
    try:
        fsrc = os.fdopen(os.open(src, os.O_RDONLY))
        shutil.copyfileobj(fsrc, fdst)
    finally:
        fdst.close()
        fsrc.close()
