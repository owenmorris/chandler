#!/usr/bin/env python

import hardhatutil, time, smtplib, os, sys
from optparse import OptionParser

whereAmI = os.path.dirname(os.path.abspath(hardhatutil.__file__))

homeDir = os.environ['HOME']
buildDir = os.path.join(homeDir, "tinderbuild")
stopFile = os.path.join(buildDir, "stop")
defaultDomain = "osafoundation.org"
defaultRsyncServer = "192.168.101.46"      #  IP of current server

def main():
    
    parser = OptionParser(usage="%prog [options] buildName", version="%prog 1.0")
    parser.add_option("-t", "--toAddr", action="store", type="string", dest="toAddr",
      default="buildreport", help="Where to mail script reports\n"
      " [default] buildreport (at) osafoundation.org")
    parser.add_option("-p", "--project", action="store", type="string", dest="project",
      default="newchandler", help="Name of script to use (without .py extension)\n"
      "[default] newchandler")
    parser.add_option("-o", "--output", action="store", type="string", dest="outputDir",
      default=os.path.join(os.environ['HOME'],"output"), help="Name of temp output directory\n"
      " [default] ~/output")
    parser.add_option("-a", "--alert", action="store", type="string", dest="alertAddr",
      default="buildman", help="E-mail to notify on build errors \n"
      " [default] buildman (at) osafoundation.org")
    parser.add_option("-r", "--rsyncServer", action="store", type="string", dest="rsyncServer",
      default=defaultRsyncServer, help="Net address of server where builds get uploaded \n"
      " [default] " + defaultRsyncServer)
    parser.add_option("-s", "--script", action="store", dest="doScript",
      default="tinderbox.py", help="Script to run for the build\n"
      " [default] tinderbox.py")
      
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        parser.error("You must at least provide a name for your build")

    buildName = args[0]
    mailtoAddr = options.toAddr
    alertAddr = options.alertAddr
    if mailtoAddr.find('@') == -1:
        mailtoAddr += "@" + defaultDomain
    if alertAddr.find('@') == -1:
        alertAddr += "@" + defaultDomain

#     print "options ", options 
#     print " Build script ", options.doScript
#     print "args ", args[0] 
    
    prevStartInt = 0
    curDir = os.path.abspath(os.getcwd())

    path = os.environ.get('PATH', os.environ.get('path'))
    cvsProgram = hardhatutil.findInPath(path, "cvs")
#    print "cvs =", cvsProgram

    go = 1
    # Main loop

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

        nowString = time.strftime("%Y-%m-%d %H:%M:%S")
        startTime = str(startInt)
        prevStartInt = startInt
        
        # check CVS for any new hardhat script
        try:
            # bring this hardhat directory up to date
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [cvsProgram, "-q", "update", "-D'"+ nowString + "'"])
            hardhatutil.dumpOutputList(outputList)
        except:
            raise TinderbuildError, "Error updating HardHat"

        
        try:
            # launch the real build script
            outputList = hardhatutil.executeCommandReturnOutput(
             [os.path.join(curDir, options.doScript), "-o", options.outputDir, 
             "-a", alertAddr, 
             "-t", mailtoAddr,
             "-r", options.rsyncServer,
             "-p", options.project, args[0] ])
            hardhatutil.dumpOutputList(outputList)
        except:
            raise TinderbuildError, "Failed to launch build script"

        if os.path.exists(stopFile):
            go = 0

class TinderbuildError(Exception):
    def __init__(self, args=None):
        self.args = args

main()    