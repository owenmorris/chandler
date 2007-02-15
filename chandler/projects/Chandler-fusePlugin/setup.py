#   Copyright (c) 2007 Open Source Applications Foundation
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


from setuptools import setup, Extension

FUSE=False

extensions = []
if FUSE:
    extensions.append(Extension('fuse.c',
                                sources = ['fuse/c/fuse.c',
                                           'fuse/c/c.c'],
                                libraries=['fuse']))

setup(name = "Chandler-fusePlugin",
      version = "0.1",
      description = "file system wrapper for Chandler repository",
      author = "OSAF",
      packages = ["fuse"],
      ext_modules = extensions,
      include_package_data = True,
      test_suite = "fuse.tests",
      entry_points = {"chandler.parcels": ["fuse = fuse"]})
