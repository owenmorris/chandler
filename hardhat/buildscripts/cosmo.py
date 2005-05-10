"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

import os, sys, re
import hardhatutil, hardhatlib

path       = os.environ.get('PATH', os.environ.get('path'))
whereAmI   = os.path.dirname(os.path.abspath(hardhatlib.__file__))
cvsProgram = hardhatutil.findInPath(path, "cvs")
antProgram = hardhatutil.findInPath(path, "ant")
treeName   = "Cosmo"
mainModule = 'server'
logPath    = 'hardhat.log'
separator  = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log, skipTests=False, upload=False):

      # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)
    buildDir   = os.path.join(workingDir, mainModule)

    os.chdir(workingDir)

      # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")

    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)

    os.mkdir(outputDir)

    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    if not os.path.exists(buildDir):
        log.write("[tbox] Pulling source tree\n")

        outputList = hardhatutil.executeCommandReturnOutputRetry(
         [cvsProgram, "-q -z3", "checkout", cvsVintage, mainModule])

        hardhatutil.dumpOutputList(outputList, log) 

        sourceChanged = True
    else:
        os.chdir(buildDir)

        log.write("[tbox] Checking for source updates\n")

        outputList = hardhatutil.executeCommandReturnOutputRetry([cvsProgram, "-q -z3", "update", "-Pd"])

        if NeedsUpdate(outputList):
            sourceChanged = True

            log.write("[tbox] %s needs updating\n" % mainModule)

            outputList = hardhatutil.executeCommandReturnOutputRetry([cvsProgram, "-q -z3", "update", "-dP", cvsVintage])

            hardhatutil.dumpOutputList(outputList, log)
        else:
            sourceChanged = False
            log.write("[tbox] %s unchanged\n" % mainModule)

    os.chdir(buildDir)

    doClean(workingDir, buildDir, log)

    doBuild(workingDir, buildDir, log)

    if skipTests:
        ret = 'success'
    else:
        ret = doTests(workingDir, buildDir, log)

    if sourceChanged:
        doDistribution(workingDir, buildDir, log, outputDir, buildVersion, buildVersionEscaped)

        changes = "-changes"
    else:
        changes = "-nochanges"

    print ret + changes

    return ret + changes 


def doClean(workingDir, buildDir, log):
    print "doClean [%s]" % workingDir
    try:
        log.write("[tbox] Clean build environment\n")

        os.chdir(buildDir)

        outputList = hardhatutil.executeCommandReturnOutput([antProgram, "clean", "dist-clean"])

        hardhatutil.dumpOutputList(outputList, log)
        
    except:
        log.write("[tbox] Clean build environment failed\n")


def doBuild(workingDir, buildDir, log):
    print "doBuild [%s]" % workingDir
    try:
        log.write("[tbox] Building\n")

        os.chdir(buildDir)

        outputList = hardhatutil.executeCommandReturnOutput([antProgram, "build"])

        hardhatutil.dumpOutputList(outputList, log)
        
    except:
        log.write("[tbox] Build failed\n")


def doTests(workingDir, buildDir, log):
    print "doTests [%s]" % workingDir
    try:
        log.write("[tbox] Running unit tests\n")

        os.chdir(buildDir)

        outputList = hardhatutil.executeCommandReturnOutput([antProgram, "test-dbsetup"])

        hardhatutil.dumpOutputList(outputList, log)

        outputList = hardhatutil.executeCommandReturnOutput([antProgram, "test"])

        hardhatutil.dumpOutputList(outputList, log)

    except Exception, e:
        doCopyLog("***Error during tests***", workingDir, logPath, log)
        return "test_failed"
    else:
        doCopyLog("Tests successful", workingDir, logPath, log)

    return "success"


def doDistribution(workingDir, buildDir, log, outputDir, buildVersion, buildVersionEscaped):
    print "doDistribution [%s]" % workingDir

    log.write(separator)
    log.write("[tbox] Creating distribution files\n")

    try:
        os.chdir(buildDir)

        outputList = hardhatutil.executeCommandReturnOutput([antProgram, "dist-release"])

        hardhatutil.dumpOutputList(outputList, log)

        sourceDir = os.path.join(buildDir, 'dist')
        targetDir = os.path.join(outputDir, buildVersion)

        if not os.path.exists(targetDir):
            os.mkdir(targetDir)

        print sourceDir, targetDir

        log.write("[tbox] Moving %s to %s\n" % (sourceDir, targetDir))

        hardhatlib.copyFiles(sourceDir, targetDir, 'cosmo*.tar.gz')

    except Exception, e:
        doCopyLog("***Error during distribution building process*** ", workingDir, logPath, log)
        raise e


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

