"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

import os, hardhatutil, hardhatlib, sys, re

path       = os.environ.get('PATH', os.environ.get('path'))
whereAmI   = os.path.dirname(os.path.abspath(hardhatlib.__file__))
svnProgram = hardhatutil.findInPath(path, "svn")

treeName  = "Chandler"
logPath   = 'hardhat.log'
separator = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"

reposRoot    = 'http://svn.osafoundation.org/chandler'
reposBase    = 'trunk'
reposModules = ['external', 'internal', 'chandler']
releaseModes = ('debug', 'release')

def Start(hardhatScript, workingDir, buildVersion, clobber, log, skipTests=False, upload=False):

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
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
      # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)
    chanDir    = os.path.join(workingDir, 'chandler')
    
      # test if we've been through the loop at least once
    if clobber:
        for module in reposModules:
            modDir = os.path.join(workingDir, module)
            if os.path.exists(modDir):
                hardhatutil.rmdirRecursive(modDir)
            
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

        svnChanges = {}
        clean      = ''

        for module in reposModules:
            svnSource = os.path.join(reposRoot, reposBase, module)
    
            log.write("[tbox] Retrieving source tree [%s]\n" % svnSource)
                     
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [svnProgram, "-q", "co", svnSource, module])

            hardhatutil.dumpOutputList(outputList, log) 

            svnChanges[module] = True

        for releaseMode in releaseModes:
            doBuild(releaseMode, workingDir, log, svnChanges, clean)
            
            if upload:
                doUploadToStaging(releaseMode, workingDir, log)

            clean = 'clean'

        for releaseMode in releaseModes:
            doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped, hardhatScript)

        if skipTests:
            ret = 'success'
        else:
            for releaseMode in releaseModes:
                ret = doTests(hardhatScript, releaseMode, workingDir,
                              outputDir, buildVersion, log)
                if ret != 'success':
                    break

        changes = "-first-run"
    else:
        print "Checking SVN for updates"
        log.write("Checking SVN for updates\n")

        svnChanges = changesInSVN(workingDir, log)
        if svnChanges['external'] or svnChanges['internal']:
            log.write("Changes in SVN require build\n")
            changes = "-changes"
            clean = 'realclean'
            for releaseMode in releaseModes:        
                doBuild(releaseMode, workingDir, log, svnChanges, clean)
                
                if upload:
                    doUploadToStaging(releaseMode, workingDir, buildVersion, log)

                clean = 'clean'
            
        if svnChanges['external'] or svnChanges['internal'] or svnChanges['chandler']:
            log.write("Changes in SVN require making distributions\n")
            changes = "-changes"            
            for releaseMode in releaseModes:        
                doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped, hardhatScript)
                    
        else:
            log.write("No changes\n")
            changes = "-nochanges"

        # do tests
        if skipTests:
            ret = 'success'
        else:
            for releaseMode in releaseModes:   
                ret = doTests(hardhatScript, releaseMode, workingDir,
                              outputDir, buildVersion, log)
                if ret != 'success':
                    break

    os.chdir(workingDir + '/external')

    return ret + changes 

def doTests(hardhatScript, mode, workingDir, outputDir, buildVersion, log):

    testDir = os.path.join(workingDir, "chandler")
    os.chdir(testDir)

    if mode == "debug":
        dashT = '-dvt'
    else:
        dashT = '-vrt'
    
    try: # test
        print "Testing " + mode
        log.write(separator)
        log.write("Testing " + mode + " ...\n")
        outputList = hardhatutil.executeCommandReturnOutput([hardhatScript, dashT])
        hardhatutil.dumpOutputList(outputList, log)

    except Exception, e:
        print "a testing error"
        doCopyLog("***Error during tests***", workingDir, logPath, log)
        return "test_failed"
    else:
        doCopyLog("Tests successful", workingDir, logPath, log)

    return "success"  # end of doTests( )


def doDistribution(releaseMode, workingDir, log, outputDir, buildVersion, buildVersionEscaped, hardhatScript):
    #   Create end-user, developer distributions
    chanDir = os.path.join(workingDir, 'chandler')
    os.chdir(chanDir)
    
    print "Making distribution files for " + releaseMode
    log.write(separator)
    log.write("Making distribution files for " + releaseMode + "\n")
    if releaseMode == "debug":
        distOption = "-dD"
    else:
        distOption = "-D"

    try:
        outputList = hardhatutil.executeCommandReturnOutput(
          [hardhatScript, "-o", os.path.join(outputDir, buildVersion), distOption, buildVersionEscaped])
        hardhatutil.dumpOutputList(outputList, log)
    except Exception, e:
        doCopyLog("***Error during distribution building process*** ", workingDir, logPath, log)
        forceBuildNextCycle(log, workingDir)
        raise e


def doCopyLog(msg, workingDir, logPath, log):
    # hardhat scripts should leave harhat.log behind both on success and
    # failure (barring catastrophic failure), so we can copy that into the
    # build log
    log.write(msg + "\n")
    log.write(separator)
    logPath = os.path.join(workingDir, logPath)
    log.write("Contents of " + logPath + ":\n")
    if os.path.exists(logPath):
        CopyLog(logPath, log)
    else:
        log.write(logPath + ' does not exist!\n')
    log.write(separator)


def changesInSVN(workingDir, log):
    changesDict = {}
