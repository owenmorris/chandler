# Chandler blueprint

import os, hardhatutil, sys

treeName = "Chandler"

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log):

    print "cvs vintage:", cvsVintage

    # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)

    if not os.path.exists(workingDir):
        os.mkdir(workingDir)
    os.chdir(workingDir)


    # do debug
    Do(hardhatScript, "debug", workingDir, cvsVintage, buildVersion, clobber, log)

    # do release
    Do(hardhatScript, "release", workingDir, cvsVintage, buildVersion, clobber, log)



# These modules are the ones to check out of CVS
cvsModules = (
    'osaf/chandler/Chandler',
    'osaf/chandler/python',
    'osaf/chandler/zodb',
    'osaf/chandler/distutils',
    'osaf/chandler/egenix-mx',
    'osaf/chandler/wxpython',
    'osaf/chandler/jabber-py',
)

# If any of these modules have changed, scrub everything before building
scrubAllModules = {
    'osaf/chandler/python':1,
    'osaf/chandler/zodb':1,
    'osaf/chandler/distutils':1,
    'osaf/chandler/egenix-mx':1,
    'osaf/chandler/wxpython':1,
    'osaf/chandler/jabber-py':1,
}

mainModule = 'osaf/chandler/Chandler'
logPath = 'osaf/chandler/hardhat.log'


def Do(hardhatScript, mode, workingDir, cvsVintage, buildVersion, clobber, log):

    print "Do " + mode
    log.write("Do " + mode + "\n")
    log.write("Build Version " + buildVersion + "\n")
    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")
    print buildVersion, buildVersionEscaped

    path = os.environ.get('PATH', os.environ.get('path'))
    print "Path =", path

    cvsProgram = hardhatutil.findInPath(path, "cvs")
    print "CVS =", cvsProgram

    print "HardHat = ", hardhatScript

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
            print "removing", modeDir
            log.write("removing " + modeDir + "\n")
            hardhatutil.rmdirRecursive(modeDir)

    if not os.path.exists(modeDir):
        print "creating", modeDir
        log.write("creating " + modeDir + "\n")
        os.mkdir(modeDir)

    os.chdir(modeDir)

    moduleData = {}
    needToScrubAll = 0

    for module in cvsModules:
        print "- - - -", module, "- - - - - - - - - - - - - - - - -"
        log.write("module: " + module + "\n")

        moduleData[module] = {}
        moduleDir = os.path.join(modeDir, module)
        # does module's directory exist?
        if not os.path.exists(moduleDir):
            # check out that module
            os.chdir(modeDir)
            print "checking out", module
            log.write("checking out: " + module + " with " + cvsVintage + "\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [cvsProgram, "-q", "checkout", cvsVintage, module])
            dumpOutputList(outputList, log)
        else:
            # it exists, see if it has changed
            os.chdir(moduleDir)
            print "seeing if we need to update", module
            outputList = hardhatutil.executeCommandReturnOutput(
             [cvsProgram, "-qn", "update", cvsVintage])
            dumpOutputList(outputList, log)
            if NeedsUpdate(outputList):
                print "YES"
                moduleData[module]["changed"] = 1
                # update it
                os.chdir(moduleDir)
                print "updating", module
                log.write("updating: " + module + " with " + cvsVintage + "\n")
                outputList = hardhatutil.executeCommandReturnOutput(
                 [cvsProgram, "-q", "update", cvsVintage])
                dumpOutputList(outputList, log)
                if scrubAllModules.has_key(module):
                    print "we need to scrub everything"
                    needToScrubAll = 1
            else:
                print "NO, unchanged"
                log.write("unchanged" + "\n")
                moduleData[module]["changed"] = 0

    mainModuleDir = os.path.join(modeDir, mainModule)
    print "Main module dir =", mainModuleDir
    if needToScrubAll:
        os.chdir(mainModuleDir)
        print "Scrubbing all"
        log.write("scrubbing all" + "\n")
        outputList = hardhatutil.executeCommandReturnOutput(
         [hardhatScript, "-nS"])
        libraryDir = os.path.join(modeDir, "osaf", "chandler", mode)
        if os.path.exists(libraryDir):
            print "removing", libraryDir
            log.write("removing " + libraryDir + "\n")
            hardhatutil.rmdirRecursive(libraryDir)
    else:
        os.chdir(mainModuleDir)
        print "scrubbing only Chandler"
        log.write("scrubbing only Chandler" + "\n")
        outputList = hardhatutil.executeCommandReturnOutput(
         [hardhatScript, "-ns"])

    os.chdir(mainModuleDir)
    try:
        if mode == "debug":
            print "Building debug"
            log.write("building debug" + "\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-dBt", "-D", buildVersionEscaped])
        if mode == "release":
            print "Building release"
            log.write("building release" + "\n")
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-rBt", "-D", buildVersionEscaped])
    except Exception, e:
        print "a build error"
        log.write("error during build" + "\n")
        log.write("build log:" + "\n")
        CopyLog(os.path.join(modeDir, logPath), log)
        log.write("end of log" + "\n")
        raise e
    else:
        log.write("build successful" + "\n")
        log.write("build log:" + "\n")
        CopyLog(os.path.join(modeDir, logPath), log)
        log.write("end of log" + "\n")


def dumpOutputList(outputList, fd = None):
    for line in outputList:
        print "------"+ line,
        if fd:
            fd.write(line)
    print

def NeedsUpdate(outputList):
    for line in outputList:
        if line.find("IDE Scripts"):
            # this hack is for skipping some Mac-specific files that
            # under Windows always appear to be needing an update
            continue
        if line[0] == "U":
            return 1
        if line[0] == "P":
            return 1
        if line[0] == "A":
            return 1
        if line[0] == "R":
            return 1

def CopyLog(file, fd):
    input = open(file, "r")
    line = input.readline()
    while line:
        fd.write(line)
        line = input.readline()
    input.close()


