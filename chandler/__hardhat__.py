import os, hardhatlib, errno

info = {
        'name':'Chandler',
       }

dependencies = (
                'python', 
                'wxpython',
                'distutils',
                'egenix-mx',
                'zodb',
                'jabber-py',
               )


def build(buildenv):

    if buildenv['os'] == 'win':
	os.chdir("distrib")
	os.chdir("win")
	if buildenv['version'] == 'release':
	    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
	     info['name'], "Copying MSVCR70.DLL to release/bin")
	    hardhatlib.copyFile("msvcr70.dll", buildenv['root'] + \
	     os.sep + "release" + os.sep + "bin")
	if buildenv['version'] == 'debug':
	    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
	     info['name'], "Copying MSVCR70.DLL to debug/bin")
	    hardhatlib.copyFile("msvcr70.dll", buildenv['root'] + \
	     os.sep + "debug" + os.sep + "bin")
	    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
	     info['name'], "Copying MSVCRTD.DLL to debug/bin")
	    hardhatlib.copyFile("msvcrtd.dll", buildenv['root'] + \
	     os.sep + "debug" + os.sep + "bin")



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


