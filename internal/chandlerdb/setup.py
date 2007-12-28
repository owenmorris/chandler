#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from setuptools import setup, Extension

def main():

    PREFIX = os.environ['PREFIX']
    DB_VER = os.environ['DB_VER']
    VERSION = os.environ['VERSION']
    DEBUG = int(os.environ.get('DEBUG', '0'))

    extensions = []
    defines = ['-DVERSION="%s"' %(VERSION)]

    sources=['chandlerdb/util/uuid.c',
             'chandlerdb/util/pyuuid.c',
             'chandlerdb/util/linkedmap.c',
             'chandlerdb/util/skiplist.c',
             'chandlerdb/util/hashtuple.c',
             'chandlerdb/util/nil.c',
             'chandlerdb/util/ctxmgr.c',
             'chandlerdb/util/iterator.c',
             'chandlerdb/util/persistentvalue.c',
             'rijndael-3.0/rijndael-api-fst.c',
             'rijndael-3.0/rijndael-alg-fst.c',
             'chandlerdb/util/rijndael.c',
             'chandlerdb/util/c.c']
    if os.name == 'nt':
        defines = ['-DWINDOWS', '-DVERSION=\\"%s\\"' %(VERSION)]
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
                                         'chandlerdb/item/itemref.c',
                                         'chandlerdb/item/values.c',
                                         'chandlerdb/item/itemvalue.c',
                                         'chandlerdb/item/sequence.c',
                                         'chandlerdb/item/mapping.c',
                                         'chandlerdb/item/set.c',
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
                           'chandlerdb/persistence/record.c',
                           'chandlerdb/persistence/store.c',
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
                        extra_compile_args = defines,
                        library_dirs=[os.path.join(PREFIX, 'db', 'lib')],
                        include_dirs=[os.path.join(PREFIX, 'db', 'include')],
                        libraries=['db-%s' %(DB_VER)])
    extensions.append(ext)

    setup(name = 'chandlerdb',
          version = VERSION,
          packages = ['chandlerdb',
                      'chandlerdb.item',
                      'chandlerdb.schema',
                      'chandlerdb.persistence',
                      'chandlerdb.util'],
          ext_modules = extensions,
          test_suite = 'tests',
          zip_safe = os.name != 'nt' or DEBUG == 0,
          include_package_data = True,
          exclude_package_data = {'': ['*.c', '*.h', '*.py']})

if __name__ == "__main__":
    main()
