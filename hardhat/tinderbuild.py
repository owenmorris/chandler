#!/usr/bin/env python

# tinderbox build client script for continuously building a project and
# reporting to a tinderbox server

# To appease older Pythons:
True = 1
False = 0

# must be run from the hardhat directory, which will be updated to the
# appropriate CVS vintage by this script, so it's a good idea to first
# bring the hardhat directory (or at least this file) up to the latest
# vintage with a "cvs update -A" before running it, since after running
# it, it may get reverted to a slightly earlier version

import hardhatutil, time, smtplib, os, sys, md5, sha

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
        os.mkdir(outputDir)

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

        if ((startInt - (5 * 60)) < prevStartInt):
            print "Sleeping 5 minutes (" + buildName + ")"
            time.sleep(5 * 60)
            # re-fetch start time now that we've slept
            startInt = int(time.time())

        startTime = str(startInt)
        prevStartInt = startInt

        nowString = time.strftime("%Y-%m-%d %H:%M:%S")
        buildVersion = hardhatutil.RemovePunctuation(nowString)
        print "Starting:", nowString, buildVersion

        log = open(logFile, "w")
        log.write("Start: " + nowString + "\n")

        try:

            try:
                # bring this hardhat directory up to date
                outputList = hardhatutil.executeCommandReturnOutputRetry(
                 [cvsProgram, "update", "-D'"+ nowString + "'"])
            except:
                hardhatutil.dumpOutputList(outputList, log)
                raise TinderbuildError, "Error updating HardHat"

            # load (or reload) the buildscript file for the project
            mod = hardhatutil.ModuleFromFile(buildscriptFile, "buildscript")

            treeName = mod.treeName

            SendMail(fromAddr, toAddr, startTime, buildName, "building", 
             treeName, None)

            ret = mod.Start(hardhatFile, buildDir, "-D'"+ nowString + "'", 
             buildVersion, 0, log)

        except TinderbuildError, e:
            print e
            print "Tinderbuild:  Build failed"
            log.write("Tinderbuild:  Build failed\n")
            status = "build_failed"

        except Exception, e:
            print e
            print "Build failed"
            log.write("Build failed\n")
            status = "build_failed"

        else:
            if ret == "success":
                print "There were changes, and the build was successful"
                log.write("There were changes, and the build was successful\n")
                status = "success"
                newDir = os.path.join(outputDir, buildVersion)
                os.rename(os.path.join(buildDir, "output"), newDir)
                log.write("Calling CreateIndex with " + newDir + "\n")
                if os.path.exists(outputDir+os.sep+"index.html"):
                    os.remove(outputDir+os.sep+"index.html")
                if os.path.exists(outputDir+os.sep+"time.js"):
                    os.remove(outputDir+os.sep+"time.js")
                for x in ["enduser", "developer", "release", "debug"]:
                    if os.path.exists(outputDir+os.sep+x+".html"):
                        os.remove(outputDir+os.sep+x+".html")
                RotateDirectories(outputDir)
                CreateIndex(outputDir, buildVersion, nowString, buildName)

                buildNameNoSpaces = buildName.replace(" ", "")
    # rsync -e ssh -avzp --delete /home/builder/output/ 192.168.101.46:continuous/kilauea-osx
                print "Rsyncing..."
                outputList = hardhatutil.executeCommandReturnOutputRetry(
                 [rsyncProgram, "-e", "ssh", "-avzp", "--delete",
                 outputDir + os.sep, 
                 "192.168.101.46:continuous/" + buildNameNoSpaces])
                hardhatutil.dumpOutputList(outputList, log)

            elif ret == "build_failed":
                print "The build failed"
                log.write("The build failed\n")
                status = "build_failed"
            
            elif ret == "test_failed":
                print "Unit tests failed"
                log.write("Unit tests failed\n")
                status = "test_failed"
            
            else:
                print "There were no changes"
                log.write("There were no changes in CVS\n")
                status = "not_running"

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

    try:
        server = smtplib.SMTP('mail.osafoundation.org')
        server.sendmail(fromAddr, toAddr, msg)
        server.quit()
    except Exception, e:
        print "SendMail error", e

def RotateDirectories(dir):
    """Removes all but the 3 newest subdirectories from the given directory;
    assumes the directories are named with timestamps (numbers) because it 
    uses normal sorting to determine the order."""

    dirs = os.listdir(dir)
    dirs.sort()
    for subdir in dirs[:-3]:
        hardhatutil.rmdirRecursive(os.path.join(dir, subdir))

