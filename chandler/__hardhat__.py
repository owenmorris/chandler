import os, hardhatlib, hardhatutil, errno, sys

info = {
        'name':'Chandler',
        'root':'..',
       }

dependencies = (
                'python',
                'distutils',
                'wxpython',
                'egenix-mx',
                'zodb',
                'jabber-py',
               )


def build(buildenv):

    if buildenv['os'] == 'posix':
        os.chdir("distrib/linux/launcher")
        hardhatlib.executeCommand( buildenv, info['name'],
         [buildenv['make']],
         "Making launcher programs")
        if buildenv['version'] == 'release':
            hardhatlib.copyFile("chandler_bin", buildenv['root'] + \
             os.sep + "release")
            hardhatlib.copyFile("chandler", buildenv['root'] + \
             os.sep + "release")
        if buildenv['version'] == 'debug':
            hardhatlib.copyFile("chandler_bin", buildenv['root'] + \
             os.sep + "debug")
            hardhatlib.copyFile("chandler", buildenv['root'] + \
             os.sep + "debug")
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
        if buildenv['version'] == 'debug':
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE,
             info['name'], "Copying RunDebug to debug")
            hardhatlib.copyFile("RunDebug", buildenv['root'] + \
             os.sep + "debug")

    if buildenv['os'] == 'win':
        os.chdir("win")
        if buildenv['version'] == 'release':
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
    pass


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

    _CreateVersionFile(buildenv)

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

            os.chdir(buildenv['root'])
            hardhatlib.compressDirectory(buildenv, "debug", 
             "Chandler_linux_dev_debug_" + buildVersionShort)

        if buildenv['os'] == 'osx':

            os.chdir(buildenv['root'])
            hardhatlib.compressDirectory(buildenv, "debug",
             "Chandler_osx_dev_debug_" + buildVersionShort)

        if buildenv['os'] == 'win':

            os.chdir(buildenv['root'])
            hardhatlib.compressDirectory(buildenv, "debug", 
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
            hardhatlib.compressDirectory(buildenv, distName, distName)

            os.chdir(buildenv['root'])
            hardhatlib.compressDirectory(buildenv, "release", 
             "Chandler_linux_dev_release_" + buildVersionShort)
            os.chdir(buildenv['root'])

        if buildenv['os'] == 'osx':

            distName = 'Chandler_osx_' + buildVersionShort
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

            os.chdir(buildenv['root'])
            hardhatlib.compressDirectory(buildenv, "release",
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
            hardhatlib.compressDirectory(buildenv, distName, distName)

            os.chdir(buildenv['root'])
            hardhatlib.compressDirectory(buildenv, "release", 
             "Chandler_win_dev_release_" + buildVersionShort)


def _CreateVersionFile(buildenv):
    versionFile = "version.py"
    if os.path.exists(versionFile):
        os.remove(versionFile)
    versionFileHandle = open(versionFile, 'w', 0)
    versionFileHandle.write("build = \"" + buildenv['buildVersion'] + "\"\n")
    versionFileHandle.close()
