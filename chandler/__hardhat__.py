import os, hardhatlib

info = {
        'name':'Chandler',
       }

dependencies = (
                'Python-2.2.2', 
		'distutils',
		'wxWindows',
		'egenix-mx-base-2.0.4',
		'ZODB4'
	       )


def build(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "Nothing to build")


def clean(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_WARNING, info['name'], 
     "Clean hasn't been set up yet")


def run(buildenv):
    
    if buildenv['version'] == 'debug':
        path = buildenv['root'] + os.sep + 'debug' + os.sep + 'bin' + 
         os.pathsep + os.environ['path']
        python = buildenv['python_d']


    if buildenv['version'] == 'release':
        path = buildenv['root'] + os.sep + 'release' + os.sep + 'bin' + 
         os.pathsep + os.environ['path']
        python = buildenv['python']


    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "Setting path to " + path)
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, info['name'], 
     "Using " + python)
    os.putenv('path', path)
    exit_code = os.spawnl(os.P_WAIT, python, python, "Chandler.py")

    if exit_code != 0:
        hardhatlib.log(buildenv, hardhatlib.HARDHAT_ERROR, info['name'], 
         "Chandler exited with code = " + str(exit_code))
        raise hardhatlib.HardHatError
