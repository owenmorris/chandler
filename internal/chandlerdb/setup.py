
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, shutil
from distutils.core import setup, Extension

def main():

    PREFIX = os.environ['PREFIX']
    
    extensions = []
    modules = ['chandlerdb.__init__',
               'chandlerdb.util.__init__',
               'chandlerdb.schema.__init__',
               'chandlerdb.item.__init__',
               'chandlerdb.item.ItemError',
               'chandlerdb.persistence.__init__']

    extensions.append(Extension('chandlerdb.util.uuid',
                                sources=['chandlerdb/util/uuid.c',
                                         'chandlerdb/util/pyuuid.c']))

    extensions.append(Extension('chandlerdb.util._rijndael',
                                sources=['rijndael-2.4/rijndael.cpp',
                                         'chandlerdb/util/rijndael.i'],
                                include_dirs=['rijndael-2.4']))

    extensions.append(Extension('chandlerdb.schema.descriptor',
                                sources=['chandlerdb/schema/descriptor.c']))

    extensions.append(Extension('chandlerdb.item.item',
                                sources=['chandlerdb/item/item.c']))

    if os.name == 'nt':
        ext = Extension('chandlerdb.persistence.container',
                        sources=['chandlerdb/persistence/container.c'],
                        include_dirs=[os.path.join(PREFIX, 'include', 'db')],
                        library_dirs=[os.path.join(PREFIX, 'lib')],
                        libraries=['libdb43', 'ws2_32'])
    else:
        ext = Extension('chandlerdb.persistence.container',
                        sources=['chandlerdb/persistence/container.c'],
                        library_dirs=[os.path.join(PREFIX, 'db', 'lib')],
                        include_dirs=[os.path.join(PREFIX, 'db', 'include')],
                        libraries=['db-4.3'])
    extensions.append(ext)

    if os.name in ('nt','posix'):
        modules.append('chandlerdb.util.lock')
    else:
        raise ValueError, 'unsupported os: %s' %(os.name)

    setup(name='chandlerdb', version='0.5',
          ext_modules=extensions,
          py_modules=modules)
    if os.name == 'nt' and os.path.exists('rijndael.py'):
        shutil.move('rijndael.py', 'chandlerdb/util/rijndael.py')
    setup(name='chandlerdb', version='0.5',
          py_modules=['chandlerdb.util.rijndael'])

if __name__ == "__main__":
    main()
