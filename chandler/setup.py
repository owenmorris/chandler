# Copyright (c) 2005 Open Source Applications Foundation.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions: 
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software. 
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import sys
from ez_setup import use_setuptools

use_setuptools()

import setuptools

class TestCommand(setuptools.Command):
    """Command to run unit tests"""

    description = "run unit tests using twisted.trial"

    user_options = [
        ('suite=','s',"Test suite to run (e.g. 'some_module.test_suite')"),
    ]

    suite = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.suite = self.suite or self.distribution.test_suite
        self.test_args = [self.suite]
        
    def run(self):

        if self.suite:
            cmd = ' '.join(self.test_args)
            if self.dry_run:
                self.announce('skipping running twisted.trial on %s" (dry run)' % cmd)
            else:
                self.announce('running "skipping running twisted.trial %s"' % cmd)
                from twisted.scripts.trial import run
                
                sys.argv = [sys.argv[0]] + self.test_args

                run()

class MakeDocsCommand(setuptools.Command):
    """Command to generate documentation"""

    description = "create html documentation"

    user_options = [
        ('output-dir=','o',"Output directory for html tree"),
    ]

    output_dir = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.output_dir = self.output_dir or "doc"

    def run(self):
        if self.output_dir:
            import epydoc.cli
            import sys
            import os.path
            import glob
            
            srcDir = os.path.join('zanshin')

            modules = [os.path.splitext(os.path.basename(path))[0]
                       for path in glob.glob(os.path.join(srcDir, '*.py'))]

            try:
                modules.remove('__init__')
            except ValueError:
                pass
                
            modules = ['zanshin.' + path for path in modules]

            sys.argv = ["epydoc.py", "--html", "--no-private", "--verbose",
                        "--output", self.output_dir]
            sys.argv += modules
            
            if self.dry_run:
                self.announce('skipping running %s (dry run)' % (sys.argv))
            else:
                self.announce('running %s' % (sys.argv))
                epydoc.cli.cli()


setuptools.setup(
    name="zanshin",
    version="0.6",
    zip_safe=True,
    classifiers=["Development Status :: 3 - Alpha",
                 "Environment :: Console",
                 "Framework :: Chandler",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python",
                 "Topic :: Software Development :: Libraries :: Python Modules"],
    description="High-level library for HTTP, WebDAV and CalDAV operations",
    long_description=open("README.txt").read(),
    author="Grant Baillie",
    author_email="grant@osafoundation.org",
    url="http://chandlerproject.org/Projects/ZanshinProject",
    test_suite="tests",
    packages=["zanshin"],
    include_package_data=True,
    cmdclass={'test':TestCommand, 'doc':MakeDocsCommand},
)
