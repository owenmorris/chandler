#!/bin/env python

"""
HardHat:  OSAF Build Environment

Command-line frontend to hardhatlib.py (see description there)

"""

import os, sys, traceback, getopt, string

def usage():
    print "python hardhat.py [OPTION]..."
    print "Hardhat builds an application and its dependencies."
    print ""
    print "-a MODULE   remove runtime directory for MODULE"
    print "-b MODULE   build module MODULE"
    print "-B MODULE   build MODULE and its dependencies"
    print "-c MODULE   clean module MODULE"
    print "-C MODULE   clean MODULE and its dependencies"
    print "-d          use debug version" 
    print "-D          create a distribution" 
    print "-e          show environment variables in build.log"
    print "-h          display this help" 
    print "-i          inspect system (not implemented)" 
    print "-n          non-interactive (won't prompt during scrubbing)" 
    print "-r          use release version (this is the default)" 
    print "-R DIR      directory to use for OSAFROOT (overrides env var)" 
    # print "-s          spawn an interactive shell" 
    print "-s          scrub MODULE (remove all local files not in CVS)" 
    print "-S          scrub MODULE and its dependencies"
    print "-t MODULE   test module MODULE" 
    # print "-v          verbose"
    print "-x MODULE   execute MODULE" 

# Earlier versions of Python don't define these, so let's include them here:
True = 1
False = 0


osafRoot = None
osafRootArg = None
if os.environ.has_key('OSAFROOT'):
    osafRoot = os.environ['OSAFROOT']

try:
    opts, args = getopt.getopt(sys.argv[1:], "a:b:B:c:C:dD:ehilnrR:s:S:t:vx:")
except getopt.GetoptError:
    usage()
    sys.exit(1)

# Look for args that we can process before initializing hardhatlib:
for opt, arg in opts:

    if opt == "-i":
        print "Inspecting system:"
        import hardhatlib
        try:
            hardhatlib.inspectSystem()
        except hardhatlib.HardHatInspectionError:
            print "Failed inspection"
            sys.exit(1)

        print "Passed inspection"
        sys.exit(0)

    if opt == "-h":
	usage()
	sys.exit(0)

    if opt == "-R":
	osafRootArg = arg


if osafRootArg:
    if os.path.isdir(osafRootArg):
	osafRoot = osafRootArg
    else:
	print "Error,", osafRootArg, "is not a directory"
	sys.exit(1)

if osafRoot:
    osafRoot = os.path.abspath(osafRoot)
    if string.find(osafRoot, ' ') >= 0:
	print "ERROR: OSAFROOT("+osafRoot+") cannot contain a space.  Exiting."
	sys.exit(1)
    print "OSAFROOT is set to", osafRoot
else:
    print "No OSAFROOT directory provided; please set via environment variable or -R"
    sys.exit(1)



# Initialize hardhatlib
import hardhatlib
# Here is a trick to figure out what directory hardhat lives in, even if
# we were called found by the user's PATH
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))
try:
    buildenv = hardhatlib.init(osafRoot)

except hardhatlib.HardHatMissingCompilerError:
    print "Could not locate compiler.  Exiting."
    sys.exit(1)

except hardhatlib.HardHatUnknownPlatformError:
    print "Unsupported platform, '" + os.name + "'.  Exiting."
    sys.exit(1)

except Exception, e:
    print "Could not initialize hardhat environment.  Exiting."
    print "Exception:", e
    traceback.print_exc()
    raise e
    sys.exit(1)
    
buildenv['hardhatroot'] = whereAmI
buildenv['version'] = 'release'
buildenv['showlog'] = False
buildenv['interactive'] = True
hardhatlib.log_rotate(buildenv)



try:
    for opt, arg in opts:
        if opt == "-a":
            hardhatlib.removeRuntimeDir(buildenv, arg)

        if opt == "-b":
            hardhatlib.build(buildenv, arg)

        if opt == "-B":
	    history = {}
            hardhatlib.buildDependencies(buildenv, arg, history)

        if opt == "-c":
            if hardhatlib.clean(buildenv, arg) == hardhatlib.HARDHAT_ERROR:
                print "Error, exiting"

        if opt == "-C":
	    history = {}
            if hardhatlib.cleanDependencies(buildenv, arg, history) == \
             hardhatlib.HARDHAT_ERROR:
                print "Error, exiting"

        if opt == "-d":
            buildenv['version'] = 'debug'

        if opt == "-D":
            hardhatlib.distribute(buildenv, arg)

        if opt == "-e":
            buildenv['showenv'] = 1

        if opt == "-h":
            usage()

        if opt == "-l":
            buildenv['showlog'] = True

        if opt == "-n":
            buildenv['interactive'] = False

        if opt == "-r":
            buildenv['version'] = 'release'

        if opt == "-s":
            hardhatlib.scrub(buildenv, arg)

        if opt == "-S":
            hardhatlib.scrubDependencies(buildenv, arg)

        if opt == "-t":
            hardhatlib.test(buildenv, arg)

        if opt == "-v":
            buildenv['verbosity'] = buildenv['verbosity'] + 1

        if opt == "-x":
            hardhatlib.run(buildenv, arg)

    if len(args) > 0:
	hardhatlib.executeScript(buildenv, args)

except hardhatlib.HardHatExternalCommandError:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print " A program that HardHat spawned exited with a non-zero exit code."
    print "          Please view the file 'build.log' for details."
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"

except hardhatlib.HardHatMissingFileError, e:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print "HardHat cannot find one its __hardhat__.py files..."
    print e 
    print "Please make sure the above file exists and try again."
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"

except Exception, e:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print "Error in HardHat:", e
    print ""
    print "Displaying traceback:"
    print ""
    traceback.print_exc()
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"



if buildenv['showlog']:
    print "Build Log:"
    hardhatlib.log_dump(buildenv)
