# Chandler new build process - run tests only

"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

import os, hardhatutil, hardhatlib, sys, re

treeName = "Chandler"
path = os.environ.get('PATH', os.environ.get('path'))
cvsProgram = hardhatutil.findInPath(path, "cvs")
mainModule = 'chandler'
logPath = 'hardhat.log'

# Here is a trick to figure out what directory hardhat lives in, even if
# we were called found by the user's PATH
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log):

    global ret

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
    
    # find path to buildscripts
    thisScriptDir = buildenv['hardhatroot'] + os.sep + "buildscripts"
    print "HardHat log:  ", os.path.join(workingDir, "hardhat.log")
    print "Build scripts dir is " + thisScriptDir + "\n"

    # initialize return value
    ret = "no_changes" 

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
    
    print "Running tests"
    # do debug
    ret = Do(hardhatScript, "debug", workingDir, outputDir, cvsVintage, 
     buildVersion, log)

    modeDir = os.path.join(workingDir, "debug")
    CopyLog(os.path.join(modeDir, logPath), log)

    # do release
    ret = Do(hardhatScript, "release", workingDir, outputDir, cvsVintage, 
     buildVersion, log)
    modeDir = os.path.join(workingDir, "release")
    CopyLog(os.path.join(modeDir, logPath), log)

    hardhatlib.log_rotate(buildenv)

    # return ret
    return "success"


def Do(hardhatScript, mode, workingDir, outputDir, cvsVintage, buildVersion, log):

    print "Do " + mode
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
    
    os.chdir(modeDir)

    testResult = DoTests(hardhatScript, modeDir, mode, log)

    return testResult  # end of Do( )

def DoTests (hardhatScript, modeDir, mode, log):

    try: # test
        if mode == "debug":
            testStr = "-dt"
        else:
            testStr = "-rt"
    
        print "Testing " + mode
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Testing " + mode + "...\n")
        outputList = hardhatutil.executeCommandReturnOutput(
         [hardhatScript, testStr])
        hardhatutil.dumpOutputList(outputList, log)

    except Exception, e:
        print "a testing error"
        log.write("***Error during tests*** " + e.str() + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Tests log:" + "\n")
        hardhatutil.dumpOutputList(outputList, log)
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

    return "success"  # end of DoTests( )


def CopyLog(file, fd):
    input = open(file, "r")
    line = input.readline()
    while line:
        fd.write(line)
        line = input.readline()
    input.close()
