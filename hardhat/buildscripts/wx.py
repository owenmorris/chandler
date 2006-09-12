
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
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

import os, sys, re, glob
import hardhatutil, hardhatlib

path        = os.environ.get('PATH', os.environ.get('path'))
whereAmI    = os.path.dirname(os.path.abspath(hardhatlib.__file__))
svnProgram  = hardhatutil.findInPath(path, 'svn')
makeProgram = hardhatutil.findInPath(path, 'make')
tarProgram  = hardhatutil.findInPath(path, 'tar')
logPath     = 'hardhat.log'
separator   = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"

treeName     = 'wx'
sleepMinutes = 5
releaseModes = ('debug', 'release')


def Log(msg, logfile):
    logfile.write('[wx] %s\n' % msg)
    print msg


def updateSource(log, workingDir, module, reposPath, branchID=None, revID=None):
    moduleDir = os.path.join(workingDir, module)
    revision  = ''
    updated   = False

    # if branchID is present then we have to modify the repository path
    # as a branch has been requested instead of the trunk
    if branchID:
        reposPath = reposPath.replace('trunk', 'branches/%s' % branchID)

    # if revID is present then we have to modify the request to include
    # the given revision #
    if revID:
        revision = '-r %s' % revID
    else:
        revision = ''

    if os.path.exists(moduleDir):
        Log('Updating %s source tree' % module, log)

        os.chdir(moduleDir)

        cmd = [svnProgram, 'up', revision]

        outputList = hardhatutil.executeCommandReturnOutputRetry(cmd)

        revision = determineRevision(outputList)

        hardhatutil.dumpOutputList(outputList, log) 

        if NeedsUpdate(outputList):
            updated = True
            Log('%s source has changed' % module, log)
        else:
            Log('%s source has not changed' % module, log)
    else:
        Log('Checking-out %s source tree' % module, log)

        os.chdir(workingDir)

        cmd = [svnProgram, 'co', revision, reposPath, module]

        outputList = hardhatutil.executeCommandReturnOutputRetry(cmd)

        revision = determineRevision(outputList)
        updated  = True

        hardhatutil.dumpOutputList(outputList, log)

    return revision, updated


def Start(hardhatScript, workingDir, buildVersion, clobber, logfile, skipTests=False, upload=False, branchID=None, revID=None):

      # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)

    os.chdir(workingDir)

      # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")

    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)

    os.mkdir(outputDir)

    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(' ', '|')

    ret         = 'failed'
    changes     = '-nochanges'
    srcWx       = False
    srcChandler = False
    srcExternal = False
    revWx       = ''
    revChandler = ''
    revExternal = ''

    updateSource(logfile, workingDir, 'internal', 'http://svn.osafoundation.org/chandler/trunk/internal', branchID, revID)

    revChandler, srcChandler = updateSource(logfile, workingDir, 'chandler', 'http://svn.osafoundation.org/chandler/trunk/chandler', branchID, revID)
    revExternal, srcExternal = updateSource(logfile, workingDir, 'external', 'http://svn.osafoundation.org/chandler/trunk/external', branchID, revID)
    revWx,       srcWx       = updateSource(logfile, workingDir, 'wx',       'http://svn.osafoundation.org/wx/trunk', branchID, revID)

    os.chdir(workingDir)

    installChandler(workingDir, logfile)

    if srcExternal:
        buildExternal(workingDir, logfile)

    if srcWx:
        changes = "-changes"

    buildWx(workingDir, logfile)
    installWx(workingDir, logfile)

    if skipTests:
        ret = 'success'
    else:
        ret = doUnitTests(workingDir, logfile)

        if ret == 'success':
            ret = doFunctionalTests(workingDir, logfile)

    Log('status [%s, %s, %s]' % (ret, changes, revWx), logfile)

    return (ret + changes, revWx)


def installChandler(workingDir, log):
    Log(separator, log)
    Log('Installing Chandler', log)

    result = True

    chandlerDir = os.path.join(workingDir, 'chandler')

    os.chdir(chandlerDir)

    Log('Removing release and debug directories', log)

    hardhatlib.rmdir_recursive(os.path.join(chandlerDir, 'release'))
    hardhatlib.rmdir_recursive(os.path.join(chandlerDir, 'debug'))

    Log('Running make install', log)

    outputList = hardhatutil.executeCommandReturnOutput([makeProgram, 'install'])
    hardhatutil.dumpOutputList(outputList, log)

    outputList = hardhatutil.executeCommandReturnOutput([makeProgram, 'DEBUG=1', 'install'])
    hardhatutil.dumpOutputList(outputList, log)

    return result


