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
#

import sys, os
import string
import glob
from optparse import OptionParser
import build_lib
log = build_lib.log

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


def parseOptions():
    _configItems = {
        'mode':      ('-m', '--mode',               's', None,  'debug or release; by default attempts both'),
        'noStop':    ('-C', '--continue',           'b', False, 'Continue even after test failures'),
        'unit':      ('-u', '--unit',               'b', False, 'unit tests each in own process'),
        'unitSuite': ('-U', '--unitSuite',          'b', False, 'all unit tests in single process'),
        'verbose':   ('-v', '--verbose',            'b', False, 'Verbose output'),
        'funcSuite': ('-f', '--funcSuite',          'b', False, 'Functional test suite'),
        'perf':      ('-p', '--perf',               'b', False, 'Performance tests'),
        'single':    ('-t', '--test',               's', '',    'Run test(s) (comma separated list)'),
        'noEnv':     ('-i', '--ignoreEnv',          'b', False, 'Ignore environment variables'),
        'help':      ('-H', '',                     'b', False, 'Extended help'),
        'dryrun':    ('-d', '--dryrun',             'b', False, 'Do all of the prep work but do not run any tests'),
        'selftest':  ('',   '--selftest',           'b', False, 'Run self test'),
        #'restored':  ('-R', '--restoredRepository', 'b', False, 'unit tests with restored repository instead of creating new for each test'),
        'profile':   ('-P', '--profile',            'b', False, 'Profile performance tests with hotshot'),
        'tbox':      ('-T', '--tbox',               'b', False, 'Tinderbox output mode'),
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

    return options


def checkOptions(options):
    if options.help:
        print __doc__
        sys.exit(2)

    if options.dryrun:
        options.verbose = True

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

    #build_lib.initLog(os.path.join(options.logPath, 'rt.log'), prefix='', echo=(not options.quiet))

    if not os.path.isdir(options.chandlerBin):
        log('Unable to locate CHANDLERBIN directory', error=True)
        sys.exit(3)

    if options.single and options.unit:
        log('Single test run (-t) only allowed by itself', error=True)
        sys.exit(1)

    if options.single:
        newsingle = []
        for single in options.single.split(','):
            if single[-3:] != '.py':
                newsingle.append(single + '.py')
            else:
                newsingle.append(single)
        options.single = ','.join(newsingle)

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

    for pattern in includePattern.split(','):
        for item in glob.glob(os.path.join(searchPath, pattern)):
            result.append(item)

    for item in os.listdir(searchPath):
        dirname = os.path.join(searchPath, item)

        if os.path.isdir(dirname):
            if item != '.svn' and dirname not in excludeDirs:
                result += findTestFiles(dirname, excludeDirs, includePattern)

    return result


def buildTestList(options, excludeTools=True):
    """
    Build test list from singles or collect all unit tests.
    """
    excludeDirs = []

    if len(options.single) > 0:
        includePattern = options.single
    else:
        includePattern = 'Test*.py'

    exclusions = ['util', 'projects', 'plugins', 'build', 'Chandler.egg-info']
    if excludeTools:
        exclusions.append('tools') 

    for item in exclusions:
        excludeDirs.append('%s/%s' % (options.chandlerHome, item))

    for item in [ 'release', 'debug' ]:
        excludeDirs.append('%s/%s' % (options.chandlerBin, item))

    result = findTestFiles(options.chandlerHome, excludeDirs, includePattern)

    for pattern in includePattern.split(','):
        if pattern in ('startup.py', 'startup_large.py'):
            result.append(pattern[:-3])
    
    return result


def runSingles(options):
    """
    Run the test(s) specified with the options.single parameter.
    """
    failed = False
    tests = buildTestList(options, False)
    if not tests:
        log('Test(s) not found')
    else:
        for test in tests:
            dir, name = os.path.split(test)
            if os.path.split(dir)[1] == 'Functional':
                if runFuncTest(options, name[:-3]):
                    failed = True
            elif name.startswith('Perf'):
                if runPerfTests(options, [test]):
                    failed = True
            elif name in ('startup', 'startup_large'):
                if runPerfTests(options, [name]):
                    failed = True                
            else:
                if runUnitTests(options, [test]):
                    failed = True
    
            if failed and not options.noStop:
                break
    
    return failed


def runUnitTests(options, testlist=None):
    """
    Locate any unit tests (-u) or any of the named test (-t) and run them
    """
    if testlist is None:
        testlist = buildTestList(options)
    failed   = False

    if len(testlist) == 0:
        log('No unit tests found to run')
    else:
        for mode in options.modes:
            for test in testlist:
                cmd = [ options.runpython[mode], test ]

                if options.verbose:
                    cmd.append('-v')
                    log(' '.join(cmd))

                if options.dryrun:
                    result = 0
                else:
                    result = build_lib.runCommand(cmd, timeout=600)

                if result != 0:
                    log('***Error exit code=%d' % result)
                    failed = True
                    failedTests.append(test)

                    if not options.noStop:
                        break

            if failed and not options.noStop:
                break

    return failed


def runUnitSuite(options):
    """
    Run all unit tests in a single process
    """
    failed = False
    
    for mode in options.modes:
        cmd = [options.runpython[mode],
               os.path.join(options.chandlerHome, 'tools', 'run_tests.py')]

        if options.verbose:
            cmd += '-v'
        
        cmd += ['application', 'i18n', 'osaf', 'repository']

        if options.verbose:
            log(' '.join(cmd))

        if options.dryrun:
            result = 0
        else:
            result = build_lib.runCommand(cmd, timeout=3600)

        if result != 0:
            log('***Error exit code=%d' % result)
            failed = True
            failedTests.append('unitSuite')

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

        try:
            for mode in options.modes:
                for test in testlist:
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

                    cmd = [ options.runpython[mode], test, 'test' ]

                    if options.verbose:
                        cmd.append('-v')
                        log(' '.join(cmd))

                    if options.dryrun:
                        result = 0
                    else:
                        os.chdir(os.path.dirname(test))
                        result = build_lib.runCommand(cmd, timeout=600, env=env)

                    if result != 0:
                        log('***Error exit code=%d' % result)
                        failed = True
                        failedTests.append(test)

                        if not options.noStop:
                            break

                if failed and not options.noStop:
                    break
        finally:
            os.chdir(saveCWD)

    return failed


def runFuncTest(options, test='FunctionalTestSuite.py'):
    """
    Run functional test
    """
    # $CHANDLERBIN/$mode/$RUN_CHANDLER --create --catch=tests $FORCE_CONT --profileDir="$PC_DIR" --parcelPath="$PP_DIR" --scriptTimeout=720 --scriptFile="$TESTNAME" -D1 -M2 2>&1 | tee $TESTLOG
    failed = False

    for mode in options.modes:
        cmd  = [ options.runchandler[mode],
                 '--create', '--catch=tests', '--scriptTimeout=720',
                 '--profileDir=%s' % options.profileDir,
                 '--parcelPath=%s' % options.parcelPath]

        if test == 'FunctionalTestSuite.py':
            cmd += ['--scriptFile=%s' % os.path.join(options.chandlerHome, 'tools', 'cats', 'Functional', test)]
        else:
            cmd += ['--chandlerTests=%s' % test]

        if options.noStop:
            cmd += [ '-F' ]

        if options.verbose or test != 'FunctionalTestSuite.py':
            cmd += ['-D2', '-M0']
        elif not options.verbose:
            cmd += ['-D1', '-M2']

        if options.verbose:
            log(' '.join(cmd))

        if options.dryrun:
            result = 0
        else:
            result = build_lib.runCommand(cmd, timeout=900)

        if result != 0:
            log('***Error exit code=%d' % result)
            failed = True
            failedTests.append(test)

            if not options.noStop:
                break

    return failed

def runScriptPerfTests(options, testlist, largeData=False):
    failed = False

    for item in testlist:
        #$CHANDLERBIN/release/$RUN_CHANDLER --create --catch=tests
        #                                   --profileDir="$PC_DIR"
        #                                   --catsPerfLog="$TIME_LOG"
        #                                   --scriptTimeout=600
        #                                   --scriptFile="$TESTNAME" &> $TESTLOG

        name = item[item.rfind('/') + 1:]

        timeLog = os.path.join(options.profileDir, 'time.log')

        if not options.dryrun:
            if os.path.isfile(timeLog):
                os.remove(timeLog)

        cmd = [ options.runchandler['release'],
                '--catch=tests', '--scriptTimeout=600',
                '--profileDir=%s'  % options.profileDir,
                '--parcelPath=%s'  % options.parcelPath,
                '--catsPerfLog=%s' % timeLog,
                '--scriptFile=%s'  % item ]

        if options.profile:
            cmd += ['--catsProfile=%s.hotshot' % os.path.join(options.profileDir, name[:-3])]

        if not largeData:
            cmd += ['--create']
        else:
            cmd += ['--restore=%s' % os.path.join(options.profileDir, 
                                                  '__repository__.001')]

        if options.verbose:
            log(' '.join(cmd))

        if options.dryrun:
            result = 0
        else:
            result = build_lib.runCommand(cmd, timeout=720)

        if result != 0:
            log('***Error exit code=%d, %s' % (result, name))
            failed = True
            failedTests.append(item)

            if not options.noStop:
                break
        else:
            if options.dryrun:
                log(name + ' [ 0.00s ]')
            else:
                line = open(timeLog).readline()[:-1]
                log(name + ' [ %ss ]' % line)

    return failed

def runStartupPerfTests(options, timer, largeData=False, repeat=3):
    # Create test repo
    log('Creating repository for startup time tests')
    cmd = [ options.runchandler['release'],
            '--catch=tests', '--scriptTimeout=60',
            '--profileDir=%s'  % options.profileDir,
            '--parcelPath=%s'  % options.parcelPath,
            '--scriptFile=%s'  % os.path.join(options.chandlerHome, 'tools', 'QATestScripts', 'Performance', 'quit.py') ]

    if not largeData:
        cmd += ['--create']
        timeout = 180
        name = 'Startup'
    else:
        cmd += ['--restore=%s' % os.path.join(options.profileDir, 
                                              '__repository__.001')]
        timeout = 600
        name = 'Startup_with_large_calendar'
    
    if options.verbose:
        log(' '.join(cmd))

    if options.dryrun:
        result = 0
    else:
        result = build_lib.runCommand(cmd, timeout=timeout)
    
    if result != 0:
        log('***Error exit code=%d, creating %s repository' % (result, name))
        failedTests.append(name)
        return True
    
    # Time startup
    values = []
    timeLog = os.path.join(options.profileDir, 'time.log')
    if not options.dryrun:
        if os.path.isfile(timeLog):
            os.remove(timeLog)

    cmd = [ timer, r'--format=%e', '-o', timeLog,
            options.runchandler['release'],
            '--catch=tests', '--scriptTimeout=60',
            '--profileDir=%s'  % options.profileDir,
            '--parcelPath=%s'  % options.parcelPath,
            '--scriptFile=%s'  % os.path.join(options.chandlerHome, 'tools', 'QATestScripts', 'Performance', 'end.py') ]

    for _ in range(repeat):
        if options.verbose:
            log(' '.join(cmd))

        if options.dryrun:
            result = 0
        else:
            result = build_lib.runCommand(cmd, timeout=180)
            
        if result == 0:
            if options.dryrun:
                line = '0.0'
            else:
                line = open(timeLog).readline()[:-1]
            try:
                value = float(line)
            except ValueError, e:
                log('%s [ %s ]' % (name, str(e)))
                failedTests.append(name)
                return True
            log('%02.2fs' % value)
            values.append(value)
        else:
            log('%s [ failed ]' % name)
            failedTests.append(name)
            return True
    else:
        values.sort()
        value = values[repeat/2]
        if not options.tbox:
            log('%s [ %02.2fs ]' % (name, value))
        else:
            log('%s [#TINDERBOX# Status = PASSED]' % name)
            log('OSAF_QA: %s | %04d | %02.2fs' % (name, os.getenv('REVISION', 0), value)) # XXX get svn revision
            log('#TINDERBOX# Testname = %s' % name)
            log('#TINDERBOX# Status = PASSED')
            log('#TINDERBOX# Time elapsed = %02.2fs (seconds)' % value)
        
    return False

def runPerfTests(options, testlist=None):
    """
    Run the Performance Test Suite
    """
    # XXX need to log the full output to intermediate file so that we can
    # XXX first show the condensed form, sleep for 5 seconds, and cat the
    # XXX full log (like do_tests.sh does).
    
    failed = False

    savePWD = os.getcwd()

    try:
        if 'release' in options.modes:
            if not options.dryrun:
                os.chdir(options.chandlerHome)
                if testlist is None:
                    for item in glob.glob(os.path.join(options.profileDir, '__repository__.0*')):
                        if os.path.isdir(item):
                            build_lib.rmdirs(item)
                        else:
                            os.remove(item)

            if testlist is None:
                testlist = []
                testlistLarge = []
                testlistStartup = ['startup', 'startup_large']
                for item in glob.glob(os.path.join(options.chandlerHome, 'tools', 'QATestScripts', 'Performance', 'Perf*.py')):
                    if 'PerfLargeData' in item:
                        testlistLarge.append(item)
                    else:
                        testlist.append(item)
            else:
                newtestlist = []
                testlistLarge = []
                testlistStartup = []
                for item in testlist:
                    if 'PerfLargeData' in item:
                        testlistLarge.append(item)
                    elif item in ('startup', 'startup_large'):
                        testlistStartup.append(item)
                    else:
                        newtestlist.append(item)
                testlist = newtestlist[:]

            # small repo tests
            if testlist:
                failed = runScriptPerfTests(options, testlist)

            # large repo tests
            if testlistLarge and (not failed or options.noStop):
                if runScriptPerfTests(options, testlistLarge, largeData=True):
                    failed = True

            # startup tests
            if testlistStartup and (not failed or options.noStop):
                if os.name == 'nt' or sys.platform == 'cygwin':
                    t = 'time.exe'
                elif sys.platform == 'darwin':
                    t = 'gtime'
                    if not build_lib.getCommand(['which', t]):
                        log('%s not found, skipping startup performance tests' % t)
                        log('NOTE: %s is not part of OS X, you need to compile one' + \
                            'yourself (get source from http://directory.fsf.org/time.html)' + \
                            'or get it from darwinports project.' % t)
                else:
                    t = '/usr/bin/time'

                if 'startup' in testlistStartup and runStartupPerfTests(options, t):
                    failed = True
                if not failed: # Don't continue even if noStop, almost certain these won't work
                    if 'startup_large' in testlistStartup and runStartupPerfTests(options, t, largeData=True):
                        failed = True
        else:
            log('Skipping Performance Tests - release mode not specified')

    finally:
        os.chdir(savePWD)

    return failed


def main(options):
    """
    >>> import optparse
    >>> options = optparse.Values()
    >>> options.noEnv     = False
    >>> options.dryrun    = True
    >>> options.mode      = None
    >>> options.perf      = False
    >>> options.funcSuite = False
    >>> options.unit      = False
    >>> options.single    = ''
    >>> options.verbose   = True
    >>> options.noStop    = False
    >>> options.help      = False
    >>> options.tbox      = False
    >>> options.unitSuite = False
    >>> options.profile   = False
    >>> main(options)

    Try and run a test that does not exist

    >>> options.single = 'TestFoo.py'
    >>> main(options)
    Test(s) not found

    Try different single tests
    
      single unit test:
      
    >>> options.single = 'TestCrypto'
    >>> main(options)
    /.../RunPython .../application/tests/TestCrypto.py -v
    
      unit test and functional test:
      
    >>> options.single = 'TestCrypto,TestSharing'
    >>> main(options)
    /.../RunChandler --create --catch=tests --scriptTimeout=720 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --chandlerTests=TestSharing -D2 -M0
    /.../RunPython .../application/tests/TestCrypto.py -v
    
      unit, functional and two perf tests, one of which is a startup test:
      
    >>> options.single = 'TestCrypto,TestSharing,PerfImportCalendar,startup_large'
    >>> main(options)
    /.../RunChandler --catch=tests --scriptTimeout=600 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --catsPerfLog=.../test_profile/time.log --scriptFile=.../tools/QATestScripts/Performance/PerfImportCalendar.py --create
    PerfImportCalendar.py [ 0.00s ]
    /.../RunChandler --create --catch=tests --scriptTimeout=720 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --chandlerTests=TestSharing -D2 -M0
    /.../RunPython .../application/tests/TestCrypto.py -v
    Creating repository for startup time tests
    /.../RunChandler... --catch=tests --scriptTimeout=60 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --scriptFile=.../tools/QATestScripts/Performance/quit.py --restore=.../test_profile/__repository__.001
    /usr/bin/time --format=%e -o .../test_profile/time.log .../RunChandler... --catch=tests --scriptTimeout=60 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --scriptFile=.../tools/QATestScripts/Performance/end.py
    0.00s
    ...

    Try and specify an invalid mode

    >>> options.single = ''
    >>> options.mode   = 'foo'
    >>> main(options)
    foo removed from mode list

    Run unit tests with --dryrun

    >>> options.mode = None
    >>> options.unit = True
    >>> main(options)
    /.../RunPython... .../tests/TestReferenceAttributes.py -v
    ...
    /.../RunPython... .../projects/Chandler-EVDBPlugin/setup.py test -v
    ...

    Run unitSuite with --dryrun

    >>> options.mode = None
    >>> options.unit = False
    >>> options.unitSuite = True
    >>> main(options)
    /.../RunPython .../tools/run_tests.py - v application i18n osaf repository

    Run functional tests with --dryrun

    >>> options.unit      = False
    >>> options.unitSuite = False
    >>> options.funcSuite = True
    >>> main(options)
    /.../RunChandler... --create --catch=tests --scriptTimeout=720 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --scriptFile=.../tools/cats/Functional/FunctionalTestSuite.py -D2 -M0
    
    Run performance tests with --dryrun

    >>> options.funcSuite = False
    >>> options.perf      = True
    >>> options.profile   = False
    >>> main(options)
    /.../RunChandler... --catch=tests --scriptTimeout=600 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --catsPerfLog=.../test_profile/time.log --scriptFile=.../tools/QATestScripts/Performance/PerfImportCalendar.py --create
    PerfImportCalendar.py [ 0.00s ]
    ...
    /.../RunChandler... --catch=tests --scriptTimeout=600 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --catsPerfLog=.../test_profile/time.log --scriptFile=.../tools/QATestScripts/Performance/PerfLargeDataResizeCalendar.py --restore=.../test_profile/__repository__.001
    PerfLargeDataResizeCalendar.py [ 0.00s ]
    ...
    Creating repository for startup time tests
    /.../RunChandler... --catch=tests --scriptTimeout=60 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --scriptFile=.../tools/QATestScripts/Performance/quit.py --create
    /usr/bin/time --format=%e -o .../test_profile/time.log .../RunChandler... --catch=tests --scriptTimeout=60 --profileDir=.../test_profile --parcelPath=.../tools/QATestScripts/DataFiles --scriptFile=.../tools/QATestScripts/Performance/end.py
    0.00s
    ...
    """
    checkOptions(options)

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

    if options.single:
        failed = runSingles(options)
    else:
        if options.unit:
            failed = runUnitTests(options)
            if not failed or options.noStop:
                if runPluginTests(options):
                    failed = True
        
        if options.unitSuite and (not failed or options.noStop):
            if runUnitSuite(options):
                failed = True
    
        if options.funcSuite and (not failed or options.noStop):
            if runFuncTest(options):
                failed = True
    
        if options.perf and (not failed or options.noStop):
            if runPerfTests(options):
                failed = True

    if len(failedTests) > 0:
        log('+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
        log('The following tests failed:')
        log('\n'.join(failedTests))
        log('')


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        import doctest
        doctest.testmod(optionflags=doctest.ELLIPSIS)
        sys.exit(0)

    main(parseOptions())

