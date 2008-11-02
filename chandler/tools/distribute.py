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
from build_lib import initLog, log, rmdirs, handleManifest, runCommand, getCommand, \
                      generateVersionData, findInPath, convertLineEndings

_debug = False

class DistributionError(Exception): pass

def parseOptions():
    _configItems = {
        'mode':      ('-m', '--mode',    's', None,  'distribute release or debug; defaults to trying both'),
        'buildDir':  ('-w', '--work',    's', '',    'working directory: where temporary distrib files will be processed'),
        'outputDir': ('-o', '--output',  's', '',    'output directory: where the final distribution files will be stored'),
        'sourceDir': ('-s', '--source',  's', '',    'chandler directory: where the distribution will be pulled from'),
        'binDir':    ('-b', '--bin',     's', '',    'chandlerBin directory: where the distribution binaries will be pulled from'),
        'quiet':     ('-q', '--quiet',   'b', False, 'Mute log echoing to stdout'),
        'tarball':   ('',   '--tarball', 'b', False, 'only create the tarball (or zip) distribution'),
        'dmg':       ('',   '--dmg',     'b', False, 'only create the OS X .dmg bundle'),
        'deb':       ('',   '--deb',     'b', False, 'only create the debian package'),
        'rpm':       ('',   '--rpm',     'b', False, 'only create the rpm package'),
        'exe':       ('',   '--exe',     'b', False, 'only create the windows .exe installer'),
        'tag':       ('-t', '--tag',     's', None,  'continuous build name/tag to add to version information')
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
    options.platformName  = 'Unknown'
    options.platformID    = ''
    options.platformSubID = ''

    rv = True

    if os.name == 'nt':
        options.platformName = 'Windows'
        options.platformID   = 'win'
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            if platform.machine() == 'i386':
                options.platformName = 'Mac OS X (intel)'
                options.platformID   = 'intel-osx'
            else:
                options.platformName = 'Mac OS X (ppc)'
                options.platformID   = 'ppc-osx'

            release   = platform.release()
            version   = release.split('.')
            platforms = {'7': 'panther', '8': 'tiger', '9': 'leopard'}

            if len(version) == 3:
                options.platformSubID = platforms.get(version[0], version[0])

            if options.platformSubID == 'leopard':
                options.platformID += '-leopard'

        elif sys.platform == 'cygwin':
            options.platformName = 'Windows'
            options.platformID   = 'win'
        else:
            options.platformName = 'Linux'
            options.platformID   = 'linux'

            if os.path.exists('/etc/lsb-release'):
                try:
                    for line in open('/etc/lsb-release', 'r').readlines():
                        name, value = line.split('=')

                        if name.startswith('DISTRIB_CODENAME'):
                            options.platformSubID = value.strip()
                            break

                except IOError:
                    pass
    else:
        log('Unknown platform: ' + os.name, error=True)
        rv = False

    return rv


def buildDistributionList(options):
    options.distribs = []

    # if any of the individual options are set then build distrib list
    if options.tarball or options.dmg or options.rpm or options.deb or options.exe:
        if options.tarball:
            if options.platformID == 'linux' or options.platformID == 'win':
                options.distribs.append('tarball')
            else:
                log('Platform is [%s] -- ignoring tarball request' % options.platformName)

        if options.dmg:
            if 'osx' in options.platformID:
                options.distribs.append('dmg')
            else:
                log('Platform is [%s] -- ignoring dmg request' % options.platformName)

        if options.rpm:
            if options.platformID == 'linux':
                options.distribs.append('rpm')
            else:
                log('Platform is [%s] -- ignoring rpm request' % options.platformName)

        if options.deb:
            if options.platformID == 'linux':
                options.distribs.append('deb')
            else:
                log('Platform is [%s] -- ignoring deb request' % options.platformName)

        if options.exe:
            if options.platformID == 'win':
                options.distribs.append('exe')
            else:
                log('Platform is [%s] -- ignoring exe request' % options.platformName)
    else:
        if options.platformID == 'linux':
            if options.platformSubID in ['gutsy', 'hardy', 'intrepid', 'jaunty']:
                options.distribs = [ 'deb' ]
            else:
                options.distribs = [ 'tarball' ]
        elif options.platformID == 'win':
            options.distribs = [ 'tarball', 'exe' ]
        else:
            options.distribs = [ 'dmg' ]

def buildDistribName(mode, options):
    if mode == 'release':
        modeStr = ''
    else:
        modeStr = '%s_' % mode
    return 'Chandler_%s_%s%s' % (options.platformID, modeStr, options.version_info['version'])

def buildDistributionImage(mode, options):
    p = options.platformID
    s = p

    if 'osx' in options.platformID:
        p = 'osx'
        s = options.platformID
    elif options.platformID == 'linux':
        if options.platformSubID in ['gutsy', 'hardy', 'intrepid', 'jaunty']:
            s = 'gutsy'

    if mode == 'release':
        manifestFile = os.path.join(options.sourceDir, 'distrib', p, 'manifest.%s' % s)
    else:
        manifestFile = os.path.join(options.sourceDir, 'distrib', p, 'manifest.debug.%s' % s)

    options.distribName = buildDistribName(mode, options)
    options.distribDir  = os.path.join(options.buildDir, options.distribName)

        # yep - we are removing the directory we are
        # about ready to create - but we want to ensure
        # it's truly empty
    if os.access(options.distribDir, os.F_OK):
        rmdirs(options.distribDir)

    os.makedirs(options.distribDir)

    # when we make an osx distribution, we actually need to put it
    # in a subdirectory (which has a .app extension).  So we set
    # distribDir locally to that .app dir so that handleManifest()
    # puts things in the right place.

    if 'osx' in options.platformID:
        distribDir = os.path.join(options.distribDir, '%s.app' % options.distribName)
    else:
        distribDir = options.distribDir

    result = handleManifest(options.buildDir, options.outputDir, distribDir, manifestFile, options.platformID)

    if result and options.platformID == 'win':
        convertLineEndings(distribDir)

    return result

def buildTarball(mode, options):
    os.chdir(options.buildDir)

    if options.platformID == 'win':
        distribFile = '%s.zip' % options.distribName

        cmd = [ findInPath(os.environ['PATH'], 'zip'), '-r', distribFile, options.distribName ]
    else:
        distribFile = '%s.tar.gz' % options.distribName

        cmd = [ 'tar', 'czf', distribFile, options.distribName ]

    if os.path.isfile(distribFile):
        os.remove(distribFile)

    r = runCommand(cmd)

    log('Compressed distribution file created (%d)' % r)
    
    if r:
        raise DistributionError(str(r))

    return distribFile

def buildDMG(mode, options):
    os.chdir(options.buildDir)

    distribFile = '%s.dmg' % options.distribName

    if os.path.isfile(distribFile):
        os.remove(distribFile)

    cmd = [ os.path.join(options.toolsDir, 'makediskimage.sh'), options.distribDir ]

    r = runCommand(cmd)

    log('OS X disk image file created (%d)' % r)

    if r:
        raise DistributionError(str(r))

    return distribFile

def buildEXE(mode, options):
    os.chdir(options.buildDir)

    result     = None
    nsisBinary = findInPath(os.environ['PATH'], 'makensis.exe')

    if nsisBinary is None:
        log('Unable to locate makensis.exe in PATH', error=True)
    else:
        nsisPath   = os.path.join(options.buildDir, 'internal', 'installers', 'win')
        nsisScript = os.path.join(nsisPath, 'makeinstaller.sh')

        scriptFile = getCommand(['cygpath', '-aw', os.path.join(nsisPath, 'chandler.nsi')])

        cmd = [ nsisBinary, '/DSNAP_%s' % mode.upper(),
                            '/DDISTRIB_DIR=%s' % options.distribName,
                            '/DDISTRIB_VERSION=%s' % options.version_info['version'],
                            scriptFile ]

        r = runCommand(cmd)

        distribFile = '%s.exe' % options.distribName

        targetFile = os.path.join(options.buildDir, distribFile)
        sourceFile = os.path.join(nsisPath, 'Setup.exe')

        if os.path.exists(targetFile):
            os.remove(targetFile)

        if os.path.exists(sourceFile):
            os.rename(sourceFile, targetFile)

            result = distribFile

    if r:
        raise DistributionError(str(r))

    return result

def buildRPM(mode, options):
    os.chdir(options.buildDir)

    rpmPath   = os.path.join(options.buildDir, 'internal', 'installers', 'rpm')
    rpmScript = os.path.join(rpmPath, 'makeinstaller.sh')
    specFile  = os.path.join(rpmPath, 'chandler.spec')
    version   = '%s.%s' % (options.version_info['major'], options.version_info['minor'])
    release   = options.version_info['release'].replace('-', '_')  # RPM doesn't like '-'

    cmd = [ rpmScript, rpmPath, specFile, options.buildDir, options.distribName, version, release ]

    r = runCommand(cmd)

    log('RPM created (%d)' % r)

    if r:
        raise DistributionError(str(r))

    return '%s.i386.rpm' % options.distribName


def buildDEB(mode, options):
    os.chdir(options.buildDir)

    debPath   = os.path.join(options.buildDir, 'internal', 'installers', 'deb')
    debScript = os.path.join(debPath, 'makeinstaller.sh')
    version   = options.version_info['version'].replace('-', '~')
    libicu    = 'libicu38'

    if options.platformSubID == 'gutsy':
        libicu = 'libicu36'

    cmd = [debScript, debPath, options.buildDir, options.distribName, version, mode, libicu]

    r = runCommand(cmd)

    log('DEB created (%d)' % r)

    if r:
        raise DistributionError(str(r))

    if mode == 'release':
        m = '_'
    else:
        m = '_debug_'
    
    return 'Chandler_linux%(mode)s%(version)s-1_i386.deb' % {'mode': m,
                                                             'version': version}


def checkOptions(options):
    options.toolsDir = os.path.abspath(os.path.dirname(__file__))

    if not options.sourceDir:
        if 'CHANDLERHOME' in os.environ:
            options.sourceDir = os.path.realpath(os.environ['CHANDLERHOME'])
        else:
            options.sourceDir = os.getcwd()

            if not os.path.isfile(os.path.join(options.sourceDir, 'version.py')):
                options.sourceDir = os.path.abspath(os.path.join(options.toolsDir, '..'))

    if not options.buildDir:
        options.buildDir = os.path.abspath(os.path.join(options.sourceDir, '..'))

    if not os.path.isdir(options.buildDir):
        sys.stderror.write('Unable to locate build directory [%s]\n' % options.buildDir)
        return False

    if not os.path.isdir(options.sourceDir):
        log('Unable to locate source (aka Chandler) directory [%s]' % options.sourceDir, error=True)
        return False

    if not options.binDir:
        if 'CHANDLERBIN' in os.environ:
            options.binDir = os.path.realpath(os.environ['CHANDLERBIN'])
        else:
            options.binDir = os.getcwd()

            if not os.path.isfile(os.path.join(options.binDir, 'version.py')):
                options.binDir = os.path.abspath(os.path.join(options.toolsDir, '..'))

    if not os.path.isdir(options.binDir):
        log('Unable to locate bin (aka ChandlerBin) directory [%s]' % options.binDir, error=True)
        return False

    if options.outputDir:
        if not os.path.isdir(options.outputDir):
            os.makedirs(options.outputDir)
    else:
        options.outputDir = options.buildDir

    if not os.path.isdir(options.outputDir):
        log('Unable to locate build output directory [%s]' % options.outputDir, error=True)
        return False

    if not os.path.isfile(os.path.join(options.sourceDir, 'version.py')):
        log('Source directory [%s] does not point to a Chandler install' % options.sourceDir, error=True)
        return False

    if options.tag is not None:
        options.tag = options.tag.strip()

    options.modes = [ 'release', 'debug' ]

    if options.mode:
        s = options.mode.lower().strip()

        if s in options.modes:
            options.modes = [ s ]
        else:
            log('Invalid mode [%s] specified' % s, error=True)
            return False

    return True


def generateTinderboxOutput(mode, distribFiles):
    if mode == 'release':
        tfilename = 'enduser'
    else:
        tfilename = 'developer'

    tfilename = os.path.join(options.outputDir, tfilename)
    tfile     = open(tfilename, 'w')

    for distribFile in distribFiles:
        log('Moving %s from %s to %s' % (distribFile, options.buildDir, options.outputDir))
        tfile.write('%s\n' % distribFile)
        os.rename(os.path.join(options.buildDir, distribFile),
                  os.path.join(options.outputDir, distribFile))

    tfile.close()


if __name__ == '__main__':
    success = True
    options = parseOptions()

    if not checkOptions(options):
        sys.exit(3)

    if not buildPlatform(options):
        sys.exit(3)

    buildDistributionList(options)

    options.version_info = generateVersionData(options.sourceDir, options.platformName, options.tag)

    if _debug:
        log(options)

    try:
        if len(options.distribs) > 0:
            options.distribFiles = {}

            for mode in options.modes:
                if os.path.isdir(os.path.join(options.binDir, mode)):
                    if not buildDistributionImage(mode, options):
                        log('An error occurred while creating the %s distribution image' % mode, error=True)
                        success = False
                        break

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

                    if options.outputDir <> options.buildDir:
                        generateTinderboxOutput(mode, options.distribFiles[mode])

                    if os.access(options.distribDir, os.F_OK):
                        rmdirs(options.distribDir)

                    if _debug:
                        log(options.distribFiles[mode])
                else:
                    log('Skipping %s because the directory is not present' % mode, error=True)
    except DistributionError:
        success = False

    # revert the contents of version.py to clear any previously generated values
    runCommand([ findInPath(os.environ['PATH'], 'svn'), 'revert', os.path.join(options.sourceDir, 'version.py') ])

    if not success:
        sys.exit('Failed to create distributions')