def buildExternal(workingDir, log):
    Log(separator, log)

    externalDir = os.path.join(workingDir, 'external')

    Log('External Directory: %s' % externalDir, log)
    Log('Setting BUILD_ROOT=%s' % externalDir, log)

    os.putenv('BUILD_ROOT', externalDir)
    os.chdir(externalDir)

    Log('changing to %s directory' % externalDir, log)

    for mode in releaseModes:
        if mode == 'debug':
            modeText = 'DEBUG=1'
        else:
            modeText = ''

        Log('running make env', log)

        cmd        = [makeProgram, modeText, 'env']
        outputList = hardhatutil.executeCommandReturnOutput(cmd)
        hardhatutil.dumpOutputList(outputList, log)

        for module in ('readline', 'python', 'swig'):
            Log('building %s' % module, log)
            os.chdir(os.path.join(externalDir, module))

            if module == 'python':
                cmd = [makeProgram, modeText, 'build', 'binaries', 'drop']
            else:
                cmd = [makeProgram, modeText, 'build']

            outputList = hardhatutil.executeCommandReturnOutput(cmd)
            hardhatutil.dumpOutputList(outputList, log)


def buildWx(workingDir, log):
    Log(separator, log)

    externalDir = os.path.join(workingDir, 'external')
    wxDir       = os.path.join(workingDir, 'wx')

    Log('External Directory: %s' % externalDir, log)
    Log('Setting BUILD_ROOT=%s' % externalDir, log)

    os.putenv('BUILD_ROOT', externalDir)
    os.chdir(externalDir)

    Log('changing to %s directory' % externalDir, log)
    Log('Building wx', log)

    for mode in releaseModes:
        if mode == 'debug':
            modeText = 'DEBUG=1'
        else:
            modeText = ''

        cmd        = [makeProgram, '-C %s' % wxDir, modeText, 'RELVER=tbox', 'realclean', 'build', 'install']
        outputList = hardhatutil.executeCommandReturnOutput(cmd)
        hardhatutil.dumpOutputList(outputList, log)


def installWx(workingDir, log):
    Log(separator, log)

    externalDir = os.path.join(workingDir, 'external')
    chandlerDir = os.path.join(workingDir, 'chandler')
    wxDir       = os.path.join(workingDir, 'wx')

    os.chdir(chandlerDir)

    for mode in releaseModes:
        tarball = os.path.join(workingDir, 'downloads', 'wxPython-%s-tbox.tar.gz' % mode)

        Log('Installing %s into %s' % (tarball, chandlerDir), log)

        cmd        = [tarProgram, '-C %s' % chandlerDir, '-xvzf', tarball]
        outputList = hardhatutil.executeCommandReturnOutput(cmd)
        hardhatutil.dumpOutputList(outputList, log)


def LogTest(error, errorDir, errorFile, logfile):
    Log(error, logfile)

    doCopyLog(error, errorDir, errorFile, logfile)


def doUnitTests(workingDir, log):
    Log(separator, log)
    Log('Running unit tests', log)

    result  = 'test_failed'
    testDir = os.path.join(workingDir, 'chandler')
    logDir  = os.path.join(testDir,    'test_profile')
    os.chdir(testDir)

    for mode in releaseModes:
        try:
            outputList = hardhatutil.executeCommandReturnOutput(['./tools/do_tests.sh', '-u', '-m %s' % mode])
            hardhatutil.dumpOutputList(outputList, log)

            result = 'success'

        except Exception, e:
            LogTest('Error while running Unit Tests', logDir, 'do_tests.log', log)
            result = 'test_failed'
            break
        else:
            LogTest('Tests successful', logDir, 'do_tests.log', log)

    return result


def dumpTestLogs(log, chandlerLog, exitCode=0):
    if chandlerLog:
        log.write('chandler.log:\n')
        try:
            CopyLog(chandlerLog, log)
        except:
            pass

        log.write(separator)

    log.write('exit code=%s\n' % exitCode)
    log.write('NOTE: If the tests themselves passed but the exit code\n')
    log.write('      reports failure, it means a shutdown problem.\n')


