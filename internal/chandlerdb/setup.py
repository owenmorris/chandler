
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, shutil
from distutils.core import setup, Extension

def main():

    extensions = []
    modules = ['chandlerdb.__init__',
               'chandlerdb.util.__init__']

    extensions.append(Extension('chandlerdb.util._uuid',
                                sources=['chandlerdb/util/uuid.c',
                                         'chandlerdb/util/pyuuid.c']))
    modules.append('chandlerdb.util.UUID')

    extensions.append(Extension('chandlerdb.util._rijndael',
                                sources=['rijndael-2.4/rijndael.cpp',
                                         'chandlerdb/util/rijndael.i'],
                                include_dirs=['rijndael-2.4']))

    if os.name == 'nt':
        extensions.append(Extension('chandlerdb.util.lock',
                                    sources=['chandlerdb/util/lock.c']))
    elif os.name == 'posix':
        modules.append('chandlerdb.util.lock')
    else:
        raise ValueError, 'unsupported os: %s' %(os.name)

    setup(name='chandlerdb', version='0.4',
          ext_modules=extensions,
          py_modules=modules)
    if os.name == 'nt':
        shutil.move('rijndael.py', 'chandlerdb/util/rijndael.py')
    setup(name='chandlerdb', version='0.4',
          py_modules=['chandlerdb.util.rijndael'])

if __name__ == "__main__":
    main()
