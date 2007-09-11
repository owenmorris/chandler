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


from setuptools import setup

setup(
    name = "Chandler-HelloWorldPlugin",
    version = "0.8",
    description = "This is just an example plugin project",
    author = "Phillip J. Eby",
    author_email = "pje@telecommunity.com",
    test_suite = "hello_world.tests",
    packages = ["hello_world"],
    include_package_data = True,
    entry_points = {
        "chandler.parcels": ["Hello World = hello_world"]
    },
    classifiers = ["Development Status :: 5 - Production/Stable",
                   "Environment :: Plugins",
                   "Framework :: Chandler",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: Apache Software License",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Office/Business :: Groupware",
                   "Topic :: Software Development :: Documentation"],
    long_description = open('README.txt').read(),
)

