#!/usr/bin/env python
#   Copyright (c) 2006 Open Source Applications Foundation
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
"""

#
# TODO Implement logging
# TODO Add Signal checks so if main program is halted all child programs are killed
#

import sys, os, unittest
from optparse import OptionParser
from types import *
from util import killableprocess

    # tests to run if no tests are specified on the command line
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


_templist = []

def buildList(tests):
    for item in tests:
        if isinstance(item, unittest.TestSuite):
            buildList(item)
        else:
            _templist.append(item.id())

    return _templist


def buildTestList(args, individual=False):
    sys.argv = args[:]

    from application import Utility

    options = Utility.initOptions()

    Utility.initProfileDir(options)
    Utility.initI18n(options)
    Utility.initLogging(options)

    args    += options.args
    testlist = []

    if len(args) == 0:
        if options.verbose:
            print 'defaulting to all modules'

        testlist = _all_modules
    else:
        # if individual tests are required (-u) then we need to
        # discover each test name so we can pass it to run_tests
        # otherwise we can just pass the parameters to run_tests
        # because it will discover them
        if individual:
            from util import test_finder

            loader = test_finder.ScanningLoader()
            tests  = loader.loadTestsFromNames(args, None)

            testlist = buildList(tests)
        else:
            testlist += args

    return testlist


def runSuites(sys_argv):
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

    unittest.main(module=None, argv=args, testLoader=test_finder.ScanningLoader())


def callRunTest(cmd):
    if options.verbose:
        print 'Calling:', cmd

    p = killableprocess.Popen(' '.join(cmd), shell=True)
    r = os.waitpid(p.pid, 0)

    return r[1]


def runSuite(testlist):
    print 'Running tests as a suite'

    cmd = ['./release/RunPython', './tools/run_tests.py']

    if options.verbose:
        cmd += ['-v']

    cmd += testlist

    return callRunTest(cmd)


def runIndividual(testlist):
    print 'Running each test individually'

    r  = 0
    rt = ['./release/RunPython', './tools/run_tests.py']

    if options.verbose:
        rt += ['-v']

    for test in testlist:
        cmd = rt + [test]

        r = callRunTest(cmd)

        if r <> 0:
            break

    return r


if __name__ == '__main__':
    options = parseOptions()

    if options.help:
        print __doc__
        sys.exit(2)

    if options.unitSuite and options.unit:
        print "both --unit and --unitSuite are specified, but only one of them is allowed at a time."
        sys.exit(1)

    testlist = buildTestList(options.args, options.unit)

    if options.unitSuite:
        r = runSuite(testlist)

        if r <> 0:
            print '\n\nerror during run [%s]' % r
            sys.exit(r)

    if options.unit:
        r = runIndividual(testlist)

        if r <> 0:
            print '\n\nerror during run [%s]' % r
            sys.exit(r)

