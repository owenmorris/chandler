
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
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

import os, sys, re, glob
import hardhatutil, hardhatlib

path       = os.environ.get('PATH', os.environ.get('path'))
whereAmI   = os.path.dirname(os.path.abspath(hardhatlib.__file__))
svnProgram = hardhatutil.findInPath(path, "svn")
antProgram = hardhatutil.findInPath(path, "maven")
logPath    = 'hardhat.log'
separator  = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"

treeName     = "Cosmo"
sleepMinutes = 30

reposRoot    = 'http://svn.osafoundation.org/server'
reposModules = [('cosmo',  'cosmo/trunk',),
               ]
reposBuild   = [('cosmo',  'clean dist'),
               ]
reposTest    = [('cosmo',  'clean test'),
               ]
reposDist    = [('cosmo',  'clean dist:release', 'dist', 'cosmo*.tar.gz'),
                ('cosmo',  'clean war:deploy',   None,   None),
               ]

def Start(hardhatScript, workingDir, buildVersion, clobber, log, skipTests=False, upload=False, branchID=None, revID=None):

      # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)

    os.chdir(workingDir)

      # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")

    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)

    os.mkdir(outputDir)

    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    sourceChanged = False
    rev = ""

    log.write("[tbox] Pulling source tree\n")

    for (module, moduleSource) in reposModules:
        moduleDir = os.path.join(workingDir, module)

        # if branchID is present then we have to modify moduleSource as a branch has
        # been requested instead of the trunk
        if branchID:
            moduleSource = moduleSource.replace('/trunk', '/branches/%s' % branchID)

        if os.path.exists(moduleDir):
            log.write("[tbox] Checking for source updates\n")
            print "updating %s" % module

            os.chdir(moduleDir)

            # if revID is present then we have to modify the request to include
            # the given revision #
            if revID:
                cmd = [svnProgram, "up", "-r %s" % revID]
            else:
                cmd = [svnProgram, "up"]

            outputList = hardhatutil.executeCommandReturnOutputRetry(cmd)

            rev = determineRevision(outputList)

            hardhatutil.dumpOutputList(outputList, log) 

            if NeedsUpdate(outputList):
                sourceChanged = True
                log.write("[tbox] %s modified\n" % module)
            else:
                log.write("[tbox] %s unchanged\n" % module)

        else:
            svnSource = os.path.join(reposRoot, moduleSource)

            log.write("[tbox] Retrieving source tree [%s]\n" % svnSource)
            print "pulling %s" % module

            os.chdir(workingDir)

            # if revID is present then we have to modify the request to include
            # the given revision #
            if revID:
                cmd = [svnProgram, "co", "-r %s" % revID, svnSource, module]
            else:
                cmd = [svnProgram, "co", svnSource, module]

            outputList = hardhatutil.executeCommandReturnOutputRetry(cmd)

            rev = determineRevision(outputList)

            hardhatutil.dumpOutputList(outputList, log)

            sourceChanged = True

    os.chdir(workingDir)

    doBuild(workingDir, log)

    if skipTests:
        ret = 'success'
    else:
        ret = doTests(workingDir, log)

    if sourceChanged:
        doDistribution(workingDir, log, outputDir, buildVersion, buildVersionEscaped)

        changes = "-changes"
    else:
        changes = "-nochanges"

    print ret + changes

    return (ret + changes, rev)


def doBuild(workingDir, log):
    log.write("[tbox] Building\n")

    for (module, target) in reposBuild:
        moduleDir = os.path.join(workingDir, module)
        mavenDir  = os.path.join(workingDir, '..', 'tbox_maven', module)

        print "Building [%s]" % module

        try:
            os.chdir(moduleDir)

            outputList = hardhatutil.executeCommandReturnOutput(
                            [antProgram,
                             '-Dmaven.home.local=' + mavenDir,
                             target])

            hardhatutil.dumpOutputList(outputList, log)

        except:
            log.write("[tbox] Build failed for [%s]\n" % module)

def doTests(workingDir, log):
    log.write("[tbox] Running unit tests\n")

    for (module, target) in reposTest:
        moduleDir = os.path.join(workingDir, module)

        print "Testing [%s]" % module

        try:
            os.chdir(moduleDir)

            outputList = hardhatutil.executeCommandReturnOutput([antProgram, target])

            hardhatutil.dumpOutputList(outputList, log)

        except Exception, e:
            doCopyLog("***Error during tests***", workingDir, logPath, log)
            return "test_failed"
        else:
            doCopyLog("Tests successful", workingDir, logPath, log)

    return "success"

def doDistribution(workingDir, log, outputDir, buildVersion, buildVersionEscaped):
    log.write(separator)
    log.write("[tbox] Creating distribution files\n")

    for (module, target, distSource, fileGlob) in reposDist:
        moduleDir = os.path.join(workingDir, module)

        print "Distribution [%s]" % module

        try:
            os.chdir(moduleDir)

            outputList = hardhatutil.executeCommandReturnOutput([antProgram, target])

            hardhatutil.dumpOutputList(outputList, log)

            if distSource:
                sourceDir = os.path.join(moduleDir, distSource)
                targetDir = os.path.join(outputDir, buildVersion)

                if not os.path.exists(targetDir):
                    os.mkdir(targetDir)

                print sourceDir, targetDir

                log.write("[tbox] Moving %s to %s\n" % (sourceDir, targetDir))

                hardhatlib.copyFiles(sourceDir, targetDir, fileGlob)

                distributionFiles = glob.glob(os.path.join(targetDir, fileGlob))

                fileOut = file(os.path.join(targetDir, 'developer'), 'w')
                fileOut.write(os.path.basename(distributionFiles[0]))
                fileOut.close()

        except Exception, e:
            doCopyLog("***Error during distribution building process*** ", workingDir, logPath, log)
            raise e

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
    log.write(msg + "\n")
    log.write(separator)
    logPath = os.path.join(workingDir, logPath)
    log.write("Contents of " + logPath + ":\n")
    if os.path.exists(logPath):
        CopyLog(logPath, log)
    else:
        log.write(logPath + ' does not exist!\n')
    log.write(separator)


def CopyLog(file, fd):
    input = open(file, "r")
    line = input.readline()
    while line:
        fd.write(line)
        line = input.readline()
    input.close()

def getVersion(fileToRead):
    input = open(fileToRead, "r")
    line = input.readline()
    while line:
        if line == "\n":
            line = input.readline()
            continue
        else:
            m=re.match('VERSION=(.*)', line)
            if not m == 'None' or m == 'NoneType':
                version = m.group(1)
                input.close()
                return version

        line = input.readline()
    input.close()
    return 'No Version'

