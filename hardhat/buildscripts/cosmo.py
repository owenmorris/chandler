"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

import os, sys, re
import hardhatutil, hardhatlib

path       = os.environ.get('PATH', os.environ.get('path'))
whereAmI   = os.path.dirname(os.path.abspath(hardhatlib.__file__))
svnProgram = hardhatutil.findInPath(path, "svn")
antProgram = hardhatutil.findInPath(path, "maven")
logPath    = 'hardhat.log'
separator  = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"

treeName     = "Cosmo"
sleepMinutes = 30

reposRoot    = 'http://svn.osafoundation.org/server'
reposModules = [('jsp',    'commons/trunk/jsp'), 
                ('spring', 'commons/trunk/spring'), 
                ('struts', 'commons/trunk/struts'),
                ('cosmo',  'cosmo/trunk',),
               ]
reposBuild   = [('jsp',    'jar:install'),  # install step done here so cosmo build 
                ('spring', 'jar:install'),  # always built against latest
                ('struts', 'jar:install'),
                ('cosmo',  '-Dmaven.test.skip=true clean test:dbsetup build'),
               ]
reposTest    = [('cosmo',  'test:dbsetup test'),
               ]
reposDist    = [('cosmo',  'dist:release', 'dist',   'cosmo*.tar.gz'),
               ]

def Start(hardhatScript, workingDir, buildVersion, clobber, log, skipTests=False, upload=False):

      # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)

    os.chdir(workingDir)

      # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")

    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)

    os.mkdir(outputDir)

    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    sourceChanged = False
            
    log.write("[tbox] Pulling source tree\n")
                                 
    for (module, moduleSource) in reposModules:
        moduleDir = os.path.join(workingDir, module)

        if os.path.exists(moduleDir):
            log.write("[tbox] Checking for source updates\n")
            print "updating %s" % module
            
            os.chdir(moduleDir)

            outputList = hardhatutil.executeCommandReturnOutputRetry([svnProgram, "up"])

            hardhatutil.dumpOutputList(outputList, log) 

            if NeedsUpdate(outputList):
                sourceChanged = True
                log.write("[tbox] %s modified\n" % module)
            else:
                log.write("[tbox] %s unchanged\n" % module)

        else:    
            svnSource = os.path.join(reposRoot, moduleSource)
    
            log.write("[tbox] Retrieving source tree [%s]\n" % svnSource)
            print "pulling %s" % module
                     
            os.chdir(workingDir)
            
            outputList = hardhatutil.executeCommandReturnOutputRetry([svnProgram, "-q", "co", svnSource, module])

            hardhatutil.dumpOutputList(outputList, log) 

            sourceChanged = True

    os.chdir(workingDir)
                      
    doBuild(workingDir, log)
    
    if skipTests:
        ret = 'success'
    else:
        ret = doTests(workingDir, log)

    if sourceChanged:
        doDistribution(workingDir, log, outputDir, buildVersion, buildVersionEscaped)

        changes = "-changes"
    else:
        changes = "-nochanges"

    print ret + changes

    return ret + changes 


def doBuild(workingDir, log):
    log.write("[tbox] Building\n")

    for (module, target) in reposBuild:
        moduleDir = os.path.join(workingDir, module)

        print "Building [%s]" % module

        try:
            os.chdir(moduleDir)

            outputList = hardhatutil.executeCommandReturnOutput([antProgram, target])

            hardhatutil.dumpOutputList(outputList, log)
        
        except:
            log.write("[tbox] Build failed for [%s]\n" % module)

def doTests(workingDir, log):
    log.write("[tbox] Running unit tests\n")

    for (module, target) in reposTest:
        moduleDir = os.path.join(workingDir, module)

        print "Testing [%s]" % module

        try:
            os.chdir(moduleDir)

            outputList = hardhatutil.executeCommandReturnOutput([antProgram, target])

            hardhatutil.dumpOutputList(outputList, log)

        except Exception, e:
            doCopyLog("***Error during tests***", workingDir, logPath, log)
            return "test_failed"
        else:
            doCopyLog("Tests successful", workingDir, logPath, log)

    return "success"

def doDistribution(workingDir, log, outputDir, buildVersion, buildVersionEscaped):
    log.write(separator)
    log.write("[tbox] Creating distribution files\n")

    for (module, target, distSource, fileGlob) in reposDist:
        moduleDir = os.path.join(workingDir, module)

        print "Distribution [%s]" % module

        try:
            os.chdir(moduleDir)

            outputList = hardhatutil.executeCommandReturnOutput([antProgram, target])

            hardhatutil.dumpOutputList(outputList, log)

            sourceDir = os.path.join(moduleDir, distSource)
            targetDir = os.path.join(outputDir, buildVersion)

            if not os.path.exists(targetDir):
                os.mkdir(targetDir)

            print sourceDir, targetDir

            log.write("[tbox] Moving %s to %s\n" % (sourceDir, targetDir))

            hardhatlib.copyFiles(sourceDir, targetDir, fileGlob)

        except Exception, e:
            doCopyLog("***Error during distribution building process*** ", workingDir, logPath, log)
            raise e

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


def doCopyLog(msg, workingDir, logPath, log):
    log.write(msg + "\n")
    log.write(separator)
    logPath = os.path.join(workingDir, logPath)
    log.write("Contents of " + logPath + ":\n")
    if os.path.exists(logPath):
        CopyLog(logPath, log)
    else:
        log.write(logPath + ' does not exist!\n')
    log.write(separator)
    

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

