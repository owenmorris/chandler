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


# This should be run once a day on a machine hosting chandler continuous
# builds. The job of this script is to prune excess directories/old
# downloads.
#
# The default policy is as follows:
# - keep all builds from the last 48 hours
# - keep one build per day for the past 30 days
# - keep the latest build
# - delete all others
#
# We assume directory structure as follows:
#
# + absolute start directory
#   + (*-osx | *-linux | *-win | *-iosx)
#     + YYYYMMDDHHMMSS
#
# We delete all YYYYMMDDHHMMSS directories that don't match our policy.

shortPolicyHours = 48
longPolicyDays   = 30
smtpServer       = 'mail.osafoundation.org'
downloadsServer  = 'builds'
fromAddr         = 'builds'
toAddr           = 'builder-admin'
defaultDomain    = 'osafoundation.org'
startDir         = '/home/builder/www/docs/chandler/continuous'
tboxDirGlob      = ['*-win', '*-osx', '*-linux', '*-iosx']

symlinkTargets   = ['cosmo-full-osx', 'cosmo-0.2-osx', 'scooby-full-osx']

symlinkNames     = { 'cosmo-full-osx':  'cosmo-continuous-latest.tar.gz',
                     'cosmo-0.2-osx':   'cosmo-0.2-continuous-latest.tar.gz',
                     'scooby-full-osx': 'scooby-continuous-latest.tar.gz',
                   }

import datetime, time, smtplib, os, glob

class mylog:
    def __init__(self):
        self.data = ''

    def __str__(self):
        return self.data
    
    def write(self, data):
        self.data += data

def rmdirRecursive(dir):
    """
    Recursively remove a directory.
    Parameters:
        dir: directory path
    Returns:
        nothing
    """

    if os.path.islink(dir):
        os.remove(dir)
        return

    for name in os.listdir(dir):
        full_name = os.path.join(dir, name)
        # on Windows, if we don't have write permission we can't remove
        # the file/directory either, so turn that on
        if os.name == 'nt':
            if not os.access(full_name, os.W_OK):
                os.chmod(full_name, 0600)
        if os.path.isdir(full_name):
            rmdirRecursive(full_name)
        else:
            os.remove(full_name)
    os.rmdir(dir)

def prune_and_link():
    global startDir

    nowDT = datetime.datetime.now()
    tooOld = nowDT - datetime.timedelta(days=longPolicyDays)
    tooNew = nowDT - datetime.timedelta(hours=longPolicyDays)

    tooOldStr = tooOld.strftime("%Y%m%d%H%M%S")
    tooNewStr = tooNew.strftime("%Y%m%d%H%M%S")

    symlinkDir = ''

    def checkArchiveDir(archive, symlinkDir):
        if archive > symlinkDir:
            symFiles = glob.glob('*.gz')

            if len(symFiles) > 0:
                symlinkDir = archive
        return symlinkDir    

    os.chdir(startDir)

    # get directories where tbox clients rsync their distributions
    topdirs = []
    for dirGlob in tboxDirGlob:
        topdirs += glob.glob(dirGlob)

    # process topdirs
    for dir in topdirs:
        os.chdir(startDir)

        if not os.path.isdir(dir):
            continue

        os.chdir(os.path.join(startDir, dir))

        # now the real pruning happens here
        betweenDays = {}
        archivedirs = glob.glob('[0-9]*')
        symlinkDirs = []

        for archive in archivedirs[:-1]: # [:-1] means 'leave latest'
            if len(archive) != 14 or not os.path.isdir(archive):
                continue 

            if archive < tooOldStr:
                #print 'delete', os.path.join(startDir, dir, archive)
                rmdirRecursive(archive)
                continue

            if archive > tooNewStr:
                #print 'leave', os.path.join(startDir, dir, archive)
                symlinkDirs.append(archive)
                continue

            # Now all we have left are those in-betweens...

            day = archive[:8]
            if betweenDays.has_key(day):
                #print 'delete', os.path.join(startDir, dir, archive)
                rmdirRecursive(archive)
                continue

            betweenDays[day] = 1
            #print 'leave', os.path.join(startDir, dir, archive)
            symlinkDirs.append(archive)

        if dir in symlinkTargets:
            print 'symlink check', dir
            symlinkDirs.sort()
            if len(symlinkDirs) > 0:
                print 'last found', symlinkDirs[-1]

                symlinkDir = checkArchiveDir(archive, symlinkDirs[-1])
                sympath    = os.path.join(startDir, dir, symlinkDir, '*.tar.gz')
                symFiles   = glob.glob(sympath)

                print 'sympath, symFiles:', sympath, symFiles

                for symSource in symFiles:
                    symTarget = os.path.join(startDir, symlinkNames[dir])
                    if os.path.isfile(symTarget) or os.path.islink(symTarget):
                        #print 'removing', symTarget
                        os.unlink(symTarget)
                    print 'linking', symSource, symTarget
                    os.symlink(symSource, symTarget)

def main():
    global shortPolicyHours, longPolicyDays, smtpServer, downloadsServer
    global fromAddr, toAddr

    fromAddr += '@' + defaultDomain
    toAddr   += '@' + defaultDomain

    try:
        prune_and_link()
    except Exception, e:
        import traceback
        log = mylog()
        traceback.print_exc(file=log)
        SendMail(fromAddr, toAddr, downloadsServer,  log)


def SendMail(fromAddr, toAddr, serverName, log):
    global smtpServer
    
    subject  = "[prunedownloads] problem from " + serverName
    msg      = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (fromAddr, toAddr, subject))
    msg      += str(log)

    print msg

    server = smtplib.SMTP(smtpServer)
    server.sendmail(fromAddr, toAddr, msg)
    server.quit()


main()
