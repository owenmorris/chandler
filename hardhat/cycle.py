#!/usr/bin/env python

#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
import traceback

def dumpException():
    t, v, tb = sys.exc_info()
    print time.strftime('%H:%M on %A, %d %B')
    print ''.join(traceback.format_exception(t, v, tb))

def main():
    whereAmI    = os.path.dirname(os.path.abspath(hardhatutil.__file__))
    curDir      = os.path.abspath(os.getcwd())
    path        = os.environ.get('PATH')
    homeDir     = os.environ.get('HOME')
    buildDir    = os.path.join(homeDir, 'tinderbuild')
    svnProgram  = hardhatutil.findInPath(path, 'svn')

    tboxScript  = os.path.join(curDir, 'tinderbox.py')
    buildScript = ' '.join(sys.argv[1:])
    stopFile    = os.path.join(buildDir, 'stop')

    if os.path.exists(stopFile):
        os.remove(stopFile)

    while True:
        os.chdir(curDir)

        print '[ cycle ] %s :: checking for hardhat svn updates' % time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            outputList = hardhatutil.executeCommandReturnOutputRetry([svnProgram, '-q', 'update'])
            hardhatutil.dumpOutputList(outputList)
        except:
            print '[ cycle ] %s :: Exception raised during svn update'  % time.strftime("%Y-%m-%d %H:%M:%S")
            dumpException()
            break

        print '[ cycle ] %s :: Running %s %s' % (time.strftime("%Y-%m-%d %H:%M:%S"), tboxScript, buildScript)
        try:
            outputList = hardhatutil.executeCommandReturnOutput([tboxScript, buildScript])
            hardhatutil.dumpOutputList(outputList)

        except hardhatutil.ExternalCommandErrorWithOutputList, e:
            print '[ cycle ] %s :: Exception during tinderbox run [%d]' % (time.strftime("%Y-%m-%d %H:%M:%S"), e.exitCode)
            hardhatutil.dumpOutputList(e.outputList)
            break

        if os.path.exists(stopFile):
            break

main()
