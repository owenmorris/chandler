import os, hardhatlib, errno, sys

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

    distDir = buildenv['root'] + os.sep + 'distrib'
    buildenv['distdir'] = distDir

    if os.access(distDir, os.F_OK):
        hardhatlib.rmdir_recursive(distDir)

    os.mkdir(distDir)

    if buildenv['os'] == 'posix':

        if buildenv['version'] == 'release':
            manifestFile = "distrib/linux/manifest.linux"
            hardhatlib.handleManifest(buildenv, manifestFile)

    if buildenv['os'] == 'osx':

        if buildenv['version'] == 'release':
            manifestFile = "distrib/osx/manifest.osx"
            hardhatlib.handleManifest(buildenv, manifestFile)

    if buildenv['os'] == 'win':

        if buildenv['version'] == 'release':
            manifestFile = "distrib" + os.sep + "win" + os.sep + "manifest.win"
            hardhatlib.handleManifest(buildenv, manifestFile)


