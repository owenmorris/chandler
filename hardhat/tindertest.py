#!/usr/bin/env python

# tinderbox build client script for continuously building a project and
# reporting to a tinderbox server
#
#  tindertest is used instead of tinderbuild to prevent uploading build
#  results when just running tests
#
# To appease older Pythons:
True = 1
False = 0

# must be run from the hardhat directory, which will be updated to the
# appropriate CVS vintage by this script, so it's a good idea to first
# bring the hardhat directory (or at least this file) up to the latest
# vintage with a "cvs update -A" before running it, since after running
# it, it may get reverted to a slightly earlier version

import hardhatutil, time, smtplib, os, sys, md5, sha
from optparse import OptionParser

whereAmI = os.path.dirname(os.path.abspath(hardhatutil.__file__))
hardhatFile = os.path.join(whereAmI, "hardhat.py")

homeDir = os.environ['HOME']
buildDir = os.path.join(homeDir, "tinderbuild")
logFile = os.path.join(buildDir, "build.log")
stopFile = os.path.join(buildDir, "stop")
fromAddr = "builds"
mailtoAddr = "buildreport"
alertAddr = "buildman"
adminAddr = "builds"
defaultDomain = "@osafoundation.org"

def main():
    global buildscriptFile, fromAddr, mailtoAddr, alertAddr, adminAddr, defaultDomain
    
    parser = OptionParser(usage="%prog [options] buildName", version="%prog 1.2")
    parser.add_option("-t", "--toAddr", action="store", type="string", dest="toAddr",
      default=mailtoAddr, help="Where to mail script reports\n"
      " [default] " + mailtoAddr + defaultDomain)
    parser.add_option("-p", "--project", action="store", type="string", dest="project",
      default="newchandler", help="Name of script to use (without .py extension)\n"
      "[default] newchandler")
    parser.add_option("-o", "--output", action="store", type="string", dest="outputDir",
      default=os.path.join(os.environ['HOME'],"output"), help="Name of temp output directory\n"
      " [default] ~/output")
    parser.add_option("-a", "--alert", action="store", type="string", dest="alertAddr",
      default=alertAddr, help="E-mail to notify on build errors \n"
      " [default] " + alertAddr + defaultDomain)

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        parser.error("You must at least provide a name for your build")

    buildName = args[0]
    fromAddr += defaultDomain
    mailtoAddr = options.toAddr
    alertAddr = options.alertAddr
    if mailtoAddr.find('@') == -1:
        mailtoAddr += defaultDomain
    if alertAddr.find('@') == -1:
        alertAddr += defaultDomain

    prevStartInt = 0
    curDir = os.path.abspath(os.getcwd())
    buildscriptFile = os.path.join("buildscripts", options.project + ".py")

    outputDir = os.path.abspath(options.outputDir)
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)

    if not os.path.exists(buildDir):
        os.mkdir(buildDir)

    path = os.environ.get('PATH', os.environ.get('path'))
    cvsProgram = hardhatutil.findInPath(path, "cvs")
    print "cvs =", cvsProgram
    rsyncProgram = hardhatutil.findInPath(path, "rsync")
    print "rsync =", rsyncProgram

    clobber = go = 1

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

            SendMail(fromAddr, mailtoAddr, startTime, buildName, "building", 
             treeName, None)

            ret = mod.Start(hardhatFile, buildDir, "-D'"+ nowString + "'", 
             buildVersion, clobber, log)

        except TinderbuildError, e:
            print e
            print "Tinderbuild:  Build failed"
            log.write("Tinderbuild:  Build failed\n")
            status = "build_failed"
            log.close()
    
            log = open(logFile, "r")
            logContents = log.read()
            log.close()
            SendMail(fromAddr, alertAddr, startTime, buildName, "The build failed", 
             treeName, logContents)
            log = open(logFile, "w")

        except Exception, e:
            print e
            print "Build failed"
            log.write("Build failed\n")
            status = "build_failed"
            log.close()
    
            log = open(logFile, "r")
            logContents = log.read()
            log.close()
            SendMail(fromAddr, alertAddr, startTime, buildName, "The build failed", 
             treeName, logContents)
            log = open(logFile, "w")

        else:
            if ret == "success-nochanges":
                print "There were no changes, and the tests were successful"
                log.write("There were no changes, and the tests were successful\n")
                status = "success"
            elif ret == "success-changes":
                print "There were changes, and the tests were successful"
                log.write("There were changes, and the tests were successful\n")
                status = "success"

                newDir = os.path.join(outputDir, buildVersion)
                print "Renaming " + os.path.join(buildDir, "output", buildVersion) + " to " + newDir 
                log.write("Renaming " + os.path.join(buildDir, "output", buildVersion) + " to " + newDir + "\n")
                os.rename(os.path.join(buildDir, "output", buildVersion), newDir)
                if os.path.exists(outputDir+os.sep+"index.html"):
                    os.remove(outputDir+os.sep+"index.html")
                if os.path.exists(outputDir+os.sep+"time.js"):
                    os.remove(outputDir+os.sep+"time.js")
                print "Calling RotateDirectories"
                log.write("Calling RotateDirectories\n")
                RotateDirectories(outputDir)
                print "Calling CreateIndex with " + newDir
                log.write("Calling CreateIndex with " + newDir + "\n")
                CreateIndex(outputDir, buildVersion, nowString, buildName)

                buildNameNoSpaces = buildName.replace(" ", "")
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
                log.close()
        
                log = open(logFile, "r")
                logContents = log.read()
                log.close()
                SendMail(fromAddr, alertAddr, startTime, buildName, "The build failed", 
                 treeName, logContents)
                log = open(logFile, "w")

            
            elif ret == "test_failed":
                print "Unit tests failed"
                log.write("Unit tests failed\n")
                status = "test_failed"
                log.close()
        
                log = open(logFile, "r")
                logContents = log.read()
                log.close()
                SendMail(fromAddr, alertAddr, startTime, buildName, "Unit tests failed", 
                 treeName, logContents)
                log = open(logFile, "w")
            
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

        SendMail(fromAddr, mailtoAddr, startTime, buildName, status, treeName, 
         logContents)

        clobber = 0

        if os.path.exists(stopFile):
            go = 0

