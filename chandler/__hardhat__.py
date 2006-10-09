import os, hardhatlib, hardhatutil, sys, platform

info = {
        'name':'chandler',
        'root':'..',
       }

dependencies = ()

def run(buildenv):

    if buildenv['version'] == 'debug':
        python = buildenv['python_d']

    if buildenv['version'] == 'release':
        python = buildenv['python']

    hardhatlib.executeCommandNoCapture( buildenv, info['name'],
     [python, "Chandler.py"], "Running Chandler" )


def removeRuntimeDir(buildenv):
    pass

def distribute(buildenv):

    majorVersion, minorVersion, releaseVersion, buildName = _getVersionInfo(buildenv)

    installTargetFile = None

    if buildenv['version'] == 'debug':
        if buildenv['os'] == 'osx':
            if platform.processor() == 'i386':
                distName = 'Chandler_iosx_debug_' + buildName
            else:
                distName = 'Chandler_osx_debug_' + buildName
            # when we make an osx distribution, we actually need to put it
            # in a subdirectory (which has a .app extension).  So we set
            # 'distdir' temporarily to that .app dir so that handleManifest()
            # puts things in the right place.  Then we set 'distdir' to its
            # parent so that it gets cleaned up further down.
            distDirParent = buildenv['root'] + os.sep + distName
            distDir = distDirParent + os.sep + distName + ".app"
            buildenv['distdir'] = distDir
            if os.access(distDirParent, os.F_OK):
                hardhatlib.rmdir_recursive(distDirParent)
            os.mkdir(distDirParent)
            os.mkdir(distDir)

            manifestFile = "distrib/osx/manifest.debug.osx"
            hardhatlib.handleManifest(buildenv, manifestFile)
            makeDiskImage = buildenv['hardhatroot'] + os.sep + \
             "makediskimage.sh"
            os.chdir(buildenv['root'])
            hardhatlib.executeCommand(buildenv, "HardHat",
             [makeDiskImage, distName],
             "Creating disk image from " + distName)
            compFile1 = distName + ".dmg"

            # reset 'distdir' up a level so that it gets removed below.
            buildenv['distdir'] = distDirParent
            distDir = distDirParent

        elif buildenv['os'] == 'posix':

            distName = 'Chandler_linux_debug_' + buildName
            distDir = buildenv['root'] + os.sep + distName
            buildenv['distdir'] = distDir
            if os.access(distDir, os.F_OK):
                hardhatlib.rmdir_recursive(distDir)
            os.mkdir(distDir)

            manifestFile = "distrib/linux/manifest.debug.linux"
            hardhatlib.handleManifest(buildenv, manifestFile)

            os.chdir(buildenv['root'])

            compFile1         = hardhatlib.compressDirectory(buildenv, [distName], distName)
            installTargetFile = hardhatlib.makeInstaller(buildenv, [distName], distName, majorVersion, minorVersion, releaseVersion)

        elif buildenv['os'] == 'win':

            distName = 'Chandler_win_debug_' + buildName
            distDir  = buildenv['root'] + os.sep + distName

            buildenv['distdir'] = distDir

            if os.access(distDir, os.F_OK):
                hardhatlib.rmdir_recursive(distDir)

            os.mkdir(distDir)

            manifestFile = "distrib" + os.sep + "win" + os.sep + "manifest.debug.win"
            hardhatlib.handleManifest(buildenv, manifestFile)

            os.chdir(buildenv['root'])

            hardhatlib.convertLineEndings(buildenv['distdir'])

            compFile1         = hardhatlib.compressDirectory(buildenv, [distName], distName)
            installTargetFile = hardhatlib.makeInstaller(buildenv, [distName], distName, majorVersion, minorVersion, releaseVersion)

    if buildenv['version'] == 'release':

        if buildenv['os'] == 'posix':

            distName = 'Chandler_linux_' + buildName
            distDir = buildenv['root'] + os.sep + distName
            buildenv['distdir'] = distDir
            if os.access(distDir, os.F_OK):
                hardhatlib.rmdir_recursive(distDir)
            os.mkdir(distDir)

            manifestFile = "distrib/linux/manifest.linux"
            hardhatlib.handleManifest(buildenv, manifestFile)

            os.chdir(buildenv['root'])

            compFile1         = hardhatlib.compressDirectory(buildenv, [distName], distName)
            installTargetFile = hardhatlib.makeInstaller(buildenv, [distName], distName, majorVersion, minorVersion, releaseVersion)

        if buildenv['os'] == 'osx':
            if platform.processor() == 'i386':
                distName = 'Chandler_iosx_' + buildName
            else:
                distName = 'Chandler_osx_' + buildName
            # when we make an osx distribution, we actually need to put it
            # in a subdirectory (which has a .app extension).  So we set
            # 'distdir' temporarily to that .app dir so that handleManifest()
            # puts things in the right place.  Then we set 'distdir' to its
            # parent so that it gets cleaned up further down.
            distDirParent = buildenv['root'] + os.sep + distName
            distDir = distDirParent + os.sep + distName + ".app"
            buildenv['distdir'] = distDir
            if os.access(distDirParent, os.F_OK):
                hardhatlib.rmdir_recursive(distDirParent)
            os.mkdir(distDirParent)
            os.mkdir(distDir)

            manifestFile = "distrib/osx/manifest.osx"
            hardhatlib.handleManifest(buildenv, manifestFile)
            makeDiskImage = buildenv['hardhatroot'] + os.sep + \
             "makediskimage.sh"
            os.chdir(buildenv['root'])
            hardhatlib.executeCommand(buildenv, "HardHat",
             [makeDiskImage, distName],
             "Creating disk image from " + distName)
            compFile1 = distName + ".dmg"

            # reset 'distdir' up a level so that it gets removed below.
            buildenv['distdir'] = distDirParent
            distDir = distDirParent

        if buildenv['os'] == 'win':

            distName = 'Chandler_win_' + buildName
            distDir  = buildenv['root'] + os.sep + distName

            buildenv['distdir'] = distDir

            if os.access(distDir, os.F_OK):
                hardhatlib.rmdir_recursive(distDir)

            os.mkdir(distDir)

            manifestFile = "distrib" + os.sep + "win" + os.sep + "manifest.win"
            hardhatlib.handleManifest(buildenv, manifestFile)

            os.chdir(buildenv['root'])
            hardhatlib.convertLineEndings(buildenv['distdir'])

            compFile1         = hardhatlib.compressDirectory(buildenv, [distName], distName)
            installTargetFile = hardhatlib.makeInstaller(buildenv, [distName], distName, majorVersion, minorVersion, releaseVersion)

    # put the compressed files in the right place if specified 'outputdir'
    if buildenv['outputdir']:
        if buildenv['version'] == 'release':
            outputFlagFile = os.path.join(buildenv['outputdir'], 'enduser')
        else:
            outputFlagFile = os.path.join(buildenv['outputdir'], 'developer')

        if os.path.exists(outputFlagFile):
            os.remove(outputFlagFile)

        if not os.path.exists(buildenv['outputdir']):
            os.mkdir(buildenv['outputdir'])

        # The end-user distro
        if os.path.exists(buildenv['outputdir'] + os.sep + compFile1):
            os.remove(buildenv['outputdir'] + os.sep + compFile1)
        os.rename(compFile1, buildenv['outputdir'] + os.sep + compFile1)

        # The end-user installer
        if installTargetFile:
            installSource = os.path.join(buildenv['root'], installTargetFile)
            installTarget = os.path.join(buildenv['outputdir'], installTargetFile)

            if os.path.exists(installTarget):
                os.remove(installTarget)

            if os.path.exists(installSource):
                os.rename(installSource, installTarget)

                _outputLine(outputFlagFile, installTargetFile)

        # write out the compressed image
        _outputLine(outputFlagFile, compFile1)

    # remove the distribution directory, since we have a tarball/zip
    if os.access(distDir, os.F_OK):
        hardhatlib.rmdir_recursive(distDir)

