#!/usr/bin/env python

# tinderbox build client script for continuously building a project and
# reporting to a tinderbox server

False = 0
True = 1

# must be run from the hardhat directory, which will be updated to the
# appropriate CVS vintage by this script, so it's a good idea to first
# bring the hardhat directory (or at least this file) up to the latest
# vintage with a "cvs update -A" before running it, since after running
# it, it may get reverted to a slightly earlier version

import hardhatutil, time, smtplib, os, sys

# args:  toAddr, buildName, project, outputDir

toAddr    = sys.argv[1]
buildName = sys.argv[2]
project   = sys.argv[3]
outputDir = sys.argv[4]

whereAmI = os.path.dirname(os.path.abspath(hardhatutil.__file__))
hardhatFile = os.path.join(whereAmI, "hardhat.py")

homeDir = os.environ['HOME']
buildDir = os.path.join(homeDir, "tinderbuild")
logFile = os.path.join(buildDir, "build.log")
stopFile = os.path.join(buildDir, "stop")
fromAddr = "builds@osafoundation.org"
buildscriptFile = os.path.join("buildscripts", project + ".py")


def main():

    prevStartInt = 0
    curDir = os.path.abspath(os.getcwd())

    if not os.path.exists(outputDir):
        print "outputDir doesn't exist:", outputDir
        sys.exit(1)

    if not os.path.exists(buildDir):
        os.mkdir(buildDir)

    path = os.environ.get('PATH', os.environ.get('path'))
    cvsProgram = hardhatutil.findInPath(path, "cvs")
    print "cvs =", cvsProgram
    rsyncProgram = hardhatutil.findInPath(path, "rsync")
    print "rsync =", rsyncProgram

    go = 1

    if os.path.exists(stopFile):
        os.remove(stopFile)

    while go:
        os.chdir(curDir)

        startInt = int(time.time())

        if False and ( (startInt - (5 * 60)) < prevStartInt):
            print "Sleeping 5 minutes (" + buildName + ")"
            time.sleep(5 * 60)
            # re-fetch start time now that we've slept
            startInt = int(time.time())

        startTime = str(startInt)
        prevStartInt = startInt

        nowString = time.strftime("%Y-%m-%d %H:%M:%S")
        print nowString
        buildVersion = hardhatutil.RemovePunctuation(nowString)
        print buildVersion



        log = open(logFile, "w")
        try:
            # bring this hardhat directory up to date
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [cvsProgram, "update", "-D'"+ nowString + "'"])

            # load (or reload) the buildscript file for the project
            mod = hardhatutil.ModuleFromFile(buildscriptFile, "buildscript")

            treeName = mod.treeName

            SendMail(fromAddr, toAddr, startTime, buildName, "building", 
             treeName, None)

            log.write("Start = " + nowString + "\n")

            ret = mod.Start(hardhatFile, buildDir, "-D'"+ nowString + "'", 
             buildVersion, 0, log)

        except Exception, e:
            print e
            print "Build failed"
            log.write("Build failed\n")
            status = "build_failed"
        else:
            if ret:
                print "There were changes, and the build was successful"
                log.write("There were changes, and the build was successful\n")
                status = "success"
                newDir = os.path.join(outputDir, buildVersion)
                print "newDir =", newDir
                os.rename(os.path.join(buildDir, "output"), newDir)
                log.write("Calling CreateIndex with " + newDir + "\n")
                if os.path.exists(outputDir+os.sep+"index.html"):
                    os.remove(outputDir+os.sep+"index.html")
                RotateDirectories(outputDir)
                CreateIndex(outputDir, buildVersion)

                buildNameNoSpaces = buildName.replace(" ", "")
    # rsync -e ssh -avzp --delete /home/builder/output/ 192.168.101.46:continuous/kilauea-osx
                print "Rsyncing..."
                outputList = hardhatutil.executeCommandReturnOutputRetry(
                 [rsyncProgram, "-e", "ssh", "-avzp", "--delete",
                 outputDir + os.sep, 
                 "192.168.101.46:continuous/" + buildNameNoSpaces])
            else:
                print "There were no changes"
                log.write("There were no changes in CVS\n")
                status = "success"

        log.write( "End = " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")

        log.close()

        log = open(logFile, "r")
        logContents = log.read()
        log.close()
        nowTime = str(int(time.time()))

        SendMail(fromAddr, toAddr, startTime, buildName, status, treeName, 
         logContents)

        if os.path.exists(stopFile):
            go = 0

def SendMail(fromAddr, toAddr, startTime, buildName, status, treeName, logContents):
    nowTime  = str(int(time.time()))
    msg      = ("From: %s\r\nTo: %s\r\n\r\n" % (fromAddr, toAddr))
    msg      = msg + "tinderbox: tree: " + treeName + "\n"
    msg      = msg + "tinderbox: buildname: " + buildName + "\n"
    msg      = msg + "tinderbox: starttime: " + startTime + "\n"
    msg      = msg + "tinderbox: timenow: " + nowTime + "\n"
    msg      = msg + "tinderbox: errorparser: unix\n"
    msg      = msg + "tinderbox: status: " + status + "\n"
    msg      = msg + "tinderbox: administrator: builds@osafoundation.org\n"
    msg      = msg + "tinderbox: END\n"
    if logContents:
        msg  = msg + logContents

    server = smtplib.SMTP('mail.osafoundation.org')
    server.sendmail(fromAddr, toAddr, msg)
    server.quit()

def RotateDirectories(dir):
    """Removes all but the 3 newest subdirectories from the given directory;
    assumes the directories are named with timestamps (numbers) because it 
    uses normal sorting to determine the order."""

    dirs = os.listdir(dir)
    dirs.sort()
    for subdir in dirs[:-3]:
        hardhatutil.rmdirRecursive(os.path.join(dir, subdir))

def CreateIndex(outputDir, newDirName):
    """Generates an index.html page from the hint files that hardhat creates
    which contain the actual distro filenames"""
    fileOut = file(outputDir+os.sep+"index.html", "w")
    for x in ["enduser", "developer", "release", "debug"]:
        actual = _readFile(outputDir+os.sep+newDirName+os.sep+x)
        fileOut.write("<p><a href="+newDirName+"/"+actual+">"+x+"</a></p>\n")
    fileOut.close()

def _readFile(path):
    fileIn = open(path, "r")
    line = fileIn.readline()
    fileIn.close()
    return line.strip()



main()
