# Chandler blueprint for new build process

"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

# To appease older Pythons:
True = 1
False = 0


import os, hardhatutil, hardhatlib, sys, re

path = os.environ.get('PATH', os.environ.get('path'))
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))
cvsProgram = hardhatutil.findInPath(path, "cvs")
treeName = "Chandler"
mainModule = 'chandler'
logPath = 'hardhat.log'
separator = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"
releaseModes = ('debug', 'release')

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log, skipTests=False):

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
    chanDir = os.path.join(workingDir, mainModule)
    # test if we've been thruough the loop at least once
    if clobber == 1:
        if os.path.exists(chanDir):
            hardhatutil.rmdirRecursive(chanDir)
            
    os.chdir(workingDir)

    # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")
    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)
    os.mkdir(outputDir)
    
    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")
    
    if not os.path.exists(chanDir):
        # Initialize sources
        print "Setup source tree..."
        log.write("- - - - tree setup - - - - - - -\n")
        
        outputList = hardhatutil.executeCommandReturnOutputRetry(
         [cvsProgram, "-q -z3", "checkout", cvsVintage, "chandler"])
        hardhatutil.dumpOutputList(outputList, log)
    
        os.chdir(chanDir)
    
        for releaseMode in releaseModes:
            doInstall(releaseMode, workingDir, log)

            doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped, hardhatScript)

            if skipTests:
                ret = 'success'
            else:
                ret = doTests(hardhatScript, releaseMode, workingDir,
                              outputDir, cvsVintage, buildVersion, log)
                if ret != 'success':
                    break

        changes = "-first-run"
    else:
        os.chdir(chanDir)
    
        print "Checking CVS for updates"
        log.write("Checking CVS for updates\n")
        cvsChanges = changesInCVS(chanDir, workingDir, cvsVintage, log)
        
        if cvsChanges:
            log.write("Changes in CVS require install\n")
            changes = "-changes"
            for releaseMode in releaseModes:        
                doInstall(releaseMode, workingDir, log)
                
        if cvsChanges:
            log.write("Changes in CVS require making distributions\n")
            changes = "-changes"
            for releaseMode in releaseModes:
                doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped, hardhatScript)
                    
        if not cvsChanges:
            log.write("No changes\n")
            changes = "-nochanges"

        # do tests
        if skipTests:
            ret = 'success'
        else:
            for releaseMode in releaseModes:   
                ret = doTests(hardhatScript, releaseMode, workingDir,
                              outputDir, cvsVintage, buildVersion, log)
                if ret != 'success':
                    break

    return ret + changes 


# These modules are the ones to check out of CVS
cvsModules = (
    'chandler',
)

def doTests(hardhatScript, mode, workingDir, outputDir, cvsVintage, buildVersion, log):

    testDir = os.path.join(workingDir, "chandler")
    os.chdir(testDir)

    if mode == "debug":
        dashT = '-dvt'
    else:
        dashT = '-vrt'
    
    try: # test
        print "Testing " + mode
        log.write(separator)
        log.write("Testing " + mode + " ...\n")
        outputList = hardhatutil.executeCommandReturnOutput(
         [hardhatScript, dashT])
        hardhatutil.dumpOutputList(outputList, log)

    except Exception, e:
        print "a testing error"
        doCopyLog("***Error during tests***", workingDir, logPath, log)
        forceBuildNextCycle(log, workingDir)
        return "test_failed"
    else:
        doCopyLog("Tests successful", workingDir, logPath, log)

    return "success"  # end of doTests( )


def doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped, hardhatScript):
    #   Create end-user, developer distributions
    print "Making distribution files for " + releaseMode
    log.write(separator)
    log.write("Making distribution files for " + releaseMode + "\n")
    if releaseMode == "debug":
        distOption = "-dD"
    else:
        distOption = "-D"

    try:
        outputList = hardhatutil.executeCommandReturnOutput(
         [hardhatScript, "-o", os.path.join(outputDir, buildVersion), distOption, buildVersionEscaped])
        hardhatutil.dumpOutputList(outputList, log)
    except Exception, e:
        doCopyLog("***Error during distribution building process*** ", workingDir, logPath, log)
        forceBuildNextCycle(log, workingDir)
        raise e


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
    

