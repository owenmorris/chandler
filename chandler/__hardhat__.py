import os, hardhatlib

manifest = {
	    'name':'Chandler',
	   }

def init(buildenv):
    # print manifest['name']
    # print buildenv['root']
    return 1

def build(buildenv):
    return 0

def run(buildenv):
    
    path = buildenv['root'] + os.sep + 'debug' + os.sep + 'bin' + os.pathsep + os.environ['path']
    path = buildenv['root'] + os.sep + 'release' + os.sep + 'bin' + os.pathsep + path
    os.putenv('path', path)
    exit_code = os.spawnl(os.P_WAIT, buildenv['python'], buildenv['python'], "Chandler.py")
    return exit_code
