import os, hardhatlib, hardhatutil, errno, sys

info = {
        'name':'Chandler',
        'root':'..',
       }

dependencies = (
                'wxpython/wxPython',
                'persistence/xerces-c',
                'persistence/pathan',
                'persistence/dbxml',
                'egenix-mx',
                'zodb',
                'jabber-py',
                'SOAPpy',
                'pychecker',
                '4suite',
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
    if buildenv['os'] == 'win':
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


    # Build UUID Extension and install it
    os.chdir(os.path.join("model","util","ext"))
    if buildenv['version'] == 'release':
        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['python'], 'setup.py', 'build', '--build-base=build_release', 'install'],
         "Building and installing UUIDext release")
    if buildenv['version'] == 'debug':
        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['python_d'], 'setup.py', 'build', '--build-base=build_debug', '--debug', 'install', '--force'],
         "Building and installing UUIDext debug")
    os.chdir("../../..")



    os.chdir("distrib")

    if buildenv['os'] == 'posix' or buildenv['os'] == 'osx':
        if buildenv['os'] == 'posix':
            os.chdir("linux")
        if buildenv['os'] == 'osx':
            os.chdir("osx")
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
             info['name'], "Copying MSVCI70.DLL to release/bin")
            hardhatlib.copyFile("msvci70.dll", buildenv['root'] + \
             os.sep + "release" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCP70.DLL to release/bin")
            hardhatlib.copyFile("msvcp70.dll", buildenv['root'] + \
             os.sep + "release" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCR70.DLL to release/bin")
            hardhatlib.copyFile("msvcr70.dll", buildenv['root'] + \
             os.sep + "release" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunRelease.bat to release")
            hardhatlib.copyFile("RunRelease.bat", buildenv['root'] + \
             os.sep + "release")
        if buildenv['version'] == 'debug':
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCI70D.DLL to debug/bin")
            hardhatlib.copyFile("msvci70d.dll", buildenv['root'] + \
             os.sep + "debug" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCP70D.DLL to debug/bin")
            hardhatlib.copyFile("msvcp70d.dll", buildenv['root'] + \
             os.sep + "debug" + os.sep + "bin")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying MSVCR70D.DLL to debug/bin")
            hardhatlib.copyFile("msvcr70d.dll", buildenv['root'] + \
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


    # Clean UUID Extension
    os.chdir(os.path.join("model","util","ext"))
    if buildenv['version'] == 'release':
        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['python'], 'setup.py', 'clean', 
         '--build-base=build_release'],
         "Cleaning UUIDext release")
        if os.path.exists("build_release"):
            hardhatlib.rmdir_recursive("build_release")
    if buildenv['version'] == 'debug':
        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['python_d'], 'setup.py', 'clean', 
         '--build-base=build_debug'],
         "Cleaning UUIDext debug")
        if os.path.exists("build_debug"):
            hardhatlib.rmdir_recursive("build_debug")
    os.chdir("../../..")


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

        if buildenv['os'] == 'posix':

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

        if buildenv['os'] == 'win':

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


def _transformFilesXslt(buildenv, transformFile, srcDir, destDir, fileList):
    """ Run the list of files through an XSLT transform
    """
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "Running XSLT processor")

    if buildenv['version'] == 'debug':
        python = buildenv['python_d']
        sitePkg = buildenv['pythonlibdir_d'] + os.sep + "site-packages"
    if buildenv['version'] == 'release':
        python = buildenv['python']
        sitePkg = buildenv['pythonlibdir'] + os.sep + "site-packages"

    if buildenv['os'] == 'win':
        if buildenv['version'] == 'debug':
            xsltScript = os.path.join(sitePkg,"Ft","Share","Bin","4xslt_d.exe")
        else:
            xsltScript = os.path.join(sitePkg,"Ft","Share","Bin","4xslt.exe")
    else:
        xsltScript = os.path.join(sitePkg, "Ft", "Share", "Bin", "4xslt")


    if not os.path.exists(destDir):
        os.mkdir(destDir)

    for file in fileList:
        srcFile = srcDir + os.sep + file
        destFile = destDir + os.sep + file
        try:
            os.makedirs(os.path.dirname(destFile))
        except Exception, e:
            pass
        if os.path.exists(srcFile):
            if buildenv['os'] == 'win':
                hardhatlib.executeCommand( buildenv, info['name'], 
                 [xsltScript, 
                 "--outfile="+destDir+os.sep+file,
                 srcFile, transformFile 
                 ], 
                 "XSLT: " + file )
            else: 
                hardhatlib.executeCommand( buildenv, info['name'], 
                 [python, xsltScript, 
                 "--outfile="+destDir+os.sep+file,
                 srcFile, transformFile 
                 ], 
                 "XSLT: " + file )

def generateDocs(buildenv):
    _transformFilesXslt(buildenv, 
     os.path.join(buildenv['root'],"Chandler","model","schema","html_transform.xml"),
     os.path.join(buildenv['root'],"Chandler"),
     os.path.join(buildenv['root'],buildenv['version'],"docs"),
     [
      os.path.join("parcels","OSAF","calendar","model","calendar.xml"),
      os.path.join("parcels","OSAF","contacts","model","contacts.xml"),
      os.path.join("application","agents","model","agents.xml"),
      os.path.join("model","schema","CoreSchema.xml"),
     ]
    )