def SendMail(fromAddr, toAddr, startTime, buildName, status, treeName, logContents):
    nowTime  = str(int(time.time()))
    msg  = ("From: %s\r\nTo: %s\r\n\r\n" % (fromAddr, toAddr))
    msg += "Subject: " + status + " from " + buildName + "\n"
    msg += "tinderbox: tree: " + treeName + "\n"
    msg += "tinderbox: buildname: " + buildName + "\n"
    msg += "tinderbox: starttime: " + startTime + "\n"
    msg += "tinderbox: timenow: " + nowTime + "\n"
    msg += "tinderbox: errorparser: unix\n"
    msg += "tinderbox: status: " + status + "\n"
    msg += "tinderbox: administrator: " + adminAddr + defaultDomain + "\n"
    msg += "tinderbox: END\n"
    if logContents:
        msg += logContents

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
    for anyDir in dirs:
        if not os.path.isdir(os.path.join(dir, anyDir)):
            dirs.remove(anyDir)

    dirs.sort()
    for subdir in dirs[:-3]:
        subdir = os.path.join(dir, subdir)
        if os.path.isdir(subdir):
            hardhatutil.rmdirRecursive(subdir)

    # hack to delete archives still being created by __hardhat__.py
    list2 = os.listdir(buildDir)
    for fileName in list2:
        fileName = os.path.join(buildDir, fileName)
        if os.path.isdir(fileName):
            continue
        elif fileName.find('Chandler_') != -1:
            os.remove(fileName)

_descriptions = {
    'enduser' : ["End-Users' distribution", "If you just want to use Chandler, this distribution contains everything you need -- just download, unpack, run."],
    'developer' : ["Developers' distribution", "If you're a developer and want to run Chandler in debugging mode, this distribution contains debug versions of the binaries.  Assertions are active, the __debug__ global is set to True, and memory leaks are listed upon exit.  You can also use this distribution to develop your own parcels (See <a href=http://wiki.osafoundation.org/bin/view/Main/ParcelLoading>Parcel Loading</a> for details on loading your own parcels)."],
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
    for x in ["enduser", "developer"]:
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
