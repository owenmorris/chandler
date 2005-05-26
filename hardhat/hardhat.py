#!/usr/bin/env python
__version__     = "$Revision$"
__date__        = "$Date$"
__copyright__   = "Copyright (c) 2003-2005 Open Source Applications Foundation"
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
    print "-b|--build            build module"
    print "-B|--BuildDeps        build module and its dependencies"
    print "-c|--clean            clean module"
    print "-C|--CleanDeps        clean module and its dependencies"
    print "-d|--debug            use debug version"
    print "-D|--Distrib VERSION  create a distribution, using VERSION as the version string"
    print "-e|--env              show environment variables in hardhat.log"
    print "-g|--docs             generate documentation (via Epydoc and XSLT transform)"
    print "-h|--help             display this help"
    print "-i|--interact         interactive python session"
    print "-j|--epydoc FILE(S)   invoke epydoc on arguments"
    print "-l|--lint             lint Python file(s) using PyChecker"
    print "-n|--noprompt         non-interactive (won't prompt during scrubbing)"
    print "-o|--ouput DIR        output directory used when creating a distribution (-D)"
    print "-r|--release          use release version (this is the default)"
    # print "-s          spawn an interactive shell"
    print "-s|--scrub            scrub module (remove all local files not in SVN)"
    print "-S|--ScrubDeps        scrub module and its dependencies"
    print "-t|--test             run all unit tests in this directory and below"
    print "-u|--update           checkout (update) source using SVN"
    print "-v|--verbose          increase output information"
    print "-x|--run              execute module"

# Earlier versions of Python don't define these, so let's include them here:
True = 1
False = 0

def getOptsAndArgs(arglist):
    try:
        return getopt.getopt(arglist, "bBcCdD:eghij:lno:rsStuvx", ['build', 'BuildDeps', 
         'clean', 'CleanDeps', 'debug', 'Distrib=', 'env', 'docs', 'help', 'interact', 'epydoc=',
         'lint', 'noprompt', 'output=', 'release', 'scrub', 'ScrubDeps', 'test', 'update', 'verbose', 'run'])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

opts, args = getOptsAndArgs(sys.argv[1:])

# Look for args that we can process before initializing hardhatlib:
for opt, arg in opts:
    if opt == "-h" or opt == "--help":
        usage()
        sys.exit(0)

# Store our current directory
curdir = os.path.abspath(".")

# Find a __hardhat__.py file:
hardHatFile = hardhatlib.findHardHatFile(".")
if hardHatFile:
    hardHatFileDir = os.path.dirname(hardHatFile)
    curmodule = hardhatlib.module_from_file(None, hardHatFile, "curmodule")
    if not curmodule.info.has_key('root'):
        print "no value for 'root' in __hardhat__.py; please add one"
        sys.exit(1)
    projectRoot = os.path.abspath(os.path.join(hardHatFileDir, 
     curmodule.info['root']))
    if curmodule.info.has_key('path'):
        curmodulepath = curmodule.info['path']
    else:
        # determine our path relative to project root:
        # curdir = os.path.abspath(".")
        # relpath = curdir[len(projectRoot)+1:]
        relpath = hardHatFileDir[len(projectRoot)+1:]
        curmodulepath = relpath

    print "Project path: ", projectRoot
    print "Module path:  ", os.path.abspath(os.path.join(projectRoot, curmodulepath))
    print "Module name:  ", curmodule.info['name']
    print "HardHat log:  ", os.path.join(projectRoot, "hardhat.log")
    print
else:
    print "Whoops, couldn't find a __hardhat__.py file."
    sys.exit(1)

if string.find(projectRoot, ' ') >= 0:
    print "ERROR: Path to project ("+projectRoot+") cannot contain a space.  Exiting."
    sys.exit(1)



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
    args_used = False  # this gets set to True if any of the flags decide to
                       # use the arguments that aren't tied to any flag

    for opt, arg in opts:
        if opt == "-b" or opt == "--build":
            hardhatlib.build(buildenv, curmodulepath)

        if opt == "-B" or opt == "--BuildDeps":
            history = {}
            hardhatlib.buildDependencies(buildenv, curmodulepath, history)

        if opt == "-c" or opt == "--clean":
            if hardhatlib.clean(buildenv, curmodulepath) == hardhatlib.HARDHAT_ERROR:
                print "Error, exiting"

        if opt == "-C" or opt == "--CleanDeps":
            history = {}
            if hardhatlib.cleanDependencies(buildenv, curmodulepath, history) == \
             hardhatlib.HARDHAT_ERROR:
                print "Error, exiting"

        if opt == "-d" or opt == "--debug":
            buildenv['version'] = 'debug'

        if opt == "-D" or opt == "--Distrib":
            buildVersionArg = arg
            # on Windows, args with spaces in them get split in two, so
            # there's a chance this arg will have it's spaces encoded into
            # pipe characters -- replace them with spaces again:
            buildVersionArg = buildVersionArg.replace("|", " ")
            hardhatlib.distribute(buildenv, curmodulepath, buildVersionArg)

        if opt == "-e" or opt == "--env":
            buildenv['showenv'] = 1

        if opt == "-g" or opt == "--docs":
            hardhatlib.generateDocs(buildenv, curmodulepath)

        if opt == "-h" or opt == "--help":
            usage()

        if opt == "-i" or opt == "--interact":
            py = buildenv['python']
            if( buildenv['version'] == 'debug' ):
                py = buildenv['python_d']
            hardhatlib.executeCommandNoCapture(buildenv, "Interactive",
             [py], "Interactive session")

        if opt == "-j" or opt == "--epydoc":
            hardhatlib.epydoc(buildenv, None, None, arg, *args)

        if opt == "-l" or opt == "--lint":
            args_used = True  # we're going to be using the leftover args
            hardhatlib.lint(buildenv, args)

        if opt == "-n" or opt == "--noprompt":
            buildenv['interactive'] = False

        if opt == "-o" or opt == "--output":
            buildenv['outputdir'] = arg

        if opt == "-r" or opt == "--release":
            buildenv['version'] = 'release'

        if opt == "-s" or opt == "--scrub":
            hardhatlib.scrub(buildenv, curmodulepath)

        if opt == "-S" or opt == "--ScrubDeps":
            hardhatlib.scrubDependencies(buildenv, curmodulepath)

        if opt == "-t" or opt == "--test":
            leftOver = hardhatlib.test(buildenv, curdir, *args)
            loo, loa = getOptsAndArgs(leftOver)
            opts.extend(loo)
            args.extend(loa)
            
        #if opt == "-u" or opt == "--update":
        #    hardhatlib.svnCheckout(buildenv, projectRoot)

        if opt == "-v" or opt == "--verbose":
            buildenv['verbosity'] = buildenv['verbosity'] + 1

        if opt == "-x" or opt == "--run":
            hardhatlib.run(buildenv, curmodulepath)

    if len(args) > 0:
        if not args_used:
            # Only do this if no flag above used the leftover arguments
            hardhatlib.executeScript(buildenv, args)

except hardhatlib.HardHatExternalCommandError:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print " A program that HardHat spawned exited with a non-zero exit code."
    print "          Please view the file 'hardhat.log' for details."
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    sys.exit(1)

except hardhatlib.HardHatUnitTestError:
    print 
    print "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    print "                The following unit test(s) failed:"
    print
    for testFile in buildenv['failed_tests']:
        print testFile
    print
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
