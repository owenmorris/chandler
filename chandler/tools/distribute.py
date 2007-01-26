#!/usr/bin/env python
#   Copyright (c) 2007 Open Source Applications Foundation
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

"""
distribute.py
"""

import sys, os
import platform
import string
from optparse import OptionParser
import build_lib

def parseOptions():
    _configItems = {
        'mode':      ('-m', '--mode',     's', None,  'distribute release or debug; defaults to trying both'),
        'buildDir':  ('-b', '--build',    's', '',    'working directory: where temporary distrib files will be processed'),
        'outputDir': ('-o', '--output',   's', '',    'output directory: where the final distribution files will be stored'),
        'sourceDir': ('-s', '--source',   's', '',    'chandler directory: where the distribution will be pulled from'),
        'tarball':   ('',   '--tarball',  'b', False, 'create the tarball (or zip) distribution - turns off -D'),
        'dmg':       ('',   '--dmg',      'b', False, 'create the OS X .dmg bundle - turns off -D'),
        'deb':       ('',   '--deb',      'b', False, 'create the debian package - turns off -D'),
        'rpm':       ('',   '--rpm',      'b', False, 'create the rpm package - turns off -D'),
        'exe':       ('',   '--exe',      'b', False, 'create the windows .exe installer - turns off -D'),
        'tag':       ('-t', '--tag',      's', '',    'release name, i.e. "0.7alpha5.dev-r12345-checkpoint20070122"'),
    }
    _usage = 'distribute [options]\n\nBundle installed Chandler working directory into a distribution'

    parser = OptionParser(version="%prog", usage=_usage)

    for key in _configItems:
        (shortCmd, longCmd, optionType, defaultValue, helpText) = _configItems[key]

        if optionType == 'b':
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              action='store_true',
                              default=defaultValue,
                              help=helpText)
        else:
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              default=defaultValue,
                              help=helpText)

    (options, args) = parser.parse_args()
    options.args    = args

    return options

def buildPlatform(options):
    options.platformName = 'Unknown'
    options.platformID   = ''

    if os.name == 'nt':
        options.platformName = 'Windows'
        options.platformID   = 'win'
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            if platform.machine() == 'i386':
                options.platformName = 'Mac OS X (intel)'
                options.platformID   = 'iosx'
            else:
                options.platformName = 'Mac OS X (ppc)'
                options.platformID   = 'osx'
        elif sys.platform == 'cygwin':
            options.platformName = 'Windows'
            options.platformID   = 'win'
        else:
            options.platformName = 'Linux'
            options.platformID   = 'linux'

def buildDistributionList(options):
    options.distribs = []

    # if any of the individual options are set then build distrib list
    if options.tarball or options.dmg or options.rpm or options.deb or options.exe:
        if options.tarball:
            if options.platformID == 'linux' or options.platformID == 'win':
                options.distribs.append('tarball')
            else:
                print 'Platform is [%s] -- ignoring tarball request' % options.platformName

        if options.dmg:
            if options.platformID == 'osx' or options.platformID == 'iosx':
                options.distribs.append('dmg')
            else:
                print 'Platform is [%s] -- ignoring dmg request' % options.platformName

        if options.rpm:
            if options.platformID == 'linux':
                options.distribs.append('rpm')
            else:
                print 'Platform is [%s] -- ignoring rpm request' % options.platformName

        if options.deb:
            if options.platformID == 'linux':
                options.distribs.append('deb')
            else:
                print 'Platform is [%s] -- ignoring deb request' % options.platformName

        if options.exe:
            if options.platformID == 'win':
                options.distribs.append('exe')
            else:
                print 'Platform is [%s] -- ignoring exe request' % options.platformName
    else:
        if options.platformID == 'linux':
            options.distribs = [ 'tarball', 'rpm', 'deb' ]
        else:
            if options.platformID == 'win':
                options.distribs = [ 'tarball', 'exe' ]
            else:
                options.distribs = [ 'tarball', 'dmg' ]

def buildDistribName(mode, options):
    return 'Chandler_%s_%s_%s' % (options.platformID, mode, options.tag)

