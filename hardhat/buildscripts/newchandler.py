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

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log):

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
        traceback.print_exc()
        raise e
        sys.exit(1)
    
    # make sure workingDir is absolute, remove it if it exists, and create it
    workingDir = os.path.abspath(workingDir)
    if os.path.exists(workingDir):
        hardhatutil.rmdirRecursive(workingDir)
    os.mkdir(workingDir)
    os.chdir(workingDir)

    # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")
    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)
    os.mkdir(outputDir)
    # Initialize sources
    print "Setup source tree..."
    log.write("- - - - tree setup - - - - - - -\n")
    
    outputList = hardhatutil.executeCommandReturnOutputRetry(
     [cvsProgram, "-q", "checkout", cvsVintage, "chandler"])
    hardhatutil.dumpOutputList(outputList, log)
    os.chdir("./chandler")

    for releaseMode in ('debug', 'release'):

        if releaseMode == "debug":
            dbgStr = "DEBUG=1"
        else:
            dbgStr = ""
        print "Doing make " + dbgStr + "install"

        log.write("Doing make " + dbgStr + "install with " + cvsVintage + "\n")

        outputList = hardhatutil.executeCommandReturnOutput(
         [buildenv['make'], dbgStr, "install" ])
        hardhatutil.dumpOutputList(outputList, log)

    # do tests
        ret = Do(hardhatScript, releaseMode, workingDir, outputDir, cvsVintage, 
         buildVersion, clobber, log)

        CopyLog(os.path.join(workingDir, logPath), log)

    return ret


# These modules are the ones to check out of CVS
cvsModules = (
    'chandler',
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

    testDir = os.path.join(workingDir, "chandler")
    print "Do " + mode
    log.write("Performing " + mode + " build, version " + buildVersion + "\n")
    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")
    log.write("( " + mode + " build skipped)\n")

    os.chdir(testDir)

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

