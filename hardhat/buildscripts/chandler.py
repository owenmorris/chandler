# Chandler blueprint

"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

# To appease older Pythons:
True = 1
False = 0


import os, hardhatutil, sys


treeName = "Chandler"

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log):

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

    # do debug
    ret = Do(hardhatScript, "debug", workingDir, outputDir, cvsVintage, 
     buildVersion, clobber, log)

    if not ret:
        # the code hasn't changed
        return False

    # do release
    ret = Do(hardhatScript, "release", workingDir, outputDir, cvsVintage, 
     buildVersion, clobber, log)

    return ret



# These modules are the ones to check out of CVS
cvsModules = (
    'osaf/chandler/Chandler',
    'osaf/chandler/python',
    'osaf/chandler/zodb',
    'osaf/chandler/egenix-mx',
    'osaf/chandler/wxpython',
    'osaf/chandler/jabber-py',
    'osaf/chandler/pychecker',
    'osaf/chandler/persistence',
    'osaf/chandler/pyxml',
    'osaf/chandler/4suite',
)

# If any of these modules have changed, scrub everything before building
scrubAllModules = {
    'osaf/chandler/python':1,
    'osaf/chandler/zodb':1,
    'osaf/chandler/egenix-mx':1,
    'osaf/chandler/wxpython':1,
    'osaf/chandler/jabber-py':1,
    'osaf/chandler/pychecker':1,
    'osaf/chandler/persistence':1,
    'osaf/chandler/pyxml':1,
    'osaf/chandler/4suite':1,
}

mainModule = 'osaf/chandler/Chandler'
logPath = 'osaf/chandler/hardhat.log'


def Do(hardhatScript, mode, workingDir, outputDir, cvsVintage, buildVersion, 
 clobber, log):

    print "Do " + mode
    log.write("Performing " + mode + " build, version " + buildVersion + "\n")
    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    path = os.environ.get('PATH', os.environ.get('path'))

    cvsProgram = hardhatutil.findInPath(path, "cvs")

    modeDir = os.path.join(workingDir, mode)

    if os.name == 'nt':
        osName = 'win'
    elif os.name == 'posix':
        osName = 'linux'
        if sys.platform == 'darwin':
            osName = 'osx'
        if sys.platform == 'cygwin':
            osName = 'win'

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

    if not changesAtAll:
        return False

    if needToScrubAll:
        os.chdir(mainModuleDir)
        print "Scrubbing all"
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Scrubbing all modules" + "\n")
        try:
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-nS"])
        except Exception, e:
            log.write("***Error during scrub***" + "\n")
            CopyLog(os.path.join(modeDir, logPath), log)
            raise e

        libraryDir = os.path.join(modeDir, "osaf", "chandler", mode)
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
            log.write("***Error during scrub***" + "\n")
            CopyLog(os.path.join(modeDir, logPath), log)
            raise e

    os.chdir(mainModuleDir)

    # Only do a big build if there were new or updated modules
    if needToScrubAll or newModules:
        bigBLittleB = "B"
    else:
        bigBLittleB = "b"

    try:
        if mode == "debug":
            print "Building debug"
            log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
            log.write("Building debug..." + "\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-o", outputDir, "-d"+bigBLittleB+"t", 
             "-D", buildVersionEscaped])

        if mode == "release":
            print "Building release"
            log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
            log.write("Building release..." + "\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-o", outputDir, "-r"+bigBLittleB+"t", 
             "-D", buildVersionEscaped])

    except Exception, e:
        print "a build error"
        log.write("***Error during build***" + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Build log:" + "\n")
        CopyLog(os.path.join(modeDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        raise e
    else:
        log.write("Build successful" + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Detailed Build :og:" + "\n")
        CopyLog(os.path.join(modeDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    return True  # end of Do( )



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
        if line[0] == "R":
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


