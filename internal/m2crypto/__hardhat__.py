import os, os.path, re, hardhatlib

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

def clean(buildenv):

    version = buildenv['version']

    if buildenv['os'] == 'osx' or buildenv['os'] == 'posix':
        pass
    elif buildenv['os'] == 'win':
        pass

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
