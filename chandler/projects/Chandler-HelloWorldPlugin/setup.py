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

#options = dict(install=dict(install_lib="...", install_scripts="...")

from setuptools import setup

setup(
    name = "Chandler-HelloWorldPlugin",
    version = "0.2",
    description = "This is just an example plugin project",
    author = "Phillip J. Eby",
    author_email = "pje@telecommunity.com",
    test_suite = "hello_world.tests",
    packages = ["hello_world"],
    include_package_data = True,
    entry_points = {
        "chandler.parcels": ["Hello World = hello_world"]
    },
    categories = ["Development Status :: 5 - Production/Stable",
                  "Environment :: Plugins",
                  "Framework :: Chandler",
                  "Intended Audience :: Developers",
                  "License :: OSI Approved :: Apache Software License",
                  "Operating System :: OS Independent",
                  "Programming Language :: Python",
                  "Topic :: Office/Business :: Groupware",
                  "Topic :: Software Development :: Documentation"],
    long_description = """
This plugin is just an example to show how minimal a plugin project can be.
It doesn't actually do anything, but is a complete example with a setup
script and tests.

If you want to experiment with its code, you can use::

    RunPython setup.py develop

to install it in development mode (where you can make changes and have them
take effect whenever Chandler is restarted), or you can use::

    RunPython setup.py install

to install it as an ``.egg`` file.

Note that when installed as an egg file, changes made to the source code will
not affect Chandler execution, until you run ``setup.py install`` or ``setup.py
develop`` again.

If you want to run this plugin's tests (which also don't do anything), use::

    RunPython setup.py test

The only thing this plugin actually does when Chandler is run, is to write an
entry to the log file when it is first loaded.  The entry will appear only if
the parcel has just been installed in a fresh repository, or if it is the first
time running a new or changed version of the parcel.

For more information on this plugin and the plugin development process, see
the original proposal at:

 http://lists.osafoundation.org/pipermail/chandler-dev/2006-March/005552.html

The svn sources for this plugin are at:

 http://svn.osafoundation.org/chandler/trunk/chandler/projects/Chandler-HelloWorldPlugin#egg=Chandler_HelloWorldPlugin-dev

and can be retrieved with ``RunPython -m easy_install --editable Chandler_HelloWorldPlugin==dev``.
"""
)
