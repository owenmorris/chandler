#!/bin/env python

"""
Nightly:  Do a complete checkout, build and release

Command-line frontend to hardhatlib.py (see description there)

"""

import os, sys, traceback, getopt, string


# Needs:  
# cvs module to checkout (chandler-source)
# which module to build (Chandler)
# working directory (nightly)
# release ID (2003.04.11)

def usage():
    print "python nightly [OPTION]..."
    print ""
    print "-c CVS-MODULE   which cvs module to checkout"
    print "-h              display this help message"
    print "-i RELEASE-ID   what to call this release"
    print "-m MODULE   	   build module to build"
    print "-w DIR   	   which directory to work in"

# Earlier versions of Python don't define these, so let's include them here:
True = 1
False = 0



# defaults:
cvsModule = "chandler-source"
module = "Chandler"
releaseId = None

workRoot = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:h:i:m:w:")
except getopt.GetoptError:
    usage()
    sys.exit(1)

# Look for args that we can process before initializing hardhatlib:
for opt, arg in opts:

    if opt == "-c":
	cvsModule = arg

    if opt == "-h":
	usage()
	sys.exit(0)

    if opt == "-i":
	releaseId = arg

    if opt == "-m":
	module = arg

    if opt == "-w":
	workRoot = arg


if workRoot:
    if not os.path.isdir(workRoot):
	print "Error,", workRoot, "is not a directory"
	sys.exit(1)

if workRoot:
    workRoot = os.path.abspath(workRoot)
    if string.find(workRoot, ' ') >= 0:
	print "ERROR: -w WORKDIR ("+workRoot+") cannot contain a space.  Exiting."
	sys.exit(1)
    print "Working directory:", workRoot
else:
    print "No Work directory provided; please set via -w"
    sys.exit(1)


# Initialize hardhatlib
import hardhatlib
# Here is a trick to figure out what directory nightly lives in, even if
# we were called found by the user's PATH
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))

try:
    buildenv = hardhatlib.init(workRoot)

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
buildenv['interactive'] = False
hardhatlib.log_rotate(buildenv)



try:
    hardhatlib.buildComplete(buildenv, releaseId, cvsModule, module)

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
