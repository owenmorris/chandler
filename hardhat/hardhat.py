#!/usr/bin/env python
__version__     = "$Revision$"
__date__        = "$Date$"
__copyright__   = "Copyright (c) 2003 Open Source Applications Foundation"
__license__     = "GPL -- see LICENSE.txt"

"""
HardHat:  OSAF Build Environment

Command-line frontend to hardhatlib.py (see description there)

"""
import os, sys, traceback, getopt, string

# Initialize hardhatlib
import hardhatlib

# Here is a trick to figure out what directory hardhat lives in, even if
# we were called found by the user's PATH
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))

def usage():
    print "python hardhat.py [OPTION]..."
    print "Hardhat builds an application and its dependencies."
    print ""
    print "-a          remove runtime directory for MODULE"
    print "-b          build module MODULE"
    print "-B          build MODULE and its dependencies"
    print "-c          clean module MODULE"
    print "-C          clean MODULE and its dependencies"
    print "-d          use debug version"
    print "-D VERSION  create a distribution, using VERSION as the version string"
    # print "-e          show environment variables in hardhat.log (on by default)"
    print "-h          display this help"
    # print "-i          inspect system (not implemented)"
    print "-n          non-interactive (won't prompt during scrubbing)"
    print "-r          use release version (this is the default)"
    # print "-s          spawn an interactive shell"
    print "-s          scrub MODULE (remove all local files not in CVS)"
    print "-S          scrub MODULE and its dependencies"
    print "-t          test module MODULE"
    # print "-v          verbose"
    print "-x          execute MODULE"

# Earlier versions of Python don't define these, so let's include them here:
True = 1
False = 0

# look in current directory for a __hardhat__.py file
if os.path.isfile("__hardhat__.py"):
    curmodule = hardhatlib.module_from_file(None, "__hardhat__.py", "curmodule")
    if not curmodule.info.has_key('root'):
        print "no value for 'root' in __hardhat__.py; please add one"
        sys.exit(1)
    projectRoot = os.path.abspath(curmodule.info['root'])
    if curmodule.info.has_key('path'):
        curmodulepath = curmodule.info['path']
    else:
        # determine our path relative to project root:
        curdir = os.path.abspath(".")
        relpath = curdir[len(projectRoot)+1:]
        curmodulepath = relpath

    print "Project path: ", projectRoot
    print "Module path:  ", os.path.join(projectRoot, curmodulepath)
    print "Module name:  ", curmodule.info['name']
    print "HardHat log:  ", os.path.join(projectRoot, "hardhat.log")
    print
else:
    print "No __hardhat__.py in current directory"
    sys.exit(1)

if string.find(projectRoot, ' ') >= 0:
    print "ERROR: Path to project ("+projectRoot+") cannot contain a space.  Exiting."
    sys.exit(1)


try:
    opts, args = getopt.getopt(sys.argv[1:], "abBcCdD:ehinrsStvx")
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


try:
    buildenv = hardhatlib.defaults
    buildenv['root'] = projectRoot
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

hardhatlib.log_rotate(buildenv)



try:
    for opt, arg in opts:
        if opt == "-a":
            hardhatlib.removeRuntimeDir(buildenv, curmodulepath)

        if opt == "-b":
            hardhatlib.build(buildenv, curmodulepath)

        if opt == "-B":
            history = {}
            hardhatlib.buildDependencies(buildenv, curmodulepath, history)

        if opt == "-c":
            if hardhatlib.clean(buildenv, curmodulepath) == hardhatlib.HARDHAT_ERROR:
                print "Error, exiting"

        if opt == "-C":
            history = {}
            if hardhatlib.cleanDependencies(buildenv, curmodulepath, history) == \
             hardhatlib.HARDHAT_ERROR:
                print "Error, exiting"

        if opt == "-d":
            buildenv['version'] = 'debug'

        if opt == "-D":
            buildVersionArg = arg
            # on Windows, args with spaces in them get split in two, so
            # there's a chance this arg will have it's spaces encoded into
            # pipe characters -- replace them with spaces again:
            buildVersionArg = buildVersionArg.replace("|", " ")
            hardhatlib.distribute(buildenv, curmodulepath, buildVersionArg)

        if opt == "-e":
            buildenv['showenv'] = 1

        if opt == "-h":
            usage()

        if opt == "-n":
            buildenv['interactive'] = False

        if opt == "-r":
            buildenv['version'] = 'release'

        if opt == "-s":
            hardhatlib.scrub(buildenv, curmodulepath)

        if opt == "-S":
            hardhatlib.scrubDependencies(buildenv, curmodulepath)

        if opt == "-t":
            hardhatlib.test(buildenv, curmodulepath)

        if opt == "-v":
            buildenv['verbosity'] = buildenv['verbosity'] + 1

        if opt == "-x":
            hardhatlib.run(buildenv, curmodulepath)

    if len(args) > 0:
        hardhatlib.executeScript(buildenv, args)

except hardhatlib.HardHatExternalCommandError:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print " A program that HardHat spawned exited with a non-zero exit code."
    print "          Please view the file 'hardhat.log' for details."
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    sys.exit(1)

except hardhatlib.HardHatMissingFileError, e:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print "HardHat cannot find one its __hardhat__.py files..."
    print e 
    print "Please make sure the above file exists and try again."
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    sys.exit(1)

except Exception, e:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print "Error in HardHat:", e
    print ""
    print "Displaying traceback:"
    print ""
    traceback.print_exc()
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    sys.exit(1)
