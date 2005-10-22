
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, shutil
from distutils.core import setup, Extension

def main():

    PREFIX = os.environ['PREFIX']
    DEBUG = int(os.environ.get('DEBUG', '0'))

    extensions = []
    modules = ['chandlerdb.__init__',
               'chandlerdb.util.__init__',
               'chandlerdb.schema.__init__',
               'chandlerdb.item.__init__',
               'chandlerdb.item.ItemError',
               'chandlerdb.item.ItemValue',
               'chandlerdb.persistence.__init__']

    if os.name in ('nt', 'posix'):
        modules.append('chandlerdb.util.lock')
    else:
        raise ValueError, 'unsupported os: %s' %(os.name)

    extensions.append(Extension('chandlerdb.util.c',
                                sources=['chandlerdb/util/uuid.c',
                                         'chandlerdb/util/pyuuid.c',
                                         'chandlerdb/util/singleref.c',
                                         'chandlerdb/util/linkedmap.c',
                                         'chandlerdb/util/skiplist.c',
                                         'rijndael-3.0/rijndael-api-fst.c',
                                         'rijndael-3.0/rijndael-alg-fst.c',
                                         'chandlerdb/util/rijndael.c',
                                         'chandlerdb/util/c.c'],
                                include_dirs=['rijndael-3.0']))

    extensions.append(Extension('chandlerdb.schema.c',
                                sources=['chandlerdb/schema/descriptor.c',
                                         'chandlerdb/schema/attribute.c',
                                         'chandlerdb/schema/kind.c',
                                         'chandlerdb/schema/c.c']))

    extensions.append(Extension('chandlerdb.item.c',
                                sources=['chandlerdb/item/item.c',
                                         'chandlerdb/item/values.c',
                                         'chandlerdb/item/c.c']))

    if os.name == 'nt':
        if DEBUG == 0:
            libdb_name = 'libdb43'
        else:
            libdb_name = 'libdb43d'
        ext = Extension('chandlerdb.persistence.c',
                        sources=['chandlerdb/persistence/repository.c',
                                 'chandlerdb/persistence/view.c',
                                 'chandlerdb/persistence/container.c',
                                 'chandlerdb/persistence/c.c'],
                        include_dirs=[os.path.join(PREFIX, 'include', 'db')],
                        library_dirs=[os.path.join(PREFIX, 'lib')],
                        libraries=[libdb_name, 'ws2_32'])
    else:
        ext = Extension('chandlerdb.persistence.c',
                        sources=['chandlerdb/persistence/repository.c',
                                 'chandlerdb/persistence/view.c',
                                 'chandlerdb/persistence/container.c',
                                 'chandlerdb/persistence/c.c'],
                        library_dirs=[os.path.join(PREFIX, 'db', 'lib')],
                        include_dirs=[os.path.join(PREFIX, 'db', 'include')],
                        libraries=['db-4.3'])
    extensions.append(ext)

    setup(name='chandlerdb', version='0.5',
          ext_modules=extensions, py_modules=modules)

if __name__ == "__main__":
    main()
