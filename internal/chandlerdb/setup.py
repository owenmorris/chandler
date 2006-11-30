#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

import os
from distutils.core import setup, Extension

def main():

    PREFIX = os.environ['PREFIX']
    DB_VER = os.environ['DB_VER']
    DEBUG = int(os.environ.get('DEBUG', '0'))

    extensions = []
    modules = ['chandlerdb.__init__',
               'chandlerdb.util.__init__',
               'chandlerdb.util.lock',
               'chandlerdb.util.debugger',
               'chandlerdb.schema.__init__',
               'chandlerdb.item.__init__',
               'chandlerdb.item.ItemError',
               'chandlerdb.item.ItemValue',
               'chandlerdb.persistence.__init__']

    defines = []
    sources=['chandlerdb/util/uuid.c',
             'chandlerdb/util/pyuuid.c',
             'chandlerdb/util/singleref.c',
             'chandlerdb/util/linkedmap.c',
             'chandlerdb/util/skiplist.c',
             'chandlerdb/util/hashtuple.c',
             'chandlerdb/util/nil.c',
             'rijndael-3.0/rijndael-api-fst.c',
             'rijndael-3.0/rijndael-alg-fst.c',
             'chandlerdb/util/rijndael.c',
             'chandlerdb/util/c.c']
    if os.name == 'nt':
        defines = ['-DWINDOWS']
        sources.append('chandlerdb/util/lock.c')

    extensions.append(Extension('chandlerdb.util.c',
                                sources = sources,
                                extra_compile_args = defines,
                                include_dirs=['rijndael-3.0']))

    extensions.append(Extension('chandlerdb.schema.c',
                                extra_compile_args = defines,
                                sources=['chandlerdb/schema/descriptor.c',
                                         'chandlerdb/schema/attribute.c',
                                         'chandlerdb/schema/kind.c',
                                         'chandlerdb/schema/redirector.c',
                                         'chandlerdb/schema/c.c']))

    extensions.append(Extension('chandlerdb.item.c',
                                extra_compile_args = defines,
                                sources=['chandlerdb/item/item.c',
                                         'chandlerdb/item/values.c',
                                         'chandlerdb/item/indexes.c',
                                         'chandlerdb/item/c.c']))

    persistence_sources = ['chandlerdb/persistence/repository.c',
                           'chandlerdb/persistence/view.c',
                           'chandlerdb/persistence/container.c',
                           'chandlerdb/persistence/sequence.c',
                           'chandlerdb/persistence/db.c',
                           'chandlerdb/persistence/cursor.c',
                           'chandlerdb/persistence/env.c',
                           'chandlerdb/persistence/txn.c',
                           'chandlerdb/persistence/lock.c',
                           'chandlerdb/persistence/c.c']
    if os.name == 'nt':
        dbver = ''.join(DB_VER.split('.'))
        if DEBUG == 0:
            libdb_name = 'libdb%s' %(dbver)
        else:
            libdb_name = 'libdb%sd' %(dbver)
        ext = Extension('chandlerdb.persistence.c',
                        sources=persistence_sources,
                        extra_compile_args = defines,
                        include_dirs=[os.path.join(PREFIX, 'include', 'db')],
                        library_dirs=[os.path.join(PREFIX, 'lib')],
                        libraries=[libdb_name, 'ws2_32'])
    else:
        ext = Extension('chandlerdb.persistence.c',
                        sources=persistence_sources,
                        library_dirs=[os.path.join(PREFIX, 'db', 'lib')],
                        include_dirs=[os.path.join(PREFIX, 'db', 'include')],
                        libraries=['db-%s' %(DB_VER)])
    extensions.append(ext)

    setup(name='chandlerdb', version='0.5',
          ext_modules=extensions, py_modules=modules)

if __name__ == "__main__":
    main()