def buildDistributionImage(mode, options):
    if options.platformID == 'iosx':
        s = 'osx'
    else:
        s = options.platformID

    if mode == 'release':
        manifestFile = os.path.join(options.sourceDir, 'distrib', s, 'manifest.%s' % s)
    else:
        manifestFile = os.path.join(options.sourceDir, 'distrib', s, 'manifest.debug.%s' % s)

    options.distribName = buildDistribName(mode, options)
    options.distribDir  = os.path.join(options.buildDir, options.distribName)

    if os.access(options.distribDir, os.F_OK):
        build_lib.rmdirs(options.distribDir)

    os.mkdir(options.distribDir)

    return build_lib.handleManifest(options.buildDir, options.outputDir, options.distribDir, manifestFile, options.platformID)

def buildTarball(mode, options):
    os.chdir(options.buildDir)

    if options.platformID == 'win':
        distribFile = '%s.zip' % options.distribName

        cmd = [ 'zip', '-r', distribFile, options.distribDir ]
    else:
        distribFile = '%s.tar.gz' % options.distribName

        cmd = [ 'tar', 'czf', distribFile, options.distribDir ]

    if os.path.isfile(distribFile):
        os.remove(distribFile)

    r = build_lib.runCommand(cmd)

    print 'Compressed distribution file created (%d)' % r

    return distribFile

def buildDMG(mode, options):
    os.chdir(options.buildDir)

    distribFile = '%s.dmg' % options.distribName

    if os.path.isfile(distribFiles):
        os.remove(distribFiles)

    cmd = [ os.path.join(options.toolsDir, 'makediskimage.sh'), options.distribDir ]

    r = build_lib.runCommand(cmd)

    print 'OS X disk image file created (%d)' % r

    return distribFile

def buildEXE(mode, options):
    pass

def buildRPM(mode, options):
    pass

def buildDEB(mode, options):
    pass


if __name__ == '__main__':
    modes   = [ 'release', 'debug' ]
    options = parseOptions()

    options.toolsDir = os.path.abspath(os.path.dirname(__file__))

    if not options.buildDir:
        options.buildDir = os.path.join(os.environ['HOME'], 'tinderbuild')

    if not options.outputDir:
        options.outputDir = options.buildDir

    if not options.sourceDir:
        if 'CHANDLERHOME' in os.environ:
            options.sourceDir = os.path.realpath(os.environ['CHANDLERHOME'])
        else:
            options.sourceDir = os.getcwd()

    if not os.path.isdir(options.sourceDir):
        print 'Unable to locate source (aka Chandler) directory [%s]' % options.sourceDir
        sys.exit(3)

    if not os.path.isdir(options.buildDir):
        print 'Unable to locate build (aka tinderbuild) directory [%s]' % options.buildDir
        sys.exit(3)

    if not os.path.isdir(options.outputDir):
        print 'Unable to locate build output directory [%s]' % options.outputDir
        sys.exit(3)

    if not os.path.isfile(os.path.join(options.sourceDir, 'version.py')):
        print 'Source directory [%s] does not point to a Chandler install' % options.sourceDir
        sys.exit(3)

    if options.mode:
        s = options.mode.lower()

        if s in modes:
            modes = [ s ]
        else:
            print 'Invalid mode [%s] specified' % s
            sys.exit(3)

    buildPlatform(options)
    buildDistributionList(options)
    options.major, options.minor, options.release, options.version = build_lib.versionInformation(options.sourceDir, options.platformName, options.tag)

    if len(options.distribs) > 0:
        options.distribFiles = {}

        for mode in modes:
            buildDistributionImage(mode, options)

            options.distribFiles[mode] = []

            for build in options.distribs:
                if build == 'tarball':
                    options.distribFiles[mode].append(buildTarball(mode, options))
                if build == 'dmg':
                    options.distribFiles[mode].append(buildDMG(mode, options))
                if build == 'exe':
                    options.distribFiles[mode].append(buildEXE(mode, options))
                if build == 'rpm':
                    options.distribFiles[mode].append(buildRPM(mode, options))
                if build == 'deb':
                    options.distribFiles[mode].append(buildDEB(mode, options))

            print options.distribFiles[mode]
