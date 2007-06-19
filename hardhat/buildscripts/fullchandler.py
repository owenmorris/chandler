
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

import os, hardhatutil, hardhatlib, sys, re, glob, platform

path          = os.environ.get('PATH', os.environ.get('path'))
whereAmI      = os.path.dirname(os.path.abspath(hardhatlib.__file__))
svnProgram    = hardhatutil.findInPath(path, "svn")
pythonProgram = hardhatutil.findInPath(path, "python")

treeName     = "Chandler" 
sleepMinutes = 5
logPath      = 'hardhat.log'
separator    = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"

reposRoot    = 'http://svn.osafoundation.org/chandler'
reposBase    = 'trunk'
reposModules = ['external', 'internal', 'chandler']
releaseModes = ('debug', 'release')

def Start(hardhatScript, workingDir, buildVersion, clobber, log, skipTests=False, upload=False, branchID=None, revID=None):

    global buildenv, changes

    try:
        buildenv = hardhatlib.defaults
        buildenv['root'] = workingDir
        buildenv['hardhatroot'] = whereAmI
        hardhatlib.init(buildenv)

    except hardhatlib.HardHatMissingCompilerError:
        print "Could not locate compiler.  Exiting."
        sys.exit(1)

    except hardhatlib.HardHatUnknownPlatformError:
        print "Unsupported platform, '" + os.name + "'.  Exiting."
        sys.exit(1)

    except hardhatlib.HardHatRegistryError:
        print
        print "Sorry, I am not able to read the windows registry to find" 
        print "the necessary VisualStudio complier settings.  Most likely you"
        print "are running the Cygwin python, which will hopefully be supported"
        print "soon.  Please download a windows version of python from:\n"
        print "http://www.python.org/download/"
        print
        sys.exit(1)

    except Exception, e:
        print "Could not initialize hardhat environment.  Exiting."
        print "Exception:", e
        import traceback
        traceback.print_exc()
        sys.exit(1)

      # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)
    chanDir    = os.path.join(workingDir, 'chandler')

      # test if we've been through the loop at least once
    if clobber:
        for module in reposModules:
            modDir = os.path.join(workingDir, module)
            if os.path.exists(modDir):
                hardhatutil.rmdirRecursive(modDir)

    os.chdir(workingDir)

      # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")

    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)

    os.mkdir(outputDir)

    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    clean = ''
    ret   = 'success'

    if not os.path.exists(chanDir):
          # Initialize sources
        print "Setup source tree..."
        log.write("- - - - tree setup - - - - - - -\n")

        svnChanges   = {}
        svnRevisions = {}

        for module in reposModules:
            svnSource = os.path.join(reposRoot, reposBase, module)

            log.write("[tbox] Retrieving source tree [%s]\n" % svnSource)
                     
            outputList = hardhatutil.executeCommandReturnOutputRetry([svnProgram, "co", svnSource, module])

            svnRevisions[module] = determineRevision(outputList)

            hardhatutil.dumpOutputList(outputList, log) 

            svnChanges[module] = True

        for releaseMode in releaseModes:
            ret = doBuild(releaseMode, workingDir, log, svnChanges, clean)

            if ret == 'success':
                if upload:
                    doUploadToStaging(releaseMode, workingDir, buildVersion, log)
            else:
                break

            clean = 'clean'

        if ret == 'success':
            for releaseMode in releaseModes:
                doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped)

            if skipTests:
                ret = 'success'
            else:
                for releaseMode in releaseModes:
                    #ret = doProjectTests(releaseMode, workingDir,
                    #                     outputDir, buildVersion, log)
                    #if ret != 'success':
                    #    break

                    ret = doTests(releaseMode, workingDir,
                                  outputDir, buildVersion, log)
                    if ret != 'success':
                        break

        changes = "-first-run"
    else:
        print "Checking SVN for updates"
        log.write("Checking SVN for updates\n")

        (svnChanges, svnRevisions) = changesInSVN(workingDir, log)

        if svnChanges['external'] or svnChanges['internal'] or svnChanges['chandler']:
            log.write("Changes in SVN require build\n")
            changes = "-changes"
            clean   = 'realclean'

            for releaseMode in releaseModes:
                ret = doBuild(releaseMode, workingDir, log, svnChanges, clean)

                if ret != 'success':
                    break
                else:
                    if upload:
                        doUploadToStaging(releaseMode, workingDir, buildVersion, log)

                    clean = 'clean'

        if ret == 'success' and (svnChanges['external'] or svnChanges['internal'] or svnChanges['chandler']):
            log.write("Changes in SVN require making distributions\n")
            changes = "-changes"
            for releaseMode in releaseModes:
                doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped)

        else:
            log.write("No changes\n")
            changes = "-nochanges"

        if ret == 'success':
            # do tests
            if not skipTests:
                for releaseMode in releaseModes:   
                    ret = doTests(releaseMode, workingDir,
                                  outputDir, buildVersion, log)
                    if ret != 'success':
                        break

    os.chdir(workingDir + '/external')

    return (ret + changes, svnRevisions['chandler'])

