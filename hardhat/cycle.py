#!/usr/bin/env python

#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import hardhatutil, time, os, sys

whereAmI = os.path.dirname(os.path.abspath(hardhatutil.__file__))

homeDir = os.environ['HOME']
buildDir = os.path.join(homeDir, "tinderbuild")
stopFile = os.path.join(buildDir, "stop")

def main():
    curDir = os.path.abspath(os.getcwd())
    path = os.environ.get('PATH', os.environ.get('path'))
    svnProgram = hardhatutil.findInPath(path, "svn")

    if os.path.exists(stopFile):
        os.remove(stopFile)

    go = 1
    firstRound = 1

    while go:
        os.chdir(curDir)

        #if not firstRound:
        #    print "Sleeping 5 minutes"
        #    time.sleep(5 * 60)

        nowString = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # check SVN for any new hardhat script
        try:
            # bring this hardhat directory up to date
            outputList = hardhatutil.executeCommandReturnOutputRetry(
             [svnProgram, "-q", "update"])
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
