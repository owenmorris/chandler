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

import sys, os
import string
import unittest
import doctest
from optparse import OptionParser
from types import *
from util import killableprocess


modes = ['release', 'debug']

    # tests to run if no tests are specified on the command line
_all_modules = ['application', 'i18n', 'repository', 'osaf']

    # global variable to force a exit from the test run
    # even if options.nonstop is True
_stop_test_run = False


def parseOptions():
    _configItems = {
        'mode':      ('-m', '--mode',               's', None,  'debug or release; by default attempts both'),
        'nonstop':   ('-C', '--continue',           'b', False, 'Continue even after test failures'),
        'unit':      ('-u', '--unit',               'b', False, 'unit tests each in own process'),
        'unitSuite': ('-U', '--unitSuite',          'b', False, 'unit tests in same process, all arguments treated as unittest.main arguments'),
        'verbose':   ('-v', '--verbose',            'b', False, 'Verbose output for unit tests'),
        'restored':  ('-R', '--restoredRepository', 'b', False, 'unit tests with restored repository instead of creating new for each test'),
        'funcSuite': ('-f', '--funcSuite',          'b', False, 'Functional test suite'),
        'func':      ('-F', '--func',               'b', False, 'Functional tests each in own process'),
        'perf':      ('-p', '--perf',               'b', False, 'Performance tests'),
        'profile':   ('-P', '--profile',            'b', False, 'Profile performance tests'),
        'single':    ('-t', '--test',               's', '',    'Run single test'),
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

def buildUnitList(tests):
    """
    Scan thru the list of unit test instances and build
    a list of all individual test names.
    """
    for item in tests:
        if isinstance(item, unittest.TestSuite):
            buildUnitList(item)
        else:
            if isinstance(item, unittest.TestCase) and \
               not isinstance(item, doctest.DocTestCase):
                _templist.append(item.id())
            else:
                print "Skipping %s as it's not a TestCase instance" % item.id()

    return _templist


def buildUnitTestList(args, individual=False):
    """
    Pass the given command line arguments to our scanning loader
    and create a list of test names.
    """
    from application import Globals, Utility

    sys.argv = args[:]
    Globals.options = Utility.initOptions()
    options  = Globals.options

    Utility.initI18n(options)
    Utility.initLogging(options)

    args    += options.args
    tests    = []
    testlist = []

    if len(args) == 0:
        if options.verbose:
            print 'defaulting to all modules'

        testlist = _all_modules
    else:
        testlist += args

    # if individual tests are required (-u or -t) then we need to
    # discover each test name so we can pass it to run_tests
    # otherwise we can just pass the parameters to run_tests
    # because it will discover them
    if individual:
        from util import test_finder

        loader = test_finder.ScanningLoader()

        for item in testlist:
            tests += buildUnitList(loader.loadTestsFromName(item))
    else:
        tests = testlist

    return tests


def doCommand(cmd):
    """
    Run the given command and return the results.
    If during the wait a ctrl-c is pressed kill the cmd's process.
    """
    if options.verbose:
        print 'Calling:', cmd

    try:
        p = killableprocess.Popen(' '.join(cmd), shell=True)
        r = p.wait()

    except KeyboardInterrupt:
        _stop_test_run = True

        print '\nKeyboard Interrupt detected, stopping test run\n'

        try:
            r = p.kill(group=True)

        except OSError:
            r = p.wait()

    return r

def doUnitTest(test):
    """
    Run the given test for each of the active modes
    """
    result = 0

    for mode in modes:
        cmd = ['./%s/RunPython' % mode, './tools/run_tests.py']

        if options.verbose:
            cmd += ['-v']

        cmd += [test]

        result = doCommand(cmd)

        if (result <> 0 and not options.nonstop) or _stop_test_run:
            break

    return result

def runUnitSuite(testlist):
    """
    Call doUnitTest with all of the given test names
    """
    print 'Running tests as a suite'

    return doUnitTest(' '.join(testlist))


def runUnitTests(testlist):
    """
    Call doUnitTest once for each given test name
    """
    result = 0

    for test in testlist:
        result = doUnitTest(test)

        if result <> 0 and not options.nonstop:
            break

    return result


def runUnitTest(testlist, target):
    """
    Scan thru the list of tests and run each test that
    includes as part of it's class name the target name.
    """
    result   = 0
    tests    = []
    target_l = target.lower()

    for test in testlist:
        pieces   = test.split('.')
        pieces_l = []

        for item in pieces:
            pieces_l.append(item.lower())

        if target_l in pieces_l:
            i        = pieces_l.index(target_l)
            testname = '.'.join(pieces[:i + 1])

            tests.append(testname)

    if len(tests) > 0:
        result = runUnitTests(tests)

    return result

def runFuncSuite():
    pass


if __name__ == '__main__':
    options = parseOptions()

    if options.help:
        print __doc__
        sys.exit(2)

    if options.mode is not None:
        m = [options.mode]
    else:
        m = modes

    modes = []

    for item in m:
        if os.path.isdir(item):
            modes.append(item)
        else:
            print 'Requested mode (%s) not availble - ignoring' % item

    if options.unitSuite and options.unit:
        print "both --unit and --unitSuite are specified, but only one of them is allowed at a time."
        sys.exit(1)

    if options.single and (options.unitSuite or options.unit):
            print "Single test run (-t) only allowed by itself"
            sys.exit(1)

    testlist = buildUnitTestList(options.args, options.unit or len(options.single) > 0)
    result   = 0

    if options.unitSuite:
        result = runUnitSuite(testlist)

    if options.unit:
        result = runUnitTests(testlist)

    if options.single:
        result = runUnitTest(testlist, options.single)

    if options.funcSuite:
        result = runFuncSuite()

    if result <> 0:
        print '\n\nError generated during run: %s' % result
        sys.exit(result)