def _outputLine(path, text):
    output = open(path, 'a', 0)
    output.write(text + "\n")
    output.close()


def _getSVNRevisionInfo(buildenv):
    revision = ''
    trunk    = False

    command = [buildenv["svn"], 'info']

    outputList = hardhatutil.executeCommandReturnOutput(command)

    for line in outputList:
        if line.lower().startswith('revision:'):
            revision = line[10:-1]
        if line.lower().startswith('url:'):
            url   = line[6:-1]
            trunk = url.find('chandler/trunk') != -1

    return revision, trunk


def _getVersionInfo(buildenv):
    majorVersion    = '0'
    minorVersion    = '0'
    releaseVersion  = '0'
    versionFilename = 'version.py'

    headerData = """\
# Note:
#   release    - base version number
#   build      - "" or ".dev"
#   checkpoint - "" or "-YYYYMMDD"
#   revision   - "####"
#
#   version    - "%s%s-r%s%s" % (release, build, revision, checkpoint)
#

"""

    versionFile = open(versionFilename, 'r')
    lines       = versionFile.readlines()
    versionFile.close()

    data = {}

    for line in lines:
        line = line.lstrip()

        if not line.startswith('#'):
            linedata = line.split('=')

            if len(linedata) == 2:
                id    = linedata[0].strip().lower()
                value = linedata[1].lstrip()
                value = value[:-1] #strip off newline

                if value.startswith('"') and id != 'version':
                    value = value[1:-1]  #remove ""'s hack

                data[id] = value

    release     = data['release']
    versionData = release.split('.')

    if len(versionData) == 2:
        majorVersion = versionData[0]
        versionData  = versionData[1].split('-')

        if len(versionData) == 2:
            minorVersion   = versionData[0]
            releaseVersion = versionData[1]
        else:
            minorVersion = versionData[0]
    else:
        if len(versionData) == 3:
            majorVersion   = versionData[0]
            minorVersion   = versionData[1]
            releaseVersion = versionData[2]
        else:
            majorVersion = release

    revision, isTrunk = _getSVNRevisionInfo(buildenv)

      # re-write the version.py file *only* if we are doing a trunk build
      # as any tag or branch will already have versioned info stored
    if isTrunk:
        if len(buildenv['buildVersion']) > 0:
            data['checkpoint'] = '-%s' % buildenv['buildVersion']

        data['revision'] = revision

        versionFile = open(versionFilename, 'w')

        versionFile.write(headerData)
        for key in ('release', 'build', 'checkpoint', 'revision'):
            if key in data:
                versionFile.write('%s = "%s"\n' % (key, data[key]))

        versionFile.write('\nversion = "%s%s-r%s%s" % (release, build, revision, checkpoint)\n\n')

        versionFile.close()

    if data['build'] == '':
        buildName = release
    else:
        buildName = '%s%s-r%s%s' % (release, data['build'], data['revision'], data['checkpoint'])

    return (majorVersion, minorVersion, releaseVersion, buildName)