def doFunctionalTests(workingDir, log):
    chandlerDir = os.path.join(workingDir,  'chandler')
    logDir      = os.path.join(chandlerDir, 'test_profile')
    chandlerLog = os.path.join(logDir,      'chandler.log')
    FuncTestLog = os.path.join(logDir,      'FunctionalTestSuite.log')

    if (os.name == 'nt') or (os.name == 'posix' and sys.platform == 'cygwin'):
        runScript = 'RunChandler.bat'
    else:
        runScript = 'RunChandler'

    os.chdir(chandlerDir)

    for mode in releaseModes:
        runChandler = os.path.join(chandlerDir, mode, runScript)

        try:
            Log(separator, log)
            Log('Running %s Functional Tests ...' % mode, log)

            try:
                os.remove(chandlerLog)
            except OSError:
                pass

            cmd = [runChandler,
                   '--create', '--catch=tests',
                   '--profileDir=%s' % logDir,
                   '--parcelPath=tools/QATestScripts/DataFiles',
                   '--scriptTimeout=600', 
                   '--scriptFile=tools/cats/Functional/FunctionalTestSuite.py',
                   '--chandlerTestDebug=1',
                   '--chandlerTestMask=0',
                  ]

            outputList = hardhatutil.executeCommandReturnOutput(cmd)
            hardhatutil.dumpOutputList(outputList, log)

            dumpTestLogs(log, chandlerLog)

            for line in outputList:
                if line.find('#TINDERBOX# Status = FAIL') >= 0 or \
                   line.find('#TINDERBOX# Status = UNCHECKED') >= 0:
                    Log('***Error during functional tests***', log)

                    forceBuildNextCycle(log, workingDir)

                    return "test_failed"

        except hardhatutil.ExternalCommandErrorWithOutputList, e:
            dumpTestLogs(log, chandlerLog, e.args)

            Log('***Error during functional tests***', log)

            forceBuildNextCycle(log, workingDir)

            return "test_failed"

        except Exception, e:
            Log('***Error during functional tests***', log)
            Log('Exception:', log)
            Log(str(e), log)

            forceBuildNextCycle(log, workingDir)

            return "test_failed"

        else:
            Log('Functional tests exit code=0', log)

    return "success"



def determineRevision(outputList):
    """
    Scan output of svn up command and extract the revision #
    """
    revision = ""

    for line in outputList:
        s = line.lower()

          # handle "Update to revision ####." - svn up
        if s.find("updated to revision") != -1:
            revision = s[19:-2]
            break
          # handle "At revision ####." - svn up
        if s.find("at revision") != -1:
            revision = s[12:-2]
            break
          # handler "Checked out revision ####." - svn co
        if s.find("checked out revision") != -1:
            revision = s[21:-2]
            break

    return revision


def NeedsUpdate(outputList):
    for line in outputList:
        if line.lower().find("ide scripts") != -1:
            # this hack is for skipping some Mac-specific files that
            # under Windows always appear to be needing an update
            continue
        if line.lower().find("xercessamples") != -1:
            # same type of hack as above
            continue
        if line.lower().find("at revision") != -1:
            continue
        if line.lower().find("restored") != -1:
            print "needs update because of", line
            return True
        if line[0] == "U":
            print "needs update because of", line
            return True
        if line[0] == "P":
            print "needs update because of", line
            return True
        if line[0] == "A":
            print "needs update because of", line
            return True

    return False


def doCopyLog(msg, workingDir, logPath, log):
    Log(msg, log)
    Log(separator, log)

    logPath = os.path.join(workingDir, logPath)

    Log('Contents of %s' % logPath, log)

    if os.path.exists(logPath):
        input = open(logPath, "r")
        line  = input.readline()
        while line:
            log.write(line)
            line = input.readline()
        input.close()
    else:
        Log('%s does not exist' % logPath, log)

    Log(separator, log)


def forceBuildNextCycle(log, workingDir):
    Log('Removing wx/Makefile to trigger build next cycle', log)
    makefile = os.path.join(workingDir, 'wx', 'Makefile')
    if os.path.exists(makefile):
        os.remove(makefile)