def doProjectTests(mode, workingDir, outputDir, buildVersion, log):

    testDir = os.path.join(workingDir, "external")
    os.chdir(testDir)

    try:
        print "Testing " + mode
        log.write(separator)
        log.write("Testing " + mode + " ...\n")

        if buildmode == "debug":
            dbgStr = "DEBUG=1"
        else:
            dbgStr = ""

        outputList = hardhatutil.executeCommandReturnOutput([buildenv['make'], dbgStr, 'test'])
        hardhatutil.dumpOutputList(outputList, log)

    except Exception, e:
        print "a testing error"
        doCopyLog("***Error during tests***", workingDir, logPath, log)
        return "test_failed"
    else:
        doCopyLog("Tests successful", workingDir, logPath, log)

    return "success"


def doTests(mode, workingDir, outputDir, buildVersion, log):

    testDir    = os.path.join(workingDir, "chandler")
    testLogDir = os.path.join(testDir, 'test_profile')
    os.chdir(testDir)

    try:
        print "Testing " + mode
        log.write(separator)
        log.write("Testing " + mode + " ...\n")
        log.write("Logging to %s\n" % testLogDir)

        cmd = [pythonProgram, './tools/rt.py', '-Ti', '-u', '-m %s' % mode]

        log.write("cmd: %s\n" % ' '.join(cmd))

        outputList = hardhatutil.executeCommandReturnOutput(cmd)
        hardhatutil.dumpOutputList(outputList, log)

    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "unit tests failed", e.exitCode
        log.write("***Error during unit tests***\n")
        log.write("Test log:\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        if e.exitCode == 0:
            err = ''
        else:
            err = '***Error '
        log.write("%sexit code=%s\n" % (err, e.exitCode))
        log.write("NOTE: If the tests themselves passed but the exit code\n")
        log.write("      reports failure, it means a shutdown problem.\n")
        forceBuildNextCycle(log, workingDir)
        return "test_failed"
    except Exception, e:
        print "a testing error"
        log.write("***Internal Error during test run: %s\n" % str(e))
        doCopyLog("***Error during unit tests***", testLogDir, 'chandler.log', log)
        return "test_failed"
    else:
        doCopyLog("Tests successful", testLogDir, 'chandler.log', log)

    return "success"  # end of doTests( )


def checkDistributionSize(log, releaseMode, workingDir, buildVersionEscaped):
    try:
        class UnexpectedSize(Exception):
            def __init__(self, f, actual, minSize, maxSize):
                self.f       = f
                self.actual  = actual
                self.minSize = minSize
                self.maxSize = maxSize
            def __str__(self):
                return 'file=%s, actual=%s, min=%s, max=%s' % (self.f,
                                                               self.actual,
                                                               self.minSize,
                                                               self.maxSize)

        sizes = {#plat     mode        suffix:max, ...
                 'win':   {'debug':   {'exe': 30, 'zip': 50},
                           'release': {'exe': 25, 'zip': 35},
                          },
                 'osx':   {'debug':   {'dmg': 50},
                           'release': {'dmg': 90},
                          },
                 'iosx':  {'debug':   {'dmg': 50},
                           'release': {'dmg': 110},
                          },
                 'linux': {'debug':   {'deb': 70, 'rpm': 70, 'gz': 70},
                           'release': {'deb': 40, 'rpm': 40, 'gz': 40},
                          },
                }

        if os.name == 'nt' or sys.platform == 'cygwin':
            buildPlatform = 'win'
        elif sys.platform == 'darwin':
            if platform.processor() == 'i386' and platform.machine() == 'i386':
                buildPlatform = 'iosx'
            else:
                buildPlatform = 'osx'
        else:
            buildPlatform = 'linux'

        for f in glob.glob('../*%s*' % buildVersionEscaped):
            if not os.path.isfile(f):
                continue
            suffix = f[f.rfind('.')+1:]
            size   = os.stat(f).st_size

            # See http://en.wikipedia.org/wiki/Megabyte
            minSize = 5 * (1024**2)
            maxSize = sizes[buildPlatform][releaseMode][suffix] * (1024**2)

            if not minSize < size < maxSize:
                raise UnexpectedSize(f, size, minSize, maxSize)

    except UnexpectedSize, e1:
        doCopyLog("***Error: %s unexpected distribution size %d, expected range %d-%d*** " % (e1.f, e1.actual, e1.minSize, e1.maxSize), workingDir, logPath, log)
        forceBuildNextCycle(log, workingDir)
        raise e1
    except Exception, e2:
        doCopyLog("***Error during distribution size measurement*** ", workingDir, logPath, log)
        forceBuildNextCycle(log, workingDir)
        raise e2


def doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped):
    #   Create end-user, developer distributions
    print "Making distribution files for " + releaseMode
    log.write(separator)
    log.write("Making distribution files for " + releaseMode + "\n")

    chanDir = os.path.join(workingDir, 'chandler')
    os.chdir(chanDir)

    try:
        cmd = [ pythonProgram, './tools/distribute.py',
                               '-o %s' % os.path.join(outputDir, buildVersion),
                               '-m %s' % releaseMode,
                               '-t %s' % buildVersion ]

        outputList = hardhatutil.executeCommandReturnOutput(cmd)
        hardhatutil.dumpOutputList(outputList, log)

    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "distribution failed", e.exitCode
        log.write("***Error during distribution***\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        forceBuildNextCycle(log, workingDir)
        raise e

    except Exception, e:
        doCopyLog("***Error during distribution building*** ", workingDir, logPath, log)
        forceBuildNextCycle(log, workingDir)
        raise e

    checkDistributionSize(log, releaseMode, workingDir, buildVersionEscaped)



def doCopyLog(msg, workingDir, logPath, log):
    # hardhat scripts should leave harhat.log behind both on success and
    # failure (barring catastrophic failure), so we can copy that into the
    # build log
    log.write(msg + "\n")
    log.write(separator)
    logPath = os.path.join(workingDir, logPath)
    log.write("Contents of " + logPath + ":\n")
    if os.path.exists(logPath):
        CopyLog(logPath, log)
    else:
        log.write(logPath + ' does not exist!\n')
    log.write(separator)


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

def changesInSVN(workingDir, log):
    changesDict   = {}
    revisionsDict = {}

    os.chdir(workingDir)

    for module in reposModules:
        log.write("[tbox] Checking for updates [%s] [%s]\n" % (workingDir, module))

        moduleDir = os.path.join(workingDir, module)

        changesDict[module] = False

        print "[%s] [%s] [%s]" % (workingDir, module, moduleDir)
        os.chdir(moduleDir)

        outputList = hardhatutil.executeCommandReturnOutputRetry([svnProgram, "up"])

        revisionsDict[module] = determineRevision(outputList)

        hardhatutil.dumpOutputList(outputList, log) 

        if NeedsUpdate(outputList):
            changesDict[module] = True
            log.write("%s needs updating\n" % module)
        else:
            log.write("%s unchanged\n" % module)

    log.write(separator)
    log.write("Done with SVN\n")

    return (changesDict, revisionsDict)


def doUploadToStaging(buildmode, workingDir, buildVersion, log):
    print "doUploadToStaging..."
    
    if buildmode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""

    buildRoot =  os.path.join(workingDir, 'external')
    print 'Setting BUILD_ROOT=', buildRoot
    log.write('Setting BUILD_ROOT=' + buildRoot + '\n')
    os.putenv('BUILD_ROOT', buildRoot)
    os.chdir(buildRoot)
    uploadDir = os.path.join(buildRoot, buildVersion)
    if not os.path.exists(uploadDir):
        os.mkdir(uploadDir)

    try:
        upload = ' uploadstaging UPLOAD=' + uploadDir
        print "Doing make " + dbgStr + upload
        log.write("Doing make " + dbgStr + upload + "\n")

        outputList = hardhatutil.executeCommandReturnOutput( [buildenv['make'], dbgStr, upload])
        hardhatutil.dumpOutputList(outputList, log)

        log.write(separator)

    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "upload error"
        log.write("***Error during upload***\n")
        log.write(separator)
        log.write("Build log:" + "\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        log.write(separator)
        raise e
    except Exception, e:
        print "upload error"
        log.write("***Error during upload***\n")
        log.write(separator)
        log.write(str(e) + "\n")
        log.write("(No build log!)\n")
        log.write(separator)
        raise e


def doBuild(buildmode, workingDir, log, svnChanges, clean='realclean'):
    # We only build external if there were changes in it
    # We build internal if external or internal were changed
    # We never build in chandler, because there is nothing to build
    if buildmode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""

    buildRoot =  os.path.join(workingDir, 'external')
    print 'Setting BUILD_ROOT=', buildRoot
    log.write('Setting BUILD_ROOT=' + buildRoot + '\n')
    os.putenv('BUILD_ROOT', buildRoot)

    ret = 'build_failed'

    try:
        for module in reposModules:
            print module, "..."
            log.write("- - - - " + module + " - - - - - - -\n")

            if module == 'external' and not svnChanges['external']:
                print 'Nothing to be done for module', module
                log.write('Nothing to be done for module ' + module + '\n')
                log.write(separator)
                continue
            if module == 'internal' and not svnChanges['external'] and not svnChanges['internal']:
                print 'Nothing to be done for module', module
                log.write('Nothing to be done for module ' + module + '\n')
                log.write(separator)
                continue

            # we get here only if the module is chandler or if changes have occurred
            # in external or internal
            if module == 'chandler':
                clean = 'clean'
                makeTargets = dbgStr + " " + clean + " distrib"
            else:
                makeTargets = dbgStr + " " + clean + " world"

            moduleDir = os.path.join(workingDir, module)
            print "cd", moduleDir
            log.write("cd " + moduleDir + "\n")
            os.chdir(moduleDir)

            print "Doing make " + makeTargets + "\n"
            log.write("Doing make " + makeTargets + "\n")

            outputList = hardhatutil.executeCommandReturnOutput( [buildenv['make'], makeTargets])
            hardhatutil.dumpOutputList(outputList, log)

            log.write(separator)

        ret = 'success'

    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "build error"
        log.write("***Error during build***\n")
        log.write(separator)
        log.write("Build log:" + "\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        if e.exitCode == 0:
            err = ''
        else:
            err = '***Error '
        log.write("%sexit code=%s\n" % (err, e.exitCode))

    except Exception, e:
        print "build error"
        log.write("***Error during build***\n")
        log.write(separator)        
        log.write("No build log!\n")
        log.write(separator)
        forceBuildNextCycle(log, workingDir)

    return ret

def forceBuildNextCycle(log, workingDir):
    doRealclean(log, workingDir)
    # We trigger build for next cycle by removing toplevel Makefiles
    # which will be noticed as an 'update' in the beginning of next
    # cycle which will cause doBuild etc. to be called.
    print 'Removing toplevel Makefiles to trigger build next cycle'
    log.write('Removing toplevel makefiles to trigger build next cycle\n')
    for module in reposModules:
        makefile = os.path.join(workingDir, module, 'Makefile')
        if os.path.exists(makefile):
            os.remove(makefile)
    

def doRealclean(log, workingDir):
    try:
        # If make install fails, it will almost certainly fail next time
        # as well - the typical case has been bad binaries packages.
        # So what we do here is try to do realclean which will force
        # the build to get new binaries tarballs next time, and if fixed
        # binaries were uploaded in the meanwhile we'll recover
        # automatically. This will also sort us out of corrupted debug/release.
        for module in reposModules:
            print "Doing make realclean in " + module + "\n"
            log.write("Doing make realclean in " + module + "\n")
            moduleDir = os.path.join(workingDir, module)
            os.chdir(moduleDir)
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], "realclean"])
            hardhatutil.dumpOutputList(outputList, log)
    except:
        print "make realclean failed\n"
        log.write("make realclean failed\n")


def NeedsUpdate(outputList):
    for line in outputList: 
        if line.lower().startswith('at revision'):
            # used to prevent the message that SVN produces when
            # nothing was updated from tripping the 'A' check below
            continue
        if line.lower().find("ide scripts") != -1:
            # this hack is for skipping some Mac-specific files that
            # under Windows always appear to be needing an update
            continue
        if line.lower().find("xercessamples") != -1:
            # same type of hack as above
            continue
        if line.lower().startswith('restored'):
            # treat a restored file as if it is a modified file
            print "needs update because of", line
            return True

        s = line[:4]  # in subversion, there are 3 possible positions
                      # the update flags are found

        if s.find("U") != -1:
            print "needs update because of", line
            return True
        if s.find("P") != -1:
            print "needs update because of", line
            return True
        if s.find("A") != -1:
            print "needs update because of", line
            return True
        if s.find("G") != -1:
            print "needs update because of", line
            return True
        if s.find("!") != -1:
            print "needs update because of", line
            return True
    return False


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

