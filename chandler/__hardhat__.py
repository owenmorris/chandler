import os, hardhatlib

info = {
        'name':'Chandler',
       }

dependencies = (
                'Python-2.2.2', 
                'wxWindows',
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
        path = buildenv['root'] + os.sep + 'debug' + os.sep + 'bin' + os.pathsep + buildenv['path']
        python = buildenv['python_d']


    if buildenv['version'] == 'release':
        path = buildenv['root'] + os.sep + 'release' + os.sep + 'bin' + os.pathsep + buildenv['path']
        python = buildenv['python']


    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "Setting path to " + path)
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "Using " + python)
    os.putenv('path', path)


    if buildenv['os'] == 'posix':
	ld_library_path = os.environ['LD_LIBRARY_PATH']
	if buildenv['version'] == 'debug':
	    additional_path = buildenv['root'] + os.sep + 'debug' + os.sep + 'lib'
	else:
	    additional_path = buildenv['root'] + os.sep + 'release' + os.sep + 'lib'
	ld_library_path = additional_path + os.pathsep + ld_library_path
	hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
	 "Setting LD_LIBRARY_PATH to " + ld_library_path)
	os.putenv('LD_LIBRARY_PATH', ld_library_path)
	

    exit_code = os.spawnl(os.P_WAIT, python, python, "Chandler.py")

    if exit_code != 0:
        hardhatlib.log(buildenv, hardhatlib.HARDHAT_ERROR, info['name'], 
         "Chandler exited with code = " + str(exit_code))
        raise hardhatlib.HardHatError

def removeRuntimeDir(buildenv):

    path = ""

    if buildenv['version'] == 'debug':
        path = buildenv['root'] + os.sep + 'debug' 

    if buildenv['version'] == 'release':
        path = buildenv['root'] + os.sep + 'release' 


    if path:
        hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'],
         "Removing: " + path)
        hardhatlib.rmdir_recursive(path)
