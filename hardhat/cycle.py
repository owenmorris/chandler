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
    curDir = os.path.abspath(os.getcwd())
    path = os.environ.get('PATH', os.environ.get('path'))
    cvsProgram = hardhatutil.findInPath(path, "cvs")

    if os.path.exists(stopFile):
        os.remove(stopFile)

    go = 1
    firstRound = 1

    while go:
        os.chdir(curDir)

        if not firstRound:
            print "Sleeping 5 minutes (" + buildName + ")"
            time.sleep(5 * 60)

        nowString = time.strftime("%Y-%m-%d %H:%M:%S")
        
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
             [os.path.join(curDir, 'tinderbox.py'), ' '.join(sys.argv[1:])])
            hardhatutil.dumpOutputList(outputList)
        except:
            raise TinderbuildError, "Failed to launch build script"

        if os.path.exists(stopFile):
            go = 0

        firstRound = 0


class TinderbuildError(Exception):
    def __init__(self, args=None):
        self.args = args

main()
