#!/usr/bin/env python
#   Copyright (c) 2006-2007 Open Source Applications Foundation
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
# TODO Add Signal checks so if main program is halted all child programs are killed
# TODO Add -U (run all tests in same process) mode
#

import sys, os
import string
import glob
from optparse import OptionParser
import build_lib


global failedTests

failedTests = []

    # When the --ignoreEnv option is used the following
    # list of environment variable names will be deleted

_ignoreEnvNames = [ 'PARCELPATH',
                    'CHANDLERWEBSERVER',
                    'PROFILEDIR',
                    'CREATE',
                    'CHANDLERNOCATCH',
                    'CHANDLERCATCH',
                    'CHANDLERNOSPLASH',
                    'CHANDLERLOGCONFIG',
                    'CHANDLEROFFLINE',
                    'CHANDLERNONEXCLUSIVEREPO',
                    'MVCC',
                  ]


def log(msg, error=False):
    build_lib.log(msg, error=error)


def parseOptions():
    _configItems = {
        'mode':      ('-m', '--mode',               's', None,  'debug or release; by default attempts both'),
        'noStop':    ('-C', '--continue',           'b', False, 'Continue even after test failures'),
        'unit':      ('-u', '--unit',               'b', False, 'unit tests each in own process'),
        'verbose':   ('-v', '--verbose',            'b', False, 'Verbose output'),
        'funcSuite': ('-f', '--funcSuite',          'b', False, 'Functional test suite'),
        'perf':      ('-p', '--perf',               'b', False, 'Performance tests'),
        'single':    ('-t', '--test',               's', '',    'Run single test'),
        'noEnv':     ('-i', '--ignoreEnv',          'b', False, 'Ignore environment variables'),
        'logPath':   ('-l', '--logPath',            's', None,  'Directory where the test run output will be stored'),
        'quiet':     ('-q', '--quiet',              'b', False, 'Mute log echoing to stdout'),
        'help':      ('-H', '',                     'b', False, 'Extended help'),
        'dryrun':    ('-d', '--dryrun',             'b', False, 'Do all of the prep work but do not run any tests'),
        #'restored':  ('-R', '--restoredRepository', 'b', False, 'unit tests with restored repository instead of creating new for each test'),
        #'profile':   ('-P', '--profile',            'b', False, 'Profile performance tests'),
        #'tbox':      ('-T', '--tbox',               'b', False, 'Tinderbox output mode'),
        #'config':    ('-L', '',                     's', None,  'Custom Chandler logging configuration file'),
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

    checkOptions(options)

    return options


def checkOptions(options):
    if options.help:
        print __doc__
        sys.exit(2)

    options.toolsDir = os.path.abspath(os.path.dirname(__file__))

    if 'CHANDLERHOME' in os.environ:
        options.chandlerHome = os.path.realpath(os.environ['CHANDLERHOME'])
    else:
        options.chandlerHome = os.path.abspath(os.path.join(options.toolsDir, '..'))

    if 'CHANDLERBIN' in os.environ:
        options.chandlerBin = os.path.realpath(os.environ['CHANDLERBIN'])
    else:
        options.chandlerBin = options.chandlerHome

    options.parcelPath = os.path.join(options.chandlerHome, 'tools', 'QATestScripts', 'DataFiles')
    options.profileDir = os.path.join(options.chandlerHome, 'test_profile')

    if options.logPath is None:
        options.logPath = options.profileDir

    build_lib.initLog(os.path.join(options.logPath, 'rt.log'), prefix='', echo=(not options.quiet))

    if not os.path.isdir(options.chandlerBin):
        log('Unable to locate CHANDLERBIN directory', error=True)
        sys.exit(3)

    if options.single and options.unit:
        log('Single test run (-t) only allowed by itself', error=True)
        sys.exit(1)

    options.runpython   = {}
    options.runchandler = {}

    for mode in [ 'debug', 'release' ]:
        if os.name == 'nt' or sys.platform == 'cygwin':
            options.runpython[mode]   = os.path.join(options.chandlerBin, mode, 'RunPython.bat')
            options.runchandler[mode] = os.path.join(options.chandlerBin, mode, 'RunChandler.bat')
        else:
            options.runpython[mode]   = os.path.join(options.chandlerBin, mode, 'RunPython')
            options.runchandler[mode] = os.path.join(options.chandlerBin, mode, 'RunChandler')

    if options.noEnv:
        for item in _ignoreEnvNames:
            try:
                if item in os.environ:
                    os.environ.pop(item)
            except:
                log('Unable to remove "%s" from the environment' % item)


def findTestFiles(searchPath, excludeDirs, includePattern):
    result = []

    for item in glob.glob(os.path.join(searchPath, includePattern)):
        result.append(item)

    for item in os.listdir(searchPath):
        dirname = os.path.join(searchPath, item)

        if os.path.isdir(dirname):
            if item != '.svn' and dirname not in excludeDirs:
                result += findTestFiles(dirname, excludeDirs, includePattern)

    return result


def buildUnitTestList(options):
    excludeDirs = []

    if len(options.single) > 0:
        includePattern = options.single
    else:
        includePattern = 'Test*.py'

    for item in [ 'tools', 'util', 'projects', 'plugins', 'build', 'Chandler.egg-info' ]:
        excludeDirs.append('%s/%s' % (options.chandlerHome, item))

    for item in [ 'release', 'debug' ]:
        excludeDirs.append('%s/%s' % (options.chandlerBin, item))

    return findTestFiles(options.chandlerHome, excludeDirs, includePattern)


def runUnitTests(options):
    """
    Locate any unit tests (-u) or any of the named test (-t) and run them
    """
    testlist = buildUnitTestList(options)
    failed   = False

    if len(testlist) == 0:
        if options.unit:
            log('No unit tests found to run')
        else:
            log('Unit test %s not found' % options.single)

    else:
        for mode in options.modes:
            for test in testlist:
                if options.dryrun:
                    log('unittest: %s' % test)
                    result = 0
                else:
                    if options.verbose:
                        log('Running %s' % test)

                    result = build_lib.runCommand([ options.runpython[mode], test ])

                if result != 0:
                    failed = True
                    failedTests.append(test)

                    if not options.noStop:
                        break

            if failed and not options.noStop:
                break

    return failed


def runPluginTests(options):
    """
    Locate any plugin tests (-u)
    """
    testlist = findTestFiles(os.path.join(options.chandlerHome, 'projects'), [], 'setup.py')
    failed   = False

    if len(testlist) == 0:
        log('No plugin tests found to run')
    else:
        saveCWD = os.getcwd()

        for mode in options.modes:
            for test in testlist:
                if options.dryrun:
                    log('plugin: %s' % test)
                    result = 0
                else:
                    if options.verbose:
                        log('Running %s' % test)

                    #if [ "$OSTYPE" = "cygwin" ]; then
                    #    C_HOME=`cygpath -aw $C_DIR`
                    #    PARCEL_PATH=`cygpath -awp $PARCELPATH:$C_DIR/plugins`
                    #else
                    #    C_HOME=$C_DIR
                    #    PARCEL_PATH=$PARCELPATH:$C_DIR/plugins
                    #fi
                    #cd `dirname $setup`
                    #PARCELPATH=$PARCEL_PATH CHANDLERHOME=$C_HOME $CHANDLERBIN/$mode/$RUN_PYTHON
                    #   `basename $setup` test 2>&1 | tee $TESTLOG
                    env = os.environ.copy()
                    env['PARCELPATH']   = os.path.join(options.chandlerHome, 'plugins')
                    env['CHANDLERHOME'] = options.chandlerHome

                    os.chdir(os.path.dirname(test))

                    result = build_lib.runCommand([ options.runpython[mode], test, 'test' ], env=env)

                if result != 0:
                    failed = True
                    failedTests.append(test)

                    if not options.noStop:
                        break

            if failed and not options.noStop:
                break

        os.chdir(saveCWD)

    return failed


def runFuncSuite(options):
    """
    Run the Functional Test Suite
    """
    # $CHANDLERBIN/$mode/$RUN_CHANDLER --create --catch=tests $FORCE_CONT --profileDir="$PC_DIR" --parcelPath="$PP_DIR" --scriptTimeout=720 --scriptFile="$TESTNAME" -D1 -M2 2>&1 | tee $TESTLOG
    failed = False

    for mode in options.modes:
        cmd = [ options.runchandler[mode],
                '--create', '--catch=tests', '--scriptTimeout=720', '-D1', '-M2',
                '--profileDir=%s' % options.profileDir,
                '--parcelPath=%s' % options.parcelPath,
                '--scriptFile=%s' % os.path.join(options.chandlerHome, 'tools', 'cats', 'Functional', 'FunctionalTestSuite.py') ]

        if options.noStop:
            cmd += [ '-F' ]

        if options.dryrun:
            log('functest: %s' % ' '.join(cmd))
            result = 0
        else:
            if options.verbose:
                log('Running %s' % ' '.join(cmd))

            result = build_lib.runCommand(cmd)

        if result != 0:
            failed = True
            failedTests.append(test)

            if not options.noStop:
                break

    return failed


def runPerfSuite(options):
    """
    Run the Performance Test Suite
    """
    failed = False

    savePWD = os.getcwd()

    if 'release' in options.modes:
        testlist      = []
        testlistLarge = []

        os.chdir(options.chandlerHome)

        timeLog = os.path.join(options.profileDir, 'time.log')
        repoDir = os.path.join(options.profileDir, '__repository__.001')

        if not options.dryrun:
            for item in glob.iglob(os.path.join(options.profileDir, '__repository__.0*')):
                if os.path.isdir(item):
                    build_util.rmdirs(item)
                else:
                    os.remove(item)

        for item in glob.iglob(os.path.join(options.chandlerHome, 'tools', 'QATestScripts', 'Performance', 'Perf*.py')):
            if 'PerfLargeData' in item:
                testlistLarge.append(item)
            else:
                testlist.append(item)

        for item in testlist:
            #$CHANDLERBIN/release/$RUN_CHANDLER --create --catch=tests
            #                                   --profileDir="$PC_DIR"
            #                                   --catsPerfLog="$TIME_LOG"
            #                                   --scriptTimeout=600
            #                                   --scriptFile="$TESTNAME" &> $TESTLOG

            if os.path.isfile(timeLog):
                os.remove(timeLog)

            cmd = [ options.runchandler['release'],
                    '--create', '--catch=tests', '--scriptTimeout=600',
                    '--profileDir=%s'  % options.profileDir,
                    '--parcelPath=%s'  % options.parcelPath,
                    '--catsPerfLog=%s' % timeLog,
                    '--scriptFile=%s'  % item ]

            if options.dryrun:
                log('perftest: %s' % ' '.join(cmd))
                result = 0
            else:
                if options.verbose:
                    log('Running %s' % ' '.join(cmd))

                result = build_lib.runCommand(cmd)

            if result != 0:
                failed = True
                failedTests.append(' '.join(cmd))

                if not options.noStop:
                    break

        if not failed:
            for item in testlistLarge:
                #$CHANDLERBIN/release/$RUN_CHANDLER --restore="$REPO" --catch=tests
                #                                   --profileDir="$PC_DIR"
                #                                   --catsPerfLog="$TIME_LOG"
                #                                   --scriptTimeout=600
                #                                   --scriptFile="$TESTNAME" &> $TESTLOG

                cmd = [ options.runchandler['release'],
                        '--catch=tests', '--scriptTimeout=600',
                        '--restore=%s'    % repoDir,
                        '--profileDir=%s' % options.profileDir,
                        '--parcelPath=%s' % options.parcelPath,
                        '--scriptFile=%s' % item ]

                if options.dryrun:
                    log('perftest: %s' % ' '.join(cmd))
                    result = 0
                else:
                    if options.verbose:
                        log('Running %s' % ' '.join(cmd))

                    result = build_lib.runCommand(cmd)

                if result != 0:
                    failed = True
                    failedTests.append(' '.join(cmd))

                    if not options.noStop:
                        break

    else:
        log('Skipping Performance Tests - release mode not specified')

    os.chdir(savePWD)

    return failed


if __name__ == '__main__':
    options = parseOptions()

    if options.mode is None:
        options.modes = modes = ['release', 'debug']

        # silently clear any missing modes if default list is specified
        for mode in modes:
            if not os.path.isdir(os.path.join(options.chandlerBin, mode)):
                options.modes.remove(mode)
    else:
        options.modes = [ options.mode ]

        # complain about any missing modes if mode was explicitly stated
        if not os.path.isdir(os.path.join(options.chandlerBin, options.mode)):
            options.modes.remove(options.mode)
            log('%s removed from mode list' % options.mode)

    failed = False

    if options.unit or len(options.single) > 0:
        failed = runUnitTests(options)
        failed = runPluginTests(options)

    if options.funcSuite and not failed:
        failed = runFuncSuite(options)

    if options.perf and not failed:
        failed = runPerfSuite(options)

    if len(failedTests) > 0:
        log('+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
        log('The following tests failed:')
        log('\n'.join(failedTests))
        log('')