_descriptions = {
    'enduser' : ["End-Users' distribution", "If you just want to use Chandler, this distribution contains everything you need -- just download, unpack, run."],
    'developer' : ["Developers' distribution", "If you're a developer and want to run Chandler in debugging mode, this distribution contains debug versions of the binaries.  Assertions are active, the __debug__ global is set to True, and memory leaks are listed upon exit.  You can also use this distribution to develop your own parcels (See <a href=http://wiki.osafoundation.org/bin/view/Main/ParcelLoading>Parcel Loading</a> for details on loading your own parcels)."],
    'release' : ["Pre-built release directory", "If you are using CVS to check out Chandler you can either build everything yourself or you can download this pre-compiled 'release' directory.  Download, unpack, and place the contained 'release' directory next to your 'Chandler' directory."],
    'debug' : ["Pre-built debug directory", "If you are using CVS to check out Chandler you can either build everything yourself or you can download this pre-compiled 'debug' directory.  Download, unpack, and place the contained 'debug' directory next to your 'Chandler' directory."],
}

def MD5sum(filename):
    """Compute MD5 checksum for the file
    """
    m = md5.new()
    fileobj = open(filename)
    filedata = fileobj.read()
    fileobj.close()
    m.update(filedata)
    return m.hexdigest()

def SHAsum(filename):
    """Compute SHA-1 checksum for the file
    """
    s = sha.new()
    fileobj = open(filename)
    filedata = fileobj.read()
    fileobj.close()
    s.update(filedata)
    return s.hexdigest()

def CreateIndex(outputDir, newDirName, nowString, buildName):
    """Generates an index.html page from the hint files that hardhat creates
    which contain the actual distro filenames"""
    fileOut = file(outputDir+os.sep+"index.html", "w")
    fileOut.write("<html><head><META HTTP-EQUIV=Pragma CONTENT=no-cache><link rel=Stylesheet href=http://www.osafoundation.org/css/OSAF.css type=text/css charset=iso-8859-1></head><body topmargin=0 leftmargin=0 marginwith=0 marginheight=0><img src=http://www.osafoundation.org/images/OSAFLogo.gif><table border=0><tr><td width=19>&nbsp;</td><td width=550>\n")
    fileOut.write("<h2>Chandler Build: " + nowString + " PDT (machine: " + buildName +")</h2>\n")
    for x in ["enduser", "developer", "release", "debug"]:
        actual = _readFile(outputDir+os.sep+newDirName+os.sep+x)
        fileOut.write("<p><a href="+x+".html> "+ _descriptions[x][0] +"</a>: " + _descriptions[x][1] +"</p>\n")
        fileOut2 = file(outputDir+os.sep+x+".html", "w")
        fileOut2.write("<html><head><META HTTP-EQUIV=Pragma CONTENT=no-cache><link rel=Stylesheet href=http://www.osafoundation.org/css/OSAF.css type=text/css charset=iso-8859-1></head><body topmargin=0 leftmargin=0 marginwith=0 marginheight=0><img src=http://www.osafoundation.org/images/OSAFLogo.gif><table border=0><tr><td width=19>&nbsp;</td><td width=550>\n")
        fileOut2.write("<h2>Chandler Build: " + nowString + " PDT (machine: " + buildName +")</h2>\n")
        fileOut2.write("<p>Download <a href="+newDirName+"/"+actual+"> "+ _descriptions[x][0] +"</a>: <br>")
        fileOut2.write(" MD5 checksum: " + MD5sum(outputDir+os.sep+newDirName+os.sep+actual) + "<br>")
        fileOut2.write(" SHA checksum: " + SHAsum(outputDir+os.sep+newDirName+os.sep+actual) + "<br>")
        fileOut2.write("<p> " + _descriptions[x][1] +"</p>\n")
        fileOut2.write("</td></tr></table></body></html>\n")
        fileOut2.close()

    fileOut.write("</td></tr></table></body></html>\n")
    fileOut.close()
    fileOut = file(outputDir+os.sep+"time.js", "w")
    fileOut.write("document.write('" + nowString + "');\n")
    fileOut.close()

def _readFile(path):
    fileIn = open(path, "r")
    line = fileIn.readline()
    fileIn.close()
    return line.strip()


class TinderbuildError(Exception):
    def __init__(self, args=None):
        self.args = args

main()
