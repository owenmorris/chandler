import os, hardhatlib

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
