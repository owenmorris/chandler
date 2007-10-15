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
    name = "Chandler-TwitterPlugin",
    version = "0.8",
    description = "Twitter support for Chandler",
    author = "Morgen Sagen",
    test_suite = "chandler_twitter.tests",
    packages = ["chandler_twitter"],
    include_package_data = True,
    # install_requires = ["python-twitter>=0.5"],
    entry_points = {
        "chandler.parcels": ["Twitter Integration = chandler_twitter"],
    },
    classifiers = ["Development Status :: 3 - Alpha",
                   "Environment :: Plugins",
                   "Framework :: Chandler",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: Apache Software License",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Office/Business :: Groupware"],
    long_description = open('README.txt').read(),
)

#        "chandler.chex_mixins": ["Twitter Integration = chandler_twitter:TwitterTranslator"],
