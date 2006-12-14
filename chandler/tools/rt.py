#!/usr/bin/env python
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

"""
rt.py -- Run Chandler tests

Usage
-----

NOTE: rt.py must be called using Chandler's RunPython

Run Unit Tests

    All::

        RunPython ./tools/rt.py -U

    Specific python module::

        RunPython ./tools/rt.py -U repository.tests.TestText

    Specific test class::

        RunPython ./tools/rt.py -U repository.tests.TestText.TestText

    Specific test method::

        RunPython ./tools/rt.py -U repository.tests.TestText.TestText.testAppend

    All tests in a suite::

        RunPython ./tools/rt.py -U application.tests.TestSchemaAPI.suite

    All tests in all modules in a package and its sub-packages::

        RunPython ./tools/rt.py -U application.tests


If you have doctests or other tests not based on the Python unittest
module, you should add them to an 'additional_tests' function in your
module, in order for run_test's test finder to be able to locate them.
The function should return a 'unittest.TestSuite' object (such as is
returned by 'doctest.DocFileSuite' or 'doctest.DocTestSuite').

Logging is configured in the same manner as for Chandler or headless.py,
i.e. by setting the CHANDLERLOGCONFIG environment variable or the -L <file>
command line argument to specify a logging configuration file.  For example:

    RunPython ./tools/rt.py -L custom.conf -v application osaf

(Note: specifying package names on the 'run_tests' command line will
cause *all* modules in all sub-packages of that package to be imported.)

"""

import sys, unittest
from optparse import OptionParser
from types import *

_all_modules = ['application', 'i18n', 'repository', 'osaf']

def parseOptions():
    _configItems = {
        'mode':      ('-m', '--mode',               's', None,  'debug or release; by default attempts both'),
        'continue':  ('-C', '--continue',           'b', False, 'Continue even after test failures'),
        'unit':      ('-u', '--unit',               'b', False, 'unit tests each in own process'),
        'unitSuite': ('-U', '--unitSuite',          'b', False, 'unit tests in same process, all arguments treated as unittest.main arguments'),
        'verbose':   ('-v', '--verbose',            'b', False, 'Verbose output for unit tests'),
        'restored':  ('-R', '--restoredRepository', 'b', False, 'unit tests with restored repository instead of creating new for each test'),
        'funcSuite': ('-f', '--funcSuite',          'b', False, 'Functional test suite'),
        'func':      ('-F', '--func',               'b', False, 'Functional tests each in own process'),
        'perf':      ('-p', '--perf',               'b', False, 'Performance tests'),
        'profile':   ('-P', '--profile',            'b', False, 'Profile performance tests'),
        'single':    ('-t', '--test',               's', None,  'Run single test'),
        'tbox':      ('-T', '--tbox',               'b', False, 'Tinderbox output mode'),
        'noEnv':     ('-i', '--ignoreEnv',          'b', False, 'Ignore environment variables'),
        'config':    ('-L', '',                     's', None,  'Custom Chandler logging configuration file'),
        'help':      ('-H', '',                     'b', False, 'Extended help'),
    }

    # %prog expands to os.path.basename(sys.argv[0])
    usage  = "usage: %prog [options]\n" + \
             "       %prog [options] -U module"
    parser = OptionParser(usage=usage, version="%prog")

    for key in _configItems:
        (shortCmd, longCmd, optionType, defaultValue, helpText) = _configItems[key]

        if optionType == 'b':
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              action='store_true',
                              default=defaultValue,
                              help=helpText)
        else:
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              default=defaultValue,
                              help=helpText)

    (options, args) = parser.parse_args()
    options.args    = args

    return options


def dumpTests(tests):
    for item in tests:
        if isinstance(item, unittest.TestSuite):
            dumpTests(item)
        else:
            print 'Test: %s' % item

def unitSuite(sys_argv):
    sys.argv = sys_argv[:]

    # Need to remove incompatible options
    sys.argv.remove('-U')

    from application import Utility
    from util import test_finder

    options = Utility.initOptions()

    Utility.initProfileDir(options)
    Utility.initI18n(options)
    Utility.initLogging(options)

    # Rebuild the command line for unittest.main
    args = [sys.argv[0]]

    # options.args has all the leftover arguments from Utility
    args += options.args

    if len(args) == 1:
        args = args + _all_modules

    if options.verbose:
        args.insert(1, '-v')

    print args

    unittest.main(module=None, argv=args, testLoader=test_finder.ScanningLoader())


if __name__ == '__main__':
    sys_argv = sys.argv[:]
    options  = parseOptions()

    if options.help:
        print __doc__
        sys.exit(2)

    if options.unitSuite and options.unit:
        print "both --unit and --unitSuite are specified, but only one of them is allowed at a time."
        sys.exit(1)

    if options.unitSuite:
        # XXX We should probably launch run_tests.py again with Chandler
        # XXX python in a subprocess so that we don't need to terminate.
        unitSuite(sys_argv)
        sys.exit(0)

    print __doc__
    raise NotImplementedError