#     print "Examining SVN"
#     log.write("Examining SVN\n")

    os.chdir(workingDir)
    
    for module in reposModules:
        log.write("[tbox] Checking for updates [%s] [%s]\n" % (workingDir, module))
                                              
        moduleDir = os.path.join(workingDir, module)

        print "[%s] [%s] [%s]" % (workingDir, module, moduleDir)
        os.chdir(moduleDir)

        outputList = hardhatutil.executeCommandReturnOutputRetry([svnProgram, "up"])

        hardhatutil.dumpOutputList(outputList, log) 

        if NeedsUpdate(outputList):
            changesDict[module] = True
            print "" + module + " needs updating"
        else:
            # print "NO, unchanged"
            log.write("Module unchanged" + "\n")

    log.write(separator)
    log.write("Done with SVN\n")
    return changesDict


def doUploadToStaging(buildmode, workingDir, buildVersion, log):
    print "doUploadToStaging..."
    
    if buildmode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""

    buildRoot =  os.path.join(workingDir, 'external')
    print 'Setting BUILD_ROOT=', buildRoot
    log.write('Setting BUILD_ROOT=' + buildRoot + '\n')
    os.putenv('BUILD_ROOT', buildRoot)
    os.chdir(buildRoot)
    uploadDir = os.path.join(buildRoot, buildVersion)
    if not os.path.exists(uploadDir):
        os.mkdir(uploadDir)

    try:
        upload = ' uploadworld UPLOAD=' + uploadDir
        print "Doing make " + dbgStr + upload
        log.write("Doing make " + dbgStr + upload + "\n")

        outputList = hardhatutil.executeCommandReturnOutput( [buildenv['make'], dbgStr, upload])
        hardhatutil.dumpOutputList(outputList, log)

        log.write(separator)

    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "upload error"
        log.write("***Error during upload***\n")
        log.write(separator)
        log.write("Build log:" + "\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        log.write(separator)
        raise e
    except Exception, e:
        print "upload error"
        log.write("***Error during upload***\n")
        log.write(separator)
        log.write(str(e) + "\n")
        log.write("(No build log!)\n")
        log.write(separator)
        raise e


def doBuild(buildmode, workingDir, log, svnChanges, clean='realclean'):
    # We only build external if there were changes in it
    # We build internal if external or internal were changed
    # We never build in chandler, because there is nothing to build
    if buildmode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""

    buildRoot =  os.path.join(workingDir, 'external')
    print 'Setting BUILD_ROOT=', buildRoot
    log.write('Setting BUILD_ROOT=' + buildRoot + '\n')
    os.putenv('BUILD_ROOT', buildRoot)

    try:
        for module in reposModules:
            print module, "..."
            log.write("- - - - " + module + " - - - - - - -\n")

            if module == 'external' and not svnChanges['external']:
                print 'Nothing to be done for module', module
                log.write('Nothing to be done for module ' + module + '\n')
                log.write(separator)
                continue
            if module == 'internal' and not svnChanges['external'] and not svnChanges['internal']:
                print 'Nothing to be done for module', module
                log.write('Nothing to be done for module ' + module + '\n')
                log.write(separator)
                continue
            if module == 'chandler':
                print 'Nothing to be done for module', module
                log.write('Nothing to be done for module ' + module + '\n')
                log.write(separator)
                continue

            moduleDir = os.path.join(workingDir, module)
            print "cd", moduleDir
            log.write("cd " + moduleDir + "\n")
            os.chdir(moduleDir)

            buildCmds = ' all binaries install'
                
            print "Doing make " + dbgStr + " " + clean + buildCmds + "\n"
            log.write("Doing make " + dbgStr + " " + clean + buildCmds + "\n")

            outputList = hardhatutil.executeCommandReturnOutput( [buildenv['make'], dbgStr, clean, buildCmds ])
            hardhatutil.dumpOutputList(outputList, log)

            log.write(separator)
            
    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "build error"
        log.write("***Error during build***\n")
        log.write(separator)
        log.write("Build log:" + "\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        log.write(separator)
        forceBuildNextCycle(log, workingDir)
        raise e
    except Exception, e:
        print "build error"
        log.write("***Error during build***\n")
        log.write(separator)        
        log.write("No build log!\n")
        log.write(separator)
        forceBuildNextCycle(log, workingDir)
        raise e


def forceBuildNextCycle(log, workingDir):
    doRealclean(log, workingDir)
    # We trigger build for next cycle by removing toplevel Makefiles
    # which will be noticed as an 'update' in the beginning of next
    # cycle which will cause doBuild etc. to be called.
    print 'Removing toplevel Makefiles to trigger build next cycle'
    log.write('Removing toplevel makefiles to trigger build next cycle\n')
    for module in svnModules:
        makefile = os.path.join(workingDir, module, 'Makefile')
        if os.path.exists(makefile):
            os.remove(makefile)
    

def doRealclean(log, workingDir):
    try:
        # If make install fails, it will almost certainly fail next time
        # as well - the typical case has been bad binaries packages.
        # So what we do here is try to do realclean which will force
        # the build to get new binaries tarballs next time, and if fixed
        # binaries were uploaded in the meanwhile we'll recover
        # automatically. This will also sort us out of corrupted debug/release.
        for module in reposModules:
            print "Doing make realclean in " + module + "\n"
            log.write("Doing make realclean in " + module + "\n")
            moduleDir = os.path.join(workingDir, module)
            os.chdir(moduleDir)
            outputList = hardhatutil.executeCommandReturnOutput(
             [buildenv['make'], "realclean"])
            hardhatutil.dumpOutputList(outputList, log)
    except:
        print "make realclean failed\n"
        log.write("make realclean failed\n")


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

