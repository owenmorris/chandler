# tinderbox build client script for continuously building a project and
# reporting to a tinderbox server

# must be run from the hardhat directory, which will be updated to the
# appropriate CVS vintage by this script, so it's a good idea to first
# bring the hardhat directory (or at least this file) up to the latest
# vintage with a "cvs update -A" before running it, since after running
# it, it may get reverted to a slightly earlier version

import hardhatutil, time, smtplib, os, sys

# args:  toAddr, buildName, project

toAddr    = sys.argv[1]
buildName = sys.argv[2]
project   = sys.argv[3]

whereAmI = os.path.dirname(os.path.abspath(hardhatutil.__file__))
hardhatFile = os.path.join(whereAmI, "hardhat.py")

homeDir = os.environ['HOME']
buildDir = os.path.join(homeDir, "tinderbuild")
logFile = os.path.join(buildDir, "build.log")
stopFile = os.path.join(buildDir, "stop")
fromAddr = "builds@osafoundation.org"
blueprintFile = os.path.join("blueprints", project + ".py")


def main():

    prevStartInt = 0
    curDir = os.path.abspath(os.getcwd())

    if not os.path.exists(buildDir):
        os.mkdir(buildDir)

    path = os.environ.get('PATH', os.environ.get('path'))
    cvsProgram = hardhatutil.findInPath(path, "cvs")
    print "CVS =", cvsProgram

    go = 1

    if os.path.exists(stopFile):
        os.remove(stopFile)

    while go:
        os.chdir(curDir)

        startInt = int(time.time())
        startTime = str(startInt)

        if( (startInt - 60) < prevStartInt):
            print "Sleeping 60 seconds"
            time.sleep(60)

        prevStartInt = startInt

        nowString = time.strftime("%Y-%m-%d %H:%M:%S")
        print nowString
        buildId = nowString.replace("-", "")
        buildId = buildId.replace(" ", "")
        buildId = buildId.replace(":", "")
        print buildId



        log = open(logFile, "w+")
        try:
            # bring this hardhat directory up to date
            outputList = hardhatutil.executeCommandReturnOutput(
             [cvsProgram, "update", "-D '"+ nowString + "'"])

            # load (or reload) the blueprint file for the project
            mod = hardhatutil.ModuleFromFile(blueprintFile, "blueprint")

            treeName = mod.treeName

            SendMail(fromAddr, toAddr, startTime, buildName, "building", 
             treeName, None)

            mod.Start(hardhatFile, buildDir, "-D '"+ nowString + "'", 
             buildId, 0, log)

        except Exception, e:
            print e
            print "something failed"
            log.write("something failed")
            status = "build_failed"
        else:
            print "all is well"
            log.write("all is well")
            status = "success"
        log.close()

        log = open(logFile, "r")
        logContents = log.read()
        log.close()
        nowTime = str(int(time.time()))

        SendMail(fromAddr, toAddr, startTime, buildName, status, treeName, 
         logContents)

        time.sleep(30)

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

main()
