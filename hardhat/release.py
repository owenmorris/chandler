#!/usr/bin/env python

# The purpose of this script is to automate Chandler release (both milestone
# and regular) process.

import os, re, sys
from optparse import OptionParser
import hardhatutil, hardhatlib
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))
path = os.environ.get('PATH', os.environ.get('path'))
svnProgram = hardhatutil.findInPath(path, "svn")


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
        self.svnVersion = version.replace('.', '_')
        self.release = release

        self.workDir = os.path.join(os.getenv('HOME'),
                                    'CHANDLER_WORKDIR_' + self.svnVersion)
        os.mkdir(self.workDir)
        os.chdir(self.workDir)
        
        self.chandlerDir = os.path.join(self.workDir, 'chandler')


    def checkoutMinimal(self):
        outputList = hardhatutil.executeCommandReturnOutputRetry(
         [svnProgram, "-q", "checkout",
          'chandler/distrib/osx/bundle'])
        #hardhatutil.dumpOutputList(outputList, log)
        

    def updatePList(self):
        bundleDir = os.path.join(self.chandlerDir,
                                 'distrib',
                                 'osx',
                                 'bundle')
        plist = os.path.join(bundleDir, 'Info.plist')
        searchLong = r'(Milestone|Release) \d\.\d\.\d+ '
        searchShort = r'>\d\.\d\.\d+<'
        if self.release:
            longVersion = 'Release ' + self.version
        else:
            longVersion = 'Milestone ' + self.version
        shortVersion = '>' + self.version + '<'
        updateSmallFile(plist,
                        searchLong,
                        longVersion + ' ')
        updateSmallFile(plist,
                        searchShort,
                        shortVersion)


    def svnChanges(self):
        self.checkoutMinimal()
        self.updatePList()

        print 'cd ' + self.workDir
        print 'svn diff -u chandler/distrib'
        print 'to see if the changes look correct, then commit them.'
        print 'Finally do:'
        print '  cvs rtag -D now CHANDLER_' + self.cvsVersion + ' chandler-all'


def main():
    parser = OptionParser()

    parser.add_option('-s', '--svn',
                      action='store_true',
                      dest='svn',
                      default=False,
                      help='make svn changes')

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

    if op.svn:
        rel.svnChanges()
        return


main()
