#!/usr/bin/env python
__version__ 	= "$Revision$"
__date__ 	= "$Date$"
__copyright__ 	= "Copyright (c) 2003 Open Source Applications Foundation"
__license__	= "GPL -- see LICENSE.txt"


"""
Nightly:  Do a complete checkout, build and release

Command-line frontend to hardhatlib.py (see description there)

"""

import os, sys, traceback, getopt, string


def usage():
    print "python nightly [OPTION]..."
    print ""
    print "-c CVS-MODULE   which cvs module to checkout"
    print "-h              display this help message"
    print "-i RELEASE-ID   what to call this release"
    print "-m MODULE  	   module to build (path relative to project path)"
    print "-p PROJECT  	   project path (relative to workdir)"
    print "-r TAG 	   which cvs revision tag to use (default is HEAD)"
    print "-s              skip the building of the binaries"
    print "-w DIR   	   work directory (top level where source gets checked out)"

# Earlier versions of Python don't define these, so let's include them here:
True = 1
False = 0



# defaults:
cvsModule = "chandler-system"
project = "osaf/chandler"
module = "Chandler"
releaseId = None
revision = None
skipBinaries = False
workRoot = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:h:i:m:p:r:sw:")
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

    if opt == "-p":
	project = arg

    if opt == "-r":
	revision = arg

    if opt == "-s":
	skipBinaries = True

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
    buildenv = hardhatlib.defaults
    buildenv['hardhatroot'] = whereAmI
    buildenv['workroot'] = workRoot
    buildenv['logfile'] = os.path.join(workRoot, "nightly.log")
    buildenv['root'] = os.path.join(workRoot, project)
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
    
hardhatlib.log_rotate(buildenv)



try:
    buildenv['releaseId'] = releaseId
    buildenv['cvsModule'] = cvsModule
    buildenv['module'] = module
    buildenv['revision'] = revision
    buildenv['skipBinaries'] = skipBinaries
    hardhatlib.buildComplete(buildenv)

except hardhatlib.HardHatExternalCommandError:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print " A program that HardHat spawned exited with a non-zero exit code."
    print "          Please view the file 'hardhat.log' for details."
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
    print "HardHat Log:"
    hardhatlib.log_dump(buildenv)
