# Chandler script for new build process
#  this is an edited version of newchandler.py
#   which only produces the distribution files

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
        traceback.print_exc()
        raise e
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
         [cvsProgram, "-q", "checkout", cvsVintage, mainModule])
        hardhatutil.dumpOutputList(outputList, log)
    
        os.chdir(chanDir)
    
        for releaseMode in ('debug', 'release'):
    
            doInstall(releaseMode, workingDir, log)
            #   Create end-user, developer distributions
            print "Making distribution files for " + releaseMode
            log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
            log.write("Making distribution files for " + releaseMode + "\n")
            if releaseMode == "debug":
                distOption = "-dD"
            else:
                distOption = "-D"
                
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-o", os.path.join(outputDir, buildVersion), distOption, buildVersionEscaped])
            hardhatutil.dumpOutputList(outputList, log)

    return "success-nochanges"

def doInstall(buildmode, workingDir, log):
# for our purposes, we do not really do a build
# we will update chandler from CVS, and grab new tarballs when they appear
    if buildmode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""

    moduleDir = os.path.join(workingDir, mainModule)
    os.chdir(moduleDir)
    print "Doing make " + dbgStr + " install\n"
    log.write("Doing make " + dbgStr + " install\n")

    outputList = hardhatutil.executeCommandReturnOutput(
     [buildenv['make'], dbgStr, "install" ])
    hardhatutil.dumpOutputList(outputList, log)


def CopyLog(file, fd):
    input = open(file, "r")
    line = input.readline()
    while line:
        fd.write(line)
        line = input.readline()
    input.close()

