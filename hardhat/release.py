#!/usr/bin/env python

# The purpose of this script is to automate Chandler release (both milestone
# and regular) process.

import os, re, sys
from optparse import OptionParser
import hardhatutil, hardhatlib
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))
path = os.environ.get('PATH', os.environ.get('path'))
cvsProgram = hardhatutil.findInPath(path, "cvs")


def updateSmallFile(filename, search, replace):
    """
    Updates a small file in-place by replacing search string with replace.
    """
    # First read into memory, replacing patterns
    f = file(filename, 'r')
    inList = []
    for line in f:
        inList.append(re.sub(search, replace, line))
    f.close()

    # Then write back out into the file
    f = file(filename, 'w')
    for line in inList:
        f.write(line)
    f.close()


class Release:
    def __init__(self, version, release):
        self.version = version
        self.cvsVersion = version.replace('.', '_')
        self.release = release

        self.workDir = os.path.join(os.getenv('HOME'),
                                    'CHANDLER_WORKDIR_' + self.cvsVersion)
        os.mkdir(self.workDir)
        os.chdir(self.workDir)
        
        self.chandlerDir = os.path.join(self.workDir, 'chandler')


    def checkoutMinimal(self):
        outputList = hardhatutil.executeCommandReturnOutputRetry(
         [cvsProgram, "-q -z3", "checkout",
          'chandler/application/welcome.html',
          'chandler/distrib/osx/bundle'])
        #hardhatutil.dumpOutputList(outputList, log)
        

    def updateWelcome(self):
        updateSmallFile(os.path.join(self.chandlerDir,
                                     'application',
                                     'welcome.html'),
                        r'\?rev=CHANDLER_[a-zA-Z0-9_]+&',
                        '?rev=CHANDLER_' + self.cvsVersion + '&')


    def updatePLists(self):
        bundleDir = os.path.join(self.chandlerDir,
                                 'distrib',
                                 'osx',
                                 'bundle')
        plist = 'Info.plist'
        rel = os.path.join(bundleDir, 'release', plist)
        deb = os.path.join(bundleDir, 'debug', plist)
        searchLong = r'(Milestone|Release) \d\.\d\.\d+ '
        searchShort = r'>\d\.\d\.\d+<'
        if self.release:
            longVersion = 'Release ' + self.version
        else:
            longVersion = 'Milestone ' + self.version
        shortVersion = '>' + self.version + '<'
        updateSmallFile(rel,
                        searchLong,
                        longVersion + ' ')
        updateSmallFile(rel,
                        searchShort,
                        shortVersion)
        updateSmallFile(deb,
                        searchLong,
                        longVersion + ' ')
        updateSmallFile(deb,
                        searchShort,
                        shortVersion)


    def cvsChanges(self):
        self.checkoutMinimal()
        self.updateWelcome()
        self.updatePLists()

        print 'cd ' + self.workDir
        print 'cvs diff -u chandler/application/welcome.html chandler/distrib'
        print 'to see if the changes look correct, then commit them.'
        print 'Finally do:'
        print '  cvs rtag -D now CHANDLER_' + self.cvsVersion + ' chandler-all'


def main():
    parser = OptionParser()

    parser.add_option('-c', '--cvs',
                      action='store_true',
                      dest='cvs',
                      default=False,
                      help='make cvs changes')

    parser.add_option('-r', '--release',
                      action='store_true',
                      dest='release',
                      default=False,
                      help='make a release rather than milestone')
    
    parser.add_option('-v', '--version',
                      action='store', type='string',
                      dest='version',
                      default=None,
                      help='version number in x.y.z format')

    (op, args) = parser.parse_args()
    if not op.version:
        print 'You must provide at least a version in x.y.z format'
        sys.exit(1)

    rel = Release(op.version, op.release)

    if op.cvs:
        rel.cvsChanges()
        return


main()