def changesInCVS(moduleDir, workingDir, cvsVintage, log):
    changesAtAll = False
    for module in cvsModules:
        print module, "..."
        log.write("- - - - " + module + " - - - - - - -\n")
        moduleDir = os.path.join(workingDir, module)
        os.chdir(moduleDir)
        # print "seeing if we need to update", module
        log.write("Seeing if we need to update " + module + "\n")
        outputList = hardhatutil.executeCommandReturnOutputRetry(
         [cvsProgram, "-qn", "update", "-d", cvsVintage])
        # hardhatutil.dumpOutputList(outputList, log)
        if NeedsUpdate(outputList):
            changesAtAll = True
            print "" + module + " needs updating"
            # update it
            print "Getting changed sources"
            log.write("Getting changed sources\n")
            
            outputList = hardhatutil.executeCommandReturnOutputRetry(
            [cvsProgram, "-q -z3", "update", "-dP", cvsVintage])
            hardhatutil.dumpOutputList(outputList, log)
        
        else:
            # print "NO, unchanged"
            log.write("Module unchanged" + "\n")

    log.write(separator)
    log.write("Done with CVS\n")
    return changesAtAll


def doInstall(buildmode, workingDir, log, cleanFirst=False):
    # for our purposes, we do not really do a build
    # we will update chandler from CVS, and grab new tarballs when they appear
    if buildmode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""

    if cleanFirst:
        clean = " clean "
    else:
        clean = " "

    moduleDir = os.path.join(workingDir, mainModule)
    os.chdir(moduleDir)
    print "Doing make " + dbgStr + clean + "install\n"
    log.write("Doing make " + dbgStr + clean + "install\n")

    try:
        outputList = hardhatutil.executeCommandReturnOutput(
          [buildenv['make'], dbgStr, clean, "install" ])
        hardhatutil.dumpOutputList(outputList, log)
    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "build error"
        log.write("***Error during build***\n")
        log.write(separator)
        log.write("Build log:" + "\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        log.write(separator)
        forceBuildNextCycle(log, workingDir)
        raise e
    except Exception, e:
        print "build error"
        log.write("***Error during build***\n")
        log.write(separator)        
        log.write("No build log!\n")
        log.write(separator)
        forceBuildNextCycle(log, workingDir)
        raise e


def forceBuildNextCycle(log, workingDir):
    doRealclean(log, workingDir)
    # We trigger build for next cycle by removing /chandler/Makefile,
    # which will be noticed as an 'update' in the beginning of next
    # cycle which will cause doInstall etc. to be called.
    print 'Removing chandler/Makefile to trigger build next cycle'
    log.write('Removing chandler/Makefile to trigger build next cycle\n')
    chandlerMakefile = os.path.join(workingDir, mainModule, 'Makefile')
    if os.path.exists(chandlerMakefile):
        os.remove(chandlerMakefile)
    

def doRealclean(log, workingDir):
    try:
        # If make install fails, it will almost certainly fail next time
        # as well - the typical case has been bad binaries packages.
        # So what we do here is try to do realclean which will force
        # the build to get new binaries tarballs next time, and if fixed
        # binaries were uploaded in the meanwhile we'll recover
        # automatically. This will also sort us out of corrupted debug/release.
        print "Doing make realclean\n"
        log.write("Doing make realclean\n")
        moduleDir = os.path.join(workingDir, mainModule)
        os.chdir(moduleDir)
        outputList = hardhatutil.executeCommandReturnOutput(
         [buildenv['make'], "realclean"])
        hardhatutil.dumpOutputList(outputList, log)
    except:
        print "make realclean failed\n"
        log.write("make realclean failed\n")

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

