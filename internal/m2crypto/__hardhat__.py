import os, os.path, re, hardhatlib, sys

info = {
        'name':'M2Crypto 0.12',
        'root':'..',
       }

dependencies = ('openssl',
                #'swig', # XXX swig in path is required at the moment
               )

def build(buildenv):    
    if buildenv['version'] == 'release':
        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['python'], 'setup.py', 'build', '--build-base=build_release', 'install'],
         "Building and installing release")

    if buildenv['version'] == 'debug':
        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['python_d'], 'setup.py', 'build', '--build-base=build_debug', '--debug', 'install',
          '--force'],
         "Building and installing debug")    

    if buildenv['os'] == 'win' and sys.platform == 'cygwin':
        if buildenv['version'] == 'release':
            hardhatlib.epydoc(buildenv, info['name'], 'Generating API docs',
                              '-o build_release/api_doc -v -n M2Crypto',
                              '--inheritance listed',
                              '--no-private',
                              'build_release/lib.win32-2.3/M2Crypto')
        if buildenv['version'] == 'debug':
            hardhatlib.epydoc(buildenv, info['name'], 'Generating API docs',
                              '-o build_debug/api_doc -v -n M2Crypto',
                              '--inheritance listed',
                              '--no-private',
                              'build_debug/lib.win32-2.3/M2Crypto')


def clean(buildenv):
    # XXX Why doesn't 'setup.py clean' work?
    
    hardhatlib.rm_files('.', '_m2crypto.py')
    hardhatlib.rm_files('SWIG', '_m2crypto.c')

    if buildenv['version'] == 'release':
        if os.path.exists("build_release"):
            hardhatlib.rmdir_recursive("build_release")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], "Removed build_release directory")

    if buildenv['version'] == 'debug':
        if os.path.exists("build_debug"):
            hardhatlib.rmdir_recursive("build_debug")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], "Removed build_debug directory")


def run(buildenv):
    pass


def ls(dir, pattern):

    pattern = '^%s$' %(pattern)
    pattern = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
    exp = re.compile(pattern)

    return filter(exp.match, os.listdir(dir))


def rm(filepath):

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass
