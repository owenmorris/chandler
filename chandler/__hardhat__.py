import os, hardhatlib, hardhatutil, errno, sys

info = {
        'name':'Chandler',
        'root':'..',
       }

dependencies = (
                'python',
                'epydoc',
                '../../internal/wx/wxPython-2.5',
                'persistence/xerces-c',
                'persistence/pathan',
                'persistence/dbxml',
                'persistence/libxml2',
                'persistence/libxslt',
                'persistence/PyLucene',
                'pyxml',
                'egenix-mx',
                'jabber-py',
                'SOAPpy',
                'pychecker',
                # 'm2crypto',
                'Chandler/repository'
               )

def build(buildenv):

    # Build the linux launcher program
    if buildenv['os'] == 'posix':
        os.chdir("distrib/linux/launcher")
        version = buildenv['version']
        buildDir = "build_"+version
        if not os.path.exists(buildDir):
            os.mkdir(buildDir)
            if not os.path.exists(os.path.join(buildDir, "Makefile")):
                os.symlink("../Makefile", os.path.join(buildDir, "Makefile"))
        os.chdir(buildDir)
        if buildenv['version'] == 'release':
            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['make'], 
             "CHANDLER_ROOT="+buildenv['root'], 
             "VPATH=.." ],
             "Making launcher programs")
        else:
            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['make'], 
             "DEBUG=1", 
             "CHANDLER_ROOT="+buildenv['root'], 
             "VPATH=.." ],
             "Making launcher programs")
        hardhatlib.copyFile("chandler_bin", buildenv['root'] + \
         os.sep + version)
        hardhatlib.copyFile("chandler", buildenv['root'] + \
         os.sep + version)

        os.chdir("../../../..")

    # Build the windows launcher program
    elif buildenv['os'] == 'win':
        version = buildenv['version']

        try:
            os.remove('output.txt')
        except:
            pass

        hardhatlib.executeCommand(buildenv, info['name'],
                                  [ buildenv['compiler'],
                                    'distrib/win/launcher/launcher.sln',
                                    '/build', version.capitalize(),
                                    '/out', 'output.txt' ],
                                  'Building launcher ' + version,
                                  0, 'output.txt')

    os.chdir("distrib")

    if buildenv['os'] == 'posix' or buildenv['os'] == 'osx':
        if buildenv['os'] == 'osx':
            os.chdir("osx")
        elif buildenv['os'] == 'posix':
            os.chdir("linux")

        if buildenv['version'] == 'release':
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunRelease to release")
            hardhatlib.copyFile("RunRelease", buildenv['root'] + \
             os.sep + "release")

            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunPython to release")
            hardhatlib.copyFile("RunPythonRelease", buildenv['root'] + \
             os.sep + "release")
            os.rename(
             buildenv['root']+os.sep+"release"+os.sep+"RunPythonRelease",
             buildenv['root']+os.sep+"release"+os.sep+"RunPython"
            )

        if buildenv['version'] == 'debug':
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunDebug to debug")
            hardhatlib.copyFile("RunDebug", buildenv['root'] + \
             os.sep + "debug")

            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunPython to debug")
            hardhatlib.copyFile("RunPythonDebug", buildenv['root'] + \
             os.sep + "debug")
            os.rename(
             buildenv['root']+os.sep+"debug"+os.sep+"RunPythonDebug",
             buildenv['root']+os.sep+"debug"+os.sep+"RunPython"
            )

    if buildenv['os'] == 'win':
        os.chdir("win")
        if buildenv['version'] == 'release':
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCP71.DLL to release/bin")
            hardhatlib.copyFile("msvcp71.dll", buildenv['root'] + \
             os.sep + "release" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCR71.DLL to release/bin")
            hardhatlib.copyFile("msvcr71.dll", buildenv['root'] + \
             os.sep + "release" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunRelease.bat to release")
            hardhatlib.copyFile("RunRelease.bat", buildenv['root'] + \
             os.sep + "release")
        if buildenv['version'] == 'debug':
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCP71D.DLL to debug/bin")
            hardhatlib.copyFile("msvcp71d.dll", buildenv['root'] + \
             os.sep + "debug" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCR71D.DLL to debug/bin")
            hardhatlib.copyFile("msvcr71d.dll", buildenv['root'] + \
             os.sep + "debug" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCRTD.DLL to debug/bin")
            hardhatlib.copyFile("msvcrtd.dll", buildenv['root'] + \
             os.sep + "debug" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunDebug.bat to debug")
            hardhatlib.copyFile("RunDebug.bat", buildenv['root'] + \
             os.sep + "debug")


def clean(buildenv):
    
    # Clean the linux launcher program
    if buildenv['os'] == 'posix':
        os.chdir("distrib/linux/launcher")
        version = buildenv['version']
        buildDir = "build_"+version
        if os.path.exists(buildDir):
            hardhatlib.rmdir_recursive(buildDir)
        os.chdir("../../..")

    # Clean the windows launcher program
    if buildenv['os'] == 'win':
        version = buildenv['version']

        try:
            os.remove('output.txt')
        except:
            pass

        hardhatlib.executeCommand(buildenv, info['name'],
                                  [ buildenv['compiler'],
                                    'distrib/win/launcher/launcher.sln',
                                    '/clean', version.capitalize(),
                                    '/out', 'output.txt' ],
                                  'Cleaning launcher ' + version,
                                  0, 'output.txt')


def run(buildenv):

    if buildenv['version'] == 'debug':
        python = buildenv['python_d']

    if buildenv['version'] == 'release':
        python = buildenv['python']

    hardhatlib.executeCommandNoCapture( buildenv, info['name'],
     [python, "Chandler.py"], "Running Chandler" )


def removeRuntimeDir(buildenv):

    path = ""

    if buildenv['version'] == 'debug':
        path = buildenv['root'] + os.sep + 'debug'

    if buildenv['version'] == 'release':
        path = buildenv['root'] + os.sep + 'release'


    if path:
        if os.access(path, os.F_OK):
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'],
             "Removing: " + path)
            hardhatlib.rmdir_recursive(path)

def distribute(buildenv):

    _createVersionFile(buildenv)

    buildVersionShort = \
     hardhatutil.RemovePunctuation(buildenv['buildVersion'])

    # When the build version string is based on one of our CVS tags
    # (which usually begin with "CHANDLER_") let's remove the "CHANDLER_"
    # prefix from the string so it doesn't end up in the generated filenames
    # (so we can avoid getting a distro file named:
    # "Chandler_linux_CHANDLER_M1.tar.gz", and instead get:
    # "Chandler_linux_M1.tar.gz")
    buildVersionShort = buildVersionShort.replace("CHANDLER_", "")


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

            os.chdir(buildenv['root'])
            compFile2 = hardhatlib.compressDirectory(buildenv, 
             ["debug"],
             "Chandler_osx_dev_debug_" + buildVersionShort)

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
            compFile1 = hardhatlib.compressDirectory(buildenv, [distName],
             distName)

            os.chdir(buildenv['root'])
            compFile2 = hardhatlib.compressDirectory(buildenv, 
             ["debug"],
             "Chandler_linux_dev_debug_" + buildVersionShort)
            os.chdir(buildenv['root'])

        elif buildenv['os'] == 'win':

            distName = 'Chandler_win_debug_' + buildVersionShort
            distDir = buildenv['root'] + os.sep + distName
            buildenv['distdir'] = distDir
            if os.access(distDir, os.F_OK):
                hardhatlib.rmdir_recursive(distDir)
            os.mkdir(distDir)

            manifestFile = "distrib" + os.sep + "win" + os.sep + \
             "manifest.debug.win"
            hardhatlib.handleManifest(buildenv, manifestFile)
            os.chdir(buildenv['root'])
            compFile1 = hardhatlib.compressDirectory(buildenv, [distName], 
             distName)

            os.chdir(buildenv['root'])
            compFile2 = hardhatlib.compressDirectory(buildenv, 
             ["debug"],
             "Chandler_win_dev_debug_" + buildVersionShort)


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
            compFile1 = hardhatlib.compressDirectory(buildenv, [distName],
             distName)

            os.chdir(buildenv['root'])
            compFile2 = hardhatlib.compressDirectory(buildenv, 
             ["release"],
             "Chandler_linux_dev_release_" + buildVersionShort)
            os.chdir(buildenv['root'])

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

            os.chdir(buildenv['root'])
            compFile2 = hardhatlib.compressDirectory(buildenv, 
             ["release"],
             "Chandler_osx_dev_release_" + buildVersionShort)

        if buildenv['os'] == 'win':

            distName = 'Chandler_win_' + buildVersionShort
            distDir = buildenv['root'] + os.sep + distName
            buildenv['distdir'] = distDir
            if os.access(distDir, os.F_OK):
                hardhatlib.rmdir_recursive(distDir)
            os.mkdir(distDir)

            manifestFile = "distrib" + os.sep + "win" + os.sep + "manifest.win"
            hardhatlib.handleManifest(buildenv, manifestFile)
            os.chdir(buildenv['root'])
            compFile1 = hardhatlib.compressDirectory(buildenv, [distName], 
             distName)

            os.chdir(buildenv['root'])
            compFile2 = hardhatlib.compressDirectory(buildenv, 
             ["release"],
             "Chandler_win_dev_release_" + buildVersionShort)

    # put the compressed files in the right place if specified 'outputdir'
    if buildenv['outputdir']:
        if not os.path.exists(buildenv['outputdir']):
            os.mkdir(buildenv['outputdir'])
        # The end-user distro
        if os.path.exists(buildenv['outputdir'] + os.sep + compFile1):
            os.remove(buildenv['outputdir'] + os.sep + compFile1)
        os.rename(compFile1, buildenv['outputdir'] + os.sep + compFile1)
        if buildenv['version'] == 'release':
            _outputLine(buildenv['outputdir']+os.sep+"enduser", compFile1)
        else:
            _outputLine(buildenv['outputdir']+os.sep+"developer", compFile1)

        # The release tarball
        if os.path.exists(buildenv['outputdir'] + os.sep + compFile2):
            os.remove(buildenv['outputdir'] + os.sep + compFile2)
        os.rename( compFile2, buildenv['outputdir'] + os.sep + compFile2)
        if buildenv['version'] == 'release':
            _outputLine(buildenv['outputdir']+os.sep+"release", compFile2)
        else:
            _outputLine(buildenv['outputdir']+os.sep+"debug", compFile2)

    # remove the distribution directory, since we have a tarball/zip
    if os.access(distDir, os.F_OK):
        hardhatlib.rmdir_recursive(distDir)

def _outputLine(path, text):
    output = open(path, 'w', 0)
    output.write(text + "\n")
    output.close()

def _createVersionFile(buildenv):
    versionFile = "version.py"
    if os.path.exists(versionFile):
        os.remove(versionFile)
    versionFileHandle = open(versionFile, 'w', 0)
    versionFileHandle.write("build = \"" + buildenv['buildVersion'] + "\"\n")
    versionFileHandle.close()

def generateDocs(buildenv):

    # Generate the content model docs
    xslDir = os.path.join("distrib","transforms")
    targetDir = os.path.join("..",buildenv['version'],"docs","model")
    hardhatlib.copyFile(os.path.join(xslDir,"includes","schema.css"), targetDir)
    hardhatlib.copyFile(os.path.join("distrib", "docs", "automatic-docs-help.html"), targetDir)
    hardhatlib.copyFile(os.path.join("distrib", "docs", "repository-intro.html"), targetDir)

    args = [os.path.join(xslDir, "generateDocs.py"), targetDir, xslDir, "."]
    hardhatlib.executeScript(buildenv, args)

    # Generate the epydocs
    targetDir = os.path.join("..",buildenv['version'],"docs","api")
    if buildenv['os'] != 'win' or sys.platform == 'cygwin':
        hardhatlib.epydoc(buildenv, info['name'], 'Generating API docs',
                          '-o %s -v -n Chandler' % targetDir,
                          '--inheritance listed',
                          '--no-private',
                          'parcels/OSAF/framework/notifications',
                          'repository/item',
                          'repository/schema')
