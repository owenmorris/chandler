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

treeName = "Chandler"
path = os.environ.get('PATH', os.environ.get('path'))
cvsProgram = hardhatutil.findInPath(path, "cvs")
mainModule = 'chandler'
logPath = 'hardhat.log'

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log):

    global ret

    # find path to buildscripts
    thisScriptDir = os.path.join("/home/markie/hardhat", "buildscripts")
    print "Build scripts dir is " + thisScriptDir + "\n"

    # make sure workingDir is absolute, remove it, and create it
    workingDir = os.path.abspath(workingDir)
    if not os.path.exists(workingDir):
        os.mkdir(workingDir)
    os.chdir(workingDir)

    # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")
    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)
    os.mkdir(outputDir)
    # Initialize external (hardly ever changes)
    print "Initializing external modules ..."
    log.write("- - - - external - - - - - - -\n")
    # not needed here?    moduleData["external"] = {}
    
    # Do external setup for both debug and release here
    for releaseMode in ('debug', 'release'):
        releaseModeDir = os.path.join(workingDir, releaseMode)
        if releaseMode == "debug":
            dbgStr = "DEBUG=1"
        else:
            dbgStr = ""

        ret = "no_changes" 
        extModuleDir = os.path.join(releaseModeDir, "external")
        intModuleDir = os.path.join(releaseModeDir, "internal")
        if not os.path.exists(releaseModeDir):
            os.mkdir(releaseModeDir)
            os.chdir(releaseModeDir)
            print "checking out external"
            log.write("Checking out: external with " + cvsVintage + "\n")
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [cvsProgram, "-q", "checkout", cvsVintage, "external"])
            hardhatutil.dumpOutputList(outputList, log)

            version = getVersion(os.path.join(extModuleDir, "Makefile"))
            sourceTarball = os.path.join(extModuleDir, "sources-" + version + ".tar")
            log.write("Checking for source tarball " + sourceTarball + "\n")
            if not os.path.exists(sourceTarball) :
                # Now need to do the setup for external - "expand" and "make"
                os.chdir(extModuleDir)
                log.write("Environment variables: \n")
                log.write("GCJ_HOME = " + os.environ['GCJ_HOME'] + "\n")
                os.environ["BUILD_ROOT"] = extModuleDir
                log.write("BUILD_ROOT = " + os.environ['BUILD_ROOT'] + "\n")
                os.environ["DEBUG"] = dbgStr
                log.write("DEBUG = " + os.environ['DEBUG'] + "\n")

                print "Building " + releaseMode
                log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
                log.write("Expanding external sources\n")
                try: 
                  #  outputList = hardhatutil.executeCommandReturnOutput(
                  #   [buildenv['make'], "expand" ])
                  #  hardhatutil.dumpOutputList(outputList, log)
                  #  outputList = hardhatutil.executeCommandReturnOutput(
                  #   [buildenv['make'], dbgStr ])
                  #  hardhatutil.dumpOutputList(outputList, log)
                  #  log.write("Making external (debug) binaries\n")
                  #  outputList = hardhatutil.executeCommandReturnOutput(
                  #   [buildenv['make'], dbgStr, "binaries" ])
                    initFile = os.path.join(thisScriptDir, 'init.sh')
                    log.write("Running init script from " + initFile + "\n")
                    outputList = hardhatutil.executeCommandReturnOutput(
                     [initFile] )
                    hardhatutil.dumpOutputList(outputList, log)

                except Exception, e:
                    print "an initialization error"
                    log.write("***Error during initialization*** " + e.str() + "\n")
                    log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
                    ret = "init_failed"


            print "checking out internal"
            log.write("Checking out: internal with " + cvsVintage + "\n")
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [cvsProgram, "-q", "checkout", cvsVintage, "internal"])
            hardhatutil.dumpOutputList(outputList, log)
            os.chdir(intModuleDir)
            log.write("Making internal (debug) programs\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], dbgStr ])
            hardhatutil.dumpOutputList(outputList, log)
            log.write("Making internal (debug) binaries\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], dbgStr, "binaries" ])
            hardhatutil.dumpOutputList(outputList, log)
            ret = "no_changes" 

            os.chdir(releaseModeDir)
            log.write("Checking out: chandler with " + cvsVintage + "\n")
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [cvsProgram, "-q", "checkout", cvsVintage, "chandler"])
            hardhatutil.dumpOutputList(outputList, log)

    # do debug
    if ret == "no_changes":
        ret = Do(hardhatScript, "debug", workingDir, outputDir, cvsVintage, 
         buildVersion, clobber, log)

    if ret == "no_changes" or ret =="build_failed" or ret == "test_failed":
        modeDir = os.path.join(workingDir, "debug")
        CopyLog(os.path.join(modeDir, logPath), log)
        pass # return ret

    # do release
    ret = Do(hardhatScript, "release", workingDir, outputDir, cvsVintage, 
     buildVersion, clobber, log)
    modeDir = os.path.join(workingDir, "release")
    CopyLog(os.path.join(modeDir, logPath), log)

    return ret


# These modules are the ones to check out of CVS
cvsModules = (
    'chandler',
    'internal',
    'external',
)

# If any of these modules have changed, scrub everything before building
scrubAllModules = {
    'internal/wxPython-2.5':1,
    'internal/UUIDext':1,
    'internal/PyLucene':1,
    'external/Makefile':1,
}


def Do(hardhatScript, mode, workingDir, outputDir, cvsVintage, buildVersion, 
 clobber, log):

    print "Do " + mode
    log.write("Performing " + mode + " build, version " + buildVersion + "\n")
    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    modeDir = os.path.join(workingDir, mode)

    if os.name == 'nt':
        osName = 'win'
    elif os.name == 'posix':
        osName = 'linux'
        if sys.platform == 'darwin':
            osName = 'osx'
        if sys.platform == 'cygwin':
            osName = 'win'

    if mode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""
    
    if clobber:
        if os.path.exists(modeDir):
            hardhatutil.rmdirRecursive(modeDir)

    if not os.path.exists(modeDir):
        os.mkdir(modeDir)

    os.chdir(modeDir)

    moduleData = {}
    needToScrubAll = False
    newModules = False
    changesAtAll = False

    print "Examining CVS"
    log.write("Examining CVS\n")
    for module in cvsModules:
        print module, "..."
        log.write("- - - - " + module + " - - - - - - -\n")
        moduleData[module] = {}
        moduleDir = os.path.join(modeDir, module)
        # does module's directory exist?
        if not os.path.exists(moduleDir):
            newModules = True
            changesAtAll = True
            # check out that module
            os.chdir(modeDir)
            print "checking out", module
            log.write("Checking out: " + module + " with " + cvsVintage + "\n")
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [cvsProgram, "-q", "checkout", cvsVintage, module])
            hardhatutil.dumpOutputList(outputList, log)
        else:
            # it exists, see if it has changed
            os.chdir(moduleDir)
            # print "seeing if we need to update", module
            log.write("Seeing if we need to update " + module + "\n")
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [cvsProgram, "-qn", "update", "-d", cvsVintage])
            # hardhatutil.dumpOutputList(outputList, log)
            if NeedsUpdate(outputList):
                print "" + module + " needs updating"
                changesAtAll = True
                moduleData[module]["changed"] = 1
                # update it
                os.chdir(moduleDir)
                log.write("Module out of date; updating: " + module + " with " + cvsVintage + "\n")
                outputList = hardhatutil.executeCommandReturnOutputRetry(
                 [cvsProgram, "-q", "update", "-d", cvsVintage])
                hardhatutil.dumpOutputList(outputList, log)
                if scrubAllModules.has_key(module):
                    # print "we need to scrub everything"
                    # log.write("Scrubbing everything before build\n")
                    needToScrubAll = True
            else:
                # print "NO, unchanged"
                log.write("Module unchanged" + "\n")
                moduleData[module]["changed"] = 0

    log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
    log.write("Done with CVS\n")
    mainModuleDir = os.path.join(modeDir, mainModule)
    extModuleDir = os.path.join(modeDir, "external")
    intModuleDir = os.path.join(modeDir, "internal")

    if not changesAtAll:
        return "no_changes"

    if needToScrubAll:
        print "Scrubbing all"
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Scrubbing all modules" + "\n")
        try:
            os.chdir(extModuleDir)
            log.write("Cleaning external\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], dbgStr, "clean" ])
            hardhatutil.dumpOutputList(outputList, log)
            os.chdir(intModuleDir)
            log.write("Cleaning internal\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], dbgStr, "clean" ])
            hardhatutil.dumpOutputList(outputList, log)
            os.chdir(mainModuleDir)
            log.write("Cleaning chandler\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-ns"])
            hardhatutil.dumpOutputList(outputList, log)

        except Exception, e:
            log.write("***Error during scrub*** " + e.str() + "\n")
            if os.path.exists(os.path.join(modeDir, logPath)) :
                CopyLog(os.path.join(modeDir, logPath), log)
            raise e

        libraryDir = os.path.join(modeDir, "chandler", mode)
        if os.path.exists(libraryDir):
            hardhatutil.rmdirRecursive(libraryDir)
    else:
        os.chdir(mainModuleDir)
        print "scrubbing only Chandler"
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Scrubbing only Chandler" + "\n")
        try:
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-ns"])
        except Exception, e:
            log.write("***Error during scrub*** " + e.str() + "\n")
            if os.path.exists(os.path.join(modeDir, logPath)) :
                CopyLog(os.path.join(modeDir, logPath), log)
            raise e

    os.chdir(mainModuleDir)

    # Only do a big build if there were new or updated modules
    

    try: # build
        if needToScrubAll or newModules:
            print "Building all in " + mode
            log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
            log.write("Building " + mode + "...\n")
            os.chdir(extModuleDir)
            log.write("Making external programs\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], dbgStr ])
            hardhatutil.dumpOutputList(outputList, log)
            log.write("Making external binaries\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], dbgStr, "binaries" ])
            hardhatutil.dumpOutputList(outputList, log)

        os.chdir(intModuleDir)
        log.write("Making internal programs\n")
        outputList = hardhatutil.executeCommandReturnOutput(
         [buildenv['make'], dbgStr ])
        hardhatutil.dumpOutputList(outputList, log)
        log.write("Making internal binaries\n")
        outputList = hardhatutil.executeCommandReturnOutput(
         [buildenv['make'], dbgStr, "binaries" ])
        hardhatutil.dumpOutputList(outputList, log)

        
    except Exception, e:
        print "a build error"
        log.write("***Error during build*** " + e.str() + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Build log:" + "\n")
        if os.path.exists(os.path.join(modeDir, logPath)) :
            CopyLog(os.path.join(modeDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        return "build_failed"
    else:
        log.write("Build successful" + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Detailed Build log:" + "\n")
        if os.path.exists(os.path.join(modeDir, logPath)) :
            CopyLog(os.path.join(modeDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    try: # test
        if mode == "debug":
            print "Testing debug"
            log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
            log.write("Testing debug..." + "\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-dt"])
            hardhatutil.dumpOutputList(outputList, log)

        if mode == "release":
            print "Testing release"
            log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
            log.write("Testing release..." + "\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-rt"])
            hardhatutil.dumpOutputList(outputList, log)

    except Exception, e:
        print "a testing error"
        log.write("***Error during tests*** " + e.str() + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Tests log:" + "\n")
        if os.path.exists(os.path.join(modeDir, logPath)) :
            CopyLog(os.path.join(modeDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        return "test_failed"
    else:
        log.write("Tests successful" + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Detailed Tests log:" + "\n")
        if os.path.exists(os.path.join(modeDir, logPath)) :
            CopyLog(os.path.join(modeDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    return "success"  # end of Do( )



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

