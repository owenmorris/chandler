import os, hardhatlib, errno

info = {
        'name':'Chandler',
       }

dependencies = (
                'Python-2.2.2', 
                'wxWindows-2.4',
                'distutils',
                'egenix-mx-base-2.0.4',
                'ZODB4',
                'PyXML'
               )


def build(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "Nothing to build")


def clean(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_WARNING, info['name'], 
     "Clean hasn't been set up yet")


def run(buildenv):

    if buildenv['version'] == 'debug':
        python = buildenv['python_d.run']

    if buildenv['version'] == 'release':
        python = buildenv['python.run']

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
            handleManifest(buildenv, manifestFile)

    if buildenv['os'] == 'osx':

        if buildenv['version'] == 'release':
            manifestFile = "distrib/osx/manifest.osx"
            handleManifest(buildenv, manifestFile)

    if buildenv['os'] == 'win':

        if buildenv['version'] == 'release':
            manifestFile = "distrib" + os.sep + "win" + os.sep + "manifest.win"
            handleManifest(buildenv, manifestFile)




def handleManifest(buildenv, filename):
    import fileinput
    import shutil

    before = "xyzzy"
    after = "plugh"

    for line in fileinput.input(filename):
        line = line[:-1]
        if line[0:1] == "!":
            line = line[1:]
            (before,after) = line.split(",")
            blen = len(before)
            print "before=", before
        else:
            print line
            if line[0:blen] == before:
                line2 = after + line[blen:]
                source = buildenv['root'] + os.sep + line
                dest = buildenv['distdir'] + os.sep + line2
                print source, "->", dest
                path = os.path.dirname(dest)
                print path
                mkdirs(path)
                shutil.copy(source, dest)


def mkdirs(newdir, mode=0777):
    try: 
        os.makedirs(newdir, mode)
    except OSError, err:
        # Reraise the error unless it's about an already existing directory 
        if err.errno != errno.EEXIST or not os.path.isdir(newdir): 
            raise

