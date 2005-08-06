import os, hardhatlib, hardhatutil, sys

info = {
        'name':'chandler',
        'root':'..',
       }

dependencies = ()

def build(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "See http://wiki.osafoundation.org/twiki/bin/view/Jungle/NewBuildInstructions for how to build")

def clean(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "See http://wiki.osafoundation.org/twiki/bin/view/Jungle/NewBuildInstructions for how to build")

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

    majorVersion, minorVersion, releaseVersion = _createVersionFile(buildenv)

    buildVersionShort = \
     hardhatutil.RemovePunctuation(buildenv['buildVersion'])

    # When the build version string is based on one of our tags
    # (which usually begin with "CHANDLER_") let's remove the "CHANDLER_"
    # prefix from the string so it doesn't end up in the generated filenames
    # (so we can avoid getting a distro file named:
    # "Chandler_linux_CHANDLER_M1.tar.gz", and instead get:
    # "Chandler_linux_M1.tar.gz")
    buildVersionShort = buildVersionShort.replace("CHANDLER_", "")

    installTargetFile = None

    if buildenv['version'] == 'debug':

        if buildenv['os'] == 'osx':

            distName = 'Chandler_osx_debug_' + buildVersionShort
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

            distName = 'Chandler_linux_debug_' + buildVersionShort
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

            distName = 'Chandler_win_debug_' + buildVersionShort
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

            distName = 'Chandler_linux_' + buildVersionShort
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

            distName = 'Chandler_osx_' + buildVersionShort
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

            distName = 'Chandler_win_' + buildVersionShort
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

def _createVersionFile(buildenv):
    majorVersion   = '0'
    minorVersion   = '5'
    releaseVersion = '4'
    versionFile    = 'version.py'
    if os.path.exists(versionFile):
        os.remove(versionFile)
    versionFileHandle = open(versionFile, 'w', 0)
    versionFileHandle.write('build = "%s"\n' % buildenv['buildVersion'])
    versionFileHandle.write('release = "%s.%s-%s"\n' % (majorVersion, minorVersion, releaseVersion))
    versionFileHandle.close()
    
    return (majorVersion, minorVersion, releaseVersion)

def generateDocs(buildenv):

    # Generate the content model docs (configure your webserver to map
    # /docs/current/model to chandler/docs/model)
    args = [os.path.join('distrib', 'docgen', 'genmodeldocs.py'), '-u',
     '/docs/current/model']
    hardhatlib.executeScript(buildenv, args)

    # Generate the epydocs
    targetDir = os.path.join("docs","api")
    hardhatlib.mkdirs(targetDir)
    if buildenv['os'] != 'win' or sys.platform == 'cygwin':
        hardhatlib.epydoc(buildenv, info['name'], 'Generating API docs',
                          '-o %s -v -n Chandler' % targetDir,
                          '--inheritance listed',
                          '--no-private',
                          'application',
                          'parcels/osaf/sharing',
                          'repository/item',
                          'repository/persistence',
                          'repository/util',
                          'repository/query',
                          'repository/schema',
                          'crypto')