def generateDocs(buildenv):

    # Generate the content model docs (configure your webserver to map
    # /docs/current/model to chandler/docs/model)
    args = [os.path.join('distrib', 'docgen', 'genmodeldocs.py'), '-u',
     '/docs/current/model']
    hardhatlib.executeScript(buildenv, args)

    # Generate the epydocs
    targetDir = os.path.join("docs","api")
    hardhatlib.mkdirs(targetDir)

    if sys.platform == 'cygwin':
        chandlerdb = 'release/bin/Lib/site-packages/chandlerdb'
        queryparser = 'release/bin/Lib/site-packages/QueryParser.py'
    elif sys.platform == 'darwin':
        chandlerdb = 'release/Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4/site-packages/chandlerdb'
        queryparser = 'release/Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4/site-packages/QueryParser.py'
    else:
        chandlerdb = 'release/lib/python2.4/site-packages/chandlerdb'
        queryparser = 'release/lib/python2.4/site-packages/QueryParser.py'

    if buildenv['os'] != 'win' or sys.platform == 'cygwin':
        hardhatlib.epydoc(buildenv, info['name'], 'Generating API docs',
                          '-o %s -v -n Chandler' % targetDir,
                          '--debug',
                          '--inheritance listed',
                          '--no-private',
                          '--exclude=".*tests.*"',
                          'application',
                          # not interested in distrib
                          'i18n',
                          'parcels/core',
                          'parcels/feeds',
                          'parcels/osaf',
                          # XXX Stuff in osaf dirs below does not show
                          'parcels/osaf/app',
                          'parcels/osaf/examples',
                          'parcels/osaf/framework',
                          'parcels/osaf/mail',
                          'parcels/osaf/pim',
                          'parcels/osaf/servlets',
                          'parcels/osaf/sharing',
                          'parcels/osaf/tests',
                          'parcels/osaf/views',
                          'parcels/photos',
                          'repository',
                          # no Python in resources
                          'samples/skeleton',
                          'tools',
                          'util',
                          'Chandler.py',
                          'profile_tests.py',
                          'run_tests.py',
                          'schema_status.py',
                          'version.py',
                          chandlerdb, # This comes from internal
                          queryparser # This comes from external
                          )
    else:
        print 'Skipping API document generation, not supported in this platform'

